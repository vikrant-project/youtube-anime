#!/usr/bin/env python3
"""
Smart Scheduler for Anime Automation
Schedules 6 uploads per day at optimal times
"""

import schedule
import time
import logging
from datetime import datetime
from typing import Callable
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class AnimeScheduler:
    def __init__(self):
        self.upload_times = [
            "06:00",  # Morning - 6 AM
            "12:00",  # Lunch - 12 PM
            "15:00",  # Afternoon - 3 PM
            "18:00",  # Evening - 6 PM
            "21:00",  # Night - 9 PM
            "00:00",  # Midnight - 12 AM
        ]
        self.jobs = []
    
    def schedule_daily_uploads(self, upload_function: Callable):
        """
        Schedule upload function to run at optimal times daily
        """
        log.info("Setting up daily upload schedule...")
        
        for upload_time in self.upload_times:
            schedule.every().day.at(upload_time).do(upload_function)
            log.info(f"  ✅ Scheduled upload at {upload_time}")
        
        log.info(f"\n📅 Total scheduled uploads: {len(self.upload_times)} per day")
    
    def schedule_once(self, upload_function: Callable, time_str: str):
        """
        Schedule a one-time upload
        """
        schedule.every().day.at(time_str).do(upload_function)
        log.info(f"Scheduled one-time upload at {time_str}")
    
    def run(self):
        """
        Start the scheduler (blocking)
        """
        log.info("\n🚀 Scheduler started! Waiting for scheduled times...")
        log.info(f"Next upload: {self._get_next_run_time()}\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _get_next_run_time(self) -> str:
        """
        Get the next scheduled run time
        """
        jobs = schedule.get_jobs()
        if jobs:
            next_run = min(job.next_run for job in jobs)
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "No jobs scheduled"
    
    def get_schedule_info(self) -> dict:
        """
        Get current schedule information
        """
        jobs = schedule.get_jobs()
        return {
            "total_jobs": len(jobs),
            "next_run": self._get_next_run_time(),
            "upload_times": self.upload_times,
            "uploads_per_day": len(self.upload_times)
        }


# Test scheduler
if __name__ == "__main__":
    def test_upload():
        print(f"\n🎬 Upload triggered at {datetime.now().strftime('%H:%M:%S')}")
        print("  Processing anime upload...")
        print("  ✅ Upload complete!\n")
    
    scheduler = AnimeScheduler()
    
    print("\n" + "="*60)
    print("ANIME SCHEDULER TEST")
    print("="*60)
    
    # Show schedule info
    info = scheduler.get_schedule_info()
    print(f"\n📊 Schedule Info:")
    print(f"   Uploads per day: {info['uploads_per_day']}")
    print(f"   Upload times: {', '.join(info['upload_times'])}")
    
    print("\n⚠️  Note: Full scheduler would run continuously")
    print("   For testing, we'll just show the schedule setup.")
    
    # In production, you would:
    # scheduler.schedule_daily_uploads(test_upload)
    # scheduler.run()
