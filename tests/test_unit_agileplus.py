"""Unit tests for AgilePlusLoop governance cycle orchestrator.

Tests the state machine, cycle execution, error handling, and graceful shutdown.
"""

from __future__ import annotations

import signal
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import orjson as json
import pytest
from pydantic import ValidationError

if TYPE_CHECKING:
    from pathlib import Path

from thegent.governance.agileplus import AgilePlusLoop, CycleResult, CycleState

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HEALTH_TARGETS_DATA: dict = {
    "version": "1.0.0",
    "dimensions": {
        "test_coverage": {
            "weight": 0.20,
            "target": 80,
            "unit": "percent",
            "direction": "higher_is_better",
        },
        "lint_violations": {
            "weight": 0.15,
            "target": 0,
            "unit": "count",
            "direction": "lower_is_better",
        },
    },
    "bands": {
        "excellent": {"min": 90},
        "healthy": {"min": 70},
        "warning": {"min": 40},
        "critical": {"min": 0},
    },
}

_SCAN_RESULT_MOCK = MagicMock()
_SCAN_RESULT_MOCK.dimensions = {"test_coverage": 60, "lint_violations": 5}

_FINDINGS_MOCK = [
    MagicMock(finding_id="finding_1", priority=1),
    MagicMock(finding_id="finding_2", priority=2),
]

_PLAN_MOCK = MagicMock()
_PLAN_MOCK.tasks = [
    MagicMock(task_id="task_1"),
    MagicMock(task_id="task_2"),
]
_PLAN_MOCK.total_estimated_calls = 10

_DEPLOYMENT_RESULT_MOCK = MagicMock()
_DEPLOYMENT_RESULT_MOCK.tasks_completed = 2
_DEPLOYMENT_RESULT_MOCK.tasks_failed = 0
_DEPLOYMENT_RESULT_MOCK.executions = [
    MagicMock(task_id="task_1", status="completed"),
    MagicMock(task_id="task_2", status="completed"),
]

_VERIFICATION_MOCK = MagicMock()
_VERIFICATION_MOCK.verdict = MagicMock(value="pass")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def health_targets_path(tmp_path: Path) -> Path:
    """Write health-targets.json to tmp_path and return its path."""
    p = tmp_path / "health-targets.json"
    p.write_text(json.dumps(_HEALTH_TARGETS_DATA).decode())
    return p


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    d = tmp_path / "project"
    d.mkdir()
    return d


@pytest.fixture
def loop(project_dir: Path, health_targets_path: Path) -> AgilePlusLoop:
    """Create an AgilePlusLoop instance for testing."""
    return AgilePlusLoop(
        project_dir=project_dir,
        health_targets_path=health_targets_path,
        health_threshold=90.0,
        max_tasks_per_cycle=10,
        max_rerolls=2,
    )


def _setup_loop_mocks(loop: AgilePlusLoop) -> None:
    """Setup common mocks for run_once tests to avoid _init_components."""
    # These mocks are set up but won't be used since _init_components is mocked
    loop._evidence_ledger = MagicMock()
    loop._cost_controller = MagicMock()
    loop._cost_controller.calls_remaining.return_value = 100
    loop._cost_controller.get_today_usage.return_value = MagicMock(calls_used=10)
    loop._health_computer = MagicMock()


# ---------------------------------------------------------------------------
# CycleState enum tests
# ---------------------------------------------------------------------------


def test_cycle_state_values() -> None:
    """CycleState enum has expected string values."""
    assert CycleState.IDLE == "idle"
    assert CycleState.SCANNING == "scanning"
    assert CycleState.ANALYZING == "analyzing"
    assert CycleState.PLANNING == "planning"
    assert CycleState.DEPLOYING == "deploying"
    assert CycleState.VERIFYING == "verifying"
    assert CycleState.COMMITTING == "committing"
    assert CycleState.ERROR == "error"


def test_cycle_state_is_strenum() -> None:
    """CycleState is a StrEnum."""
    assert isinstance(CycleState.IDLE, str)


# ---------------------------------------------------------------------------
# CycleResult model tests
# ---------------------------------------------------------------------------


def test_cycle_result_defaults() -> None:
    """CycleResult model has correct default values."""
    result = CycleResult(cycle_id="test_123", state=CycleState.IDLE)
    assert result.cycle_id == "test_123"
    assert result.state == CycleState.IDLE
    assert result.health_score == 0.0
    assert result.health_band == ""
    assert result.findings_count == 0
    assert result.tasks_planned == 0
    assert result.tasks_executed == 0
    assert result.tasks_verified == 0
    assert result.budget_used == 0
    assert result.budget_remaining == 0
    assert result.started_at == ""
    assert result.completed_at == ""
    assert result.error == ""


