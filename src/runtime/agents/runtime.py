"""Agent runtime for executing agents with Anthropic API."""
import json
import logging
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from pathlib import Path

from .definition import AgentDefinition
from .tools import ToolRegistry
from .state import StateManager
from .model_selector import ModelSelector

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


class AgentRuntime:
    """Runtime for executing an agent based on its definition."""

    # Model mapping from friendly names to API model IDs
    MODEL_MAP = {
        "haiku": "claude-3-5-haiku-20241022",
        "sonnet": "claude-3-5-sonnet-20241022",
        "opus": "claude-opus-4-20241229"
    }

    def __init__(
        self,
        definition: AgentDefinition,
        api_key: str,
        tools: Optional[ToolRegistry] = None,
        state_file: Optional[Path] = None,
        budget_tier: str = "balanced"
    ):
        """
        Initialize agent runtime.

        Args:
            definition: Agent definition specifying behavior
            api_key: Anthropic API key
            tools: Optional tool registry for agent capabilities
            state_file: Optional path to state file for persistence/resume
            budget_tier: Budget tier for model selection (full_firepower, balanced, economical)
        """
        self.definition = definition
        self.client = Anthropic(api_key=api_key)
        self.tools = tools
        self.iteration_count = 0
        self.state_manager = StateManager(state_file) if state_file else None
        self.budget_tier = budget_tier

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with the given input.

        Args:
            input_data: Input data matching the agent's expected input format

        Returns:
            Output data matching the agent's expected output format

        Raises:
            ValueError: If input doesn't match expected format
        """
        # Validate input
        self._validate_input(input_data)

        # Initialize or resume state
        if self.state_manager:
            if self.state_manager.can_resume():
                logger.info("Resuming from previous state")
                resume_info = self.state_manager.get_resume_info()
                self.iteration_count = resume_info["iteration"]
                # For now, we'll start fresh but log the resume
                # Full resume with conversation history would need message reconstruction
                logger.info(f"Previous execution had {resume_info['spawned_agents_count']} spawned agents")
            else:
                self.state_manager.init_execution(self.definition.name, input_data)

        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(input_data)

        # Select model using ModelSelector based on budget tier and task complexity
        model = ModelSelector.select_model(
            budget_tier=self.budget_tier,
            task_complexity=self.definition.task_complexity,
            agent_name=self.definition.name
        )

        logger.info(f"Executing agent: {self.definition.name}")
        logger.info(f"Using model: {model} (tier={self.budget_tier}, complexity={self.definition.task_complexity})")

        # Initialize conversation
        messages = [{"role": "user", "content": user_prompt}]

        # Prepare API call kwargs
        api_kwargs = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages
        }

        # Add tools if available
        if self.tools:
            api_kwargs["tools"] = self.tools.to_anthropic_format()

        # Execute agent loop
        response_data = None
        try:
            while self.iteration_count < self.definition.max_iterations:
                self.iteration_count += 1
                logger.info(f"Iteration {self.iteration_count}/{self.definition.max_iterations}")

                # Call Anthropic API
                response = self.client.messages.create(**api_kwargs)

                # Record iteration in state
                if self.state_manager:
                    assistant_message = {
                        "role": "assistant",
                        "content": response.content
                    }
                    self.state_manager.record_iteration(self.iteration_count, assistant_message)
                    self.state_manager.checkpoint()

                # Handle tool use
                if response.stop_reason == "tool_use":
                    logger.info("Agent requested tool use")
                    messages = self._handle_tool_use(messages, response)
                    api_kwargs["messages"] = messages
                    continue

                # Extract final response
                response_data = self._extract_final_response(response)

                # Check termination conditions
                if not response_data.get("needs_clarification", False):
                    logger.info("Agent completed successfully")
                    break

                # If we need clarification, we would handle that here
                # For now, we'll just continue (in a real system, we'd ask the user)
                logger.warning("Agent needs clarification but continuing anyway")

            if self.iteration_count >= self.definition.max_iterations:
                logger.warning(f"Agent reached max iterations ({self.definition.max_iterations})")

            # Mark as completed
            if self.state_manager and response_data:
                self.state_manager.mark_completed(response_data)

            return response_data

        except Exception as e:
            # Mark as failed on exception
            if self.state_manager:
                self.state_manager.mark_failed(str(e))
            raise

    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate that input data contains required fields.

        Args:
            input_data: Input to validate

        Raises:
            ValueError: If required fields are missing
        """
        # Parse expected input format
        try:
            expected_schema = json.loads(self.definition.input_format)
        except json.JSONDecodeError:
            # If we can't parse the schema, skip validation
            return

        # Check for required fields
        for field, description in expected_schema.items():
            # Fields without "optional" in description are required
            if "optional" not in description.lower():
                if field not in input_data:
                    raise ValueError(f"Missing required input field: {field}")

    def _build_system_prompt(self) -> str:
        """Build the system prompt from agent definition."""
        prompt = f"""You are a {self.definition.name} agent.

## Purpose
{self.definition.purpose}

## Instructions
{self.definition.instructions}

## Input Format
Your input will be provided in the following format:
```json
{self.definition.input_format}
```

## Output Format
You must respond with JSON matching this exact format:
```json
{self.definition.output_format}
```

## When to Request Clarification
Request clarification when:
{chr(10).join(f"- {cond}" for cond in self.definition.clarification_conditions)}

## Termination Conditions
You are done when:
{chr(10).join(f"- {cond}" for cond in self.definition.termination_conditions)}

CRITICAL: Your response must be valid JSON matching the Output Format exactly.
"""
        return prompt

    def _build_user_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build the user prompt with input data."""
        return f"""Please complete the following task:

