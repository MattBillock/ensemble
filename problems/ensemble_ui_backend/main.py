import asyncio
import json
from typing import Dict, Optional, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
import uvicorn

class AgentStatus(BaseModel):
    agent_id: str
    status: str
    progress: float = Field(ge=0.0, le=1.0)
    phase: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SolutionRequest(BaseModel):
    task: str
    parameters: Dict[str, Any]

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

app = FastAPI()
websocket_manager = WebSocketManager()

@app.websocket("/ws/agent-status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.post("/api/generate-solution")
async def generate_solution(request: SolutionRequest):
    try:
        # Simulated agent spawning and solution generation
        status = AgentStatus(
            agent_id=f"agent_{request.task}",
            status="running",
            progress=0.5,
            phase="Generating Solution"
        )
        await websocket_manager.broadcast(status.json())
        
        # Placeholder for actual solution generation logic
        await asyncio.sleep(2)  # Simulate processing
        
        final_status = AgentStatus(
            agent_id=f"agent_{request.task}",
            status="completed",
            progress=1.0,
            phase="Solution Generated",
            result={"solution": "Simulated solution"}
        )
        await websocket_manager.broadcast(final_status.json())
        
        return {"job_id": f"job_{request.task}", "status": "completed"}
    except Exception as e:
        error_status = AgentStatus(
            agent_id=f"agent_{request.task}",
            status="error",
            progress=0.0,
            error=str(e)
        )
        await websocket_manager.broadcast(error_status.json())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)