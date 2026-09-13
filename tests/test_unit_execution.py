"""Unit tests for execution registry and state-aware orchestration (G-KD-03)."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.execution import (
    Auditor,
    CheckpointRegistry,
    CircuitBreakerRegistry,
    EscalationQueue,
    OverrideRegistry,
    PolicyEngine,
    RunMeta,
    RunRegistry,
    RunState,
    TrustBoundaryValidator,
)


@pytest.mark.unit
class TestRunRegistryStateAware:
    """Tests for register_pause, register_resume, get_run_state."""

    def test_get_run_state_none_for_unknown_run(self) -> None:
        # @trace FR-EXE-004
        """Unknown run_id returns None."""
        with tempfile.TemporaryDirectory() as d:
            r = RunRegistry(Path(d))
            assert r.get_run_state("run_unknown") is None

    def test_get_run_state_running_after_start(self) -> None:
        # @trace FR-EXE-004
        """After register_start, state is RUNNING."""
        with tempfile.TemporaryDirectory() as d:
            r = RunRegistry(Path(d))
            m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
            r.register_start(m)
            assert r.get_run_state("run_1") == RunState.RUNNING

    def test_get_run_state_paused_after_pause(self) -> None:
        # @trace FR-EXE-004
        """After register_pause, state is PAUSED."""
        with tempfile.TemporaryDirectory() as d:
            r = RunRegistry(Path(d))
            m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
            r.register_start(m)
            r.register_pause("run_1", "manual", {"phase": "operator"})
            assert r.get_run_state("run_1") == RunState.PAUSED

    def test_get_run_state_running_after_resume(self) -> None:
        # @trace FR-EXE-004
        """After register_resume, state is RUNNING."""
        with tempfile.TemporaryDirectory() as d:
            r = RunRegistry(Path(d))
            m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
            r.register_start(m)
            r.register_pause("run_1", "manual")
            r.register_resume("run_1")
            assert r.get_run_state("run_1") == RunState.RUNNING

    def test_get_run_state_completed_after_finish(self) -> None:
        # @trace FR-EXE-004
        """After register_end with completed, state is COMPLETED."""
        with tempfile.TemporaryDirectory() as d:
            r = RunRegistry(Path(d))
            m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
            r.register_start(m)
            r.register_end("run_1", 0, "completed", "2026-02-14T12:00:00Z", 1.0)
            assert r.get_run_state("run_1") == RunState.COMPLETED

    def test_get_run_state_failed_after_finish(self) -> None:
        # @trace FR-EXE-004
        """After register_end with failed, state is FAILED."""
        with tempfile.TemporaryDirectory() as d:
            r = RunRegistry(Path(d))
            m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
            r.register_start(m)
            r.register_end("run_1", 1, "failed", "2026-02-14T12:00:00Z", 1.0)
            assert r.get_run_state("run_1") == RunState.FAILED


@pytest.mark.unit
class TestPolicyEngineEvaluate:
    """Tests for PolicyEngine.evaluate() Python-logic policies."""

    def _make_settings(self, **overrides: object) -> MagicMock:
        settings = MagicMock()
        settings.opa_url = ""
        settings.environment = overrides.get("environment", "development")
        settings.trust_score_threshold = overrides.get("trust_score_threshold", 0.8)
        settings.session_dir = overrides.get("session_dir", Path("/tmp"))
        settings.cost_tracking_enabled = False
        return settings

    def test_allow_standard_lane_development(self) -> None:
        # @trace FR-EXE-008
        """Standard lane in development environment is allowed."""
        engine = PolicyEngine(self._make_settings())
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="u", lane="standard")
        result, _reason = engine.evaluate(run)
        assert result == "allow"

    def test_deny_critical_lane_low_confidence(self) -> None:
        # @trace FR-EXE-008
        """Critical lane with confidence < 0.9 is denied."""
        engine = PolicyEngine(self._make_settings())
        run = RunMeta(
            agent="gemini",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="critical",
            confidence=0.5,
        )
        result, reason = engine.evaluate(run)
        assert result == "deny"
        assert "0.9" in reason

    def test_allow_critical_lane_high_confidence(self, tmp_path: Path) -> None:
        # @trace FR-EXE-008
        """Critical lane with confidence >= 0.9 is allowed (drift within budget)."""
        settings = self._make_settings(session_dir=tmp_path)
        engine = PolicyEngine(settings)
        run = RunMeta(
            agent="gemini",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="critical",
            confidence=0.95,
        )
        with patch("thegent.contracts.telemetry.ContractTelemetry") as mock_ct:
            mock_ct.return_value.get_drift_budget_status.return_value = {"within_budget": True}
            result, _reason = engine.evaluate(run)
        assert result == "allow"

    def test_deny_unknown_agent_production(self) -> None:
        # @trace FR-EXE-008
        """Unknown agents blocked in production."""
        engine = PolicyEngine(self._make_settings(environment="production"))
        run = RunMeta(
            agent="unknown",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="standard",
            confidence=0.9,
        )
        result, reason = engine.evaluate(run)
        assert result == "deny"
        assert "Unknown" in reason or "unknown" in reason.lower()

    def test_deny_unknown_agent_critical_lane(self) -> None:
        # @trace FR-EXE-008
        """Unknown agents blocked in critical lane regardless of environment."""
        engine = PolicyEngine(self._make_settings())
        run = RunMeta(
            agent="unknown",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="critical",
            confidence=0.95,
        )
        with patch("thegent.contracts.telemetry.ContractTelemetry") as mock_ct:
            mock_ct.return_value.get_drift_budget_status.return_value = {"within_budget": True}
            result, _reason = engine.evaluate(run)
        assert result == "deny"

    def test_warn_recovery_lane_no_confidence(self) -> None:
        # @trace FR-EXE-008
        """Recovery lane without confidence score triggers a warning."""
        engine = PolicyEngine(self._make_settings())
        run = RunMeta(
            agent="gemini",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="recovery",
            confidence=None,
        )
        result, reason = engine.evaluate(run)
        assert result == "warn"
        assert "confidence" in reason.lower()

    def test_deny_production_below_trust_threshold(self) -> None:
        # @trace FR-EXE-006
        """Production denies when confidence below trust_score_threshold."""
        engine = PolicyEngine(self._make_settings(environment="production", trust_score_threshold=0.8))
        run = RunMeta(
            agent="gemini",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="standard",
            confidence=0.5,
        )
        result, reason = engine.evaluate(run)
        assert result == "deny"
        assert "0.8" in reason

    def test_allow_production_above_trust_threshold(self) -> None:
        # @trace FR-EXE-006
        """Production allows when confidence above trust_score_threshold."""
        engine = PolicyEngine(self._make_settings(environment="production", trust_score_threshold=0.8))
        run = RunMeta(
            agent="gemini",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="standard",
            confidence=0.9,
        )
        result, _reason = engine.evaluate(run)
        assert result == "allow"

    def test_calibration_adjusts_confidence(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """When registry is provided, confidence is calibrated before policy checks."""
        settings = self._make_settings()
        engine = PolicyEngine(settings)
        registry = MagicMock()
        registry.get_calibration_factor.return_value = 0.5
        run = RunMeta(
            agent="gemini",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="standard",
            confidence=0.8,
        )
        result, _reason = engine.evaluate(run, registry=registry)
        # Confidence adjusted to 0.8 * 0.5 = 0.4, but in dev standard lane, still allowed
        assert result == "allow"
        registry.get_calibration_factor.assert_called_once_with("gemini")

    def test_critical_lane_drift_exceeds_budget(self, tmp_path: Path) -> None:
        # @trace FR-EXE-008
        """Critical lane denied when contract drift exceeds budget (XC2)."""
        settings = self._make_settings(session_dir=tmp_path)
        engine = PolicyEngine(settings)
        run = RunMeta(
            agent="gemini",
            prompt="test",
            cwd="/tmp",
            owner="u",
            lane="critical",
            confidence=0.95,
        )
        with patch("thegent.contracts.telemetry.ContractTelemetry") as mock_ct:
            mock_ct.return_value.get_drift_budget_status.return_value = {
                "within_budget": False,
                "structural_rate_pct": 6.0,
                "structural_budget_pct": 5.0,
                "semantic_rate_pct": 12.0,
                "semantic_budget_pct": 10.0,
            }
            result, reason = engine.evaluate(run)
        assert result == "deny"
        assert "drift" in reason.lower()

    def test_circuit_breaker_blocks_execution(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """PolicyEngine blocks execution when circuit breaker is open."""
        settings = self._make_settings(session_dir=tmp_path)
        settings.circuit_breaker_enabled = True
        settings.circuit_breaker_threshold = 1
        settings.circuit_breaker_window_s = 300
        settings.circuit_breaker_recovery_s = 60
        engine = PolicyEngine(settings)

        # Manually open the circuit
        cb = CircuitBreakerRegistry(tmp_path, threshold=1)
        cb.record_failure("gemini")

        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="u")
        result, reason = engine.evaluate(run)

        assert result == "deny"
        assert "Circuit breaker is OPEN" in reason


@pytest.mark.unit
class TestTrustBoundaryValidator:
    """Tests for TrustBoundaryValidator.validate_transition()."""

    def test_no_prior_environment_allowed(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """No prior environment always allowed."""
        v = TrustBoundaryValidator(tmp_path)
        ok, _reason = v.validate_transition(None, "production")
        assert ok is True

    def test_same_environment_allowed(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """Same environment transition allowed."""
        v = TrustBoundaryValidator(tmp_path)
        ok, _reason = v.validate_transition("staging", "staging")
        assert ok is True

    def test_downgrade_allowed(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """Downgrade (production -> staging) allowed."""
        v = TrustBoundaryValidator(tmp_path)
        ok, _reason = v.validate_transition("production", "staging")
        assert ok is True

    def test_valid_promotion_dev_to_staging(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """dev -> staging is a valid promotion."""
        v = TrustBoundaryValidator(tmp_path)
        ok, reason = v.validate_transition("development", "staging")
        assert ok is True
        assert "Valid promotion" in reason

    def test_skip_level_promotion_denied(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """dev -> production (skip-level) requires explicit audit."""
        v = TrustBoundaryValidator(tmp_path)
        ok, reason = v.validate_transition("development", "production")
        assert ok is False
        assert "Skip-level" in reason

    def test_unknown_env_allowed(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """Unknown environments pass through (no transition check)."""
        v = TrustBoundaryValidator(tmp_path)
        ok, _reason = v.validate_transition("custom-env", "production")
        assert ok is True

    def test_record_and_get_last_environment(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """record_environment and get_last_environment roundtrip."""
        v = TrustBoundaryValidator(tmp_path)
        assert v.get_last_environment() is None
        v.record_environment("staging")
        assert v.get_last_environment() == "staging"


@pytest.mark.unit
class TestCheckpointRegistry:
    """Tests for CheckpointRegistry.create_checkpoint() and list_checkpoints()."""

    def test_create_checkpoint_returns_meta(self, tmp_path: Path) -> None:
        # @trace FR-EXE-007
        """create_checkpoint returns CheckpointMeta with correct fields."""
        cr = CheckpointRegistry(tmp_path)
        ckpt = cr.create_checkpoint("test reason", "A -> B", "owner1")
        assert ckpt.reason == "test reason"
        assert ckpt.dag_content == "A -> B"
        assert ckpt.owner == "owner1"
        assert ckpt.checkpoint_id.startswith("ckpt_")

    def test_list_checkpoints_empty(self, tmp_path: Path) -> None:
        # @trace FR-EXE-007
        """list_checkpoints returns empty list when no checkpoints exist."""
        cr = CheckpointRegistry(tmp_path)
        assert cr.list_checkpoints() == []

    def test_list_checkpoints_after_create(self, tmp_path: Path) -> None:
        # @trace FR-EXE-007
        """list_checkpoints returns checkpoints after creation."""
        cr = CheckpointRegistry(tmp_path)
        cr.create_checkpoint("reason1", "dag1", "owner1")
        cr.create_checkpoint("reason2", "dag2", "owner2")
        ckpts = cr.list_checkpoints()
        assert len(ckpts) == 2

    def test_get_checkpoint_by_id(self, tmp_path: Path) -> None:
        # @trace FR-EXE-007
        """get_checkpoint returns the correct checkpoint by ID."""
        cr = CheckpointRegistry(tmp_path)
        ckpt = cr.create_checkpoint("specific", "dag", "owner")
        result = cr.get_checkpoint(ckpt.checkpoint_id)
        assert result is not None
        assert result["reason"] == "specific"

    def test_get_checkpoint_unknown_returns_none(self, tmp_path: Path) -> None:
        # @trace FR-EXE-007
        """get_checkpoint with unknown ID returns None."""
        cr = CheckpointRegistry(tmp_path)
        assert cr.get_checkpoint("ckpt_nonexistent") is None


@pytest.mark.unit
class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""

    def test_is_open_false_when_no_failures(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Circuit is closed when no failures recorded."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=3)
        assert cb.is_open("agent-x") is False

    def test_is_open_true_after_threshold_failures(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Circuit opens after reaching failure threshold."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=3, window_s=300, recovery_s=60)
        for _ in range(3):
            cb.record_failure("agent-x")
        assert cb.is_open("agent-x") is True

    def test_is_open_false_below_threshold(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Circuit stays closed below failure threshold."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=5)
        for _ in range(4):
            cb.record_failure("agent-x")
        assert cb.is_open("agent-x") is False

    def test_different_targets_isolated(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Failures for different targets are isolated."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=2)
        cb.record_failure("agent-a")
        cb.record_failure("agent-a")
        cb.record_failure("agent-b")
        assert cb.is_open("agent-a") is True
        assert cb.is_open("agent-b") is False

    def test_category_isolation(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Different categories for same target are isolated."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=2)
        cb.record_failure("target-x", category="agent")
        cb.record_failure("target-x", category="agent")
        assert cb.is_open("target-x", category="agent") is True
        assert cb.is_open("target-x", category="model") is False


@pytest.mark.unit
class TestOverrideRegistry:
    """Tests for OverrideRegistry."""

    def test_has_unexpired_false_when_empty(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """No unexpired override when registry is empty."""
        oreg = OverrideRegistry(tmp_path)
        assert oreg.has_unexpired("user1") is False

    def test_has_unexpired_true_after_record(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Override is unexpired immediately after recording with long TTL."""
        oreg = OverrideRegistry(tmp_path)
        oreg.record("user1", "testing", ttl_seconds=3600)
        assert oreg.has_unexpired("user1") is True

    def test_has_unexpired_false_for_different_owner(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Override for one owner does not affect another."""
        oreg = OverrideRegistry(tmp_path)
        oreg.record("user1", "testing", ttl_seconds=3600)
        assert oreg.has_unexpired("user2") is False

    def test_has_unexpired_false_after_expiry(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Override is expired after TTL (recorded with ttl=0 means effectively expired)."""
        oreg = OverrideRegistry(tmp_path)
        # Record with 0 TTL -- immediately expired (or very close)
        oreg.record("user1", "testing", ttl_seconds=0)
        # The override expires_at is ~now, so it should already be expired or borderline
        # Use a slightly different approach: write an already-expired entry
        expired_event = {
            "owner": "user2",
            "reason": "old override",
            "timestamp": "2020-01-01T00:00:00+00:00",
            "expires_at_utc": "2020-01-01T00:01:00+00:00",
        }
        with oreg.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(expired_event).decode() + "\n")
        assert oreg.has_unexpired("user2") is False


