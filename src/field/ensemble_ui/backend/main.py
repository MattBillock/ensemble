import asyncio
import json
import os
import logging
import uuid
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import threading
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Custom logging adapter for request IDs
class RequestLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        request_id = extra.get('request_id', 'none')
        agent_id = extra.get('agent_id', 'none')
        return f'[{request_id}][{agent_id}] {msg}', kwargs

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

class AgentMessage(BaseModel):
    agent_id: str
    message: str

class AgentOrchestrator:
    def __init__(self):
        self.active_agents: Dict[str, Any] = {}
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        # Get project root (4 levels up from backend/main.py to get to ensemble root)
        # backend/main.py -> backend -> ensemble_ui -> field -> src -> ensemble
        self.project_root = Path(__file__).parent.parent.parent.parent.parent

        # WebSocket connections for broadcasting updates
        self.active_connections: list[WebSocket] = []

        # Request tracking
        self.request_count = 0

        self.logger = RequestLogger(logger, {})
        self.logger.info(f"🔧 Project root: {self.project_root}", extra={'request_id': 'init', 'agent_id': 'system'})
        self.logger.info(f"🔧 Leadership path: {self.project_root / 'leadership'}", extra={'request_id': 'init', 'agent_id': 'system'})

    async def broadcast_status(self):
        """Broadcast current status to all connected WebSocket clients."""
        status = {
            "active_agents": list(self.active_agents.keys()),
            "agents": self.active_agents
        }
        # Remove connections that are closed
        before_count = len(self.active_connections)
        self.active_connections = [
            ws for ws in self.active_connections
            if ws.client_state.name == "CONNECTED"
        ]
        after_count = len(self.active_connections)

        if before_count != after_count:
            self.logger.info(f"Cleaned up {before_count - after_count} disconnected WebSocket(s)",
                           extra={'request_id': 'broadcast', 'agent_id': 'system'})

        # Broadcast to all connected clients
        success_count = 0
        for connection in self.active_connections:
            try:
                await connection.send_json(status)
                success_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to broadcast to WebSocket: {e}",
                                  extra={'request_id': 'broadcast', 'agent_id': 'system'})

        if success_count > 0:
            self.logger.debug(f"Broadcasted status to {success_count} WebSocket(s)",
                            extra={'request_id': 'broadcast', 'agent_id': 'system'})

    def _scan_output_files(self, output_dir: Path, before_snapshot: set, request_id: str = 'scan', agent_id: str = 'system') -> list:
        """Scan output directory for new files created during execution."""
        try:
            if not output_dir.exists():
                self.logger.debug(f"Output directory does not exist: {output_dir}",
                                extra={'request_id': request_id, 'agent_id': agent_id})
                return []

            current_files = set()
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    current_files.add(str(file_path))

            new_files = current_files - before_snapshot

            if new_files:
                self.logger.info(f"Found {len(new_files)} new file(s) in output directory",
                               extra={'request_id': request_id, 'agent_id': agent_id})

            files_list = []
            for file_path_str in new_files:
                file_path = Path(file_path_str)
                try:
                    # Read file content (limit to reasonable size)
                    content = file_path.read_text(encoding='utf-8')
                    if len(content) > 50000:  # Limit to 50KB for display
                        content = content[:50000] + "\n... (truncated)"
                        self.logger.debug(f"Truncated file content: {file_path.name}",
                                        extra={'request_id': request_id, 'agent_id': agent_id})

                    files_list.append({
                        "path": str(file_path.relative_to(self.project_root)),
                        "filename": file_path.name,
                        "content": content,
                        "size": file_path.stat().st_size
                    })
                except Exception as e:
                    self.logger.error(f"Could not read file {file_path}: {e}",
                                    extra={'request_id': request_id, 'agent_id': agent_id})

            return files_list
        except Exception as e:
            self.logger.error(f"Error scanning output files: {e}",
                            extra={'request_id': request_id, 'agent_id': agent_id})
            return []

    def _execute_agent_background(self, agent_id: str, runtime, input_data):
        """Execute agent in background thread."""
        # Get request_id from agent info
        agent_info = self.active_agents.get(agent_id, {})
        request_id = agent_info.get("request_id", "unknown")
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting agent execution",
                           extra={'request_id': request_id, 'agent_id': agent_id})

            # Add log entry
            if "logs" not in self.active_agents[agent_id]:
                self.active_agents[agent_id]["logs"] = []
            self.active_agents[agent_id]["logs"].append(f"🚀 Starting execution...")

            # Snapshot files before execution
            output_dir = self.project_root / "src" / "field" / "ensemble_ui" / "output"
            before_files = set()
            if output_dir.exists():
                for file_path in output_dir.rglob('*'):
                    if file_path.is_file():
                        before_files.add(str(file_path))

            # Execute agent
            result = runtime.execute(input_data)

            # Calculate execution time
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Scan for new files
            generated_files = self._scan_output_files(output_dir, before_files, request_id, agent_id)

            # Record file generation in activity tracker
            if generated_files:
                activity_tracker = AgentRuntime.get_activity_tracker()
                agent_name = self.active_agents[agent_id].get("type", "unknown")

                for file_info in generated_files:
                    # Determine file type from extension
                    file_path = file_info.get("path", "")
                    file_ext = Path(file_path).suffix.lower()
                    file_type_map = {
                        ".md": "markdown",
                        ".py": "python",
                        ".js": "javascript",
                        ".tsx": "typescript-react",
                        ".ts": "typescript",
                        ".json": "json",
                        ".yaml": "yaml",
                        ".yml": "yaml",
                        ".txt": "text"
                    }
                    file_type = file_type_map.get(file_ext, "unknown")

                    # Get preview (first 500 chars)
                    content = file_info.get("content", "")
                    preview = content[:500] if content else None

                    activity_tracker.record_file_generated(
                        agent_id=agent_id,
                        agent_name=agent_name,
                        request_id=request_id,
                        file_path=file_path,
                        file_size=file_info.get("size", 0),
                        file_type=file_type,
                        preview=preview
                    )

            # Update with result
            self.active_agents[agent_id]["status"] = "completed"
            self.active_agents[agent_id]["result"] = result
            self.active_agents[agent_id]["generated_files"] = generated_files
            self.active_agents[agent_id]["completed_at"] = end_time.isoformat()
            self.active_agents[agent_id]["duration_ms"] = duration_ms

            if generated_files:
                file_count = len(generated_files)
                self.active_agents[agent_id]["logs"].append(f"📁 Generated {file_count} file(s)")

            self.active_agents[agent_id]["logs"].append(f"✅ Completed successfully")

            self.logger.info(f"Agent execution completed successfully",
                           extra={
                               'request_id': request_id,
                               'agent_id': agent_id,
                               'duration_ms': duration_ms,
                               'files_generated': len(generated_files)
                           })

        except Exception as e:
            import traceback
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            self.active_agents[agent_id]["status"] = "error"
            self.active_agents[agent_id].update(error_details)
            self.active_agents[agent_id]["failed_at"] = end_time.isoformat()
            self.active_agents[agent_id]["duration_ms"] = duration_ms
            self.active_agents[agent_id]["logs"].append(f"❌ Error: {str(e)}")

            self.logger.error(f"Agent execution failed: {str(e)}",
                            extra={
                                'request_id': request_id,
                                'agent_id': agent_id,
                                'duration_ms': duration_ms,
                                'error_type': type(e).__name__
                            })

    async def spawn_executive_director(self, problem_description: str, budget_tier: str = "balanced"):
        """Spawn the Executive Director agent to handle the problem."""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        self.request_count += 1

        agent_id = f"exec_dir_{self.request_count}"

        self.logger.info(f"Spawning Executive Director", extra={
            'request_id': request_id,
            'agent_id': agent_id,
            'budget_tier': budget_tier,
            'problem_length': len(problem_description)
        })

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
                budget_tier=budget_tier,  # Pass budget tier to spawned agents
                parent_agent_id=agent_id,  # This agent is the parent for spawned agents
                request_id=request_id  # Pass request ID for tracing
            )
            tools.register(spawn_tool)

            # Ensure output directory exists
            output_dir = self.project_root / "src" / "field" / "ensemble_ui" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Store agent info with tracing metadata
            self.active_agents[agent_id] = {
                "type": "executive_director",
                "status": "initializing",
                "problem": problem_description,
                "budget_tier": budget_tier,
                "messages": [],  # Conversation history
                "request_id": request_id,
                "created_at": datetime.now().isoformat(),
                "parent_agent_id": None,  # Top-level agent
                "spawned_agents": [],  # Track children
                "metadata": {
                    "problem_length": len(problem_description),
                    "budget_tier": budget_tier
                }
            }

            # Create runtime with budget tier and metrics parameters
            runtime = AgentRuntime(
                exec_dir_def,
                api_key=self.api_key,
                tools=tools,
                budget_tier=budget_tier,
                agent_id=agent_id,
                request_id=request_id,
                parent_agent_id=None  # Top-level agent
            )

            # Prepare input data
            input_data = {
                "user_vision": problem_description,
                "output_directory": str(output_dir),
                "context": "User submitted problem via web UI"
            }

            # Update status to running
            self.active_agents[agent_id]["status"] = "running"

            # Execute agent in background thread
            thread = threading.Thread(
                target=self._execute_agent_background,
                args=(agent_id, runtime, input_data),
                daemon=True
            )
            thread.start()

            return agent_id, {"status": "running", "agent_id": agent_id}

        except Exception as e:
            import traceback
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            self.active_agents[agent_id] = {
                "type": "executive_director",
                "status": "error",
                "problem": problem_description,
                "budget_tier": budget_tier,
                "request_id": request_id,
                "created_at": datetime.now().isoformat(),
                "failed_at": datetime.now().isoformat(),
                **error_details
            }
            # Log the error
            self.logger.error(f"Error spawning executive director: {str(e)}",
                            extra={
                                'request_id': request_id,
                                'agent_id': agent_id,
                                'error_type': type(e).__name__
                            })
            return agent_id, {"status": "error", **error_details}

    def get_agent_status(self, agent_id: str):
        return self.active_agents.get(agent_id, {"status": "not_found"})

    def add_message_to_agent(self, agent_id: str, message: str, sender: str = "user"):
        """Add a message to the agent's conversation history and resume if needed."""
        if agent_id not in self.active_agents:
            self.logger.warning(f"Attempted to add message to non-existent agent",
                              extra={'request_id': 'message', 'agent_id': agent_id})
            return {"error": "Agent not found"}

        agent_info = self.active_agents[agent_id]
        request_id = agent_info.get("request_id", "unknown")

        if "messages" not in agent_info:
            agent_info["messages"] = []

        timestamp = __import__("datetime").datetime.now().isoformat()
        agent_info["messages"].append({
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        })

        self.logger.info(f"Message added to agent conversation",
                       extra={
                           'request_id': request_id,
                           'agent_id': agent_id,
                           'sender': sender,
                           'message_length': len(message)
                       })

        # Also add to logs for visibility
        if "logs" not in agent_info:
            agent_info["logs"] = []
        agent_info["logs"].append(f"💬 {sender}: {message}")

        # If agent was waiting for user input and is now completed, create follow-up task
        if (agent_info.get("status") == "completed" and
            agent_info.get("result", {}).get("status") == "needs_user_input"):

            self.logger.info(f"Agent needs follow-up with user input, creating continuation task",
                           extra={'request_id': request_id, 'agent_id': agent_id})

            agent_info["logs"].append(f"🔄 Creating follow-up task with full conversation context...")

            # Get the original problem and build conversation context
            problem = agent_info.get("problem", "")
            budget_tier = agent_info.get("budget_tier", "balanced")

            # Get previous result summary
            prev_result = agent_info.get("result", {})
            prev_summary = prev_result.get("summary", "")
            prev_question = prev_result.get("user_question", "")

            # Build COMPLETE conversation history with timestamps
            conversation_history = []
            for msg in agent_info.get("messages", []):
                timestamp = msg.get("timestamp", "")
                sender = msg.get("sender", "unknown")
                content = msg.get("message", "")
                conversation_history.append(f"[{timestamp}] {sender}: {content}")

            # Create updated task with FULL context
            updated_task = f"""# Task Continuation with Full Context

## Original Request
{problem}

## Previous Agent Analysis
{prev_summary if prev_summary else 'Agent analyzed the request'}

## Agent's Question
{prev_question}

## Complete Conversation History
{chr(10).join(conversation_history)}

## Instructions
You now have the COMPLETE conversation history above. The user has provided all necessary clarifications. Please proceed with implementation WITHOUT asking for more clarification unless the requirements are genuinely contradictory.

Use the conversation context to understand:
- What the user wants (original request)
- What was unclear (agent's question)
- What the user clarified (conversation history)

Proceed with confident implementation based on this full context."""

            # Mark this agent as "superseded"
            agent_info["logs"].append(f"✨ Launching new agent with your input...")

            # This will be handled by returning a special flag
            return {
                "success": True,
                "message": "Agent resumed",
                "spawn_new_task": True,
                "task": updated_task,
                "budget_tier": budget_tier
            }

        return {"success": True, "message": "Message added"}

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
    request_id = str(uuid.uuid4())[:8]
    orchestrator.logger.info(f"API request: generate-solution",
                            extra={
                                'request_id': request_id,
                                'agent_id': 'api',
                                'budget_tier': request.budget_tier,
                                'problem_length': len(request.problem)
                            })
    try:
        # Spawn Executive Director with problem description and budget tier
        agent_id, result = await orchestrator.spawn_executive_director(
            request.problem,
            budget_tier=request.budget_tier
        )

        orchestrator.logger.info(f"API response: generate-solution success",
                                extra={
                                    'request_id': request_id,
                                    'agent_id': agent_id,
                                    'status': 'success'
                                })

        return {
            "agent_id": agent_id,
            "status": "completed",
            "result": result,
            "budget_tier": request.budget_tier
        }
    except Exception as e:
        orchestrator.logger.error(f"API error: generate-solution failed: {str(e)}",
                                 extra={
                                     'request_id': request_id,
                                     'agent_id': 'api',
                                     'error_type': type(e).__name__
                                 })
        return {"error": str(e), "status": "error"}

