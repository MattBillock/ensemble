"""Tool definitions for agent capabilities."""
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .definition import AgentDefinition
    from .runtime import AgentRuntime

logger = logging.getLogger(__name__)


class Tool(Protocol):
    """Protocol for agent tools."""

    name: str
    description: str
    input_schema: Dict[str, Any]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given inputs.

        Args:
            inputs: Tool input parameters

        Returns:
            Result dictionary with at least {"success": bool}
        """
        ...

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert tool to Anthropic API format."""
        ...


class WriteFileTool:
    """Tool for writing content to files."""

    name = "write_file"
    description = "Write content to a file, creating parent directories if needed"
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["file_path", "content"]
    }

    # Code file extensions that require can_write_code permission
    CODE_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h",
        ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".cs", ".sql"
    }

    def __init__(self, agent_definition: Optional["AgentDefinition"] = None):
        """Initialize with optional agent definition for permission checking."""
        self.agent_definition = agent_definition

    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file path is a code file."""
        return file_path.suffix.lower() in self.CODE_EXTENSIONS

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file path is a test file."""
        # Only apply test file detection to actual code files
        # This prevents false positives on documentation like "test_tasks.md"
        if file_path.suffix.lower() not in self.CODE_EXTENSIONS:
            return False

        # Check file name patterns for code files
        name = file_path.name.lower()
        if name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.js") or name.endswith(".spec.js") or name.endswith(".test.ts") or name.endswith(".spec.ts"):
            return True

        # Check if in test directory
        parts = [p.lower() for p in file_path.parts]
        if any(p in ["test", "tests", "__tests__", "spec", "specs"] for p in parts):
            return True

        return False

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to a file."""
        file_path = Path(inputs["file_path"])
        content = inputs["content"]

        # Check if agent has permission to write test files
        if self._is_test_file(file_path):
            if self.agent_definition and not self.agent_definition.can_write_tests:
                error_msg = (
                    f"ROGUE AGENT DETECTED: Agent '{self.agent_definition.name}' attempted to write "
                    f"test file '{file_path}' but lacks can_write_tests permission. "
                    f"This agent is a supervisor/coordinator and should delegate to test writers."
                )
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        # Check if agent has permission to write code files (non-test code)
        if self._is_code_file(file_path) and not self._is_test_file(file_path):
            if self.agent_definition and not self.agent_definition.can_write_code:
                error_msg = (
                    f"ROGUE AGENT DETECTED: Agent '{self.agent_definition.name}' attempted to write "
                    f"code file '{file_path}' but lacks can_write_code permission. "
                    f"This agent is a supervisor/coordinator and should delegate to code writers."
                )
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            file_path.write_text(content)

            logger.info(f"Successfully wrote file: {file_path}")
            return {
                "success": True,
                "message": f"File written successfully to {file_path}"
            }

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class ReadFileTool:
    """Tool for reading content from files."""

    name = "read_file"
    description = "Read content from a file"
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["file_path"]
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Read content from a file."""
        file_path = Path(inputs["file_path"])

        try:
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            content = file_path.read_text()

            logger.info(f"Successfully read file: {file_path}")
            return {
                "success": True,
                "content": content
            }

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class RunCommandTool:
    """Tool for executing shell commands."""

    name = "run_command"
    description = "Execute a shell command and return the output"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            },
            "working_directory": {
                "type": "string",
                "description": "Optional working directory for command execution"
            }
        },
        "required": ["command"]
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command."""
        command = inputs["command"]
        working_dir = inputs.get("working_directory")

        try:
            logger.info(f"Executing command: {command}")

            # Execute command with shell=True to support pipes, redirects, etc.
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout for safety
            )

            success = result.returncode == 0

            logger.info(f"Command completed with exit code: {result.returncode}")

            return {
                "success": success,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command timed out after 30 seconds"
            }
        except Exception as e:
            logger.error(f"Failed to execute command {command}: {e}")
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class ProjectTrackingTool:
    """Tool for tracking project state and tasks."""

    name = "project_tracking"
    description = "Manage project state, tasks, and notes for the current project"
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create_project", "add_task", "update_task", "add_note", "get_summary", "get_next_tasks"],
                "description": "Action to perform"
            },
            "project_id": {
                "type": "string",
                "description": "Project ID (not needed for create_project)"
            },
            "project_name": {
                "type": "string",
                "description": "Project name (for create_project)"
            },
            "description": {
                "type": "string",
                "description": "Description (for create_project or add_task)"
            },
            "task_id": {
                "type": "string",
                "description": "Task ID (for update_task)"
            },
            "status": {
                "type": "string",
                "enum": ["todo", "in_progress", "completed", "blocked", "cancelled"],
                "description": "Task status (for update_task)"
            },
            "note": {
                "type": "string",
                "description": "Note text (for add_note or update_task)"
            },
            "assigned_to": {
                "type": "string",
                "description": "Agent type (for add_task)"
            },
            "category": {
                "type": "string",
                "enum": ["general", "decision", "milestone", "issue"],
                "description": "Note category (for add_note)"
            }
        },
        "required": ["action"]
    }

    def __init__(self, request_id: Optional[str] = None, output_directory: Optional[str] = None):
        """
        Initialize project tracking tool.

        Args:
            request_id: Current request ID
            output_directory: Project output directory
        """
        self.request_id = request_id
        self.output_directory = output_directory

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project tracking action."""
        from .project_tracker import ProjectTracker, TaskStatus

        action = inputs["action"]
        tracker = ProjectTracker()

        try:
            if action == "create_project":
                if "project_name" not in inputs or "description" not in inputs:
                    return {
                        "success": False,
                        "error": "project_name and description required for create_project"
                    }

                project = tracker.create_project(
                    project_name=inputs["project_name"],
                    description=inputs["description"],
                    request_id=self.request_id,
                    output_directory=self.output_directory
                )

                return {
                    "success": True,
                    "project_id": project.project_id,
                    "message": f"Created project: {project.project_name}",
                    "summary": tracker.get_project_summary(project.project_id)
                }

            elif action == "add_task":
                if "project_id" not in inputs or "description" not in inputs:
                    return {
                        "success": False,
                        "error": "project_id and description required for add_task"
                    }

                task_id = tracker.add_task(
                    project_id=inputs["project_id"],
                    description=inputs["description"],
                    assigned_to=inputs.get("assigned_to")
                )

                return {
                    "success": True,
                    "task_id": task_id,
                    "message": f"Added task: {inputs['description']}"
                }

            elif action == "update_task":
                if "project_id" not in inputs or "task_id" not in inputs or "status" not in inputs:
                    return {
                        "success": False,
                        "error": "project_id, task_id, and status required for update_task"
                    }

                tracker.update_task_status(
                    project_id=inputs["project_id"],
                    task_id=inputs["task_id"],
                    status=TaskStatus(inputs["status"]),
                    note=inputs.get("note")
                )

                return {
                    "success": True,
                    "message": f"Updated task status to {inputs['status']}"
                }

            elif action == "add_note":
                if "project_id" not in inputs or "note" not in inputs:
                    return {
                        "success": False,
                        "error": "project_id and note required for add_note"
                    }

                tracker.add_note(
                    project_id=inputs["project_id"],
                    note=inputs["note"],
                    category=inputs.get("category", "general")
                )

                return {
                    "success": True,
                    "message": "Added note to project"
                }

            elif action == "get_summary":
                if "project_id" not in inputs:
                    return {
                        "success": False,
                        "error": "project_id required for get_summary"
                    }

                summary = tracker.get_project_summary(inputs["project_id"])

                return {
                    "success": True,
                    "summary": summary
                }

            elif action == "get_next_tasks":
                if "project_id" not in inputs:
                    return {
                        "success": False,
                        "error": "project_id required for get_next_tasks"
                    }

                next_tasks = tracker.get_next_tasks(inputs["project_id"])

                return {
                    "success": True,
                    "next_tasks": [
                        {
                            "task_id": task.task_id,
                            "description": task.description,
                            "assigned_to": task.assigned_to
                        }
                        for task in next_tasks
                    ]
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

        except Exception as e:
            logger.error(f"Project tracking error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class GitCommitTool:
    """Tool for committing changes to git repository."""

    name = "git_commit"
    description = "Commit changes to the git repository with a descriptive message"
    input_schema = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Commit message describing the changes"
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of specific files to commit. If not provided, commits all modified files."
            }
        },
        "required": ["message"]
    }

    def __init__(self, working_directory: Optional[Path] = None, agent_id: Optional[str] = None, request_id: Optional[str] = None):
        """
        Initialize git commit tool.

        Args:
            working_directory: Git repository root directory
            agent_id: ID of the agent using this tool (for activity tracking)
            request_id: Request ID for tracking (for activity tracking)
        """
        self.working_directory = working_directory or Path.cwd()
        self.agent_id = agent_id
        self.request_id = request_id

    def _validate_commit_message(self, message: str) -> tuple[bool, Optional[str]]:
        """Validate commit message format."""
        if not message or len(message.strip()) == 0:
            return False, "Commit message cannot be empty"

        if len(message) < 10:
            return False, "Commit message should be at least 10 characters long"

        # Check for common bad patterns
        bad_patterns = ["wip", "temp", "test commit", "asdf", "fix"]
        if message.lower().strip() in bad_patterns:
            return False, f"Please provide a more descriptive commit message than '{message}'"

        return True, None

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Commit changes to git repository."""
        message = inputs["message"]
        files = inputs.get("files", [])

        # Validate commit message
        is_valid, error = self._validate_commit_message(message)
        if not is_valid:
            logger.warning(f"Invalid commit message: {error}")
            return {
                "success": False,
                "error": error
            }

        try:
            logger.info(f"Committing changes to git: {message}")

            # Stage files
            if files:
                # Add specific files
                for file_path in files:
                    add_result = subprocess.run(
                        ["git", "add", file_path],
                        cwd=self.working_directory,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if add_result.returncode != 0:
                        logger.warning(f"Failed to stage file {file_path}: {add_result.stderr}")
            else:
                # Add all modified and untracked files
                add_result = subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.working_directory,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if add_result.returncode != 0:
                    logger.error(f"Failed to stage files: {add_result.stderr}")
                    return {
                        "success": False,
                        "error": f"Failed to stage files: {add_result.stderr}"
                    }

            # Check if there are any changes to commit
            status_result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.working_directory,
                capture_output=True,
                timeout=5
            )

            if status_result.returncode == 0:
                # No changes staged
                logger.info("No changes to commit")
                return {
                    "success": True,
                    "message": "No changes to commit",
                    "commit_hash": None
                }

            # Commit changes
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=10
            )

            if commit_result.returncode != 0:
                logger.error(f"Failed to commit: {commit_result.stderr}")
                return {
                    "success": False,
                    "error": f"Failed to commit: {commit_result.stderr}"
                }

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"

            # Get list of committed files
            files_result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            committed_files = files_result.stdout.strip().split('\n') if files_result.returncode == 0 else []

            # Record in activity tracker if agent_id is available
            if self.agent_id and self.request_id:
                try:
                    from .runtime import AgentRuntime
                    activity_tracker = AgentRuntime.get_activity_tracker()

                    # Get agent name from somewhere, or use agent_id as fallback
                    agent_name = self.agent_id  # Could be improved by passing agent_name

                    activity_tracker.record_git_commit(
                        agent_id=self.agent_id,
                        agent_name=agent_name,
                        request_id=self.request_id,
                        commit_hash=commit_hash,
                        commit_message=message,
                        files=committed_files
                    )
                except Exception as e:
                    logger.warning(f"Failed to record git commit in activity tracker: {e}")

            logger.info(f"Successfully committed changes: {commit_hash}")
            return {
                "success": True,
                "message": "Changes committed successfully",
                "commit_hash": commit_hash,
                "files": committed_files,
                "commit_output": commit_result.stdout
            }

        except subprocess.TimeoutExpired:
            logger.error("Git command timed out")
            return {
                "success": False,
                "error": "Git command timed out"
            }
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class SpawnAgentTool:
    """Tool for spawning and executing other agents."""

    name = "spawn_agent"
    description = "Spawn and execute a specialist agent to perform a specific task"
    input_schema = {
        "type": "object",
        "properties": {
            "agent_type": {
                "type": "string",
                "description": "The type of agent to spawn (e.g., 'code_writer', 'code_tester')"
            },
            "input_data": {
                "type": "object",
                "description": "Input data to pass to the spawned agent"
            }
        },
        "required": ["agent_type", "input_data"]
    }

    def __init__(
        self,
        agent_types_dir: Path,
        api_key: str,
        tools: Optional["ToolRegistry"] = None,
        budget_tier: str = "balanced",
        parent_agent_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Initialize spawn agent tool.

        Args:
            agent_types_dir: Directory containing agent type definitions
            api_key: Anthropic API key for spawned agents
            tools: Optional tool registry to provide to spawned agents
            budget_tier: Budget tier for model selection (full_firepower, balanced, economical)
            parent_agent_id: ID of the agent spawning this tool (for metrics)
            request_id: Request ID for tracing (for metrics)
        """
        self.agent_types_dir = agent_types_dir
        self.api_key = api_key
        self.tools = tools
        self.budget_tier = budget_tier
        self.parent_agent_id = parent_agent_id
        self.request_id = request_id or "unknown"

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Spawn and execute an agent."""
        # Import here to avoid circular dependency
        from .definition import AgentDefinition
        from .runtime import AgentRuntime

        agent_type = inputs["agent_type"]
        input_data = inputs["input_data"]

        try:
            logger.info(f"Spawning agent: {agent_type}")

            # Load agent definition
            agent_def_path = self.agent_types_dir / f"{agent_type}.md"
            agent_definition = AgentDefinition.from_file(agent_def_path)

            # Validate required inputs
            required_fields = agent_definition.get_required_input_fields()
            provided_fields = set(input_data.keys())
            missing_fields = required_fields - provided_fields

            if missing_fields:
                error_msg = (
                    f"Missing required input fields for {agent_type}: {sorted(missing_fields)}. "
                    f"Required: {sorted(required_fields)}, Provided: {sorted(provided_fields)}"
                )
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

            # Generate unique agent_id for spawned agent
            import time
            spawned_agent_id = f"{agent_type}_{int(time.time()*1000)}"

            # Create runtime for the agent with budget tier and metrics parameters
            runtime = AgentRuntime(
                agent_definition,
                api_key=self.api_key,
                tools=self.tools,
                budget_tier=self.budget_tier,
                agent_id=spawned_agent_id,
                request_id=self.request_id,
                parent_agent_id=self.parent_agent_id
            )

            # Execute the agent
            result = runtime.execute(input_data)

            # Increment parent's spawned agents count (if parent runtime exists)
            # This would need to be tracked differently in a real implementation

            logger.info(f"Agent {agent_type} completed successfully")

            return {
                "success": True,
                "result": result
            }

        except FileNotFoundError as e:
            logger.error(f"Agent type not found: {agent_type}")
            return {
                "success": False,
                "error": f"Unknown agent type: {agent_type}. Agent definition file not found."
            }
        except Exception as e:
            logger.error(f"Failed to execute agent {agent_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def to_anthropic_format(self) -> List[Dict[str, Any]]:
        """Convert all tools to Anthropic API format."""
        return [tool.to_anthropic_format() for tool in self._tools.values()]

    @classmethod
    def default(cls, agent_definition: Optional["AgentDefinition"] = None, request_id: Optional[str] = None, output_directory: Optional[str] = None) -> "ToolRegistry":
        """
        Create a registry with default tools.

        Args:
            agent_definition: Optional agent definition for permission checking
            request_id: Optional request ID for project tracking
            output_directory: Optional output directory for project tracking
        """
        registry = cls()
        registry.register(WriteFileTool(agent_definition))
        registry.register(ReadFileTool())
        registry.register(RunCommandTool())
        registry.register(GitCommitTool())  # Add git commit capability
        registry.register(ProjectTrackingTool(request_id=request_id, output_directory=output_directory))  # Add project tracking
        return registry
