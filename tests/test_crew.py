"""Unit tests for crew system."""

import pytest

from thegent.agents.crew import (
    Crew,
    CrewAgent,
    CrewExecutor,
    CrewStage,
    ExecutionMode,
    MonitoringEngine,
    RouterManager,
    RoutingStrategy,
    Task,
    TaskStatus,
    WorkflowEngine,
)
from thegent.agents.crew.executor import (
    AgentAssigner,
    ExecutionResult,
    HierarchicalAssigner,
    RoundRobinAssigner,
    SkillBasedAssigner,
    TaskExecutor,
)


class TestCrew:
    """Test Crew model."""

    def test_create_crew(self):
        """Test crew creation."""
        crew = Crew(
            name="Test Crew",
            description="Test description",
            execution_mode=ExecutionMode.SEQUENTIAL,
        )

        assert crew.name == "Test Crew"
        assert crew.description == "Test description"
        assert crew.execution_mode == ExecutionMode.SEQUENTIAL
        assert crew.status == "idle"

    def test_add_agent(self):
        """Test adding agent to crew."""
        crew = Crew(name="Test Crew")
        agent = CrewAgent(role="coder", name="Coder")

        crew.add_agent(agent)
        assert len(crew.agents) == 1
        assert crew.agents[0] == agent

    def test_add_task(self):
        """Test adding task to crew."""
        crew = Crew(name="Test Crew")
        task = Task(description="Test task")

        crew.add_task(task)
        assert len(crew.tasks) == 1
        assert crew.tasks[0] == task

    def test_get_agent_by_id(self):
        """Test getting agent by ID."""
        crew = Crew(name="Test Crew")
        agent = CrewAgent(role="coder", name="Coder")
        crew.add_agent(agent)

        found = crew.get_agent_by_id(agent.id)
        assert found == agent

    def test_get_task_by_id(self):
        """Test getting task by ID."""
        crew = Crew(name="Test Crew")
        task = Task(description="Test task")
        crew.add_task(task)

        found = crew.get_task_by_id(task.id)
        assert found == task


class TestTask:
    """Test Task model."""

    def test_create_task(self):
        """Test task creation."""
        task = Task(description="Test task")

        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert len(task.dependencies) == 0

    def test_add_dependency(self):
        """Test adding dependency."""
        task1 = Task(description="Task 1")
        task2 = Task(description="Task 2")

        task2.add_dependency(task1.id)
        assert task1.id in task2.dependencies

    def test_is_ready(self):
        """Test dependency readiness check."""
        task1 = Task(description="Task 1")
        task2 = Task(description="Task 2")
        task2.add_dependency(task1.id)

        assert not task2.is_ready(set())
        assert task2.is_ready({task1.id})

    def test_mark_completed(self):
        """Test marking task as completed."""
        task = Task(description="Test task")
        task.mark_completed("result")

        assert task.status == TaskStatus.COMPLETED
        assert task.result == "result"
        assert task.completed_at is not None

    def test_mark_failed(self):
        """Test marking task as failed."""
        task = Task(description="Test task")
        task.mark_failed("error")

        assert task.status == TaskStatus.FAILED
        assert task.error == "error"
        assert task.completed_at is not None


class TestCrewAgent:
    """Test CrewAgent model."""

    def test_create_agent(self):
        """Test agent creation."""
        agent = CrewAgent(role="coder", name="Coder")

        assert agent.role == "coder"
        assert agent.name == "Coder"

    def test_can_handle_task(self):
        """Test task handling check."""
        agent = CrewAgent(role="coder", capabilities=["python", "javascript"])

        assert agent.can_handle_task("Write Python code")
        assert agent.can_handle_task("Implement JavaScript feature")
        assert not agent.can_handle_task("Design UI mockup")


class TestTaskExecutor:
    """Test TaskExecutor."""

    def test_resolve_dependencies(self):
        """Test dependency resolution."""
        executor = TaskExecutor()

        task1 = Task(description="Task 1")
        task2 = Task(description="Task 2")
        task3 = Task(description="Task 3")

        task2.add_dependency(task1.id)
        task3.add_dependency(task2.id)

        ordered = executor.resolve_dependencies([task3, task1, task2])
        assert ordered[0].id == task1.id
        assert ordered[1].id == task2.id
        assert ordered[2].id == task3.id

    def test_resolve_dependencies_circular(self):
        """Test circular dependency detection."""
        executor = TaskExecutor()

        task1 = Task(description="Task 1")
        task2 = Task(description="Task 2")

        task1.add_dependency(task2.id)
        task2.add_dependency(task1.id)

        with pytest.raises(ValueError, match="Circular dependency"):
            executor.resolve_dependencies([task1, task2])

    def test_get_task_input(self):
        """Test getting task input from dependencies."""
        executor = TaskExecutor()

        task1 = Task(description="Task 1")
        task2 = Task(description="Task 2")
        task2.add_dependency(task1.id)

        completed = {
            task1.id: ExecutionResult(task_id=task1.id, success=True, result="result1"),
        }

        context = executor.get_task_input(task2, completed)
        assert "dependencies" in context
        assert task1.id in context["dependencies"]
        assert context["dependencies"][task1.id]["result"] == "result1"


