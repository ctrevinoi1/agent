import os
import json
from typing import Dict, List, Any, Optional
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.orchestrator import orchestrator

# Define API models
class OsintQuery(BaseModel):
    query: str
    
class OsintResponse(BaseModel):
    query: str
    report: str
    
class WorkflowStatus(BaseModel):
    query: str
    status: Dict[str, Any]

# Create FastAPI app
app = FastAPI(
    title="OSINT Analysis System",
    description="A CAMEL-based multi-agent system for OSINT collection, verification, and reporting",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: List[WebSocket] = []

async def update_client(websocket: WebSocket, message: str):
    """Send a status update to a connected client."""
    await websocket.send_text(json.dumps({"status": message}))

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "OSINT Analysis System API", "status": "online"}

@app.post("/query", response_model=OsintResponse)
async def process_query(query: OsintQuery, background_tasks: BackgroundTasks):
    """
    Process an OSINT query synchronously.
    This will return a 202 Accepted response and process the query in the background.
    Check /status for updates.
    """
    # Start the query processing in the background
    background_tasks.add_task(orchestrator.process_query, query.query)
    
    # Return a response immediately
    return {
        "query": query.query,
        "report": "Processing query in the background. Check /status for updates."
    }

@app.get("/status")
async def get_status():
    """Get the current workflow status."""
    return orchestrator.get_workflow_state()

@app.get("/report")
async def get_report():
    """Get the final report."""
    if not orchestrator.get_final_report():
        raise HTTPException(status_code=404, detail="No report available yet")
    
    return {
        "query": orchestrator.current_query,
        "report": orchestrator.get_final_report()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            data = json.loads(data)
            
            if "query" in data:
                # Process the query
                query = data["query"]
                
                # Define a callback to send status updates
                async def status_callback(message: str):
                    await websocket.send_text(json.dumps({"status": message}))
                
                # Process the query with the callback
                final_report = await orchestrator.process_query(query, status_callback)
                
                # Send the final report
                await websocket.send_text(json.dumps({
                    "report": final_report,
                    "status": "complete"
                }))
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    
    except Exception as e:
        # Handle any other exceptions
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass
        
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    # Run the server directly if this script is executed
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True) 