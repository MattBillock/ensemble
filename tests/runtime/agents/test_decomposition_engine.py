"""
Unit tests for decomposition_engine module.

Tests the TaskDecompositionEngine class and related models.
"""

import pytest
from src.runtime.agents.decomposition_engine import (
    TaskComplexity,
    AgentType,
    SubTask,
    TaskAnalysis,
    DecompositionPlan,
    ResourceEstimate,
    AgentAllocation,
    AllocationPlan,
    Schedule,
    TaskDecompositionEngine,
)


class TestTaskComplexity:
    """Test TaskComplexity enum."""

    def test_complexity_values(self):
        """Test all complexity values."""
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.CREATIVE.value == "creative"
        assert TaskComplexity.STRATEGIC.value == "strategic"


class TestAgentType:
    """Test AgentType enum."""

    def test_agent_type_values(self):
        """Test some agent type values."""
        assert AgentType.EXECUTIVE_DIRECTOR.value == "executive_director"
        assert AgentType.DEVELOPMENT_MANAGER.value == "development_manager"
        assert AgentType.BACKEND_DEVELOPER.value == "backend_developer"
        assert AgentType.FRONTEND_DEVELOPER.value == "frontend_developer"
        assert AgentType.TEST_WRITER.value == "test_writer"


class TestSubTask:
    """Test SubTask pydantic model."""

    def test_subtask_creation_minimal(self):
        """Test creating SubTask with minimal fields."""
        task = SubTask(
            task_id="task_1",
            description="Test task",
            complexity=TaskComplexity.SIMPLE,
            estimated_duration_mins=30,
            required_agent_type=AgentType.BACKEND_DEVELOPER,
        )

        assert task.task_id == "task_1"
        assert task.description == "Test task"
        assert task.complexity == TaskComplexity.SIMPLE
        assert task.estimated_duration_mins == 30
        assert task.dependencies == []
        assert task.priority == 5  # default

    def test_subtask_creation_full(self):
        """Test creating SubTask with all fields."""
        task = SubTask(
            task_id="task_2",
            description="Full task",
            complexity=TaskComplexity.STRATEGIC,
            estimated_duration_mins=60,
            required_agent_type=AgentType.SYSTEM_ARCHITECT,
            dependencies=["task_1"],
            required_tools=["write_file", "read_file"],
            inputs=["requirements.md"],
            outputs=["architecture.md"],
            acceptance_criteria=["Docs complete"],
            priority=8,
            parallelizable=True,
        )

        assert task.dependencies == ["task_1"]
        assert task.required_tools == ["write_file", "read_file"]
        assert task.priority == 8
        assert task.parallelizable is True


class TestTaskAnalysis:
    """Test TaskAnalysis pydantic model."""

    def test_task_analysis_creation(self):
        """Test creating TaskAnalysis."""
        analysis = TaskAnalysis(
            original_request="Build a REST API",
            goal="Create REST API endpoints",
            scope=["Backend implementation"],
            required_components=["api", "database"],
        )

        assert analysis.original_request == "Build a REST API"
        assert analysis.goal == "Create REST API endpoints"
        assert analysis.domain == "general"  # default
        assert analysis.out_of_scope == []  # default

    def test_task_analysis_with_constraints(self):
        """Test TaskAnalysis with constraints."""
        analysis = TaskAnalysis(
            original_request="Build API with auth",
            goal="Build secure API",
            scope=["Backend"],
            required_components=["api"],
            constraints=["Must be secure"],
            assumptions=["Using FastAPI"],
        )

        assert analysis.constraints == ["Must be secure"]
        assert analysis.assumptions == ["Using FastAPI"]


class TestDecompositionPlan:
    """Test DecompositionPlan pydantic model."""

    def test_decomposition_plan_creation(self):
        """Test creating DecompositionPlan."""
        analysis = TaskAnalysis(
            original_request="Test",
            goal="Test goal",
            scope=["Scope"],
            required_components=["core"],
        )

        sub_tasks = [
            SubTask(
                task_id="t1",
                description="Task 1",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
            )
        ]

        plan = DecompositionPlan(
            analysis=analysis,
            sub_tasks=sub_tasks,
            total_estimated_duration_mins=30,
            critical_path_duration_mins=30,
        )

        assert plan.total_estimated_duration_mins == 30
        assert plan.parallelization_opportunities == 0  # default


class TestResourceEstimate:
    """Test ResourceEstimate pydantic model."""

    def test_resource_estimate_creation(self):
        """Test creating ResourceEstimate."""
        estimate = ResourceEstimate(
            total_agents_needed=5,
            agents_by_type={"backend_developer": 3, "test_writer": 2},
            estimated_total_cost_usd=0.15,
            estimated_tokens=10000,
            peak_concurrent_agents=3,
            estimated_wall_clock_mins=60,
        )

        assert estimate.total_agents_needed == 5
        assert estimate.estimated_total_cost_usd == 0.15
        assert estimate.peak_concurrent_agents == 3


