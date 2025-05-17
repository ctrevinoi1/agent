#!/usr/bin/env python
"""
OSINT Analysis System

A CAMEL-based multi-agent system for OSINT collection, verification, and reporting.

---
RECOMMENDATION:
For development and debugging, it is often better to run the API server and GUI in separate terminals/processes for better isolation and easier debugging. The current approach (running both in one script, with the API in a thread) is convenient for simple use, but less robust for production or heavy use. Consider splitting them for advanced scenarios.
---
"""

import os
import sys
import argparse
import asyncio
from threading import Thread
import uvicorn
import logging
from logging import StreamHandler
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }
    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL
        record.levelname = f"{color}{record.levelname}{reset}"
        record.msg = f"{color}{record.msg}{reset}"
        return super().format(record)

# Set up logger
logger = logging.getLogger("osint")
logger.setLevel(logging.DEBUG)
handler = StreamHandler()
formatter = ColorFormatter('[%(asctime)s] %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(handler)


def run_api_server():
    """Run the FastAPI server."""
    from app.server import app
    logger.info("Starting backend API server (FastAPI) on 0.0.0.0:8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_gui():
    """Run the GUI application."""
    from app.gui.main import main
    logger.info("Launching GUI application...")
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
    logger.info(f"Parsed arguments: mode={args.mode}, host={args.host}, port={args.port}")
    
    # Ensure data directories exist
    os.makedirs('app/data/media', exist_ok=True)
    logger.debug("Ensured app/data/media directory exists.")
    
    # Log user query intake (if applicable)
    # (If you want to log user queries, you would do so in the API or GUI modules when the user submits a query)
    
    # Run in the selected mode
    if args.mode in ["api", "both"]:
        # Start API server
        if args.mode == "both":
            logger.info("Running in BOTH mode: launching API server in a background thread.")
            server_thread = Thread(target=run_api_server)
            server_thread.daemon = True
            server_thread.start()
        else:
            logger.info("Running in API mode: launching API server only.")
            run_api_server()
    
    if args.mode in ["gui", "both"]:
        logger.info("Running in GUI mode: launching GUI application.")
        run_gui()

    # Example: Log agent/tool usage (expand in actual agent/tool code)
    # logger.info("Agent XYZ called for task ABC")

if __name__ == "__main__":
    main() 