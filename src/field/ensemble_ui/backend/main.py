import asyncio
import json
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

class AgentOrchestrator:
    def __init__(self):
        self.active_agents: Dict[str, Any] = {}
    
    async def spawn_agent(self, agent_type: str):
        # Placeholder for agent spawning logic
        agent_id = f"{agent_type}_{len(self.active_agents) + 1}"
        self.active_agents[agent_id] = {"type": agent_type, "status": "initializing"}
        return agent_id

    def get_agent_status(self, agent_id: str):
        return self.active_agents.get(agent_id, {"status": "not_found"})

app = FastAPI(title="Ensemble UI Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AgentOrchestrator()

@app.post("/api/generate-solution")
async def generate_solution():
    """HTTP endpoint to trigger solution generation"""
    try:
        agent_id = await orchestrator.spawn_agent("solution_generator")
        return {"agent_id": agent_id, "status": "agent_spawned"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.websocket("/ws/agent-status")
async def agent_status_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time agent status updates"""
    await websocket.accept()
    try:
        while True:
            # Receive possible agent_id request
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                agent_id = request.get('agent_id')
                
                if agent_id:
                    status = orchestrator.get_agent_status(agent_id)
                    await websocket.send_json(status)
                else:
                    # Send all active agent statuses
                    await websocket.send_json({
                        "active_agents": list(orchestrator.active_agents.keys())
                    })
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)