#!/usr/bin/env python3
"""
Video Processor - Adds black screens to anime videos
Adds black segments at start, middle, and end to comply with YouTube policies
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.black_screen_duration = int(os.getenv('BLACK_SCREEN_DURATION', '5'))
        self.output_dir = Path("processed_videos")
        self.output_dir.mkdir(exist_ok=True)
        
    def add_black_screens(self, input_video: str, output_name: Optional[str] = None) -> Optional[str]:
        """
        Add black screens at start, middle, and end of video
        Returns: Path to processed video
        """
        try:
            input_path = Path(input_video)
            
            if not input_path.exists():
                log.error(f"Input video not found: {input_video}")
                return None
            
            # Get video duration
            duration = self._get_video_duration(str(input_path))
            if not duration:
                log.error("Could not get video duration")
                return None
            
            log.info(f"Processing video: {input_path.name} (Duration: {duration}s)")
            
            # Generate output filename
            if output_name:
                output_file = self.output_dir / output_name
            else:
                output_file = self.output_dir / f"processed_{input_path.name}"
            
            # Create black screen video
            black_screen_file = self._create_black_screen()
            if not black_screen_file:
                log.error("Could not create black screen")
                return None
            
            # Calculate middle position
            middle_position = duration / 2
            
            # Split video into two parts at middle
            first_part = self.output_dir / "temp_first_part.mp4"
            second_part = self.output_dir / "temp_second_part.mp4"
            
            # Extract first part (0 to middle)
            cmd_first = [
                'ffmpeg', '-i', str(input_path),
                '-t', str(middle_position),
                '-c', 'copy',
                '-y', str(first_part)
            ]
            
            # Extract second part (middle to end)
            cmd_second = [
                'ffmpeg', '-i', str(input_path),
                '-ss', str(middle_position),
                '-c', 'copy',
                '-y', str(second_part)
            ]
            
            # Execute splits
            subprocess.run(cmd_first, check=True, capture_output=True)
            subprocess.run(cmd_second, check=True, capture_output=True)
            
            # Create concat file
            concat_file = self.output_dir / "concat_list.txt"
            with open(concat_file, 'w') as f:
                f.write(f"file '{black_screen_file}'\n")  # Start black screen
                f.write(f"file '{first_part.absolute()}'\n")  # First part
                f.write(f"file '{black_screen_file}'\n")  # Middle black screen
                f.write(f"file '{second_part.absolute()}'\n")  # Second part
                f.write(f"file '{black_screen_file}'\n")  # End black screen
            
            # Concatenate all parts
            cmd_concat = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y', str(output_file)
            ]
            
            subprocess.run(cmd_concat, check=True, capture_output=True)
            
            # Cleanup temp files
            self._cleanup_temp_files([black_screen_file, first_part, second_part, concat_file])
            
            log.info(f"✅ Video processed successfully: {output_file}")
            return str(output_file)
            
        except Exception as e:
            log.error(f"Video processing error: {e}")
            return None
    
    def _get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
            
        except Exception as e:
            log.error(f"Error getting video duration: {e}")
            return None
    
    def _create_black_screen(self) -> Optional[str]:
        """Create a black screen video file"""
        try:
            black_screen_path = self.output_dir / "black_screen.mp4"
            
            # Check if already exists
            if black_screen_path.exists():
                return str(black_screen_path)
            
            # Create black screen using ffmpeg
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=black:s=1920x1080:d={self.black_screen_duration}',
                '-f', 'lavfi',
                '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-t', str(self.black_screen_duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                '-y', str(black_screen_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            log.info(f"Created black screen: {black_screen_path}")
            return str(black_screen_path)
            
        except Exception as e:
            log.error(f"Error creating black screen: {e}")
            return None
    
    def _cleanup_temp_files(self, files: list):
        """Clean up temporary files"""
        for file in files:
            try:
                if isinstance(file, (str, Path)):
                    file_path = Path(file)
                    if file_path.exists():
                        file_path.unlink()
            except Exception as e:
                log.warning(f"Could not delete temp file {file}: {e}")
    
    def add_text_overlay(self, video_path: str, text: str, position: str = "bottom") -> Optional[str]:
        """
        Add text overlay to video (optional feature)
        """
        try:
            input_path = Path(video_path)
            output_path = self.output_dir / f"text_overlay_{input_path.name}"
            
            # Position mapping
            positions = {
                "top": "x=(w-text_w)/2:y=50",
                "bottom": "x=(w-text_w)/2:y=h-th-50",
                "center": "x=(w-text_w)/2:y=(h-text_h)/2"
            }
            
            pos = positions.get(position, positions["bottom"])
            
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vf', f"drawtext=text='{text}':fontsize=40:fontcolor=white:{pos}:box=1:boxcolor=black@0.5:boxborderw=5",
                '-c:a', 'copy',
                '-y', str(output_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            log.info(f"Added text overlay: {output_path}")
            return str(output_path)
            
        except Exception as e:
            log.error(f"Text overlay error: {e}")
            return None


# Test the video processor
if __name__ == "__main__":
    processor = VideoProcessor()
    
    print("\n" + "="*60)
    print("VIDEO PROCESSOR TEST")
    print("="*60)
    
    # Test with sample video (you'll need to provide a test video)
    test_video = "test_anime.mp4"
    
    if Path(test_video).exists():
        print(f"\nProcessing video: {test_video}")
        output = processor.add_black_screens(test_video)
        
        if output:
            print(f"✅ SUCCESS: Processed video saved to {output}")
        else:
            print("❌ FAILED: Could not process video")
    else:
        print(f"\n⚠️  Test video not found: {test_video}")
        print("Creating black screen demo...")
        
        # Just test black screen creation
        black_screen = processor._create_black_screen()
        if black_screen:
            print(f"✅ Black screen created: {black_screen}")
        else:
            print("❌ Black screen creation failed")
