#!/usr/bin/env python3
"""
AI Message Generator for YouTube Descriptions
Creates engaging promotional content for anime videos
"""

import os
import requests
import logging
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class MessageGenerator:
    def __init__(self):
        self.nvidia_api_key = os.getenv('NVIDIA_API_KEY')
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
    def generate_youtube_description(self, anime_name: str, season: int, episode: int, synopsis: str = "") -> Dict[str, str]:
        """
        Generate YouTube video description with title, description, tags, and hashtags
        """
        try:
            prompt = f"""Create an engaging YouTube video description for an anime episode.

Anime: {anime_name}
Season: {season}
Episode: {episode}
Synopsis: {synopsis if synopsis else "Action-packed anime episode"}

Generate the following (return as JSON):
1. title: Catchy YouTube title (max 100 chars)
2. description: Engaging description with emojis (200-300 words)
3. tags: 15 relevant tags as array
4. hashtags: 15 trending hashtags as array

The description should:
- Start with attention-grabbing hook
- Include episode highlights
- Add 3-5 relevant emojis
- Encourage engagement (like, share, subscribe)
- Mention it's English dubbed

Example format:
{{
  "title": "Demon Slayer S1E1 - Epic Battle Begins! [English Dub]",
  "description": "🔥 BREAKING: Watch the most intense anime episode... (rest of description)",
  "tags": ["demon slayer", "anime", "english dub", ...],
  "hashtags": ["#DemonSlayer", "#Anime", "#EnglishDub", ...]
}}

Return ONLY valid JSON, no other text."""

            headers = {
                "Authorization": f"Bearer {self.nvidia_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Extract JSON
            import json
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                youtube_content = json.loads(content[json_start:json_end])
                log.info(f"Generated YouTube content for {anime_name} S{season}E{episode}")
                return youtube_content
            else:
                return self._default_content(anime_name, season, episode)
                
        except Exception as e:
            log.error(f"Message generation error: {e}")
            return self._default_content(anime_name, season, episode)
    
    def _default_content(self, anime_name: str, season: int, episode: int) -> Dict[str, str]:
        """Fallback content if AI fails"""
        return {
            "title": f"{anime_name} S{season}E{episode} - English Dubbed [Full Episode]",
            "description": f"""🎬 Watch {anime_name} Season {season} Episode {episode} in English Dub!

🚨 BREAKING: The digital anime landscape is evolving FAST, and staying ahead means watching the best content! 🌍✨ 

This episode features:
✅ High-quality English dubbing
✅ Action-packed scenes
✅ Character development
✅ Epic storytelling

📺 Don't miss out on this incredible episode!

👇 ENGAGE WITH US:
• Like if you enjoyed the episode! 👍
• Share with fellow anime fans! 🔄
• Subscribe for daily anime uploads! 🔔
• Comment your thoughts below! 💭

🎯 We upload 6 NEW anime episodes daily at optimal times!

#Anime #EnglishDub #{anime_name.replace(' ', '')}

---
Disclaimer: This is for entertainment purposes. All rights belong to respective owners.""",
            "tags": [
                anime_name.lower(),
                "anime",
                "english dub",
                "anime english dubbed",
                "full episode",
                "anime 2025",
                "best anime",
                "watch anime",
                "anime series",
                "dubbed anime",
                f"season {season}",
                f"episode {episode}",
                "anime community",
                "anime fans",
                "trending anime"
            ],
            "hashtags": [
                f"#{anime_name.replace(' ', '')}",
                "#Anime",
                "#EnglishDub",
                "#AnimeEnglishDubbed",
                "#AnimeSeries",
                "#WatchAnime",
                "#AnimeLovers",
                "#AnimeCommunity",
                "#TrendingAnime",
                "#Anime2025",
                "#BestAnime",
                "#FullEpisode",
                "#DailyAnime",
                "#AnimeAddict",
                "#MustWatch"
            ]
        }
    
    def generate_viral_message(self, topic: str) -> str:
        """
        Generate viral social media message like the example provided
        """
        try:
            prompt = f"""Create a viral social media post about: {topic}

Style: Engaging, uses emojis, has urgency, encourages engagement
Format: Similar to trending YouTube/social media posts

The message should:
- Start with 🚨 BREAKING NEWS or similar hook
- Use relevant emojis throughout (5-10 total)
- Create sense of urgency/excitement
- Ask engaging questions
- End with call-to-action
- Include relevant hashtags (10-15)

Keep it 150-250 words.

Return just the message text, no JSON."""

            headers = {
                "Authorization": f"Bearer {self.nvidia_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": 800
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            message = result['choices'][0]['message']['content'].strip()
            
            log.info(f"Generated viral message for: {topic}")
            return message
            
        except Exception as e:
            log.error(f"Viral message generation error: {e}")
            return self._default_viral_message(topic)
    
    def _default_viral_message(self, topic: str) -> str:
        """Default viral message template"""
        return f"""🚨 BREAKING NEWS: The anime world is evolving FAST! 🌍✨

{topic} is taking over, and you DON'T want to miss this! 📈

🔥 Did you know? This anime is DOMINATING engagement rates in 2025! 📊 
But here's the kicker: English dubbed content is the FUTURE! 💯

🎬 We're uploading 6 EPIC episodes DAILY! 
⏰ Morning, afternoon, evening, and late night drops!

How are YOU staying ahead of the anime curve? Drop your thoughts below! 👇

Don't forget to:
• 👍 LIKE this video!
• 🔄 SHARE with anime fans!
• 🔔 SUBSCRIBE for daily uploads!
• 💭 COMMENT your favorite moment!

#Anime #EnglishDub #TrendingNow #AnimeLovers #MustWatch #DailyAnime #AnimeCommunity #Viral #AnimeAddict #BestAnime #WatchAnime #Anime2025 #FullEpisode #AnimeSeries #EpicAnime"""


# Test the message generator
if __name__ == "__main__":
    generator = MessageGenerator()
    
    # Test 1: Generate YouTube description
    print("\n" + "="*60)
    print("TEST 1: YouTube Description for Demon Slayer")
    print("="*60)
    
    content = generator.generate_youtube_description(
        anime_name="Demon Slayer",
        season=1,
        episode=1,
        synopsis="Tanjiro begins his journey to become a demon slayer"
    )
    
    print(f"\nTitle: {content['title']}")
    print(f"\nDescription:\n{content['description']}")
    print(f"\nTags: {', '.join(content['tags'][:10])}...")
    print(f"\nHashtags: {' '.join(content['hashtags'][:10])}...")
    
    # Test 2: Generate viral message
    print("\n" + "="*60)
    print("TEST 2: Viral Message")
    print("="*60)
    
    viral_msg = generator.generate_viral_message("One Piece reaches new heights")
    print(f"\n{viral_msg}")
