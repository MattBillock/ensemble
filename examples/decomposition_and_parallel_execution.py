"""
Example: Smart Task Decomposition + Parallel Execution

Demonstrates the complete workflow:
1. Analyze user request
2. Decompose into sub-tasks with dependencies
3. Create execution plan with phases
4. Execute tasks in parallel using the parallel executor
"""
import time
from src.runtime.agents.decomposition_engine import TaskDecompositionEngine
from src.runtime.agents.parallel_executor import ParallelAgentExecutor, ExecutionPlan


def simulate_agent_execution(task_id: str, config: dict) -> dict:
    """
    Simulate an agent executing a task.

    In real usage, this would spawn an actual agent and return its output.
    """
    print(f"  → Executing {task_id}: {config.get('description', 'No description')}")

    # Simulate work based on complexity
    duration = config.get('estimated_duration_mins', 30)
    sleep_time = duration / 600  # Scale down for demo (30 mins → 0.05s)

    time.sleep(sleep_time)

    agent_type = config.get('agent_type', 'unknown')
    print(f"  ✓ Completed {task_id} ({agent_type})")

    return {
        "task_id": task_id,
        "status": "success",
        "output": {
            "description": config.get('description'),
            "agent_type": agent_type,
            "files_created": config.get('outputs', [])
        }
    }


def example_backend_task():
    """Example: Backend API development."""
    print("=" * 80)
    print("EXAMPLE 1: Backend API Development")
    print("=" * 80)

    # Step 1: Analyze and decompose
    engine = TaskDecompositionEngine()
    request = "Build a REST API for blog posts with CRUD operations, PostgreSQL database, and JWT authentication"

    print(f"\n📋 User Request: {request}\n")

    analysis = engine.analyze_task(request)
    print(f"🔍 Analysis:")
    print(f"  - Domain: {analysis.domain}")
    print(f"  - Components: {', '.join(analysis.required_components)}")
    print(f"  - Scope: {len(analysis.scope)} items")

    plan = engine.decompose_task(analysis)
    print(f"\n📦 Decomposition:")
    print(f"  - Total tasks: {len(plan.sub_tasks)}")
    print(f"  - Total estimated time: {plan.total_estimated_duration_mins} mins")
    print(f"  - Critical path: {plan.critical_path_duration_mins} mins")
    print(f"  - Parallelization opportunities: {plan.parallelization_opportunities}")
    print(f"  - Dependency layers: {plan.dependency_layers}")

    # Step 2: Estimate resources
    estimate = engine.estimate_resources(plan)
    print(f"\n💰 Resource Estimate:")
    print(f"  - Total agents needed: {estimate.total_agents_needed}")
    print(f"  - Estimated cost: ${estimate.estimated_total_cost_usd:.3f}")
    print(f"  - Peak concurrent agents: {estimate.peak_concurrent_agents}")
    print(f"  - Wall clock time: {estimate.estimated_wall_clock_mins} mins")
    print(f"  - Time savings: {plan.total_estimated_duration_mins - estimate.estimated_wall_clock_mins} mins ({((plan.total_estimated_duration_mins - estimate.estimated_wall_clock_mins) / plan.total_estimated_duration_mins * 100):.0f}%)")

    # Step 3: Create allocation plan
    allocation = engine.optimize_allocation(plan)
    print(f"\n🗓️  Execution Phases: {allocation.total_phases}")
    for phase_idx, phase_tasks in enumerate(allocation.execution_phases):
        print(f"  Phase {phase_idx + 1}: {len(phase_tasks)} parallel task(s)")
        for task_id in phase_tasks:
            task = next(t for t in plan.sub_tasks if t.task_id == task_id)
            print(f"    - {task_id}: {task.description[:60]}...")

    # Step 4: Execute with parallel executor
    print(f"\n⚡ Parallel Execution:")
    print("-" * 80)

    # Create task configs for executor
    task_configs = {}
    for task in plan.sub_tasks:
        task_configs[task.task_id] = {
            "description": task.description,
            "agent_type": task.required_agent_type,
            "estimated_duration_mins": task.estimated_duration_mins,
            "outputs": task.outputs
        }

    exec_plan = ExecutionPlan(
        plan_id="backend_api_plan",
        phases=allocation.execution_phases,
        task_configs=task_configs,
        max_concurrent=3
    )

    executor = ParallelAgentExecutor(max_concurrent=3)

    start_time = time.time()
    phase_results = executor.execute_plan(exec_plan, simulate_agent_execution)
    total_time = time.time() - start_time

    print("-" * 80)
    print(f"\n✅ Execution Complete!")
    print(f"  - Total time: {total_time:.2f}s (simulated: {total_time * 600:.0f} mins)")
    print(f"  - Phases executed: {len(phase_results)}")

    for phase_result in phase_results:
        print(f"\n  Phase {phase_result.phase_number}:")
        print(f"    - Tasks: {phase_result.total_tasks}")
        print(f"    - Successful: {phase_result.successful}")
        print(f"    - Failed: {phase_result.failed}")
        print(f"    - Duration: {phase_result.duration_ms / 1000:.2f}s")

    executor.shutdown()


