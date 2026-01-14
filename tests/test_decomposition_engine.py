"""Tests for Smart Task Decomposition Engine."""
import pytest
import networkx as nx
from datetime import datetime

from src.runtime.agents.decomposition_engine import (
    TaskDecompositionEngine,
    TaskAnalysis,
    SubTask,
    DecompositionPlan,
    ResourceEstimate,
    AllocationPlan,
    Schedule,
    TaskComplexity,
    AgentType
)


class TestTaskAnalysis:
    """Test task analysis functionality."""

    def test_analyze_backend_task(self):
        """Test analyzing a backend task."""
        engine = TaskDecompositionEngine()
        request = "Create a REST API for user authentication with JWT tokens and PostgreSQL database"

        analysis = engine.analyze_task(request)

        assert analysis.original_request == request
        assert "authentication" in analysis.goal.lower() or "api" in analysis.goal.lower()
        assert analysis.domain == "backend"
        assert "authentication" in analysis.required_components or "api" in analysis.required_components
        assert len(analysis.scope) > 0
        assert len(analysis.assumptions) > 0

    def test_analyze_frontend_task(self):
        """Test analyzing a frontend task."""
        engine = TaskDecompositionEngine()
        request = "Build a React dashboard component with charts and filters"

        analysis = engine.analyze_task(request)

        assert analysis.domain == "frontend"
        assert "ui_components" in analysis.required_components

    def test_analyze_fullstack_task(self):
        """Test analyzing a full-stack task."""
        engine = TaskDecompositionEngine()
        request = "Create a complete user management system with API backend and React frontend UI"

        analysis = engine.analyze_task(request)

        assert analysis.domain == "full_stack"
        assert len(analysis.required_components) >= 2


class TestTaskDecomposition:
    """Test task decomposition functionality."""

    def test_decompose_backend_task(self):
        """Test decomposing a backend task."""
        engine = TaskDecompositionEngine()
        analysis = TaskAnalysis(
            original_request="Build user auth API",
            goal="Build user authentication API",
            scope=["Backend API", "Database", "JWT auth"],
            required_components=["api", "database", "authentication"],
            domain="backend"
        )

        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0
        assert plan.total_estimated_duration_mins > 0
        assert plan.critical_path_duration_mins > 0
        assert plan.dependency_layers >= 1

        # Verify tasks have proper structure
        for task in plan.sub_tasks:
            assert task.task_id
            assert task.description
            assert task.complexity in [TaskComplexity.SIMPLE, TaskComplexity.CREATIVE, TaskComplexity.STRATEGIC]
            assert task.estimated_duration_mins > 0
            assert task.required_agent_type

    def test_decompose_frontend_task(self):
        """Test decomposing a frontend task."""
        engine = TaskDecompositionEngine()
        analysis = TaskAnalysis(
            original_request="Build dashboard UI",
            goal="Build React dashboard",
            scope=["UI components", "State management"],
            required_components=["ui_components"],
            domain="frontend"
        )

        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0
        # Should have at least UI components and tests
        assert any("component" in task.description.lower() for task in plan.sub_tasks)

    def test_decompose_creates_valid_dag(self):
        """Test that decomposition creates a valid DAG."""
        engine = TaskDecompositionEngine()
        analysis = TaskAnalysis(
            original_request="Build simple API",
            goal="Build API endpoint",
            scope=["API"],
            required_components=["api", "database"],
            domain="backend"
        )

        plan = engine.decompose_task(analysis)
        graph = engine.generate_dependency_graph(plan.sub_tasks)

        # Should be a DAG (no cycles)
        assert nx.is_directed_acyclic_graph(graph)
        # Should have nodes
        assert len(graph.nodes()) > 0
        # Number of nodes should match number of tasks
        assert len(graph.nodes()) == len(plan.sub_tasks)


