"""Unit tests for MCP REST endpoints for tray integration."""


import pytest

from thegent.mcp_server import http_app


@pytest.fixture
def mock_app():
    """Create a mock ASGI app for testing."""
    app = http_app(stateless_http=True)
    return app


def get_client(mock_app):
    """Get a synchronous test client."""
    from starlette.testclient import TestClient

    return TestClient(mock_app)


@pytest.mark.unit
class TestProjectsEndpoints:
    """Tests for Projects REST endpoints."""

    def test_list_projects_returns_json(self, mock_app):
        """GET /api/v1/projects returns JSON array."""
        client = get_client(mock_app)
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_returns_mock_projects(self, mock_app):
        """GET /api/v1/projects returns mock project data."""
        client = get_client(mock_app)
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        # Should have at least mock data
        assert isinstance(data, list)

    def test_create_project(self, mock_app):
        """POST /api/v1/projects creates a project."""
        client = get_client(mock_app)
        response = client.post(
            "/api/v1/projects",
            json={"name": "test-project", "path": "/test/path", "language": "python"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "test-project"

    def test_get_project(self, mock_app):
        """GET /api/v1/projects/{project_id} returns a project."""
        client = get_client(mock_app)
        response = client.get("/api/v1/projects/test-project-1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data

    def test_update_project(self, mock_app):
        """PUT /api/v1/projects/{project_id} updates a project."""
        client = get_client(mock_app)
        response = client.put(
            "/api/v1/projects/test-project-1",
            json={"name": "updated-name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-name"

    def test_delete_project(self, mock_app):
        """DELETE /api/v1/projects/{project_id} deletes a project."""
        client = get_client(mock_app)
        response = client.delete("/api/v1/projects/test-project-1")
        assert response.status_code in {204, 200}


@pytest.mark.unit
class TestAgentsEndpoints:
    """Tests for Agents REST endpoints."""

    def test_list_agents(self, mock_app):
        """GET /api/v1/agents returns JSON array."""
        client = get_client(mock_app)
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_agent(self, mock_app):
        """GET /api/v1/agents/{agent_id} returns an agent."""
        client = get_client(mock_app)
        response = client.get("/api/v1/agents/claude")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data

    def test_update_agent(self, mock_app):
        """PUT /api/v1/agents/{agent_id} updates an agent."""
        client = get_client(mock_app)
        response = client.put(
            "/api/v1/agents/claude",
            json={"model": "claude-sonnet-4-20250514"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data


@pytest.mark.unit
class TestRunsEndpoints:
    """Tests for Runs REST endpoints."""

    def test_list_runs(self, mock_app):
        """GET /api/v1/runs returns JSON array."""
        client = get_client(mock_app)
        response = client.get("/api/v1/runs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_runs_with_filters(self, mock_app):
        """GET /api/v1/runs accepts query parameters."""
        client = get_client(mock_app)
        response = client.get("/api/v1/runs?project_id=test&status=running")
        assert response.status_code == 200

    def test_get_run(self, mock_app):
        """GET /api/v1/runs/{run_id} returns a run."""
        client = get_client(mock_app)
        response = client.get("/api/v1/runs/run-001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data


@pytest.mark.unit
class TestGardenerEndpoints:
    """Tests for Gardener REST endpoints."""

    def test_gardener_status(self, mock_app):
        """GET /api/v1/gardener/status returns gardener status."""
        client = get_client(mock_app)
        response = client.get("/api/v1/gardener/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "active_agents" in data

    def test_start_gardener(self, mock_app):
        """POST /api/v1/gardener/start starts the gardener."""
        client = get_client(mock_app)
        response = client.post("/api/v1/gardener/start")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data

    def test_stop_gardener(self, mock_app):
        """POST /api/v1/gardener/stop stops the gardener."""
        client = get_client(mock_app)
        response = client.post("/api/v1/gardener/stop")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data

    def test_scan_gardener(self, mock_app):
        """POST /api/v1/gardener/scan triggers a scan."""
        client = get_client(mock_app)
        response = client.post("/api/v1/gardener/scan")
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data or "status" in data

    def test_get_gardener_config(self, mock_app):
        """GET /api/v1/gardener/config returns gardener config."""
        client = get_client(mock_app)
        response = client.get("/api/v1/gardener/config")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_update_gardener_config(self, mock_app):
        """PUT /api/v1/gardener/config updates gardener config."""
        client = get_client(mock_app)
        response = client.put(
            "/api/v1/gardener/config",
            json={"max_agents": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.unit
class TestCostsEndpoints:
    """Tests for Costs REST endpoints."""

    def test_daily_cost(self, mock_app):
        """GET /api/v1/costs/daily returns daily cost summary."""
        client = get_client(mock_app)
        response = client.get("/api/v1/costs/daily")
        assert response.status_code == 200
        data = response.json()
        assert "daily_spend" in data
        assert "daily_budget" in data

    def test_monthly_cost(self, mock_app):
        """GET /api/v1/costs/monthly returns monthly cost summary."""
        client = get_client(mock_app)
        response = client.get("/api/v1/costs/monthly")
        assert response.status_code == 200
        data = response.json()
        assert "monthly_spend" in data
        assert "monthly_budget" in data

    def test_get_cost_alerts(self, mock_app):
        """GET /api/v1/costs/alerts returns cost alerts."""
        client = get_client(mock_app)
        response = client.get("/api/v1/costs/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_cost_alert(self, mock_app):
        """POST /api/v1/costs/alerts creates a cost alert."""
        client = get_client(mock_app)
        response = client.post(
            "/api/v1/costs/alerts",
            json={"threshold": 100.0, "message": "Budget exceeded"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data or "threshold" in data


@pytest.mark.unit
class TestGamificationEndpoints:
    """Tests for Gamification REST endpoints."""

    def test_gamification_stats(self, mock_app):
        """GET /api/v1/gamification/stats returns gamification stats."""
        client = get_client(mock_app)
        response = client.get("/api/v1/gamification/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_xp" in data
        assert "level" in data

    def test_achievements(self, mock_app):
        """GET /api/v1/gamification/achievements returns achievements."""
        client = get_client(mock_app)
        response = client.get("/api/v1/gamification/achievements")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
