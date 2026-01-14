"""Smart Task Decomposition Engine.

Analyzes user requests, breaks them into optimal sub-tasks, generates dependency graphs,
estimates resources, and creates execution plans for agent orchestration.
"""
import logging
import re
import networkx as nx
from typing import List, Dict, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class TaskComplexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"           # < 30 mins, straightforward implementation
    CREATIVE = "creative"       # 30-60 mins, requires design decisions
    STRATEGIC = "strategic"     # 60+ mins, complex architecture/planning


class AgentType(str, Enum):
    """Types of agents available."""
    EXECUTIVE_DIRECTOR = "executive_director"
    DEVELOPMENT_MANAGER = "development_manager"
    SYSTEM_ARCHITECT = "system_architect"
    BACKEND_COORDINATOR = "backend_coordinator"
    FRONTEND_COORDINATOR = "frontend_coordinator"
    TEST_COORDINATOR = "test_coordinator"
    BACKEND_LEAD = "backend_lead"
    FRONTEND_LEAD = "frontend_lead"
    BACKEND_DEVELOPER = "backend_developer"
    FRONTEND_DEVELOPER = "frontend_developer"
    UNIT_TEST_LEAD = "unit_test_lead"
    INTEGRATION_TEST_LEAD = "integration_test_lead"
    TEST_WRITER = "test_writer"


# ============================================================================
# Pydantic Models
# ============================================================================

class SubTask(BaseModel):
    """A single decomposed sub-task."""
    model_config = ConfigDict(use_enum_values=True)

    task_id: str = Field(..., description="Unique task identifier")
    description: str = Field(..., description="What needs to be done")
    complexity: TaskComplexity = Field(..., description="Task complexity level")
    estimated_duration_mins: int = Field(..., description="Estimated time in minutes")
    required_agent_type: AgentType = Field(..., description="Which agent can handle this")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")
    required_tools: List[str] = Field(default_factory=list, description="Tools needed")
    inputs: List[str] = Field(default_factory=list, description="Required inputs")
    outputs: List[str] = Field(default_factory=list, description="Expected outputs")
    acceptance_criteria: List[str] = Field(default_factory=list, description="How to verify completion")
    priority: int = Field(default=5, description="Priority 1-10, higher = more important")
    parallelizable: bool = Field(default=False, description="Can run in parallel with other tasks")


class TaskAnalysis(BaseModel):
    """Analysis of the user's request."""
    original_request: str = Field(..., description="The user's original request")
    goal: str = Field(..., description="High-level goal to achieve")
    scope: List[str] = Field(..., description="What's included in scope")
    out_of_scope: List[str] = Field(default_factory=list, description="What's explicitly out of scope")
    constraints: List[str] = Field(default_factory=list, description="Constraints and limitations")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    required_components: List[str] = Field(..., description="Components that need to be built/modified")
    domain: str = Field(default="general", description="Domain (backend, frontend, testing, etc)")


class DecompositionPlan(BaseModel):
    """Complete task decomposition with dependency graph."""
    analysis: TaskAnalysis = Field(..., description="Task analysis")
    sub_tasks: List[SubTask] = Field(..., description="Decomposed sub-tasks")
    total_estimated_duration_mins: int = Field(..., description="Total estimated time")
    critical_path_duration_mins: int = Field(..., description="Critical path duration")
    parallelization_opportunities: int = Field(default=0, description="Number of parallel tasks")
    dependency_layers: int = Field(default=1, description="Number of dependency layers")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ResourceEstimate(BaseModel):
    """Resource requirements for execution."""
    total_agents_needed: int = Field(..., description="Total agents to spawn")
    agents_by_type: Dict[str, int] = Field(..., description="Agent count by type")
    estimated_total_cost_usd: float = Field(..., description="Estimated cost in USD")
    estimated_tokens: int = Field(..., description="Estimated token usage")
    peak_concurrent_agents: int = Field(..., description="Max agents running simultaneously")
    estimated_wall_clock_mins: int = Field(..., description="Wall clock time with parallelization")