class TestDependencyGraph:
    """Test dependency graph generation."""

    def test_generate_simple_graph(self):
        """Test generating a simple dependency graph."""
        engine = TaskDecompositionEngine()

        tasks = [
            SubTask(
                task_id="task_1",
                description="Create models",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=[]
            ),
            SubTask(
                task_id="task_2",
                description="Create API",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=40,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["task_1"]
            ),
            SubTask(
                task_id="task_3",
                description="Write tests",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=25,
                required_agent_type=AgentType.TEST_WRITER,
                dependencies=["task_1", "task_2"]
            )
        ]

        graph = engine.generate_dependency_graph(tasks)

        assert len(graph.nodes()) == 3
        assert len(graph.edges()) == 3  # task_1->task_2, task_1->task_3, task_2->task_3
        assert nx.is_directed_acyclic_graph(graph)

    def test_detect_circular_dependencies(self):
        """Test that circular dependencies are detected."""
        engine = TaskDecompositionEngine()

        # Create circular dependency: task_1 -> task_2 -> task_1
        tasks = [
            SubTask(
                task_id="task_1",
                description="Task 1",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=10,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["task_2"]  # Depends on task_2
            ),
            SubTask(
                task_id="task_2",
                description="Task 2",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=10,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["task_1"]  # Depends on task_1 - creates cycle!
            )
        ]

        with pytest.raises(ValueError, match="Circular dependencies"):
            graph = engine.generate_dependency_graph(tasks)

    def test_parallel_tasks(self):
        """Test identifying parallel tasks."""
        engine = TaskDecompositionEngine()

        # Create tasks that can run in parallel (no dependencies between them)
        tasks = [
            SubTask(
                task_id="task_1",
                description="Task 1",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=20,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=[]
            ),
            SubTask(
                task_id="task_2",
                description="Task 2",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=20,
                required_agent_type=AgentType.FRONTEND_DEVELOPER,
                dependencies=[]
            ),
            SubTask(
                task_id="task_3",
                description="Task 3",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=15,
                required_agent_type=AgentType.TEST_WRITER,
                dependencies=["task_1", "task_2"]
            )
        ]

        graph = engine.generate_dependency_graph(tasks)

        # task_1 and task_2 can run in parallel
        # They should be in the same generation
        generations = list(nx.topological_generations(graph))
        assert len(generations[0]) == 2  # First generation has 2 parallel tasks
        assert set(generations[0]) == {"task_1", "task_2"}


class TestResourceEstimation:
    """Test resource estimation."""

    def test_estimate_resources(self):
        """Test basic resource estimation."""
        engine = TaskDecompositionEngine()

        analysis = TaskAnalysis(
            original_request="Build API",
            goal="Build API",
            scope=["API"],
            required_components=["api", "database"],
            domain="backend"
        )

        plan = engine.decompose_task(analysis)
        estimate = engine.estimate_resources(plan)

        assert estimate.total_agents_needed == len(plan.sub_tasks)
        assert estimate.estimated_total_cost_usd > 0
        assert estimate.estimated_tokens > 0
        assert estimate.peak_concurrent_agents > 0
        assert estimate.estimated_wall_clock_mins > 0
        assert len(estimate.agents_by_type) > 0

    def test_resource_estimation_with_parallelization(self):
        """Test that parallelization reduces wall clock time."""
        engine = TaskDecompositionEngine()

        # Create tasks that can run in parallel
        tasks = [
            SubTask(
                task_id="task_1",
                description="Backend",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=60,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=[]
            ),
            SubTask(
                task_id="task_2",
                description="Frontend",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=60,
                required_agent_type=AgentType.FRONTEND_DEVELOPER,
                dependencies=[]
            )
        ]

        plan = DecompositionPlan(
            analysis=TaskAnalysis(
                original_request="Build app",
                goal="Build app",
                scope=["Full stack"],
                required_components=["api", "ui_components"],
                domain="full_stack"
            ),
            sub_tasks=tasks,
            total_estimated_duration_mins=120,
            critical_path_duration_mins=60,  # Can run in parallel
            parallelization_opportunities=2,
            dependency_layers=1
        )

        estimate = engine.estimate_resources(plan)

        # Wall clock time should be critical path (60), not total (120)
        assert estimate.estimated_wall_clock_mins == 60
        assert estimate.peak_concurrent_agents == 2