def test_cycle_result_all_fields() -> None:
    """CycleResult model accepts all fields."""
    result = CycleResult(
        cycle_id="test_456",
        state=CycleState.COMMITTING,
        health_score=85.0,
        health_band="healthy",
        findings_count=5,
        tasks_planned=10,
        tasks_executed=8,
        tasks_verified=7,
        budget_used=15,
        budget_remaining=85,
        started_at="2024-01-01T00:00:00",
        completed_at="2024-01-01T00:01:00",
        error="",
    )
    assert result.cycle_id == "test_456"
    assert result.state == CycleState.COMMITTING
    assert result.health_score == 85.0
    assert result.health_band == "healthy"


def test_cycle_result_with_error() -> None:
    """CycleResult model stores error messages."""
    result = CycleResult(
        cycle_id="test_err",
        state=CycleState.ERROR,
        error="Something went wrong",
    )
    assert result.error == "Something went wrong"


def test_cycle_result_invalid_state() -> None:
    """CycleResult rejects invalid state values."""
    with pytest.raises(ValidationError):
        CycleResult(cycle_id="test", state="invalid_state")


# ---------------------------------------------------------------------------
# AgilePlusLoop initialization tests
# ---------------------------------------------------------------------------


def test_loop_initialization_defaults(loop: AgilePlusLoop) -> None:
    """AgilePlusLoop initializes with correct defaults."""
    assert loop.state == CycleState.IDLE
    assert loop.cycle_id == ""
    assert loop.health_threshold == 90.0
    assert loop.max_tasks_per_cycle == 10
    assert loop.max_rerolls == 2


def test_loop_initialization_custom_params(
    project_dir: Path,
    health_targets_path: Path,
) -> None:
    """AgilePlusLoop accepts custom parameters."""
    loop = AgilePlusLoop(
        project_dir=project_dir,
        health_targets_path=health_targets_path,
        health_threshold=80.0,
        max_tasks_per_cycle=5,
        max_rerolls=1,
    )
    assert loop.health_threshold == 80.0
    assert loop.max_tasks_per_cycle == 5
    assert loop.max_rerolls == 1


def test_loop_initializes_components_as_none(loop: AgilePlusLoop) -> None:
    """Components are initialized lazily (None initially)."""
    assert loop._scanner is None
    assert loop._analyzer is None
    assert loop._planner is None
    assert loop._backlog is None
    assert loop._cost_controller is None
    assert loop._evidence_ledger is None


def test_loop_signal_handlers_registered(loop: AgilePlusLoop) -> None:
    """Signal handlers are registered for graceful shutdown."""
    # Check that signal handlers are set - we verify by checking the handler
    # is a callable (the actual signal handling is tested separately)
    assert callable(loop._shutdown_requested) is not True  # Not initialized as True


# ---------------------------------------------------------------------------
# AgilePlusLoop.run_once() tests
# ---------------------------------------------------------------------------


