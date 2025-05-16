import os
import json
from typing import Dict, List, Any
import asyncio
from datetime import datetime

from app.agents.base import BaseAgent
from app.config.config import config
from app.tools.search import web_search, social_media_search
from app.tools.media import download_media, extract_metadata

class CollectorAgent(BaseAgent):
    """
    Agent responsible for collecting OSINT data from various sources.
    Gathers information from web searches, social media, and other open sources.
    """
    
    def __init__(self):
        """Initialize the Collector Agent with appropriate tools."""
        super().__init__("Collector", config.COLLECTOR_PROMPT_TEMPLATE)
        
        # Register tools
        self.register_tool("web_search", web_search)
        self.register_tool("social_media_search", social_media_search)
        self.register_tool("download_media", download_media)
        self.register_tool("extract_metadata", extract_metadata)
    
    async def collect(self, query: str) -> List[Dict[str, Any]]:
        """
        Collect OSINT data based on the user query.
        
        Args:
            query: The user's OSINT query
            
        Returns:
            A list of collected data items
        """
        # Generate a collection prompt from the user query
        prompt = self.format_prompt(user_query=query)
        
        # Call LLM to decide what to search for
        messages = [
            {"role": "system", "content": "You are a Collector Agent in an OSINT system. Based on the user query, generate 3-5 specific search terms that would help gather relevant information. Focus on finding evidence related to the query."},
            {"role": "user", "content": f"User Query: {query}\n\nGenerate search terms:"}
        ]
        
        search_terms_response = await self.call_llm(messages)
        
        # Parse the search terms (assuming they're numbered or listed)
        search_terms = []
        for line in search_terms_response.split("\n"):
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("*") or 
                        any(line.startswith(f"{i}.") for i in range(1, 10))):
                term = line.split(" ", 1)[1].strip() if " " in line else line
                search_terms.append(term)
        
        # If no terms were parsed properly, use the query itself
        if not search_terms:
            search_terms = [query]
        
        # Collect data from different sources
        collected_data = []
        
        # Web search
        for term in search_terms:
            try:
                web_results = await self.call_tool("web_search", query=term, max_results=5)
                for result in web_results:
                    collected_data.append({
                        "id": f"web_{len(collected_data)}",
                        "source": "web",
                        "source_name": result.get("source", "Unknown"),
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "content": result.get("snippet", ""),
                        "timestamp": result.get("date", datetime.now().isoformat()),
                        "search_term": term,
                        "metadata": {}
                    })
            except Exception as e:
                print(f"Error in web search for '{term}': {e}")
        
        # Social media search
        for term in search_terms:
            try:
                social_results = await self.call_tool("social_media_search", 
                                                     query=term, 
                                                     platforms=["twitter", "reddit"],
                                                     max_results=5)
                
                for result in social_results:
                    # Download media if present
                    media_path = None
                    media_metadata = {}
                    
                    if "media_url" in result and result["media_url"]:
                        try:
                            media_path = await self.call_tool("download_media", 
                                                           url=result["media_url"])
                            
                            if media_path:
                                media_metadata = await self.call_tool("extract_metadata", 
                                                                    file_path=media_path)
                        except Exception as e:
                            print(f"Error downloading media: {e}")
                    
                    collected_data.append({
                        "id": f"social_{len(collected_data)}",
                        "source": "social_media",
                        "source_name": result.get("platform", "Unknown"),
                        "user": result.get("user", "Unknown"),
                        "url": result.get("url", ""),
                        "content": result.get("text", ""),
                        "timestamp": result.get("date", datetime.now().isoformat()),
                        "search_term": term,
                        "media_path": media_path,
                        "media_metadata": media_metadata,
                        "metadata": {
                            "likes": result.get("likes", 0),
                            "shares": result.get("shares", 0),
                            "comments": result.get("comments", 0)
                        }
                    })
            except Exception as e:
                print(f"Error in social media search for '{term}': {e}")
        
        # Add the collection results to memory
        self.add_to_memory({
            "query": query,
            "search_terms": search_terms,
            "collected_data": collected_data,
            "timestamp": datetime.now().isoformat()
        })
        
        return collected_data 