class TestAgentAllocation:
    """Test AgentAllocation pydantic model."""

    def test_agent_allocation_creation(self):
        """Test creating AgentAllocation."""
        allocation = AgentAllocation(
            task_id="task_1",
            agent_type=AgentType.BACKEND_DEVELOPER,
            estimated_start="2024-01-01T00:00:00",
            estimated_duration_mins=30,
        )

        assert allocation.task_id == "task_1"
        assert allocation.estimated_duration_mins == 30


class TestAllocationPlan:
    """Test AllocationPlan pydantic model."""

    def test_allocation_plan_creation(self):
        """Test creating AllocationPlan."""
        allocations = [
            AgentAllocation(
                task_id="t1",
                agent_type=AgentType.BACKEND_DEVELOPER,
                estimated_start="2024-01-01T00:00:00",
                estimated_duration_mins=30,
            )
        ]

        plan = AllocationPlan(
            allocations=allocations,
            execution_phases=[["t1"]],
            total_phases=1,
        )

        assert plan.total_phases == 1
        assert len(plan.allocations) == 1


class TestSchedule:
    """Test Schedule pydantic model."""

    def test_schedule_creation(self):
        """Test creating Schedule."""
        schedule = Schedule(
            phases=[{"phase": 1, "tasks": []}],
            estimated_completion_time="2024-01-01T01:00:00",
            critical_path=["t1", "t2"],
        )

        assert len(schedule.phases) == 1
        assert schedule.critical_path == ["t1", "t2"]