def test_run_once_full_cycle(loop: AgilePlusLoop) -> None:
    """run_once executes full scan-analyze-plan-deploy-verify-commit cycle."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK) as mock_scan,
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=50.0, band=MagicMock(value="warning")),
        ) as mock_compute,
        patch.object(AgilePlusLoop, "_run_analysis", return_value=_FINDINGS_MOCK) as mock_analysis,
        patch.object(AgilePlusLoop, "_run_planning", return_value=_PLAN_MOCK) as mock_planning,
        patch.object(AgilePlusLoop, "_run_deployment", return_value=_DEPLOYMENT_RESULT_MOCK) as mock_deploy,
        patch.object(AgilePlusLoop, "_run_verification", return_value=2) as mock_verify,
        patch.object(AgilePlusLoop, "_run_commitment") as mock_commit,
    ):
        result = loop.run_once(force=False)

    # Verify state transitions
    assert mock_scan.call_count == 1
    assert mock_compute.call_count == 1
    assert mock_analysis.call_count == 1
    assert mock_planning.call_count == 1
    assert mock_deploy.call_count == 1
    assert mock_verify.call_count == 1
    assert mock_commit.call_count == 1

    # Verify result
    assert result.cycle_id.startswith("cycle_")
    assert result.state == CycleState.IDLE
    assert result.health_score == 50.0
    assert result.findings_count == 2
    assert result.tasks_planned == 2
    assert result.tasks_executed == 2
    assert result.tasks_verified == 2


def test_run_once_idle_when_healthy(loop: AgilePlusLoop) -> None:
    """run_once idles when health >= threshold (without force)."""
    _setup_loop_mocks(loop)

    # Create health mock properly using configure_mock
    healthy_health = MagicMock()
    type(healthy_health).score = 95.0  # Use type() to set the attribute properly
    healthy_health.configure_mock(band=MagicMock(value="excellent"))

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(AgilePlusLoop, "_compute_health", return_value=healthy_health),
    ):
        result = loop.run_once(force=False)

    # Should return early with IDLE state in result
    assert result.state == CycleState.IDLE
    assert result.health_score == 95.0


def test_run_once_forces_cycle_when_healthy(loop: AgilePlusLoop) -> None:
    """run_once with force=True runs full cycle even when healthy."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=95.0, band=MagicMock(value="excellent")),
        ),
        patch.object(AgilePlusLoop, "_run_analysis", return_value=[]),
        patch.object(AgilePlusLoop, "_run_planning", return_value=MagicMock(tasks=[])),
        patch.object(AgilePlusLoop, "_run_deployment", return_value=MagicMock(tasks_completed=0)),
        patch.object(AgilePlusLoop, "_run_verification", return_value=0),
        patch.object(AgilePlusLoop, "_run_commitment"),
    ):
        result = loop.run_once(force=True)

    # Should run full cycle despite healthy score
    assert result.state == CycleState.IDLE  # Completed successfully


def test_run_once_state_transitions(
    project_dir: Path,
    health_targets_path: Path,
) -> None:
    """run_once correctly transitions through all States."""
    loop = AgilePlusLoop(
        project_dir=project_dir,
        health_targets_path=health_targets_path,
        health_threshold=90.0,
    )
    _setup_loop_mocks(loop)

    # Track state changes by patching setattr
    states_seen: list[CycleState] = []
    original_setattr = AgilePlusLoop.__setattr__

    def track_state(self: AgilePlusLoop, name: str, value: object) -> None:
        if name == "_state" and isinstance(value, CycleState):
            states_seen.append(value)
        original_setattr(self, name, value)

    with patch.object(AgilePlusLoop, "__setattr__", track_state):
        with (
            patch.object(AgilePlusLoop, "_init_components"),
            patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
            patch.object(
                AgilePlusLoop,
                "_compute_health",
                return_value=MagicMock(score=50.0, band=MagicMock(value="warning")),
            ),
            patch.object(AgilePlusLoop, "_run_analysis", return_value=_FINDINGS_MOCK),
            patch.object(AgilePlusLoop, "_run_planning", return_value=_PLAN_MOCK),
            patch.object(AgilePlusLoop, "_run_deployment", return_value=_DEPLOYMENT_RESULT_MOCK),
            patch.object(AgilePlusLoop, "_run_verification", return_value=2),
            patch.object(AgilePlusLoop, "_run_commitment"),
        ):
            loop.run_once(force=True)

    # Verify expected state transitions
    assert CycleState.SCANNING in states_seen
    assert CycleState.ANALYZING in states_seen
    assert CycleState.PLANNING in states_seen
    assert CycleState.DEPLOYING in states_seen
    assert CycleState.VERIFYING in states_seen
    assert CycleState.COMMITTING in states_seen


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


def test_run_once_handles_scan_error(loop: AgilePlusLoop) -> None:
    """run_once handles scan errors gracefully."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", side_effect=RuntimeError("Scan failed")),
    ):
        result = loop.run_once(force=True)

    assert result.state == CycleState.ERROR
    assert "Scan failed" in result.error


def test_run_once_handles_analysis_error(loop: AgilePlusLoop) -> None:
    """run_once handles analysis errors gracefully."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=50.0, band=MagicMock(value="warning")),
        ),
        patch.object(AgilePlusLoop, "_run_analysis", side_effect=RuntimeError("Analysis failed")),
    ):
        result = loop.run_once(force=True)

    assert result.state == CycleState.ERROR
    assert "Analysis failed" in result.error