@app.websocket("/ws/agent-status")
async def agent_status_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time agent status updates"""
    await websocket.accept()
    orchestrator.active_connections.append(websocket)
    orchestrator.logger.info(f"WebSocket connected",
                            extra={
                                'request_id': 'ws',
                                'agent_id': 'websocket',
                                'total_connections': len(orchestrator.active_connections)
                            })

    try:
        # Send initial status
        await websocket.send_json({
            "active_agents": list(orchestrator.active_agents.keys()),
            "agents": orchestrator.active_agents
        })

        # Keep connection alive and send periodic updates
        while True:
            try:
                # Try to receive messages (with timeout)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
            except asyncio.TimeoutError:
                # Timeout is fine, just send status update
                pass
            except:
                break

            # Send current status
            await websocket.send_json({
                "active_agents": list(orchestrator.active_agents.keys()),
                "agents": orchestrator.active_agents
            })

    except WebSocketDisconnect:
        orchestrator.logger.info(f"WebSocket disconnected",
                                extra={
                                    'request_id': 'ws',
                                    'agent_id': 'websocket'
                                })
    finally:
        if websocket in orchestrator.active_connections:
            orchestrator.active_connections.remove(websocket)
        orchestrator.logger.info(f"WebSocket cleanup complete",
                                extra={
                                    'request_id': 'ws',
                                    'agent_id': 'websocket',
                                    'remaining_connections': len(orchestrator.active_connections)
                                })

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

@app.post("/api/agents/{agent_id}/message")
async def send_message_to_agent(agent_id: str, message: AgentMessage):
    """Send a message to a running agent"""
    request_id = str(uuid.uuid4())[:8]
    orchestrator.logger.info(f"API request: send message to agent",
                            extra={
                                'request_id': request_id,
                                'agent_id': agent_id,
                                'message_length': len(message.message)
                            })

    result = orchestrator.add_message_to_agent(agent_id, message.message)

    if "error" in result:
        orchestrator.logger.warning(f"API error: message send failed - agent not found",
                                   extra={
                                       'request_id': request_id,
                                       'agent_id': agent_id
                                   })
        return {"error": result["error"]}, 404

    orchestrator.logger.info(f"API response: message sent successfully",
                            extra={
                                'request_id': request_id,
                                'agent_id': agent_id
                            })
    return result

# Activity Tracking Endpoints (for polling-based UI updates)
@app.get("/api/activity/recent")
async def get_recent_activities(
    agent_id: str = None,
    request_id: str = None,
    activity_types: str = None,
    limit: int = 100
):
    """Get recent agent activities for UI updates"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()

    # Parse activity types if provided
    types_list = None
    if activity_types:
        from src.runtime.agents.activity_tracker import ActivityType
        types_list = [ActivityType(t.strip()) for t in activity_types.split(',')]

    activities = tracker.get_activities(
        agent_id=agent_id,
        request_id=request_id,
        activity_types=types_list,
        limit=limit
    )

    return {"activities": activities}