class TestTaskDecompositionEngine:
    """Test TaskDecompositionEngine class."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return TaskDecompositionEngine()

    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert hasattr(engine, 'SIMPLE_KEYWORDS')
        assert hasattr(engine, 'CREATIVE_KEYWORDS')
        assert hasattr(engine, 'STRATEGIC_KEYWORDS')

    def test_analyze_task_backend(self, engine):
        """Test analyzing backend task."""
        analysis = engine.analyze_task(
            "Build a REST API with database endpoints for user management"
        )

        assert analysis.domain == "backend"
        assert "api" in analysis.required_components or "database" in analysis.required_components
        assert len(analysis.goal) > 0

    def test_analyze_task_frontend(self, engine):
        """Test analyzing frontend task."""
        analysis = engine.analyze_task(
            "Create a dashboard UI component with React interface for data visualization"
        )

        assert analysis.domain == "frontend"
        assert "ui_components" in analysis.required_components

    def test_analyze_task_fullstack(self, engine):
        """Test analyzing full-stack task."""
        analysis = engine.analyze_task(
            "Build a complete app with REST API backend service and React dashboard UI component interface"
        )

        assert analysis.domain == "full_stack"

    def test_analyze_task_testing(self, engine):
        """Test analyzing testing task."""
        analysis = engine.analyze_task(
            "Write pytest tests and improve coverage for the testing module"
        )

        assert analysis.domain == "testing"
        assert "tests" in analysis.required_components

    def test_analyze_task_general(self, engine):
        """Test analyzing general task."""
        analysis = engine.analyze_task("Fix a bug in the code")

        assert analysis.domain == "general"

    def test_analyze_task_extracts_constraints(self, engine):
        """Test that constraints are extracted."""
        analysis = engine.analyze_task(
            "Build a simple and secure API quickly"
        )

        assert "Keep implementation simple" in analysis.constraints
        assert "Must follow security best practices" in analysis.constraints

    def test_decompose_backend_task(self, engine):
        """Test decomposing backend task."""
        analysis = TaskAnalysis(
            original_request="Build API",
            goal="Build API",
            scope=["Backend"],
            required_components=["api", "database"],
            domain="backend",
        )

        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0
        assert plan.total_estimated_duration_mins > 0
        assert plan.dependency_layers >= 1

    def test_decompose_frontend_task(self, engine):
        """Test decomposing frontend task."""
        analysis = TaskAnalysis(
            original_request="Build UI",
            goal="Build UI",
            scope=["Frontend"],
            required_components=["ui_components"],
            domain="frontend",
        )

        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0

    def test_decompose_fullstack_task(self, engine):
        """Test decomposing full-stack task."""
        analysis = TaskAnalysis(
            original_request="Build full app",
            goal="Build full app",
            scope=["Full stack"],
            required_components=["api", "ui_components"],
            domain="full_stack",
        )

        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0

    def test_decompose_testing_task(self, engine):
        """Test decomposing testing task."""
        analysis = TaskAnalysis(
            original_request="Write tests",
            goal="Write tests",
            scope=["Testing"],
            required_components=["tests"],
            domain="testing",
        )

        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0

    def test_decompose_general_task(self, engine):
        """Test decomposing general task."""
        analysis = TaskAnalysis(
            original_request="Do something",
            goal="Do something",
            scope=["General"],
            required_components=["core"],
            domain="general",
        )

        plan = engine.decompose_task(analysis)

        assert len(plan.sub_tasks) > 0

    def test_generate_dependency_graph(self, engine):
        """Test generating dependency graph."""
        sub_tasks = [
            SubTask(
                task_id="t1",
                description="First task",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
            ),
            SubTask(
                task_id="t2",
                description="Second task",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["t1"],
            ),
        ]

        graph = engine.generate_dependency_graph(sub_tasks)

        assert graph.has_node("t1")
        assert graph.has_node("t2")
        assert graph.has_edge("t1", "t2")

    def test_generate_dependency_graph_warns_missing_dep(self, engine):
        """Test that missing dependencies are logged."""
        sub_tasks = [
            SubTask(
                task_id="t1",
                description="Task with missing dep",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["nonexistent"],  # Doesn't exist
            ),
        ]

        # Should not raise, just log warning
        graph = engine.generate_dependency_graph(sub_tasks)

        assert graph.has_node("t1")
        # Edge should not exist since dependency doesn't exist
        assert not graph.has_edge("nonexistent", "t1")

    def test_generate_dependency_graph_circular_dependency_raises(self, engine):
        """Test that circular dependencies raise error."""
        sub_tasks = [
            SubTask(
                task_id="t1",
                description="Task 1",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["t2"],  # Circular!
            ),
            SubTask(
                task_id="t2",
                description="Task 2",
                complexity=TaskComplexity.SIMPLE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=["t1"],  # Circular!
            ),
        ]

        with pytest.raises(ValueError, match="Circular dependencies"):
            engine.generate_dependency_graph(sub_tasks)

    def test_estimate_resources(self, engine):
        """Test resource estimation."""
        analysis = TaskAnalysis(
            original_request="Build API",
            goal="Build API",
            scope=["Backend"],
            required_components=["api"],
            domain="backend",
        )

        plan = engine.decompose_task(analysis)
        estimate = engine.estimate_resources(plan)

        assert estimate.total_agents_needed > 0
        assert estimate.estimated_total_cost_usd > 0
        assert estimate.estimated_tokens > 0
        assert estimate.peak_concurrent_agents >= 1

    def test_optimize_allocation(self, engine):
        """Test allocation optimization."""
        analysis = TaskAnalysis(
            original_request="Build API",
            goal="Build API",
            scope=["Backend"],
            required_components=["api", "database"],
            domain="backend",
        )

        decomp_plan = engine.decompose_task(analysis)
        allocation_plan = engine.optimize_allocation(decomp_plan)

        assert len(allocation_plan.allocations) == len(decomp_plan.sub_tasks)
        assert allocation_plan.total_phases >= 1
        assert len(allocation_plan.execution_phases) == allocation_plan.total_phases

    def test_generate_execution_schedule(self, engine):
        """Test execution schedule generation."""
        analysis = TaskAnalysis(
            original_request="Build API",
            goal="Build API",
            scope=["Backend"],
            required_components=["api"],
            domain="backend",
        )

        decomp_plan = engine.decompose_task(analysis)
        allocation_plan = engine.optimize_allocation(decomp_plan)
        schedule = engine.generate_execution_schedule(decomp_plan, allocation_plan)

        assert len(schedule.phases) > 0
        assert len(schedule.critical_path) > 0
        assert schedule.start_time is not None
        assert schedule.estimated_completion_time is not None


class TestInferDomain:
    """Test domain inference helper."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return TaskDecompositionEngine()

    def test_infer_backend_domain(self, engine):
        """Test inferring backend domain."""
        domain = engine._infer_domain("Build REST API endpoint with database service")
        assert domain == "backend"

    def test_infer_frontend_domain(self, engine):
        """Test inferring frontend domain."""
        domain = engine._infer_domain("Create React component with dashboard UI interface")
        assert domain == "frontend"

    def test_infer_testing_domain(self, engine):
        """Test inferring testing domain."""
        domain = engine._infer_domain("Write pytest tests for coverage")
        assert domain == "testing"

    def test_infer_general_domain(self, engine):
        """Test inferring general domain."""
        domain = engine._infer_domain("Fix a small bug")
        assert domain == "general"


