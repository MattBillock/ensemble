"""Parallel Agent Execution Framework.

Enables concurrent execution of independent agent tasks based on dependency graphs
and execution phases from the Task Decomposition Engine.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Execution Models
# ============================================================================

class ExecutionStatus(str, Enum):
    """Status of a task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"  # Dependencies not satisfied


class ExecutionResult(BaseModel):
    """Result of a task execution."""
    task_id: str
    status: ExecutionStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    agent_id: Optional[str] = None


class PhaseResult(BaseModel):
    """Result of executing a phase."""
    phase_number: int
    task_results: List[ExecutionResult]
    total_tasks: int
    successful: int
    failed: int
    duration_ms: int
    started_at: str
    completed_at: str


class ExecutionPlan(BaseModel):
    """Complete execution plan with phases."""
    plan_id: str
    phases: List[List[str]]  # List of phases, each containing task IDs
    task_configs: Dict[str, Dict[str, Any]]  # task_id -> config
    max_concurrent: int = 5
    timeout_per_task_ms: int = 600000  # 10 minutes default


# ============================================================================
# Parallel Executor
# ============================================================================

class ParallelAgentExecutor:
    """
    Executes agents in parallel based on dependency phases.

    Features:
    - Concurrent execution within phases
    - Sequential phase ordering (respects dependencies)
    - Resource limiting (max concurrent agents)
    - Error handling and retry logic
    - Progress tracking and cancellation
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout_per_task_ms: int = 600000,
        retry_failed: bool = False,
        max_retries: int = 1
    ):
        """
        Initialize parallel executor.

        Args:
            max_concurrent: Maximum number of agents to run simultaneously
            timeout_per_task_ms: Timeout per task in milliseconds
            retry_failed: Whether to retry failed tasks
            max_retries: Maximum number of retries per task
        """
        self.max_concurrent = max_concurrent
        self.timeout_per_task_ms = timeout_per_task_ms
        self.retry_failed = retry_failed
        self.max_retries = max_retries

        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.logger = logging.getLogger(__name__)

        # Execution state
        self.running_tasks: Dict[str, Future] = {}
        self.completed_tasks: Dict[str, ExecutionResult] = {}
        self.failed_tasks: Dict[str, ExecutionResult] = {}
        self.cancelled = False

    def execute_plan(
        self,
        plan: ExecutionPlan,
        agent_spawn_fn: Callable[[str, Dict[str, Any]], Any]
    ) -> List[PhaseResult]:
        """
        Execute a complete execution plan phase by phase.

        Args:
            plan: Execution plan with phases
            agent_spawn_fn: Function to spawn an agent: fn(task_id, config) -> result

        Returns:
            List of phase results
        """
        self.logger.info(f"Starting execution plan {plan.plan_id} with {len(plan.phases)} phases")

        phase_results = []

        for phase_idx, phase_tasks in enumerate(plan.phases):
            if self.cancelled:
                self.logger.warning("Execution cancelled, stopping")
                break

            self.logger.info(f"Executing Phase {phase_idx + 1}/{len(plan.phases)} with {len(phase_tasks)} tasks")

            # Execute phase
            phase_result = self._execute_phase(
                phase_number=phase_idx + 1,
                task_ids=phase_tasks,
                task_configs=plan.task_configs,
                agent_spawn_fn=agent_spawn_fn
            )

            phase_results.append(phase_result)

            # Check if phase failed critically
            if phase_result.failed > 0:
                self.logger.warning(f"Phase {phase_idx + 1} had {phase_result.failed} failures")

                # If all tasks failed, stop execution
                if phase_result.successful == 0:
                    self.logger.error(f"Phase {phase_idx + 1} completely failed, stopping execution")
                    break

        return phase_results

    def execute_phase(
        self,
        phase_tasks: List[str],
        task_configs: Dict[str, Dict[str, Any]],
        agent_spawn_fn: Callable[[str, Dict[str, Any]], Any]
    ) -> PhaseResult:
        """
        Execute a single phase of tasks in parallel.

        Args:
            phase_tasks: List of task IDs to execute
            task_configs: Configuration for each task
            agent_spawn_fn: Function to spawn an agent

        Returns:
            PhaseResult with execution outcomes
        """
        return self._execute_phase(
            phase_number=1,
            task_ids=phase_tasks,
            task_configs=task_configs,
            agent_spawn_fn=agent_spawn_fn
        )

    def _execute_phase(
        self,
        phase_number: int,
        task_ids: List[str],
        task_configs: Dict[str, Dict[str, Any]],
        agent_spawn_fn: Callable[[str, Dict[str, Any]], Any]
    ) -> PhaseResult:
        """Execute a phase with parallel tasks."""
        start_time = datetime.now()
        futures: Dict[str, Future] = {}
        results: List[ExecutionResult] = []

        # Submit all tasks to thread pool
        for task_id in task_ids:
            if self.cancelled:
                break

            config = task_configs.get(task_id, {})

            self.logger.info(f"Submitting task {task_id} to thread pool")

            future = self.executor.submit(
                self._execute_task,
                task_id,
                config,
                agent_spawn_fn
            )
            futures[task_id] = future
            self.running_tasks[task_id] = future

        # Wait for all tasks to complete
        for task_id, future in futures.items():
            try:
                timeout_seconds = self.timeout_per_task_ms / 1000.0
                result = future.result(timeout=timeout_seconds)
                results.append(result)

                if result.status == ExecutionStatus.COMPLETED:
                    self.completed_tasks[task_id] = result
                else:
                    self.failed_tasks[task_id] = result

            except TimeoutError:
                self.logger.error(f"Task {task_id} timed out after {timeout_seconds}s")
                result = ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.FAILED,
                    error=f"Task timed out after {timeout_seconds}s",
                    started_at=datetime.now().isoformat()
                )
                results.append(result)
                self.failed_tasks[task_id] = result

            except Exception as e:
                self.logger.error(f"Task {task_id} failed with exception: {e}")
                result = ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.FAILED,
                    error=str(e),
                    started_at=datetime.now().isoformat()
                )
                results.append(result)
                self.failed_tasks[task_id] = result

            finally:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

        # Calculate phase metrics
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        successful = sum(1 for r in results if r.status == ExecutionStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == ExecutionStatus.FAILED)

        return PhaseResult(
            phase_number=phase_number,
            task_results=results,
            total_tasks=len(task_ids),
            successful=successful,
            failed=failed,
            duration_ms=duration_ms,
            started_at=start_time.isoformat(),
            completed_at=end_time.isoformat()
        )

    def _execute_task(
        self,
        task_id: str,
        config: Dict[str, Any],
        agent_spawn_fn: Callable[[str, Dict[str, Any]], Any]
    ) -> ExecutionResult:
        """Execute a single task (runs in thread pool)."""
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting task {task_id}")

            # Call agent spawn function
            output = agent_spawn_fn(task_id, config)

            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Check if output indicates failure
            if isinstance(output, dict) and output.get("status") == "failed":
                return ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.FAILED,
                    output=output,
                    error=output.get("error", "Unknown error"),
                    started_at=start_time.isoformat(),
                    completed_at=end_time.isoformat(),
                    duration_ms=duration_ms
                )

            return ExecutionResult(
                task_id=task_id,
                status=ExecutionStatus.COMPLETED,
                output=output if isinstance(output, dict) else {"result": output},
                started_at=start_time.isoformat(),
                completed_at=end_time.isoformat(),
                duration_ms=duration_ms
            )

        except Exception as e:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            self.logger.error(f"Task {task_id} failed with exception: {e}", exc_info=True)

            return ExecutionResult(
                task_id=task_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                started_at=start_time.isoformat(),
                completed_at=end_time.isoformat(),
                duration_ms=duration_ms
            )

    def cancel_execution(self):
        """Cancel ongoing execution."""
        self.logger.warning("Cancelling parallel execution")
        self.cancelled = True

        # Cancel running tasks
        for task_id, future in list(self.running_tasks.items()):
            future.cancel()
            self.logger.info(f"Cancelled task {task_id}")

    def get_progress(self) -> Dict[str, Any]:
        """Get current execution progress."""
        return {
            "running": len(self.running_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "running_tasks": list(self.running_tasks.keys()),
            "cancelled": self.cancelled
        }

    def shutdown(self):
        """Shutdown executor and cleanup resources."""
        self.logger.info("Shutting down parallel executor")
        self.cancel_execution()
        self.executor.shutdown(wait=True)


# ============================================================================
# Async Parallel Executor (Alternative Implementation)
# ============================================================================

class AsyncParallelExecutor:
    """
    Async version of parallel executor using asyncio.

    Better for I/O-bound agent operations (API calls).
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout_per_task_ms: int = 600000
    ):
        """Initialize async executor."""
        self.max_concurrent = max_concurrent
        self.timeout_per_task_ms = timeout_per_task_ms
        self.logger = logging.getLogger(__name__)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_phase(
        self,
        phase_tasks: List[str],
        task_configs: Dict[str, Dict[str, Any]],
        agent_spawn_fn: Callable[[str, Dict[str, Any]], Any]
    ) -> PhaseResult:
        """Execute phase with async concurrency control."""
        start_time = datetime.now()

        # Create tasks with semaphore for concurrency control
        tasks = [
            self._execute_task_async(task_id, task_configs.get(task_id, {}), agent_spawn_fn)
            for task_id in phase_tasks
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        execution_results = []
        for i, result in enumerate(results):
            task_id = phase_tasks[i]

            if isinstance(result, Exception):
                execution_results.append(ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.FAILED,
                    error=str(result),
                    started_at=start_time.isoformat()
                ))
            elif isinstance(result, ExecutionResult):
                execution_results.append(result)
            else:
                # Wrap non-ExecutionResult returns
                execution_results.append(ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.COMPLETED,
                    output={"result": result},
                    started_at=start_time.isoformat()
                ))

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        successful = sum(1 for r in execution_results if r.status == ExecutionStatus.COMPLETED)
        failed = sum(1 for r in execution_results if r.status == ExecutionStatus.FAILED)

        return PhaseResult(
            phase_number=1,
            task_results=execution_results,
            total_tasks=len(phase_tasks),
            successful=successful,
            failed=failed,
            duration_ms=duration_ms,
            started_at=start_time.isoformat(),
            completed_at=end_time.isoformat()
        )

    async def _execute_task_async(
        self,
        task_id: str,
        config: Dict[str, Any],
        agent_spawn_fn: Callable[[str, Dict[str, Any]], Any]
    ) -> ExecutionResult:
        """Execute a single task with async concurrency control."""
        async with self.semaphore:
            start_time = datetime.now()

            try:
                self.logger.info(f"Starting async task {task_id}")

                # If agent_spawn_fn is async, await it; otherwise run in executor
                if asyncio.iscoroutinefunction(agent_spawn_fn):
                    output = await agent_spawn_fn(task_id, config)
                else:
                    loop = asyncio.get_event_loop()
                    output = await loop.run_in_executor(None, agent_spawn_fn, task_id, config)

                end_time = datetime.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)

                return ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.COMPLETED,
                    output=output if isinstance(output, dict) else {"result": output},
                    started_at=start_time.isoformat(),
                    completed_at=end_time.isoformat(),
                    duration_ms=duration_ms
                )

            except Exception as e:
                end_time = datetime.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)

                self.logger.error(f"Async task {task_id} failed: {e}", exc_info=True)

                return ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.FAILED,
                    error=str(e),
                    started_at=start_time.isoformat(),
                    completed_at=end_time.isoformat(),
                    duration_ms=duration_ms
                )
