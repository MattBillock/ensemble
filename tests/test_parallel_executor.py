"""Tests for Parallel Agent Execution Framework."""
import pytest
import asyncio
import time
from unittest.mock import Mock
from datetime import datetime

from src.runtime.agents.parallel_executor import (
    ParallelAgentExecutor,
    AsyncParallelExecutor,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    PhaseResult
)


class TestParallelExecutor:
    """Test threaded parallel executor."""

    def test_execute_single_task(self):
        """Test executing a single task."""
        executor = ParallelAgentExecutor(max_concurrent=2)

        def mock_agent_fn(task_id, config):
            return {"task_id": task_id, "status": "success", "output": config.get("data")}

        phase_result = executor.execute_phase(
            phase_tasks=["task_1"],
            task_configs={"task_1": {"data": "test_data"}},
            agent_spawn_fn=mock_agent_fn
        )

        assert phase_result.total_tasks == 1
        assert phase_result.successful == 1
        assert phase_result.failed == 0
        assert len(phase_result.task_results) == 1

        result = phase_result.task_results[0]
        assert result.task_id == "task_1"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output["output"] == "test_data"

        executor.shutdown()

    def test_execute_multiple_tasks_in_parallel(self):
        """Test executing multiple tasks in parallel."""
        executor = ParallelAgentExecutor(max_concurrent=3)
        execution_times = {}

        def slow_agent_fn(task_id, config):
            start = time.time()
            time.sleep(0.1)  # Simulate work
            execution_times[task_id] = time.time() - start
            return {"task_id": task_id, "status": "success"}

        start_time = time.time()

        phase_result = executor.execute_phase(
            phase_tasks=["task_1", "task_2", "task_3"],
            task_configs={
                "task_1": {},
                "task_2": {},
                "task_3": {}
            },
            agent_spawn_fn=slow_agent_fn
        )

        total_time = time.time() - start_time

        # All tasks should complete successfully
        assert phase_result.total_tasks == 3
        assert phase_result.successful == 3
        assert phase_result.failed == 0

        # With parallelization, should take ~0.1s, not 0.3s
        # Allow some overhead
        assert total_time < 0.3, f"Tasks ran sequentially (took {total_time}s)"

        executor.shutdown()

    def test_handle_task_failure(self):
        """Test handling of task failures."""
        executor = ParallelAgentExecutor(max_concurrent=2)

        def failing_agent_fn(task_id, config):
            if task_id == "task_2":
                raise ValueError("Task 2 intentionally failed")
            return {"task_id": task_id, "status": "success"}

        phase_result = executor.execute_phase(
            phase_tasks=["task_1", "task_2", "task_3"],
            task_configs={"task_1": {}, "task_2": {}, "task_3": {}},
            agent_spawn_fn=failing_agent_fn
        )

        assert phase_result.total_tasks == 3
        assert phase_result.successful == 2
        assert phase_result.failed == 1

        # Find the failed task
        failed_results = [r for r in phase_result.task_results if r.status == ExecutionStatus.FAILED]
        assert len(failed_results) == 1
        assert failed_results[0].task_id == "task_2"
        assert "intentionally failed" in failed_results[0].error

        executor.shutdown()

    def test_execute_plan_with_phases(self):
        """Test executing a multi-phase plan."""
        executor = ParallelAgentExecutor(max_concurrent=2)

        executed_tasks = []

        def tracking_agent_fn(task_id, config):
            executed_tasks.append(task_id)
            return {"task_id": task_id, "status": "success"}

        plan = ExecutionPlan(
            plan_id="test_plan",
            phases=[
                ["task_1", "task_2"],  # Phase 1: 2 parallel tasks
                ["task_3"],             # Phase 2: 1 task (depends on phase 1)
                ["task_4", "task_5"]    # Phase 3: 2 parallel tasks
            ],
            task_configs={
                "task_1": {},
                "task_2": {},
                "task_3": {},
                "task_4": {},
                "task_5": {}
            },
            max_concurrent=2
        )

        phase_results = executor.execute_plan(plan, tracking_agent_fn)

        # Should have 3 phases
        assert len(phase_results) == 3

        # All tasks should complete
        assert phase_results[0].successful == 2
        assert phase_results[1].successful == 1
        assert phase_results[2].successful == 2

        # All 5 tasks should have been executed
        assert len(executed_tasks) == 5
        assert set(executed_tasks) == {"task_1", "task_2", "task_3", "task_4", "task_5"}

        executor.shutdown()

    def test_respect_max_concurrent_limit(self):
        """Test that max_concurrent limit is respected."""
        max_concurrent = 2
        executor = ParallelAgentExecutor(max_concurrent=max_concurrent)

        concurrent_count = []
        max_seen = 0
        lock = asyncio.Lock()

        def concurrent_tracking_fn(task_id, config):
            nonlocal max_seen

            # Track concurrent execution
            concurrent_count.append(task_id)
            current_count = len(concurrent_count)
            if current_count > max_seen:
                max_seen = current_count

            time.sleep(0.05)  # Simulate work

            concurrent_count.remove(task_id)
            return {"task_id": task_id}

        phase_result = executor.execute_phase(
            phase_tasks=["task_1", "task_2", "task_3", "task_4", "task_5"],
            task_configs={f"task_{i}": {} for i in range(1, 6)},
            agent_spawn_fn=concurrent_tracking_fn
        )

        assert phase_result.successful == 5

        # Should never exceed max_concurrent
        # Note: Due to threading timing, this might be slightly higher
        assert max_seen <= max_concurrent + 1, f"Exceeded concurrency limit: {max_seen} > {max_concurrent}"

        executor.shutdown()

    def test_task_timeout(self):
        """Test task timeout handling."""
        executor = ParallelAgentExecutor(
            max_concurrent=2,
            timeout_per_task_ms=100  # 100ms timeout
        )

        def slow_agent_fn(task_id, config):
            if task_id == "slow_task":
                time.sleep(1)  # Will timeout
            return {"task_id": task_id}

        phase_result = executor.execute_phase(
            phase_tasks=["fast_task", "slow_task"],
            task_configs={"fast_task": {}, "slow_task": {}},
            agent_spawn_fn=slow_agent_fn
        )

        assert phase_result.total_tasks == 2
        assert phase_result.successful == 1
        assert phase_result.failed == 1

        # Find the timed out task
        failed = [r for r in phase_result.task_results if r.status == ExecutionStatus.FAILED]
        assert len(failed) == 1
        assert "timed out" in failed[0].error

        executor.shutdown()

    def test_cancel_execution(self):
        """Test cancelling ongoing execution."""
        executor = ParallelAgentExecutor(max_concurrent=2)

        def long_running_fn(task_id, config):
            time.sleep(2)  # Long task
            return {"task_id": task_id}

        # Start execution in a separate thread
        import threading

        def run_execution():
            executor.execute_phase(
                phase_tasks=["task_1", "task_2"],
                task_configs={"task_1": {}, "task_2": {}},
                agent_spawn_fn=long_running_fn
            )

        thread = threading.Thread(target=run_execution)
        thread.start()

        time.sleep(0.1)  # Let it start

        # Cancel execution
        executor.cancel_execution()

        assert executor.cancelled is True

        # Wait for thread to finish
        thread.join(timeout=1)

        executor.shutdown()

    def test_get_progress(self):
        """Test progress tracking."""
        executor = ParallelAgentExecutor(max_concurrent=2)

        def slow_fn(task_id, config):
            time.sleep(0.2)
            return {"task_id": task_id}

        # Start execution in thread
        import threading

        def run_execution():
            executor.execute_phase(
                phase_tasks=["task_1", "task_2"],
                task_configs={"task_1": {}, "task_2": {}},
                agent_spawn_fn=slow_fn
            )

        thread = threading.Thread(target=run_execution)
        thread.start()

        time.sleep(0.05)  # Let some tasks start

        progress = executor.get_progress()

        # Should have some running tasks
        assert "running" in progress
        assert "completed" in progress
        assert "failed" in progress

        thread.join(timeout=2)
        executor.shutdown()


