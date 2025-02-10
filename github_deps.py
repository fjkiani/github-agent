from dataclasses import dataclass
import httpx
from pydantic_ai.models.openai import OpenAIModel
from typing import Dict, Any
import json
from pathlib import Path
import os

@dataclass
class GitHubDeps:
    client: httpx.AsyncClient
    github_token: str | None = None
    model: OpenAIModel | None = None
    _cache_file: str = ".github_cache.json"
    _cache: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize cache from file if it exists"""
        self._cache = {}
        if Path(self._cache_file).exists():
            try:
                with open(self._cache_file, 'r') as f:
                    self._cache = json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")

    def get_headers(self) -> dict:
        """Get GitHub API headers with correct token format"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Agent'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        return headers

    def get_from_cache(self, key: str) -> Any:
        """Get value from cache"""
        return self._cache.get(key)

    def save_to_cache(self, key: str, value: Any):
        """Save value to cache and persist to file"""
        self._cache[key] = value
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(self._cache, f)
        except Exception as e:
            print(f"Error saving cache: {e}")

    async def get_repo_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository data with caching"""
        cache_key = f"repo_{owner}_{repo}"
        
        # Check cache first
        cached = self.get_from_cache(cache_key)
        if cached:
            print("Using cached repo data")
            return cached

        # Debug token
        print("\nGitHub Token Debug:")
        print(f"- Token exists: {'Yes' if self.github_token else 'No'}")
        if self.github_token:
            print(f"- Token starts with: {self.github_token[:10]}...")
            print(f"- Token length: {len(self.github_token)}")

        # Make API call if not in cache
        headers = self.get_headers()
        api_url = f'https://api.github.com/repos/{owner}/{repo}'
        print(f"\nMaking GitHub API call:")
        print(f"- URL: {api_url}")
        print(f"- Headers: {headers}")
        
        try:
            # Try unauthenticated first for public repos
            basic_headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'GitHub-Agent'
            }
            print("\nTrying unauthenticated request first...")
            response = await self.client.get(api_url, headers=basic_headers)
            print(f"- Status: {response.status_code}")
            
            if response.status_code != 200 and self.github_token:
                print("\nTrying with authentication...")
                response = await self.client.get(api_url, headers=headers)
                print(f"- Status: {response.status_code}")
            
            print(f"- Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                self.save_to_cache(cache_key, data)
                return data
            else:
                print(f"Error response: {response.text}")
                return None
            
        except Exception as e:
            print(f"Exception during API call: {str(e)}")
            return None 