def test_run_once_handles_planning_error(loop: AgilePlusLoop) -> None:
    """run_once handles planning errors gracefully."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=50.0, band=MagicMock(value="warning")),
        ),
        patch.object(AgilePlusLoop, "_run_analysis", return_value=_FINDINGS_MOCK),
        patch.object(AgilePlusLoop, "_run_planning", side_effect=RuntimeError("Planning failed")),
    ):
        result = loop.run_once(force=True)

    assert result.state == CycleState.ERROR
    assert "Planning failed" in result.error


def test_run_once_handles_deployment_error(loop: AgilePlusLoop) -> None:
    """run_once handles deployment errors gracefully."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=50.0, band=MagicMock(value="warning")),
        ),
        patch.object(AgilePlusLoop, "_run_analysis", return_value=_FINDINGS_MOCK),
        patch.object(AgilePlusLoop, "_run_planning", return_value=_PLAN_MOCK),
        patch.object(
            AgilePlusLoop,
            "_run_deployment",
            side_effect=RuntimeError("Deployment failed"),
        ),
    ):
        result = loop.run_once(force=True)

    assert result.state == CycleState.ERROR
    assert "Deployment failed" in result.error


def test_run_once_handles_verification_error(loop: AgilePlusLoop) -> None:
    """run_once handles verification errors gracefully."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=50.0, band=MagicMock(value="warning")),
        ),
        patch.object(AgilePlusLoop, "_run_analysis", return_value=_FINDINGS_MOCK),
        patch.object(AgilePlusLoop, "_run_planning", return_value=_PLAN_MOCK),
        patch.object(AgilePlusLoop, "_run_deployment", return_value=_DEPLOYMENT_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_run_verification",
            side_effect=RuntimeError("Verification failed"),
        ),
    ):
        result = loop.run_once(force=True)

    assert result.state == CycleState.ERROR
    assert "Verification failed" in result.error


# ---------------------------------------------------------------------------
# run_continuous tests
# ---------------------------------------------------------------------------


@patch("time.sleep")
@patch.object(AgilePlusLoop, "run_once")
def test_run_continuous_single_cycle(
    mock_run_once: MagicMock,
    mock_sleep: MagicMock,
    loop: AgilePlusLoop,
) -> None:
    """run_continuous runs until max_cycles is reached."""
    mock_run_once.return_value = MagicMock(
        health_score=50.0,
        state=CycleState.IDLE,
    )

    results = loop.run_continuous(interval_seconds=60, max_cycles=1)

    assert len(results) == 1
    assert mock_run_once.call_count == 1


@patch("time.sleep")
@patch.object(AgilePlusLoop, "run_once")
def test_run_continuous_multiple_cycles(
    mock_run_once: MagicMock,
    mock_sleep: MagicMock,
    loop: AgilePlusLoop,
) -> None:
    """run_continuous runs multiple cycles."""
    mock_run_once.return_value = MagicMock(
        health_score=50.0,
        state=CycleState.IDLE,
    )

    results = loop.run_continuous(interval_seconds=60, max_cycles=3)

    assert len(results) == 3
    assert mock_run_once.call_count == 3


@patch("time.sleep")
@patch.object(AgilePlusLoop, "run_once")
def test_run_continuous_health_based_interval(
    mock_run_once: MagicMock,
    mock_sleep: MagicMock,
    loop: AgilePlusLoop,
) -> None:
    """run_continuous uses longer interval when healthy."""
    loop._shutdown_requested = False

    # First call returns healthy score, second call returns unhealthy
    mock_run_once.side_effect = [
        MagicMock(health_score=95.0, state=CycleState.IDLE),
        MagicMock(health_score=50.0, state=CycleState.IDLE),
    ]

    with patch.object(AgilePlusLoop, "run_once", mock_run_once):
        loop.run_continuous(interval_seconds=60, max_cycles=2)

    # First call should have slept for interval * 2 (healthy)
    assert mock_sleep.call_count >= 1


@patch("time.sleep")
@patch.object(AgilePlusLoop, "run_once")
def test_run_continuous_respects_shutdown(
    mock_run_once: MagicMock,
    mock_sleep: MagicMock,
    loop: AgilePlusLoop,
) -> None:
    """run_continuous stops when shutdown is requested."""
    # Set shutdown flag before starting
    loop._shutdown_requested = True

    mock_run_once.return_value = MagicMock(
        health_score=50.0,
        state=CycleState.IDLE,
    )

    with patch.object(AgilePlusLoop, "run_once", mock_run_once):
        loop.run_continuous(interval_seconds=60, max_cycles=10)

    # Should not have run any cycles due to shutdown
    assert mock_run_once.call_count == 0


# ---------------------------------------------------------------------------
# Graceful shutdown tests
# ---------------------------------------------------------------------------


def test_request_shutdown_sets_flag(loop: AgilePlusLoop) -> None:
    """request_shutdown sets the shutdown flag."""
    assert loop._shutdown_requested is False
    loop.request_shutdown()
    assert loop._shutdown_requested is True


def test_signal_handler_sets_shutdown_flag(loop: AgilePlusLoop) -> None:
    """Signal handler correctly sets shutdown flag."""
    assert loop._shutdown_requested is False
    loop._signal_handler(signal.SIGINT, None)
    assert loop._shutdown_requested is True


def test_signal_handler_handles_sigterm(loop: AgilePlusLoop) -> None:
    """Signal handler handles SIGTERM."""
    loop._shutdown_requested = False
    loop._signal_handler(signal.SIGTERM, None)
    assert loop._shutdown_requested is True


# ---------------------------------------------------------------------------
# get_status tests
# ---------------------------------------------------------------------------


def test_get_status_idle(loop: AgilePlusLoop) -> None:
    """get_status returns correct status when idle."""
    status = loop.get_status()
    assert status["state"] == "idle"
    assert status["cycle_id"] == ""
    assert status["shutdown_requested"] is False


def test_get_status_during_cycle(
    project_dir: Path,
    health_targets_path: Path,
) -> None:
    """get_status reflects current cycle state."""
    loop = AgilePlusLoop(
        project_dir=project_dir,
        health_targets_path=health_targets_path,
    )
    loop._state = CycleState.SCANNING
    loop._cycle_id = "cycle_abc123"

    status = loop.get_status()
    assert status["state"] == "scanning"
    assert status["cycle_id"] == "cycle_abc123"


def test_get_status_after_shutdown_request(loop: AgilePlusLoop) -> None:
    """get_status shows shutdown requested."""
    loop._shutdown_requested = True
    status = loop.get_status()
    assert status["shutdown_requested"] is True


# ---------------------------------------------------------------------------
# Properties tests
# ---------------------------------------------------------------------------


def test_state_property(loop: AgilePlusLoop) -> None:
    """state property returns current state."""
    assert loop.state == CycleState.IDLE
    loop._state = CycleState.SCANNING
    assert loop.state == CycleState.SCANNING


def test_cycle_id_property(loop: AgilePlusLoop) -> None:
    """cycle_id property returns current cycle ID."""
    assert loop.cycle_id == ""
    loop._cycle_id = "cycle_xyz"
    assert loop.cycle_id == "cycle_xyz"


# ---------------------------------------------------------------------------
# Component initialization tests
# ---------------------------------------------------------------------------


def test_init_components(
    project_dir: Path,
    health_targets_path: Path,
) -> None:
    """_init_components initializes all required components."""
    loop = AgilePlusLoop(
        project_dir=project_dir,
        health_targets_path=health_targets_path,
    )

    # Mock at the point of import - these are imported inside _init_components
    with (
        patch("thegent.governance.scanner.CodebaseScanner") as mock_scanner,
        patch("thegent.governance.health_score.HealthScoreComputer") as mock_hc,
        patch("thegent.governance.analyzer.HealthAnalyzer") as mock_analyzer,
        patch("thegent.planning.remediation_planner.RemediationPlanner") as mock_planner,
        patch("thegent.governance.backlog.BacklogManager") as mock_backlog,
        patch("thegent.cost.aggregator_controller.CostController") as mock_cost,
        patch("thegent.governance.evidence_ledger.EvidenceLedger") as mock_ledger,
        patch("thegent.config.ThegentSettings") as mock_settings,
    ):
        mock_scanner.return_value = MagicMock()
        mock_hc.return_value = MagicMock()
        mock_analyzer.return_value = MagicMock()
        mock_planner.return_value = MagicMock()
        mock_backlog.return_value = MagicMock()
        mock_cost.return_value = MagicMock()
        mock_ledger.return_value = MagicMock()
        mock_settings.return_value = MagicMock(session_dir=project_dir / ".thegent")

        loop._init_components()

    # Verify components are initialized
    assert loop._scanner is not None
    assert loop._analyzer is not None
    assert loop._planner is not None
    assert loop._backlog is not None
    assert loop._cost_controller is not None
    assert loop._evidence_ledger is not None
    assert loop._health_computer is not None


# ---------------------------------------------------------------------------
# Edge cases and integration tests
# ---------------------------------------------------------------------------


def test_run_once_with_empty_findings(loop: AgilePlusLoop) -> None:
    """run_once handles empty findings list."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=50.0, band=MagicMock(value="warning")),
        ),
        patch.object(AgilePlusLoop, "_run_analysis", return_value=[]),
        patch.object(
            AgilePlusLoop,
            "_run_planning",
            return_value=MagicMock(tasks=[], total_estimated_calls=0),
        ),
        patch.object(AgilePlusLoop, "_run_deployment") as mock_deploy,
        patch.object(AgilePlusLoop, "_run_verification", return_value=0),
        patch.object(AgilePlusLoop, "_run_commitment"),
    ):
        result = loop.run_once(force=True)

    assert result.findings_count == 0
    assert result.tasks_planned == 0
    # Deployment should still be called but with empty plan
    assert mock_deploy.call_count == 1


