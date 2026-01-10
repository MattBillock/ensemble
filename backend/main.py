from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json

app = FastAPI()

class AgentStatusManager:
    def __init__(self):
        self.active_connections = []
        self.agent_statuses = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_status(self, status: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(status)
            except Exception as e:
                print(f"Error broadcasting status: {e}")

agent_status_manager = AgentStatusManager()

@app.websocket("/ws/agent-status")
async def agent_status_websocket(websocket: WebSocket):
    await agent_status_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            status = json.loads(data)
            agent_status_manager.agent_statuses[status.get('agent_id', 'unknown')] = status
            await agent_status_manager.broadcast_status(status)
    except WebSocketDisconnect:
        agent_status_manager.disconnect(websocket)

@app.post("/api/generate-solution")
async def generate_solution(agent_details: dict):
    try:
        # Simulated agent spawning mechanism
        agent_id = agent_details.get('agent_id', 'default')
        status = {
            'agent_id': agent_id,
            'status': 'spawning',
            'details': agent_details
        }
        await agent_status_manager.broadcast_status(status)
        
        # Simulate solution generation
        await asyncio.sleep(1)
        
        status.update({
            'status': 'completed',
            'solution': 'Generated solution for ' + agent_id
        })
        await agent_status_manager.broadcast_status(status)
        
        return {
            "agent_id": agent_id,
            "solution": status['solution']
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)