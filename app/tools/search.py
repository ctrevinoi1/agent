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
            tools=[{
                "type": "web_search_preview",
                "search_context_size": search_context_size
            }],
            input=query
        )
        # Find the message output item
        for item in response.output:
            if item["type"] == "message":
                content = item["content"][0]
                text = content.get("text", "")
                citations = []
                for ann in content.get("annotations", []):
                    if ann.get("type") == "url_citation":
                        citations.append({
                            "url": ann.get("url"),
                            "title": ann.get("title")
                        })
                return {"text": text, "citations": citations}
        return {"text": "", "citations": []}
    result = await loop.run_in_executor(None, sync_search)
    return [result]

async def social_media_search(
    query: str,
    platforms: List[str] = ["twitter"],
    max_results: int = 10,
    lang: str = "en"
) -> List[Dict[str, Any]]:
    """
    Search social media platforms for posts related to the query using Social Searcher API.

    Args:
        query: The search query
        platforms: List of platforms to search (e.g., twitter, facebook, instagram, etc.)
        max_results: Maximum number of results to return
        lang: Language code (default 'en')

    Returns:
        A list of social media posts
    """
    print(f"Searching social media for: {query} on platforms: {platforms} (Social Searcher API)")

    if not SOCIAL_SEARCHER_API_KEY:
        raise ValueError("SOCIAL_SEARCHER_API_KEY not set in environment.")

    # Social Searcher API only allows one network per request, so aggregate results
    results = []
    for platform in platforms:
        params = {
            "q": query,
            "key": SOCIAL_SEARCHER_API_KEY,
            "network": platform,
            "limit": max_results,
            "lang": lang
        }
        # Social Searcher API is synchronous, so run in executor
        def fetch():
            resp = requests.get("https://api.social-searcher.com/v2/search", params=params)
            resp.raise_for_status()
            return resp.json()
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, fetch)
        posts = data.get("posts", [])
        for post in posts:
            results.append({
                "platform": platform,
                "user": post.get("user", {}).get("name"),
                "url": post.get("url"),
                "text": post.get("text"),
                "date": post.get("date"),
                "media_url": post.get("media", [None])[0] if post.get("media") else None,
                "likes": post.get("likes"),
                "shares": post.get("shares"),
                "comments": post.get("comments"),
                "sentiment": post.get("sentiment")
            })
        # Optionally, break if enough results
        if len(results) >= max_results:
            break
    return results[:max_results]

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
        for item in response.output:
            if item["type"] == "message":
                content = item["content"][0]
                text = content.get("text", "")
                citations = []
                for ann in content.get("annotations", []):
                    if ann.get("type") == "url_citation":
                        citations.append({
                            "url": ann.get("url"),
                            "title": ann.get("title")
                        })
                return {"text": text, "citations": citations}
        return {"text": "", "citations": []}
    result = await loop.run_in_executor(None, sync_search)
    return [result] 