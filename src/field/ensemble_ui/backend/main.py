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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure structured logging with file and console output
LOG_DIR = Path(__file__).parent.parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "ensemble-backend.log"

# Create formatters
log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
date_format = '%Y-%m-%d %H:%M:%S'

# Console handler (stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# File handler (rotates at 10MB, keeps 5 backups)
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)  # Capture more detail in file
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    datefmt=date_format,
    handlers=[console_handler, file_handler]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {LOG_FILE}")

# Custom logging adapter for request IDs
class RequestLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        request_id = extra.get('request_id', 'none')
        agent_id = extra.get('agent_id', 'none')
        return f'[{request_id}][{agent_id}] {msg}', kwargs

# Import Ensemble agent runtime
import sys

# Add project root to Python path (Path already imported above)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool
from src.runtime.agents.github_integration import GitHubIntegration
from src.runtime.agents.title_generator import TitleGenerator

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

        # Create a swarm session for tracking
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm_state = get_swarm_state()
        session_id = swarm_state.create_session(
            request_id=request_id,
            user_prompt=problem_description,
            budget_tier=budget_tier,
            title=f"Task {self.request_count}"  # Will be updated by title generator
        )

        self.logger.info(f"Created swarm session: {session_id}", extra={
            'request_id': request_id,
            'agent_id': agent_id,
            'session_id': session_id
        })

        # Detect GitHub repo URL (cached after first call)
        github_repo_url = GitHubIntegration.detect_repo_url(str(self.project_root))

        # Record request in activity tracker for timeline view
        activity_tracker = AgentRuntime.get_activity_tracker()
        activity_tracker.record_request_started(
            request_id=request_id,
            prompt=problem_description,
            budget_tier=budget_tier,
            root_agent_id=agent_id,
            github_repo_url=github_repo_url
        )

        # Start async title generation
        self._generate_title_async(request_id, problem_description)

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
                request_id=request_id,  # Pass request ID for tracing
                session_id=session_id  # Pass session ID for swarm state tracking
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
                parent_agent_id=None,  # Top-level agent
                session_id=session_id  # For swarm state tracking
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

    def _generate_title_async(self, request_id: str, prompt: str):
        """Generate title for request asynchronously in background thread."""
        def generate():
            try:
                generator = TitleGenerator(self.api_key)
                title = generator.generate_title(prompt)
                # Update the request with the generated title
                activity_tracker = AgentRuntime.get_activity_tracker()
                activity_tracker.update_request_title(request_id, title)
                self.logger.info(f"Generated title for request",
                               extra={'request_id': request_id, 'title': title})
            except Exception as e:
                self.logger.error(f"Failed to generate title: {e}",
                                extra={'request_id': request_id})

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

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

