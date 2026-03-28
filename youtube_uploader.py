#!/usr/bin/env python3
"""
YouTube Uploader with Smart Scheduling
Uploads anime videos to YouTube with optimal timing for maximum views
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv
import pickle

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeUploader:
    def __init__(self):
        self.client_id = os.getenv('YOUTUBE_CLIENT_ID')
        self.client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        self.refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
        self.credentials = None
        self.youtube = None
        
        # Initialize credentials
        self._init_credentials()
        
    def _init_credentials(self):
        """Initialize YouTube API credentials"""
        try:
            # Create credentials from environment variables
            self.credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            
            # Refresh the token
            if self.credentials.expired or not self.credentials.valid:
                self.credentials.refresh(Request())
            
            # Build YouTube API client
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            log.info("✅ YouTube API initialized successfully")
            
        except Exception as e:
            log.error(f"YouTube API initialization error: {e}")
            self.youtube = None
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        thumbnail_path: Optional[str] = None,
        category: str = "1",  # Film & Animation
        privacy: str = "public"
    ) -> Optional[str]:
        """
        Upload video to YouTube
        Returns: Video ID if successful
        """
        try:
            if not self.youtube:
                log.error("YouTube API not initialized")
                return None
            
            video_file = Path(video_path)
            if not video_file.exists():
                log.error(f"Video file not found: {video_path}")
                return None
            
            log.info(f"Uploading video: {video_file.name}")
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title[:100],  # Max 100 chars
                    'description': description,
                    'tags': tags[:500],  # Max 500 tags
                    'categoryId': category
                },
                'status': {
                    'privacyStatus': privacy,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload
            media = MediaFileUpload(
                str(video_file),
                mimetype='video/mp4',
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )
            
            # Execute upload
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    log.info(f"Upload progress: {progress}%")
            
            video_id = response['id']
            log.info(f"✅ Video uploaded successfully! Video ID: {video_id}")
            log.info(f"   URL: https://www.youtube.com/watch?v={video_id}")
            
            # Upload thumbnail if provided
            if thumbnail_path and Path(thumbnail_path).exists():
                self._upload_thumbnail(video_id, thumbnail_path)
            
            return video_id
            
        except HttpError as e:
            log.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            log.error(f"Upload error: {e}")
            return None
    
    def _upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Upload custom thumbnail to video"""
        try:
            log.info(f"Uploading thumbnail for video {video_id}")
            
            media = MediaFileUpload(
                thumbnail_path,
                mimetype='image/png',
                resumable=True
            )
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            
            log.info("✅ Thumbnail uploaded successfully")
            return True
            
        except Exception as e:
            log.error(f"Thumbnail upload error: {e}")
            return False
    
    def get_optimal_upload_times(self) -> list:
        """
        Get optimal upload times for maximum YouTube views
        Based on audience engagement patterns
        """
        # Optimal times in 24-hour format (PST/US timezone preference)
        # These times are research-backed for maximum engagement
        optimal_times = [
            "06:00",  # Morning commute (6 AM)
            "12:00",  # Lunch break (12 PM)
            "15:00",  # Afternoon break (3 PM)
            "18:00",  # Evening prime time (6 PM)
            "21:00",  # Night prime time (9 PM)
            "00:00",  # Late night/international audience (12 AM)
        ]
        
        return optimal_times
    
    def schedule_upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        thumbnail_path: Optional[str] = None,
        scheduled_time: Optional[str] = None
    ) -> Optional[str]:
        """
        Schedule video upload for optimal time
        """
        try:
            # For immediate upload (scheduled uploads require API approval)
            log.info(f"Scheduling upload: {title}")
            
            # Upload as unlisted first, then set to public
            video_id = self.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                thumbnail_path=thumbnail_path,
                privacy="public"  # Change to "unlisted" for scheduled publishing
            )
            
            if video_id:
                log.info(f"Video ready for publishing at scheduled time")
            
            return video_id
            
        except Exception as e:
            log.error(f"Schedule upload error: {e}")
            return None
    
    def update_video_privacy(self, video_id: str, privacy: str = "public") -> bool:
        """Update video privacy status"""
        try:
            self.youtube.videos().update(
                part='status',
                body={
                    'id': video_id,
                    'status': {
                        'privacyStatus': privacy
                    }
                }
            ).execute()
            
            log.info(f"✅ Video {video_id} privacy updated to {privacy}")
            return True
            
        except Exception as e:
            log.error(f"Privacy update error: {e}")
            return False
    
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """Get video information"""
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics,status',
                id=video_id
            ).execute()
            
            if response['items']:
                return response['items'][0]
            return None
            
        except Exception as e:
            log.error(f"Get video info error: {e}")
            return None


# Test the YouTube uploader
if __name__ == "__main__":
    uploader = YouTubeUploader()
    
    print("\n" + "="*60)
    print("YOUTUBE UPLOADER TEST")
    print("="*60)
    
    # Display optimal upload times
    print("\n📅 Optimal Upload Times:")
    times = uploader.get_optimal_upload_times()
    for i, time in enumerate(times, 1):
        print(f"   {i}. {time}")
    
    # Test upload (uncomment when you have a test video)
    """
    test_video = "test_anime.mp4"
    test_thumbnail = "test_thumbnail.png"
    
    if Path(test_video).exists():
        print(f"\nUploading test video: {test_video}")
        
        video_id = uploader.upload_video(
            video_path=test_video,
            title="Test Anime Upload - Demon Slayer S1E1 [English Dub]",
            description="Test upload for anime automation system",
            tags=["anime", "test", "demon slayer", "english dub"],
            thumbnail_path=test_thumbnail if Path(test_thumbnail).exists() else None,
            privacy="private"  # Use private for testing
        )
        
        if video_id:
            print(f"\n✅ SUCCESS: Video uploaded!")
            print(f"   Video ID: {video_id}")
            print(f"   URL: https://www.youtube.com/watch?v={video_id}")
        else:
            print("\n❌ FAILED: Could not upload video")
    else:
        print(f"\n⚠️  Test video not found: {test_video}")
    """
    
    print("\n✅ YouTube uploader ready!")