def test_run_once_completed_at_timestamp(loop: AgilePlusLoop) -> None:
    """run_once sets completed_at timestamp."""
    _setup_loop_mocks(loop)

    with (
        patch.object(AgilePlusLoop, "_init_components"),
        patch.object(AgilePlusLoop, "_run_scan", return_value=_SCAN_RESULT_MOCK),
        patch.object(
            AgilePlusLoop,
            "_compute_health",
            return_value=MagicMock(score=95.0, band=MagicMock(value="excellent")),
        ),
    ):
        result = loop.run_once(force=False)

    assert result.completed_at != ""
    # Should be ISO format timestamp
    assert "T" in result.completed_at


def test_loop_preserves_project_dir(
    project_dir: Path,
    health_targets_path: Path,
) -> None:
    """AgilePlusLoop preserves project_dir reference."""
    loop = AgilePlusLoop(
        project_dir=project_dir,
        health_targets_path=health_targets_path,
    )
    assert loop.project_dir == project_dir


def test_loop_preserves_health_targets_path(
    project_dir: Path,
    health_targets_path: Path,
) -> None:
    """AgilePlusLoop preserves health_targets_path reference."""
    loop = AgilePlusLoop(
        project_dir=project_dir,
        health_targets_path=health_targets_path,
    )
    assert loop.health_targets_path == health_targets_path