# Start recovery orchestrator on app startup
@app.on_event("startup")
async def startup_event():
    """Initialize background services on startup."""
    try:
        from src.runtime.agents.swarm_recovery import get_recovery_orchestrator
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            recovery_orchestrator = get_recovery_orchestrator(api_key=api_key)
            recovery_orchestrator.start()
            logger.info("Recovery orchestrator started")
        else:
            logger.warning("ANTHROPIC_API_KEY not set - recovery orchestrator not started")
    except Exception as e:
        logger.error(f"Failed to start recovery orchestrator: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    try:
        from src.runtime.agents.swarm_recovery import get_recovery_orchestrator
        orchestrator = get_recovery_orchestrator()
        orchestrator.stop()
        logger.info("Recovery orchestrator stopped")
    except Exception as e:
        logger.error(f"Error stopping recovery orchestrator: {e}")

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
    """WebSocket endpoint for real-time agent status updates (legacy)"""
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
            except Exception as e:
                logger.debug(f"WebSocket receive error: {e}")
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


@app.websocket("/ws/events")
async def events_ws(websocket: WebSocket):
    """
    Enhanced WebSocket endpoint for real-time event streaming.

    Supports subscriptions and filtering. Send a JSON message to configure:
    {
        "action": "subscribe",
        "event_types": ["agent_spawned", "agent_completed", "tool_use"],
        "filters": {"request_id": "abc123"}
    }
    """
    from src.runtime.agents.websocket_manager import get_websocket_manager, EventType

    await websocket.accept()
    ws_manager = get_websocket_manager()

    # Default subscriptions (all events)
    subscriptions = set(EventType)
    filters = {}

    # Register client
    client_id = await ws_manager.register_client(
        websocket=websocket,
        subscriptions=subscriptions,
        filters=filters
    )

    orchestrator.logger.info(f"Enhanced WebSocket connected: {client_id}",
                            extra={
                                'request_id': 'ws',
                                'agent_id': 'websocket',
                                'client_id': client_id
                            })

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "client_id": client_id,
                "subscriptions": [s.value for s in subscriptions],
                "message": "Connected to Ensemble event stream"
            }
        })

        # Listen for subscription updates
        while True:
            try:
                message = await websocket.receive_json()

                action = message.get("action")

                if action == "subscribe":
                    # Update subscriptions
                    event_types = message.get("event_types", [])
                    if event_types:
                        subscriptions = {
                            EventType(et) for et in event_types
                            if et in [e.value for e in EventType]
                        }

                    new_filters = message.get("filters", {})
                    await ws_manager.update_subscriptions(
                        client_id,
                        subscriptions,
                        new_filters
                    )

                    await websocket.send_json({
                        "type": "subscription_updated",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "subscriptions": [s.value for s in subscriptions],
                            "filters": new_filters
                        }
                    })

                elif action == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                        "data": {}
                    })

                elif action == "get_buffer":
                    # Send buffered events
                    buffer_data = list(ws_manager.event_buffer)
                    await websocket.send_json({
                        "type": "buffered_events",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "events": buffer_data,
                            "count": len(buffer_data)
                        }
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                orchestrator.logger.warning(f"WebSocket message error: {e}",
                                          extra={
                                              'request_id': 'ws',
                                              'agent_id': 'websocket',
                                              'client_id': client_id
                                          })
                # Send error but don't disconnect
                try:
                    await websocket.send_json({
                        "type": "error",
                        "timestamp": datetime.now().isoformat(),
                        "data": {"message": str(e)}
                    })
                except Exception as send_error:
                    logger.debug(f"Failed to send error to WebSocket: {send_error}")
                    break

    except WebSocketDisconnect:
        orchestrator.logger.info(f"Enhanced WebSocket disconnected: {client_id}",
                                extra={
                                    'request_id': 'ws',
                                    'agent_id': 'websocket',
                                    'client_id': client_id
                                })
    finally:
        await ws_manager.unregister_client(client_id)
        orchestrator.logger.info(f"Enhanced WebSocket cleanup complete: {client_id}",
                                extra={
                                    'request_id': 'ws',
                                    'agent_id': 'websocket',
                                    'client_id': client_id
                                })


@app.get("/api/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    from src.runtime.agents.websocket_manager import get_websocket_manager

    ws_manager = get_websocket_manager()
    return ws_manager.get_stats()

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
    # Validate input to prevent path traversal attacks
    valid_tiers = {"leadership", "coordinators", "developers", "testers", "designers"}
    if agent_tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid agent tier. Must be one of: {', '.join(valid_tiers)}")

    # Reject path traversal attempts
    if ".." in agent_name or "/" in agent_name or "\\" in agent_name:
        raise HTTPException(status_code=400, detail="Invalid agent name")

    agent_path = orchestrator.project_root / agent_tier / f"{agent_name}.md"

    # Verify the resolved path is still within project_root
    try:
        agent_path.resolve().relative_to(orchestrator.project_root.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not agent_path.exists():
        raise HTTPException(status_code=404, detail="Agent not found")

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
        raise HTTPException(status_code=404, detail=result["error"])

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
        raise HTTPException(status_code=404, detail="Agent not found")
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
        raise HTTPException(status_code=400, detail="Missing 'answer' field")

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

# ========== Timeline View Endpoints ==========

@app.get("/api/requests")
async def get_requests(limit: int = 50):
    """Get all requests for timeline view, most recent first."""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()
    requests = tracker.get_requests(limit)
    return {"requests": requests, "count": len(requests)}

@app.get("/api/requests/{request_id}/timeline")
async def get_request_timeline(request_id: str):
    """Get complete timeline data for a specific request."""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()
    timeline = tracker.get_request_timeline(request_id)
    return timeline

@app.get("/api/git/repo-info")
async def get_git_repo_info():
    """Get auto-detected GitHub repository information."""
    repo_info = GitHubIntegration.get_repo_info(str(orchestrator.project_root))
    return repo_info

@app.get("/api/deliverables/{request_id}")
async def get_deliverables(request_id: str):
    """Get all deliverables (files and commits) for a request with GitHub links."""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()

    # Get GitHub repo info for generating links
    repo_info = GitHubIntegration.get_repo_info(str(orchestrator.project_root))
    repo_url = repo_info.get("repo_url")
    branch = repo_info.get("branch", "main")

    # Get timeline which includes deliverables
    timeline = tracker.get_request_timeline(request_id)
    if "error" in timeline:
        return timeline

    deliverables = timeline.get("deliverables", [])

    # Add GitHub URLs to deliverables
    for d in deliverables:
        if repo_url:
            if d["type"] == "file":
                d["github_url"] = GitHubIntegration.get_file_url(repo_url, d["path"], branch)
            elif d["type"] == "commit":
                d["github_url"] = GitHubIntegration.get_commit_url(repo_url, d["hash"])

    return {
        "request_id": request_id,
        "deliverables": deliverables,
        "github_repo": repo_url,
        "branch": branch,
        "file_count": len([d for d in deliverables if d["type"] == "file"]),
        "commit_count": len([d for d in deliverables if d["type"] == "commit"])
    }

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

    # Validate path to prevent path traversal attacks
    valid_tiers = {"leadership", "coordinators", "developers", "testers", "designers"}
    path_parts = update.agent_path.split("/")
    if len(path_parts) != 2 or path_parts[0] not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid agent path. Must be <tier>/<name>.md where tier is one of: {', '.join(valid_tiers)}")

    # Reject path traversal attempts
    if ".." in update.agent_path:
        raise HTTPException(status_code=400, detail="Invalid agent path")

    # Must be a .md file
    if not update.agent_path.endswith(".md"):
        raise HTTPException(status_code=400, detail="Agent path must end with .md")

    try:
        agent_path = orchestrator.project_root / update.agent_path

        # Verify the resolved path is within project_root
        try:
            agent_path.resolve().relative_to(orchestrator.project_root.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent path - path traversal detected")

        if not agent_path.exists():
            orchestrator.logger.warning(f"API error: agent file not found",
                                       extra={
                                           'request_id': request_id,
                                           'agent_id': 'api',
                                           'agent_path': update.agent_path
                                       })
            raise HTTPException(status_code=404, detail=f"Agent file not found: {update.agent_path}")

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
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update agent: {str(e)}. Backup restored."
            )

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        orchestrator.logger.error(f"API error: update agent definition failed: {str(e)}",
                                 extra={
                                     'request_id': request_id,
                                     'agent_id': 'api',
                                     'error_type': type(e).__name__
                                 })
        raise HTTPException(status_code=500, detail=str(e))

# ========== Self-Improvement Loop Endpoints ==========

class RecommendationAction(BaseModel):
    recommendation_id: str
    reason: str = ""

@app.get("/api/self-improvement/analyze")
async def run_self_improvement_analysis(days: int = 30):
    """Run self-improvement analysis and generate recommendations.

    When auto-apply mode is enabled, recommendations will be automatically applied.
    """
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()
    analysis = loop.run_analysis(days)

    # Auto-apply if enabled
    auto_apply_results = None
    if _auto_apply_config.get("enabled") and _auto_apply_config.get("apply_on_analysis"):
        logger.info("Auto-apply mode enabled - applying recommendations automatically")
        auto_apply_results = loop.auto_approve_and_apply_all()
        analysis["auto_apply_results"] = auto_apply_results

    return analysis

@app.get("/api/self-improvement/recommendations")
async def get_pending_recommendations():
    """Get all pending improvement recommendations."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()
    recommendations = loop.get_pending_recommendations()
    return {"recommendations": recommendations, "count": len(recommendations)}

@app.get("/api/self-improvement/feedback/{agent_name}")
async def get_agent_feedback(agent_name: str):
    """Get performance feedback for a specific agent."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()
    feedback = loop.get_feedback_for_agent(agent_name)
    return {"agent_name": agent_name, "feedback": feedback}

@app.post("/api/self-improvement/recommendations/{recommendation_id}/approve")
async def approve_recommendation(recommendation_id: str):
    """Approve a recommendation (human-in-the-loop)."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()
    result = loop.approve_recommendation(recommendation_id)
    return result

@app.post("/api/self-improvement/recommendations/{recommendation_id}/reject")
async def reject_recommendation(recommendation_id: str, action: RecommendationAction):
    """Reject a recommendation with optional reason."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()
    result = loop.reject_recommendation(recommendation_id, action.reason)
    return result

# ========== Achievement System Endpoints ==========

@app.get("/api/achievements")
async def get_all_achievements():
    """Get all available achievements with unlock status."""
    from src.runtime.agents.achievements import get_achievement_tracker
    tracker = get_achievement_tracker()
    achievements = tracker.get_all_achievements()
    return {"achievements": achievements, "count": len(achievements)}

@app.get("/api/achievements/recent")
async def get_recent_achievements(limit: int = 10):
    """Get most recently awarded achievements."""
    from src.runtime.agents.achievements import get_achievement_tracker
    tracker = get_achievement_tracker()
    recent = tracker.get_recent_achievements(limit)
    return {"achievements": recent, "count": len(recent)}

@app.get("/api/achievements/stats")
async def get_achievement_stats():
    """Get overall achievement statistics."""
    from src.runtime.agents.achievements import get_achievement_tracker
    tracker = get_achievement_tracker()
    return tracker.get_achievement_stats()

@app.get("/api/achievements/agent/{agent_class}")
async def get_agent_achievements(agent_class: str):
    """Get all achievements earned by a specific agent class."""
    from src.runtime.agents.achievements import get_achievement_tracker
    tracker = get_achievement_tracker()
    achievements = tracker.get_achievements_for_agent(agent_class)
    return {"agent_class": agent_class, "achievements": achievements, "count": len(achievements)}

@app.get("/api/self-improvement/status")
async def get_self_improvement_status():
    """Get overall self-improvement loop status."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    from pathlib import Path

    loop = get_improvement_loop()
    recommendations_dir = Path.home() / ".ensemble" / "recommendations"

    # Count total and pending recommendations
    total_recommendations = 0
    pending_count = 0
    approved_count = 0
    rejected_count = 0

    if recommendations_dir.exists():
        for filepath in recommendations_dir.glob("recommendations_*.json"):
            with open(filepath) as f:
                data = json.load(f)
                for item in data:
                    total_recommendations += 1
                    status = item.get("status", "pending")
                    if status == "pending":
                        pending_count += 1
                    elif status == "approved":
                        approved_count += 1
                    elif status == "rejected":
                        rejected_count += 1

    return {
        "status": "active",
        "feedback_injection": "enabled",
        "total_recommendations": total_recommendations,
        "pending_recommendations": pending_count,
        "approved_recommendations": approved_count,
        "rejected_recommendations": rejected_count
    }

# Auto-apply mode configuration (in-memory, persisted to file)
_auto_apply_config = {
    "enabled": False,
    "apply_on_analysis": True,  # Auto-apply when running analysis
    "min_priority": "medium",   # Only auto-apply recommendations at or above this priority
}
_auto_apply_config_path = Path.home() / ".ensemble" / "auto_apply_config.json"

def _load_auto_apply_config():
    """Load auto-apply config from file if it exists."""
    global _auto_apply_config
    if _auto_apply_config_path.exists():
        try:
            with open(_auto_apply_config_path) as f:
                saved = json.load(f)
                _auto_apply_config.update(saved)
        except Exception as e:
            logger.warning(f"Failed to load auto-apply config: {e}")

def _save_auto_apply_config():
    """Save auto-apply config to file."""
    try:
        _auto_apply_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_auto_apply_config_path, 'w') as f:
            json.dump(_auto_apply_config, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save auto-apply config: {e}")

# Load config on module import
_load_auto_apply_config()

@app.get("/api/self-improvement/auto-apply")
async def get_auto_apply_config():
    """Get current auto-apply configuration."""
    return _auto_apply_config

class AutoApplyConfig(BaseModel):
    enabled: bool
    apply_on_analysis: bool = True
    min_priority: str = "medium"

@app.post("/api/self-improvement/auto-apply")
async def set_auto_apply_config(config: AutoApplyConfig):
    """Set auto-apply configuration. When enabled, recommendations are automatically applied."""
    global _auto_apply_config
    _auto_apply_config["enabled"] = config.enabled
    _auto_apply_config["apply_on_analysis"] = config.apply_on_analysis
    _auto_apply_config["min_priority"] = config.min_priority
    _save_auto_apply_config()

    logger.info(f"Auto-apply mode {'ENABLED' if config.enabled else 'disabled'}")

    return {
        "success": True,
        "message": f"Auto-apply {'enabled' if config.enabled else 'disabled'}",
        "config": _auto_apply_config
    }

@app.post("/api/self-improvement/apply-all")
async def apply_all_recommendations():
    """Immediately apply all pending recommendations (bumpers off mode)."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()

    results = loop.auto_approve_and_apply_all()

    return {
        "success": True,
        "message": f"Applied {results['applied']} recommendations",
        "results": results
    }

@app.post("/api/self-improvement/recommendations/{recommendation_id}/apply")
async def apply_single_recommendation(recommendation_id: str):
    """Apply a single recommendation (approve + apply changes)."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()

    # First approve
    approve_result = loop.approve_recommendation(recommendation_id)
    if not approve_result.get("success"):
        return approve_result

    # Then apply
    apply_result = loop.apply_recommendation(recommendation_id)
    return apply_result

# ========== Swarm State Management Endpoints ==========

@app.get("/api/swarm/sessions")
async def get_swarm_sessions(limit: int = 50, status: str = None):
    """Get all swarm sessions with optional status filter."""
    try:
        from src.runtime.agents.swarm_state import SwarmStateManager
        state_manager = SwarmStateManager()

        sessions = state_manager.get_sessions(limit=limit, status=status)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error getting swarm sessions: {e}")
        return {"error": str(e), "sessions": []}

@app.get("/api/swarm/sessions/{session_id}")
async def get_swarm_session(session_id: str):
    """Get detailed information about a specific session."""
    try:
        from src.runtime.agents.swarm_state import SwarmStateManager
        state_manager = SwarmStateManager()

        session = state_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get agents for this session
        agents = state_manager.get_session_agents(session_id)

        return {
            "session": session,
            "agents": agents,
            "agent_count": len(agents)
        }
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return {"error": str(e)}

@app.get("/api/swarm/agents")
async def get_swarm_agents(session_id: str = None, status: str = None, limit: int = 100):
    """Get all agents with optional filters."""
    try:
        from src.runtime.agents.swarm_state import SwarmStateManager
        state_manager = SwarmStateManager()

        agents = state_manager.get_agents(
            session_id=session_id,
            status=status,
            limit=limit
        )
        return {"agents": agents, "count": len(agents)}
    except Exception as e:
        logger.error(f"Error getting swarm agents: {e}")
        return {"error": str(e), "agents": []}

@app.get("/api/swarm/agents/{agent_id}")
async def get_swarm_agent(agent_id: str):
    """Get detailed information about a specific agent."""
    try:
        from src.runtime.agents.swarm_state import SwarmStateManager
        state_manager = SwarmStateManager()

        agent = state_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Get messages and tool executions
        messages = state_manager.get_agent_messages(agent_id, limit=50)
        tool_executions = state_manager.get_agent_tool_executions(agent_id, limit=50)

        return {
            "agent": agent,
            "messages": messages,
            "tool_executions": tool_executions
        }
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        return {"error": str(e)}

@app.get("/api/swarm/stats")
async def get_swarm_stats():
    """Get overall swarm statistics."""
    try:
        from src.runtime.agents.swarm_state import SwarmStateManager
        state_manager = SwarmStateManager()

        stats = state_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting swarm stats: {e}")
        return {"error": str(e)}

@app.get("/api/swarm/events")
async def get_swarm_events(
    session_id: str = None,
    agent_id: str = None,
    event_type: str = None,
    limit: int = 100
):
    """Get swarm events with optional filters."""
    try:
        from src.runtime.agents.swarm_state import SwarmStateManager
        state_manager = SwarmStateManager()

        events = state_manager.get_events(
            session_id=session_id,
            agent_id=agent_id,
            event_type=event_type,
            limit=limit
        )
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Error getting swarm events: {e}")
        return {"error": str(e), "events": []}

# ========== Recovery System Endpoints ==========

@app.get("/api/recovery/stalled")
async def get_stalled_agents(threshold_minutes: int = 5):
    """Get list of stalled agents that may need recovery."""
    try:
        from src.runtime.agents.swarm_state import SwarmStateManager
        state_manager = SwarmStateManager()

        stalled = state_manager.get_stalled_agents(threshold_minutes)
        return {"stalled_agents": stalled, "count": len(stalled)}
    except Exception as e:
        logger.error(f"Error getting stalled agents: {e}")
        return {"error": str(e), "stalled_agents": []}

@app.get("/api/recovery/queue")
async def get_recovery_queue():
    """Get the current recovery queue status."""
    try:
        from src.runtime.agents.swarm_recovery import get_recovery_orchestrator
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        orchestrator = get_recovery_orchestrator(api_key=api_key)

        # Ensure the orchestrator is running
        if not orchestrator._running:
            orchestrator.start()

        queue = orchestrator.get_queue_status()
        return queue
    except Exception as e:
        logger.error(f"Error getting recovery queue: {e}")
        return {"error": str(e), "queue": []}

@app.post("/api/recovery/trigger/{agent_id}")
async def trigger_agent_recovery(agent_id: str, strategy: str = "retry"):
    """Manually trigger recovery for a specific agent."""
    try:
        from src.runtime.agents.swarm_recovery import get_recovery_orchestrator, RecoveryStrategy
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        orchestrator = get_recovery_orchestrator(api_key=api_key)

        # Ensure the orchestrator is running
        if not orchestrator._running:
            orchestrator.start()

        # Map string to enum
        strategy_map = {
            "retry": RecoveryStrategy.RETRY,
            "retry_with_backoff": RecoveryStrategy.RETRY_WITH_BACKOFF,
            "escalate_model": RecoveryStrategy.ESCALATE_MODEL,
            "spawn_replacement": RecoveryStrategy.SPAWN_REPLACEMENT,
            "abort": RecoveryStrategy.ABORT
        }

        recovery_strategy = strategy_map.get(strategy, RecoveryStrategy.RETRY)
        result = orchestrator.recover_agent(agent_id, recovery_strategy)

        return {
            "agent_id": agent_id,
            "strategy": strategy,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error triggering recovery for {agent_id}: {e}")
        return {"error": str(e)}

@app.post("/api/recovery/scan")
async def scan_for_stalled_agents(threshold_minutes: int = 5):
    """Scan for stalled agents and queue them for recovery."""
    try:
        from src.runtime.agents.swarm_recovery import StallDetector
        detector = StallDetector()

        stalled = detector.detect_stalled_agents(threshold_minutes)
        queued = detector.queue_for_recovery(stalled)

        return {
            "scanned": True,
            "stalled_found": len(stalled),
            "queued_for_recovery": queued
        }
    except Exception as e:
        logger.error(f"Error scanning for stalled agents: {e}")
        return {"error": str(e)}

@app.get("/api/recovery/history")
async def get_recovery_history(limit: int = 50):
    """Get history of recovery operations."""
    try:
        from src.runtime.agents.swarm_recovery import get_recovery_orchestrator
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        orchestrator = get_recovery_orchestrator(api_key=api_key)

        history = orchestrator.get_recovery_history(limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Error getting recovery history: {e}")
        return {"error": str(e), "history": []}

# ========== Cost Tracking Endpoints ==========

@app.get("/api/costs/summary")
async def get_cost_summary(days: int = 30):
    """Get cost summary for the specified period."""
    try:
        from src.runtime.agents.runtime import AgentRuntime
        tracker = AgentRuntime.get_metrics_tracker()

        # Get token usage stats
        stats = tracker.get_summary_stats(days)

        # Calculate estimated costs (rough estimates based on Claude pricing)
        # These are approximate - actual costs depend on the specific model used
        cost_per_1k_input = 0.003  # ~$3/million input tokens (Sonnet average)
        cost_per_1k_output = 0.015  # ~$15/million output tokens

        total_input = stats.get("total_input_tokens", 0)
        total_output = stats.get("total_output_tokens", 0)

        estimated_input_cost = (total_input / 1000) * cost_per_1k_input
        estimated_output_cost = (total_output / 1000) * cost_per_1k_output
        estimated_total_cost = estimated_input_cost + estimated_output_cost

        return {
            "period_days": days,
            "token_usage": {
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output
            },
            "estimated_costs": {
                "input_cost_usd": round(estimated_input_cost, 4),
                "output_cost_usd": round(estimated_output_cost, 4),
                "total_cost_usd": round(estimated_total_cost, 4)
            },
            "execution_stats": {
                "total_executions": stats.get("total_executions", 0),
                "successful_executions": stats.get("successful_executions", 0),
                "failed_executions": stats.get("failed_executions", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error getting cost summary: {e}")
        return {"error": str(e)}

@app.get("/api/costs/by-agent")
async def get_costs_by_agent(days: int = 30):
    """Get cost breakdown by agent type."""
    try:
        from src.runtime.agents.runtime import AgentRuntime
        tracker = AgentRuntime.get_metrics_tracker()

        # Get per-agent stats
        agent_stats = tracker.get_success_rate_by_agent(days=days)

        cost_per_1k_input = 0.003
        cost_per_1k_output = 0.015

        agent_costs = []
        for agent in agent_stats.get("agents", []):
            input_tokens = agent.get("avg_input_tokens", 0) * agent.get("total_executions", 0)
            output_tokens = agent.get("avg_output_tokens", 0) * agent.get("total_executions", 0)

            estimated_cost = (input_tokens / 1000) * cost_per_1k_input + \
                           (output_tokens / 1000) * cost_per_1k_output

            agent_costs.append({
                "agent_name": agent.get("agent_name"),
                "executions": agent.get("total_executions", 0),
                "total_input_tokens": int(input_tokens),
                "total_output_tokens": int(output_tokens),
                "estimated_cost_usd": round(estimated_cost, 4)
            })

        # Sort by cost descending
        agent_costs.sort(key=lambda x: x["estimated_cost_usd"], reverse=True)

        return {
            "period_days": days,
            "agents": agent_costs,
            "total_agents": len(agent_costs)
        }
    except Exception as e:
        logger.error(f"Error getting costs by agent: {e}")
        return {"error": str(e)}

@app.get("/api/costs/by-model")
async def get_costs_by_model(days: int = 30):
    """Get cost breakdown by model used."""
    try:
        from src.runtime.agents.runtime import AgentRuntime
        tracker = AgentRuntime.get_metrics_tracker()

        model_stats = tracker.get_success_rate_by_model(days=days)

        # Model-specific pricing (approximate)
        model_pricing = {
            "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "default": {"input": 0.003, "output": 0.015}
        }

        model_costs = []
        for model in model_stats.get("models", []):
            model_id = model.get("model_id", "unknown")
            pricing = model_pricing.get(model_id, model_pricing["default"])

            input_tokens = model.get("total_input_tokens", 0)
            output_tokens = model.get("total_output_tokens", 0)

            estimated_cost = (input_tokens / 1000) * pricing["input"] + \
                           (output_tokens / 1000) * pricing["output"]

            model_costs.append({
                "model_id": model_id,
                "executions": model.get("total_executions", 0),
                "total_input_tokens": input_tokens,
                "total_output_tokens": output_tokens,
                "estimated_cost_usd": round(estimated_cost, 4),
                "pricing": pricing
            })

        model_costs.sort(key=lambda x: x["estimated_cost_usd"], reverse=True)

        return {
            "period_days": days,
            "models": model_costs,
            "total_models": len(model_costs)
        }
    except Exception as e:
        logger.error(f"Error getting costs by model: {e}")
        return {"error": str(e)}

@app.get("/api/costs/trends")
async def get_cost_trends(days: int = 30, granularity: str = "day"):
    """Get cost trends over time."""
    try:
        from src.runtime.agents.runtime import AgentRuntime
        tracker = AgentRuntime.get_metrics_tracker()

        trends = tracker.get_performance_trends(days=days)

        cost_per_1k_input = 0.003
        cost_per_1k_output = 0.015

        cost_trends = []
        for point in trends.get("trends", []):
            input_tokens = point.get("total_input_tokens", 0)
            output_tokens = point.get("total_output_tokens", 0)

            estimated_cost = (input_tokens / 1000) * cost_per_1k_input + \
                           (output_tokens / 1000) * cost_per_1k_output

            cost_trends.append({
                "date": point.get("date"),
                "executions": point.get("executions", 0),
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost_usd": round(estimated_cost, 4)
            })

        return {
            "period_days": days,
            "granularity": granularity,
            "trends": cost_trends
        }
    except Exception as e:
        logger.error(f"Error getting cost trends: {e}")
        return {"error": str(e)}

# ========== Data Retention Endpoints ==========

@app.get("/api/retention/status")
async def get_retention_status():
    """Get current data retention status and database size."""
    try:
        from src.runtime.agents.data_retention import DataRetentionManager
        manager = DataRetentionManager()

        status = manager.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting retention status: {e}")
        return {"error": str(e)}

@app.post("/api/retention/cleanup")
async def trigger_cleanup(dry_run: bool = True):
    """Trigger data cleanup based on retention policies."""
    try:
        from src.runtime.agents.data_retention import DataRetentionManager
        manager = DataRetentionManager()

        result = manager.run_cleanup(dry_run=dry_run)
        return {
            "dry_run": dry_run,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error running cleanup: {e}")
        return {"error": str(e)}

@app.post("/api/retention/archive/{session_id}")
async def archive_session(session_id: str):
    """Archive a completed session."""
    try:
        from src.runtime.agents.data_retention import DataArchiver
        archiver = DataArchiver()

        result = archiver.archive_session_by_id(session_id)
        return result
    except Exception as e:
        logger.error(f"Error archiving session {session_id}: {e}")
        return {"error": str(e)}

# ========== Streaming Control Endpoints ==========

class StreamingConfig(BaseModel):
    enabled: bool = True
    poll_interval_ms: int = 2000  # Default 2 seconds
    event_types: list = None  # Filter specific event types

# Global streaming configuration
_streaming_config = {
    "enabled": True,
    "poll_interval_ms": 2000,
    "event_types": None
}

@app.get("/api/streaming/config")
async def get_streaming_config():
    """Get current streaming/polling configuration."""
    return _streaming_config

@app.post("/api/streaming/config")
async def update_streaming_config(config: StreamingConfig):
    """Update streaming/polling configuration."""
    global _streaming_config
    _streaming_config["enabled"] = config.enabled
    _streaming_config["poll_interval_ms"] = max(500, min(config.poll_interval_ms, 30000))  # Clamp between 500ms and 30s
    _streaming_config["event_types"] = config.event_types

    logger.info(f"Streaming config updated: enabled={config.enabled}, interval={_streaming_config['poll_interval_ms']}ms")

    return _streaming_config

@app.post("/api/streaming/start")
async def start_streaming():
    """Enable real-time streaming updates."""
    global _streaming_config
    _streaming_config["enabled"] = True
    return {"status": "streaming_enabled", "config": _streaming_config}

@app.post("/api/streaming/stop")
async def stop_streaming():
    """Disable real-time streaming updates."""
    global _streaming_config
    _streaming_config["enabled"] = False
    return {"status": "streaming_disabled", "config": _streaming_config}

# ========== System Polish Endpoints ==========

class SystemPolishRequest(BaseModel):
    scope: str = "full"  # full|agents|codebase|documentation|tests
    iterations_per_agent: int = 100
    time_range_days: int = 30
    auto_apply: bool = False
    focus_areas: list = None

@app.post("/api/system-polish/start")
async def start_system_polish(request: SystemPolishRequest, background_tasks: BackgroundTasks):
    """Start a System Polish Refresh task."""
    import uuid
    polish_id = str(uuid.uuid4())[:8]

    # Store the request for the background task
    polish_config = {
        "polish_id": polish_id,
        "scope": request.scope,
        "iterations_per_agent": request.iterations_per_agent,
        "time_range_days": request.time_range_days,
        "auto_apply": request.auto_apply,
        "focus_areas": request.focus_areas or ["performance", "costs", "quality", "focus", "redundancy"],
        "started_at": datetime.now().isoformat(),
        "status": "running"
    }

    # Store config for status tracking
    config_path = Path.home() / ".ensemble" / "polish_results" / f"{polish_id}_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(polish_config, f, indent=2)

    logger.info(f"Started System Polish Refresh: {polish_id}")
    return {
        "polish_id": polish_id,
        "status": "started",
        "message": "System Polish Refresh initiated. Check /api/system-polish/status for progress."
    }

@app.get("/api/system-polish/status/{polish_id}")
async def get_polish_status(polish_id: str):
    """Get status of a System Polish Refresh task."""
    result_path = Path.home() / ".ensemble" / "polish_results" / f"{polish_id}.json"
    config_path = Path.home() / ".ensemble" / "polish_results" / f"{polish_id}_config.json"

    if result_path.exists():
        with open(result_path) as f:
            data = json.load(f)
        if "error" in data:
            return {"polish_id": polish_id, "status": "failed", "error": data["error"]}
        return {
            "polish_id": polish_id,
            "status": "completed",
            "result": data.get("result"),
            "completed_at": data.get("completed_at")
        }

    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        return {"polish_id": polish_id, "status": "running", "config": config}

    return {"polish_id": polish_id, "status": "not_found"}

@app.get("/api/system-polish/history")
async def get_polish_history(limit: int = 10):
    """Get history of System Polish Refresh executions."""
    results_dir = Path.home() / ".ensemble" / "polish_results"
    if not results_dir.exists():
        return {"history": [], "count": 0}

    history = []
    for result_file in sorted(results_dir.glob("*_config.json"), reverse=True)[:limit]:
        polish_id = result_file.stem.replace("_config", "")
        with open(result_file) as f:
            config = json.load(f)

        # Check if completed
        completed_path = results_dir / f"{polish_id}.json"
        status = "completed" if completed_path.exists() else "running"

        history.append({
            "polish_id": polish_id,
            "scope": config.get("scope"),
            "status": status,
            "started_at": config.get("started_at")
        })

    return {"history": history, "count": len(history)}

# ========== Guardrail System Endpoints ==========

@app.get("/api/guardrails/stats")
async def get_guardrail_stats():
    """Get guardrail system statistics."""
    try:
        from src.runtime.agents.guardrail_system import get_guardrail_system
        system = get_guardrail_system()
        return system.get_guardrail_stats()
    except Exception as e:
        logger.error(f"Error getting guardrail stats: {e}")
        return {"error": str(e)}

@app.get("/api/guardrails/agent/{agent_type:path}")
async def get_guardrails_for_agent(agent_type: str):
    """Get guardrails applicable to a specific agent type."""
    try:
        from src.runtime.agents.guardrail_system import get_guardrail_system
        system = get_guardrail_system()
        guardrails = system.get_guardrails_for_agent(agent_type)
        return {
            "agent_type": agent_type,
            "guardrails": [
                {
                    "id": g.id,
                    "text": g.text,
                    "category": g.category.value,
                    "severity": g.severity,
                    "success_rate": g.success_rate
                }
                for g in guardrails
            ],
            "count": len(guardrails)
        }
    except Exception as e:
        logger.error(f"Error getting guardrails for {agent_type}: {e}")
        return {"error": str(e)}

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