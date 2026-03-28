#!/usr/bin/env python3
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ANIME STREAM & DOWNLOAD API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 API ENDPOINTS:
 
 1) Download Anime Episode:
    GET /?name=ANIME_NAME&season=SEASON_NUM&episode=EP_NUM&dubbed=yes/no
    Example: /?name=naruto&season=1&episode=1&dubbed=no
    
 2) Download Movie:
    GET /?movie=MOVIE_NAME&dubbed=yes/no
    Example: /?movie=your-name&dubbed=yes
    
 3) Search Anime:
    GET /search?q=QUERY
    Example: /search?q=naruto
    
 4) Get Anime Info:
    GET /info?name=ANIME_NAME
    Example: /info?name=naruto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 SETUP (Ubuntu 22.04 VPS):

 1) System deps:
    sudo apt update && sudo apt install -y ffmpeg curl git

 2) ani-cli:
    sudo curl -sL https://raw.githubusercontent.com/pystardust/ani-cli/master/ani-cli \
      -o /usr/local/bin/ani-cli && sudo chmod +x /usr/local/bin/ani-cli

 3) yt-dlp:
    sudo curl -sL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
      -o /usr/local/bin/yt-dlp && sudo chmod +x /usr/local/bin/yt-dlp

 4) Python deps (auto-installed on first run):
    pip3 install flask requests

 5) Run:
    python3 anime_api.py

 6) Access: http://YOUR_VPS_IP:9079
    Firewall: sudo ufw allow 9079/tcp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, sys, subprocess, json, re, logging, tempfile
from pathlib import Path
from urllib.parse import quote, unquote

# ── Auto-install Python packages ──────────────────────────────────────────
def _pip(pkg, imp=None):
    imp = imp or pkg.replace('-','_')
    try:
        __import__(imp)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable,'-m','pip','install','--quiet',pkg])

for _p,_i in [('flask',None), ('requests',None)]:
    _pip(_p,_i)

from flask import Flask, request, jsonify, send_file, Response
import requests as httpx

# ── Config ────────────────────────────────────────────────────────────────
HOST         = '0.0.0.0'
PORT         = 9079
DOWNLOAD_DIR = os.path.expanduser('~/anime_downloads')
JIKAN        = 'https://api.jikan.moe/v4'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

# ── Tool checks ───────────────────────────────────────────────────────────
def ani_cli_ok():
    try: return subprocess.run(['ani-cli','--version'],capture_output=True,timeout=5).returncode==0
    except: return False

def ytdlp_ok():
    try: return subprocess.run(['yt-dlp','--version'],capture_output=True,timeout=5).returncode==0
    except: return False

# ── Jikan (MyAnimeList public API) ────────────────────────────────────────
_jcache = {}  # slug -> metadata dict

def jikan_search(query, limit=20):
    try:
        r = httpx.get(f'{JIKAN}/anime', params={'q':query,'limit':limit,'sfw':True}, timeout=12)
        if r.status_code != 200: return []
        results = []
        for a in r.json().get('data',[]):
            mid   = str(a.get('mal_id',''))
            title = a.get('title_english') or a.get('title','Unknown')
            slug  = re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')+'-m'+mid
            cover = (a.get('images',{}).get('jpg',{}).get('large_image_url') or
                     a.get('images',{}).get('jpg',{}).get('image_url',''))
            meta = {
                'id':slug,'mal_id':mid,'title':title,'cover':cover,
                'episodes_count': a.get('episodes') or 0,
                'score': a.get('score') or 0.0,
                'synopsis': (a.get('synopsis') or 'No description.')[:600],
                'genres': [g['name'] for g in a.get('genres',[])],
                'status': a.get('status',''), 'year':'',
                'type': a.get('type','TV'),
            }
            aired = a.get('aired',{}).get('prop',{}).get('from',{}) or {}
            meta['year'] = str(aired.get('year',''))
            _jcache[slug] = meta
            results.append(meta)
        return results
    except Exception as e:
        log.warning(f'Jikan search error: {e}')
        return []

