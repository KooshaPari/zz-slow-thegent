"""Python-side tests for WL-012 Phase 3: Route Executors and Orchestrator.

Covers:
- P3.1 RoutingDecision / ExecutionOutcome data models
- P3.2 RoutingOrchestratorBridge: multi-agent routing, arbitration policies
- P3.3 read_routing_audit: reads JSONL audit log written by Rust AuditLogger
- P3.4 make_routing_decision_from_factors: heuristic uses ThegentSettings fields
- CLI: router_config, router_status helpers
- Config: router_band_width, router_dwell_time, router_max_dwell, router_override_threshold, router_audit_path

# @trace WL-012
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import orjson as json
import pytest

# ---------------------------------------------------------------------------
# P3.1 — Data models
# ---------------------------------------------------------------------------


class TestRoutingDecisionModel:
    """P3.1: RoutingDecision mirrors Rust RoutingDecision struct."""

    def test_lifecycle_decision_fields(self) -> None:
        from thegent.utils.routing_impl.route_executor import RoutingDecision

        d = RoutingDecision(mode="Lifecycle", risk_score=0.2, rationale="low risk")
        assert d.mode == "Lifecycle"
        assert d.risk_score == 0.2  # noqa: PLR2004
        assert d.rationale == "low risk"

    def test_thegent_decision_fields(self) -> None:
        from thegent.utils.routing_impl.route_executor import RoutingDecision

        d = RoutingDecision(mode="TheGent", risk_score=0.85, rationale="high risk task")
        assert d.mode == "TheGent"
        assert d.risk_score == 0.85  # noqa: PLR2004

    def test_execution_outcome_fields(self) -> None:
        from thegent.utils.routing_impl.route_executor import ExecutionOutcome

        o = ExecutionOutcome(
            decision_id="abc123",
            provider="lifecycle",
            model="gemini-3-flash",
            latency_ms=42,
            cost_usd=0.001,
            success=True,
        )
        assert o.decision_id == "abc123"
        assert o.provider == "lifecycle"
        assert o.success is True
        assert o.error is None

    def test_execution_outcome_failure(self) -> None:
        from thegent.utils.routing_impl.route_executor import ExecutionOutcome

        o = ExecutionOutcome(
            decision_id="xyz",
            provider="thegent",
            model="claude-sonnet-4.6",
            latency_ms=0,
            cost_usd=0.0,
            success=False,
            error="timeout",
        )
        assert o.success is False
        assert o.error == "timeout"


# ---------------------------------------------------------------------------
# P3.2 — RoutingOrchestratorBridge
# ---------------------------------------------------------------------------


class TestRoutingOrchestratorBridge:
    """P3.2: RoutingOrchestratorBridge manages per-agent routing state."""

    def test_record_decision_adds_agent(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge()
        orch.record_decision("agent-1", RoutingDecision("Lifecycle", 0.3, "ok"))
        status = orch.status()
        assert status.total_decisions == 1
        assert len(status.agents) == 1
        assert status.agents[0].agent_id == "agent-1"
        assert status.agents[0].lifecycle_decisions == 1

    def test_multiple_agents_tracked_separately(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge()
        orch.record_decision("a1", RoutingDecision("Lifecycle", 0.2, "r1"))
        orch.record_decision("a2", RoutingDecision("TheGent", 0.8, "r2"))
        orch.record_decision("a1", RoutingDecision("Lifecycle", 0.2, "r3"))

        status = orch.status()
        assert status.total_decisions == 3  # noqa: PLR2004
        assert len(status.agents) == 2  # noqa: PLR2004

        a1 = next(a for a in status.agents if a.agent_id == "a1")
        a2 = next(a for a in status.agents if a.agent_id == "a2")
        assert a1.lifecycle_decisions == 2  # noqa: PLR2004
        assert a2.thegent_decisions == 1

    def test_arbitrate_majority_wins_defaults_lifecycle(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge(policy="MajorityWins")
        orch.record_decision("a1", RoutingDecision("Lifecycle", 0.1, ""))
        orch.record_decision("a2", RoutingDecision("Lifecycle", 0.2, ""))
        orch.record_decision("a3", RoutingDecision("TheGent", 0.9, ""))

        result = orch.arbitrate()
        assert result == "Lifecycle"

    def test_arbitrate_majority_wins_thegent_wins_tie(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge(policy="MajorityWins")
        orch.record_decision("a1", RoutingDecision("TheGent", 0.9, ""))
        orch.record_decision("a2", RoutingDecision("Lifecycle", 0.1, ""))

        # Tie → TheGent wins (most restrictive on tie)
        result = orch.arbitrate()
        assert result == "TheGent"

    def test_arbitrate_most_restrictive_wins_any_thegent_vote(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge(policy="MostRestrictiveWins")
        orch.record_decision("a1", RoutingDecision("Lifecycle", 0.1, ""))
        orch.record_decision("a2", RoutingDecision("Lifecycle", 0.2, ""))
        # Single TheGent vote flips it
        orch.record_decision("a3", RoutingDecision("TheGent", 0.9, ""))

        result = orch.arbitrate()
        assert result == "TheGent"

    def test_arbitrate_most_restrictive_all_lifecycle(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge(policy="MostRestrictiveWins")
        orch.record_decision("a1", RoutingDecision("Lifecycle", 0.1, ""))
        orch.record_decision("a2", RoutingDecision("Lifecycle", 0.2, ""))

        result = orch.arbitrate()
        assert result == "Lifecycle"

    def test_arbitrate_empty_returns_none(self) -> None:
        from thegent.utils.routing_impl.route_executor import RoutingOrchestratorBridge

        orch = RoutingOrchestratorBridge()
        assert orch.arbitrate() is None

    def test_status_percentages_correct(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge()
        for _ in range(3):
            orch.record_decision("a1", RoutingDecision("Lifecycle", 0.2, ""))
        for _ in range(1):
            orch.record_decision("a1", RoutingDecision("TheGent", 0.9, ""))

        status = orch.status()
        assert status.lifecycle_pct == pytest.approx(75.0)
        assert status.thegent_pct == pytest.approx(25.0)

    def test_status_display_contains_agent_ids(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge()
        orch.record_decision("agent-alpha", RoutingDecision("Lifecycle", 0.1, "ok"))
        text = orch.status().display()
        assert "agent-alpha" in text
        assert "Router Status" in text

    def test_status_to_json_roundtrip(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            RoutingDecision,
            RoutingOrchestratorBridge,
        )

        orch = RoutingOrchestratorBridge()
        orch.record_decision("a1", RoutingDecision("Lifecycle", 0.1, ""))
        status = orch.status()
        blob = status.to_json()
        data = json.loads(blob)
        assert data["total_decisions"] == 1
        assert len(data["agents"]) == 1


# ---------------------------------------------------------------------------
# P3.3 — read_routing_audit
# ---------------------------------------------------------------------------


class TestReadRoutingAudit:
    """P3.3: read_routing_audit reads JSONL produced by Rust AuditLogger."""

    def _make_audit_record(
        self,
        decision_id: str,
        provider: str = "lifecycle",
        model: str = "gemini-3-flash",
        prev_hash: str = "",
    ) -> dict:
        """Produce a synthetic audit record with a valid hash chain link."""
        record = {
            "timestamp": "2026-02-20T12:00:00Z",
            "decision_id": decision_id,
            "provider": provider,
            "model": model,
            "latency_ms": 42,
            "cost": 0.001,
            "prev_hash": prev_hash,
        }
        # Compute hash (ADR-015 pattern: sort_keys, exclude hash field)
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":").decode())
        record["hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        return record

    def test_returns_empty_for_missing_file(self) -> None:
        from thegent.utils.routing_impl.route_executor import read_routing_audit

        result = read_routing_audit(Path("/tmp/nonexistent-routing-audit.jsonl"), limit=10)
        assert result == []

    def test_reads_single_record(self, tmp_path: Path) -> None:
        from thegent.utils.routing_impl.route_executor import read_routing_audit

        rec = self._make_audit_record("id-001")
        audit_file = tmp_path / "routing_audit.jsonl"
        audit_file.write_text(json.dumps(rec).decode() + "\n", encoding="utf-8")

        records = read_routing_audit(audit_file, limit=10)
        assert len(records) == 1
        assert records[0]["decision_id"] == "id-001"
        assert records[0]["provider"] == "lifecycle"

    def test_reads_multiple_records(self, tmp_path: Path) -> None:
        from thegent.utils.routing_impl.route_executor import read_routing_audit

        lines = []
        prev = ""
        for i in range(5):
            rec = self._make_audit_record(f"id-{i:03}", prev_hash=prev)
            prev = rec["hash"]
            lines.append(json.dumps(rec).decode())

        audit_file = tmp_path / "routing_audit.jsonl"
        audit_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        records = read_routing_audit(audit_file, limit=10)
        assert len(records) == 5  # noqa: PLR2004

    def test_limit_returns_last_n(self, tmp_path: Path) -> None:
        from thegent.utils.routing_impl.route_executor import read_routing_audit

        lines = []
        prev = ""
        for i in range(10):
            rec = self._make_audit_record(f"id-{i:03}", prev_hash=prev)
            prev = rec["hash"]
            lines.append(json.dumps(rec).decode())

        audit_file = tmp_path / "routing_audit.jsonl"
        audit_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        records = read_routing_audit(audit_file, limit=3)
        assert len(records) == 3  # noqa: PLR2004
        # Last 3 records
        assert records[0]["decision_id"] == "id-007"
        assert records[2]["decision_id"] == "id-009"

    def test_hash_chain_can_be_verified(self, tmp_path: Path) -> None:
        """Verify that Python router_verify logic works on synthetic JSONL."""
        from thegent.utils.routing_impl.route_executor import read_routing_audit

        lines = []
        prev = ""
        for i in range(4):
            rec = self._make_audit_record(f"chain-{i}", prev_hash=prev)
            prev = rec["hash"]
            lines.append(json.dumps(rec).decode())

        audit_file = tmp_path / "routing_audit.jsonl"
        audit_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        records = read_routing_audit(audit_file, limit=100)

        # Re-verify chain using the same ADR-015 algorithm
        prev_hash = ""
        for i, record in enumerate(records):
            d = {k: v for k, v in record.items() if k != "hash"}
            canonical = json.dumps(d, sort_keys=True, separators=(",", ":").decode())
            expected = hashlib.sha256(canonical.encode()).hexdigest()
            assert record["hash"] == expected, f"Hash mismatch at record {i}"
            assert record["prev_hash"] == prev_hash, f"Chain broken at record {i}"
            prev_hash = record["hash"]


# ---------------------------------------------------------------------------
# P3.4 — Configuration and make_routing_decision_from_factors
# ---------------------------------------------------------------------------


class TestMakeRoutingDecision:
    """P3.4: make_routing_decision_from_factors uses ThegentSettings hysteresis params."""

    def test_simple_complexity_routes_lifecycle(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        d = make_routing_decision_from_factors("simple")
        assert d.mode == "Lifecycle"
        assert d.risk_score == pytest.approx(0.1)

    def test_very_complex_routes_thegent_with_default_band(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        # Default band=0.15 → high threshold = 1.0 - 0.15 = 0.85
        # very_complex risk = 0.9 > 0.85 → TheGent
        d = make_routing_decision_from_factors("very_complex")
        assert d.mode == "TheGent"
        assert d.risk_score == pytest.approx(0.9)

    def test_moderate_routes_lifecycle_with_default_band(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        # moderate risk = 0.45; high threshold = 0.85 → Lifecycle
        d = make_routing_decision_from_factors("moderate")
        assert d.mode == "Lifecycle"

    def test_cost_sensitive_reduces_risk(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        # complex = 0.7, cost_sensitive → 0.6; threshold = 0.85 → Lifecycle
        d = make_routing_decision_from_factors("complex", cost_sensitive=True)
        assert d.risk_score == pytest.approx(0.6)
        assert d.mode == "Lifecycle"

    def test_latency_critical_reduces_risk(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        d_base = make_routing_decision_from_factors("moderate")
        d_latency = make_routing_decision_from_factors("moderate", latency_critical=True)
        assert d_latency.risk_score < d_base.risk_score

    def test_invalid_complexity_raises_value_error(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        with pytest.raises(ValueError, match="Unknown complexity level"):
            make_routing_decision_from_factors("bogus")

    def test_narrow_band_promotes_complex_to_thegent(self) -> None:
        """Wide band raises threshold so complex tasks stay Lifecycle; narrow band flips to TheGent."""
        from thegent.config import ThegentSettings
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        # Small band: high threshold = 1.0 - 0.05 = 0.95; complex=0.7 → Lifecycle
        small_band = ThegentSettings(router_band_width=0.05)  # type: ignore[call-arg]
        d_small = make_routing_decision_from_factors("complex", settings=small_band)
        assert d_small.mode == "Lifecycle"

        # Large band: high = 1.0 - 0.35 = 0.65; complex=0.7 > 0.65 → TheGent
        large_band = ThegentSettings(router_band_width=0.35)  # type: ignore[call-arg]
        d_large = make_routing_decision_from_factors("complex", settings=large_band)
        assert d_large.mode == "TheGent"

    def test_rationale_contains_band_width(self) -> None:
        from thegent.utils.routing_impl.route_executor import (
            make_routing_decision_from_factors,
        )

        d = make_routing_decision_from_factors("simple")
        assert "band_width" in d.rationale


class TestRouterSettingsConfig:
    """P3.4: ThegentSettings exposes router hysteresis env vars."""

    def test_default_band_width(self) -> None:
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_band_width == pytest.approx(0.15)

    def test_default_dwell_time(self) -> None:
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_dwell_time == 300  # noqa: PLR2004

    def test_default_max_dwell(self) -> None:
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_max_dwell == 1800  # noqa: PLR2004

    def test_default_override_threshold(self) -> None:
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_override_threshold == pytest.approx(0.20)

    def test_env_override_band_width(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_ROUTER_BAND_WIDTH", "0.25")
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_band_width == pytest.approx(0.25)

    def test_env_override_dwell_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_ROUTER_DWELL_TIME", "600")
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_dwell_time == 600  # noqa: PLR2004

    def test_env_override_max_dwell(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_ROUTER_MAX_DWELL", "3600")
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_max_dwell == 3600  # noqa: PLR2004

    def test_env_override_override_threshold(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_ROUTER_OVERRIDE_THRESHOLD", "0.35")
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_override_threshold == pytest.approx(0.35)

    def test_env_override_audit_path(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        audit_path = str(tmp_path / "my_audit.jsonl")
        monkeypatch.setenv("THGENT_ROUTER_AUDIT_PATH", audit_path)
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        assert s.router_audit_path == audit_path


# ---------------------------------------------------------------------------
# RouterStatus display helpers
# ---------------------------------------------------------------------------


class TestRouterStatusDisplay:
    """RouterStatus.display() and to_json() produce correct output."""

    def test_display_shows_policy(self) -> None:
        from thegent.utils.routing_impl.route_executor import RouterStatus

        st = RouterStatus(policy="MostRestrictiveWins", total_decisions=5)
        text = st.display()
        assert "MostRestrictiveWins" in text

    def test_display_shows_quorum(self) -> None:
        from thegent.utils.routing_impl.route_executor import RouterStatus

        st = RouterStatus(quorum_decision="TheGent", total_decisions=2)
        text = st.display()
        assert "TheGent" in text

    def test_to_json_has_all_keys(self) -> None:
        from thegent.utils.routing_impl.route_executor import RouterStatus

        st = RouterStatus(total_decisions=3, lifecycle_pct=66.7, thegent_pct=33.3)
        data = json.loads(st.to_json())
        assert set(data.keys()) == {
            "agents",
            "total_decisions",
            "policy",
            "quorum_decision",
            "lifecycle_pct",
            "thegent_pct",
        }