{json.dumps(input_data, indent=2)}

Remember to respond with valid JSON matching the expected output format.
"""

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from agent response, handling various formats.

        Args:
            response_text: Raw text response from agent

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If no valid JSON found
        """
        import re

        # Try parsing as-is first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_block_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to parse the first complete JSON object
        # Find first { and try parsing incrementally
        first_brace = response_text.find('{')
        if first_brace != -1:
            brace_count = 0
            in_string = False
            escape_next = False

            for i in range(first_brace, len(response_text)):
                char = response_text[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1

                        if brace_count == 0:
                            # Found complete JSON object
                            json_str = response_text[first_brace:i + 1]
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                break

        # If nothing worked, log the response and raise
        logger.error(f"Could not extract JSON from response: {response_text}")
        raise ValueError(f"Agent response does not contain valid JSON: {response_text[:500]}")

    def _handle_tool_use(self, messages: List[Dict[str, Any]], response: Any) -> List[Dict[str, Any]]:
        """
        Handle tool use requests from the agent.

        Args:
            messages: Current conversation messages
            response: API response containing tool_use blocks

        Returns:
            Updated messages list with tool results
        """
        # Add assistant's response to messages
        assistant_content = []
        tool_results = []

        for content_block in response.content:
            if content_block.type == "tool_use":
                logger.info(f"Executing tool: {content_block.name}")

                # Add tool use to assistant content
                assistant_content.append({
                    "type": "tool_use",
                    "id": content_block.id,
                    "name": content_block.name,
                    "input": content_block.input
                })

                # Execute the tool
                tool = self.tools.get_tool(content_block.name)
                if tool:
                    try:
                        result = tool.execute(content_block.input)
                        logger.info(f"Tool {content_block.name} executed successfully")
                    except Exception as e:
                        logger.error(f"Tool {content_block.name} failed: {e}")
                        result = {"success": False, "error": str(e)}
                else:
                    logger.error(f"Unknown tool: {content_block.name}")
                    result = {"success": False, "error": f"Unknown tool: {content_block.name}"}

                # Record tool result in state
                if self.state_manager:
                    self.state_manager.record_tool_result(
                        content_block.name,
                        content_block.input,
                        result
                    )

                # Add tool result
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": json.dumps(result)
                })

        # Add assistant message with tool uses
        messages.append({
            "role": "assistant",
            "content": assistant_content
        })

        # Add tool results
        messages.append({
            "role": "user",
            "content": tool_results
        })

        return messages

    def _extract_final_response(self, response: Any) -> Dict[str, Any]:
        """
        Extract final response data from API response.

        Args:
            response: API response

        Returns:
            Parsed response data
        """
        # Find text content in response
        for content_block in response.content:
            if hasattr(content_block, 'type') and content_block.type == "text":
                try:
                    return self._extract_json_from_response(content_block.text)
                except ValueError:
                    # If JSON parsing fails, return the text as a conversational response
                    logger.info("Agent response is conversational (not JSON), wrapping in success response")
                    return {
                        "status": "completed",
                        "response_type": "conversational",
                        "message": content_block.text,
                        "agent": self.definition.name
                    }
            elif hasattr(content_block, 'text'):
                # Fallback for mock objects
                try:
                    return self._extract_json_from_response(content_block.text)
                except ValueError:
                    logger.info("Agent response is conversational (not JSON), wrapping in success response")
                    return {
                        "status": "completed",
                        "response_type": "conversational",
                        "message": content_block.text,
                        "agent": self.definition.name
                    }

        # If no text found, return empty
        logger.warning("No text content found in response")
        return {}

