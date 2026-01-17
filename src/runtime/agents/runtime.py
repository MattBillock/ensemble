"""Agent runtime for executing agents with Anthropic API."""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from pathlib import Path

from .definition import AgentDefinition
from .tools import ToolRegistry
from .state import StateManager
from .model_selector import ModelSelector
from .metrics import AgentMetricsTracker
from .activity_tracker import AgentActivityTracker
from .resilience import (
    CircuitBreaker,
    retry_with_exponential_backoff,
    CircuitBreakerOpenError,
    get_global_rate_limiter,
)
from .validation import ResponseValidator
from .naming.name_generator import generate_agent_name, generate_family_name
from .self_improvement import get_improvement_loop
from .achievements import get_achievement_tracker

# New system integrations
from .swarm_state import get_swarm_state
from .event_bus import get_event_bus, EventType
from .model_router import get_model_router, TaskProfile
from .iteration_tuner import get_iteration_tuner

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


class TokenUsage:
    """
    Tracks token usage for API calls.

    This class provides methods to track and accumulate token usage across
    multiple API calls, including prompt tokens and completion tokens.
    """

    def __init__(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        """
        Initialize token usage tracking.

        Args:
            prompt_tokens: Initial prompt token count (default 0)
            completion_tokens: Initial completion token count (default 0)

        Raises:
            ValueError: If token values are negative
        """
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("Token values cannot be negative")

        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens

    @property
    def prompt_tokens(self) -> int:
        """Get the prompt token count."""
        return self._prompt_tokens

    @property
    def completion_tokens(self) -> int:
        """Get the completion token count."""
        return self._completion_tokens

    @property
    def total_tokens(self) -> int:
        """Get the total token count (prompt + completion)."""
        return self._prompt_tokens + self._completion_tokens

    def add_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """
        Add tokens to the current counts.

        Args:
            prompt_tokens: Number of prompt tokens to add
            completion_tokens: Number of completion tokens to add

        Raises:
            ValueError: If token values are negative
        """
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("Token values cannot be negative")

        self._prompt_tokens += prompt_tokens
        self._completion_tokens += completion_tokens

    def to_dict(self) -> Dict[str, int]:
        """
        Convert token usage to a dictionary.

        Returns:
            Dictionary with prompt_tokens, completion_tokens, and total_tokens
        """
        return {
            "prompt_tokens": self._prompt_tokens,
            "completion_tokens": self._completion_tokens,
            "total_tokens": self.total_tokens,
        }


class AgentRuntime:
    """Runtime for executing an agent based on its definition."""

    # Shared metrics tracker across all runtimes
    _metrics_tracker = None
    # Shared activity tracker across all runtimes
    _activity_tracker = None
    # Shared circuit breaker for API calls
    _circuit_breaker = None
    # Cached regex patterns (class-level to avoid recompilation)
    _json_block_pattern = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.DOTALL)

    @classmethod
    def get_metrics_tracker(cls) -> AgentMetricsTracker:
        """Get or create the shared metrics tracker."""
        if cls._metrics_tracker is None:
            cls._metrics_tracker = AgentMetricsTracker()
        return cls._metrics_tracker

    @classmethod
    def get_activity_tracker(cls) -> AgentActivityTracker:
        """Get or create the shared activity tracker."""
        if cls._activity_tracker is None:
            cls._activity_tracker = AgentActivityTracker()
        return cls._activity_tracker

    @classmethod
    def get_circuit_breaker(cls) -> CircuitBreaker:
        """Get or create the shared circuit breaker."""
        if cls._circuit_breaker is None:
            cls._circuit_breaker = CircuitBreaker(
                failure_threshold=5,
                timeout_seconds=60,
                success_threshold=2
            )
        return cls._circuit_breaker

    @classmethod
    def get_swarm_state(cls):
        """Get the swarm state manager."""
        return get_swarm_state()

    @classmethod
    def get_event_bus(cls):
        """Get the event bus for real-time communication."""
        return get_event_bus()

    @classmethod
    def get_model_router(cls, api_key: Optional[str] = None):
        """Get the model router for dynamic model selection."""
        return get_model_router(anthropic_key=api_key)

    def __init__(
        self,
        definition: AgentDefinition,
        api_key: str,
        tools: Optional[ToolRegistry] = None,
        state_file: Optional[Path] = None,
        budget_tier: str = "balanced",
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
        parent_agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        use_dynamic_model_selection: bool = True,
        auto_continue: bool = True,
        fully_autonomous: bool = False,
        family_name: Optional[str] = None
    ):
        """
        Initialize agent runtime.

        Args:
            definition: Agent definition specifying behavior
            api_key: Anthropic API key
            tools: Optional tool registry for agent capabilities
            state_file: Optional path to state file for persistence/resume
            budget_tier: Budget tier for model selection (full_firepower, balanced, economical, dynamic)
            agent_id: Optional agent ID for metrics tracking
            request_id: Optional request ID for tracing
            parent_agent_id: Optional parent agent ID for hierarchy tracking
            session_id: Optional session ID for swarm state tracking
            use_dynamic_model_selection: Whether to use dynamic model router with fuzzing
            auto_continue: If True, automatically continue through milestones without approval
            fully_autonomous: If True, bypass ALL user confirmations and proceed with best judgment
            family_name: Optional family name for agent group cohesion
        """
        self.definition = definition
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        self.tools = tools
        self.iteration_count = 0
        self.state_manager = StateManager(state_file) if state_file else None
        self.budget_tier = budget_tier
        self.use_dynamic_model_selection = use_dynamic_model_selection
        self.auto_continue = auto_continue  # Whether to auto-continue through milestones
        self.fully_autonomous = fully_autonomous  # Whether to bypass ALL user confirmations

        # Iteration tuning: store original and get effective (tuned) max iterations
        self.original_max_iterations = definition.max_iterations
        tuner = get_iteration_tuner()
        effective_max = tuner.get_effective_max_iterations(definition.name, definition.max_iterations)
        if effective_max != definition.max_iterations:
            logger.info(f"Using tuned max_iterations for {definition.name}: {effective_max} (original: {definition.max_iterations})")
            definition.max_iterations = effective_max

        # Generate family name for root agents (those without a parent)
        # Child agents inherit their parent's family name
        if family_name:
            self.family_name = family_name
        elif parent_agent_id is None:
            # Root agent - generate a new family name
            self.family_name = generate_family_name()
            logger.info(f"Generated new family name for root agent: {self.family_name}")
        else:
            # Child agent without explicit family name - use a placeholder
            # (In practice, parent should pass family_name to children)
            self.family_name = None

        # Generate whimsical, memorable agent ID (e.g., "Lumawick Sparrow-Director-4729")
        self.agent_id = agent_id or generate_agent_name(
            agent_type=definition.name,
            parent_id=parent_agent_id,
            use_whimsical=True,
            family_name=self.family_name
        )
        self.request_id = request_id or "unknown"
        self.session_id = session_id
        self.parent_agent_id = parent_agent_id
        self.spawned_agents_count = 0
        self.start_time = None
        self.model_used = None
        # Token tracking for cost analysis
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        # Message history pruning configuration
        self.max_message_history = 50  # Keep last 50 messages max
        self.prune_frequency = 10  # Prune every 10 iterations
        # User input for resume
        self.user_answer = None

        # Register with swarm state if session exists
        if self.session_id:
            self._register_with_swarm_state()

    def _register_with_swarm_state(self):
        """Register this agent with the swarm state manager."""
        try:
            swarm_state = self.get_swarm_state()
            swarm_state.register_agent(
                agent_id=self.agent_id,
                session_id=self.session_id,
                agent_type=self.definition.definition_path or self.definition.category,
                agent_name=self.definition.name,
                request_id=self.request_id,
                parent_agent_id=self.parent_agent_id,
                max_iterations=self.definition.max_iterations
            )

            # Emit agent spawned event
            event_bus = self.get_event_bus()
            event_bus.publish_agent_spawned(
                session_id=self.session_id,
                agent_id=self.agent_id,
                agent_type=self.definition.category,
                agent_name=self.definition.name,
                parent_agent_id=self.parent_agent_id
            )
        except Exception as e:
            logger.warning(f"Failed to register with swarm state: {e}")

    def _select_model_dynamic(self, input_data: Dict[str, Any]) -> str:
        """
        Select model using dynamic model router with quality fuzzing.

        Args:
            input_data: Input data to analyze for complexity

        Returns:
            Selected model ID
        """
        try:
            router = self.get_model_router(self.api_key)

            # Build task description from input
            task_desc = ""
            for key in ["problem_description", "task", "user_vision", "milestone"]:
                if key in input_data:
                    task_desc = str(input_data[key])
                    break

            # Analyze task profile
            profile = router.analyze_task_profile(
                task_description=task_desc or self.definition.purpose,
                agent_type=self.definition.name,
                context_size=len(str(input_data))
            )

            # Determine mode based on budget_tier
            if self.budget_tier == "full_firepower":
                mode = "full_power"
            elif self.budget_tier == "economical":
                mode = "economical"
            else:
                mode = "dynamic"

            # Select model
            result = router.select_model(task_profile=profile, mode=mode)

            logger.info(f"Dynamic model selection: {result.selection_reason}")

            return result.model_id

        except Exception as e:
            logger.warning(f"Dynamic model selection failed, falling back to static: {e}")
            return ModelSelector.select_model(
                budget_tier=self.budget_tier,
                task_complexity=self.definition.task_complexity,
                agent_name=self.definition.name
            )

    def set_user_answer(self, answer: str):
        """
        Set user answer for resuming execution after a question.

        Args:
            answer: User's answer to the agent's question
        """
        self.user_answer = answer

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
        # Record start time for metrics
        self.start_time = datetime.now()

        # Validate input
        self._validate_input(input_data)

        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(input_data)

        # Select model - first check agent's explicit model_preference, then fallback to dynamic/static
        model = None

        # Check if agent definition has an explicit model preference (not the default)
        if self.definition.model_preference and self.definition.model_preference.lower() not in ["default", "haiku"]:
            model_map = {
                "opus": "claude-opus-4-5-20251101",
                "sonnet": "claude-sonnet-4-5-20250929",
                "haiku": "claude-3-5-haiku-20241022"
            }
            pref = self.definition.model_preference.lower()
            if pref in model_map:
                model = model_map[pref]
                logger.info(f"Using agent's model_preference override: {pref} -> {model}")

        # Fallback to dynamic/static selection if no preference override
        if model is None:
            if self.use_dynamic_model_selection and self.budget_tier != "full_firepower":
                model = self._select_model_dynamic(input_data)
            else:
                model = ModelSelector.select_model(
                    budget_tier=self.budget_tier,
                    task_complexity=self.definition.task_complexity,
                    agent_name=self.definition.name
                )

        # Store model for metrics
        self.model_used = model

        logger.info(f"Executing agent: {self.definition.name}")
        logger.info(f"Using model: {model} (tier={self.budget_tier}, complexity={self.definition.task_complexity})")

        # Update swarm state with model info
        if self.session_id:
            try:
                swarm_state = self.get_swarm_state()
                swarm_state.update_agent_status(
                    self.agent_id,
                    status="running",
                    iteration=0
                )
            except Exception as e:
                logger.warning(f"Failed to update swarm state: {e}")

        # Record agent start in activity tracker
        activity_tracker = self.get_activity_tracker()
        # Extract problem description from input_data if available
        problem_desc = None
        if input_data:
            problem_desc = input_data.get("user_vision") or input_data.get("problem_description") or input_data.get("problem")
        activity_tracker.record_agent_started(
            agent_id=self.agent_id,
            agent_name=self.definition.name,
            agent_type=self.definition.category,
            request_id=self.request_id,
            parent_agent_id=self.parent_agent_id,
            input_data=input_data,
            model=model,
            problem=problem_desc,
            project_id=self.request_id,  # Use request_id as project_id
            current_stage="requirements"  # Initial stage
        )

        # Initialize or resume state
        if self.state_manager:
            if self.state_manager.can_resume():
                logger.info("Resuming from previous state")
                resume_info = self.state_manager.get_resume_info()
                self.iteration_count = resume_info["iteration"]
                logger.info(f"Previous execution had {resume_info['spawned_agents_count']} spawned agents")
            else:
                self.state_manager.init_execution(self.definition.name, input_data)

        # Initialize conversation
        messages = [{"role": "user", "content": user_prompt}]

        # If resuming with user answer, inject it into conversation
        if self.user_answer:
            logger.info(f"Resuming with user answer: {self.user_answer[:100]}...")
            messages.append({
                "role": "user",
                "content": f"User's answer to your question:\n\n{self.user_answer}\n\nPlease continue with the implementation based on this clarification."
            })

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

                # Record iteration start
                activity_tracker.record_iteration_started(
                    agent_id=self.agent_id,
                    agent_name=self.definition.name,
                    request_id=self.request_id,
                    iteration=self.iteration_count,
                    max_iterations=self.definition.max_iterations
                )

                # Call Anthropic API with retry logic and circuit breaker
                circuit_breaker = self.get_circuit_breaker()

                # Apply rate limiting before API call
                rate_limiter = get_global_rate_limiter()

                # Estimate input tokens (rough approximation: ~4 chars per token)
                estimated_input_tokens = len(str(api_kwargs.get("messages", []))) // 4

                wait_time = rate_limiter.wait_time_needed(estimated_input_tokens)
                if wait_time > 0:
                    logger.info(
                        f"Rate limit throttle: waiting {wait_time:.2f}s before API call "
                        f"(agent: {self.definition.name}, iteration: {self.iteration_count})"
                    )
                    time.sleep(wait_time)

                def _make_api_call():
                    """Wrapper for API call to use with retry logic."""
                    return circuit_breaker.call(
                        self.client.messages.create,
                        **api_kwargs
                    )

                try:
                    response = retry_with_exponential_backoff(
                        _make_api_call,
                        max_retries=3,
                        base_delay=1.0,
                        max_delay=60.0,
                        retryable_exceptions=(APIConnectionError, RateLimitError, APIError),
                        on_retry=lambda e, attempt, delay: logger.warning(
                            f"API call retry {attempt}: {type(e).__name__}: {e}"
                        )
                    )
                except CircuitBreakerOpenError as e:
                    logger.error(f"Circuit breaker is open, aborting execution: {e}")
                    raise
                except (APIConnectionError, RateLimitError, APIError) as e:
                    logger.error(f"API call failed after all retries: {type(e).__name__}: {e}")
                    raise

                # Capture token usage from this iteration
                if hasattr(response, 'usage'):
                    self.total_input_tokens += response.usage.input_tokens
                    self.total_output_tokens += response.usage.output_tokens
                    logger.debug(f"Iteration {self.iteration_count}: "
                               f"+{response.usage.input_tokens} input, "
                               f"+{response.usage.output_tokens} output tokens "
                               f"(total: {self.total_input_tokens + self.total_output_tokens})")

                    # Record usage in global rate limiter for accurate tracking
                    rate_limiter.record_usage(
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens
                    )

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

                    # Prune message history periodically to prevent unbounded growth
                    if self.iteration_count % self.prune_frequency == 0:
                        messages = self._prune_message_history(messages)

                    api_kwargs["messages"] = messages
                    continue

                # Extract final response
                response_data = self._extract_final_response(response)

                # Validate response against expected schema
                if response_data and response_data.get("response_type") != "conversational":
                    is_valid, validation_errors = ResponseValidator.validate_response(
                        response_data,
                        self.definition.output_format
                    )
                    if not is_valid:
                        logger.warning(
                            f"Response validation failed: {validation_errors}. "
                            f"Response: {response_data}"
                        )
                        # Continue anyway but log the issue
                        # In production, you might want to retry or fail

                # Check termination conditions
                needs_clarification = response_data.get("needs_clarification", False)
                needs_user_input = response_data.get("status") == "needs_user_input"

                # Check if agent is still working (in_progress or phase not complete)
                status = response_data.get("status", "")
                phase = response_data.get("phase", "")
                is_still_working = status == "in_progress"
                phase_not_complete = phase and phase.lower() not in ["complete", "completed", "done", "success"]

                # EXPLICIT completion check: require BOTH status="success" AND phase="complete"
                # This prevents false completion when agent reports progress without finishing
                is_explicitly_complete = (
                    status.lower() == "success" and
                    phase.lower() in ["complete", "completed", "done"]
                )

                if needs_clarification or needs_user_input:
                    # Agent needs user input - record question and wait (unless fully_autonomous)
                    question = response_data.get("user_question") or response_data.get("clarification_question", "")

                    if question:
                        if self.fully_autonomous:
                            # In fully autonomous mode, skip the pause and proceed with best judgment
                            logger.info(f"FULLY AUTONOMOUS MODE: Skipping user input for question: {question}")

                            # Add a message to guide the agent to proceed with defaults
                            messages.append({
                                "role": "user",
                                "content": f"AUTONOMOUS MODE ACTIVE: The system is running in fully autonomous mode. "
                                          f"Your question was: '{question}'. "
                                          f"Please proceed with your best judgment using reasonable defaults. "
                                          f"Make standard technical assumptions and continue with the task."
                            })
                            api_kwargs["messages"] = messages
                            # Don't return - continue the loop
                        else:
                            logger.info(f"Agent {self.definition.name} needs user input: {question}")

                            # Generate question ID
                            import uuid
                            question_id = f"q_{self.agent_id}_{uuid.uuid4().hex[:8]}"

                            # Record question in activity tracker
                            activity_tracker.record_question(
                                agent_id=self.agent_id,
                                agent_name=self.definition.name,
                                request_id=self.request_id,
                                question_id=question_id,
                                question=question,
                                options=response_data.get("options")
                            )

                            # Add question_id to response for tracking
                            response_data["question_id"] = question_id
                            response_data["awaiting_user_input"] = True

                            # Return partial response with question - execution will pause here
                            # The orchestrator/UI will need to provide an answer and resume execution
                            return response_data
                    else:
                        logger.warning("Agent indicated needs_clarification/needs_user_input but didn't provide question")
                        # Continue anyway if no question provided
                elif is_explicitly_complete:
                    # Agent explicitly reported success with phase=complete - allow exit
                    logger.info(f"Agent explicitly completed: status='{status}', phase='{phase}'")
                    break
                elif is_still_working or phase_not_complete or not is_explicitly_complete:
                    # Agent reported progress but hasn't explicitly completed
                    # This includes: status="success" with wrong phase, empty phase, etc.
                    logger.info(f"Agent reported status='{status}', phase='{phase}' - not explicitly complete, continuing")

                    if not self.auto_continue and not self.fully_autonomous:
                        # Pause for approval - return with milestone status
                        logger.info(f"auto_continue=False, pausing for milestone approval")

                        # Generate approval question
                        import uuid
                        question_id = f"milestone_{self.agent_id}_{uuid.uuid4().hex[:8]}"

                        current_milestone = response_data.get("current_milestone", "")
                        milestone_msg = f" (Milestone: {current_milestone})" if current_milestone else ""

                        activity_tracker.record_question(
                            agent_id=self.agent_id,
                            agent_name=self.definition.name,
                            request_id=self.request_id,
                            question_id=question_id,
                            question=f"Milestone complete{milestone_msg}. Continue to next milestone?",
                            options=["Yes, continue", "No, stop here"]
                        )

                        response_data["question_id"] = question_id
                        response_data["awaiting_approval"] = True
                        response_data["approval_type"] = "milestone"

                        return response_data

                    # Auto-continue mode: nudge agent to continue
                    logger.info(f"auto_continue=True, nudging to continue with next phase/milestone")

                    # Add the agent's progress report to messages
                    text_content = ""
                    for block in response.content:
                        if hasattr(block, 'text'):
                            text_content = block.text
                            break

                    if text_content:
                        messages.append({
                            "role": "assistant",
                            "content": text_content
                        })

                    # Send continuation prompt
                    continuation_prompt = (
                        f"Good progress! You reported status='{status}' and phase='{phase}'. "
                        f"Please continue with the next step. Use the appropriate tools to proceed "
                        f"with implementation. Do not stop until all milestones are complete and "
                        f"status='success' with phase='complete'."
                    )
                    messages.append({
                        "role": "user",
                        "content": continuation_prompt
                    })

                    api_kwargs["messages"] = messages

                    # Prune if needed
                    if self.iteration_count % self.prune_frequency == 0:
                        messages = self._prune_message_history(messages)
                        api_kwargs["messages"] = messages

                    continue
                # Note: No else branch needed - explicit completion check is now in the elif above
                # The elif covers all non-complete cases since it includes "not is_explicitly_complete"

            if self.iteration_count >= self.definition.max_iterations:
                logger.warning(f"Agent reached max iterations ({self.definition.max_iterations})")

            # Mark as completed
            if self.state_manager and response_data:
                self.state_manager.mark_completed(response_data)

            # Record agent completion in activity tracker with cost/performance data
            completion_time = datetime.now()
            completion_duration_ms = None
            completion_cost = None
            if self.start_time:
                completion_duration_ms = int((completion_time - self.start_time).total_seconds() * 1000)
                # Calculate cost estimate
                from .cost_calculator import CostCalculator
                completion_cost = CostCalculator.calculate_cost(
                    model=self.model_used or "unknown",
                    input_tokens=self.total_input_tokens,
                    output_tokens=self.total_output_tokens
                )

            activity_tracker.record_agent_completed(
                agent_id=self.agent_id,
                agent_name=self.definition.name,
                request_id=self.request_id,
                result=response_data,
                started_at=self.start_time.isoformat() if self.start_time else None,
                completed_at=completion_time.isoformat(),
                duration_ms=completion_duration_ms,
                model_used=self.model_used,
                cost_estimate=completion_cost,
                input_tokens=self.total_input_tokens,
                output_tokens=self.total_output_tokens
            )

            # Record metrics on success
            self._record_execution_metrics(
                success=True,
                response_data=response_data,
                input_data=input_data
            )

            return response_data

        except Exception as e:
            import traceback
            # Mark as failed on exception
            if self.state_manager:
                self.state_manager.mark_failed(str(e))

            # Record agent failure in activity tracker
            activity_tracker.record_agent_failed(
                agent_id=self.agent_id,
                agent_name=self.definition.name,
                request_id=self.request_id,
                error=str(e),
                traceback=traceback.format_exc()
            )

            # Record metrics on failure
            self._record_execution_metrics(
                success=False,
                error=e,
                input_data=input_data
            )

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
        for field, field_spec in expected_schema.items():
            # Handle both simple format ("field": "string") and JSON schema format ("field": {"type": "..."})
            if isinstance(field_spec, dict):
                # JSON schema format - check for optional in description
                description = field_spec.get("description", "")
                is_optional = "optional" in description.lower() if description else False
            elif isinstance(field_spec, str):
                # Simple format - check for optional in the string
                is_optional = "optional" in field_spec.lower()
            else:
                # Unknown format, assume required
                is_optional = False

            if not is_optional and field not in input_data:
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
        # Inject performance feedback if available (self-improvement loop)
        feedback_section = self._get_performance_feedback()
        if feedback_section:
            prompt += f"\n{feedback_section}\n"

        return prompt

    def _get_performance_feedback(self) -> Optional[str]:
        """Get performance feedback for this agent type from the self-improvement loop."""
        try:
            improvement_loop = get_improvement_loop()
            feedback = improvement_loop.get_feedback_for_agent(self.definition.name)
            if feedback and len(feedback) > 50:  # Only include meaningful feedback
                return feedback
        except Exception as e:
            # Don't fail agent execution if feedback fails
            logger.warning(f"Could not get performance feedback: {e}")
        return None

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
        # Try parsing as-is first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block using cached regex pattern
        match = self._json_block_pattern.search(response_text)
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
        # Get activity tracker
        activity_tracker = self.get_activity_tracker()

        # Add assistant's response to messages
        assistant_content = []
        tool_results = []

        for content_block in response.content:
            if content_block.type == "tool_use":
                logger.info(f"Executing tool: {content_block.name}")

                # Record tool use started
                activity_tracker.record_tool_use(
                    agent_id=self.agent_id,
                    agent_name=self.definition.name,
                    request_id=self.request_id,
                    iteration=self.iteration_count,
                    tool_name=content_block.name,
                    tool_inputs=content_block.input,
                    status="started"
                )

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

                        # Record tool use completed
                        activity_tracker.record_tool_use(
                            agent_id=self.agent_id,
                            agent_name=self.definition.name,
                            request_id=self.request_id,
                            iteration=self.iteration_count,
                            tool_name=content_block.name,
                            tool_inputs=content_block.input,
                            status="completed"
                        )
                    except Exception as e:
                        logger.error(f"Tool {content_block.name} failed: {e}")
                        result = {"success": False, "error": str(e)}

                        # Record tool use failed
                        activity_tracker.record_tool_use(
                            agent_id=self.agent_id,
                            agent_name=self.definition.name,
                            request_id=self.request_id,
                            iteration=self.iteration_count,
                            tool_name=content_block.name,
                            tool_inputs=content_block.input,
                            status="failed"
                        )
                else:
                    logger.error(f"Unknown tool: {content_block.name}")
                    result = {"success": False, "error": f"Unknown tool: {content_block.name}"}

                    # Record tool use failed
                    activity_tracker.record_tool_use(
                        agent_id=self.agent_id,
                        agent_name=self.definition.name,
                        request_id=self.request_id,
                        iteration=self.iteration_count,
                        tool_name=content_block.name,
                        tool_inputs=content_block.input,
                        status="failed"
                    )

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

    def _prune_message_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prune message history to prevent unbounded growth.

        Keeps the initial user message and the most recent messages.

        Args:
            messages: Current message history

        Returns:
            Pruned message history
        """
        if len(messages) <= self.max_message_history:
            return messages

        logger.info(
            f"Pruning message history from {len(messages)} to {self.max_message_history} messages"
        )

        # Keep first message (initial user prompt) and most recent messages
        initial_message = messages[0]
        recent_messages = messages[-(self.max_message_history - 1):]

        return [initial_message] + recent_messages

    def _record_execution_metrics(
        self,
        success: bool,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        input_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record execution metrics to the metrics tracker.

        Args:
            success: Whether execution succeeded
            response_data: Agent response data if successful
            error: Exception if failed
            input_data: Input data provided to agent
        """
        if not self.start_time:
            logger.warning("Cannot record metrics: start_time not set")
            return

        try:
            end_time = datetime.now()
            duration_ms = int((end_time - self.start_time).total_seconds() * 1000)

            # Use agent category from definition (derived from file path)
            agent_type = self.definition.category

            # Extract error type if failed
            error_type = None
            if error:
                error_type = type(error).__name__

            # Extract task description
            task_description = None
            if input_data:
                # Try common field names for task description
                for key in ["problem_description", "task", "user_vision", "milestone"]:
                    if key in input_data:
                        desc = str(input_data[key])
                        task_description = desc[:200] if len(desc) > 200 else desc
                        break

            # Extract self-analysis and performance analysis from response
            self_analysis = None
            performance_analysis = None
            if response_data:
                self_analysis = response_data.get("self_analysis")
                performance_analysis = response_data.get("performance_analysis")

            # Calculate cost
            from .cost_calculator import CostCalculator
            estimated_cost = CostCalculator.calculate_cost(
                model=self.model_used or "unknown",
                input_tokens=self.total_input_tokens,
                output_tokens=self.total_output_tokens
            )

            # Get metrics tracker and record execution
            metrics = self.get_metrics_tracker()
            metrics.record_execution(
                agent_id=self.agent_id,
                agent_type=agent_type,
                agent_name=self.definition.name,
                model_used=self.model_used or "unknown",
                task_complexity=self.definition.task_complexity,
                budget_tier=self.budget_tier,
                success=success,
                duration_ms=duration_ms,
                iterations=self.iteration_count,
                created_at=self.start_time.isoformat(),
                completed_at=end_time.isoformat(),
                request_id=self.request_id,
                parent_agent_id=self.parent_agent_id,
                spawned_agents_count=self.spawned_agents_count,
                error_type=error_type,
                tokens_used=self.total_input_tokens + self.total_output_tokens,
                input_tokens=self.total_input_tokens,
                output_tokens=self.total_output_tokens,
                estimated_cost=estimated_cost,
                task_description=task_description,
                self_analysis=self_analysis,
                performance_analysis=performance_analysis
            )

            logger.info(f"Recorded metrics for {self.definition.name}: success={success}, duration={duration_ms}ms")

            # Record result for iteration tuning (unless error is API rate limit)
            if error_type not in ("RateLimitError", "APIError", "APIConnectionError"):
                tuner = get_iteration_tuner()
                tuning_action = tuner.record_execution_result(
                    agent_name=self.definition.name,
                    success=success,
                    original_max=self.original_max_iterations,
                    actual_iterations=self.iteration_count
                )
                if tuning_action.value != "unchanged":
                    logger.info(f"Iteration tuning for {self.definition.name}: {tuning_action.value}")

            # Check for achievements
            try:
                achievement_tracker = get_achievement_tracker()
                execution_data = {
                    "success": success,
                    "duration_ms": duration_ms,
                    "iterations": self.iteration_count,
                    "spawned_agents_count": self.spawned_agents_count,
                    "tokens_used": self.total_input_tokens + self.total_output_tokens,
                    "error_type": error_type,
                    "self_analysis": self_analysis,
                    "performance_analysis": performance_analysis
                }
                awarded = achievement_tracker.check_and_award(
                    agent_id=self.agent_id,
                    agent_name=self.definition.name,
                    agent_class=self.definition.name,
                    execution_data=execution_data
                )
                if awarded:
                    for achievement in awarded:
                        logger.info(f"Achievement unlocked for {self.definition.name}: {achievement.achievement_id}")
            except Exception as ae:
                logger.warning(f"Achievement check failed (non-critical): {ae}")

        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
            # Don't re-raise - metrics recording should not break execution

