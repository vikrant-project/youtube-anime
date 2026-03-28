#!/usr/bin/env python3
"""
Database Manager for Anime Automation
Tracks uploaded videos, schedules, and statistics
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class AnimeDatabase:
    def __init__(self, db_path: str = "anime_automation.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            cursor = self.conn.cursor()
            
            # Create uploads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anime_name TEXT NOT NULL,
                    season INTEGER NOT NULL,
                    episode INTEGER NOT NULL,
                    video_id TEXT,
                    video_url TEXT,
                    title TEXT,
                    upload_time TIMESTAMP,
                    status TEXT,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0
                )
            ''')
            
            # Create schedule table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anime_name TEXT NOT NULL,
                    season INTEGER NOT NULL,
                    episode INTEGER NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    uploads_count INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    avg_engagement REAL DEFAULT 0.0
                )
            ''')
            
            self.conn.commit()
            log.info("✅ Database initialized successfully")
            
        except Exception as e:
            log.error(f"Database initialization error: {e}")
    
    def add_upload(self, anime_name: str, season: int, episode: int, 
                   video_id: Optional[str] = None, title: Optional[str] = None, 
                   status: str = "pending") -> int:
        """Add new upload record"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO uploads (anime_name, season, episode, video_id, title, upload_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (anime_name, season, episode, video_id, title, datetime.now(), status))
            
            self.conn.commit()
            upload_id = cursor.lastrowid
            log.info(f"Added upload record: {anime_name} S{season}E{episode}")
            return upload_id
            
        except Exception as e:
            log.error(f"Add upload error: {e}")
            return -1
    
    def update_upload(self, upload_id: int, video_id: str, video_url: str, status: str = "completed"):
        """Update upload record with YouTube info"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE uploads 
                SET video_id = ?, video_url = ?, status = ?, upload_time = ?
                WHERE id = ?
            ''', (video_id, video_url, status, datetime.now(), upload_id))
            
            self.conn.commit()
            log.info(f"Updated upload {upload_id}: {video_id}")
            
        except Exception as e:
            log.error(f"Update upload error: {e}")
    
    def get_recent_uploads(self, limit: int = 10) -> List[Dict]:
        """Get recent uploads"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM uploads 
                ORDER BY upload_time DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            log.error(f"Get uploads error: {e}")
            return []
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """Get statistics for a specific date"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            cursor = self.conn.cursor()
            
            # Get upload count for date
            cursor.execute('''
                SELECT COUNT(*) as count FROM uploads 
                WHERE DATE(upload_time) = ?
            ''', (date,))
            
            upload_count = cursor.fetchone()['count']
            
            return {
                "date": date,
                "uploads": upload_count,
                "status": "success"
            }
            
        except Exception as e:
            log.error(f"Get stats error: {e}")
            return {"date": date, "uploads": 0, "status": "error"}
    
    def schedule_upload(self, anime_name: str, season: int, episode: int, scheduled_time: str) -> int:
        """Add scheduled upload"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO schedule (anime_name, season, episode, scheduled_time)
                VALUES (?, ?, ?, ?)
            ''', (anime_name, season, episode, scheduled_time))
            
            self.conn.commit()
            schedule_id = cursor.lastrowid
            log.info(f"Scheduled upload: {anime_name} S{season}E{episode} at {scheduled_time}")
            return schedule_id
            
        except Exception as e:
            log.error(f"Schedule upload error: {e}")
            return -1
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            log.info("Database connection closed")


# Test database
if __name__ == "__main__":
    db = AnimeDatabase("test_anime.db")
    
    print("\n" + "="*60)
    print("DATABASE TEST")
    print("="*60)
    
    # Test add upload
    print("\n1. Adding test upload...")
    upload_id = db.add_upload("Demon Slayer", 1, 1, "test_video_123", "Test Title")
    print(f"   Upload ID: {upload_id}")
    
    # Test update upload
    print("\n2. Updating upload...")
    db.update_upload(upload_id, "abc123", "https://youtube.com/watch?v=abc123", "completed")
    
    # Test get uploads
    print("\n3. Recent uploads:")
    uploads = db.get_recent_uploads(5)
    for upload in uploads:
        print(f"   {upload['anime_name']} S{upload['season']}E{upload['episode']} - {upload['status']}")
    
    # Test stats
    print("\n4. Daily stats:")
    stats = db.get_daily_stats()
    print(f"   Date: {stats['date']}")
    print(f"   Uploads: {stats['uploads']}")
    
    db.close()
    print("\n✅ Database test complete!")
