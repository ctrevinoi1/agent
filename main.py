#!/usr/bin/env python
"""
OSINT Analysis System

A CAMEL-based multi-agent system for OSINT collection, verification, and reporting.
"""

import os
import sys
import argparse
import asyncio
from threading import Thread
import uvicorn

def run_api_server():
    """Run the FastAPI server."""
    from app.server import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_gui():
    """Run the GUI application."""
    from app.gui.main import main
    main()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="OSINT Analysis System")
    
    # Mode selection
    parser.add_argument(
        "--mode", 
        choices=["api", "gui", "both"], 
        default="both", 
        help="Run mode: 'api' for API server only, 'gui' for GUI only, 'both' for both (default)"
    )
    
    # API server options
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="API server host (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="API server port (default: 8000)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Ensure data directories exist
    os.makedirs('app/data/media', exist_ok=True)
    
    # Run in the selected mode
    if args.mode in ["api", "both"]:
        # Start API server
        if args.mode == "both":
            # Run API server in a separate thread if running both
            server_thread = Thread(target=run_api_server)
            server_thread.daemon = True
            server_thread.start()
        else:
            # Run API server directly if that's all we're running
            run_api_server()
    
    if args.mode in ["gui", "both"]:
        # Start GUI
        run_gui()

if __name__ == "__main__":
    main() 