@app.get("/api/activity/hierarchy")
async def get_agent_hierarchy(request_id: str = None):
    """Get agent hierarchy tree"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()
    hierarchy = tracker.get_agent_hierarchy(request_id)
    return {"hierarchy": hierarchy}

@app.get("/api/activity/states")
async def get_all_agent_states():
    """Get current state of all agents"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()
    states = tracker.get_all_agent_states()
    return {"agent_states": states}

@app.get("/api/activity/states/{agent_id}")
async def get_agent_state(agent_id: str):
    """Get current state of a specific agent"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()
    state = tracker.get_agent_state(agent_id)
    if state is None:
        return {"error": "Agent not found"}, 404
    return {"agent_state": state}

@app.get("/api/activity/questions")
async def get_pending_questions():
    """Get pending questions that need user response"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()
    questions = tracker.get_pending_questions()
    return {"questions": questions}

@app.post("/api/activity/questions/{question_id}/answer")
async def answer_question(question_id: str, answer: dict):
    """Answer a pending question"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()

    if "answer" not in answer:
        return {"error": "Missing 'answer' field"}, 400

    tracker.record_answer(question_id, answer["answer"])
    return {"success": True, "question_id": question_id}

@app.get("/api/activity/files")
async def get_generated_files(
    agent_id: str = None,
    request_id: str = None,
    limit: int = 100
):
    """Get generated files from activity tracker"""
    from src.runtime.agents.runtime import AgentRuntime
    from src.runtime.agents.activity_tracker import ActivityType

    tracker = AgentRuntime.get_activity_tracker()

    # Get FILE_GENERATED activities
    activities = tracker.get_activities(
        agent_id=agent_id,
        request_id=request_id,
        activity_types=[ActivityType.FILE_GENERATED],
        limit=limit
    )

    # Extract file information from activities
    files = []
    for activity in activities:
        data = activity.get("data", {})
        files.append({
            "agent_id": activity.get("agent_id"),
            "agent_name": activity.get("agent_name"),
            "request_id": activity.get("request_id"),
            "timestamp": activity.get("timestamp"),
            "file_path": data.get("file_path"),
            "file_size": data.get("file_size"),
            "file_type": data.get("file_type"),
            "preview": data.get("preview")
        })

    return {"files": files, "count": len(files)}

@app.get("/api/metrics/summary")
async def get_metrics_summary(days: int = 30):
    """Get overall system metrics summary"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_summary_stats(days)

