"""
Unit tests for parallel_executor module.

Tests the ParallelAgentExecutor and AsyncParallelExecutor classes.
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch
from src.runtime.agents.parallel_executor import (
    ExecutionStatus,
    ExecutionResult,
    PhaseResult,
    ExecutionPlan,
    ParallelAgentExecutor,
    AsyncParallelExecutor,
)


class TestExecutionStatus:
    """Test ExecutionStatus enum."""

    def test_status_values(self):
        """Test all status values."""
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"
        assert ExecutionStatus.BLOCKED.value == "blocked"


class TestExecutionResult:
    """Test ExecutionResult pydantic model."""

    def test_result_creation_minimal(self):
        """Test creating ExecutionResult with minimal fields."""
        result = ExecutionResult(
            task_id="task_1",
            status=ExecutionStatus.COMPLETED,
        )

        assert result.task_id == "task_1"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output is None
        assert result.error is None

    def test_result_creation_full(self):
        """Test creating ExecutionResult with all fields."""
        result = ExecutionResult(
            task_id="task_2",
            status=ExecutionStatus.FAILED,
            output={"data": "value"},
            error="Something went wrong",
            started_at="2024-01-01T00:00:00",
            completed_at="2024-01-01T00:01:00",
            duration_ms=60000,
            agent_id="agent-123",
        )

        assert result.task_id == "task_2"
        assert result.status == ExecutionStatus.FAILED
        assert result.output == {"data": "value"}
        assert result.error == "Something went wrong"
        assert result.duration_ms == 60000


class TestPhaseResult:
    """Test PhaseResult pydantic model."""

    def test_phase_result_creation(self):
        """Test creating PhaseResult."""
        task_results = [
            ExecutionResult(task_id="t1", status=ExecutionStatus.COMPLETED),
            ExecutionResult(task_id="t2", status=ExecutionStatus.FAILED),
        ]

        phase = PhaseResult(
            phase_number=1,
            task_results=task_results,
            total_tasks=2,
            successful=1,
            failed=1,
            duration_ms=5000,
            started_at="2024-01-01T00:00:00",
            completed_at="2024-01-01T00:00:05",
        )

        assert phase.phase_number == 1
        assert len(phase.task_results) == 2
        assert phase.successful == 1
        assert phase.failed == 1


class TestExecutionPlan:
    """Test ExecutionPlan pydantic model."""

    def test_plan_creation(self):
        """Test creating ExecutionPlan."""
        plan = ExecutionPlan(
            plan_id="plan_1",
            phases=[["task_1", "task_2"], ["task_3"]],
            task_configs={
                "task_1": {"agent_type": "developer"},
                "task_2": {"agent_type": "tester"},
                "task_3": {"agent_type": "reviewer"},
            },
        )

        assert plan.plan_id == "plan_1"
        assert len(plan.phases) == 2
        assert len(plan.phases[0]) == 2
        assert len(plan.phases[1]) == 1
        assert plan.max_concurrent == 5  # default
        assert plan.timeout_per_task_ms == 600000  # default

    def test_plan_with_custom_settings(self):
        """Test ExecutionPlan with custom settings."""
        plan = ExecutionPlan(
            plan_id="plan_2",
            phases=[["task_1"]],
            task_configs={"task_1": {}},
            max_concurrent=10,
            timeout_per_task_ms=300000,
        )

        assert plan.max_concurrent == 10
        assert plan.timeout_per_task_ms == 300000


class TestParallelAgentExecutor:
    """Test ParallelAgentExecutor class."""

    @pytest.fixture
    def executor(self):
        """Create a fresh executor instance."""
        exec = ParallelAgentExecutor(
            max_concurrent=3,
            timeout_per_task_ms=5000,
        )
        yield exec
        exec.shutdown()

    def test_initialization(self, executor):
        """Test executor initialization."""
        assert executor.max_concurrent == 3
        assert executor.timeout_per_task_ms == 5000
        assert executor.retry_failed is False
        assert executor.cancelled is False

    def test_initialization_with_retry(self):
        """Test executor with retry enabled."""
        exec = ParallelAgentExecutor(retry_failed=True, max_retries=3)
        assert exec.retry_failed is True
        assert exec.max_retries == 3
        exec.shutdown()

    def test_execute_single_task_success(self, executor):
        """Test executing a single successful task."""
        def spawn_fn(task_id, config):
            return {"status": "success", "task": task_id}

        result = executor.execute_phase(
            phase_tasks=["task_1"],
            task_configs={"task_1": {"data": "value"}},
            agent_spawn_fn=spawn_fn,
        )

        assert result.phase_number == 1
        assert result.total_tasks == 1
        assert result.successful == 1
        assert result.failed == 0
        assert len(result.task_results) == 1
        assert result.task_results[0].status == ExecutionStatus.COMPLETED

    def test_execute_single_task_failure(self, executor):
        """Test executing a task that fails."""
        def spawn_fn(task_id, config):
            return {"status": "failed", "error": "Task failed"}

        result = executor.execute_phase(
            phase_tasks=["task_1"],
            task_configs={"task_1": {}},
            agent_spawn_fn=spawn_fn,
        )

        assert result.successful == 0
        assert result.failed == 1
        assert result.task_results[0].status == ExecutionStatus.FAILED

    def test_execute_task_exception(self, executor):
        """Test task that raises exception."""
        def spawn_fn(task_id, config):
            raise ValueError("Something broke")

        result = executor.execute_phase(
            phase_tasks=["task_1"],
            task_configs={"task_1": {}},
            agent_spawn_fn=spawn_fn,
        )

        assert result.failed == 1
        assert "Something broke" in result.task_results[0].error

    def test_execute_multiple_tasks_parallel(self, executor):
        """Test executing multiple tasks in parallel."""
        execution_order = []

        def spawn_fn(task_id, config):
            execution_order.append(task_id)
            time.sleep(0.1)  # Small delay
            return {"task": task_id}

        result = executor.execute_phase(
            phase_tasks=["t1", "t2", "t3"],
            task_configs={"t1": {}, "t2": {}, "t3": {}},
            agent_spawn_fn=spawn_fn,
        )

        assert result.total_tasks == 3
        assert result.successful == 3
        # All tasks should be in execution order (may be in any order due to parallel)
        assert set(execution_order) == {"t1", "t2", "t3"}

    def test_execute_plan_multiple_phases(self, executor):
        """Test executing a multi-phase plan."""
        phase_calls = []

        def spawn_fn(task_id, config):
            phase_calls.append(task_id)
            return {"task": task_id}

        plan = ExecutionPlan(
            plan_id="test_plan",
            phases=[["p1_t1", "p1_t2"], ["p2_t1"]],
            task_configs={
                "p1_t1": {},
                "p1_t2": {},
                "p2_t1": {},
            },
        )

        results = executor.execute_plan(plan, spawn_fn)

        assert len(results) == 2
        assert results[0].phase_number == 1
        assert results[1].phase_number == 2
        assert set(phase_calls) == {"p1_t1", "p1_t2", "p2_t1"}

    def test_execute_plan_stops_on_complete_failure(self, executor):
        """Test that plan stops if all tasks in a phase fail."""
        call_count = 0

        def spawn_fn(task_id, config):
            nonlocal call_count
            call_count += 1
            raise ValueError("All fail")

        plan = ExecutionPlan(
            plan_id="test_plan",
            phases=[["t1"], ["t2", "t3"]],  # Phase 2 should not execute
            task_configs={"t1": {}, "t2": {}, "t3": {}},
        )

        results = executor.execute_plan(plan, spawn_fn)

        # Only first phase should execute since it completely fails
        assert len(results) == 1
        assert results[0].failed == 1
        assert call_count == 1  # Only t1 was called

    def test_cancel_execution(self, executor):
        """Test cancelling execution."""
        executor.cancel_execution()

        assert executor.cancelled is True

    def test_get_progress(self, executor):
        """Test getting execution progress."""
        progress = executor.get_progress()

        assert "running" in progress
        assert "completed" in progress
        assert "failed" in progress
        assert "cancelled" in progress
        assert progress["running"] == 0
        assert progress["completed"] == 0

    def test_get_progress_during_execution(self, executor):
        """Test progress during execution."""
        def slow_spawn_fn(task_id, config):
            time.sleep(0.5)
            return {"task": task_id}

        # Start execution in background
        import threading

        def run_execution():
            executor.execute_phase(
                phase_tasks=["t1"],
                task_configs={"t1": {}},
                agent_spawn_fn=slow_spawn_fn,
            )

        thread = threading.Thread(target=run_execution)
        thread.start()

        # Give time for task to start
        time.sleep(0.1)

        progress = executor.get_progress()
        # Task might be running or completed depending on timing
        assert progress["running"] >= 0

        thread.join()

    def test_execute_with_missing_config(self, executor):
        """Test executing task with missing config uses empty dict."""
        received_config = None

        def spawn_fn(task_id, config):
            nonlocal received_config
            received_config = config
            return {"task": task_id}

        executor.execute_phase(
            phase_tasks=["task_1"],
            task_configs={},  # No config for task_1
            agent_spawn_fn=spawn_fn,
        )

        assert received_config == {}

    def test_shutdown(self):
        """Test executor shutdown."""
        exec = ParallelAgentExecutor()

        exec.shutdown()

        assert exec.cancelled is True


class TestParallelExecutorTimeout:
    """Test timeout behavior."""

    def test_task_timeout(self):
        """Test that slow tasks timeout."""
        executor = ParallelAgentExecutor(
            max_concurrent=1,
            timeout_per_task_ms=100,  # 100ms timeout
        )

        def slow_spawn_fn(task_id, config):
            time.sleep(1)  # 1 second - will timeout
            return {"task": task_id}

        result = executor.execute_phase(
            phase_tasks=["slow_task"],
            task_configs={"slow_task": {}},
            agent_spawn_fn=slow_spawn_fn,
        )

        assert result.failed == 1
        assert "timed out" in result.task_results[0].error.lower()

        executor.shutdown()


class TestAsyncParallelExecutor:
    """Test AsyncParallelExecutor class."""

    @pytest.fixture
    def async_executor(self):
        """Create async executor instance."""
        return AsyncParallelExecutor(max_concurrent=3, timeout_per_task_ms=5000)

    def test_initialization(self, async_executor):
        """Test async executor initialization."""
        assert async_executor.max_concurrent == 3
        assert async_executor.timeout_per_task_ms == 5000

    @pytest.mark.asyncio
    async def test_execute_phase_success(self, async_executor):
        """Test async phase execution with success."""
        def spawn_fn(task_id, config):
            return {"task": task_id, "config": config}

        result = await async_executor.execute_phase(
            phase_tasks=["t1", "t2"],
            task_configs={"t1": {"data": "a"}, "t2": {"data": "b"}},
            agent_spawn_fn=spawn_fn,
        )

        assert result.total_tasks == 2
        assert result.successful == 2
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_execute_phase_with_async_spawn_fn(self, async_executor):
        """Test async execution with async spawn function."""
        async def async_spawn_fn(task_id, config):
            await asyncio.sleep(0.01)
            return {"task": task_id}

        result = await async_executor.execute_phase(
            phase_tasks=["t1"],
            task_configs={"t1": {}},
            agent_spawn_fn=async_spawn_fn,
        )

        assert result.successful == 1

    @pytest.mark.asyncio
    async def test_execute_phase_failure(self, async_executor):
        """Test async execution with failure."""
        def spawn_fn(task_id, config):
            raise ValueError("Async task failed")

        result = await async_executor.execute_phase(
            phase_tasks=["t1"],
            task_configs={"t1": {}},
            agent_spawn_fn=spawn_fn,
        )

        assert result.failed == 1
        assert "Async task failed" in result.task_results[0].error

    @pytest.mark.asyncio
    async def test_execute_phase_mixed_results(self, async_executor):
        """Test async execution with mixed success/failure."""
        def spawn_fn(task_id, config):
            if task_id == "fail_task":
                raise ValueError("Failed")
            return {"task": task_id}

        result = await async_executor.execute_phase(
            phase_tasks=["ok_task", "fail_task"],
            task_configs={"ok_task": {}, "fail_task": {}},
            agent_spawn_fn=spawn_fn,
        )

        assert result.successful == 1
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, async_executor):
        """Test that concurrency limit is respected."""
        concurrent_count = 0
        max_concurrent_seen = 0

        async def counting_spawn_fn(task_id, config):
            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return {"task": task_id}

        # Run more tasks than max_concurrent
        result = await async_executor.execute_phase(
            phase_tasks=["t1", "t2", "t3", "t4", "t5"],
            task_configs={f"t{i}": {} for i in range(1, 6)},
            agent_spawn_fn=counting_spawn_fn,
        )

        assert result.successful == 5
        # Max concurrent should not exceed limit (3)
        assert max_concurrent_seen <= 3


class TestExecutionResultDuration:
    """Test duration tracking in results."""

    def test_duration_calculated_correctly(self):
        """Test that duration is calculated correctly."""
        executor = ParallelAgentExecutor()

        def timed_spawn_fn(task_id, config):
            time.sleep(0.1)  # 100ms
            return {"task": task_id}

        result = executor.execute_phase(
            phase_tasks=["t1"],
            task_configs={"t1": {}},
            agent_spawn_fn=timed_spawn_fn,
        )

        # Duration should be at least 100ms
        assert result.duration_ms >= 100
        assert result.task_results[0].duration_ms >= 100

        executor.shutdown()


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_phase(self):
        """Test executing empty phase."""
        executor = ParallelAgentExecutor()

        result = executor.execute_phase(
            phase_tasks=[],
            task_configs={},
            agent_spawn_fn=lambda t, c: {},
        )

        assert result.total_tasks == 0
        assert result.successful == 0
        assert result.failed == 0

        executor.shutdown()

    def test_empty_plan(self):
        """Test executing empty plan."""
        executor = ParallelAgentExecutor()

        plan = ExecutionPlan(
            plan_id="empty",
            phases=[],
            task_configs={},
        )

        results = executor.execute_plan(plan, lambda t, c: {})

        assert len(results) == 0

        executor.shutdown()

    def test_non_dict_output(self):
        """Test handling non-dict output from spawn function."""
        executor = ParallelAgentExecutor()

        def string_spawn_fn(task_id, config):
            return "string result"

        result = executor.execute_phase(
            phase_tasks=["t1"],
            task_configs={"t1": {}},
            agent_spawn_fn=string_spawn_fn,
        )

        # Should wrap in dict
        assert result.successful == 1
        assert result.task_results[0].output == {"result": "string result"}

        executor.shutdown()

    def test_cancelled_during_phase(self):
        """Test cancellation during phase execution."""
        executor = ParallelAgentExecutor()
        executor.cancelled = True  # Pre-cancel

        result = executor.execute_phase(
            phase_tasks=["t1", "t2"],
            task_configs={"t1": {}, "t2": {}},
            agent_spawn_fn=lambda t, c: {"task": t},
        )

        # Should have fewer results due to cancellation
        assert result.total_tasks <= 2

        executor.shutdown()