class AgentAllocation(BaseModel):
    """Allocation of a task to an agent."""
    model_config = ConfigDict(use_enum_values=True)

    task_id: str
    agent_type: AgentType
    estimated_start: str
    estimated_duration_mins: int
    dependencies_satisfied: List[str] = Field(default_factory=list)


class AllocationPlan(BaseModel):
    """Plan for allocating tasks to agents."""
    allocations: List[AgentAllocation] = Field(..., description="Task-to-agent allocations")
    execution_phases: List[List[str]] = Field(..., description="Tasks grouped by parallel execution phases")
    total_phases: int = Field(..., description="Number of sequential phases")


class Schedule(BaseModel):
    """Execution schedule with timeline."""
    phases: List[Dict[str, Any]] = Field(..., description="Execution phases with timing")
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    estimated_completion_time: str = Field(..., description="Estimated completion timestamp")
    critical_path: List[str] = Field(..., description="Critical path task IDs")


# ============================================================================
# Task Decomposition Engine
# ============================================================================

class TaskDecompositionEngine:
    """
    Smart task decomposition engine that breaks down user requests into
    optimal sub-tasks with dependency graphs and resource estimates.
    """

    # Complexity heuristics (keywords that suggest complexity level)
    SIMPLE_KEYWORDS = {
        "add", "create simple", "basic", "update", "fix", "rename", "delete",
        "change", "modify", "simple", "quick"
    }

    CREATIVE_KEYWORDS = {
        "implement", "build", "design", "create", "develop", "integrate",
        "refactor", "optimize", "enhance"
    }

    STRATEGIC_KEYWORDS = {
        "architecture", "system", "framework", "complex", "comprehensive",
        "strategy", "plan", "migrate", "scale"
    }

    # Agent cost estimates (USD per execution based on model + complexity)
    AGENT_COST_ESTIMATES = {
        AgentType.EXECUTIVE_DIRECTOR: 0.05,      # Sonnet, strategic
        AgentType.DEVELOPMENT_MANAGER: 0.02,      # Haiku, coordination
        AgentType.SYSTEM_ARCHITECT: 0.03,         # Haiku, creative
        AgentType.BACKEND_COORDINATOR: 0.01,      # Haiku, simple
        AgentType.FRONTEND_COORDINATOR: 0.01,     # Haiku, simple
        AgentType.TEST_COORDINATOR: 0.01,         # Haiku, simple
        AgentType.BACKEND_LEAD: 0.02,             # Haiku, creative
        AgentType.FRONTEND_LEAD: 0.02,            # Haiku, creative
        AgentType.BACKEND_DEVELOPER: 0.015,       # Haiku, creative
        AgentType.FRONTEND_DEVELOPER: 0.015,      # Haiku, creative
        AgentType.UNIT_TEST_LEAD: 0.015,          # Haiku, creative
        AgentType.INTEGRATION_TEST_LEAD: 0.015,   # Haiku, creative
        AgentType.TEST_WRITER: 0.01,              # Haiku, simple
    }

    def __init__(self):
        """Initialize the decomposition engine."""
        self.logger = logging.getLogger(__name__)

    def analyze_task(self, user_request: str) -> TaskAnalysis:
        """
        Analyze the user's request to understand goals, scope, and components.

        Args:
            user_request: The user's original request

        Returns:
            TaskAnalysis with extracted information
        """
        self.logger.info(f"Analyzing task: {user_request[:100]}...")

        # Extract goal (first sentence or clause)
        goal = user_request.split('.')[0].strip()

        # Determine domain based on keywords
        domain = self._infer_domain(user_request)

        # Identify required components (simplified heuristic)
        components = self._extract_components(user_request, domain)

        # Extract scope
        scope = self._extract_scope(user_request, domain, components)

        # Make reasonable assumptions
        assumptions = self._generate_assumptions(domain, components)

        # Identify constraints
        constraints = self._extract_constraints(user_request)

        return TaskAnalysis(
            original_request=user_request,
            goal=goal,
            scope=scope,
            out_of_scope=[],  # Can be refined with user feedback
            constraints=constraints,
            assumptions=assumptions,
            required_components=components,
            domain=domain
        )

    def decompose_task(self, task_analysis: TaskAnalysis) -> DecompositionPlan:
        """
        Decompose analyzed task into optimal sub-tasks.

        Args:
            task_analysis: Analysis of the task

        Returns:
            DecompositionPlan with sub-tasks and dependency graph
        """
        self.logger.info(f"Decomposing task: {task_analysis.goal}")

        sub_tasks = []

        # Generate sub-tasks based on domain and components
        if task_analysis.domain == "backend":
            sub_tasks.extend(self._decompose_backend_task(task_analysis))
        elif task_analysis.domain == "frontend":
            sub_tasks.extend(self._decompose_frontend_task(task_analysis))
        elif task_analysis.domain == "full_stack":
            sub_tasks.extend(self._decompose_fullstack_task(task_analysis))
        elif task_analysis.domain == "testing":
            sub_tasks.extend(self._decompose_testing_task(task_analysis))
        else:
            sub_tasks.extend(self._decompose_general_task(task_analysis))

        # Build dependency graph to validate and optimize
        graph = self.generate_dependency_graph(sub_tasks)

        # Calculate metrics
        total_duration = sum(task.estimated_duration_mins for task in sub_tasks)
        critical_path_duration = self._calculate_critical_path_duration(graph, sub_tasks)
        parallelization_opps = self._count_parallelizable_tasks(graph, sub_tasks)
        dependency_layers = self._count_dependency_layers(graph)

        return DecompositionPlan(
            analysis=task_analysis,
            sub_tasks=sub_tasks,
            total_estimated_duration_mins=total_duration,
            critical_path_duration_mins=critical_path_duration,
            parallelization_opportunities=parallelization_opps,
            dependency_layers=dependency_layers
        )

    def generate_dependency_graph(self, sub_tasks: List[SubTask]) -> nx.DiGraph:
        """
        Generate directed acyclic graph (DAG) of task dependencies.

        Args:
            sub_tasks: List of sub-tasks

        Returns:
            NetworkX DiGraph representing dependencies
        """
        graph = nx.DiGraph()

        # Add nodes
        for task in sub_tasks:
            graph.add_node(
                task.task_id,
                task=task,
                duration=task.estimated_duration_mins,
                agent_type=task.required_agent_type
            )

        # Add edges for dependencies
        for task in sub_tasks:
            for dep_id in task.dependencies:
                if graph.has_node(dep_id):
                    graph.add_edge(dep_id, task.task_id)
                else:
                    self.logger.warning(f"Dependency {dep_id} not found for task {task.task_id}")

        # Validate DAG (no cycles)
        if not nx.is_directed_acyclic_graph(graph):
            self.logger.error("Dependency graph contains cycles!")
            cycles = list(nx.simple_cycles(graph))
            raise ValueError(f"Circular dependencies detected: {cycles}")

        return graph

    def estimate_resources(self, decomp_plan: DecompositionPlan) -> ResourceEstimate:
        """
        Estimate resources needed for execution.

        Args:
            decomp_plan: Decomposition plan

        Returns:
            ResourceEstimate with cost and agent requirements
        """
        # Count agents by type
        agents_by_type = {}
        total_cost = 0.0
        total_tokens = 0

        for task in decomp_plan.sub_tasks:
            agent_type = task.required_agent_type
            agents_by_type[agent_type] = agents_by_type.get(agent_type, 0) + 1

            # Estimate cost
            cost = self.AGENT_COST_ESTIMATES.get(agent_type, 0.02)
            total_cost += cost

            # Estimate tokens (rough: 1000 tokens per 10 mins of work)
            tokens = int((task.estimated_duration_mins / 10) * 1000)
            total_tokens += tokens

        # Calculate peak concurrent agents from dependency graph
        graph = self.generate_dependency_graph(decomp_plan.sub_tasks)
        peak_concurrent = self._calculate_peak_concurrent_agents(graph)

        # Wall clock time is critical path duration (parallelization considered)
        wall_clock_mins = decomp_plan.critical_path_duration_mins

        return ResourceEstimate(
            total_agents_needed=len(decomp_plan.sub_tasks),
            agents_by_type=agents_by_type,
            estimated_total_cost_usd=round(total_cost, 3),
            estimated_tokens=total_tokens,
            peak_concurrent_agents=peak_concurrent,
            estimated_wall_clock_mins=wall_clock_mins
        )

    def optimize_allocation(
        self,
        decomp_plan: DecompositionPlan,
        available_agents: Optional[Dict[AgentType, int]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> AllocationPlan:
        """
        Optimize task allocation to agents.

        Args:
            decomp_plan: Decomposition plan
            available_agents: Available agent counts (None = unlimited)
            constraints: Additional constraints (max_concurrent, budget, etc)

        Returns:
            AllocationPlan with optimized allocations
        """
        graph = self.generate_dependency_graph(decomp_plan.sub_tasks)

        # Topological sort to get execution order
        try:
            topo_order = list(nx.topological_sort(graph))
        except nx.NetworkXError as e:
            self.logger.error(f"Failed to create topological sort: {e}")
            raise ValueError("Cannot optimize allocation - invalid dependency graph")

        # Group tasks into parallel execution phases
        phases = self._create_execution_phases(graph, decomp_plan.sub_tasks)

        # Create allocations
        allocations = []
        current_time = datetime.now()

        for phase_idx, phase_tasks in enumerate(phases):
            for task_id in phase_tasks:
                task = next(t for t in decomp_plan.sub_tasks if t.task_id == task_id)

                allocation = AgentAllocation(
                    task_id=task_id,
                    agent_type=task.required_agent_type,
                    estimated_start=current_time.isoformat(),
                    estimated_duration_mins=task.estimated_duration_mins,
                    dependencies_satisfied=task.dependencies
                )
                allocations.append(allocation)

            # Move time forward by longest task in this phase
            if phase_tasks:
                max_duration = max(
                    next(t for t in decomp_plan.sub_tasks if t.task_id == tid).estimated_duration_mins
                    for tid in phase_tasks
                )
                current_time += timedelta(minutes=max_duration)

        return AllocationPlan(
            allocations=allocations,
            execution_phases=phases,
            total_phases=len(phases)
        )

    def generate_execution_schedule(
        self,
        decomp_plan: DecompositionPlan,
        allocation_plan: AllocationPlan
    ) -> Schedule:
        """
        Generate execution schedule with timeline.

        Args:
            decomp_plan: Decomposition plan
            allocation_plan: Allocation plan

        Returns:
            Schedule with phases and timeline
        """
        graph = self.generate_dependency_graph(decomp_plan.sub_tasks)

        # Find critical path
        critical_path = self._find_critical_path(graph, decomp_plan.sub_tasks)

        # Build phases with timing
        phases = []
        current_time = datetime.now()

        for phase_idx, phase_task_ids in enumerate(allocation_plan.execution_phases):
            phase_tasks = []
            max_duration = 0

            for task_id in phase_task_ids:
                task = next(t for t in decomp_plan.sub_tasks if t.task_id == task_id)
                allocation = next(a for a in allocation_plan.allocations if a.task_id == task_id)

                # Handle both enum and string values
                agent_type_value = task.required_agent_type
                if hasattr(agent_type_value, 'value'):
                    agent_type_value = agent_type_value.value

                phase_tasks.append({
                    "task_id": task_id,
                    "description": task.description,
                    "agent_type": agent_type_value,
                    "estimated_duration_mins": task.estimated_duration_mins,
                    "start_time": current_time.isoformat(),
                    "on_critical_path": task_id in critical_path
                })

                max_duration = max(max_duration, task.estimated_duration_mins)

            phases.append({
                "phase": phase_idx + 1,
                "tasks": phase_tasks,
                "parallel_tasks": len(phase_tasks),
                "duration_mins": max_duration,
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(minutes=max_duration)).isoformat()
            })

            current_time += timedelta(minutes=max_duration)

        return Schedule(
            phases=phases,
            start_time=datetime.now().isoformat(),
            estimated_completion_time=current_time.isoformat(),
            critical_path=critical_path
        )

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _infer_domain(self, request: str) -> str:
        """Infer domain from request text."""
        request_lower = request.lower()

        backend_keywords = {"api", "endpoint", "database", "server", "backend", "service", "postgresql", "mysql", "fastapi", "django", "flask"}
        frontend_keywords = {"ui", "component", "frontend", "react", "vue", "angular", "page", "dashboard", "interface"}
        testing_keywords = {"test", "testing", "pytest", "jest", "coverage"}

        backend_score = sum(1 for kw in backend_keywords if kw in request_lower)
        frontend_score = sum(1 for kw in frontend_keywords if kw in request_lower)
        testing_score = sum(1 for kw in testing_keywords if kw in request_lower)

        # Require significant presence of both for full_stack (at least 2 keywords each)
        if backend_score >= 2 and frontend_score >= 2:
            return "full_stack"
        elif backend_score > frontend_score and backend_score > testing_score:
            return "backend"
        elif frontend_score > backend_score and frontend_score > testing_score:
            return "frontend"
        elif testing_score > backend_score and testing_score > frontend_score:
            return "testing"
        else:
            return "general"

    def _extract_components(self, request: str, domain: str) -> List[str]:
        """Extract components mentioned in request."""
        components = []
        request_lower = request.lower()

        # Common component patterns
        if "auth" in request_lower or "login" in request_lower:
            components.append("authentication")
        if "database" in request_lower or "model" in request_lower:
            components.append("database")
        if "api" in request_lower or "endpoint" in request_lower:
            components.append("api")
        if "ui" in request_lower or "interface" in request_lower or "component" in request_lower:
            components.append("ui_components")
        if "test" in request_lower:
            components.append("tests")

        return components if components else ["core"]

    def _extract_scope(self, request: str, domain: str, components: List[str]) -> List[str]:
        """Extract scope items."""
        scope = []

        # Domain-specific scope
        if domain == "backend":
            scope.append("Backend implementation")
            if "api" in components:
                scope.append("REST API endpoints")
            if "database" in components:
                scope.append("Database models and migrations")
        elif domain == "frontend":
            scope.append("Frontend implementation")
            if "ui_components" in components:
                scope.append("UI components and views")
        elif domain == "full_stack":
            scope.extend(["Backend services", "Frontend interface", "Integration"])

        # Testing scope
        if "tests" in components or "test" in request.lower():
            scope.append("Unit and integration tests")

        return scope if scope else ["Implementation of requested feature"]

    def _generate_assumptions(self, domain: str, components: List[str]) -> List[str]:
        """Generate reasonable assumptions."""
        assumptions = []

        if domain == "backend" or domain == "full_stack":
            assumptions.append("Using existing backend framework (FastAPI/Express)")
            if "database" in components:
                assumptions.append("PostgreSQL with ORM (SQLAlchemy/Prisma)")
            if "authentication" in components:
                assumptions.append("JWT-based authentication")

        if domain == "frontend" or domain == "full_stack":
            assumptions.append("Using existing frontend framework (React/Vue)")

        assumptions.append("Code follows existing project patterns")
        assumptions.append("Tests should be written alongside implementation")

        return assumptions

    def _extract_constraints(self, request: str) -> List[str]:
        """Extract constraints from request."""
        constraints = []
        request_lower = request.lower()

        if "quick" in request_lower or "simple" in request_lower:
            constraints.append("Keep implementation simple")
        if "secure" in request_lower or "security" in request_lower:
            constraints.append("Must follow security best practices")
        if "performan" in request_lower:  # performance/performant
            constraints.append("Performance-critical")

        return constraints

    def _infer_complexity(self, description: str) -> TaskComplexity:
        """Infer task complexity from description."""
        desc_lower = description.lower()

        # Check for strategic keywords first
        if any(kw in desc_lower for kw in self.STRATEGIC_KEYWORDS):
            return TaskComplexity.STRATEGIC

        # Then creative
        if any(kw in desc_lower for kw in self.CREATIVE_KEYWORDS):
            return TaskComplexity.CREATIVE

        # Default to simple
        return TaskComplexity.SIMPLE

    def _decompose_backend_task(self, analysis: TaskAnalysis) -> List[SubTask]:
        """Decompose backend task."""
        tasks = []
        task_counter = 1

        # Architecture/planning (if strategic)
        if any("architecture" in comp or "system" in comp for comp in analysis.required_components):
            tasks.append(SubTask(
                task_id=f"task_{task_counter}",
                description="Design backend architecture and data models",
                complexity=TaskComplexity.STRATEGIC,
                estimated_duration_mins=45,
                required_agent_type=AgentType.SYSTEM_ARCHITECT,
                outputs=["architecture_doc.md"],
                acceptance_criteria=["Architecture document created", "Data models defined"]
            ))
            task_counter += 1

        # Database models
        if "database" in analysis.required_components:
            tasks.append(SubTask(
                task_id=f"task_{task_counter}",
                description="Create database models and migrations",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=[tasks[-1].task_id] if tasks else [],
                required_tools=["write_file", "run_command"],
                outputs=["models.py", "migrations/"],
                acceptance_criteria=["Models created", "Migrations generated", "Tests pass"]
            ))
            task_counter += 1

        # API endpoints
        if "api" in analysis.required_components:
            tasks.append(SubTask(
                task_id=f"task_{task_counter}",
                description="Implement API endpoints with validation",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=40,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=[tasks[-1].task_id] if tasks else [],
                required_tools=["write_file", "run_command"],
                outputs=["routes.py", "schemas.py"],
                acceptance_criteria=["Endpoints implemented", "Validation added", "API tests pass"]
            ))
            task_counter += 1

        # Authentication
        if "authentication" in analysis.required_components:
            tasks.append(SubTask(
                task_id=f"task_{task_counter}",
                description="Implement authentication with JWT",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=35,
                required_agent_type=AgentType.BACKEND_DEVELOPER,
                dependencies=[t.task_id for t in tasks if "database" in t.description.lower()],
                required_tools=["write_file"],
                outputs=["auth.py", "middleware/auth.py"],
                acceptance_criteria=["JWT auth working", "Token validation implemented", "Auth tests pass"]
            ))
            task_counter += 1

        # Tests
        if "tests" in analysis.required_components or len(tasks) > 0:
            tasks.append(SubTask(
                task_id=f"task_{task_counter}",
                description="Write comprehensive backend tests",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=25,
                required_agent_type=AgentType.TEST_WRITER,
                dependencies=[t.task_id for t in tasks],
                required_tools=["write_file", "run_command"],
                outputs=["tests/test_backend.py"],
                acceptance_criteria=["Tests written", "Coverage > 80%", "All tests pass"]
            ))
            task_counter += 1

        return tasks

    def _decompose_frontend_task(self, analysis: TaskAnalysis) -> List[SubTask]:
        """Decompose frontend task."""
        tasks = []
        task_counter = 1

        # UI components
        if "ui_components" in analysis.required_components:
            tasks.append(SubTask(
                task_id=f"task_{task_counter}",
                description="Create UI components with styling",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=35,
                required_agent_type=AgentType.FRONTEND_DEVELOPER,
                required_tools=["write_file"],
                outputs=["components/*.jsx"],
                acceptance_criteria=["Components created", "Styled appropriately", "Props validated"]
            ))
            task_counter += 1

        # State management
        tasks.append(SubTask(
            task_id=f"task_{task_counter}",
            description="Implement state management and data flow",
            complexity=TaskComplexity.CREATIVE,
            estimated_duration_mins=30,
            required_agent_type=AgentType.FRONTEND_DEVELOPER,
            dependencies=[tasks[-1].task_id] if tasks else [],
            required_tools=["write_file"],
            outputs=["hooks/", "context/"],
            acceptance_criteria=["State management working", "Data flow correct"]
        ))
        task_counter += 1

        # API integration
        if "api" in analysis.required_components:
            tasks.append(SubTask(
                task_id=f"task_{task_counter}",
                description="Integrate with backend API",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=25,
                required_agent_type=AgentType.FRONTEND_DEVELOPER,
                dependencies=[t.task_id for t in tasks],
                required_tools=["write_file"],
                outputs=["api/client.js"],
                acceptance_criteria=["API calls working", "Error handling implemented"]
            ))
            task_counter += 1

        # Tests
        tasks.append(SubTask(
            task_id=f"task_{task_counter}",
            description="Write frontend component tests",
            complexity=TaskComplexity.CREATIVE,
            estimated_duration_mins=20,
            required_agent_type=AgentType.TEST_WRITER,
            dependencies=[t.task_id for t in tasks],
            required_tools=["write_file", "run_command"],
            outputs=["tests/components.test.jsx"],
            acceptance_criteria=["Component tests written", "Tests pass"]
        ))

        return tasks

    def _decompose_fullstack_task(self, analysis: TaskAnalysis) -> List[SubTask]:
        """Decompose full-stack task."""
        # Combine backend and frontend decomposition
        backend_analysis = TaskAnalysis(
            original_request=analysis.original_request,
            goal=analysis.goal + " (backend)",
            scope=[s for s in analysis.scope if "backend" in s.lower() or "api" in s.lower()],
            required_components=[c for c in analysis.required_components if c in ["database", "api", "authentication"]],
            domain="backend"
        )

        frontend_analysis = TaskAnalysis(
            original_request=analysis.original_request,
            goal=analysis.goal + " (frontend)",
            scope=[s for s in analysis.scope if "frontend" in s.lower() or "ui" in s.lower()],
            required_components=[c for c in analysis.required_components if c in ["ui_components", "api"]],
            domain="frontend"
        )

        backend_tasks = self._decompose_backend_task(backend_analysis)
        frontend_tasks = self._decompose_frontend_task(frontend_analysis)

        # Renumber frontend tasks
        next_id = len(backend_tasks) + 1
        for task in frontend_tasks:
            old_id = task.task_id
            new_id = f"task_{next_id}"
            task.task_id = new_id
            next_id += 1

            # Update dependencies to point to backend API task if needed
            if "api" in task.description.lower() and backend_tasks:
                api_task = next((t for t in backend_tasks if "api" in t.description.lower()), None)
                if api_task:
                    task.dependencies.append(api_task.task_id)

        return backend_tasks + frontend_tasks

    def _decompose_testing_task(self, analysis: TaskAnalysis) -> List[SubTask]:
        """Decompose testing task."""
        return [
            SubTask(
                task_id="task_1",
                description="Write unit tests with coverage",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=30,
                required_agent_type=AgentType.TEST_WRITER,
                required_tools=["write_file", "run_command"],
                outputs=["tests/unit/"],
                acceptance_criteria=["Unit tests written", "Coverage > 80%", "Tests pass"]
            ),
            SubTask(
                task_id="task_2",
                description="Write integration tests",
                complexity=TaskComplexity.CREATIVE,
                estimated_duration_mins=35,
                required_agent_type=AgentType.INTEGRATION_TEST_LEAD,
                dependencies=["task_1"],
                required_tools=["write_file", "run_command"],
                outputs=["tests/integration/"],
                acceptance_criteria=["Integration tests written", "Tests pass"]
            )
        ]

    def _decompose_general_task(self, analysis: TaskAnalysis) -> List[SubTask]:
        """Decompose general/unknown task."""
        complexity = self._infer_complexity(analysis.goal)

        return [
            SubTask(
                task_id="task_1",
                description=analysis.goal,
                complexity=complexity,
                estimated_duration_mins=40 if complexity == TaskComplexity.STRATEGIC else 30,
                required_agent_type=AgentType.BACKEND_DEVELOPER,  # Default
                required_tools=["write_file"],
                outputs=["implementation"],
                acceptance_criteria=["Feature implemented", "Tests pass"]
            )
        ]

    def _calculate_critical_path_duration(self, graph: nx.DiGraph, tasks: List[SubTask]) -> int:
        """Calculate critical path duration through the dependency graph."""
        if not graph.nodes():
            return 0

        # Find longest path (critical path)
        try:
            longest_path = nx.dag_longest_path(graph, weight='duration')
            duration = nx.dag_longest_path_length(graph, weight='duration')
            return int(duration)
        except Exception as e:
            self.logger.warning(f"Could not calculate critical path: {e}")
            # Fallback: sum of all tasks (no parallelization)
            return sum(task.estimated_duration_mins for task in tasks)

    def _count_parallelizable_tasks(self, graph: nx.DiGraph, tasks: List[SubTask]) -> int:
        """Count tasks that can run in parallel."""
        # Tasks with no dependencies or same dependencies can run in parallel
        dep_groups = {}
        for task in tasks:
            dep_key = tuple(sorted(task.dependencies))
            if dep_key not in dep_groups:
                dep_groups[dep_key] = []
            dep_groups[dep_key].append(task.task_id)

        # Count groups with more than 1 task (parallelizable)
        parallel_count = sum(len(group) for group in dep_groups.values() if len(group) > 1)
        return parallel_count

    def _count_dependency_layers(self, graph: nx.DiGraph) -> int:
        """Count the number of dependency layers (longest path)."""
        if not graph.nodes():
            return 0

        try:
            return len(nx.dag_longest_path(graph))
        except Exception:
            return 1

    def _calculate_peak_concurrent_agents(self, graph: nx.DiGraph) -> int:
        """Calculate peak concurrent agents needed."""
        if not graph.nodes():
            return 0

        # Group tasks by execution level (topological generations)
        levels = list(nx.topological_generations(graph))
        max_concurrent = max(len(level) for level in levels) if levels else 1
        return max_concurrent

    def _create_execution_phases(self, graph: nx.DiGraph, tasks: List[SubTask]) -> List[List[str]]:
        """Create phases of tasks that can execute in parallel."""
        phases = []

        try:
            # Use topological generations to get parallel execution groups
            for generation in nx.topological_generations(graph):
                phases.append(list(generation))
        except Exception as e:
            self.logger.warning(f"Could not create execution phases: {e}")
            # Fallback: all tasks in sequence
            phases = [[task.task_id] for task in tasks]

        return phases

    def _find_critical_path(self, graph: nx.DiGraph, tasks: List[SubTask]) -> List[str]:
        """Find the critical path (longest path) through the graph."""
        try:
            return list(nx.dag_longest_path(graph, weight='duration'))
        except Exception as e:
            self.logger.warning(f"Could not find critical path: {e}")
            return [task.task_id for task in tasks]
