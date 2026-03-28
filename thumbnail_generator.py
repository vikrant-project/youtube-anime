#!/usr/bin/env python3
"""
AI Thumbnail Generator using NVIDIA Stable Diffusion 3 Medium
Generates anime-style thumbnails for YouTube videos
"""

import os
import requests
import base64
import logging
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class ThumbnailGenerator:
    def __init__(self):
        self.api_key = os.getenv('NVIDIA_IMAGE_API_KEY')
        self.api_url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"
        self.output_dir = Path("thumbnails")
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_thumbnail(self, anime_name: str, episode: int, season: int = 1) -> Optional[str]:
        """
        Generate anime thumbnail using Stable Diffusion 3
        Returns: Path to saved thumbnail image
        """
        try:
            # Create AI prompt for anime thumbnail
            prompt = self._create_prompt(anime_name, episode, season)
            
            log.info(f"Generating thumbnail for {anime_name} S{season}E{episode}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            
            payload = {
                "prompt": prompt,
                "cfg_scale": 5,
                "aspect_ratio": "16:9",
                "seed": 0,
                "steps": 50,
                "negative_prompt": "low quality, blurry, distorted, watermark, text, logo, bad anatomy"
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Save the generated image
            if 'image' in result:
                image_data = base64.b64decode(result['image'])
            elif 'artifacts' in result and len(result['artifacts']) > 0:
                image_data = base64.b64decode(result['artifacts'][0]['base64'])
            else:
                log.error(f"Unexpected API response format: {result.keys()}")
                return None
            
            # Save thumbnail
            filename = f"{anime_name.replace(' ', '_')}_S{season}E{episode}_thumbnail.png"
            filepath = self.output_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            log.info(f"Thumbnail saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            log.error(f"Thumbnail generation error: {e}")
            return None
    
    def _create_prompt(self, anime_name: str, episode: int, season: int) -> str:
        """
        Create optimized prompt for anime thumbnail
        """
        prompts = [
            f"Anime style thumbnail for {anime_name}, vibrant colors, dynamic action pose, high quality anime art, professional YouTube thumbnail, epic composition, dramatic lighting",
            f"Epic anime scene from {anime_name}, cinematic composition, vibrant colors, detailed character art, action-packed moment, high quality digital art, YouTube thumbnail style",
            f"Professional anime thumbnail featuring {anime_name}, bold colors, dynamic character pose, detailed background, eye-catching composition, high resolution anime art",
            f"{anime_name} anime poster style, dramatic scene, vibrant color palette, detailed anime characters, epic background, professional quality, YouTube thumbnail format"
        ]
        
        # Rotate through prompts based on episode number
        return prompts[episode % len(prompts)]
    
    def generate_custom_thumbnail(self, custom_prompt: str, filename: str) -> Optional[str]:
        """
        Generate thumbnail with custom prompt
        """
        try:
            log.info(f"Generating custom thumbnail: {filename}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            
            payload = {
                "prompt": custom_prompt,
                "cfg_scale": 5,
                "aspect_ratio": "16:9",
                "seed": 0,
                "steps": 50,
                "negative_prompt": "low quality, blurry, distorted, watermark"
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Save the generated image
            if 'image' in result:
                image_data = base64.b64decode(result['image'])
            elif 'artifacts' in result and len(result['artifacts']) > 0:
                image_data = base64.b64decode(result['artifacts'][0]['base64'])
            else:
                return None
            
            filepath = self.output_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            log.info(f"Custom thumbnail saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            log.error(f"Custom thumbnail generation error: {e}")
            return None


# Test the thumbnail generator
if __name__ == "__main__":
    generator = ThumbnailGenerator()
    
    # Test 1: Generate thumbnail for popular anime
    print("\nGenerating thumbnail for Demon Slayer...")
    thumbnail_path = generator.generate_thumbnail("Demon Slayer", episode=1, season=1)
    
    if thumbnail_path:
        print(f"✅ Thumbnail generated successfully: {thumbnail_path}")
    else:
        print("❌ Thumbnail generation failed")
    
    # Test 2: Custom thumbnail
    print("\nGenerating custom anime thumbnail...")
    custom_path = generator.generate_custom_thumbnail(
        "Epic anime battle scene, vibrant colors, dynamic action, high quality",
        "custom_test.png"
    )
    
    if custom_path:
        print(f"✅ Custom thumbnail generated: {custom_path}")
    else:
        print("❌ Custom thumbnail failed")