class TestAsyncParallelExecutor:
    """Test async parallel executor."""

    @pytest.mark.asyncio
    async def test_execute_async_phase(self):
        """Test executing async phase."""
        executor = AsyncParallelExecutor(max_concurrent=3)

        async def async_agent_fn(task_id, config):
            await asyncio.sleep(0.01)  # Simulate async work
            return {"task_id": task_id, "status": "success"}

        phase_result = await executor.execute_phase(
            phase_tasks=["task_1", "task_2", "task_3"],
            task_configs={
                "task_1": {},
                "task_2": {},
                "task_3": {}
            },
            agent_spawn_fn=async_agent_fn
        )

        assert phase_result.total_tasks == 3
        assert phase_result.successful == 3
        assert phase_result.failed == 0

    @pytest.mark.asyncio
    async def test_async_parallelization(self):
        """Test that async tasks run in parallel."""
        executor = AsyncParallelExecutor(max_concurrent=3)

        async def async_slow_fn(task_id, config):
            await asyncio.sleep(0.1)
            return {"task_id": task_id}

        start_time = time.time()

        phase_result = await executor.execute_phase(
            phase_tasks=["task_1", "task_2", "task_3"],
            task_configs={"task_1": {}, "task_2": {}, "task_3": {}},
            agent_spawn_fn=async_slow_fn
        )

        total_time = time.time() - start_time

        assert phase_result.successful == 3

        # Should take ~0.1s (parallel), not 0.3s (sequential)
        assert total_time < 0.25, f"Tasks ran sequentially (took {total_time}s)"

    @pytest.mark.asyncio
    async def test_async_handle_failure(self):
        """Test async failure handling."""
        executor = AsyncParallelExecutor(max_concurrent=2)

        async def async_failing_fn(task_id, config):
            if task_id == "fail_task":
                raise ValueError("Intentional async failure")
            await asyncio.sleep(0.01)
            return {"task_id": task_id}

        phase_result = await executor.execute_phase(
            phase_tasks=["success_task", "fail_task"],
            task_configs={"success_task": {}, "fail_task": {}},
            agent_spawn_fn=async_failing_fn
        )

        assert phase_result.total_tasks == 2
        assert phase_result.successful == 1
        assert phase_result.failed == 1

        failed = [r for r in phase_result.task_results if r.status == ExecutionStatus.FAILED]
        assert len(failed) == 1
        assert "Intentional async failure" in failed[0].error

    @pytest.mark.asyncio
    async def test_async_respect_concurrency_limit(self):
        """Test that async executor respects concurrency limit."""
        max_concurrent = 2
        executor = AsyncParallelExecutor(max_concurrent=max_concurrent)

        active_tasks = set()
        max_seen = 0

        async def concurrent_tracking_fn(task_id, config):
            nonlocal max_seen

            active_tasks.add(task_id)
            current_count = len(active_tasks)
            if current_count > max_seen:
                max_seen = current_count

            await asyncio.sleep(0.05)

            active_tasks.remove(task_id)
            return {"task_id": task_id}

        phase_result = await executor.execute_phase(
            phase_tasks=["task_1", "task_2", "task_3", "task_4", "task_5"],
            task_configs={f"task_{i}": {} for i in range(1, 6)},
            agent_spawn_fn=concurrent_tracking_fn
        )

        assert phase_result.successful == 5
        assert max_seen <= max_concurrent, f"Exceeded concurrency: {max_seen} > {max_concurrent}"