def jikan_episodes(mal_id):
    eps = []
    try:
        for pg in range(1,30):
            r = httpx.get(f'{JIKAN}/anime/{mal_id}/episodes',params={'page':pg},timeout=12)
            if r.status_code != 200: break
            data = r.json()
            for e in data.get('data',[]):
                eps.append({
                    'number':  e.get('mal_id', len(eps)+1),
                    'title':   e.get('title') or f"Episode {e.get('mal_id','')}",
                    'duration':'~24 min',
                    'filler':  e.get('filler',False),
                    'recap':   e.get('recap',False),
                })
            if not data.get('pagination',{}).get('has_next_page',False):
                break
    except Exception as e:
        log.warning(f'Jikan episodes error: {e}')
    return eps

def build_detail(slug):
    meta = _jcache.get(slug)
    if not meta:
        title = re.sub(r'-m\d+$','',slug).replace('-',' ')
        results = jikan_search(title)
        meta = next((r for r in results if r['id']==slug), results[0] if results else None)
    if not meta:
        n = 12
        return {'id':slug,'mal_id':'','title':slug.replace('-',' ').title(),'cover':'',
                'synopsis':'No description.','episodes_count':n,'score':0,'genres':[],
                'status':'','year':'','type':'TV',
                'episodes':[{'number':i,'title':f'Episode {i}','duration':'~24 min','filler':False,'recap':False} for i in range(1,n+1)]}
    mal_id = meta['mal_id']
    eps = jikan_episodes(mal_id) if mal_id else []
    if not eps:
        n = meta['episodes_count'] or 12
        eps = [{'number':i,'title':f'Episode {i}','duration':'~24 min','filler':False,'recap':False} for i in range(1,n+1)]
    meta = dict(meta)
    meta['episodes'] = eps
    meta['episodes_count'] = len(eps)
    return meta

# ── ani-cli stream URL ────────────────────────────────────────────────────
_ani_map = {}

def ani_search(query, dub=False):
    try:
        slug = re.sub(r'[^a-z0-9]+','-',query.lower()).strip('-')
        _ani_map[slug] = {'query':query,'idx':'1','title':query,'dub':dub}
    except Exception as e:
        log.warning(f'ani-cli search: {e}')

def ani_stream_url(slug, episode, dub=False):
    if not ani_cli_ok():
        return None
    info = _ani_map.get(slug)
    query = info['query'] if info else re.sub(r'-m\d+$','',slug).replace('-',' ')
    is_dub= (info['dub'] if info else False) or dub
    
    try:
        cmd = ['ani-cli', '-S', '1', '-e', str(episode)]
        if is_dub:
            cmd.append('--dub')
        cmd.append(query)
        
        env = os.environ.copy()
        env['ANI_CLI_PLAYER'] = 'debug'
        env['ANI_CLI_QUALITY'] = 'best'
        if 'HOME' not in env or not env['HOME']:
            env['HOME'] = os.path.expanduser('~')
        
        log.info(f'Running ani-cli with debug player: {" ".join(cmd)}')
        
        proc = subprocess.run(
            cmd,
            capture_output=True, 
            text=True, 
            timeout=120,
            env=env
        )
        out = proc.stdout + proc.stderr
        
        # Look for "Selected link:" in debug output
        selected_match = re.search(r'Selected link:\s*(\S+)', out, re.IGNORECASE)
        if selected_match:
            url = selected_match.group(1).strip()
            url = re.sub(r'[\'"\s]+$', '', url)
            log.info(f'Found selected link from ani-cli: {url}')
            
            if url.startswith('http://') or url.startswith('https://'):
                return url
            else:
                log.warning(f'Invalid URL format: {url}')
        
        # Look for "All links:" section
        all_links_match = re.search(r'All links:.*?(\bhttps?://\S+)', out, re.IGNORECASE | re.DOTALL)
        if all_links_match:
            url = all_links_match.group(1).strip()
            url = re.sub(r'[\'"\s]+$', '', url)
            log.info(f'Found link from "All links" section: {url}')
            return url
        
        # Fallback: Look for m3u8, mp4, or ts URLs
        urls = re.findall(r'https?://\S+\.(?:m3u8|mp4|ts)(?:\S+)?', out)
        if urls:
            log.info(f'Found stream URL via regex: {urls[0]}')
            return urls[0]
        
        log.warning(f'No stream URL found in ani-cli output for {query} ep{episode}')
        return None
        
    except subprocess.TimeoutExpired:
        log.error(f'ani-cli timed out after 120s for {query} ep{episode}')
        return None
    except Exception as e:
        log.error(f'ani-cli error for {query} ep{episode}: {e}')
        return None

