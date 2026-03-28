#!/usr/bin/env python3
"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ANIME AUTOMATION SYSTEM - MAIN ORCHESTRATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
 Complete automation pipeline:
 1. AI searches for anime (NVIDIA API)
 2. Downloads anime via ani-cli API
 3. Generates AI thumbnail (Stable Diffusion 3)
 4. Generates AI promotional content
 5. Processes video (adds black screens)
 6. Uploads to YouTube at optimal times
 7. Auto-push to GitHub
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import logging
import requests
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

# Import our modules
from ai_anime_search import AIAnimeSearch
from thumbnail_generator import ThumbnailGenerator
from message_generator import MessageGenerator
from video_processor import VideoProcessor
from youtube_uploader import YouTubeUploader
from database import AnimeDatabase
from scheduler import AnimeScheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('anime_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

class AnimeAutomation:
    def __init__(self):
        self.ai_search = AIAnimeSearch()
        self.thumbnail_gen = ThumbnailGenerator()
        self.message_gen = MessageGenerator()
        self.video_processor = VideoProcessor()
        self.youtube_uploader = YouTubeUploader()
        self.database = AnimeDatabase()
        self.scheduler = AnimeScheduler()
        
        self.anime_api_url = "http://localhost:9079"
        self.downloads_dir = Path.home() / "anime_downloads"
        
        log.info("━" * 60)
        log.info("🎬 ANIME AUTOMATION SYSTEM INITIALIZED")
        log.info("━" * 60)
    
    def process_and_upload_anime(self, user_query: str) -> Dict:
        """
        Complete pipeline: Search -> Download -> Process -> Upload
        """
        try:
            log.info(f"\n{'='*60}")
            log.info(f"🚀 STARTING NEW AUTOMATION: {user_query}")
            log.info(f"{'='*60}\n")
            
            # Step 1: AI Search
            log.info("STEP 1: 🤖 AI Anime Search")
            anime_info = self.ai_search.search_anime_with_ai(user_query)
            
            anime_name = anime_info.get('anime_name', 'Unknown')
            season = anime_info.get('season', 1)
            episode = anime_info.get('episode', 1)
            dubbed = anime_info.get('dubbed', True)
            
            log.info(f"  ✅ Found: {anime_name} S{season}E{episode} (Dubbed: {dubbed})")
            
            # Step 2: Download Anime
            log.info("\nSTEP 2: 📥 Downloading Anime")
            video_path = self._download_anime(anime_name, season, episode, dubbed)
            
            if not video_path:
                log.error("  ❌ Download failed")
                return {"success": False, "error": "Download failed"}
            
            log.info(f"  ✅ Downloaded: {video_path}")
            
            # Step 3: Generate Thumbnail
            log.info("\nSTEP 3: 🎨 Generating AI Thumbnail")
            thumbnail_path = self.thumbnail_gen.generate_thumbnail(anime_name, episode, season)
            
            if thumbnail_path:
                log.info(f"  ✅ Thumbnail: {thumbnail_path}")
            else:
                log.warning("  ⚠️  Thumbnail generation failed, continuing without it")
            
            # Step 4: Generate YouTube Content
            log.info("\nSTEP 4: 📝 Generating YouTube Description")
            youtube_content = self.message_gen.generate_youtube_description(
                anime_name, season, episode
            )
            
            log.info(f"  ✅ Title: {youtube_content['title']}")
            
            # Step 5: Process Video (Add Black Screens)
            log.info("\nSTEP 5: 🎬 Processing Video")
            processed_video = self.video_processor.add_black_screens(video_path)
            
            if not processed_video:
                log.warning("  ⚠️  Processing failed, using original video")
                processed_video = video_path
            else:
                log.info(f"  ✅ Processed: {processed_video}")
            
            # Step 6: Upload to YouTube
            log.info("\nSTEP 6: 📤 Uploading to YouTube")
            video_id = self.youtube_uploader.upload_video(
                video_path=processed_video,
                title=youtube_content['title'],
                description=youtube_content['description'],
                tags=youtube_content['tags'],
                thumbnail_path=thumbnail_path,
                privacy="public"
            )
            
            if video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                log.info(f"  ✅ Uploaded! Video URL: {video_url}")
                
                # Save to database
                upload_id = self.database.add_upload(
                    anime_name, season, episode, video_id, youtube_content['title'], "completed"
                )
                self.database.update_upload(upload_id, video_id, video_url, "completed")
                
                return {
                    "success": True,
                    "anime_name": anime_name,
                    "season": season,
                    "episode": episode,
                    "video_id": video_id,
                    "video_url": video_url,
                    "title": youtube_content['title']
                }
            else:
                log.error("  ❌ Upload failed")
                return {"success": False, "error": "Upload failed"}
            
        except Exception as e:
            log.error(f"Pipeline error: {e}")
            return {"success": False, "error": str(e)}
    
    def _download_anime(self, anime_name: str, season: int, episode: int, dubbed: bool = True) -> Optional[str]:
        """
        Download anime using the API
        """
        try:
            # Build API request
            params = {
                'name': anime_name,
                'season': season,
                'episode': episode,
                'dubbed': 'yes' if dubbed else 'no'
            }
            
            # Make request to anime API
            response = requests.get(self.anime_api_url, params=params, timeout=300)
            
            if response.status_code == 200:
                # Save video file
                filename = f"{anime_name.replace(' ', '_')}_S{season}E{episode}.mp4"
                filepath = self.downloads_dir / filename
                
                self.downloads_dir.mkdir(exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return str(filepath)
            else:
                log.error(f"Download API error: {response.status_code}")
                return None
                
        except Exception as e:
            log.error(f"Download error: {e}")
            return None
    
    def start_auto_mode(self):
        """
        Start automatic mode - 6 uploads per day at optimal times
        """
        log.info("\n🤖 STARTING AUTO MODE")
        log.info("   📅 6 uploads per day at optimal times")
        
        # Get popular anime list
        popular_anime = [
            "Demon Slayer",
            "Attack on Titan",
            "My Hero Academia",
            "Jujutsu Kaisen",
            "One Piece",
            "Naruto"
        ]
        
        anime_index = 0
        episode = 1
        
        def scheduled_upload():
            nonlocal anime_index, episode
            
            anime = popular_anime[anime_index % len(popular_anime)]
            query = f"{anime} episode {episode} English dubbed"
            
            log.info(f"\n⏰ SCHEDULED UPLOAD TRIGGERED: {query}")
            result = self.process_and_upload_anime(query)
            
            if result.get('success'):
                log.info(f"✅ Auto upload successful: {result['video_url']}")
            else:
                log.error(f"❌ Auto upload failed: {result.get('error')}")
            
            # Move to next anime/episode
            anime_index += 1
            if anime_index % len(popular_anime) == 0:
                episode += 1
        
        # Schedule uploads
        self.scheduler.schedule_daily_uploads(scheduled_upload)
        
        # Show schedule info
        info = self.scheduler.get_schedule_info()
        log.info(f"\n📊 Schedule Configuration:")
        log.info(f"   Uploads per day: {info['uploads_per_day']}")
        log.info(f"   Times: {', '.join(info['upload_times'])}")
        log.info(f"   Next run: {info['next_run']}")
        
        # Start scheduler
        self.scheduler.run()
    
    def test_pipeline(self):
        """
        Test the complete pipeline with a single anime
        """
        log.info("\n🧪 TESTING PIPELINE")
        
        test_query = "Demon Slayer season 1 episode 1 English dubbed"
        result = self.process_and_upload_anime(test_query)
        
        if result.get('success'):
            log.info("\n✅ PIPELINE TEST SUCCESSFUL!")
            log.info(f"   Video URL: {result['video_url']}")
        else:
            log.error("\n❌ PIPELINE TEST FAILED!")
            log.error(f"   Error: {result.get('error')}")
        
        return result


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Anime Automation System')
    parser.add_argument('--mode', choices=['test', 'auto', 'single'], default='test',
                       help='Operation mode: test, auto, or single')
    parser.add_argument('--query', type=str, help='Anime query for single mode')
    
    args = parser.parse_args()
    
    automation = AnimeAutomation()
    
    if args.mode == 'test':
        # Test mode
        automation.test_pipeline()
        
    elif args.mode == 'auto':
        # Auto mode - 6 uploads per day
        automation.start_auto_mode()
        
    elif args.mode == 'single':
        # Single upload mode
        if not args.query:
            log.error("Error: --query required for single mode")
            sys.exit(1)
        
        result = automation.process_and_upload_anime(args.query)
        
        if result.get('success'):
            log.info(f"\n✅ SUCCESS: {result['video_url']}")
        else:
            log.error(f"\n❌ FAILED: {result.get('error')}")


if __name__ == "__main__":
    print("""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     🎬 ANIME AUTOMATION SYSTEM
     AI-Powered YouTube Anime Upload Automation
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
     Usage:
       python main.py --mode test      # Test pipeline
       python main.py --mode auto      # Auto mode (6/day)
       python main.py --mode single --query "Naruto episode 1"
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    main()