@app.get("/api/metrics/agents")
async def get_agent_metrics(agent_name: str = None, days: int = 30):
    """Get success rates by agent type"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_success_rate_by_agent(agent_name, days)

@app.get("/api/metrics/models")
async def get_model_metrics(days: int = 30):
    """Get model performance comparison"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_success_rate_by_model(days)

@app.get("/api/metrics/complexity")
async def get_complexity_metrics(days: int = 30):
    """Get performance by task complexity"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_success_rate_by_complexity(days)

@app.get("/api/metrics/trends")
async def get_performance_trends(agent_name: str = None, days: int = 30):
    """Get performance trends over time"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_performance_trends(agent_name, days)

@app.get("/api/metrics/errors")
async def get_error_analysis(days: int = 30):
    """Get common error patterns"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_error_analysis(days)

@app.get("/api/metrics/self-analyses")
async def get_self_analyses(agent_name: str = None, limit: int = 10):
    """Get recent agent self-assessments"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_self_analyses(agent_name, limit)

@app.get("/api/metrics/correlation/{agent_name}")
async def get_agent_model_correlation(agent_name: str, days: int = 30):
    """Get best models for specific agent"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return tracker.get_agent_model_correlation(agent_name, days)

@app.get("/api/metrics/executions")
async def get_recent_executions(limit: int = 20):
    """Get recent agent executions"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_metrics_tracker()
    return {"executions": tracker.get_recent_executions(limit)}

