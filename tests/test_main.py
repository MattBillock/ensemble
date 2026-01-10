import pytest
from fastapi.testclient import TestClient
from backend.main import app, agent_status_manager
import json
import asyncio

client = TestClient(app)

def test_generate_solution():
    agent_details = {
        "agent_id": "solution_agent",
        "type": "test_generation"
    }
    
    response = client.post("/api/generate-solution", json=agent_details)
    
    assert response.status_code == 200
    assert "solution" in response.json()
    assert response.json()["agent_id"] == "solution_agent"

@pytest.mark.asyncio
async def test_agent_status_broadcasting():
    # Simulate WebSocket connection and status broadcasting
    status = {
        "agent_id": "test_agent",
        "status": "active",
        "details": {"type": "test"}
    }
    
    # Mock broadcast mechanism
    original_broadcast = agent_status_manager.broadcast_status
    
    broadcast_result = []
    async def mock_broadcast(status):
        broadcast_result.append(status)
        await original_broadcast(status)
    
    agent_status_manager.broadcast_status = mock_broadcast
    
    await agent_status_manager.broadcast_status(status)
    
    # Restore original broadcast method
    agent_status_manager.broadcast_status = original_broadcast
    
    assert len(broadcast_result) == 1
    assert broadcast_result[0] == status

@pytest.mark.asyncio
async def test_multiple_agent_status_broadcasts():
    statuses = [
        {"agent_id": f"agent_{i}", "status": "active"} 
        for i in range(3)
    ]
    
    broadcast_results = []
    original_broadcast = agent_status_manager.broadcast_status
    
    async def mock_broadcast(status):
        broadcast_results.append(status)
        await original_broadcast(status)
    
    agent_status_manager.broadcast_status = mock_broadcast
    
    for status in statuses:
        await agent_status_manager.broadcast_status(status)
    
    # Restore original broadcast method
    agent_status_manager.broadcast_status = original_broadcast
    
    assert len(broadcast_results) == len(statuses)
    assert all(result in statuses for result in broadcast_results)