def example_fullstack_task():
    """Example: Full-stack application."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Full-Stack Todo Application")
    print("=" * 80)

    engine = TaskDecompositionEngine()
    request = "Create a todo list application with FastAPI backend, React frontend, and PostgreSQL database"

    print(f"\n📋 User Request: {request}\n")

    analysis = engine.analyze_task(request)
    plan = engine.decompose_task(analysis)
    estimate = engine.estimate_resources(plan)
    allocation = engine.optimize_allocation(plan)

    print(f"🔍 Analysis: {analysis.domain}")
    print(f"📦 Tasks: {len(plan.sub_tasks)}")
    print(f"💰 Cost: ${estimate.estimated_total_cost_usd:.3f}")
    print(f"⏱️  Time: {estimate.estimated_wall_clock_mins} mins (with parallelization)")
    print(f"🚀 Speedup: {((plan.total_estimated_duration_mins - estimate.estimated_wall_clock_mins) / plan.total_estimated_duration_mins * 100):.0f}%")

    print(f"\n🗓️  Execution Plan:")
    for phase_idx, phase_tasks in enumerate(allocation.execution_phases):
        print(f"\n  Phase {phase_idx + 1}:")
        for task_id in phase_tasks:
            task = next(t for t in plan.sub_tasks if t.task_id == task_id)
            print(f"    [{task.required_agent_type:25s}] {task.description[:50]}")

    # Execute
    print(f"\n⚡ Executing...")

    task_configs = {}
    for task in plan.sub_tasks:
        task_configs[task.task_id] = {
            "description": task.description,
            "agent_type": task.required_agent_type,
            "estimated_duration_mins": task.estimated_duration_mins
        }

    exec_plan = ExecutionPlan(
        plan_id="fullstack_todo_plan",
        phases=allocation.execution_phases,
        task_configs=task_configs,
        max_concurrent=3
    )

    executor = ParallelAgentExecutor(max_concurrent=3)

    start_time = time.time()
    phase_results = executor.execute_plan(exec_plan, simulate_agent_execution)
    total_time = time.time() - start_time

    print(f"\n✅ Complete in {total_time:.2f}s!")
    print(f"   All {sum(p.successful for p in phase_results)} tasks executed successfully")

    executor.shutdown()


def example_show_parallelization_benefit():
    """Example: Demonstrate parallelization benefits."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Parallelization Benefits")
    print("=" * 80)

    engine = TaskDecompositionEngine()

    # Create a request with obvious parallelization opportunities
    request = "Build authentication API backend AND user dashboard frontend"

    analysis = engine.analyze_task(request)
    plan = engine.decompose_task(analysis)
    estimate = engine.estimate_resources(plan)

    print(f"\n📊 Parallelization Analysis:")
    print(f"  - Total sequential time: {plan.total_estimated_duration_mins} mins")
    print(f"  - Critical path time: {plan.critical_path_duration_mins} mins")
    print(f"  - Wall clock time (parallel): {estimate.estimated_wall_clock_mins} mins")
    print(f"  - Time saved: {plan.total_estimated_duration_mins - estimate.estimated_wall_clock_mins} mins")
    print(f"  - Speedup factor: {plan.total_estimated_duration_mins / estimate.estimated_wall_clock_mins:.2f}x")
    print(f"  - Efficiency gain: {((plan.total_estimated_duration_mins - estimate.estimated_wall_clock_mins) / plan.total_estimated_duration_mins * 100):.0f}%")

    print(f"\n🎯 Peak Concurrency: {estimate.peak_concurrent_agents} agents")
    print(f"   (Backend and frontend tasks can run simultaneously)")

    allocation = engine.optimize_allocation(plan)

    print(f"\n📅 Execution Phases:")
    for phase_idx, phase_tasks in enumerate(allocation.execution_phases):
        phase_duration = max(
            next(t for t in plan.sub_tasks if t.task_id == tid).estimated_duration_mins
            for tid in phase_tasks
        )
        print(f"\n  Phase {phase_idx + 1} ({phase_duration} mins):")
        for task_id in phase_tasks:
            task = next(t for t in plan.sub_tasks if t.task_id == task_id)
            print(f"    [{task.estimated_duration_mins:3d}m] {task.description[:55]}")

        if len(phase_tasks) > 1:
            print(f"    → {len(phase_tasks)} tasks running in parallel!")


def main():
    """Run all examples."""
    print("\n" + "🚀 " + "=" * 76 + " 🚀")
    print("  Smart Task Decomposition + Parallel Execution Examples")
    print("🚀 " + "=" * 76 + " 🚀")

    # Run examples
    example_backend_task()
    example_fullstack_task()
    example_show_parallelization_benefit()

    print("\n\n" + "=" * 80)
    print("✨ All examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
