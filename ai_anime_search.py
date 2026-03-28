#!/usr/bin/env python3
"""
AI-Powered Anime Search using NVIDIA API
Automatically finds anime name, season, episode, and filters for English dubbed
"""

import os
import requests
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class AIAnimeSearch:
    def __init__(self):
        self.nvidia_api_key = os.getenv('NVIDIA_API_KEY')
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
    def search_anime_with_ai(self, user_query: str) -> Dict:
        """
        Use AI to parse and extract anime information from user query
        Returns: {anime_name, season, episode, dubbed}
        """
        try:
            prompt = f"""You are an anime expert assistant. Extract anime information from the user's query.

User Query: "{user_query}"

Extract and return ONLY a JSON object with these fields:
- anime_name: The anime title (official name)
- season: Season number (default: 1)
- episode: Episode number (if mentioned, otherwise: 1)
- dubbed: true if English dubbed is requested, false otherwise
- genres: List of anime genres if mentioned
- description: Brief description if user wants specific type

Example output:
{{"anime_name": "Naruto", "season": 1, "episode": 5, "dubbed": true, "genres": ["action", "adventure"], "description": "ninja anime"}}

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
                "temperature": 0.2,
                "max_tokens": 500
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                anime_info = json.loads(content[json_start:json_end])
                log.info(f"AI extracted anime info: {anime_info}")
                return anime_info
            else:
                log.error("No JSON found in AI response")
                return self._default_response(user_query)
                
        except Exception as e:
            log.error(f"AI search error: {e}")
            return self._default_response(user_query)
    
    def _default_response(self, query: str) -> Dict:
        """Fallback response if AI fails"""
        return {
            "anime_name": query,
            "season": 1,
            "episode": 1,
            "dubbed": True,
            "genres": [],
            "description": ""
        }
    
    def find_anime_recommendations(self, genre: str, count: int = 5) -> List[Dict]:
        """
        Get AI recommendations for anime based on genre
        """
        try:
            prompt = f"""List {count} popular English dubbed anime in the {genre} genre.

Return ONLY a JSON array of objects with these fields:
- anime_name: Official anime title
- description: One sentence description
- popularity: Rating 1-10

Example:
[{{"anime_name": "My Hero Academia", "description": "Students train to become heroes", "popularity": 9}}]

Return ONLY valid JSON array, no other text."""

            headers = {
                "Authorization": f"Bearer {self.nvidia_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta/llama-3.1-8b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 1000
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Extract JSON array
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                recommendations = json.loads(content[json_start:json_end])
                log.info(f"AI recommended {len(recommendations)} anime")
                return recommendations
            else:
                return []
                
        except Exception as e:
            log.error(f"AI recommendations error: {e}")
            return []


# Test the AI search
if __name__ == "__main__":
    ai_search = AIAnimeSearch()
    
    # Test 1: Search with natural language
    result = ai_search.search_anime_with_ai("I want to watch Demon Slayer season 2 episode 5 in English dub")
    print("\nTest 1 - Natural Language Search:")
    print(json.dumps(result, indent=2))
    
    # Test 2: Simple search
    result = ai_search.search_anime_with_ai("Attack on Titan")
    print("\nTest 2 - Simple Search:")
    print(json.dumps(result, indent=2))
    
    # Test 3: Get recommendations
    recommendations = ai_search.find_anime_recommendations("action", count=3)
    print("\nTest 3 - Action Anime Recommendations:")
    print(json.dumps(recommendations, indent=2))