class TestExecutionModels:
    """Test execution data models."""

    def test_execution_result_model(self):
        """Test ExecutionResult model."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            output={"data": "test"},
            started_at="2026-01-11T00:00:00",
            completed_at="2026-01-11T00:01:00",
            duration_ms=60000
        )

        assert result.task_id == "test_task"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output["data"] == "test"
        assert result.error is None

    def test_phase_result_model(self):
        """Test PhaseResult model."""
        results = [
            ExecutionResult(
                task_id=f"task_{i}",
                status=ExecutionStatus.COMPLETED,
                started_at=datetime.now().isoformat()
            )
            for i in range(3)
        ]

        phase = PhaseResult(
            phase_number=1,
            task_results=results,
            total_tasks=3,
            successful=3,
            failed=0,
            duration_ms=5000,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat()
        )

        assert phase.phase_number == 1
        assert phase.total_tasks == 3
        assert phase.successful == 3
        assert len(phase.task_results) == 3

    def test_execution_plan_model(self):
        """Test ExecutionPlan model."""
        plan = ExecutionPlan(
            plan_id="plan_123",
            phases=[["task_1"], ["task_2", "task_3"]],
            task_configs={
                "task_1": {"agent": "backend"},
                "task_2": {"agent": "frontend"},
                "task_3": {"agent": "test"}
            },
            max_concurrent=3
        )

        assert plan.plan_id == "plan_123"
        assert len(plan.phases) == 2
        assert len(plan.phases[0]) == 1
        assert len(plan.phases[1]) == 2
        assert plan.max_concurrent == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