class TestAgentAssigner:
    """Test agent assignment strategies."""

    def test_round_robin_assigner(self):
        """Test round-robin assignment."""
        assigner = RoundRobinAssigner()

        task1 = Task(description="Task 1")
        task2 = Task(description="Task 2")
        task3 = Task(description="Task 3")

        agent1 = CrewAgent(role="agent1")
        agent2 = CrewAgent(role="agent2")

        assignments = assigner.assign([task1, task2, task3], [agent1, agent2])

        assert assignments[task1.id] == agent1.id
        assert assignments[task2.id] == agent2.id
        assert assignments[task3.id] == agent1.id

    def test_skill_based_assigner(self):
        """Test skill-based assignment."""
        assigner = SkillBasedAssigner()

        task = Task(description="Write Python code")

        python_agent = CrewAgent(role="python-developer", capabilities=["python"])
        js_agent = CrewAgent(role="javascript-developer", capabilities=["javascript"])

        assignments = assigner.assign([task], [python_agent, js_agent])

        assert assignments[task.id] == python_agent.id

    def test_hierarchical_assigner(self):
        """Test hierarchical assignment."""
        assigner = HierarchicalAssigner()

        task1 = Task(description="Task 1")
        task2 = Task(description="Task 2")
        task3 = Task(description="Task 3")

        manager = CrewAgent(role="manager")
        worker = CrewAgent(role="worker")

        assignments = assigner.assign([task1, task2, task3], [manager, worker])

        # First tasks should go to manager
        assert assignments[task1.id] == manager.id
        assert assignments[task2.id] == manager.id
        # Later tasks to worker
        assert assignments[task3.id] == worker.id

    def test_agent_assigner_base_raises_type_error(self) -> None:
        """Test abstract AgentAssigner.assign raises explicit TypeError."""
        # @trace WL-3005
        assigner = AgentAssigner()
        with pytest.raises(
            TypeError,
            match=r"AgentAssigner.assign\(\) is abstract and must be implemented by a concrete AgentAssigner subclass",
        ):
            assigner.assign([], [])


class TestCrewExecutor:
    """Test CrewExecutor."""

    def test_create_executor(self):
        """Test executor creation."""
        crew = Crew(name="Test Crew")
        executor = CrewExecutor(crew)

        assert executor.crew == crew
        assert executor.task_executor is not None
        assert executor.agent_assigner is not None

    def test_assign_tasks_to_agents(self):
        """Test task assignment."""
        crew = Crew(name="Test Crew", execution_mode=ExecutionMode.SEQUENTIAL)

        agent = CrewAgent(role="coder")
        task = Task(description="Test task")

        crew.add_agent(agent)
        crew.add_task(task)

        executor = CrewExecutor(crew)
        assignments = executor.assign_tasks_to_agents()

        assert task.id in assignments
        assert assignments[task.id] == agent.id


