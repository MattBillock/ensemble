"""
Swarm Recovery System - Resume stalled agents and recover failed sessions.

Provides automatic detection and recovery of stalled agents, with
configurable strategies for different failure modes.
"""
import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Strategies for recovering failed/stalled agents."""
    RETRY = "retry"                    # Simple retry with same parameters
    RETRY_WITH_BACKOFF = "retry_backoff"  # Retry with exponential backoff
    ENHANCE_PROMPT = "enhance_prompt"  # Run parameter enhancer on prompt
    REFACTOR_AGENT = "refactor_agent"  # Run refactor on agent definition
    ESCALATE_MODEL = "escalate_model"  # Retry with more powerful model
    SPAWN_REPLACEMENT = "spawn_replacement"  # Spawn new agent to take over
    MANUAL_INTERVENTION = "manual"     # Flag for human review
    ABORT = "abort"                    # Mark as permanently failed


@dataclass
class RecoveryTask:
    """A task in the recovery queue."""
    recovery_id: int
    agent_id: str
    session_id: str
    agent_type: str
    agent_name: str
    input_data: Dict[str, Any]
    reason: str
    strategy: RecoveryStrategy
    priority: int
    attempts: int
    max_attempts: int
    created_at: datetime
    last_attempt: Optional[datetime] = None


class StallDetector:
    """Detects stalled agents based on activity patterns."""

    def __init__(
        self,
        stall_threshold_minutes: int = 5,
        max_iteration_time_minutes: int = 10,
        check_interval_seconds: int = 30
    ):
        self.stall_threshold = timedelta(minutes=stall_threshold_minutes)
        self.max_iteration_time = timedelta(minutes=max_iteration_time_minutes)
        self.check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def detect_stalled_agents(
        self,
        threshold_minutes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Detect agents that appear to be stalled."""
        from .swarm_state import get_swarm_state

        stalled = []
        swarm_state = get_swarm_state()

        # Use provided threshold or default
        threshold = threshold_minutes if threshold_minutes is not None else int(self.stall_threshold.total_seconds() / 60)

        # Get running agents that haven't updated recently
        running_agents = swarm_state.get_stalled_agents(
            stall_threshold_minutes=threshold
        )

        for agent in running_agents:
            stall_reason = self._diagnose_stall(agent)
            if stall_reason:
                stalled.append({
                    **agent,
                    "stall_reason": stall_reason
                })

        return stalled

    def queue_for_recovery(
        self,
        stalled_agents: List[Dict[str, Any]]
    ) -> int:
        """Queue stalled agents for recovery."""
        from .swarm_state import get_swarm_state

        swarm_state = get_swarm_state()
        queued_count = 0

        for agent in stalled_agents:
            agent_id = agent['agent_id']
            session_id = agent['session_id']
            stall_reason = agent.get('stall_reason', 'unknown')

            # Mark agent as stalled
            swarm_state.update_agent_status(agent_id, "stalled")

            # Queue for recovery
            swarm_state.queue_for_recovery(
                agent_id=agent_id,
                session_id=session_id,
                reason=stall_reason,
                strategy="retry",  # Default strategy
                priority=0
            )

            queued_count += 1
            logger.info(f"Queued stalled agent {agent_id} for recovery: {stall_reason}")

        return queued_count

    def _diagnose_stall(self, agent: Dict[str, Any]) -> Optional[str]:
        """Diagnose why an agent might be stalled."""
        last_checkpoint = agent.get('last_checkpoint')
        iteration = agent.get('iteration', 0)
        max_iterations = agent.get('max_iterations', 10)

        # Check if stuck at max iterations
        if iteration >= max_iterations:
            return "max_iterations_reached"

        # Check if no activity for too long
        if last_checkpoint:
            try:
                checkpoint_time = datetime.fromisoformat(last_checkpoint.replace('Z', '+00:00'))
                if datetime.now().astimezone() - checkpoint_time > self.stall_threshold:
                    return "no_activity"
            except:
                pass

        # Check if started but never made progress
        if iteration == 0 and agent.get('started_at'):
            return "stuck_at_start"

        return None

    def start_monitoring(self, on_stall_detected: Callable[[List[Dict]], None]):
        """Start background stall monitoring."""
        if self._running:
            return

        self._running = True

        def monitor_loop():
            while self._running:
                try:
                    stalled = self.detect_stalled_agents()
                    if stalled:
                        on_stall_detected(stalled)
                except Exception as e:
                    logger.error(f"Stall detection error: {e}")

                time.sleep(self.check_interval)

        self._thread = threading.Thread(target=monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Stall detector started")

    def stop_monitoring(self):
        """Stop background stall monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)


class RecoveryOrchestrator:
    """
    Orchestrates recovery of stalled/failed agents.

    Features:
    - Automatic stall detection
    - Multiple recovery strategies
    - Priority-based queue processing
    - Concurrent recovery limit
    - Human-in-the-loop for critical failures
    """

    def __init__(
        self,
        max_concurrent_recoveries: int = 3,
        stall_threshold_minutes: int = 5,
        api_key: Optional[str] = None
    ):
        self.max_concurrent = max_concurrent_recoveries
        self.api_key = api_key
        self._running = False
        self._current_recoveries: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

        self.stall_detector = StallDetector(
            stall_threshold_minutes=stall_threshold_minutes
        )

    def start(self):
        """Start the recovery orchestrator."""
        if self._running:
            return

        self._running = True

        # Start stall detection
        self.stall_detector.start_monitoring(self._on_stalls_detected)

        # Start recovery queue processor
        self._queue_thread = threading.Thread(
            target=self._process_recovery_queue,
            daemon=True
        )
        self._queue_thread.start()

        logger.info("Recovery orchestrator started")

    def stop(self):
        """Stop the recovery orchestrator."""
        self._running = False
        self.stall_detector.stop_monitoring()

        if hasattr(self, '_queue_thread'):
            self._queue_thread.join(timeout=5)

    def _on_stalls_detected(self, stalled_agents: List[Dict[str, Any]]):
        """Handle detected stalled agents."""
        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        for agent in stalled_agents:
            agent_id = agent['agent_id']
            session_id = agent['session_id']
            stall_reason = agent.get('stall_reason', 'unknown')

            # Determine recovery strategy
            strategy = self._determine_strategy(agent, stall_reason)

            # Mark agent as stalled
            swarm_state.update_agent_status(agent_id, "stalled")

            # Queue for recovery
            swarm_state.queue_for_recovery(
                agent_id=agent_id,
                session_id=session_id,
                reason=stall_reason,
                strategy=strategy.value,
                priority=self._calculate_priority(agent, stall_reason)
            )

            logger.warning(
                f"Agent {agent_id} ({agent.get('agent_name')}) stalled: {stall_reason}, "
                f"queued for {strategy.value} recovery"
            )

    def _determine_strategy(
        self,
        agent: Dict[str, Any],
        stall_reason: str
    ) -> RecoveryStrategy:
        """
        Determine the best recovery strategy for a stalled agent.

        Recovery escalation order:
        1. RETRY - Simple retry for transient issues
        2. REFACTOR_AGENT - Update agent definition with guardrails (after any failure)
        3. ENHANCE_PROMPT - Improve the prompt before escalating model
        4. ESCALATE_MODEL - Use more powerful model
        5. MANUAL_INTERVENTION - Human review needed
        """
        iteration = agent.get('iteration', 0)
        attempts = agent.get('recovery_attempts', 0)

        # Progressive escalation based on attempts
        if attempts == 0:
            # First failure - simple retry
            if stall_reason == "stuck_at_start":
                return RecoveryStrategy.RETRY
            elif stall_reason == "no_activity":
                return RecoveryStrategy.RETRY_WITH_BACKOFF
            else:
                return RecoveryStrategy.RETRY

        elif attempts == 1:
            # Second attempt - run agent definition refactor
            # This adds guardrails based on the failure pattern
            return RecoveryStrategy.REFACTOR_AGENT

        elif attempts == 2:
            # Third attempt - enhance the prompt
            # Improve clarity, add constraints before escalating model
            return RecoveryStrategy.ENHANCE_PROMPT

        elif attempts == 3:
            # Fourth attempt - escalate to more powerful model
            return RecoveryStrategy.ESCALATE_MODEL

        elif attempts >= 4:
            # Too many failures - need human review
            return RecoveryStrategy.MANUAL_INTERVENTION

        # Based on stall reason for edge cases
        if stall_reason == "max_iterations_reached":
            # Agent ran out of iterations - enhance prompt or escalate
            return RecoveryStrategy.ENHANCE_PROMPT
        else:
            return RecoveryStrategy.RETRY

    def _calculate_priority(
        self,
        agent: Dict[str, Any],
        stall_reason: str
    ) -> int:
        """Calculate recovery priority (higher = more urgent)."""
        priority = 0

        # Root agents are highest priority
        parent_id = agent.get('parent_agent_id')
        if parent_id is None:
            priority += 100

        # Agents with more progress are higher priority
        iteration = agent.get('iteration', 0)
        priority += iteration * 5

        # Leadership agents are higher priority
        agent_type = agent.get('agent_type', '').lower()
        if 'executive' in agent_type or 'director' in agent_type:
            priority += 50
        elif 'coordinator' in agent_type or 'manager' in agent_type:
            priority += 30
        elif 'lead' in agent_type:
            priority += 20

        return priority

    def _process_recovery_queue(self):
        """Process the recovery queue continuously."""
        from .swarm_state import get_swarm_state

        while self._running:
            try:
                # Check if we can take more recoveries
                with self._lock:
                    active_count = len(self._current_recoveries)

                if active_count >= self.max_concurrent:
                    time.sleep(5)
                    continue

                # Get next recovery task
                swarm_state = get_swarm_state()
                queue = swarm_state.get_recovery_queue(limit=1)

                if not queue:
                    time.sleep(5)
                    continue

                task = queue[0]

                # Start recovery in background
                recovery_thread = threading.Thread(
                    target=self._execute_recovery,
                    args=(task,),
                    daemon=True
                )
                recovery_thread.start()

                with self._lock:
                    self._current_recoveries[task['agent_id']] = recovery_thread

            except Exception as e:
                logger.error(f"Recovery queue processing error: {e}")
                time.sleep(5)

    def _execute_recovery(self, task: Dict[str, Any]):
        """Execute a recovery task."""
        from .swarm_state import get_swarm_state

        agent_id = task['agent_id']
        recovery_id = task['id']
        strategy = RecoveryStrategy(task['recovery_strategy'])

        swarm_state = get_swarm_state()

        try:
            logger.info(f"Starting recovery for agent {agent_id} with strategy {strategy.value}")

            # Update recovery status
            swarm_state.update_recovery_status(recovery_id, "in_progress", increment_attempts=True)

            # Execute based on strategy
            if strategy == RecoveryStrategy.RETRY:
                success = self._retry_agent(task)
            elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                success = self._retry_agent(task, backoff=True)
            elif strategy == RecoveryStrategy.REFACTOR_AGENT:
                # Run agent definition refactor, then retry
                self._refactor_agent_definition(task)
                success = self._retry_agent(task)
            elif strategy == RecoveryStrategy.ENHANCE_PROMPT:
                # Enhance prompt, then retry
                enhanced_input = self._enhance_prompt(task)
                if enhanced_input:
                    task['input_data'] = enhanced_input
                success = self._retry_agent(task)
            elif strategy == RecoveryStrategy.ESCALATE_MODEL:
                success = self._retry_agent(task, escalate_model=True)
            elif strategy == RecoveryStrategy.SPAWN_REPLACEMENT:
                success = self._spawn_replacement(task)
            elif strategy == RecoveryStrategy.MANUAL_INTERVENTION:
                # Just mark for manual review
                swarm_state.update_recovery_status(recovery_id, "needs_review")
                logger.info(f"Agent {agent_id} flagged for manual intervention")
                return
            else:
                # Abort
                swarm_state.update_agent_status(agent_id, "failed", error_message="Recovery aborted")
                swarm_state.update_recovery_status(recovery_id, "aborted")
                return

            if success:
                swarm_state.update_recovery_status(recovery_id, "completed")
                swarm_state.update_agent_status(agent_id, "recovered")
                logger.info(f"Successfully recovered agent {agent_id}")
            else:
                # Check if we should retry or escalate
                if task['attempts'] < task['max_attempts']:
                    swarm_state.update_recovery_status(recovery_id, "pending")
                else:
                    swarm_state.update_recovery_status(recovery_id, "failed")
                    swarm_state.update_agent_status(agent_id, "failed", error_message="Recovery failed after max attempts")

        except Exception as e:
            logger.error(f"Recovery failed for agent {agent_id}: {e}")
            swarm_state.update_recovery_status(recovery_id, "failed")
            swarm_state.update_agent_status(agent_id, "failed", error_message=str(e))

        finally:
            with self._lock:
                self._current_recoveries.pop(agent_id, None)

    def _retry_agent(
        self,
        task: Dict[str, Any],
        backoff: bool = False,
        escalate_model: bool = False
    ) -> bool:
        """Retry a stalled agent."""
        from .definition import AgentDefinition
        from .runtime import AgentRuntime
        from .swarm_state import get_swarm_state

        if not self.api_key:
            logger.error("Cannot retry agent: no API key configured")
            return False

        agent_id = task['agent_id']
        agent_type = task['agent_type']
        input_data = task.get('input_data', {})

        swarm_state = get_swarm_state()

        # Get original agent info
        agent_info = swarm_state.get_agent(agent_id)
        if not agent_info:
            return False

        # Apply backoff if requested
        if backoff:
            attempt = task.get('attempts', 0)
            delay = min(60, 2 ** attempt)  # Max 60 seconds
            time.sleep(delay)

        # Determine model
        budget_tier = "balanced"
        if escalate_model:
            # Escalate from current model
            current_model = agent_info.get('model_used', '')
            if 'haiku' in current_model.lower():
                budget_tier = "balanced"  # haiku -> sonnet
            elif 'sonnet' in current_model.lower():
                budget_tier = "full_firepower"  # sonnet -> opus
            else:
                budget_tier = "full_firepower"

        try:
            # Load agent definition
            agent_types_dir = Path(__file__).parent.parent.parent.parent
            agent_def_path = agent_types_dir / f"{agent_type}.md"
            agent_definition = AgentDefinition.from_file(agent_def_path)

            # Create new runtime with potentially escalated model
            new_agent_id = f"{agent_id}_recovery_{int(time.time())}"

            # Create tools with the agent's permissions
            from .tools import ToolRegistry, SpawnAgentTool
            tools = ToolRegistry.default(
                agent_definition=agent_definition,
                request_id=task.get('request_id'),
                session_id=task.get('session_id'),
                agent_id=new_agent_id
            )

            # Add spawn capability
            spawn_tool = SpawnAgentTool(
                agent_types_dir=agent_types_dir,
                api_key=self.api_key,
                tools=None,
                budget_tier=budget_tier,
                parent_agent_id=new_agent_id,
                request_id=task.get('request_id'),
                session_id=task.get('session_id')
            )
            tools.register(spawn_tool)

            runtime = AgentRuntime(
                agent_definition,
                api_key=self.api_key,
                tools=tools,  # Now includes tools with correct permissions
                budget_tier=budget_tier,
                agent_id=new_agent_id,
                request_id=task.get('request_id'),
                parent_agent_id=agent_info.get('parent_agent_id'),
                session_id=task.get('session_id')
            )

            # Execute
            result = runtime.execute(input_data)

            return result.get('status') == 'success'

        except Exception as e:
            logger.error(f"Agent retry failed: {e}")
            return False

    def _spawn_replacement(self, task: Dict[str, Any]) -> bool:
        """Spawn a replacement agent to take over the task."""
        # Similar to retry but creates a fresh agent
        return self._retry_agent(task, escalate_model=True)

    def _refactor_agent_definition(self, task: Dict[str, Any]) -> bool:
        """
        Run agent definition refactor to add guardrails.

        This analyzes the failure and updates the agent definition
        to prevent similar failures in the future.
        """
        from .guardrail_system import get_guardrail_system

        agent_type = task.get('agent_type', '')
        failure_reason = task.get('recovery_reason', 'unknown')
        input_data = task.get('input_data', {})

        try:
            guardrail_system = get_guardrail_system()

            # Learn from this failure
            guardrail_system.learn_from_failure(
                agent_type=agent_type,
                failure_type=failure_reason,
                failure_description=f"Agent {task.get('agent_name')} failed: {failure_reason}",
                context={
                    "input_summary": str(input_data)[:500],
                    "attempts": task.get('attempts', 0),
                    "max_iterations": task.get('max_attempts', 10),
                }
            )

            logger.info(f"Recorded failure pattern for {agent_type}: {failure_reason}")

            # If we have an agent definition path, try to update it
            agent_def_path = self._get_agent_definition_path(agent_type)
            if agent_def_path and agent_def_path.exists():
                self._update_agent_definition_with_guardrails(agent_def_path, agent_type)

            return True

        except Exception as e:
            logger.error(f"Agent refactor failed: {e}")
            return False

    def _get_agent_definition_path(self, agent_type: str) -> Optional[Path]:
        """Get the path to an agent definition file."""
        # Agent types are like "developers/code_writer" -> "developers/code_writer.md"
        base_path = Path(__file__).parent.parent.parent.parent
        agent_path = base_path / f"{agent_type}.md"
        if agent_path.exists():
            return agent_path
        return None

    def _update_agent_definition_with_guardrails(
        self,
        agent_path: Path,
        agent_type: str
    ) -> bool:
        """Update an agent definition file with new guardrails."""
        from .guardrail_system import get_guardrail_system

        try:
            guardrail_system = get_guardrail_system()

            # Get formatted guardrails for this agent
            guardrails_section = guardrail_system.format_guardrails_for_agent_definition(
                agent_type, format_style="markdown"
            )

            if not guardrails_section:
                return False

            # Read current definition
            content = agent_path.read_text()

            # Check if we already have an anti-patterns section
            if "### Anti-Patterns" in content:
                # Already has guardrails, skip
                logger.info(f"Agent {agent_type} already has anti-patterns section")
                return True

            # Find the Instructions section and add guardrails after it
            if "## Instructions" in content:
                # Insert before ## Self-Improvement or at end of instructions
                if "## Self-Improvement" in content:
                    parts = content.split("## Self-Improvement")
                    new_content = parts[0] + guardrails_section + "\n## Self-Improvement" + parts[1]
                else:
                    # Add at end
                    new_content = content + "\n" + guardrails_section

                # Backup and update
                backup_path = agent_path.with_suffix('.md.backup')
                backup_path.write_text(content)

                agent_path.write_text(new_content)
                logger.info(f"Updated agent definition: {agent_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update agent definition: {e}")
            return False

    def _enhance_prompt(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enhance the input prompt for better success.

        Adds guardrails, clarifies requirements, and improves structure.
        """
        from .guardrail_system import get_guardrail_system

        agent_type = task.get('agent_type', '')
        input_data = task.get('input_data', {})
        failure_reason = task.get('recovery_reason', 'unknown')

        try:
            guardrail_system = get_guardrail_system()

            # Get the task/prompt from input data
            task_field = None
            for field in ['task', 'prompt', 'message', 'problem', 'request']:
                if field in input_data:
                    task_field = field
                    break

            if not task_field:
                logger.warning("Could not find task field in input data")
                return input_data

            original_prompt = input_data[task_field]

            # Apply guardrails to the prompt
            enhanced_prompt, applied_ids = guardrail_system.apply_guardrails_to_prompt(
                prompt=original_prompt,
                agent_type=agent_type,
                max_guardrails=8
            )

            # Add failure-specific guidance
            failure_guidance = self._get_failure_specific_guidance(failure_reason)
            if failure_guidance:
                enhanced_prompt += f"\n\n**PREVIOUS FAILURE - AVOID THIS:**\n{failure_guidance}"

            # Add explicit completion criteria if missing
            if "complete when" not in enhanced_prompt.lower() and "success criteria" not in enhanced_prompt.lower():
                enhanced_prompt += "\n\n**COMPLETION CRITERIA:**\n- Task is complete when all explicit requirements are implemented\n- Verify functionality before marking done\n- Do NOT consider partial completion as done"

            # Update input data with enhanced prompt
            enhanced_input = dict(input_data)
            enhanced_input[task_field] = enhanced_prompt
            enhanced_input['_enhanced'] = True
            enhanced_input['_guardrails_applied'] = applied_ids

            logger.info(f"Enhanced prompt for {agent_type} with {len(applied_ids)} guardrails")
            return enhanced_input

        except Exception as e:
            logger.error(f"Prompt enhancement failed: {e}")
            return input_data

    def _get_failure_specific_guidance(self, failure_reason: str) -> str:
        """Get specific guidance based on the failure type."""
        guidance_map = {
            "max_iterations_reached": "The previous attempt ran out of iterations. Focus on completing the core requirements first before any extras.",
            "scope_creep": "The previous attempt expanded beyond the task scope. Stay strictly within the explicit requirements.",
            "no_activity": "The previous attempt stalled. If you encounter any blockers, immediately ask for clarification instead of stopping.",
            "incomplete": "The previous attempt was incomplete. Ensure all requirements are fully implemented before finishing.",
            "stuck_at_start": "The previous attempt failed to start. Break down the first step into smaller, concrete actions.",
            "error_loop": "The previous attempt kept encountering errors. Try a different approach if the first one doesn't work.",
        }
        return guidance_map.get(failure_reason, "")

    def queue_manual_recovery(
        self,
        agent_id: str,
        session_id: str,
        reason: str = "Manual recovery requested"
    ):
        """Manually queue an agent for recovery."""
        from .swarm_state import get_swarm_state

        swarm_state = get_swarm_state()
        swarm_state.queue_for_recovery(
            agent_id=agent_id,
            session_id=session_id,
            reason=reason,
            strategy=RecoveryStrategy.RETRY.value,
            priority=200  # High priority for manual requests
        )

        logger.info(f"Manually queued agent {agent_id} for recovery")

    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status."""
        from .swarm_state import get_swarm_state

        swarm_state = get_swarm_state()
        queue = swarm_state.get_recovery_queue(limit=100)

        with self._lock:
            active_recoveries = list(self._current_recoveries.keys())

        return {
            "is_running": self._running,
            "active_recoveries": active_recoveries,
            "queue_length": len(queue),
            "pending_tasks": [
                {
                    "agent_id": t['agent_id'],
                    "agent_name": t.get('agent_name'),
                    "reason": t['recovery_reason'],
                    "strategy": t['recovery_strategy'],
                    "attempts": t['attempts']
                }
                for t in queue
            ]
        }

    def get_queue_status(self) -> Dict[str, Any]:
        """Get the current recovery queue status (alias for API)."""
        return self.get_recovery_status()

    def recover_agent(
        self,
        agent_id: str,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    ) -> Dict[str, Any]:
        """Manually trigger recovery for a specific agent."""
        from .swarm_state import get_swarm_state

        swarm_state = get_swarm_state()

        # Get agent info
        agent = swarm_state.get_agent(agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        # Queue for recovery with high priority
        swarm_state.queue_for_recovery(
            agent_id=agent_id,
            session_id=agent['session_id'],
            reason="Manual recovery triggered via API",
            strategy=strategy.value,
            priority=250  # Very high priority for manual requests
        )

        return {
            "success": True,
            "message": f"Agent {agent_id} queued for {strategy.value} recovery",
            "agent_name": agent.get('agent_name'),
            "session_id": agent['session_id']
        }

    def get_recovery_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of recovery operations."""
        from .swarm_state import get_swarm_state

        swarm_state = get_swarm_state()

        with swarm_state._get_connection() as conn:
            rows = conn.execute("""
                SELECT r.*, a.agent_name, a.agent_type
                FROM recovery_queue r
                JOIN agents a ON r.agent_id = a.agent_id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]


# Global recovery orchestrator
_recovery_orchestrator: Optional[RecoveryOrchestrator] = None


def get_recovery_orchestrator(api_key: Optional[str] = None) -> RecoveryOrchestrator:
    """Get or create the global recovery orchestrator."""
    global _recovery_orchestrator
    if _recovery_orchestrator is None:
        _recovery_orchestrator = RecoveryOrchestrator(api_key=api_key)
    elif api_key and not _recovery_orchestrator.api_key:
        _recovery_orchestrator.api_key = api_key
    return _recovery_orchestrator
