import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import re
from openai import OpenAI
from dotenv import load_dotenv
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1")
client = OpenAI(api_key=OPENAI_API_KEY)
SOCIAL_SEARCHER_API_KEY = os.getenv("SOCIAL_SEARCHER_API_KEY")

# Mock implementations - in a real system, these would connect to actual APIs
async def web_search(query: str, max_results: int = 10, search_context_size: str = "medium") -> List[Dict[str, Any]]:
    """
    Search the web for information related to the query using OpenAI's web search tool.
    Args:
        query: The search query
        max_results: (Unused, for compatibility)
        search_context_size: "low", "medium", or "high"
    Returns:
        A list of dicts with 'text' and 'citations' (if any)
    """
    print(f"Searching web for: {query} (OpenAI Web Search API)")
    loop = asyncio.get_event_loop()
    def sync_search():
        response = client.responses.create(
            model=LLM_MODEL,
            input=query,
            tools=[{
                "type": "web_search_preview",
                "search_context_size": search_context_size
            }],
        )
        # Parse the response for message content and citations
        text = ""
        citations = []
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type') and item.type == "message" and hasattr(item, 'content') and item.content:
                    content_item = item.content[0]
                    if hasattr(content_item, 'type') and content_item.type == "output_text":
                        text = content_item.text if hasattr(content_item, 'text') else ""
                        if hasattr(content_item, 'annotations') and content_item.annotations:
                            for ann in content_item.annotations:
                                if hasattr(ann, 'type') and ann.type == "url_citation":
                                    citations.append({
                                        "url": ann.url if hasattr(ann, 'url') else None,
                                        "title": ann.title if hasattr(ann, 'title') else None
                                    })
                        break # Assuming one message item with the main content
        elif hasattr(response, 'output_text'): # Fallback for simpler structure
            text = response.output_text
        
        return {"text": text, "citations": citations}
    result = await loop.run_in_executor(None, sync_search)
    return [result]

async def social_media_search(query: str, platforms: Optional[List[str]] = None, max_results: int = 10, lang: str = "en") -> List[Dict[str, Any]]:
    """
    Search social media for posts related to the query using Social Searcher API.
    Args:
        query: The search query
        platforms: List of platforms/networks (e.g., ["twitter", "reddit"])
        max_results: Number of results to return
        lang: Language code (default: "en")
    Returns:
        A list of normalized social media post dicts
    """
    print(f"Searching social media for: {query} on platforms: {platforms} (Social Searcher API)")
    if not SOCIAL_SEARCHER_API_KEY:
        raise RuntimeError("Missing SOCIAL_SEARCHER_API_KEY in environment. Please check your .env file.")
    
    results = []
    loop = asyncio.get_event_loop()

    async def fetch_platform_data(platform: Optional[str]):
        params = {
            "q": query,
            "key": SOCIAL_SEARCHER_API_KEY,
            "limit": max_results,
            "lang": lang,
        }
        if platform:
            params["network"] = platform
        
        url = "https://api.social-searcher.com/v2/search"
        
        try:
            # Run the synchronous requests.get call in a thread pool
            resp = await loop.run_in_executor(None, lambda: requests.get(url, params=params))
            
            if resp.status_code == 200:
                data = resp.json()
                platform_results = []
                for post in data.get("posts", []):
                    platform_results.append({
                        "platform": post.get("network"),
                        "user": post.get("user", {}).get("name"),
                        "url": post.get("url"),
                        "text": post.get("text"),
                        "date": post.get("posted"),
                        "media_url": post.get("image"),
                        "likes": post.get("popularity", {}).get("likes", 0),
                        "shares": post.get("popularity", {}).get("shares", 0),
                        "comments": post.get("popularity", {}).get("comments", 0),
                        "sentiment": post.get("sentiment"),
                        "type": post.get("type"),
                        "lang": post.get("lang"),
                        "raw": post
                    })
                return platform_results
            elif resp.status_code == 405:
                error_message = (
                    f"Social Searcher API error: 405 Method Not Allowed. Response: {resp.text}. "
                    f"This often indicates a permission issue with your API key (SOCIAL_SEARCHER_API_KEY) "
                    f"for the network '{platform}' or the API version. "
                    f"Please verify your key, its permissions, and that the network identifier is correct. "
                    f"The API docs state 'network: web...' and to 'Contact us for the list of supported networks'."
                )
                print(error_message) # Log detailed error
                # Optionally, re-raise or return empty to not break the whole search
                # For now, let's let it raise to make the issue visible
                raise RuntimeError(error_message)

            else:
                raise RuntimeError(f"Social Searcher API error: {resp.status_code} {resp.text} for network: {platform}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed for {platform or 'general search'}: {e}")

    # Create a list of tasks to run concurrently if platforms are specified
    if platforms and isinstance(platforms, list):
        tasks = [fetch_platform_data(p) for p in platforms]
        platform_results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for res_list in platform_results_list:
            if isinstance(res_list, list):
                results.extend(res_list)
            elif isinstance(res_list, Exception):
                # Handle or log exceptions from individual platform fetches if needed
                print(f"Error fetching data for a platform: {res_list}") # Or raise it
    elif platforms is None: # Perform a general search if no specific platforms
        results.extend(await fetch_platform_data(None))
    else: # If platforms is not a list or None (e.g. a single string)
        print(f"Warning: 'platforms' parameter should be a list or None. Received: {platforms}. Treating as a single platform search.")
        results.extend(await fetch_platform_data(str(platforms)))


    return results

# Function to implement in a real system - connects to a proper news API
async def news_search(query: str, days_back: int = 30, max_results: int = 10, search_context_size: str = "medium") -> List[Dict[str, Any]]:
    """
    Search news sources for recent articles related to the query using OpenAI's web search tool.
    Args:
        query: The search query
        days_back: How many days back to search (included in the prompt)
        max_results: (Unused, for compatibility)
        search_context_size: "low", "medium", or "high"
    Returns:
        A list of dicts with 'text' and 'citations' (if any)
    """
    print(f"Searching news for: {query} (OpenAI Web Search API)")
    loop = asyncio.get_event_loop()
    def sync_search():
        # Craft a news-specific prompt
        news_prompt = (
            f"Find recent news articles from reputable sources (such as Reuters, Al Jazeera, Haaretz, BBC, The Guardian, New York Times, etc.) "
            f"from the last {days_back} days about: {query}. "
            f"List the most relevant articles with their sources and dates."
        )
        response = client.responses.create(
            model=LLM_MODEL,
            tools=[{
                "type": "web_search_preview",
                "search_context_size": search_context_size
            }],
            input=news_prompt
        )
        # Find the message output item
        text = ""
        citations = []
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if hasattr(item, 'type') and item.type == "message" and hasattr(item, 'content') and item.content:
                    content_item = item.content[0]
                    if hasattr(content_item, 'type') and content_item.type == "output_text":
                        text = content_item.text if hasattr(content_item, 'text') else ""
                        if hasattr(content_item, 'annotations') and content_item.annotations:
                            for ann in content_item.annotations:
                                if hasattr(ann, 'type') and ann.type == "url_citation":
                                    citations.append({
                                        "url": ann.url if hasattr(ann, 'url') else None,
                                        "title": ann.title if hasattr(ann, 'title') else None
                                    })
                        break # Assuming one message item with the main content
        elif hasattr(response, 'output_text'): # Fallback for simpler structure
            text = response.output_text

        return {"text": text, "citations": citations}
    result = await loop.run_in_executor(None, sync_search)
    return [result] 