import os
import json
from typing import Dict, List, Any, Optional
import asyncio

from app.config.config import config
from app.agents.collector import CollectorAgent
from app.agents.verifier import VerifierAgent
from app.agents.reporter import ReporterAgent
from app.agents.ethical_filter import EthicalFilterAgent
from app.logging_config import logger

class Orchestrator:
    """
    The main orchestrator that manages the CAMEL agent workflow.
    Coordinates communication between agents and handles the data flow.
    """
    
    def __init__(self):
        """Initialize the orchestrator and its agents."""
        self.collector_agent = CollectorAgent()
        self.verifier_agent = VerifierAgent()
        self.reporter_agent = ReporterAgent()
        self.ethical_filter_agent = EthicalFilterAgent()
        
        # Create data directories if they don't exist
        os.makedirs(config.SAVE_MEDIA_PATH, exist_ok=True)
        
        # Workflow state
        self.current_query = ""
        self.collected_data = []
        self.verified_data = []
        self.draft_report = ""
        self.final_report = ""
        
    async def process_query(self, query: str, callback=None) -> str:
        """
        Process a user query through the entire CAMEL agent workflow.
        
        Args:
            query: The user's OSINT query
            callback: Optional callback function to receive status updates
            
        Returns:
            The final report as a string
        """
        self.current_query = query
        logger.info(f"Processing query: {query}")
        
        # Step 1: Collection
        if callback:
            await callback("Starting data collection...")
        logger.info("Invoking CollectorAgent for data collection.")
        self.collected_data = await self.collector_agent.collect(query)
        logger.info(f"CollectorAgent collected {len(self.collected_data)} items.")
        if callback:
            await callback(f"Collection complete. Found {len(self.collected_data)} items.")
        
        # Step 2: Verification
        if callback:
            await callback("Starting verification process...")
        logger.info("Invoking VerifierAgent for data verification.")
        self.verified_data = await self.verifier_agent.verify(
            query, self.collected_data
        )
        logger.info(f"VerifierAgent verified {len(self.verified_data)} items.")
        if callback:
            await callback(f"Verification complete. {len(self.verified_data)} items verified.")
        
        # Step 3: Report writing
        if callback:
            await callback("Generating report...")
        logger.info("Invoking ReporterAgent to generate report.")
        self.draft_report = await self.reporter_agent.generate_report(
            query, self.verified_data
        )
        logger.info("ReporterAgent generated draft report.")
        
        # Step 4: Ethical filtering
        if callback:
            await callback("Applying ethical filter...")
        logger.info("Invoking EthicalFilterAgent for ethical filtering.")
        self.final_report = await self.ethical_filter_agent.filter(
            self.draft_report
        )
        logger.info("EthicalFilterAgent produced final report.")
        if callback:
            await callback("Report complete.")
        
        return self.final_report
    
    def get_workflow_state(self) -> Dict[str, Any]:
        """Get the current state of the workflow."""
        return {
            "query": self.current_query,
            "collection_status": len(self.collected_data),
            "verification_status": len(self.verified_data),
            "report_status": bool(self.draft_report),
            "complete": bool(self.final_report)
        }
    
    def get_collected_data(self) -> List[Dict[str, Any]]:
        """Get the collected data items."""
        return self.collected_data
    
    def get_verified_data(self) -> List[Dict[str, Any]]:
        """Get the verified data items."""
        return self.verified_data
    
    def get_draft_report(self) -> str:
        """Get the draft report."""
        return self.draft_report
    
    def get_final_report(self) -> str:
        """Get the final report."""
        return self.final_report

# Singleton instance
orchestrator = Orchestrator() 