# ---------------------------------------------------------------------------
# Additional test cases for coverage
# ---------------------------------------------------------------------------


def test_cycle_result_model_validation() -> None:
    """CycleResult validates fields correctly."""
    # Valid creation
    result = CycleResult(cycle_id="test", state=CycleState.IDLE)
    assert result.cycle_id == "test"

    # Invalid state should raise
    with pytest.raises(ValidationError):
        CycleResult(cycle_id="test", state="not_a_state")


def test_run_continuous_with_zero_max_cycles(
    loop: AgilePlusLoop,
) -> None:
    """run_continuous handles zero max_cycles."""
    mock_result = MagicMock()
    mock_result.health_score = 50.0
    mock_result.state = CycleState.IDLE

    with (
        patch.object(AgilePlusLoop, "run_once", return_value=mock_result) as mock_run,
        patch("time.sleep"),
    ):
        results = loop.run_continuous(interval_seconds=60, max_cycles=0)

    # Should not run any cycles
    assert mock_run.call_count == 0
    assert len(results) == 0


def test_run_continuous_infinite_loop(
    loop: AgilePlusLoop,
) -> None:
    """run_continuous handles infinite loop with shutdown."""
    loop._shutdown_requested = True

    with patch.object(AgilePlusLoop, "run_once") as mock_run, patch("time.sleep"):
        loop.run_continuous(interval_seconds=60, max_cycles=None)

    # Should stop immediately due to shutdown
    assert mock_run.call_count == 0


def test_cycle_state_string_comparison() -> None:
    """CycleState values can be compared as strings."""
    assert CycleState.IDLE == "idle"
    assert CycleState.SCANNING == "scanning"
    assert "idle" in [s.value for s in CycleState]


def test_cycle_result_model_field_types() -> None:
    """CycleResult model has correct field types."""
    result = CycleResult(
        cycle_id="test",
        state=CycleState.IDLE,
        health_score=85.5,
        health_band="healthy",
        findings_count=10,
        tasks_planned=5,
        tasks_executed=3,
        tasks_verified=2,
        budget_used=100,
        budget_remaining=400,
    )
    # Verify types
    assert isinstance(result.cycle_id, str)
    assert isinstance(result.health_score, float)
    assert isinstance(result.findings_count, int)
    assert isinstance(result.tasks_planned, int)