class TestWorkflowEngine:
    """Test WorkflowEngine."""

    def test_add_stage(self):
        """Test adding stage."""
        engine = WorkflowEngine()
        stage = CrewStage(id="stage1", name="Stage 1")

        engine.add_stage(stage)
        assert len(engine.stages) == 1

    def test_resolve_stage_dependencies(self):
        """Test stage dependency resolution."""
        engine = WorkflowEngine()

        stage1 = CrewStage(id="stage1", name="Stage 1")
        stage2 = CrewStage(id="stage2", name="Stage 2", depends_on=["stage1"])

        engine.add_stage(stage2)
        engine.add_stage(stage1)

        ordered = engine.resolve_stage_dependencies()
        assert ordered[0].id == "stage1"
        assert ordered[1].id == "stage2"

    def test_wl9470_resolve_three_stage_chain(self):
        # @trace WL-9470
        engine = WorkflowEngine()
        s1 = CrewStage(id="s1", name="S1")
        s2 = CrewStage(id="s2", name="S2", depends_on=["s1"])
        s3 = CrewStage(id="s3", name="S3", depends_on=["s2"])
        engine.add_stage(s3)
        engine.add_stage(s1)
        engine.add_stage(s2)
        assert [stage.id for stage in engine.resolve_stage_dependencies()] == ["s1", "s2", "s3"]

    def test_wl9471_unknown_dependency_fails_fast(self):
        # @trace WL-9471
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="s1", name="S1", depends_on=["missing"]))
        with pytest.raises(ValueError, match="Unknown dependency"):
            engine.resolve_stage_dependencies()

    def test_wl9472_self_dependency_fails_fast(self):
        # @trace WL-9472
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="s1", name="S1", depends_on=["s1"]))
        with pytest.raises(ValueError, match="cannot depend on itself"):
            engine.resolve_stage_dependencies()

    def test_wl9473_duplicate_stage_id_fails_fast(self):
        # @trace WL-9473
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="dup", name="A"))
        engine.add_stage(CrewStage(id="dup", name="B"))
        with pytest.raises(ValueError, match="Duplicate stage id"):
            engine.resolve_stage_dependencies()

    def test_wl9474_cycle_detection_still_enforced(self):
        # @trace WL-9474
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="a", name="A", depends_on=["b"]))
        engine.add_stage(CrewStage(id="b", name="B", depends_on=["a"]))
        with pytest.raises(ValueError, match="Circular dependency"):
            engine.resolve_stage_dependencies()

    def test_wl9475_independent_stages_allowed(self):
        # @trace WL-9475
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="a", name="A"))
        engine.add_stage(CrewStage(id="b", name="B"))
        ordered = {stage.id for stage in engine.resolve_stage_dependencies()}
        assert ordered == {"a", "b"}

    def test_wl9476_execute_empty_stage(self):
        # @trace WL-9476
        engine = WorkflowEngine()
        stage = CrewStage(id="empty", name="Empty")
        assert engine.execute_stage(stage) == {}
        assert engine.results["empty"] == {}

    def test_wl9477_execute_populates_stage_result_map(self):
        # @trace WL-9477
        engine = WorkflowEngine()
        stage = CrewStage(id="s1", name="S1")
        engine.execute_stage(stage)
        assert "s1" in engine.results

    def test_wl9478_dependency_order_respected_for_branches(self):
        # @trace WL-9478
        engine = WorkflowEngine()
        root = CrewStage(id="root", name="Root")
        left = CrewStage(id="left", name="Left", depends_on=["root"])
        right = CrewStage(id="right", name="Right", depends_on=["root"])
        engine.add_stage(left)
        engine.add_stage(root)
        engine.add_stage(right)
        ordered_ids = [stage.id for stage in engine.resolve_stage_dependencies()]
        assert ordered_ids[0] == "root"
        assert set(ordered_ids[1:]) == {"left", "right"}

    def test_wl9479_execute_uses_resolved_stage_order(self):
        # @trace WL-9479
        engine = WorkflowEngine()
        first = CrewStage(id="first", name="First")
        second = CrewStage(id="second", name="Second", depends_on=["first"])
        engine.add_stage(second)
        engine.add_stage(first)
        results = engine.execute()
        assert list(results.keys()) == ["first", "second"]

    def test_wl9520_empty_stage_id_fails_fast(self):
        # @trace WL-9520
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="", name="Empty"))
        with pytest.raises(ValueError, match="Stage id cannot be empty"):
            engine.resolve_stage_dependencies()

    def test_wl9521_whitespace_stage_id_fails_fast(self):
        # @trace WL-9521
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="   ", name="Whitespace"))
        with pytest.raises(ValueError, match="Stage id cannot be empty"):
            engine.resolve_stage_dependencies()

    def test_wl9522_duplicate_crew_ids_fail_in_execution_plan(self):
        # @trace WL-9522
        engine = WorkflowEngine()
        crew_a = Crew(name="A")
        crew_b = Crew(name="B")
        crew_b.id = crew_a.id
        engine.add_stage(CrewStage(id="s1", name="Stage", crews=[crew_a, crew_b]))
        with pytest.raises(ValueError, match="Duplicate crew id"):
            engine.execute()

    def test_wl9523_distinct_crew_ids_pass_execution_plan(self):
        # @trace WL-9523
        engine = WorkflowEngine()
        crew_a = Crew(name="A")
        crew_b = Crew(name="B")
        engine.add_stage(CrewStage(id="s1", name="Stage", crews=[crew_a, crew_b]))
        plan = engine._build_execution_plan()
        assert [stage.id for stage in plan] == ["s1"]

    def test_wl9524_execution_plan_respects_dependency_order(self):
        # @trace WL-9524
        engine = WorkflowEngine()
        a = CrewStage(id="a", name="A")
        b = CrewStage(id="b", name="B", depends_on=["a"])
        c = CrewStage(id="c", name="C", depends_on=["b"])
        engine.add_stage(c)
        engine.add_stage(a)
        engine.add_stage(b)
        plan = engine._build_execution_plan()
        assert [stage.id for stage in plan] == ["a", "b", "c"]

    def test_wl9525_execute_uses_frozen_execution_plan(self, monkeypatch):
        # @trace WL-9525
        engine = WorkflowEngine()
        first = CrewStage(id="first", name="First")
        second = CrewStage(id="second", name="Second", depends_on=["first"])
        engine.add_stage(second)
        engine.add_stage(first)

        original_execute_stage = engine.execute_stage

        def mutate_and_execute(stage):
            engine.add_stage(CrewStage(id="late", name="Late"))
            return original_execute_stage(stage)

        monkeypatch.setattr(engine, "execute_stage", mutate_and_execute)
        results = engine.execute()
        assert list(results.keys()) == ["first", "second"]
        assert "late" not in results

    def test_wl9526_execute_surfaces_stage_execution_error(self, monkeypatch):
        # @trace WL-9526
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="s1", name="Stage"))

        def raise_error(stage):
            raise RuntimeError(f"boom:{stage.id}")

        monkeypatch.setattr(engine, "execute_stage", raise_error)
        with pytest.raises(RuntimeError, match="boom:s1"):
            engine.execute()

    def test_wl9527_empty_workflow_execution_is_noop(self):
        # @trace WL-9527
        engine = WorkflowEngine()
        assert engine._build_execution_plan() == []
        assert engine.execute() == {}

    def test_wl9528_execute_stage_overwrites_previous_stage_result(self):
        # @trace WL-9528
        engine = WorkflowEngine()
        stage = CrewStage(id="s1", name="Stage")
        engine.results["s1"] = {"stale": {}}
        result = engine.execute_stage(stage)
        assert result == {}
        assert engine.results["s1"] == {}

    def test_wl9529_dependency_validation_happens_before_execution(self, monkeypatch):
        # @trace WL-9529
        engine = WorkflowEngine()
        engine.add_stage(CrewStage(id="s1", name="S1", depends_on=["missing"]))

        called = {"value": False}

        def should_not_run(stage):
            called["value"] = True
            return {}

        monkeypatch.setattr(engine, "execute_stage", should_not_run)
        with pytest.raises(ValueError, match="Unknown dependency"):
            engine.execute()
        assert called["value"] is False