# ── Download video file ───────────────────────────────────────────────────
def download_video(url, filename):
    """Download video using yt-dlp and return file path"""
    try:
        safe_fname = re.sub(r'[^\w\s-]','',filename).strip().replace(' ','_') + '.mp4'
        fpath = os.path.join(DOWNLOAD_DIR, safe_fname)
        
        if not url:
            raise RuntimeError("Could not get stream URL")
        
        log.info(f'Starting download: {filename} from URL: {url}')
        
        if ytdlp_ok():
            cmd = [
                'yt-dlp',
                '--no-playlist',
                '--no-warnings',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '--referer', 'https://allanime.to/',
                '--add-header', 'Origin:https://allanime.to',
                '--add-header', 'Accept:*/*',
                '--no-check-certificate',
                '--format', 'best[ext=mp4]/best',
                '-o', fpath,
                url
            ]
            
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if proc.returncode != 0:
                log.error(f'yt-dlp failed: {proc.stderr}')
                raise RuntimeError(f"Download failed: {proc.stderr[:200]}")
        else:
            # Fallback: stream via requests
            log.info('yt-dlp not available, using requests fallback')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://allanime.to/',
                'Origin': 'https://allanime.to',
                'Accept': '*/*'
            }
            r = httpx.get(url, stream=True, timeout=30, headers=headers, allow_redirects=True)
            r.raise_for_status()
            
            with open(fpath,'wb') as f:
                for chunk in r.iter_content(65536):
                    if chunk:
                        f.write(chunk)
        
        if not os.path.exists(fpath):
            raise RuntimeError("File not created")
        
        sz = os.path.getsize(fpath)
        if sz < 1000000:  # Less than 1MB
            log.warning(f'Downloaded file is suspiciously small: {sz} bytes')
        
        log.info(f'Download completed: {safe_fname} ({sz} bytes)')
        return fpath
        
    except Exception as e:
        log.error(f'Download error: {e}')
        raise

# ══════════════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════════════

@app.route('/')
def root():
    """
    Main endpoint for downloading anime episodes or movies
    
    For Episodes: /?name=ANIME_NAME&season=SEASON_NUM&episode=EP_NUM&dubbed=yes/no
    For Movies:   /?movie=MOVIE_NAME&dubbed=yes/no
    """
    try:
        # Check if it's a movie request
        movie_name = request.args.get('movie')
        if movie_name:
            dubbed = request.args.get('dubbed', 'no').lower() in ['yes', 'true', '1']
            return download_movie(movie_name, dubbed)
        
        # Episode request
        anime_name = request.args.get('name')
        season = request.args.get('season', '1')
        episode = request.args.get('episode')
        dubbed = request.args.get('dubbed', 'no').lower() in ['yes', 'true', '1']
        
        if not anime_name or not episode:
            return jsonify({
                'error': 'Missing required parameters',
                'usage': {
                    'episode': '/?name=ANIME_NAME&season=SEASON_NUM&episode=EP_NUM&dubbed=yes/no',
                    'movie': '/?movie=MOVIE_NAME&dubbed=yes/no'
                }
            }), 400
        
        # Build query with season if provided
        if season and season != '1':
            query = f"{anime_name} season {season}"
        else:
            query = anime_name
        
        # Get stream URL
        slug = re.sub(r'[^a-z0-9]+','-', query.lower()).strip('-')
        ani_search(query, dubbed)
        
        stream_url = ani_stream_url(slug, int(episode), dubbed)
        
        if not stream_url:
            return jsonify({
                'error': 'Could not find stream URL',
                'anime': anime_name,
                'season': season,
                'episode': episode,
                'dubbed': dubbed,
                'suggestion': 'Make sure ani-cli is installed and the anime exists'
            }), 404
        
        # Download the video
        filename = f"{anime_name}_S{season}E{episode}_{'dub' if dubbed else 'sub'}"
        filepath = download_video(stream_url, filename)
        
        # Send file to user's device
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='video/mp4'
        )
        
    except Exception as e:
        log.error(f'Error in root endpoint: {e}')
        return jsonify({'error': str(e)}), 500

