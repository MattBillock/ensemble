import asyncio
import json
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import Ensemble agent runtime
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool

load_dotenv()

class ProblemRequest(BaseModel):
    problem: str
    budget_tier: str = "balanced"  # full_firepower, balanced, economical

class ModelOverrideRequest(BaseModel):
    agent_name: str
    model_id: str  # Specific Claude model ID to use

class AgentFileUpdate(BaseModel):
    agent_path: str  # Relative path like "leadership/executive_director.md"
    content: str

class AgentOrchestrator:
    def __init__(self):
        self.active_agents: Dict[str, Any] = {}
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        # Get project root (3 levels up from backend/main.py)
        self.project_root = Path(__file__).parent.parent.parent.parent

    async def spawn_executive_director(self, problem_description: str, budget_tier: str = "balanced"):
        """Spawn the Executive Director agent to handle the problem."""
        agent_id = f"exec_dir_{len(self.active_agents) + 1}"

        try:
            # Load Executive Director
            exec_dir_path = self.project_root / "leadership" / "executive_director.md"
            exec_dir_def = AgentDefinition.from_file(exec_dir_path)

            # Set up tools
            tools = ToolRegistry.default(exec_dir_def)
            spawn_tool = SpawnAgentTool(
                agent_types_dir=self.project_root,
                api_key=self.api_key,
                tools=tools,
                budget_tier=budget_tier  # Pass budget tier to spawned agents
            )
            tools.register(spawn_tool)

            # Store agent info
            self.active_agents[agent_id] = {
                "type": "executive_director",
                "status": "initializing",
                "problem": problem_description,
                "budget_tier": budget_tier
            }

            # Create runtime with budget tier
            runtime = AgentRuntime(
                exec_dir_def,
                api_key=self.api_key,
                tools=tools,
                budget_tier=budget_tier
            )

            # Execute in background
            input_data = {
                "user_vision": problem_description,
                "output_directory": str(self.project_root / "src" / "field" / "ensemble_ui" / "output"),
                "context": "User submitted problem via web UI"
            }

            # Update status
            self.active_agents[agent_id]["status"] = "running"

            # Execute agent (this will block, so in production we'd run in background task)
            result = runtime.execute(input_data)

            # Update with result
            self.active_agents[agent_id]["status"] = "completed"
            self.active_agents[agent_id]["result"] = result

            return agent_id, result

        except Exception as e:
            self.active_agents[agent_id] = {
                "type": "executive_director",
                "status": "error",
                "error": str(e)
            }
            raise

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
async def generate_solution(request: ProblemRequest):
    """HTTP endpoint to trigger solution generation"""
    try:
        # Spawn Executive Director with problem description and budget tier
        agent_id, result = await orchestrator.spawn_executive_director(
            request.problem,
            budget_tier=request.budget_tier
        )

        return {
            "agent_id": agent_id,
            "status": "completed",
            "result": result,
            "budget_tier": request.budget_tier
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

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

@app.get("/api/status")
async def get_application_status():
    """Get current application status and statistics"""
    return {
        "status": "running",
        "active_agents": len(orchestrator.active_agents),
        "agents": {
            agent_id: {
                "type": info.get("type"),
                "status": info.get("status"),
                "budget_tier": info.get("budget_tier", "balanced")
            }
            for agent_id, info in orchestrator.active_agents.items()
        }
    }

@app.get("/api/available-models")
async def get_available_models():
    """Get list of available Claude models"""
    from src.runtime.agents.model_selector import ModelSelector
    return {
        "tiers": ModelSelector.get_available_tiers(),
        "complexities": ModelSelector.get_available_complexities(),
        "tier_descriptions": {
            tier: ModelSelector.get_tier_description(tier)
            for tier in ModelSelector.get_available_tiers()
        },
        "cost_multipliers": {
            tier: ModelSelector.estimate_cost_multiplier(tier)
            for tier in ModelSelector.get_available_tiers()
        }
    }

@app.get("/api/agents")
async def list_agents():
    """List all available agent definitions"""
    agents = []
    for directory in ["leadership", "coordinators", "developers", "testers", "designers"]:
        agent_dir = orchestrator.project_root / directory
        if agent_dir.exists():
            for agent_file in agent_dir.glob("*.md"):
                agents.append({
                    "name": agent_file.stem,
                    "path": f"{directory}/{agent_file.name}",
                    "tier": directory
                })
    return {"agents": agents}

@app.get("/api/agents/{agent_tier}/{agent_name}")
async def get_agent_definition(agent_tier: str, agent_name: str):
    """Get agent definition file content"""
    agent_path = orchestrator.project_root / agent_tier / f"{agent_name}.md"
    if not agent_path.exists():
        return {"error": "Agent not found"}, 404

    content = agent_path.read_text()
    return {
        "path": f"{agent_tier}/{agent_name}.md",
        "content": content
    }

@app.post("/api/agents/update")
async def update_agent_definition(update: AgentFileUpdate):
    """Update an agent definition file"""
    try:
        agent_path = orchestrator.project_root / update.agent_path
        if not agent_path.exists():
            return {"error": "Agent file not found", "path": update.agent_path}, 404

        # Backup current version
        backup_path = agent_path.with_suffix(".md.backup")
        agent_path.rename(backup_path)

        try:
            # Write new content
            agent_path.write_text(update.content)

            # Validate by trying to load it
            from src.runtime.agents import AgentDefinition
            AgentDefinition.from_file(agent_path)

            return {
                "success": True,
                "message": f"Updated {update.agent_path}",
                "backup": str(backup_path)
            }
        except Exception as e:
            # Restore backup on failure
            backup_path.rename(agent_path)
            return {
                "error": f"Failed to update agent: {str(e)}",
                "backup_restored": True
            }, 400

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)