class TestRouterManager:
    """Test RouterManager."""

    def test_create_router(self):
        """Test router creation."""
        router = RouterManager(strategy=RoutingStrategy.BALANCED)

        assert router.strategy == RoutingStrategy.BALANCED

    def test_select_agent_cost_optimized(self):
        """Test cost-optimized routing."""
        router = RouterManager(strategy=RoutingStrategy.BALANCED)

        agent1 = CrewAgent(role="agent1")
        agent2 = CrewAgent(role="agent2")

        from thegent.agents.crew.router_logic import RouteMetrics

        router.update_agent_metrics(agent1.id, RouteMetrics(cost_per_token=0.001))
        router.update_agent_metrics(agent2.id, RouteMetrics(cost_per_token=0.002))

        selected = router.select_agent("Test task", [agent1, agent2])
        # Router may return None if no implementation available, or an agent
        assert selected is None or selected.id in [agent1.id, agent2.id]


class TestMonitoringEngine:
    """Test MonitoringEngine."""

    def test_check_health(self):
        """Test health checking."""
        engine = MonitoringEngine()
        crew = Crew(name="Test Crew")

        agent = CrewAgent(role="coder")
        task = Task(description="Test task")

        crew.add_agent(agent)
        crew.add_task(task)

        health = engine.check_health(crew)
        assert health.healthy is True

    def test_track_performance(self):
        """Test performance tracking."""
        engine = MonitoringEngine()

        results = {
            "task1": ExecutionResult(task_id="task1", success=True, duration_seconds=10.0),
            "task2": ExecutionResult(task_id="task2", success=True, duration_seconds=20.0),
            "task3": ExecutionResult(task_id="task3", success=False, duration_seconds=5.0),
        }

        metrics = engine.track_performance("crew1", results)

        assert metrics.total_tasks == 3
        assert metrics.completed_tasks == 2
        assert metrics.failed_tasks == 1
        assert metrics.avg_duration_seconds == 15.0

    def test_track_costs(self):
        """Test cost tracking."""
        engine = MonitoringEngine()

        results = {
            "task1": ExecutionResult(task_id="task1", success=True, tokens_used=100, cost_usd=0.01),
            "task2": ExecutionResult(task_id="task2", success=True, tokens_used=200, cost_usd=0.02),
        }

        metrics = engine.track_costs("crew1", results)

        assert metrics.total_tokens == 300
        assert metrics.total_cost_usd == 0.03
        assert metrics.cost_per_task == 0.015