@app.post("/api/agents/update")
async def update_agent_definition(update: AgentFileUpdate):
    """Update an agent definition file"""
    request_id = str(uuid.uuid4())[:8]
    orchestrator.logger.info(f"API request: update agent definition",
                            extra={
                                'request_id': request_id,
                                'agent_id': 'api',
                                'agent_path': update.agent_path,
                                'content_length': len(update.content)
                            })
    try:
        agent_path = orchestrator.project_root / update.agent_path
        if not agent_path.exists():
            orchestrator.logger.warning(f"API error: agent file not found",
                                       extra={
                                           'request_id': request_id,
                                           'agent_id': 'api',
                                           'agent_path': update.agent_path
                                       })
            return {"error": "Agent file not found", "path": update.agent_path}, 404

        # Backup current version
        backup_path = agent_path.with_suffix(".md.backup")
        agent_path.rename(backup_path)
        orchestrator.logger.info(f"Created backup of agent definition",
                                extra={
                                    'request_id': request_id,
                                    'agent_id': 'api',
                                    'backup_path': str(backup_path)
                                })

        try:
            # Write new content
            agent_path.write_text(update.content)

            # Validate by trying to load it
            from src.runtime.agents import AgentDefinition
            AgentDefinition.from_file(agent_path)

            orchestrator.logger.info(f"API response: agent definition updated successfully",
                                    extra={
                                        'request_id': request_id,
                                        'agent_id': 'api',
                                        'agent_path': update.agent_path
                                    })

            return {
                "success": True,
                "message": f"Updated {update.agent_path}",
                "backup": str(backup_path)
            }
        except Exception as e:
            # Restore backup on failure
            backup_path.rename(agent_path)
            orchestrator.logger.error(f"API error: agent update failed, restored backup: {str(e)}",
                                     extra={
                                         'request_id': request_id,
                                         'agent_id': 'api',
                                         'agent_path': update.agent_path,
                                         'error_type': type(e).__name__
                                     })
            return {
                "error": f"Failed to update agent: {str(e)}",
                "backup_restored": True
            }, 400

    except Exception as e:
        orchestrator.logger.error(f"API error: update agent definition failed: {str(e)}",
                                 extra={
                                     'request_id': request_id,
                                     'agent_id': 'api',
                                     'error_type': type(e).__name__
                                 })
        return {"error": str(e)}, 500

if __name__ == "__main__":
    # Development mode with auto-reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Using 8001 to not conflict with other apps
        reload=True,
        reload_dirs=[
            str(Path(__file__).parent),  # Backend directory
            str(Path(__file__).parent.parent.parent.parent / "src" / "runtime"),  # Runtime code
            str(Path(__file__).parent.parent.parent.parent / "leadership"),  # Agent definitions
            str(Path(__file__).parent.parent.parent.parent / "coordinators"),
            str(Path(__file__).parent.parent.parent.parent / "developers"),
            str(Path(__file__).parent.parent.parent.parent / "testers"),
            str(Path(__file__).parent.parent.parent.parent / "designers"),
        ],
        reload_includes=["*.py", "*.md"],  # Watch Python and agent definition files
    )