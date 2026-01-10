import pytest
from fastapi.testclient import TestClient
from websockets import connect
import asyncio
from main import app

client = TestClient(app)

def test_generate_solution():
    response = client.post("/api/generate-solution", json={
        "task": "test_task",
        "parameters": {"example": "data"}
    })
    assert response.status_code == 200
    assert "job_id" in response.json()
    assert response.json()["status"] == "completed"

@pytest.mark.asyncio
async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/agent-status"
    async with connect(uri) as websocket:
        assert websocket.open is True

@pytest.mark.asyncio
async def test_solution_generation_status_broadcast():
    # This test simulates a WebSocket connection receiving status updates
    status_updates = []
    uri = "ws://localhost:8000/ws/agent-status"
    
    async def receive_updates():
        async with connect(uri) as websocket:
            try:
                while True:
                    message = await websocket.recv()
                    status_updates.append(message)
            except:
                pass

    # Run solution generation in background
    async def generate_solution():
        client.post("/api/generate-solution", json={
            "task": "broadcast_test",
            "parameters": {"example": "data"}
        })

    # Create task for receiving updates
    receive_task = asyncio.create_task(receive_updates())
    
    # Wait a moment and then generate solution
    await asyncio.sleep(0.5)
    await generate_solution()
    
    # Wait for updates
    await asyncio.sleep(2)
    
    # Cancel receiving task
    receive_task.cancel()

    # Validate received updates
    assert len(status_updates) >= 2  # Running and completed statuses
    assert any("running" in status for status in status_updates)
    assert any("completed" in status for status in status_updates)

def test_error_handling():
    # Test error scenario
    response = client.post("/api/generate-solution", json={
        "task": "error_test",
        "parameters": {"cause_error": True}
    })
    assert response.status_code == 500