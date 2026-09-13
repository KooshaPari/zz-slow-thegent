"""Unit tests for thegent API client."""

import pytest

pytest.importorskip("PySide6")


from thegent.tray.plugins.thegent.api_client import (
    Agent,
    CostSummary,
    GamificationStats,
    GardenerStatus,
    Project,
    Run,
    ThegentAPIClient,
)


@pytest.mark.unit
class TestThegentAPIClientInit:
    """Tests for ThegentAPIClient initialization."""

    def test_default_host_port(self) -> None:
        """Default host is 127.0.0.1 and port is 3847."""
        client = ThegentAPIClient()
        assert client._host == "127.0.0.1"
        assert client._port == 3847

    def test_custom_host_port(self) -> None:
        """Custom host and port are set correctly."""
        client = ThegentAPIClient(host="192.168.1.100", port=9999)
        assert client._host == "192.168.1.100"
        assert client._port == 9999


@pytest.mark.unit
class TestThegentAPIClientUrl:
    """Tests for _get_url method."""

    def test_get_url_default_port(self) -> None:
        """_get_url formats URL correctly with default port."""
        client = ThegentAPIClient()
        url = client._get_url("/api/projects")
        assert url == "http://127.0.0.1:3847/api/projects"

    def test_get_url_custom_port(self) -> None:
        """_get_url formats URL correctly with custom port."""
        client = ThegentAPIClient(host="0.0.0.0", port=8080)
        url = client._get_url("/api/agents")
        assert url == "http://0.0.0.0:8080/api/agents"

    def test_get_url_trailing_slash(self) -> None:
        """_get_url handles paths with trailing slash."""
        client = ThegentAPIClient()
        url = client._get_url("/api/projects/")
        assert url == "http://127.0.0.1:3847/api/projects/"


@pytest.mark.unit
class TestProjectDataclass:
    """Tests for Project dataclass."""

    def test_project_creation(self) -> None:
        """Project dataclass can be created with required fields."""
        project = Project(
            id="proj-001",
            name="Test Project",
            path="/path/to/project",
            language="python",
            coverage=85.5,
            last_run="2026-02-15T10:00:00Z",
        )
        assert project.id == "proj-001"
        assert project.name == "Test Project"
        assert project.path == "/path/to/project"
        assert project.language == "python"
        assert project.coverage == 85.5
        assert project.last_run == "2026-02-15T10:00:00Z"


@pytest.mark.unit
class TestAgentDataclass:
    """Tests for Agent dataclass."""

    def test_agent_creation(self) -> None:
        """Agent dataclass can be created with required fields."""
        agent = Agent(
            id="agent-001",
            name="Test Agent",
            model="claude-opus-4-6",
            context_limit=200000,
            rate_input=15.0,
            rate_output=75.0,
            status="active",
            bounded_contexts=[],
        )
        assert agent.id == "agent-001"
        assert agent.name == "Test Agent"
        assert agent.model == "claude-opus-4-6"
        assert agent.context_limit == 200000
        assert agent.rate_input == 15.0
        assert agent.rate_output == 75.0
        assert agent.status == "active"
        assert agent.bounded_contexts == []

    def test_agent_with_bounded_contexts(self) -> None:
        """Agent can have bounded contexts."""
        agent = Agent(
            id="agent-002",
            name="Code Agent",
            model="claude-sonnet-4-20250514",
            context_limit=150000,
            rate_input=10.0,
            rate_output=50.0,
            status="active",
            bounded_contexts=["code", "review"],
        )
        assert len(agent.bounded_contexts) == 2
        assert "code" in agent.bounded_contexts


@pytest.mark.unit
class TestRunDataclass:
    """Tests for Run dataclass."""

    def test_run_creation(self) -> None:
        """Run dataclass can be created with required fields."""
        run = Run(
            id="run-001",
            project_id="proj-001",
            agent_id="agent-001",
            status="completed",
            duration=120.5,
            cost=0.50,
            xp=100,
            started_at="2026-02-15T10:00:00Z",
            ended_at="2026-02-15T10:02:00Z",
        )
        assert run.id == "run-001"
        assert run.project_id == "proj-001"
        assert run.agent_id == "agent-001"
        assert run.status == "completed"
        assert run.duration == 120.5
        assert run.cost == 0.50
        assert run.xp == 100


@pytest.mark.unit
class TestGardenerStatusDataclass:
    """Tests for GardenerStatus dataclass."""

    def test_gardener_status_creation(self) -> None:
        """GardenerStatus dataclass can be created."""
        status = GardenerStatus(
            running=True,
            active_agents=3,
            max_agents=5,
            uptime_seconds=3600,
            runs_today=15,
            total_xp=5000,
            level=10,
            hunger_states={"agent-001": 0.2, "agent-002": 0.5},
        )
        assert status.running is True
        assert status.active_agents == 3
        assert status.max_agents == 5
        assert status.uptime_seconds == 3600
        assert status.runs_today == 15
        assert status.total_xp == 5000
        assert status.level == 10
        assert len(status.hunger_states) == 2


@pytest.mark.unit
class TestCostSummaryDataclass:
    """Tests for CostSummary dataclass."""

    def test_cost_summary_creation(self) -> None:
        """CostSummary dataclass can be created."""
        cost = CostSummary(
            daily_spend=10.50,
            daily_budget=100.0,
            daily_percent=10.5,
            monthly_spend=250.0,
            monthly_budget=1000.0,
            by_project={},
            by_agent={},
        )
        assert cost.daily_spend == 10.50
        assert cost.daily_budget == 100.0
        assert cost.daily_percent == 10.5
        assert cost.monthly_spend == 250.0
        assert cost.monthly_budget == 1000.0


@pytest.mark.unit
class TestGamificationStatsDataclass:
    """Tests for GamificationStats dataclass."""

    def test_gamification_stats_creation(self) -> None:
        """GamificationStats dataclass can be created."""
        stats = GamificationStats(
            total_xp=5000,
            level=10,
            xp_to_next_level=1000,
            runs_today=15,
            achievements_count=25,
            streak_days=7,
        )
        assert stats.total_xp == 5000
        assert stats.level == 10
        assert stats.xp_to_next_level == 1000
        assert stats.runs_today == 15
        assert stats.achievements_count == 25
        assert stats.streak_days == 7
