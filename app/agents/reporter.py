import os
import json
from typing import Dict, List, Any
import asyncio
from datetime import datetime

from app.agents.base import BaseAgent
from app.config.config import config

class ReporterAgent(BaseAgent):
    """
    Agent responsible for generating comprehensive OSINT reports from verified data.
    Creates structured, objective reports with proper citations and evidence.
    """
    
    def __init__(self):
        """Initialize the Reporter Agent."""
        super().__init__("Reporter", config.REPORT_PROMPT_TEMPLATE)
    
    async def generate_report(self, query: str, verified_data: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive OSINT report based on verified data.
        
        Args:
            query: The original user query
            verified_data: The verified data from the Verifier Agent
            
        Returns:
            A formatted Markdown report
        """
        # Generate a report prompt
        prompt = self.format_prompt(
            user_query=query,
            verified_data=json.dumps(verified_data, indent=2)
        )
        
        # Prepare data for the LLM
        # First, let's categorize the data
        categories = {}
        for item in verified_data:
            source_type = item.get("source", "other")
            if source_type not in categories:
                categories[source_type] = []
            categories[source_type].append(item)
        
        # Create sources for citation
        sources = []
        for item in verified_data:
            source = {
                "id": item.get("id", "unknown"),
                "title": item.get("title", item.get("content", "")[:50] + "..."),
                "url": item.get("url", ""),
                "source_name": item.get("source_name", "Unknown Source"),
                "date": item.get("timestamp", "").split("T")[0]
            }
            sources.append(source)
        
        # Create a summary for the LLM
        data_summary = {
            "query": query,
            "categories": {k: len(v) for k, v in categories.items()},
            "source_count": len(sources),
            "sources": sources,
            "verified_data_sample": verified_data[:3] if len(verified_data) > 3 else verified_data,
            "has_media": any("media_path" in item and item["media_path"] for item in verified_data)
        }
        
        # Call LLM to generate the report
        report_messages = [
            {"role": "system", "content": """You are a Report Writer Agent in an OSINT system. Your task is to create a comprehensive, objective report based on verified data.
            
            Format your report in Markdown with the following sections:
            1. Summary - A brief overview of findings
            2. Background - Context and explanation of the topic
            3. Findings - Detailed presentation of the evidence (with subsections as needed)
            4. Analysis - Interpretation of the evidence and patterns
            5. Conclusion - Summary of key insights
            6. Sources - Formatted citations for all sources
            
            Present the facts objectively. Cite sources using [ID] notation and include them in the Sources section.
            Use appropriate formatting like headers, bullet points, and emphasis to make the report readable.
            When discussing evidence, note the verification methods and confidence levels.
            """},
            {"role": "user", "content": f"User Query: {query}\n\nData Summary: {json.dumps(data_summary, indent=2)}\n\nGenerate a complete OSINT report:"}
        ]
        
        report_content = await self.call_llm(report_messages)
        
        # Include any media references if needed
        if data_summary["has_media"]:
            # This would be replaced with actual media embedding in a real implementation
            # For now, we'll just add placeholders in the report
            for item in verified_data:
                if "media_path" in item and item["media_path"]:
                    media_reference = f"\n\n![Media from {item.get('id')}]({item['media_path']})\n"
                    if media_reference not in report_content:
                        # Find a good place to insert it - after the first mention of this source
                        source_mention = f"[{item.get('id')}]"
                        if source_mention in report_content:
                            parts = report_content.split(source_mention, 1)
                            if len(parts) > 1:
                                # Insert after the first paragraph that mentions this source
                                paragraph_end = parts[1].find("\n\n")
                                if paragraph_end > 0:
                                    report_content = parts[0] + source_mention + parts[1][:paragraph_end] + media_reference + parts[1][paragraph_end:]
        
        # Add the report to memory
        self.add_to_memory({
            "query": query,
            "report": report_content,
            "sources_used": len(sources),
            "timestamp": datetime.now().isoformat()
        })
        
        return report_content 