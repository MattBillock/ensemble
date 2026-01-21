import asyncio
import json
import os
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
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
from src.runtime.agents.log_monitor import get_log_monitor, init_log_monitor

load_dotenv()

class ProblemRequest(BaseModel):
    problem: str
    budget_tier: str = "balanced"  # full_firepower, balanced, economical
    auto_continue: bool = True  # If True, auto-continue through milestones without approval
    fully_autonomous: bool = False  # If True, bypass ALL confirmations (not default - must be explicit)


class BugFixRequest(BaseModel):
    """Request to fix a bug or issue."""
    bug_description: str
    reproduction_steps: Optional[List[str]] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    affected_files: Optional[List[str]] = None
    priority: str = "medium"  # critical, high, medium, low
    auto_apply: bool = False  # If True, apply fix automatically
    budget_tier: str = "balanced"

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

        # YOLO Mode - when enabled, skip all review phases and run fully autonomous
        self.yolo_mode = False

        # Swarm Pause - when enabled, agents will pause at next checkpoint
        self.swarm_paused = False
        self.pause_reason = None

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
            self.active_agents[agent_id]["result"] = result
            self.active_agents[agent_id]["generated_files"] = generated_files
            self.active_agents[agent_id]["completed_at"] = end_time.isoformat()
            self.active_agents[agent_id]["duration_ms"] = duration_ms

            if generated_files:
                file_count = len(generated_files)
                self.active_agents[agent_id]["logs"].append(f"📁 Generated {file_count} file(s)")

            # Check if agent is waiting for user input
            if result and result.get("status") == "needs_user_input":
                self.active_agents[agent_id]["status"] = "awaiting_user_input"
                self.active_agents[agent_id]["awaiting_question_id"] = result.get("question_id")
                self.active_agents[agent_id]["continuation_context"] = {
                    "original_input": input_data,
                    "question": result.get("user_question"),
                    "agent_type": self.active_agents[agent_id].get("type"),
                    "budget_tier": self.active_agents[agent_id].get("budget_tier"),
                    "request_id": request_id
                }
                self.active_agents[agent_id]["logs"].append(
                    f"❓ Waiting for user input: {result.get('user_question', 'No question provided')}"
                )
                self.logger.info(
                    f"Agent awaiting user input",
                    extra={
                        'request_id': request_id,
                        'agent_id': agent_id,
                        'question_id': result.get('question_id'),
                        'duration_ms': duration_ms
                    }
                )
            else:
                self.active_agents[agent_id]["status"] = "completed"
                self.active_agents[agent_id]["logs"].append(f"✅ Completed successfully")

            # Only log completion if actually completed (not waiting for input)
            if self.active_agents[agent_id]["status"] == "completed":
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

    async def spawn_executive_director(self, problem_description: str, budget_tier: str = "balanced", auto_continue: bool = True, fully_autonomous: bool = False):
        """Spawn the Executive Director agent to handle the problem.

        Args:
            problem_description: The task/problem for the agent to solve
            budget_tier: Budget tier for model selection (full_firepower, balanced, economical)
            auto_continue: If True, agents automatically continue through milestones without approval
            fully_autonomous: If True, bypass ALL user confirmations and proceed with best judgment
        """
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        self.request_count += 1

        agent_id = f"exec_dir_{self.request_count}"

        # Generate family name for this task group - all agents will share this surname
        from src.runtime.agents.naming.name_generator import generate_family_name
        family_name = generate_family_name()

        self.logger.info(f"Spawning Executive Director", extra={
            'request_id': request_id,
            'agent_id': agent_id,
            'budget_tier': budget_tier,
            'family_name': family_name,
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
            # Load Executive Director from consolidated agents/ folder
            exec_dir_path = self.project_root / "agents" / "leadership" / "executive_director.md"
            exec_dir_def = AgentDefinition.from_file(exec_dir_path)

            # Set up tools
            tools = ToolRegistry.default(exec_dir_def)
            spawn_tool = SpawnAgentTool(
                agent_types_dir=self.project_root / "agents",
                api_key=self.api_key,
                tools=tools,
                budget_tier=budget_tier,  # Pass budget tier to spawned agents
                parent_agent_id=agent_id,  # This agent is the parent for spawned agents
                request_id=request_id,  # Pass request ID for tracing
                session_id=session_id,  # Pass session ID for swarm state tracking
                auto_continue=auto_continue,  # Pass auto_continue for milestone handling
                family_name=family_name,  # Pass family name to all child agents
                fully_autonomous=fully_autonomous  # Pass fully_autonomous for bypassing confirmations
            )
            tools.register(spawn_tool)

            # Ensure output directory exists
            output_dir = self.project_root / "src" / "field" / "ensemble_ui" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate project_id for this execution
            project_id = str(uuid.uuid4())[:8]

            # Store agent info with tracing metadata
            self.active_agents[agent_id] = {
                "type": "executive_director",
                "name": agent_id,  # Whimsical name (same as agent_id)
                "agent_class": "executive_director",  # Canonical agent class name
                "status": "initializing",
                "problem": problem_description,
                "budget_tier": budget_tier,
                "messages": [],  # Conversation history
                "request_id": request_id,
                "project_id": project_id,  # Project grouping
                "family_name": family_name,  # Family name for agent group
                "current_stage": "requirements",  # Stage tracking
                "created_at": datetime.now().isoformat(),
                "parent_agent_id": None,  # Top-level agent
                "spawned_agents": [],  # Track children
                "metadata": {
                    "problem_length": len(problem_description),
                    "budget_tier": budget_tier,
                    "family_name": family_name
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
                session_id=session_id,  # For swarm state tracking
                auto_continue=auto_continue,  # For milestone handling
                fully_autonomous=fully_autonomous  # Bypass all confirmations when True
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
                "name": agent_id,  # Whimsical name
                "agent_class": "executive_director",
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

    async def continue_agent_with_answer(self, agent_id: str, answer: str):
        """Continue an agent execution after receiving user answer.

        Args:
            agent_id: ID of the agent that was waiting for input
            answer: User's answer to the agent's question
        """
        agent_info = self.active_agents.get(agent_id)
        if not agent_info:
            self.logger.warning(f"Attempted to continue non-existent agent",
                              extra={'request_id': 'continuation', 'agent_id': agent_id})
            return None, {"error": "Agent not found"}

        context = agent_info.get("continuation_context", {})
        original_input = context.get("original_input", {})
        question = context.get("question", "")
        original_request_id = context.get("request_id", "unknown")
        budget_tier = context.get("budget_tier", "balanced")

        self.logger.info(f"Continuing agent with user answer",
                        extra={
                            'request_id': original_request_id,
                            'agent_id': agent_id,
                            'answer_length': len(answer)
                        })

        # Build continuation problem description
        original_problem = original_input.get("user_vision", "")
        continuation_problem = f"""CONTINUATION OF PREVIOUS TASK

## Original Task
{original_problem}

## Previous Question
{question}

## User's Answer
{answer}

## Instructions
The user has answered your question above. Please continue with implementation based on their clarification. Do not ask the same question again - proceed with the approach based on their answer."""

        # Mark old agent as superseded
        self.active_agents[agent_id]["status"] = "superseded"
        self.active_agents[agent_id]["superseded_by_answer"] = True
        self.active_agents[agent_id]["logs"].append(f"➡️ Continued with new agent after user answer")

        # Spawn a new executive director with continuation context
        return await self.spawn_executive_director(
            problem_description=continuation_problem,
            budget_tier=budget_tier,
            auto_continue=True
        )

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

# Start recovery orchestrator and log monitor on app startup
@app.on_event("startup")
async def startup_event():
    """Initialize background services on startup."""
    # Initialize log monitor first to capture any startup errors
    try:
        log_monitor = init_log_monitor()
        logger.info("Log monitor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize log monitor: {e}")

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
        # Use YOLO mode if enabled globally or if explicitly set in request
        use_autonomous = request.fully_autonomous or orchestrator.yolo_mode

        # Spawn Executive Director with problem description and budget tier
        agent_id, result = await orchestrator.spawn_executive_director(
            request.problem,
            budget_tier=request.budget_tier,
            auto_continue=request.auto_continue,
            fully_autonomous=use_autonomous
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


@app.post("/api/fix-bug")
async def fix_bug(request: BugFixRequest, background_tasks: BackgroundTasks):
    """
    HTTP endpoint to trigger autonomous bug fix.

    Spawns a Bug Fix Director that analyzes the issue, creates a fix plan,
    and orchestrates sub-agents to implement and test the fix.
    """
    request_id = str(uuid.uuid4())[:8]
    orchestrator.logger.info(
        f"API request: fix-bug",
        extra={
            "request_id": request_id,
            "agent_id": "api",
            "priority": request.priority,
            "budget_tier": request.budget_tier,
        },
    )

    try:
        # Build task description for Bug Fix Director
        task_parts = [f"Fix the following bug:\n\n{request.bug_description}"]

        if request.reproduction_steps:
            steps_text = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(request.reproduction_steps))
            task_parts.append(f"\nReproduction steps:\n{steps_text}")

        if request.expected_behavior:
            task_parts.append(f"\nExpected behavior: {request.expected_behavior}")

        if request.actual_behavior:
            task_parts.append(f"\nActual behavior: {request.actual_behavior}")

        if request.affected_files:
            files_text = ", ".join(request.affected_files)
            task_parts.append(f"\nPotentially affected files: {files_text}")

        task_parts.append(f"\nPriority: {request.priority}")
        task_parts.append(f"\nAuto-apply fix: {request.auto_apply}")

        task_description = "\n".join(task_parts)

        # Spawn Executive Director with bug fix task
        # The Executive Director will read the bug_fix_director.md for guidance
        bug_fix_task = f"""You are acting as a Bug Fix Director. Read agents/leadership/bug_fix_director.md for detailed instructions.

{task_description}

IMPORTANT: After fixing the bug, generate a summary report and save it to:
src/field/ensemble_ui/output/completed/bugfix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md

The report should include: root cause analysis, files modified, tests added, and verification results.
"""
        agent_id, result = await orchestrator.spawn_executive_director(
            bug_fix_task,
            budget_tier=request.budget_tier,
            auto_continue=True,
            fully_autonomous=True,  # Bug fix should be autonomous
        )

        orchestrator.logger.info(
            f"API response: fix-bug success",
            extra={
                "request_id": request_id,
                "agent_id": agent_id,
                "status": "success",
            },
        )

        return {
            "agent_id": agent_id,
            "status": "completed",
            "result": result,
            "priority": request.priority,
            "budget_tier": request.budget_tier,
        }
    except Exception as e:
        orchestrator.logger.error(
            f"API error: fix-bug failed: {str(e)}",
            extra={
                "request_id": request_id,
                "agent_id": "api",
                "error_type": type(e).__name__,
            },
        )
        return {"error": str(e), "status": "error"}


@app.get("/api/completed-reports")
async def get_completed_reports(limit: int = 50):
    """
    Get list of completed bug fix and other reports from the completed folder.
    """
    try:
        completed_dir = orchestrator.project_root / "src" / "field" / "ensemble_ui" / "output" / "completed"

        if not completed_dir.exists():
            return {"reports": [], "total": 0}

        reports = []
        for file_path in sorted(completed_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                content = file_path.read_text(encoding="utf-8")
                # Extract title from first line
                title = content.split("\n")[0].replace("#", "").strip() if content else file_path.name

                reports.append({
                    "id": file_path.stem,
                    "file_path": str(file_path.relative_to(orchestrator.project_root)),
                    "file_name": file_path.name,
                    "title": title,
                    "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "size_bytes": file_path.stat().st_size,
                })
            except Exception as e:
                logger.warning(f"Error reading report {file_path}: {e}")
                continue

        return {"reports": reports, "total": len(reports)}
    except Exception as e:
        logger.error(f"Error getting completed reports: {e}")
        return {"error": str(e), "reports": [], "total": 0}


@app.get("/api/completed-reports/{report_id}/content")
async def get_completed_report_content(report_id: str):
    """
    Get the full content of a completed report.
    """
    try:
        completed_dir = orchestrator.project_root / "src" / "field" / "ensemble_ui" / "output" / "completed"
        file_path = completed_dir / f"{report_id}.md"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        content = file_path.read_text(encoding="utf-8")

        return {
            "id": report_id,
            "file_path": str(file_path.relative_to(orchestrator.project_root)),
            "content": content,
            "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SpawnFromReportRequest(BaseModel):
    """Request to spawn a new task from a completed report."""
    problem_description: str
    budget_tier: str = "balanced"
    auto_continue: bool = True
    fully_autonomous: bool = False


@app.post("/api/completed-reports/{report_id}/spawn")
async def spawn_task_from_report(
    report_id: str,
    request: SpawnFromReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Spawn a new Executive Director task using context from a completed report.

    This enables users to start follow-up work based on completed reports,
    maintaining lineage between tasks.
    """
    try:
        # Get the source report
        completed_dir = orchestrator.project_root / "src" / "field" / "ensemble_ui" / "output" / "completed"
        file_path = completed_dir / f"{report_id}.md"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        report_content = file_path.read_text(encoding="utf-8")
        report_title = report_content.split("\n")[0].replace("#", "").strip() if report_content else report_id

        # Generate request ID
        new_request_id = f"report_spawn_{uuid.uuid4().hex[:8]}"

        # Build enhanced problem description with report context
        enhanced_problem = f"""Follow-up task from completed report: "{report_title}"

**User Request:**
{request.problem_description}

**Source Report Context:**
The following is a summary from the completed report that this task builds upon:

{report_content[:3000]}
{"..." if len(report_content) > 3000 else ""}
"""

        # Record lineage before starting the task
        from src.runtime.agents.runtime import AgentRuntime
        activity_tracker = AgentRuntime.get_activity_tracker()

        activity_tracker.record_request_started(
            request_id=new_request_id,
            prompt=request.problem_description,
            budget_tier=request.budget_tier
        )

        activity_tracker.record_task_spawned_from_report(
            report_id=report_id,
            report_title=report_title,
            new_request_id=new_request_id,
            problem_description=request.problem_description
        )

        # Use YOLO mode if enabled globally or if explicitly set in request
        use_autonomous = request.fully_autonomous or orchestrator.yolo_mode

        # Spawn Executive Director with problem description and budget tier
        agent_id, result = await orchestrator.spawn_executive_director(
            enhanced_problem,
            budget_tier=request.budget_tier,
            auto_continue=request.auto_continue,
            fully_autonomous=use_autonomous
        )

        return {
            "success": True,
            "request_id": new_request_id,
            "agent_id": agent_id,
            "message": f"Started new task from report '{report_title}'",
            "result": result,
            "lineage": {
                "source_type": "completed_report",
                "source_id": report_id,
                "source_title": report_title
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error spawning task from report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/completed-reports/{report_id}/spawned-tasks")
async def get_spawned_tasks_for_report(report_id: str):
    """
    Get all tasks that were spawned from a specific completed report.
    """
    try:
        from src.runtime.agents.runtime import AgentRuntime
        activity_tracker = AgentRuntime.get_activity_tracker()

        spawned_tasks = activity_tracker.get_tasks_spawned_from_report(report_id)

        return {
            "report_id": report_id,
            "spawned_tasks": spawned_tasks,
            "count": len(spawned_tasks)
        }
    except Exception as e:
        logger.error(f"Error getting spawned tasks for report {report_id}: {e}")
        return {"error": str(e), "spawned_tasks": [], "count": 0}


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

@app.post("/api/agents/{agent_id:path}/message")
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

@app.get("/api/activity/states/{agent_id:path}")
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

@app.post("/api/activity/questions/{question_id:path}/answer")
async def answer_question(question_id: str, answer: dict, background_tasks: BackgroundTasks):
    """Answer a pending question and trigger agent continuation"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()

    if "answer" not in answer:
        raise HTTPException(status_code=400, detail="Missing 'answer' field")

    user_answer = answer["answer"]
    tracker.record_answer(question_id, user_answer)

    # Find the agent waiting for this answer and trigger continuation
    waiting_agent_id = None
    for agent_id, agent_info in orchestrator.active_agents.items():
        if agent_info.get("awaiting_question_id") == question_id:
            waiting_agent_id = agent_id
            break

    if waiting_agent_id:
        # Trigger agent continuation with the user's answer
        new_agent_id, result = await orchestrator.continue_agent_with_answer(
            waiting_agent_id,
            user_answer
        )
        return {
            "success": True,
            "question_id": question_id,
            "continuation_agent_id": new_agent_id,
            "original_agent_id": waiting_agent_id
        }

    return {"success": True, "question_id": question_id}

@app.post("/api/activity/clear")
async def clear_activities():
    """Clear all activities and reset the tracker"""
    from src.runtime.agents.runtime import AgentRuntime
    tracker = AgentRuntime.get_activity_tracker()
    result = tracker.clear_all(include_activities=True, include_agents=True)
    return {"success": True, "cleared": result}

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


# ========== Project Summary Endpoints ==========

@app.get("/api/projects/summary")
async def get_projects_summary():
    """Get summary of all projects grouped by request_id from persistent storage."""
    from src.runtime.agents.runtime import AgentRuntime

    projects = {}
    activity_tracker = AgentRuntime.get_activity_tracker()

    # Get all agent states from activity tracker (persistent)
    agent_states = getattr(activity_tracker, 'agent_states', {})
    # Also get hierarchy for fallback data
    agent_hierarchy = getattr(activity_tracker, 'agent_hierarchy', {})

    for agent_id, state in agent_states.items():
        if not isinstance(state, dict):
            continue

        # Try to get request_id from state, fall back to hierarchy
        request_id = state.get("request_id")
        if not request_id:
            hierarchy_data = agent_hierarchy.get(agent_id, {})
            request_id = hierarchy_data.get("request_id", "unknown")
        if not request_id or request_id == "unknown":
            continue

        if request_id not in projects:
            projects[request_id] = {
                "project_id": request_id,
                "project_name": "",
                "total_agents": 0,
                "active_agents": 0,
                "completed_agents": 0,
                "failed_agents": 0,
                "awaiting_input": 0,
                "current_stage": "unknown",
                "created_at": state.get("started_at"),
                "agents": []
            }

        projects[request_id]["total_agents"] += 1
        status = state.get("status", "unknown")

        if status == "running":
            projects[request_id]["active_agents"] += 1
        elif status == "completed":
            projects[request_id]["completed_agents"] += 1
        elif status in ("failed", "error", "forever_failed"):
            projects[request_id]["failed_agents"] += 1
        elif status in ("awaiting_user_input", "needs_review"):
            projects[request_id]["awaiting_input"] += 1

        # Track agent info
        projects[request_id]["agents"].append({
            "agent_id": agent_id,
            "agent_type": state.get("agent_type", "unknown"),
            "status": status
        })

        # Get project name from problem field (the actual task description)
        # Priority: executive director's problem > any agent's problem > fallback to current_task
        agent_type = state.get("agent_type", "")
        problem = state.get("problem", "")

        if "executive" in agent_type.lower() or "director" in agent_type.lower():
            if problem and not projects[request_id]["project_name"]:
                projects[request_id]["project_name"] = problem[:80]

        # Fallback: use problem field from any agent if no name yet
        if not projects[request_id]["project_name"] and problem:
            projects[request_id]["project_name"] = problem[:80]

        # Last resort: use current_task but filter out tool-related messages
        if not projects[request_id]["project_name"]:
            task = state.get("current_task", "")
            # Skip status messages that don't describe the actual task
            skip_patterns = ["Using tool:", "Processing", "Thinking...", "Initializing",
                           "Completed", "Failed:", "Waiting for"]
            if task and not any(pattern in task for pattern in skip_patterns):
                projects[request_id]["project_name"] = task[:80]

    # Also check orchestrator.active_agents for any running tasks not yet in activity_tracker
    for agent_id, agent_info in orchestrator.active_agents.items():
        request_id = agent_info.get("request_id", "default")
        if request_id not in projects:
            projects[request_id] = {
                "project_id": request_id,
                "project_name": agent_info.get("problem", "")[:80] or "Active Task",
                "total_agents": 1,
                "active_agents": 1,
                "completed_agents": 0,
                "failed_agents": 0,
                "awaiting_input": 0,
                "current_stage": agent_info.get("current_stage", "running"),
                "created_at": agent_info.get("created_at"),
                "agents": []
            }

    # Get pending reviews and deliverable info for all projects
    from src.runtime.agents.swarm_state import get_swarm_state
    swarm_state = get_swarm_state()

    # Build a map of pending reviews per request_id
    pending_reviews_map = {}
    completed_reviews_map = {}
    try:
        # Get pending reviews
        pending_reviews = swarm_state.get_pending_reviews(status="pending")
        for review in pending_reviews:
            req_id = review.get("request_id")
            if req_id:
                if req_id not in pending_reviews_map:
                    pending_reviews_map[req_id] = []
                pending_reviews_map[req_id].append(review)

        # Get approved/implemented reviews (completed deliverables)
        approved_reviews = swarm_state.get_pending_reviews(status="approved")
        implemented_reviews = swarm_state.get_pending_reviews(status="implemented")
        for review in approved_reviews + implemented_reviews:
            req_id = review.get("request_id")
            if req_id:
                if req_id not in completed_reviews_map:
                    completed_reviews_map[req_id] = []
                completed_reviews_map[req_id].append(review)
    except Exception as e:
        logger.warning(f"Failed to get review data for projects: {e}")

    # Calculate stage distribution based on DELIVERABLE status, not just agents
    stage_counts = {}
    for p in projects.values():
        project_id = p["project_id"]

        # Count pending and completed reviews for this project
        pending_count = len(pending_reviews_map.get(project_id, []))
        completed_count = len(completed_reviews_map.get(project_id, []))

        p["pending_reviews"] = pending_count
        p["completed_deliverables"] = completed_count

        # Determine DELIVERABLE stage (primary status)
        if pending_count > 0:
            deliverable_stage = "pending_review"
        elif completed_count > 0 and p["active_agents"] == 0:
            deliverable_stage = "deliverables_complete"
        elif p["active_agents"] > 0:
            deliverable_stage = "in_progress"
        elif p["failed_agents"] > 0 and p["completed_agents"] == 0:
            deliverable_stage = "failed"
        elif p["awaiting_input"] > 0:
            deliverable_stage = "awaiting_input"
        elif p["completed_agents"] == p["total_agents"] and p["total_agents"] > 0:
            deliverable_stage = "agents_done"
        else:
            deliverable_stage = "idle"

        p["current_stage"] = deliverable_stage
        p["deliverable_status"] = deliverable_stage

        # Also track agent status separately for the second column
        if p["active_agents"] > 0:
            agent_stage = "running"
        elif p["failed_agents"] > 0:
            agent_stage = "failed"
        elif p["completed_agents"] > 0:
            agent_stage = "completed"
        else:
            agent_stage = "idle"
        p["agent_status"] = agent_stage

        stage_counts[deliverable_stage] = stage_counts.get(deliverable_stage, 0) + 1

    # Sort by created_at (newest first)
    sorted_projects = sorted(
        projects.values(),
        key=lambda x: x.get("created_at") or "",
        reverse=True
    )

    return {
        "projects": sorted_projects,
        "summary": {
            "total_projects": len(projects),
            "active_projects": sum(1 for p in projects.values() if p["active_agents"] > 0),
            "stage_distribution": stage_counts,
        }
    }


@app.post("/api/projects/{project_id}/continue")
async def continue_project(project_id: str, budget_tier: str = "balanced"):
    """Continue a project by spawning a new Executive Director with context."""
    from src.runtime.agents.runtime import AgentRuntime

    activity_tracker = AgentRuntime.get_activity_tracker()
    agent_states = getattr(activity_tracker, 'agent_states', {})

    # Find the original problem for this project
    problem = None
    completed_work = []

    for agent_id, state in agent_states.items():
        if not isinstance(state, dict):
            continue
        state_project_id = state.get("project_id") or state.get("request_id")
        if state_project_id == project_id:
            # Get the problem description
            if state.get("problem") and not problem:
                problem = state.get("problem")
            # Collect completed work summaries
            if state.get("status") == "completed" and state.get("summary"):
                completed_work.append({
                    "agent": state.get("agent_type") or state.get("agent_name"),
                    "summary": state.get("summary")
                })

    if not problem:
        return {"error": "Could not find original problem for this project", "status": "error"}

    # Build continuation prompt
    continuation_prompt = f"""CONTINUATION REQUEST:

Original Task: {problem}

This is a continuation of a previous session. The following work has already been completed:
"""
    if completed_work:
        for work in completed_work[:10]:  # Limit to 10 summaries
            continuation_prompt += f"\n- {work['agent']}: {work['summary'][:200]}"
    else:
        continuation_prompt += "\n(No completed work summaries available)"

    continuation_prompt += """

Please review the existing work and continue from where the previous session left off.
Do not restart from the beginning - identify remaining tasks and complete them."""

    try:
        agent_id, result = await orchestrator.spawn_executive_director(
            continuation_prompt,
            budget_tier=budget_tier,
            auto_continue=True,
            fully_autonomous=orchestrator.yolo_mode
        )

        return {
            "agent_id": agent_id,
            "status": "started",
            "project_id": project_id,
            "message": "Project continuation started"
        }
    except Exception as e:
        logger.error(f"Error continuing project {project_id}: {e}")
        return {"error": str(e), "status": "error"}


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
async def apply_single_recommendation(recommendation_id: str, background_tasks: BackgroundTasks):
    """Apply a single recommendation by spawning an Executive Director to implement it."""
    from src.runtime.agents.self_improvement import get_improvement_loop
    loop = get_improvement_loop()

    # First approve the recommendation
    approve_result = loop.approve_recommendation(recommendation_id)
    if not approve_result.get("success"):
        return approve_result

    # Get the recommendation details to build the task prompt
    recommendation = loop.get_recommendation_by_id(recommendation_id)
    if not recommendation:
        return {"success": False, "message": "Recommendation not found"}

    # Build a task prompt for the Executive Director
    rec_type = recommendation.get("type", "unknown")
    agent_name = recommendation.get("agent_name", "Unknown Agent")
    title = recommendation.get("title", "Improvement")
    description = recommendation.get("description", "")
    suggested_changes = recommendation.get("suggested_changes", {})

    # Create a detailed task prompt based on recommendation type
    if rec_type in ["model_upgrade", "model_downgrade"]:
        new_model = suggested_changes.get("new_model", "sonnet")
        task_prompt = f"""Self-Improvement Task: Update model configuration for {agent_name}

**Recommendation:** {title}
**Description:** {description}

**Required Change:**
Update the agent definition file for {agent_name} to use the '{new_model}' model.
The model preference is in the ## Model Preference section of the agent's markdown file.

After making the change:
1. Verify the syntax is correct
2. Update any related configuration if needed
3. Report the changes made"""

    elif rec_type in ["iteration_increase", "iteration_decrease"]:
        new_iterations = suggested_changes.get("new_max_iterations", 10)
        task_prompt = f"""Self-Improvement Task: Update iteration limit for {agent_name}

**Recommendation:** {title}
**Description:** {description}

**Required Change:**
Update the agent definition file for {agent_name} to use {new_iterations} max iterations.
The max iterations setting is in the ## Max Iterations section of the agent's markdown file.

After making the change:
1. Verify the syntax is correct
2. Report the changes made"""

    elif rec_type in ["definition_tweak", "definition_major"]:
        note = suggested_changes.get("note", description)
        task_prompt = f"""Self-Improvement Task: Improve agent definition for {agent_name}

**Recommendation:** {title}
**Description:** {description}

**Performance Insight to Address:**
{note}

**Required Changes:**
1. Review the current agent definition for {agent_name}
2. Identify the root cause of the performance issue described above
3. Update the agent's instructions, capabilities, or constraints to address the issue
4. Test the changes if possible
5. Report what was changed and why

Focus on improving the agent's effectiveness without breaking existing functionality.
Agent definition files are located in: agents/ directory (agents/leadership/, agents/coordinators/, agents/developers/, agents/testers/, agents/designers/, agents/support/)."""

    else:
        # Generic improvement task
        task_prompt = f"""Self-Improvement Task: {title}

**Agent:** {agent_name}
**Type:** {rec_type}
**Description:** {description}

**Suggested Changes:**
{json.dumps(suggested_changes, indent=2) if suggested_changes else 'Review and improve as needed'}

Please implement the recommended improvement and report what was done."""

    # Spawn an Executive Director to implement the improvement
    try:
        asyncio.create_task(
            orchestrator.spawn_executive_director(
                problem_description=task_prompt,
                budget_tier="balanced",
                auto_continue=True
            )
        )

        # Mark the recommendation as being implemented
        loop.mark_recommendation_in_progress(recommendation_id)

        return {
            "success": True,
            "message": f"Spawned Executive Director to implement: {title}",
            "recommendation_id": recommendation_id,
            "agent_spawned": True
        }
    except Exception as e:
        logger.error(f"Failed to spawn Executive Director for recommendation: {e}")
        return {
            "success": False,
            "message": f"Failed to spawn agent: {str(e)}",
            "recommendation_id": recommendation_id
        }

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

@app.get("/api/swarm/agents/{agent_id:path}")
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

# ========== Pending Review Endpoints ==========

class ReviewApprovalAction(BaseModel):
    review_id: int
    override_params: Optional[Dict[str, Any]] = None


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content."""
    import yaml

    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].lstrip('\n')
        return frontmatter or {}, body
    except yaml.YAMLError:
        return {}, content


async def execute_review_action(
    review: Dict[str, Any],
    action: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute an action based on review approval."""

    if action == "start_implementation":
        # Spawn executive director to implement based on the requirements doc
        budget_tier = params.get("budget_tier", "balanced")
        file_path = review.get("file_path", "")

        # Build task prompt
        task_prompt = f"""Implement the requirements documented in: {file_path}

Read the requirements document and implement all specified features.
Follow TDD methodology: write tests first, then implementation."""

        agent_id, result = await orchestrator.spawn_executive_director(
            problem_description=task_prompt,
            budget_tier=budget_tier,
            auto_continue=True
        )
        return {"agent_id": agent_id, "status": result.get("status")}

    elif action == "create_tests":
        # Spawn test coordinator to create tests
        budget_tier = params.get("budget_tier", "balanced")
        file_path = review.get("file_path", "")

        task_prompt = f"""Create tests based on: {file_path}

Read the document and create comprehensive test coverage."""

        agent_id, result = await orchestrator.spawn_executive_director(
            problem_description=task_prompt,
            budget_tier=budget_tier,
            auto_continue=True
        )
        return {"agent_id": agent_id, "status": result.get("status")}

    elif action == "run_analysis":
        # Trigger analysis based on architecture doc
        return {"status": "analysis_triggered"}

    else:
        return {"error": f"Unknown action: {action}"}


@app.get("/api/pending-reviews")
async def get_pending_reviews(
    status: str = "pending",
    limit: int = 50,
    offset: int = 0
):
    """Get pending review items."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()
        reviews = swarm.get_pending_reviews(status=status, limit=limit, offset=offset)
        return {"reviews": reviews, "count": len(reviews)}
    except Exception as e:
        logger.error(f"Error getting pending reviews: {e}")
        return {"error": str(e), "reviews": [], "count": 0}


@app.get("/api/pending-reviews/{review_id}")
async def get_pending_review(review_id: int):
    """Get a specific pending review."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()
        review = swarm.get_pending_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pending-reviews/{review_id}/content")
async def get_pending_review_content(review_id: int):
    """Get full file content for a pending review."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()
        review = swarm.get_pending_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        # Read file content from disk
        file_path = orchestrator.project_root / review["file_path"]
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        content = file_path.read_text(encoding='utf-8')
        frontmatter, body = parse_frontmatter(content)

        return {
            "review_id": review_id,
            "file_path": review["file_path"],
            "frontmatter": frontmatter,
            "content": body,
            "full_content": content
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pending-reviews/{review_id}/approve")
async def approve_pending_review(review_id: int, action: ReviewApprovalAction = None):
    """Approve a pending review and execute its action."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()
        review = swarm.get_pending_review(review_id)

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        if review["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Review already {review['status']}")

        # Get action from review (or override)
        action_name = review.get("action", "start_implementation")
        action_params = {}
        if action and action.override_params:
            action_params = action.override_params
        elif review.get("action_params"):
            action_params = review["action_params"]

        # Execute action based on type
        result = await execute_review_action(review, action_name, action_params)

        # Update review status to in_progress (agent is running)
        # Status will be updated to 'completed' when agent finishes
        swarm.update_pending_review(review_id, status="in_progress", execution_result=result)

        return {
            "success": True,
            "review_id": review_id,
            "action_executed": action_name,
            "result": result,
            "agent_id": result.get("agent_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pending-reviews/{review_id}/reject")
async def reject_pending_review(review_id: int, reason: str = None):
    """Reject a pending review."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()
        review = swarm.get_pending_review(review_id)

        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        swarm.update_pending_review(review_id, status="rejected")

        return {"success": True, "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pending-reviews/scan")
async def scan_for_pending_reviews():
    """Manually trigger scan for new reviewable files.

    Note: In YOLO mode, this will skip creating pending reviews to allow
    fully autonomous operation without human review gates.
    """
    try:
        from src.runtime.agents.pending_review_scanner import PendingReviewScanner
        scanner = PendingReviewScanner(orchestrator.project_root)
        # Pass YOLO mode to scanner - when enabled, skip creating pending reviews
        new_reviews = scanner.scan_output_directory(yolo_mode=orchestrator.yolo_mode)
        return {
            "scanned": True,
            "new_reviews": len(new_reviews),
            "reviews": new_reviews,
            "yolo_mode": orchestrator.yolo_mode
        }
    except Exception as e:
        logger.error(f"Error scanning for reviews: {e}")
        return {"error": str(e), "scanned": False, "new_reviews": 0}


@app.post("/api/pending-reviews/approve-all")
async def approve_all_pending_reviews(background_tasks: BackgroundTasks):
    """Approve all pending reviews and spawn Executive Directors for each."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()

        # Get all pending reviews
        pending = swarm.get_pending_reviews(status='pending')
        logger.info(f"Approve All: Found {len(pending) if pending else 0} pending reviews")

        if not pending:
            return {"success": True, "message": "No pending reviews to approve", "approved": 0}

        approved_count = 0
        results = []

        for review in pending:
            review_id = review.get('id')
            file_path = review.get("file_path", "")
            review_type = review.get("review_type", "unknown")

            logger.info(f"Processing review {review_id}: {file_path} (type: {review_type})")

            try:
                # Mark as in_progress
                swarm.update_pending_review(review_id, status='in_progress')

                # Read the file content to create a proper problem description
                problem_desc = f"Implement the requirements defined in: {file_path}"

                # Try to read the file for more context
                try:
                    full_path = orchestrator.project_root / file_path.lstrip('/')
                    if full_path.exists():
                        content = full_path.read_text()
                        # Extract first line or title as problem summary
                        first_line = content.split('\n')[0].strip('# \n')
                        if first_line:
                            problem_desc = f"Implement: {first_line}\n\nFull requirements in: {file_path}"
                except Exception as read_err:
                    logger.warning(f"Could not read file {file_path}: {read_err}")

                # Spawn an executive director for this review
                logger.info(f"Spawning Executive Director for: {problem_desc[:100]}...")
                agent_id, result = await orchestrator.spawn_executive_director(
                    problem_desc,
                    budget_tier="balanced",
                    auto_continue=True,
                    fully_autonomous=True  # Run fully autonomous for bulk approval
                )

                # Update review with execution result
                swarm.update_pending_review_status(
                    review_id,
                    'in_progress',
                    execution_result={'agent_id': agent_id, 'status': result.get('status')}
                )

                results.append({
                    'review_id': review_id,
                    'file_path': file_path,
                    'agent_id': agent_id,
                    'status': 'started',
                    'problem': problem_desc[:100]
                })
                approved_count += 1
                logger.info(f"Successfully spawned agent {agent_id} for review {review_id}")

            except Exception as e:
                logger.error(f"Error approving review {review_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                results.append({
                    'review_id': review_id,
                    'file_path': file_path,
                    'status': 'error',
                    'error': str(e)
                })

        return {
            "success": True,
            "message": f"Spawned {approved_count} Executive Director(s) for {len(pending)} pending reviews",
            "approved": approved_count,
            "total": len(pending),
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in bulk approval: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "approved": 0}


@app.post("/api/pending-reviews/reconcile")
async def reconcile_pending_review_statuses():
    """
    Reconcile pending review statuses with actual agent states.

    Reviews marked as 'in_progress' but with no running agent will be
    updated to 'completed' or 'stalled' based on agent completion status.
    """
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        from src.runtime.agents.runtime import AgentRuntime

        swarm = get_swarm_state()
        activity_tracker = AgentRuntime.get_activity_tracker()

        # Get all in_progress reviews
        in_progress = swarm.get_pending_reviews(status='in_progress')
        logger.info(f"Reconcile: Found {len(in_progress) if in_progress else 0} in_progress reviews")

        if not in_progress:
            return {"success": True, "message": "No in_progress reviews to reconcile", "updated": 0}

        # Get current running agents
        running_agents = set()
        all_states = activity_tracker.get_all_agent_states()
        for agent_id, state in all_states.items():
            if isinstance(state, dict) and state.get('status') == 'running':
                running_agents.add(agent_id)

        updated_count = 0
        results = []

        for review in in_progress:
            review_id = review.get('id')
            execution_result = review.get('execution_result', {})
            agent_id = None

            # Extract agent_id from execution_result
            if isinstance(execution_result, dict):
                agent_id = execution_result.get('agent_id')
            elif isinstance(execution_result, str):
                try:
                    import json
                    result_data = json.loads(execution_result)
                    agent_id = result_data.get('agent_id')
                except:
                    pass

            # Check if agent is still running
            is_running = agent_id in running_agents if agent_id else False

            if not is_running:
                # Check if agent completed successfully or failed
                agent_state = all_states.get(agent_id, {}) if agent_id else {}
                agent_status = agent_state.get('status', 'unknown') if isinstance(agent_state, dict) else 'unknown'

                # Determine new status
                if agent_status == 'completed':
                    new_status = 'completed'
                elif agent_status in ('failed', 'error', 'forever_failed'):
                    new_status = 'failed'
                else:
                    # No agent found or unknown - mark as stalled
                    new_status = 'stalled'

                swarm.update_pending_review(review_id, status=new_status)
                updated_count += 1
                results.append({
                    'review_id': review_id,
                    'agent_id': agent_id,
                    'old_status': 'in_progress',
                    'new_status': new_status
                })

        return {
            "success": True,
            "message": f"Reconciled {updated_count} of {len(in_progress)} in_progress reviews",
            "updated": updated_count,
            "total_checked": len(in_progress),
            "results": results
        }

    except Exception as e:
        logger.error(f"Error reconciling reviews: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "updated": 0}


@app.get("/api/agent-improvement-reports")
async def get_agent_improvement_reports(limit: int = 50):
    """Get reports of agents that need improvement."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()
        reports = swarm.get_improvement_reports(limit=limit)
        return {"reports": reports, "count": len(reports)}
    except Exception as e:
        logger.error(f"Error getting improvement reports: {e}")
        return {"error": str(e), "reports": [], "count": 0}


# ========== Agent Stats API ==========

@app.get("/api/agent-stats")
async def get_all_agent_stats():
    """Get stats for all agent classes."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        from src.runtime.agents.achievements import get_achievement_tracker

        swarm = get_swarm_state()
        tracker = get_achievement_tracker()

        # Get unique agent classes from agents table
        agents_data = swarm.get_agents_summary()

        # Get achievement counts per agent class
        achievement_stats = tracker.get_achievement_stats()
        top_agents = {a['agent']: a['count'] for a in achievement_stats.get('top_agents', [])}

        # Build agent stats list
        agent_stats = []
        for agent in agents_data:
            agent_class = agent.get('agent_name', 'Unknown')
            agent_stats.append({
                'agent_class': agent_class,
                'total_runs': agent.get('count', 0),
                'achievement_count': top_agents.get(agent_class, 0),
                'last_activity': agent.get('last_activity'),
                'status': agent.get('status', 'idle')
            })

        return {"agents": agent_stats, "count": len(agent_stats)}
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        return {"error": str(e), "agents": [], "count": 0}


@app.get("/api/agent-stats/{agent_class}")
async def get_agent_details(agent_class: str):
    """Get detailed stats for a specific agent class."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        from src.runtime.agents.achievements import get_achievement_tracker
        from src.runtime.agents.runtime import AgentRuntime

        swarm = get_swarm_state()
        tracker = get_achievement_tracker()

        # Get agent's achievements
        achievements = tracker.get_achievements_for_agent(agent_class)

        # Get recent activities from activity tracker
        activity_tracker = AgentRuntime.get_activity_tracker()
        activities = []
        for activity in activity_tracker.activities[-100:]:  # Last 100 activities
            if hasattr(activity, 'agent_name') and activity.agent_name == agent_class:
                # Handle timestamp - could be datetime or already a string
                timestamp = getattr(activity, 'timestamp', None)
                if timestamp is not None:
                    if hasattr(timestamp, 'isoformat'):
                        timestamp = timestamp.isoformat()
                    # If already a string, keep it as is

                activities.append({
                    'type': activity.activity_type.value if hasattr(activity.activity_type, 'value') else str(activity.activity_type),
                    'timestamp': timestamp,
                    'data': getattr(activity, 'data', {}),
                    'agent_id': getattr(activity, 'agent_id', None)
                })

        # Get running agents of this class
        running_agents = []
        for agent_id, agent_data in orchestrator.active_agents.items():
            if agent_data.get('name') == agent_class or agent_data.get('agent_class') == agent_class:
                running_agents.append({
                    'agent_id': agent_id,
                    'status': agent_data.get('status', 'unknown'),
                    'started_at': agent_data.get('started_at'),
                    'task': agent_data.get('task', '')[:100]  # First 100 chars of task
                })

        return {
            'agent_class': agent_class,
            'achievements': achievements,
            'achievement_count': len(achievements),
            'recent_activities': activities[-20:],  # Last 20 activities
            'running_agents': running_agents,
            'is_active': len(running_agents) > 0
        }
    except Exception as e:
        logger.error(f"Error getting agent details: {e}")
        return {"error": str(e), "agent_class": agent_class}


@app.get("/api/agents/running")
async def get_running_agents():
    """Get list of currently running agents."""
    try:
        running = []
        for agent_id, agent_data in orchestrator.active_agents.items():
            running.append({
                'agent_id': agent_id,
                'name': agent_data.get('name', 'Unknown'),
                'agent_class': agent_data.get('agent_class', agent_data.get('name', 'Unknown')),
                'status': agent_data.get('status', 'unknown'),
                'started_at': agent_data.get('started_at'),
                'task': agent_data.get('task', '')[:200]
            })
        return {"agents": running, "count": len(running)}
    except Exception as e:
        logger.error(f"Error getting running agents: {e}")
        return {"error": str(e), "agents": [], "count": 0}


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

@app.post("/api/recovery/trigger/{agent_id:path}")
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


@app.post("/api/agents/{agent_id:path}/restart")
async def restart_agent_job(
    agent_id: str,
    clear_messages: bool = True,
    new_max_iterations: Optional[int] = None
):
    """
    Properly restart a failed/stalled agent job.

    This resets the agent's state (iteration=0, clears errors) and re-executes it
    with the same input data. Unlike recovery which creates new agents, this
    restarts the existing agent in-place.
    """
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        from src.runtime.agents.definition import AgentDefinition
        from src.runtime.agents.runtime import AgentRuntime
        from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool
        from pathlib import Path

        swarm_state = get_swarm_state()

        # Get agent info before restart
        agent = swarm_state.get_agent(agent_id)
        if not agent:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        # Store original input data for re-execution
        raw_input_data = agent.get('input_data', {})

        # Robustly convert input_data to a dict
        import json
        input_data = {}
        if raw_input_data:
            if isinstance(raw_input_data, dict):
                input_data = raw_input_data
            elif isinstance(raw_input_data, str):
                try:
                    parsed = json.loads(raw_input_data)
                    if isinstance(parsed, dict):
                        input_data = parsed
                    else:
                        input_data = {"task": str(parsed)}
                except (json.JSONDecodeError, TypeError, ValueError):
                    input_data = {"task": raw_input_data}
            else:
                input_data = {"task": str(raw_input_data)}

        # Ensure we have at least a problem/task field
        if not input_data:
            # Try to get problem from agent state
            problem = agent.get('problem', '') or agent.get('current_task', '')
            if problem:
                input_data = {"problem": problem}
            else:
                input_data = {"problem": "Continue previous task"}

        logger.info(f"Restarting agent {agent_id} with input_data: {input_data}")

        agent_type = agent['agent_type']
        session_id = agent['session_id']
        parent_agent_id = agent.get('parent_agent_id')
        request_id = agent.get('request_id')

        # Restart the agent (reset state)
        restarted = swarm_state.restart_agent(
            agent_id=agent_id,
            clear_messages=clear_messages,
            new_max_iterations=new_max_iterations
        )

        if not restarted:
            return {"success": False, "error": "Failed to restart agent"}

        # Re-execute the agent in background
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"success": False, "error": "No API key configured"}

        def execute_agent():
            try:
                # Load agent definition
                agent_types_dir = Path(__file__).parent.parent.parent.parent.parent
                agent_def_path = agent_types_dir / f"{agent_type}.md"

                if not agent_def_path.exists():
                    logger.error(f"Agent definition not found: {agent_def_path}")
                    swarm_state.update_agent_status(agent_id, "failed", error_message="Agent definition not found")
                    return

                agent_definition = AgentDefinition.from_file(agent_def_path)

                # Create tools
                tools = ToolRegistry.default(
                    agent_definition=agent_definition,
                    request_id=request_id,
                    session_id=session_id,
                    agent_id=agent_id
                )

                # Add spawn tool
                spawn_tool = SpawnAgentTool(
                    agent_types_dir=agent_types_dir,
                    api_key=api_key,
                    tools=None,
                    budget_tier="balanced",
                    parent_agent_id=agent_id,
                    request_id=request_id,
                    session_id=session_id
                )
                tools.register(spawn_tool)

                # Create runtime and execute
                runtime = AgentRuntime(
                    agent_definition,
                    api_key=api_key,
                    tools=tools,
                    budget_tier="balanced",
                    agent_id=agent_id,
                    request_id=request_id,
                    parent_agent_id=parent_agent_id,
                    session_id=session_id
                )

                result = runtime.execute(input_data)
                logger.info(f"Restarted agent {agent_id} completed: {result.get('status')}")

            except Exception as e:
                logger.error(f"Restarted agent {agent_id} failed: {e}")
                swarm_state.update_agent_status(agent_id, "failed", error_message=str(e))

        # Execute in background thread
        import threading
        thread = threading.Thread(target=execute_agent, daemon=True)
        thread.start()

        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {agent_id} restarted with iteration=0",
            "agent_type": agent_type,
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Error restarting agent {agent_id}: {e}")
        return {"success": False, "error": str(e)}


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
        # Stats are nested under "overall" key
        overall = stats.get("overall", {})

        # Calculate estimated costs (rough estimates based on Claude pricing)
        # These are approximate - actual costs depend on the specific model used
        cost_per_1k_input = 0.003  # ~$3/million input tokens (Sonnet average)
        cost_per_1k_output = 0.015  # ~$15/million output tokens

        total_input = overall.get("total_input_tokens", 0) or 0
        total_output = overall.get("total_output_tokens", 0) or 0

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
                "total_executions": overall.get("total_executions", 0) or 0,
                "successful_executions": overall.get("successful", 0) or 0,
                "failed_executions": overall.get("failed", 0) or 0
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

# Global streaming configuration with thread safety
_streaming_config = {
    "enabled": True,
    "poll_interval_ms": 2000,
    "event_types": None
}
_streaming_config_lock = asyncio.Lock()

@app.get("/api/streaming/config")
async def get_streaming_config():
    """Get current streaming/polling configuration."""
    async with _streaming_config_lock:
        return _streaming_config.copy()

@app.post("/api/streaming/config")
async def update_streaming_config(config: StreamingConfig):
    """Update streaming/polling configuration."""
    async with _streaming_config_lock:
        _streaming_config["enabled"] = config.enabled
        _streaming_config["poll_interval_ms"] = max(500, min(config.poll_interval_ms, 30000))  # Clamp between 500ms and 30s
        _streaming_config["event_types"] = config.event_types

        logger.info(f"Streaming config updated: enabled={config.enabled}, interval={_streaming_config['poll_interval_ms']}ms")

        return _streaming_config.copy()

@app.post("/api/streaming/start")
async def start_streaming():
    """Enable real-time streaming updates."""
    async with _streaming_config_lock:
        _streaming_config["enabled"] = True
        return {"status": "streaming_enabled", "config": _streaming_config.copy()}

@app.post("/api/streaming/stop")
async def stop_streaming():
    """Disable real-time streaming updates."""
    async with _streaming_config_lock:
        _streaming_config["enabled"] = False
        return {"status": "streaming_disabled", "config": _streaming_config.copy()}

# ========== YOLO Mode Endpoints ==========

@app.get("/api/yolo-mode")
async def get_yolo_mode():
    """Get current YOLO mode status. When enabled, all tasks run fully autonomously without review."""
    return {
        "enabled": orchestrator.yolo_mode,
        "description": "YOLO Mode skips all human review phases and runs tasks fully autonomously."
    }

@app.post("/api/yolo-mode")
async def set_yolo_mode(enabled: bool = True):
    """Enable or disable YOLO mode. When enabled, all new tasks run fully autonomously."""
    orchestrator.yolo_mode = enabled
    status = "enabled" if enabled else "disabled"
    logger.info(f"YOLO Mode {status} - all new tasks will run {'fully autonomous' if enabled else 'with human review'}")

    cleared_reviews = 0
    if enabled:
        # Auto-clear existing pending reviews when enabling YOLO mode
        try:
            from src.runtime.agents.swarm_state import get_swarm_state
            swarm = get_swarm_state()
            pending = swarm.get_pending_reviews(status='pending')
            for review in pending:
                swarm.update_pending_review(review['id'], status='auto_approved_yolo')
                cleared_reviews += 1
            if cleared_reviews > 0:
                logger.info(f"YOLO Mode: Auto-approved {cleared_reviews} pending reviews")
        except Exception as e:
            logger.warning(f"Failed to auto-clear pending reviews: {e}")

    return {
        "enabled": orchestrator.yolo_mode,
        "message": f"YOLO Mode {status}. {'All review phases will be skipped.' if enabled else 'Human review is required.'}",
        "cleared_reviews": cleared_reviews
    }

@app.post("/api/yolo-mode/enable")
async def enable_yolo_mode():
    """Shortcut to enable YOLO mode. Also auto-approves any pending reviews."""
    orchestrator.yolo_mode = True
    logger.info("YOLO Mode ENABLED - Bumpers off, full autonomous operation")

    cleared_reviews = 0
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm = get_swarm_state()
        pending = swarm.get_pending_reviews(status='pending')
        for review in pending:
            swarm.update_pending_review(review['id'], status='auto_approved_yolo')
            cleared_reviews += 1
        if cleared_reviews > 0:
            logger.info(f"YOLO Mode: Auto-approved {cleared_reviews} pending reviews")
    except Exception as e:
        logger.warning(f"Failed to auto-clear pending reviews: {e}")

    return {
        "enabled": True,
        "message": f"YOLO Mode activated. No reviews, no regrets. Auto-approved {cleared_reviews} pending reviews.",
        "cleared_reviews": cleared_reviews
    }

@app.post("/api/yolo-mode/disable")
async def disable_yolo_mode():
    """Shortcut to disable YOLO mode."""
    orchestrator.yolo_mode = False
    logger.info("YOLO Mode DISABLED - Human review required")
    return {"enabled": False, "message": "YOLO Mode deactivated. Back to safety."}


# ========== Zombie Agent Cleanup ==========

@app.post("/api/agents/clear-zombies")
async def clear_zombie_agents():
    """
    Clear zombie agents from the orchestrator.

    Zombie agents are those that are registered as 'running' but haven't
    had activity for a long time, or are in 'error' status.
    """
    cleared = []
    kept = []

    for agent_id, agent_info in list(orchestrator.active_agents.items()):
        status = agent_info.get("status", "unknown")

        # Remove agents in error or unknown status
        if status in ("error", "unknown", "failed"):
            cleared.append({
                "agent_id": agent_id,
                "type": agent_info.get("type"),
                "status": status,
                "reason": f"Status was '{status}'"
            })
            del orchestrator.active_agents[agent_id]
        else:
            kept.append({
                "agent_id": agent_id,
                "type": agent_info.get("type"),
                "status": status
            })

    logger.info(f"Cleared {len(cleared)} zombie agents, kept {len(kept)}")
    return {
        "cleared": cleared,
        "kept": kept,
        "cleared_count": len(cleared),
        "remaining_count": len(kept)
    }


@app.post("/api/agents/force-clear-all")
async def force_clear_all_agents():
    """
    Force clear ALL agents from the orchestrator.
    Use with caution - this will stop tracking all active agents.
    """
    count = len(orchestrator.active_agents)
    agents_cleared = list(orchestrator.active_agents.keys())
    orchestrator.active_agents.clear()

    logger.warning(f"Force cleared ALL {count} agents from orchestrator")
    return {
        "success": True,
        "cleared_count": count,
        "cleared_agents": agents_cleared,
        "message": f"Cleared {count} agents from orchestrator"
    }


@app.post("/api/requests/mark-stale")
async def mark_stale_requests():
    """
    Mark orphaned 'running' requests as 'abandoned' if their agents are no longer active.
    This helps clean up the UI when agents have been lost.
    """
    from src.runtime.agents.runtime import AgentRuntime
    from datetime import datetime

    activity_tracker = AgentRuntime.get_activity_tracker()

    # Get all requests
    requests = getattr(activity_tracker, 'requests', {})

    marked = []
    active_agent_ids = set(orchestrator.active_agents.keys())

    for request_id, request_data in requests.items():
        if not isinstance(request_data, dict):
            continue

        status = request_data.get("status")
        if status != "running":
            continue

        # Check if the root agent is still active
        root_agent_id = request_data.get("root_agent_id")
        if root_agent_id and root_agent_id in active_agent_ids:
            continue

        # Mark as abandoned
        request_data["status"] = "abandoned"
        request_data["completed_at"] = datetime.now().isoformat()
        request_data["abandonment_reason"] = "Root agent no longer active"
        marked.append({
            "request_id": request_id,
            "title": request_data.get("title"),
            "root_agent_id": root_agent_id
        })

    return {
        "marked_count": len(marked),
        "marked": marked
    }


@app.post("/api/requests/{request_id}/mark-completed")
async def mark_request_completed(request_id: str):
    """Manually mark a request as completed."""
    from src.runtime.agents.runtime import AgentRuntime
    from datetime import datetime

    activity_tracker = AgentRuntime.get_activity_tracker()
    requests = getattr(activity_tracker, 'requests', {})

    if request_id not in requests:
        return {"error": f"Request {request_id} not found", "success": False}

    requests[request_id]["status"] = "completed"
    requests[request_id]["completed_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "request_id": request_id,
        "message": "Request marked as completed"
    }


# ========== Swarm Pause/Resume Endpoints ==========

class SwarmPauseRequest(BaseModel):
    reason: Optional[str] = None


@app.get("/api/swarm/pause-status")
async def get_swarm_pause_status():
    """Get current swarm pause status."""
    from src.runtime.agents.runtime import AgentRuntime
    activity_tracker = AgentRuntime.get_activity_tracker()

    # Count running agents
    running_count = 0
    agent_states = getattr(activity_tracker, 'agent_states', {})
    for state in agent_states.values():
        if isinstance(state, dict) and state.get('status') == 'running':
            running_count += 1

    return {
        "paused": orchestrator.swarm_paused,
        "reason": orchestrator.pause_reason,
        "running_agents": running_count,
        "message": "Swarm is paused. Agents will stop at next checkpoint." if orchestrator.swarm_paused else "Swarm is running normally."
    }


@app.post("/api/swarm/pause")
async def pause_swarm(request: SwarmPauseRequest = None):
    """
    Pause the entire agent swarm.

    Running agents will complete their current operation and then pause.
    This is useful for:
    - Token exhaustion situations
    - Emergency stops
    - Resource management
    """
    orchestrator.swarm_paused = True
    orchestrator.pause_reason = request.reason if request else "User requested pause"

    logger.warning(f"⏸️ SWARM PAUSED: {orchestrator.pause_reason}")

    # Broadcast pause status to websocket clients
    try:
        await orchestrator.broadcast_status()
    except Exception as e:
        logger.warning(f"Could not broadcast pause status: {e}")

    return {
        "paused": True,
        "reason": orchestrator.pause_reason,
        "message": "Swarm paused. Running agents will stop at next checkpoint."
    }


@app.post("/api/swarm/resume")
async def resume_swarm():
    """Resume the agent swarm after a pause."""
    orchestrator.swarm_paused = False
    previous_reason = orchestrator.pause_reason
    orchestrator.pause_reason = None

    logger.info("▶️ SWARM RESUMED")

    # Broadcast resume status
    try:
        await orchestrator.broadcast_status()
    except Exception as e:
        logger.warning(f"Could not broadcast resume status: {e}")

    return {
        "paused": False,
        "previous_reason": previous_reason,
        "message": "Swarm resumed. Agents can continue processing."
    }


@app.post("/api/swarm/toggle-pause")
async def toggle_swarm_pause(request: SwarmPauseRequest = None):
    """Toggle the swarm pause state."""
    if orchestrator.swarm_paused:
        return await resume_swarm()
    else:
        return await pause_swarm(request)


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

# ========== Iteration Tuning Endpoints ==========

@app.get("/api/iteration-tuning/status")
async def get_iteration_tuning_status():
    """Get current iteration tuning status for all agents."""
    try:
        from src.runtime.agents.iteration_tuner import get_iteration_tuner
        tuner = get_iteration_tuner()
        agents = tuner.get_all_tuned_agents()
        return {
            "agents": agents,
            "total_agents": len(agents),
            "flagged_for_escalation": len([a for a in agents if a.get("escalation_flagged")])
        }
    except Exception as e:
        logger.error(f"Error getting iteration tuning status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/iteration-tuning/escalations")
async def get_iteration_tuning_escalations():
    """Get agents flagged for model escalation consideration."""
    try:
        from src.runtime.agents.iteration_tuner import get_iteration_tuner
        tuner = get_iteration_tuner()
        return {
            "flagged_agents": tuner.get_flagged_for_escalation(),
            "recommendation": "Consider upgrading these agents to a more capable model (e.g., Sonnet -> Opus)"
        }
    except Exception as e:
        logger.error(f"Error getting escalation flags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/iteration-tuning/history")
async def get_iteration_tuning_history(agent_name: str = None, limit: int = 50):
    """Get iteration tuning history."""
    try:
        from src.runtime.agents.iteration_tuner import get_iteration_tuner
        tuner = get_iteration_tuner()
        return {
            "history": tuner.get_tuning_history(agent_name, limit),
            "agent_filter": agent_name
        }
    except Exception as e:
        logger.error(f"Error getting tuning history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/iteration-tuning/{agent_name}/reset")
async def reset_iteration_tuning(agent_name: str):
    """Reset tuning for a specific agent back to original values."""
    try:
        from src.runtime.agents.iteration_tuner import get_iteration_tuner
        tuner = get_iteration_tuner()
        success = tuner.reset_agent_tuning(agent_name)
        if success:
            return {"success": True, "message": f"Reset tuning for {agent_name}"}
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found in tuning database")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/iteration-tuning/reset-all")
async def reset_all_iteration_tuning():
    """Reset tuning for all agents back to original values."""
    try:
        from src.runtime.agents.iteration_tuner import get_iteration_tuner
        tuner = get_iteration_tuner()
        count = tuner.reset_all_tuning()
        return {"success": True, "message": f"Reset tuning for {count} agents"}
    except Exception as e:
        logger.error(f"Error resetting all tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Agent Cleanup Endpoints ==========

class AgentCleanupRequest(BaseModel):
    statuses: Optional[List[str]] = None  # e.g., ['stalled', 'failed', 'pending']
    max_age_hours: Optional[int] = None   # Only delete agents older than this
    preserve_running: bool = True          # Always True by default for safety


@app.post("/api/swarm/cleanup")
async def cleanup_agents(request: AgentCleanupRequest):
    """
    Clean up stale/old agents.

    Options:
    - statuses: List of statuses to clean ['stalled', 'failed', 'pending', 'completed']
    - max_age_hours: Only delete agents older than this many hours
    - preserve_running: If True (default), never delete running agents
    """
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        from src.runtime.agents.runtime import AgentRuntime

        # Determine statuses to clear
        statuses_to_clear = request.statuses or []
        if request.preserve_running and 'running' in statuses_to_clear:
            statuses_to_clear = [s for s in statuses_to_clear if s != 'running']

        deleted = {"agents": 0, "activity_tracker": 0}

        # Clear from activity tracker (this is what the UI reads from)
        activity_tracker = AgentRuntime.get_activity_tracker()
        if statuses_to_clear:
            tracker_result = activity_tracker.clear_agents_by_status(statuses_to_clear)
            deleted["activity_tracker"] = tracker_result.get("agents", 0)

        # Also clear from swarm_state database
        try:
            swarm_state = get_swarm_state()

            with swarm_state._get_connection() as conn:
                conn.row_factory = None

                # Build query for agents to delete
                conditions = []
                params = []

                if request.statuses:
                    placeholders = ','.join('?' * len(request.statuses))
                    conditions.append(f"status IN ({placeholders})")
                    params.extend(request.statuses)

                if request.preserve_running:
                    conditions.append("status != 'running'")

                if request.max_age_hours:
                    conditions.append(f"created_at < datetime('now', '-{request.max_age_hours} hours')")

                if not conditions:
                    conditions.append("status != 'running'")  # Default: clean non-running

                where_clause = " AND ".join(conditions)

                # Get agent IDs to delete
                cursor = conn.execute(f"SELECT agent_id FROM agents WHERE {where_clause}", params)
                agent_ids = [row[0] for row in cursor.fetchall()]

                if agent_ids:
                    agent_placeholders = ','.join('?' * len(agent_ids))

                    # Delete related data
                    conn.execute(f"DELETE FROM agent_messages WHERE agent_id IN ({agent_placeholders})", agent_ids)
                    conn.execute(f"DELETE FROM tool_executions WHERE agent_id IN ({agent_placeholders})", agent_ids)
                    conn.execute(f"DELETE FROM events WHERE agent_id IN ({agent_placeholders})", agent_ids)
                    conn.execute(f"DELETE FROM recovery_queue WHERE agent_id IN ({agent_placeholders})", agent_ids)
                    cursor = conn.execute(f"DELETE FROM agents WHERE agent_id IN ({agent_placeholders})", agent_ids)
                    deleted["agents"] = cursor.rowcount
                    conn.commit()
        except Exception as db_err:
            # Log but don't fail - activity tracker cleanup is the primary goal
            logger.warning(f"Swarm state DB cleanup failed (non-critical): {db_err}")

        return {"success": True, "deleted": deleted}

    except Exception as e:
        logger.error(f"Error cleaning up agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/swarm/cleanup/preview")
async def preview_cleanup(
    statuses: str = Query(None, description="Comma-separated statuses to clean"),
    max_age_hours: int = Query(None, description="Only agents older than this"),
    preserve_running: bool = Query(True, description="Preserve running agents")
):
    """Preview what would be cleaned up without actually deleting."""
    try:
        from src.runtime.agents.swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        with swarm_state._get_connection() as conn:
            conn.row_factory = None

            query = "SELECT status, COUNT(*) as count FROM agents WHERE 1=1"
            params = []

            if statuses:
                status_list = [s.strip() for s in statuses.split(',')]
                placeholders = ','.join('?' * len(status_list))
                query += f" AND status IN ({placeholders})"
                params.extend(status_list)

            if preserve_running:
                query += " AND status != 'running'"

            if max_age_hours:
                query += f" AND created_at < datetime('now', '-{max_age_hours} hours')"

            query += " GROUP BY status"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return {
                "would_delete": {row[0]: row[1] for row in rows},
                "total": sum(row[1] for row in rows)
            }

    except Exception as e:
        logger.error(f"Error previewing cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Agent Definition Management API ==========

# Valid agent category subdirectories within agents/ folder
# ONLY these subdirectories contain agent definitions
VALID_AGENT_CATEGORIES = frozenset([
    'leadership',
    'coordinators',
    'developers',
    'testers',
    'designers',
    'support',
])

# For backwards compatibility
VALID_AGENT_DIRS = VALID_AGENT_CATEGORIES


def discover_agent_directories() -> Dict[str, str]:
    """
    Discover agent directories from the consolidated agents/ folder.

    All agent definitions live in agents/<category>/*.md
    Only categories in VALID_AGENT_CATEGORIES are considered.
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    agents_root = project_root / "agents"
    agent_dirs = {}

    if not agents_root.exists():
        logger.warning(f"Agents directory not found: {agents_root}")
        return agent_dirs

    # Only check category subdirectories in the whitelist
    for category in VALID_AGENT_CATEGORIES:
        category_path = agents_root / category
        if not category_path.exists() or not category_path.is_dir():
            continue

        # Verify directory contains at least one valid agent definition
        md_files = list(category_path.glob("*.md"))
        for md_file in md_files:
            if md_file.name.startswith(("_", "README", "AGENT_TEMPLATE")):
                continue
            try:
                content = md_file.read_text(encoding='utf-8')
                if "## Purpose" in content or "## Instantiation" in content:
                    agent_dirs[category] = category
                    break
            except Exception:
                continue

    return agent_dirs


def get_agent_dirs() -> Dict[str, str]:
    """Get agent directories, using cache for performance."""
    if not hasattr(get_agent_dirs, '_cache') or get_agent_dirs._cache is None:
        get_agent_dirs._cache = discover_agent_directories()
    return get_agent_dirs._cache


def invalidate_agent_dirs_cache():
    """Invalidate the agent directories cache."""
    get_agent_dirs._cache = None


@app.get("/api/agent-categories")
async def list_agent_categories():
    """List all discovered agent categories."""
    try:
        agent_dirs = get_agent_dirs()
        return {
            "categories": list(agent_dirs.keys()),
            "count": len(agent_dirs)
        }
    except Exception as e:
        logger.error(f"Error listing agent categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-hierarchy")
async def get_agent_hierarchy():
    """Build agent hierarchy dynamically from spawn permissions in definitions."""
    import re
    try:
        project_root = Path(__file__).parent.parent.parent.parent.parent
        agents_root = project_root / "agents"
        agents = {}  # agent_path -> {name, purpose, category, can_spawn: []}

        # First pass: collect all agents and their spawn permissions
        for category, dirname in get_agent_dirs().items():
            agent_dir = agents_root / dirname
            if not agent_dir.exists():
                continue

            for md_file in sorted(agent_dir.glob("*.md")):
                if md_file.name.startswith(("_", "AGENT_TEMPLATE", "README")):
                    continue

                content = md_file.read_text(encoding='utf-8')
                lines = content.split('\n')

                # Extract name
                name = md_file.stem.replace("_", " ").title()
                for line in lines:
                    if line.startswith("# "):
                        name = line[2:].strip()
                        break

                # Extract purpose
                purpose = ""
                in_purpose = False
                for line in lines:
                    if line.startswith("## Purpose"):
                        in_purpose = True
                        continue
                    if in_purpose:
                        if line.startswith("##"):
                            break
                        if line.strip():
                            purpose = line.strip()[:100]
                            break

                # Extract spawn permissions (CAN Spawn section)
                can_spawn = []
                in_spawn = False
                for line in lines:
                    if "**CAN Spawn" in line or "CAN Spawn:" in line:
                        in_spawn = True
                        continue
                    if in_spawn:
                        if line.startswith("**CANNOT") or line.startswith("## ") or (line.strip() == "" and can_spawn):
                            break
                        # Parse agent paths like developers/backend_lead, testers/unit_test_lead
                        matches = re.findall(r'([a-z_]+/[a-z_]+)', line)
                        can_spawn.extend(matches)

                agent_path = f"{category}/{md_file.stem}"
                agents[agent_path] = {
                    "name": name,
                    "purpose": purpose,
                    "category": category,
                    "can_spawn": can_spawn,
                    "path": agent_path
                }

        # Build hierarchy tree (find children for each agent)
        hierarchy = {}
        for agent_path, agent_data in agents.items():
            children = []
            for child_path in agent_data["can_spawn"]:
                if child_path in agents:
                    children.append({
                        "path": child_path,
                        "name": agents[child_path]["name"],
                        "category": agents[child_path]["category"]
                    })
            hierarchy[agent_path] = {
                **agent_data,
                "children": children
            }

        # Find root agents (not spawned by anyone else)
        all_spawnable = set()
        for agent_data in agents.values():
            all_spawnable.update(agent_data["can_spawn"])

        roots = [path for path in agents.keys() if path not in all_spawnable]

        return {
            "agents": hierarchy,
            "roots": roots,
            "total_agents": len(agents),
            "categories": list(get_agent_dirs().keys())
        }
    except Exception as e:
        logger.error(f"Error building agent hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refresh-agent-cache")
async def refresh_agent_cache():
    """Force refresh of the agent directory cache."""
    invalidate_agent_dirs_cache()
    return {"success": True, "message": "Agent cache invalidated"}


@app.get("/api/agent-definitions")
async def list_agent_definitions():
    """List all agent definition files organized by category."""
    try:
        project_root = Path(__file__).parent.parent.parent.parent.parent
        agents_by_category = {}

        for category, dirname in get_agent_dirs().items():
            agent_dir = project_root / dirname
            agents = []

            if agent_dir.exists():
                for md_file in sorted(agent_dir.glob("*.md")):
                    # Skip non-agent files
                    if md_file.name.startswith(("_", "AGENT_TEMPLATE", "README")):
                        continue

                    # Parse basic info from file
                    content = md_file.read_text(encoding='utf-8')
                    lines = content.split('\n')

                    # Extract name from first header
                    name = md_file.stem.replace("_", " ").title()
                    for line in lines:
                        if line.startswith("# "):
                            name = line[2:].strip()
                            break

                    # Extract purpose (first paragraph after ## Purpose)
                    purpose = ""
                    in_purpose = False
                    for line in lines:
                        if line.startswith("## Purpose"):
                            in_purpose = True
                            continue
                        if in_purpose:
                            if line.startswith("##"):
                                break
                            if line.strip():
                                purpose = line.strip()
                                break

                    agents.append({
                        "filename": md_file.name,
                        "name": name,
                        "purpose": purpose[:200] + "..." if len(purpose) > 200 else purpose,
                        "category": category,
                        "path": str(md_file.relative_to(project_root)),
                        "size_bytes": md_file.stat().st_size,
                        "modified_at": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
                    })

            agents_by_category[category] = agents

        # Calculate totals
        total_agents = sum(len(agents) for agents in agents_by_category.values())

        return {
            "categories": agents_by_category,
            "total_agents": total_agents,
            "category_counts": {k: len(v) for k, v in agents_by_category.items()}
        }
    except Exception as e:
        logger.error(f"Error listing agent definitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-definitions/{category}/{filename}")
async def get_agent_definition(category: str, filename: str):
    """Get a specific agent definition file content."""
    try:
        if category not in get_agent_dirs():
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        project_root = Path(__file__).parent.parent.parent.parent.parent
        file_path = project_root / get_agent_dirs()[category] / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Agent definition not found")

        if not filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only markdown files allowed")

        content = file_path.read_text(encoding='utf-8')

        # Parse sections
        sections = {}
        current_section = "header"
        current_content = []

        for line in content.split('\n'):
            if line.startswith("## "):
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip().lower().replace(" ", "_")
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return {
            "filename": filename,
            "category": category,
            "path": str(file_path.relative_to(project_root)),
            "content": content,
            "sections": sections,
            "size_bytes": file_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading agent definition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AgentDefinitionUpdate(BaseModel):
    content: str


@app.put("/api/agent-definitions/{category}/{filename}")
async def update_agent_definition(category: str, filename: str, update: AgentDefinitionUpdate):
    """Update an agent definition file."""
    try:
        if category not in get_agent_dirs():
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        project_root = Path(__file__).parent.parent.parent.parent.parent
        file_path = project_root / get_agent_dirs()[category] / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Agent definition not found")

        if not filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only markdown files allowed")

        # Create backup
        backup_path = file_path.with_suffix('.md.backup')
        backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')

        # Write new content
        file_path.write_text(update.content, encoding='utf-8')

        logger.info(f"Updated agent definition: {category}/{filename}")

        return {
            "success": True,
            "filename": filename,
            "category": category,
            "backup_created": str(backup_path.relative_to(project_root)),
            "size_bytes": file_path.stat().st_size,
            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent definition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent-definitions/{category}/{filename}/restore")
async def restore_agent_definition(category: str, filename: str):
    """Restore an agent definition from backup."""
    try:
        if category not in get_agent_dirs():
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        project_root = Path(__file__).parent.parent.parent.parent.parent
        file_path = project_root / get_agent_dirs()[category] / filename
        backup_path = file_path.with_suffix('.md.backup')

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="No backup found")

        # Restore from backup
        file_path.write_text(backup_path.read_text(encoding='utf-8'), encoding='utf-8')

        logger.info(f"Restored agent definition from backup: {category}/{filename}")

        return {
            "success": True,
            "filename": filename,
            "category": category,
            "restored_from": str(backup_path.relative_to(project_root))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring agent definition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-definitions/template")
async def get_agent_template():
    """Get the agent definition template."""
    try:
        project_root = Path(__file__).parent.parent.parent.parent.parent
        template_path = project_root / "leadership" / "AGENT_TEMPLATE.md"

        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "content": template_path.read_text(encoding='utf-8'),
            "path": str(template_path.relative_to(project_root))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading agent template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Session Recovery API Endpoints ==========

@app.get("/api/sessions")
async def get_sessions(
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum sessions to return"),
    include_agents: bool = Query(False, description="Include agent data")
):
    """Get all swarm sessions, optionally filtered by status."""
    try:
        from src.runtime.agents.persistence import get_persistence
        persistence = get_persistence()
        sessions = persistence.get_sessions(
            status=status,
            limit=limit,
            include_agents=include_agents
        )
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/incomplete")
async def get_incomplete_sessions():
    """Get all incomplete sessions for recovery."""
    try:
        from src.runtime.agents.persistence import get_persistence
        persistence = get_persistence()
        sessions = persistence.get_incomplete_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error getting incomplete sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session with all its agents."""
    try:
        from src.runtime.agents.persistence import get_persistence
        persistence = get_persistence()
        session = persistence.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session['agents'] = persistence.get_agents_for_session(session_id)
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/resume")
async def resume_session(session_id: str, background_tasks: BackgroundTasks):
    """Resume a recovered session."""
    try:
        from src.runtime.agents.persistence import get_persistence
        persistence = get_persistence()
        session = persistence.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session['status'] not in ('recovered', 'failed', 'paused'):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resume session with status '{session['status']}'"
            )

        # Resume by spawning a new executive director with continuation context
        continuation_prompt = f"""RESUMING INTERRUPTED SESSION

## Original Task
{session['prompt']}

## Context
This session was interrupted and is being resumed. Review the work completed so far and continue from where it left off. Do not restart from the beginning - continue the existing work.

## Instructions
1. Assess what has been completed
2. Identify remaining work
3. Continue implementation"""

        # Spawn new agent to continue
        agent_id, result = await orchestrator.spawn_executive_director(
            problem_description=continuation_prompt,
            budget_tier=session.get('budget_tier', 'balanced'),
            auto_continue=True
        )

        # Update session status
        persistence.update_session(session_id, status='running')

        return {
            "success": True,
            "session_id": session_id,
            "new_agent_id": agent_id,
            "message": "Session resumed with new agent"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions/{session_id}/abandon")
async def abandon_session(session_id: str):
    """Mark a session as abandoned."""
    try:
        from src.runtime.agents.persistence import get_persistence
        persistence = get_persistence()
        session = persistence.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        persistence.update_session(session_id, status='abandoned')
        return {"success": True, "session_id": session_id, "status": "abandoned"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error abandoning session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its agents."""
    try:
        from src.runtime.agents.persistence import get_persistence
        persistence = get_persistence()
        success = persistence.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "session_id": session_id, "deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Log Monitor / Runtime Issues Endpoints ==========

@app.get("/api/issues")
async def get_runtime_issues(
    severity: Optional[str] = None,
    category: Optional[str] = None,
    unresolved_only: bool = True,
    limit: int = 50
):
    """
    Get detected runtime issues for user review.

    The log monitor automatically detects errors and failures,
    categorizes them, and suggests remediation actions.
    """
    try:
        monitor = get_log_monitor()

        # Convert string params to enums if provided
        from src.runtime.agents.log_monitor import IssueSeverity, IssueCategory
        sev_enum = None
        cat_enum = None

        if severity:
            try:
                sev_enum = IssueSeverity(severity.lower())
            except ValueError:
                pass

        if category:
            try:
                cat_enum = IssueCategory(category.lower())
            except ValueError:
                pass

        issues = monitor.get_issues(
            severity=sev_enum,
            category=cat_enum,
            unresolved_only=unresolved_only,
            limit=limit
        )

        return {
            "issues": issues,
            "count": len(issues),
            "unresolved_only": unresolved_only
        }
    except Exception as e:
        logger.error(f"Error getting issues: {e}")
        return {"error": str(e), "issues": [], "count": 0}


@app.get("/api/issues/summary")
async def get_issues_summary():
    """Get a summary of current runtime issues."""
    try:
        monitor = get_log_monitor()
        return monitor.get_summary()
    except Exception as e:
        logger.error(f"Error getting issues summary: {e}")
        return {"error": str(e)}


@app.post("/api/issues/{issue_id}/resolve")
async def resolve_issue(issue_id: str):
    """Mark an issue as resolved."""
    try:
        monitor = get_log_monitor()
        success = monitor.resolve_issue(issue_id)
        if success:
            return {"success": True, "issue_id": issue_id, "resolved": True}
        else:
            raise HTTPException(status_code=404, detail="Issue not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving issue {issue_id}: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/issues/resolve-all")
async def resolve_all_issues():
    """Mark all issues as resolved."""
    try:
        monitor = get_log_monitor()
        count = monitor.resolve_all()
        return {"success": True, "resolved_count": count}
    except Exception as e:
        logger.error(f"Error resolving all issues: {e}")
        return {"success": False, "error": str(e)}


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