class TestAllocationAndScheduling:
    """Test allocation and scheduling."""

    def test_create_allocation_plan(self):
        """Test creating an allocation plan."""
        engine = TaskDecompositionEngine()

        analysis = TaskAnalysis(
            original_request="Build API",
            goal="Build API",
            scope=["API"],
            required_components=["api"],
            domain="backend"
        )

        plan = engine.decompose_task(analysis)
        allocation = engine.optimize_allocation(plan)

        assert len(allocation.allocations) == len(plan.sub_tasks)
        assert allocation.total_phases >= 1
        assert len(allocation.execution_phases) == allocation.total_phases

        # All tasks should be allocated
        allocated_tasks = {a.task_id for a in allocation.allocations}
        plan_tasks = {t.task_id for t in plan.sub_tasks}
        assert allocated_tasks == plan_tasks

    def test_generate_schedule(self):
        """Test generating an execution schedule."""
        engine = TaskDecompositionEngine()

        analysis = TaskAnalysis(
            original_request="Build API",
            goal="Build API",
            scope=["API"],
            required_components=["api", "database"],
            domain="backend"
        )

        plan = engine.decompose_task(analysis)
        allocation = engine.optimize_allocation(plan)
        schedule = engine.generate_execution_schedule(plan, allocation)

        assert len(schedule.phases) > 0
        assert schedule.start_time
        assert schedule.estimated_completion_time
        assert len(schedule.critical_path) > 0

        # Each phase should have tasks
        for phase in schedule.phases:
            assert len(phase["tasks"]) > 0
            assert phase["duration_mins"] > 0

    def test_critical_path_identified(self):
        """Test that critical path is correctly identified."""
        engine = TaskDecompositionEngine()

        # Create a simple chain: task_1 -> task_2 -> task_3
        tasks = [
            SubTask(
                task_id="task_1",
                description="Step 1",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=20,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=[]
            ),
            SubTask(
                task_id="task_2",
                description="Step 2",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["task_1"]
            ),
            SubTask(
                task_id="task_3",
                description="Step 3",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=25,
                required_agent_type=AgentType.TEST_WRITER,
                dependencies=["task_2"]
            )
        ]

        plan = DecompositionPlan(
            analysis=TaskAnalysis(
                original_request="Test",
                goal="Test",
                scope=["Test"],
                required_components=["test"],
                domain="backend"
            ),
            sub_tasks=tasks,
            total_estimated_duration_mins=75,
            critical_path_duration_mins=75,
            parallelization_opportunities=0,
            dependency_layers=3
        )

        allocation = engine.optimize_allocation(plan)
        schedule = engine.generate_execution_schedule(plan, allocation)

        # Critical path should be all three tasks
        assert len(schedule.critical_path) == 3
        assert set(schedule.critical_path) == {"task_1", "task_2", "task_3"}


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_workflow_backend(self):
        """Test complete workflow for a backend task."""
        engine = TaskDecompositionEngine()

        # 1. Analyze
        request = "Build a REST API for blog posts with CRUD operations and PostgreSQL"
        analysis = engine.analyze_task(request)

        assert analysis.domain == "backend"

        # 2. Decompose
        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0
        assert plan.total_estimated_duration_mins > 0

        # 3. Estimate resources
        estimate = engine.estimate_resources(plan)

        assert estimate.total_agents_needed > 0
        assert estimate.estimated_total_cost_usd > 0

        # 4. Create allocation
        allocation = engine.optimize_allocation(plan)

        assert len(allocation.allocations) == len(plan.sub_tasks)

        # 5. Generate schedule
        schedule = engine.generate_execution_schedule(plan, allocation)

        assert len(schedule.phases) > 0
        assert len(schedule.critical_path) > 0

    def test_complete_workflow_fullstack(self):
        """Test complete workflow for a full-stack task."""
        engine = TaskDecompositionEngine()

        request = "Create a todo list application with FastAPI backend and React frontend"

        # Full workflow
        analysis = engine.analyze_task(request)
        plan = engine.decompose_task(analysis)
        estimate = engine.estimate_resources(plan)
        allocation = engine.optimize_allocation(plan)
        schedule = engine.generate_execution_schedule(plan, allocation)

        # Should have both backend and frontend tasks
        agent_types = {task.required_agent_type for task in plan.sub_tasks}
        assert AgentType.BACKEND_DEVELOPER in agent_types or AgentType.BACKEND_LEAD in agent_types
        assert AgentType.FRONTEND_DEVELOPER in agent_types or AgentType.FRONTEND_LEAD in agent_types

        # Should have parallelization opportunities
        assert estimate.peak_concurrent_agents > 1 or plan.parallelization_opportunities > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