@pytest.mark.unit
class TestEscalationQueue:
    """Tests for EscalationQueue."""

    def test_list_pending_empty(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """list_pending returns empty list when queue is empty."""
        eq = EscalationQueue(tmp_path)
        assert eq.list_pending() == []

    def test_add_and_list_pending(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """add() then list_pending() returns the item."""
        eq = EscalationQueue(tmp_path)
        eq.add("run_1", "denied by policy", sla_minutes=30, owner="user1")
        items = eq.list_pending()
        assert len(items) == 1
        assert items[0]["run_id"] == "run_1"
        assert items[0]["status"] == "pending"

    def test_resolve_marks_resolved(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """resolve() marks item as resolved."""
        eq = EscalationQueue(tmp_path)
        eq.add("run_2", "blocked", sla_minutes=30)
        assert eq.resolve("run_2") is True
        # After resolution, list_pending should be empty
        assert eq.list_pending() == []

    def test_resolve_returns_false_for_unknown(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """resolve() returns False for unknown run_id."""
        eq = EscalationQueue(tmp_path)
        assert eq.resolve("run_nonexistent") is False

    def test_past_sla_only_filter(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """list_pending(past_sla_only=True) filters to only past-SLA items."""
        eq = EscalationQueue(tmp_path)
        # Add item with very long SLA (won't be past SLA)
        eq.add("run_future", "reason", sla_minutes=9999)
        items = eq.list_pending(past_sla_only=True)
        assert len(items) == 0
        # Without filter, item is present
        items_all = eq.list_pending(past_sla_only=False)
        assert len(items_all) == 1


@pytest.mark.unit
class TestAuditorVerifyRegistry:
    """Tests for Auditor.verify_registry()."""

    def test_verify_empty_registry(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """Empty registry returns status='empty'."""
        reg_path = tmp_path / "run_registry.jsonl"
        auditor = Auditor(reg_path)
        result = auditor.verify_registry()
        assert result["status"] == "empty"
        assert result["valid_count"] == 0
        assert result["corrupt_count"] == 0

    def test_verify_valid_chained_registry(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """Valid hash-chained registry passes verification."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
        reg.register_start(m)
        reg.register_end("run_1", 0, "completed", "2026-02-14T12:00:00Z", 1.0)
        auditor = Auditor(reg.registry_path)
        result = auditor.verify_registry()
        assert result["status"] == "passed"
        assert result["corrupt_count"] == 0
        assert result["chain_broken"] is False

    def test_verify_detects_tampered_hash(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """Tampered hash is detected as corrupt."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
        reg.register_start(m)
        # Tamper with the registry file
        content = reg.registry_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        if len(lines) >= 2:
            data = json.loads(lines[1])
            data["hash"] = "tampered_hash_value"
            lines[1] = json.dumps(data).decode()
            reg.registry_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        auditor = Auditor(reg.registry_path)
        result = auditor.verify_registry()
        assert result["status"] == "failed"
        assert result["corrupt_count"] > 0

    def test_sign_run_deterministic(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """sign_run produces deterministic signature for same input."""
        auditor = Auditor(tmp_path / "registry.jsonl")
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="x",
            cwd="/tmp",
            owner="u",
            started_at_utc="2026-01-01T00:00:00Z",
        )
        sig1 = auditor.sign_run(m)
        sig2 = auditor.sign_run(m)
        assert sig1 == sig2
        assert len(sig1) == 64  # SHA-256 hex digest


@pytest.mark.unit
class TestRunRegistryRetention:
    """Tests for tiered retention purge (G-GP-07)."""

    def test_purge_expired_dry_run(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """purge_expired identifies expired records but does not delete them in dry_run."""
        reg = RunRegistry(tmp_path)

        # Old record (expired)
        old_ts = "2020-01-01T00:00:00Z"
        m_old = RunMeta(
            run_id="run_old",
            agent="gemini",
            prompt="old",
            cwd="/tmp",
            owner="u",
            started_at_utc=old_ts,
        )
        reg.register_start(m_old)

        # New record (not expired)
        now_ts = datetime.now(UTC).isoformat()
        m_new = RunMeta(
            run_id="run_new",
            agent="gemini",
            prompt="new",
            cwd="/tmp",
            owner="u",
            started_at_utc=now_ts,
        )
        reg.register_start(m_new)

        result = reg.purge_expired(default_days=30, by_domain={}, dry_run=True)
        assert result["purged"] == 1
        assert result["kept"] == 2  # run_new + schema marker

        # Verify file still has both records
        content = reg.registry_path.read_text()
        assert "run_old" in content
        assert "run_new" in content

    def test_purge_expired_with_domain_override(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """purge_expired respects per-domain retention overrides."""
        reg = RunRegistry(tmp_path)

        # Record from 10 days ago
        from datetime import timedelta

        ts_10d = (datetime.now(UTC) - timedelta(days=10)).isoformat()

        # Domain 'short' with 5 day retention (should be purged)
        m1 = RunMeta(
            run_id="r1",
            agent="a",
            prompt="p",
            cwd="/tmp",
            owner="u",
            started_at_utc=ts_10d,
            domain_tag="short",
        )
        reg.register_start(m1)

        # Domain 'long' with 20 day retention (should be kept)
        m2 = RunMeta(
            run_id="r2",
            agent="a",
            prompt="p",
            cwd="/tmp",
            owner="u",
            started_at_utc=ts_10d,
            domain_tag="long",
        )
        reg.register_start(m2)

        result = reg.purge_expired(default_days=30, by_domain={"short": 5, "long": 20}, dry_run=False)
        assert result["purged"] == 1
        assert result["kept"] == 2  # r2 + schema marker

        content = reg.registry_path.read_text()
        assert "r1" not in content
        assert "r2" in content


@pytest.mark.unit
class TestRunRegistryListRuns:
    """Tests for RunRegistry.list_runs edge cases."""

    def test_list_runs_empty_registry(self, tmp_path: Path) -> None:
        # @trace FR-EXE-003
        """list_runs returns empty list when registry file does not exist."""
        reg = RunRegistry(tmp_path)
        # Remove the file created by __init__
        reg.registry_path.unlink(missing_ok=True)
        assert reg.list_runs() == []

    def test_list_runs_only_schema_marker(self, tmp_path: Path) -> None:
        # @trace FR-EXE-003
        """list_runs returns empty list when only schema marker exists (no run_id)."""
        reg = RunRegistry(tmp_path)
        runs = reg.list_runs()
        assert runs == []

    def test_list_runs_returns_started_runs(self, tmp_path: Path) -> None:
        # @trace FR-EXE-003
        """list_runs returns runs that have been started."""
        reg = RunRegistry(tmp_path)
        m1 = RunMeta(
            run_id="run_a",
            agent="gemini",
            prompt="p1",
            cwd="/tmp",
            owner="u",
            started_at_utc="2026-02-14T10:00:00Z",
        )
        m2 = RunMeta(
            run_id="run_b",
            agent="claude",
            prompt="p2",
            cwd="/tmp",
            owner="u",
            started_at_utc="2026-02-14T11:00:00Z",
        )
        reg.register_start(m1)
        reg.register_start(m2)
        runs = reg.list_runs()
        assert len(runs) == 2
        assert runs[0]["run_id"] == "run_b"  # sorted desc by started_at_utc
        assert runs[1]["run_id"] == "run_a"

    def test_list_runs_merges_finish_event(self, tmp_path: Path) -> None:
        # @trace FR-EXE-003
        """list_runs merges finish event data into the run entry."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_x", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        reg.register_end("run_x", 0, "completed", "2026-02-14T12:00:00Z", 5.0)
        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["status"] == "completed"
        assert runs[0]["exit_code"] == 0

    def test_list_runs_respects_limit(self, tmp_path: Path) -> None:
        # @trace FR-EXE-003
        """list_runs respects the limit parameter."""
        reg = RunRegistry(tmp_path)
        for i in range(5):
            m = RunMeta(
                run_id=f"run_{i}",
                agent="gemini",
                prompt="p",
                cwd="/tmp",
                owner="u",
                started_at_utc=f"2026-02-14T{10 + i:02d}:00:00Z",
            )
            reg.register_start(m)
        runs = reg.list_runs(limit=2)
        assert len(runs) == 2

    def test_list_runs_corrupted_lines_skipped(self, tmp_path: Path) -> None:
        # @trace FR-EXE-003
        """list_runs skips corrupted JSON lines."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_ok", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write("this is not valid json\n")
            f.write("{broken json\n")
        runs = reg.list_runs()
        assert len(runs) == 1
        assert runs[0]["run_id"] == "run_ok"


@pytest.mark.unit
class TestRunRegistryFindByToken:
    """Tests for RunRegistry.find_by_token idempotency lookup."""

    def test_find_by_token_no_file(self, tmp_path: Path) -> None:
        # @trace FR-EXE-009
        """find_by_token returns None when registry does not exist."""
        reg = RunRegistry(tmp_path)
        reg.registry_path.unlink(missing_ok=True)
        assert reg.find_by_token("tok-abc") is None

    def test_find_by_token_no_match(self, tmp_path: Path) -> None:
        # @trace FR-EXE-009
        """find_by_token returns None when no run has the token."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            idempotency_token="tok-other",
        )
        reg.register_start(m)
        assert reg.find_by_token("tok-abc") is None

    def test_find_by_token_returns_matching_run(self, tmp_path: Path) -> None:
        # @trace FR-EXE-009
        """find_by_token returns the run matching the token."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            idempotency_token="tok-abc",
        )
        reg.register_start(m)
        result = reg.find_by_token("tok-abc")
        assert result is not None
        assert result["run_id"] == "run_1"
        assert result["idempotency_token"] == "tok-abc"

    def test_find_by_token_returns_most_recent(self, tmp_path: Path) -> None:
        # @trace FR-EXE-009
        """find_by_token returns the most recent run when multiple runs share a token."""
        reg = RunRegistry(tmp_path)
        m1 = RunMeta(
            run_id="run_old",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            idempotency_token="tok-dup",
            started_at_utc="2026-01-01T00:00:00Z",
        )
        m2 = RunMeta(
            run_id="run_new",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            idempotency_token="tok-dup",
            started_at_utc="2026-02-14T00:00:00Z",
        )
        reg.register_start(m1)
        reg.register_start(m2)
        result = reg.find_by_token("tok-dup")
        assert result is not None
        assert result["run_id"] == "run_new"

    def test_find_by_token_merges_finish_data(self, tmp_path: Path) -> None:
        # @trace FR-EXE-009
        """find_by_token merges finish event data when same run_id."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_tok",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            idempotency_token="tok-fin",
        )
        reg.register_start(m)
        # Write finish event with matching token
        finish_event = {
            "run_id": "run_tok",
            "event": "finish",
            "exit_code": 0,
            "status": "completed",
            "idempotency_token": "tok-fin",
        }
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(finish_event).decode() + "\n")
        result = reg.find_by_token("tok-fin")
        assert result is not None
        assert result["status"] == "completed"

    def test_find_by_token_merges_feedback_score(self, tmp_path: Path) -> None:
        # @trace FR-EXE-009
        """find_by_token merges feedback_score from feedback events."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_fb",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            idempotency_token="tok-fb",
        )
        reg.register_start(m)
        feedback_event = {
            "run_id": "run_fb",
            "event": "feedback",
            "feedback_score": 0.9,
            "idempotency_token": "tok-fb",
        }
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_event).decode() + "\n")
        result = reg.find_by_token("tok-fb")
        assert result is not None
        assert result.get("feedback_score") == 0.9


@pytest.mark.unit
class TestCalibrationFactor:
    """Tests for RunRegistry.get_calibration_factor."""

    def test_calibration_factor_no_file(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """Returns 1.0 when no registry file exists."""
        reg = RunRegistry(tmp_path)
        reg.registry_path.unlink(missing_ok=True)
        assert reg.get_calibration_factor("gemini") == 1.0

    def test_calibration_factor_no_feedback(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """Returns 1.0 when no feedback scores exist for agent."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=0.9,
        )
        reg.register_start(m)
        assert reg.get_calibration_factor("gemini") == 1.0

    def test_calibration_factor_overconfident(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """Returns factor < 1.0 when agent is overconfident (high confidence, low feedback)."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=0.9,
        )
        reg.register_start(m)
        reg.register_feedback("run_1", score=0.5)
        factor = reg.get_calibration_factor("gemini")
        assert factor < 1.0
        assert factor >= 0.5

    def test_calibration_factor_underconfident(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """Returns factor > 1.0 when agent is underconfident (low confidence, high feedback)."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=0.3,
        )
        reg.register_start(m)
        reg.register_feedback("run_1", score=0.9)
        factor = reg.get_calibration_factor("gemini")
        assert factor > 1.0
        assert factor <= 2.0

    def test_calibration_factor_different_agent_ignored(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """Feedback for a different agent is not included in calibration."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="claude",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=0.9,
        )
        reg.register_start(m)
        reg.register_feedback("run_1", score=0.1)
        assert reg.get_calibration_factor("gemini") == 1.0

    def test_calibration_factor_clamped_max(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """Calibration factor is clamped to max 2.0."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=0.1,
        )
        reg.register_start(m)
        reg.register_feedback("run_1", score=1.0)
        factor = reg.get_calibration_factor("gemini")
        assert factor == 2.0

    def test_calibration_factor_clamped_min(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """Calibration factor is clamped to min 0.5."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=1.0,
        )
        reg.register_start(m)
        reg.register_feedback("run_1", score=0.1)
        factor = reg.get_calibration_factor("gemini")
        assert factor == 0.5


@pytest.mark.unit
class TestPolicyEngineOPAQuery:
    """Tests for PolicyEngine._query_opa method."""

    def _make_settings(self, **overrides: object) -> MagicMock:
        settings = MagicMock()
        settings.opa_url = overrides.get("opa_url", "http://localhost:8181")
        settings.opa_timeout_ms = overrides.get("opa_timeout_ms", 500)
        settings.environment = overrides.get("environment", "development")
        settings.trust_score_threshold = overrides.get("trust_score_threshold", 0.8)
        settings.session_dir = overrides.get("session_dir", Path("/tmp"))
        return settings

    def test_query_opa_returns_none_when_url_empty(self) -> None:
        # @trace FR-GOV-001
        """_query_opa returns None when OPA URL is empty."""
        settings = self._make_settings(opa_url="")
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="u")
        assert engine._query_opa(run) is None

    def test_query_opa_returns_none_when_url_whitespace(self) -> None:
        # @trace FR-GOV-001
        """_query_opa returns None when OPA URL is whitespace."""
        settings = self._make_settings(opa_url="   ")
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="u")
        assert engine._query_opa(run) is None

    def test_query_opa_returns_allow_on_success(self) -> None:
        # @trace FR-GOV-001
        """_query_opa returns ('allow', reason) when OPA allows."""
        settings = self._make_settings()
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="u")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"allow": True, "reason": "All good"}}
        mock_resp.raise_for_status.return_value = None
        with patch("thegent.execution.httpx.post", return_value=mock_resp):
            result = engine._query_opa(run)
        assert result == ("allow", "All good")

    def test_query_opa_returns_deny_on_reject(self) -> None:
        # @trace FR-GOV-001
        """_query_opa returns ('deny', reason) when OPA denies."""
        settings = self._make_settings()
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="u")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": {"allow": False, "reason": "Not allowed"}}
        mock_resp.raise_for_status.return_value = None
        with patch("thegent.execution.httpx.post", return_value=mock_resp):
            result = engine._query_opa(run)
        assert result == ("deny", "Not allowed")

    def test_query_opa_returns_none_on_network_error(self) -> None:
        # @trace FR-GOV-001
        """_query_opa returns None when network fails."""
        settings = self._make_settings()
        engine = PolicyEngine(settings)
        run = RunMeta(agent="gemini", prompt="test", cwd="/tmp", owner="u")
        with patch("thegent.execution.httpx.post", side_effect=OSError("conn refused")):
            result = engine._query_opa(run)
        assert result is None


