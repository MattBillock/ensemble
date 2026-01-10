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

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to a file."""
        file_path = Path(inputs["file_path"])
        content = inputs["content"]

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
        tools: Optional["ToolRegistry"] = None
    ):
        """
        Initialize spawn agent tool.

        Args:
            agent_types_dir: Directory containing agent type definitions
            api_key: Anthropic API key for spawned agents
            tools: Optional tool registry to provide to spawned agents
        """
        self.agent_types_dir = agent_types_dir
        self.api_key = api_key
        self.tools = tools

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

            # Create runtime for the agent
            runtime = AgentRuntime(
                agent_definition,
                api_key=self.api_key,
                tools=self.tools
            )

            # Execute the agent
            result = runtime.execute(input_data)

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
    def default(cls) -> "ToolRegistry":
        """Create a registry with default tools."""
        registry = cls()
        registry.register(WriteFileTool())
        registry.register(ReadFileTool())
        registry.register(RunCommandTool())
        return registry
