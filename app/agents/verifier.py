import os
import json
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from app.agents.base import BaseAgent
from app.config.config import config
from app.tools.verification import (
    reverse_image_search, 
    geolocate_image, 
    analyze_shadows,
    check_source_reliability,
    check_metadata_consistency
)
from app.logging_config import logger

class VerifierAgent(BaseAgent):
    """
    Agent responsible for verifying the authenticity and reliability of collected OSINT data.
    Performs tasks like geolocation, reverse image search, cross-referencing, etc.
    """
    
    def __init__(self):
        """Initialize the Verifier Agent with appropriate tools."""
        super().__init__("Verifier", config.VERIFICATION_PROMPT_TEMPLATE)
        
        # Register tools
        self.register_tool("reverse_image_search", reverse_image_search)
        self.register_tool("geolocate_image", geolocate_image)
        self.register_tool("analyze_shadows", analyze_shadows)
        self.register_tool("check_source_reliability", check_source_reliability)
        self.register_tool("check_metadata_consistency", check_metadata_consistency)
    
    async def verify(self, query: str, collected_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify the collected OSINT data.
        
        Args:
            query: The original user query
            collected_data: The data collected by the Collector Agent
            
        Returns:
            A list of verified data items
        """
        logger.info(f"VerifierAgent: Verifying data for query: {query}")
        # Generate a verification prompt
        prompt = self.format_prompt(
            user_query=query,
            collected_data=json.dumps(collected_data, indent=2)
        )
        
        verified_data = []
        
        # Process each collected item
        for item in collected_data:
            # Initialize verification metadata
            verification = {
                "verified": False,
                "confidence": 0.0,
                "methods": [],
                "notes": []
            }
            
            try:
                logger.info(f"VerifierAgent: Checking source reliability for {item.get('url', '')}")
                # Check source reliability
                source_reliability = await self.call_tool(
                    "check_source_reliability",
                    source_name=item.get("source_name", "Unknown"),
                    url=item.get("url", "")
                )
                
                verification["methods"].append("source_reliability_check")
                verification["notes"].append(f"Source reliability: {source_reliability.get('reliability', 'Unknown')}")
                
                # If the source is known to be unreliable, skip this item
                if source_reliability.get("reliability") == "unreliable":
                    verification["notes"].append("Source is known to be unreliable. Item rejected.")
                    continue
                
                # For items with media, perform additional verification
                if "media_path" in item and item["media_path"]:
                    logger.info(f"VerifierAgent: Running reverse_image_search for media: {item['media_path']}")
                    # Reverse image search
                    reverse_results = await self.call_tool(
                        "reverse_image_search",
                        image_path=item["media_path"]
                    )
                    
                    verification["methods"].append("reverse_image_search")
                    
                    # Check if the image appears elsewhere
                    if reverse_results.get("matches", []):
                        earliest_match = min(
                            reverse_results.get("matches", []), 
                            key=lambda x: x.get("date", "9999-12-31")
                        )
                        
                        # If the image is older than claimed, flag it
                        if earliest_match.get("date", "") < item.get("timestamp", "").split("T")[0]:
                            verification["notes"].append(
                                f"WARNING: Image appears to be older than claimed. "
                                f"Earliest match: {earliest_match.get('date')} "
                                f"from {earliest_match.get('url')}"
                            )
                        else:
                            verification["notes"].append("Image verified with reverse search.")
                    else:
                        verification["notes"].append("No matches found in reverse image search.")
                    
                    # Attempt to geolocate the image
                    logger.info(f"VerifierAgent: Running geolocate_image for media: {item['media_path']}")
                    geolocate_result = await self.call_tool(
                        "geolocate_image",
                        image_path=item["media_path"]
                    )
                    
                    verification["methods"].append("geolocation")
                    
                    if geolocate_result.get("location"):
                        item["verified_location"] = geolocate_result.get("location")
                        verification["notes"].append(
                            f"Geolocation: {geolocate_result.get('location')} "
                            f"(Confidence: {geolocate_result.get('confidence')})"
                        )
                    
                    # Analyze shadows for time verification
                    logger.info(f"VerifierAgent: Running analyze_shadows for media: {item['media_path']}")
                    shadow_result = await self.call_tool(
                        "analyze_shadows",
                        image_path=item["media_path"],
                        claimed_location=item.get("verified_location"),
                        claimed_time=item.get("timestamp")
                    )
                    
                    verification["methods"].append("shadow_analysis")
                    
                    if shadow_result.get("consistent") is not None:
                        if shadow_result.get("consistent"):
                            verification["notes"].append(
                                f"Shadow analysis confirms claimed time: {item.get('timestamp')}"
                            )
                        else:
                            verification["notes"].append(
                                f"WARNING: Shadow analysis suggests inconsistency with claimed time. "
                                f"Estimated time: {shadow_result.get('estimated_time')}"
                            )
                
                # Check metadata consistency
                logger.info(f"VerifierAgent: Checking metadata consistency for item {item.get('id', 'unknown')}")
                metadata_check = await self.call_tool(
                    "check_metadata_consistency",
                    item=item
                )
                
                verification["methods"].append("metadata_consistency")
                verification["notes"].append(f"Metadata check: {metadata_check.get('result', 'Unknown')}")
                
                # Call LLM to make a final verification decision based on all the evidence
                verification_messages = [
                    {"role": "system", "content": "You are a Verification Agent in an OSINT system. Evaluate the item and verification results to determine if this item should be considered verified. Return a confidence score (0-1) and a brief explanation."},
                    {"role": "user", "content": f"Item: {json.dumps(item, indent=2)}\nVerification Results: {json.dumps(verification, indent=2)}"}
                ]
                
                verification_decision = await self.call_llm(verification_messages)
                
                # Parse the verification decision (assuming JSON-like format)
                try:
                    # Try to find confidence score
                    confidence_line = [line for line in verification_decision.split("\n") 
                                     if "confidence" in line.lower()]
                    if confidence_line:
                        try:
                            confidence_str = confidence_line[0].split(":")[1].strip()
                            # Remove any trailing characters
                            confidence_str = ''.join(c for c in confidence_str if c.isdigit() or c in ['.'])
                            verification["confidence"] = float(confidence_str)
                        except:
                            verification["confidence"] = 0.5
                    
                    # Try to find verification status
                    verified_line = [line for line in verification_decision.split("\n") 
                                   if "verified" in line.lower()]
                    if verified_line:
                        verification["verified"] = "verified: true" in verification_decision.lower() or "true" in verified_line[0].lower()
                    
                    # Add explanation
                    explanation_line = [line for line in verification_decision.split("\n") 
                                      if "explanation" in line.lower()]
                    if explanation_line and len(explanation_line[0].split(":", 1)) > 1:
                        verification["notes"].append(f"Final assessment: {explanation_line[0].split(':', 1)[1].strip()}")
                    elif len(verification_decision.split("\n")) > 0:
                        first_line = verification_decision.split("\n")[0]
                        verification["notes"].append(f"Final assessment: {first_line}")
                except:
                    # If parsing fails, make a conservative decision
                    verification["verified"] = False
                    verification["confidence"] = 0.2
                    verification["notes"].append("Failed to parse verification decision.")
                
                # Add verification metadata to the item
                item["verification"] = verification
                
                # Only include verified items in the results
                if verification["verified"] and verification["confidence"] >= 0.5:
                    verified_data.append(item)
            
            except Exception as e:
                logger.error(f"Error verifying item {item.get('id', 'unknown')}: {e}")
        
        # Add verification results to memory
        self.add_to_memory({
            "query": query,
            "verified_data": verified_data,
            "verification_count": len(verified_data),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"VerifierAgent: Finished verifying data for query: {query}")
        return verified_data 