def download_movie(movie_name, dubbed=False):
    """Download anime movie"""
    try:
        slug = re.sub(r'[^a-z0-9]+','-', movie_name.lower()).strip('-')
        ani_search(movie_name, dubbed)
        
        # Movies are usually episode 1
        stream_url = ani_stream_url(slug, 1, dubbed)
        
        if not stream_url:
            return jsonify({
                'error': 'Could not find movie stream URL',
                'movie': movie_name,
                'dubbed': dubbed
            }), 404
        
        filename = f"{movie_name}_movie_{'dub' if dubbed else 'sub'}"
        filepath = download_video(stream_url, filename)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='video/mp4'
        )
        
    except Exception as e:
        log.error(f'Error downloading movie: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search():
    """
    Search for anime
    
    GET /search?q=QUERY
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Missing query parameter', 'usage': '/search?q=QUERY'}), 400
    
    try:
        results = jikan_search(query, limit=20)
        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        log.error(f'Search error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/info')
def info():
    """
    Get detailed information about an anime
    
    GET /info?name=ANIME_NAME
    """
    name = request.args.get('name', '')
    if not name:
        return jsonify({'error': 'Missing name parameter', 'usage': '/info?name=ANIME_NAME'}), 400
    
    try:
        # Search for the anime first
        results = jikan_search(name, limit=1)
        if not results:
            return jsonify({'error': 'Anime not found', 'name': name}), 404
        
        # Get detailed info
        slug = results[0]['id']
        detail = build_detail(slug)
        
        return jsonify({
            'success': True,
            'anime': detail
        })
    except Exception as e:
        log.error(f'Info error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """API status and health check"""
    return jsonify({
        'status': 'online',
        'version': '2.0-API',
        'ani_cli_installed': ani_cli_ok(),
        'yt_dlp_installed': ytdlp_ok(),
        'endpoints': {
            'download_episode': '/?name=ANIME_NAME&season=SEASON_NUM&episode=EP_NUM&dubbed=yes/no',
            'download_movie': '/?movie=MOVIE_NAME&dubbed=yes/no',
            'search': '/search?q=QUERY',
            'info': '/info?name=ANIME_NAME',
            'status': '/status'
        }
    })

# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("━" * 60)
    print("🎬 ANIME STREAM & DOWNLOAD API")
    print("━" * 60)
    print(f"🌐 Server: http://{HOST}:{PORT}")
    print(f"📁 Downloads: {DOWNLOAD_DIR}")
    print(f"✅ ani-cli: {'Installed' if ani_cli_ok() else '❌ NOT INSTALLED'}")
    print(f"✅ yt-dlp: {'Installed' if ytdlp_ok() else '❌ NOT INSTALLED'}")
    print("\n📚 API ENDPOINTS:")
    print(f"  • Episode: /?name=naruto&season=1&episode=1&dubbed=no")
    print(f"  • Movie:   /?movie=your-name&dubbed=yes")
    print(f"  • Search:  /search?q=naruto")
    print(f"  • Info:    /info?name=naruto")
    print(f"  • Status:  /status")
    print("━" * 60)
    
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