class TestInferComplexity:
    """Test complexity inference helper."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return TaskDecompositionEngine()

    def test_infer_strategic_complexity(self, engine):
        """Test inferring strategic complexity."""
        complexity = engine._infer_complexity("Design system architecture")
        assert complexity == TaskComplexity.STRATEGIC

    def test_infer_creative_complexity(self, engine):
        """Test inferring creative complexity."""
        complexity = engine._infer_complexity("Implement new feature")
        assert complexity == TaskComplexity.CREATIVE

    def test_infer_simple_complexity(self, engine):
        """Test inferring simple complexity."""
        complexity = engine._infer_complexity("Fix typo")
        assert complexity == TaskComplexity.SIMPLE


class TestExtractComponents:
    """Test component extraction helper."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return TaskDecompositionEngine()

    def test_extract_auth_component(self, engine):
        """Test extracting authentication component."""
        components = engine._extract_components("Add login functionality", "backend")
        assert "authentication" in components

    def test_extract_database_component(self, engine):
        """Test extracting database component."""
        components = engine._extract_components("Create database models", "backend")
        assert "database" in components

    def test_extract_api_component(self, engine):
        """Test extracting API component."""
        components = engine._extract_components("Build API endpoints", "backend")
        assert "api" in components

    def test_extract_ui_component(self, engine):
        """Test extracting UI component."""
        components = engine._extract_components("Create UI interface", "frontend")
        assert "ui_components" in components

    def test_extract_test_component(self, engine):
        """Test extracting test component."""
        components = engine._extract_components("Write tests", "testing")
        assert "tests" in components

    def test_extract_default_component(self, engine):
        """Test default component extraction."""
        components = engine._extract_components("Do something", "general")
        assert "core" in components


class TestExtractScope:
    """Test scope extraction helper."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return TaskDecompositionEngine()

    def test_extract_backend_scope(self, engine):
        """Test extracting backend scope."""
        scope = engine._extract_scope("Build API", "backend", ["api"])
        assert "Backend implementation" in scope
        assert "REST API endpoints" in scope

    def test_extract_frontend_scope(self, engine):
        """Test extracting frontend scope."""
        scope = engine._extract_scope("Build UI", "frontend", ["ui_components"])
        assert "Frontend implementation" in scope
        assert "UI components and views" in scope

    def test_extract_fullstack_scope(self, engine):
        """Test extracting full-stack scope."""
        scope = engine._extract_scope("Build app", "full_stack", [])
        assert "Backend services" in scope
        assert "Frontend interface" in scope


class TestGenerateAssumptions:
    """Test assumptions generation helper."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return TaskDecompositionEngine()

    def test_generate_backend_assumptions(self, engine):
        """Test generating backend assumptions."""
        assumptions = engine._generate_assumptions("backend", ["database"])
        assert any("PostgreSQL" in a or "FastAPI" in a for a in assumptions)

    def test_generate_frontend_assumptions(self, engine):
        """Test generating frontend assumptions."""
        assumptions = engine._generate_assumptions("frontend", [])
        assert any("React" in a or "frontend" in a.lower() for a in assumptions)

    def test_common_assumptions_always_present(self, engine):
        """Test that common assumptions are always present."""
        assumptions = engine._generate_assumptions("general", [])
        assert any("patterns" in a.lower() for a in assumptions)
        assert any("test" in a.lower() for a in assumptions)


class TestExtractConstraints:
    """Test constraint extraction helper."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return TaskDecompositionEngine()

    def test_extract_simple_constraint(self, engine):
        """Test extracting simple constraint."""
        constraints = engine._extract_constraints("Keep it simple and quick")
        assert "Keep implementation simple" in constraints

    def test_extract_security_constraint(self, engine):
        """Test extracting security constraint."""
        constraints = engine._extract_constraints("Must be secure")
        assert "Must follow security best practices" in constraints

    def test_extract_performance_constraint(self, engine):
        """Test extracting performance constraint."""
        constraints = engine._extract_constraints("Needs high performance")
        assert "Performance-critical" in constraints

    def test_no_constraints(self, engine):
        """Test when no constraints found."""
        constraints = engine._extract_constraints("Build a feature")
        assert constraints == []


class TestAgentCostEstimates:
    """Test agent cost estimates."""

    def test_cost_estimates_defined(self):
        """Test that cost estimates are defined for all agent types."""
        engine = TaskDecompositionEngine()

        for agent_type in AgentType:
            assert agent_type in engine.AGENT_COST_ESTIMATES

    def test_cost_estimates_reasonable(self):
        """Test that cost estimates are in reasonable range."""
        engine = TaskDecompositionEngine()

        for agent_type, cost in engine.AGENT_COST_ESTIMATES.items():
            assert 0.0 < cost < 1.0  # Between 0 and $1 per execution