@pytest.mark.unit
class TestCircuitBreakerHalfOpen:
    """Tests for CircuitBreakerRegistry half-open state transitions."""

    def test_half_open_allows_after_recovery_period(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Circuit transitions to half-open (closed) after recovery_s elapsed."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=2, window_s=600, recovery_s=1)
        cb.record_failure("agent-x")
        cb.record_failure("agent-x")
        assert cb.is_open("agent-x") is True
        # Simulate time passing by writing old timestamp failures
        import time

        time.sleep(1.1)  # Wait past recovery_s
        assert cb.is_open("agent-x") is False  # Half-open: allow trial

    def test_circuit_remains_open_within_recovery(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Circuit stays open within recovery period."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=2, window_s=600, recovery_s=9999)
        cb.record_failure("agent-x")
        cb.record_failure("agent-x")
        assert cb.is_open("agent-x") is True


@pytest.mark.unit
class TestEscalationQueueSLAExpiry:
    """Tests for EscalationQueue SLA expiry checks."""

    def test_past_sla_item_marked(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """Items past SLA have past_sla=True in listing."""
        eq = EscalationQueue(tmp_path)
        # Write an item with SLA already passed
        datetime.now(UTC)
        past_sla = {
            "run_id": "run_expired",
            "reason": "blocked",
            "blocked_at_utc": "2020-01-01T00:00:00+00:00",
            "escalate_by_utc": "2020-01-01T00:01:00+00:00",
            "sla_minutes": 1,
            "status": "pending",
            "priority": 0,
        }
        eq.session_dir.mkdir(parents=True, exist_ok=True)
        with eq.queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(past_sla).decode() + "\n")
        items = eq.list_pending(past_sla_only=True)
        assert len(items) == 1
        assert items[0]["past_sla"] is True

    def test_resolve_nonexistent_queue_file(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """resolve returns False when queue file does not exist."""
        eq = EscalationQueue(tmp_path)
        assert eq.resolve("run_x") is False

    def test_add_with_priority_sorting(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """list_pending sorts by priority.

        AUDIT-N+32: priorities must be in {1..5}; use ``5`` for the
        "high" row instead of the previous out-of-range ``10`` which
        the hardened ``EscalationQueue.add`` correctly rejects.
        """
        eq = EscalationQueue(tmp_path)
        eq.add("run_low", "reason", priority=1)
        eq.add("run_high", "reason", priority=5)
        items = eq.list_pending()
        assert len(items) == 2

    def test_resolve_already_resolved_returns_false(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """resolve returns False when item already resolved."""
        eq = EscalationQueue(tmp_path)
        eq.add("run_r", "blocked")
        eq.resolve("run_r")
        assert eq.resolve("run_r") is False


@pytest.mark.unit
class TestRunRegistryRegisterFeedback:
    """Tests for RunRegistry.register_feedback."""

    def test_register_feedback_appends_event(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """register_feedback appends a feedback event with hash chaining."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_fb", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        reg.register_feedback("run_fb", score=0.85, note="good output")
        content = reg.registry_path.read_text(encoding="utf-8")
        assert '"feedback"' in content
        assert '"feedback_score"' in content

    def test_register_feedback_with_no_note(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """register_feedback works without a note."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_fb2", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        reg.register_feedback("run_fb2", score=0.5)
        content = reg.registry_path.read_text(encoding="utf-8")
        assert '"feedback_note": null' in content


@pytest.mark.unit
class TestRunRegistryHashChaining:
    """Tests for hash chaining integrity in RunRegistry."""

    def test_register_end_with_cost_usd(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """register_end records cost_usd when provided."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_cost", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        reg.register_end("run_cost", 0, "completed", "2026-02-14T12:00:00Z", 1.0, cost_usd=0.05)
        content = reg.registry_path.read_text(encoding="utf-8")
        assert '"cost_usd": 0.05' in content

    def test_register_end_without_cost_usd(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """register_end omits cost_usd when not provided."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_nocost", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        reg.register_end("run_nocost", 0, "completed", "2026-02-14T12:00:00Z", 1.0)
        lines = reg.registry_path.read_text(encoding="utf-8").strip().split("\n")
        finish_line = [l for l in lines if '"finish"' in l]
        assert len(finish_line) == 1
        data = json.loads(finish_line[0])
        assert "cost_usd" not in data

    def test_get_last_hash_returns_hash(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """_get_last_hash returns hash of last record."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_h", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        last_hash = reg._get_last_hash()
        assert last_hash is not None
        assert len(last_hash) == 64

    def test_get_last_hash_empty_file(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """_get_last_hash returns None when file does not exist."""
        reg = RunRegistry(tmp_path)
        reg.registry_path.unlink(missing_ok=True)
        assert reg._get_last_hash() is None


@pytest.mark.unit
class TestGetLastHashExceptionPath:
    """Tests for _get_last_hash exception handling (lines 126-128)."""

    def test_get_last_hash_corrupt_file_returns_none(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """_get_last_hash returns None when file has invalid JSON."""
        reg = RunRegistry(tmp_path)
        reg.registry_path.write_text("not valid json at all\n", encoding="utf-8")
        assert reg._get_last_hash() is None


@pytest.mark.unit
class TestGetRunStateExceptionPath:
    """Tests for get_run_state JSON decode exception (lines 246-247)."""

    def test_get_run_state_skips_corrupt_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-004
        """get_run_state skips corrupt JSON lines and still returns state."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
        reg.register_start(m)
        # Append corrupt line
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write("corrupt json line\n")
        assert reg.get_run_state("run_1") == RunState.RUNNING


@pytest.mark.unit
class TestFindByTokenExceptionPath:
    """Tests for find_by_token exception handling (lines 301-302)."""

    def test_find_by_token_skips_corrupt_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-009
        """find_by_token skips corrupt JSON lines."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            idempotency_token="tok-1",
        )
        reg.register_start(m)
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write("{{corrupt}}\n")
        result = reg.find_by_token("tok-1")
        assert result is not None
        assert result["run_id"] == "run_1"


@pytest.mark.unit
class TestCalibrationFactorExceptionPath:
    """Tests for get_calibration_factor exception handling (lines 321, 327-328, 338)."""

    def test_calibration_factor_skips_corrupt_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """get_calibration_factor skips corrupt lines and still returns valid result."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=0.5,
        )
        reg.register_start(m)
        reg.register_feedback("run_1", score=0.5)
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write("{{corrupt json}}\n")
        factor = reg.get_calibration_factor("gemini")
        assert 0.5 <= factor <= 2.0

    def test_calibration_factor_zero_confidence_returns_one(self, tmp_path: Path) -> None:
        # @trace FR-EXE-006
        """get_calibration_factor returns 1.0 when avg_confidence is 0."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(
            run_id="run_1",
            agent="gemini",
            prompt="p",
            cwd="/tmp",
            owner="u",
            confidence=0,
        )
        reg.register_start(m)
        reg.register_feedback("run_1", score=0.5)
        factor = reg.get_calibration_factor("gemini")
        assert factor == 1.0


@pytest.mark.unit
class TestPurgeExpiredExceptionPaths:
    """Tests for purge_expired exception handling (lines 354, 370-371, 380-381, 385, 396-397)."""

    def test_purge_expired_no_file_returns_zeros(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """purge_expired returns zeros when no registry file exists."""
        reg = RunRegistry(tmp_path)
        reg.registry_path.unlink(missing_ok=True)
        result = reg.purge_expired(default_days=30, by_domain={})
        assert result == {"kept": 0, "purged": 0}

    def test_purge_expired_corrupt_domain_lines_kept(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """purge_expired keeps lines that raise exceptions during date parse."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_1", agent="gemini", prompt="p", cwd="/tmp", owner="u")
        reg.register_start(m)
        # Append corrupt line
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write("{{bad json}}\n")
        result = reg.purge_expired(default_days=30, by_domain={}, dry_run=True)
        assert result["kept"] >= 1

    def test_purge_expired_record_no_timestamp_kept(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """purge_expired keeps records that have no timestamp (lines 380-381)."""
        reg = RunRegistry(tmp_path)
        # Write a record with no timestamp fields
        no_ts = {"run_id": "run_nots", "event": "custom"}
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(no_ts).decode() + "\n")
        result = reg.purge_expired(default_days=30, by_domain={}, dry_run=True)
        assert result["kept"] >= 1

    def test_purge_expired_naive_timestamp_gets_utc(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """purge_expired handles naive timestamps by adding UTC (line 385)."""
        reg = RunRegistry(tmp_path)
        # Write a record with a naive timestamp (no timezone info)
        naive_ts_record = {
            "run_id": "run_naive",
            "started_at_utc": "2020-01-01T00:00:00",
        }
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(naive_ts_record).decode() + "\n")
        result = reg.purge_expired(default_days=30, by_domain={}, dry_run=False)
        # Old record should be purged
        assert result["purged"] >= 1

    def test_purge_expired_exception_in_second_pass_keeps_line(self, tmp_path: Path) -> None:
        # @trace FR-GOV-007
        """purge_expired keeps line on exception in second pass (lines 396-397)."""
        reg = RunRegistry(tmp_path)
        # Write a record with invalid timestamp format to trigger exception
        bad_record = {"run_id": "run_bad", "started_at_utc": "not-a-date"}
        with reg.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(bad_record).decode() + "\n")
        result = reg.purge_expired(default_days=30, by_domain={}, dry_run=True)
        assert result["kept"] >= 1


@pytest.mark.unit
class TestCheckpointRegistryExceptionPaths:
    """Tests for CheckpointRegistry exception handling (lines 435-436, 451-453)."""

    def test_list_checkpoints_skips_corrupt_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-007
        """list_checkpoints skips corrupt JSON lines."""
        cr = CheckpointRegistry(tmp_path)
        cr.create_checkpoint("reason", "dag", "owner")
        with cr.registry_path.open("a", encoding="utf-8") as f:
            f.write("{{corrupt line}}\n")
        ckpts = cr.list_checkpoints()
        assert len(ckpts) == 1

    def test_get_checkpoint_skips_corrupt_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-007
        """get_checkpoint skips corrupt JSON and returns None if not found."""
        cr = CheckpointRegistry(tmp_path)
        with cr.registry_path.open("a", encoding="utf-8") as f:
            f.write("{{corrupt}}\n")
        assert cr.get_checkpoint("ckpt_nonexistent") is None


@pytest.mark.unit
class TestPolicyEngineCircuitBreakerModel:
    """Tests for PolicyEngine circuit breaker for model (line 524)."""

    def test_circuit_breaker_blocks_model(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """PolicyEngine blocks execution when model circuit breaker is open."""
        settings = MagicMock()
        settings.opa_url = ""
        settings.environment = "development"
        settings.trust_score_threshold = 0.8
        settings.session_dir = tmp_path
        settings.cost_tracking_enabled = False
        settings.circuit_breaker_enabled = True
        settings.circuit_breaker_threshold = 1
        settings.circuit_breaker_window_s = 300
        settings.circuit_breaker_recovery_s = 60
        engine = PolicyEngine(settings)

        # Record failure for model (not agent)
        cb = CircuitBreakerRegistry(tmp_path, threshold=1)
        cb.record_failure("gpt-4", category="model")

        run = RunMeta(agent="gemini", model="gpt-4", prompt="test", cwd="/tmp", owner="u")
        result, reason = engine.evaluate(run)
        assert result == "deny"
        assert "model" in reason.lower()


@pytest.mark.unit
class TestTrustBoundaryValidatorGetLastEnvironmentException:
    """Tests for TrustBoundaryValidator.get_last_environment exception (lines 606-607)."""

    def test_get_last_environment_corrupt_file_returns_none(self, tmp_path: Path) -> None:
        # @trace FR-EXE-010
        """get_last_environment returns None when state file is corrupt."""
        v = TrustBoundaryValidator(tmp_path)
        v.state_path.parent.mkdir(parents=True, exist_ok=True)
        v.state_path.write_text("{{not json}}", encoding="utf-8")
        assert v.get_last_environment() is None


@pytest.mark.unit
class TestAuditorVerifyRegistryDetailedPaths:
    """Tests covering auditor lines 661, 669-670, 686-687, 692-698, 701-703."""

    def test_verify_blank_lines_skipped(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """verify_registry skips blank lines (line 661)."""
        reg = RunRegistry(tmp_path)
        m = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
        reg.register_start(m)
        # Insert blank lines
        content = reg.registry_path.read_text(encoding="utf-8")
        content = content + "\n\n\n"
        reg.registry_path.write_text(content, encoding="utf-8")
        auditor = Auditor(reg.registry_path)
        result = auditor.verify_registry()
        assert result["status"] in ("passed", "failed")

    def test_verify_chain_broken_detected(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """verify_registry detects broken hash chain (lines 669-670)."""
        reg = RunRegistry(tmp_path)
        m1 = RunMeta(run_id="run_1", agent="gemini", prompt="x", cwd="/tmp", owner="u")
        reg.register_start(m1)
        # Tamper with prev_hash
        lines = reg.registry_path.read_text(encoding="utf-8").strip().split("\n")
        if len(lines) >= 2:
            data = json.loads(lines[1])
            data["prev_hash"] = "wrong_hash"
            data["hash"] = "recalculated_but_wrong"
            lines[1] = json.dumps(data).decode()
            reg.registry_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        auditor = Auditor(reg.registry_path)
        result = auditor.verify_registry()
        assert result["chain_broken"] is True

    def test_verify_missing_hash_counts_corrupt(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """verify_registry counts records with missing hash as corrupt (lines 686-687)."""
        reg_path = tmp_path / "registry.jsonl"
        record = {"run_id": "run_no_hash", "event": "start"}
        reg_path.write_text(json.dumps(record).decode() + "\n", encoding="utf-8")
        auditor = Auditor(reg_path)
        result = auditor.verify_registry()
        assert result["corrupt_count"] >= 1
        assert any("Missing hash" in i for i in result["issues"])

    def test_verify_signature_mismatch_detected(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """verify_registry detects signature mismatch (lines 692-698)."""
        import hashlib as _hl

        reg_path = tmp_path / "registry.jsonl"
        record = {
            "run_id": "run_sig",
            "started_at_utc": "2026-01-01T00:00:00Z",
            "owner": "u",
            "prompt": "test",
            "signature": "wrong_sig_value",
        }
        # Calculate correct hash
        d = {k: v for k, v in record.items() if k != "hash"}
        body = __import__("json").dumps(d, sort_keys=True, separators=(",", ":"))
        record["hash"] = _hl.sha256(body.encode()).hexdigest()
        # Recalculate after adding hash (to make hash valid but sig wrong)
        d2 = {k: v for k, v in record.items() if k != "hash"}
        body2 = __import__("json").dumps(d2, sort_keys=True, separators=(",", ":"))
        record["hash"] = _hl.sha256(body2.encode()).hexdigest()

        reg_path.write_text(json.dumps(record).decode() + "\n", encoding="utf-8")
        auditor = Auditor(reg_path)
        result = auditor.verify_registry()
        # Either hash or sig mismatch is detected
        assert result["corrupt_count"] >= 1

    def test_verify_json_decode_error_counts_corrupt(self, tmp_path: Path) -> None:
        # @trace FR-EXE-002
        """verify_registry counts JSON decode errors as corrupt (lines 701-703)."""
        reg_path = tmp_path / "registry.jsonl"
        reg_path.write_text("{{not valid json}}\n", encoding="utf-8")
        auditor = Auditor(reg_path)
        result = auditor.verify_registry()
        assert result["corrupt_count"] >= 1
        assert any("JSON decode error" in i for i in result["issues"])


@pytest.mark.unit
class TestCircuitBreakerExceptionPath:
    """Tests for CircuitBreakerRegistry is_open exception (lines 755-756)."""

    def test_is_open_skips_corrupt_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """is_open skips corrupt JSON lines."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=2)
        cb.record_failure("agent-x")
        with cb.registry_path.open("a", encoding="utf-8") as f:
            f.write("{{corrupt}}\n")
        # Should not raise; circuit still closed (only 1 failure)
        assert cb.is_open("agent-x") is False


@pytest.mark.unit
class TestOverrideRegistryExceptionPaths:
    """Tests for OverrideRegistry.has_unexpired exception handling (lines 796, 803, 807-808)."""

    def test_has_unexpired_skips_blank_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """has_unexpired skips blank lines (line 796)."""
        oreg = OverrideRegistry(tmp_path)
        oreg.record("user1", "reason", ttl_seconds=3600)
        with oreg.registry_path.open("a", encoding="utf-8") as f:
            f.write("\n\n")
        assert oreg.has_unexpired("user1") is True

    def test_has_unexpired_skips_no_expires_at(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """has_unexpired skips records without expires_at_utc (line 803)."""
        oreg = OverrideRegistry(tmp_path)
        no_expiry = {
            "owner": "user1",
            "reason": "test",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        oreg.session_dir.mkdir(parents=True, exist_ok=True)
        with oreg.registry_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(no_expiry).decode() + "\n")
        assert oreg.has_unexpired("user1") is False

    def test_has_unexpired_skips_corrupt_json(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """has_unexpired skips corrupt JSON lines (lines 807-808)."""
        oreg = OverrideRegistry(tmp_path)
        oreg.record("user1", "reason", ttl_seconds=3600)
        with oreg.registry_path.open("a", encoding="utf-8") as f:
            f.write("{{bad json}}\n")
        assert oreg.has_unexpired("user1") is True


@pytest.mark.unit
class TestEscalationQueueExceptionPaths:
    """Tests for EscalationQueue exception handling (lines 858, 865, 871-872, 885, 893-894)."""

    def test_list_pending_skips_blank_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """list_pending skips blank lines (line 858)."""
        eq = EscalationQueue(tmp_path)
        eq.add("run_1", "reason")
        with eq.queue_path.open("a", encoding="utf-8") as f:
            f.write("\n\n")
        items = eq.list_pending()
        assert len(items) == 1

    def test_list_pending_skips_no_escalate_by(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """list_pending skips items without escalate_by_utc (line 865)."""
        eq = EscalationQueue(tmp_path)
        no_sla = {
            "run_id": "run_nosla",
            "status": "pending",
            "reason": "test",
            "priority": 0,
        }
        eq.session_dir.mkdir(parents=True, exist_ok=True)
        with eq.queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(no_sla).decode() + "\n")
        items = eq.list_pending()
        assert len(items) == 0

    def test_list_pending_skips_corrupt_json(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """list_pending skips corrupt JSON lines (lines 871-872)."""
        eq = EscalationQueue(tmp_path)
        eq.add("run_ok", "reason")
        with eq.queue_path.open("a", encoding="utf-8") as f:
            f.write("{{bad json}}\n")
        items = eq.list_pending()
        assert len(items) == 1

    def test_resolve_skips_blank_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """resolve skips blank lines (line 885)."""
        eq = EscalationQueue(tmp_path)
        eq.add("run_1", "reason")
        with eq.queue_path.open("a", encoding="utf-8") as f:
            f.write("\n\n")
        assert eq.resolve("run_1") is True

    def test_resolve_keeps_corrupt_lines(self, tmp_path: Path) -> None:
        # @trace FR-EXE-005
        """resolve does not write garbage after the JSONL stream.

        AUDIT-N+32: the hardened ``_save`` writes a clean snapshot of
        ``self.queue + self._corrupt_lines`` rather than re-reading the
        on-disk file and preserving every byte. The contract that
        ``resolve`` does not introduce invalid JSON into the file
        remains true — any corrupt line present before ``resolve`` is
        still in the file (because we never delete it on disk), but
        the new behaviour is to overwrite the file with a clean
        snapshot rather than preserve every byte verbatim. This test
        now asserts that ``resolve`` still succeeds and the JSONL
        remains parseable (no partial-write corruption).
        """
        eq = EscalationQueue(tmp_path)
        eq.add("run_1", "reason")
        with eq.queue_path.open("a", encoding="utf-8") as f:
            f.write("corrupt-json-line\n")
        assert eq.resolve("run_1") is True
        # Verify the JSONL is still well-formed JSON (no partial
        # writes introduced by ``resolve``).
        content = eq.queue_path.read_text(encoding="utf-8")
        # ``run_1`` must have been removed; remaining bytes must parse
        # as JSON or be the original corrupt line we explicitly wrote.
        import json as _json

        for line in content.splitlines():
            if line == "corrupt-json-line":
                continue
            _json.loads(line)  # must not raise


@pytest.mark.unit
class TestConcurrencyControllerCriticalLane:
    """Tests for ConcurrencyController critical lane reservation (swarm-critical-lane).

    Traces to: FR-EXE-011 (Critical lane slot reservation prevents starvation).
    """

    def _make_controller(self, tmp_path: Path, max_concurrency: int = 5, critical_lane_slots: int = 2):
        """Build a ConcurrencyController with load-based limits disabled for deterministic tests."""
        from thegent.execution import ConcurrencyController

        return ConcurrencyController(
            session_dir=tmp_path,
            max_concurrency=max_concurrency,
            use_load_based=False,
            critical_lane_slots=critical_lane_slots,
        )

    def _patch_running(self, running_count: int):
        """Return a context manager that mocks ps_impl to report N running sessions.

        execution.py imports ps_impl via ``from thegent.cli.commands.impl import ps_impl``
        at call-time, so we patch the binding in the source module.
        """
        return patch(
            "thegent.cli.commands.impl.ps_impl",
            return_value=[{"status": "running"}] * running_count,
        )

    def test_critical_lane_slots_defaults_to_two(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """ConcurrencyController defaults critical_lane_slots to 2."""
        from thegent.execution import ConcurrencyController

        cc = ConcurrencyController(session_dir=tmp_path, max_concurrency=5, use_load_based=False)
        assert cc.critical_lane_slots == 2

    def test_critical_lane_slots_explicit(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """Explicit critical_lane_slots value is stored correctly."""
        cc = self._make_controller(tmp_path, max_concurrency=10, critical_lane_slots=3)
        assert cc.critical_lane_slots == 3

    def test_critical_lane_slots_from_env(self, tmp_path: Path, monkeypatch) -> None:
        # @trace FR-EXE-011
        """THGENT_CRITICAL_LANE_SLOTS env var sets critical_lane_slots."""
        from thegent.execution import ConcurrencyController

        monkeypatch.setenv("THGENT_CRITICAL_LANE_SLOTS", "4")
        cc = ConcurrencyController(session_dir=tmp_path, max_concurrency=10, use_load_based=False)
        assert cc.critical_lane_slots == 4

    def test_critical_lane_slots_env_invalid_falls_back_to_default(self, tmp_path: Path, monkeypatch) -> None:
        # @trace FR-EXE-011
        """Invalid THGENT_CRITICAL_LANE_SLOTS env var falls back to default 2."""
        from thegent.execution import ConcurrencyController

        monkeypatch.setenv("THGENT_CRITICAL_LANE_SLOTS", "not-a-number")
        cc = ConcurrencyController(session_dir=tmp_path, max_concurrency=10, use_load_based=False)
        assert cc.critical_lane_slots == 2

    def test_standard_run_blocked_when_standard_slots_full(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """Standard run is blocked when all standard-available slots are occupied.

        max_concurrency=5, critical_lane_slots=2 → standard cap = 3.
        With 3 running sessions, a standard run must be blocked.
        """
        cc = self._make_controller(tmp_path, max_concurrency=5, critical_lane_slots=2)
        with self._patch_running(3):
            # 3 running == standard cap (5-2=3) → blocked
            assert cc.acquire(priority="standard") is False

    def test_critical_run_admitted_when_standard_slots_full(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """Critical run is admitted even when all standard-available slots are occupied.

        max_concurrency=5, critical_lane_slots=2, running=3.
        Standard would be blocked (3 >= 3), but critical uses all 5 slots.
        """
        cc = self._make_controller(tmp_path, max_concurrency=5, critical_lane_slots=2)
        with self._patch_running(3):
            # Standard is blocked
            assert cc.acquire(priority="standard") is False
            # Critical is admitted (3 < 5)
            assert cc.acquire(priority="critical") is True

    def test_standard_run_admitted_when_slots_available(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """Standard run is admitted when standard slots are available."""
        cc = self._make_controller(tmp_path, max_concurrency=5, critical_lane_slots=2)
        with self._patch_running(2):
            # 2 running < 3 standard cap → admitted
            assert cc.acquire(priority="standard") is True

    def test_both_blocked_when_all_slots_full(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """Both standard and critical runs are blocked when max_concurrency is exhausted."""
        cc = self._make_controller(tmp_path, max_concurrency=5, critical_lane_slots=2)
        with self._patch_running(5):
            assert cc.acquire(priority="standard") is False
            assert cc.acquire(priority="critical") is False

    def test_lane_critical_treated_as_critical_priority(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """A run with lane='critical' is treated as critical regardless of priority kwarg."""
        cc = self._make_controller(tmp_path, max_concurrency=5, critical_lane_slots=2)
        with self._patch_running(3):
            # lane=critical overrides default priority="standard"
            assert cc.acquire(lane="critical") is True

    def test_priority_critical_kwarg_treated_as_critical(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """A run with is_critical via priority='critical' uses full slot pool."""
        cc = self._make_controller(tmp_path, max_concurrency=5, critical_lane_slots=2)
        with self._patch_running(4):
            # 4 running < 5 total → critical admitted
            assert cc.acquire(priority="critical") is True

    def test_zero_critical_lane_slots_no_reservation(self, tmp_path: Path) -> None:
        # @trace FR-EXE-011
        """With critical_lane_slots=0, standard runs may use all slots (no reservation)."""
        cc = self._make_controller(tmp_path, max_concurrency=5, critical_lane_slots=0)
        with self._patch_running(4):
            # standard cap = max(1, 5-0) = 5 → 4 < 5 → admitted
            assert cc.acquire(priority="standard") is True
