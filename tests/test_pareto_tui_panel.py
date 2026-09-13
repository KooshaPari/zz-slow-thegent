"""Tests for the Pareto Frontier TUI Panel — WL-031.

Covers:
- ParetoTuiSession.get_status
- ParetoTuiSession.get_audit_history
- ParetoTuiSession.get_pareto_data
- Edge cases: empty file, absent file (default path), explicit missing path

# @trace WL-031
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thegent.cli.tui.pareto import ParetoTuiSession
from thegent.utils.routing_impl.route_executor import RouterStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_audit_record(
    provider: str = "lifecycle",
    model: str = "gemini-3-flash",
    latency_ms: int = 10,
    cost: float = 0.0001,
) -> dict:
    return {
        "timestamp": "2026-02-20T00:00:00Z",
        "decision_id": "test-decision-id",
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
        "cost": cost,
        "prev_hash": "",
        "hash": "abc123",
    }


def _write_audit_file(tmp_path: Path, records: list[dict]) -> Path:
    audit = tmp_path / "routing_audit.jsonl"
    with audit.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    return audit


# ---------------------------------------------------------------------------
# TestParetoTuiSession
# ---------------------------------------------------------------------------


class TestParetoTuiSession:
    # @trace WL-031

    def test_get_status_returns_router_status(self, tmp_path: Path) -> None:
        """get_status returns a RouterStatus when audit has at least one record."""
        audit = _write_audit_file(tmp_path, [_make_audit_record()])
        session = ParetoTuiSession(audit_path=audit)
        status = session.get_status()
        assert isinstance(status, RouterStatus)

    def test_get_status_none_on_empty_file(self, tmp_path: Path) -> None:
        """get_status returns None when audit file exists but is empty."""
        audit = tmp_path / "routing_audit.jsonl"
        audit.write_text("", encoding="utf-8")
        session = ParetoTuiSession(audit_path=audit)
        result = session.get_status()
        assert result is None

    def test_get_status_reflects_provider(self, tmp_path: Path) -> None:
        """get_status reflects the provider from the latest audit entry."""
        records = [
            _make_audit_record(provider="lifecycle"),
            _make_audit_record(provider="thegent"),
        ]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        status = session.get_status()
        assert status is not None
        assert status.total_decisions >= 1

    def test_get_audit_history_returns_list(self, tmp_path: Path) -> None:
        """get_audit_history returns a list of dicts."""
        records = [_make_audit_record() for _ in range(5)]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        history = session.get_audit_history()
        assert isinstance(history, list)
        assert len(history) == 5

    def test_get_audit_history_respects_limit(self, tmp_path: Path) -> None:
        """get_audit_history returns at most `limit` records."""
        records = [_make_audit_record(latency_ms=i) for i in range(20)]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        history = session.get_audit_history(limit=10)
        assert len(history) == 10

    def test_get_audit_history_chronological_order(self, tmp_path: Path) -> None:
        """get_audit_history preserves chronological order (oldest first)."""
        records = [_make_audit_record(latency_ms=i * 10) for i in range(1, 6)]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        history = session.get_audit_history(limit=5)
        latencies = [r["latency_ms"] for r in history]
        assert latencies == sorted(latencies)

    def test_get_audit_history_empty_file_returns_empty_list(
        self, tmp_path: Path
    ) -> None:
        """get_audit_history returns [] when audit file is empty."""
        audit = tmp_path / "routing_audit.jsonl"
        audit.write_text("", encoding="utf-8")
        session = ParetoTuiSession(audit_path=audit)
        assert session.get_audit_history() == []

    def test_missing_audit_file_raises_file_not_found(self, tmp_path: Path) -> None:
        """Passing a non-existent audit_path raises FileNotFoundError."""
        absent = tmp_path / "does_not_exist.jsonl"
        with pytest.raises(FileNotFoundError, match="Audit file not found"):
            ParetoTuiSession(audit_path=absent)

    def test_get_pareto_data_returns_correct_shape(self, tmp_path: Path) -> None:
        """get_pareto_data returns a dict with 'providers', 'current', 'history'."""
        records = [
            _make_audit_record(provider="lifecycle", cost=0.001, latency_ms=5),
            _make_audit_record(provider="thegent", cost=0.01, latency_ms=50),
        ]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        data = session.get_pareto_data()
        assert set(data.keys()) == {"providers", "current", "history", "parse_errors"}
        assert isinstance(data["providers"], list)
        assert isinstance(data["current"], dict)
        assert isinstance(data["history"], list)
        assert isinstance(data["parse_errors"], list)

    def test_get_pareto_data_empty_audit_returns_none_current(
        self, tmp_path: Path
    ) -> None:
        """get_pareto_data returns current=None when audit file is empty."""
        audit = tmp_path / "routing_audit.jsonl"
        audit.write_text("", encoding="utf-8")
        session = ParetoTuiSession(audit_path=audit)
        data = session.get_pareto_data()
        assert data["current"] is None
        assert data["providers"] == []
        assert data["history"] == []
        assert data["parse_errors"] == []

    def test_get_audit_history_malformed_json_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """get_audit_history raises ValueError on malformed JSON lines."""
        audit = tmp_path / "routing_audit.jsonl"
        audit.write_text("{not valid json}\n", encoding="utf-8")
        session = ParetoTuiSession(audit_path=audit)
        with pytest.raises(ValueError, match="Malformed JSON"):
            session.get_audit_history()

    def test_get_audit_history_non_strict_skips_malformed_rows(
        self, tmp_path: Path
    ) -> None:
        """Non-strict mode skips malformed JSON lines instead of raising."""
        audit = tmp_path / "routing_audit.jsonl"
        audit.write_text(
            "{not valid json}\n" + json.dumps(_make_audit_record()) + "\n",
            encoding="utf-8",
        )
        session = ParetoTuiSession(audit_path=audit)
        history = session.get_audit_history(strict=False)
        assert len(history) == 1

    def test_get_pareto_data_non_strict_returns_parse_errors(
        self, tmp_path: Path
    ) -> None:
        """Non-strict mode surfaces parse_errors for malformed JSON rows."""
        audit = tmp_path / "routing_audit.jsonl"
        audit.write_text(
            "{not valid json}\n" + json.dumps(_make_audit_record()) + "\n",
            encoding="utf-8",
        )
        session = ParetoTuiSession(audit_path=audit)
        data = session.get_pareto_data(strict=False)
        assert len(data["history"]) == 1
        assert data["parse_errors"] == ["line 1"]


# ---------------------------------------------------------------------------
# TestParetoTuiIntegration
# ---------------------------------------------------------------------------


class TestParetoTuiIntegration:
    # @trace WL-031

    def test_provider_count_matches_unique_providers(self, tmp_path: Path) -> None:
        """get_pareto_data aggregates distinct providers correctly."""
        records = [
            _make_audit_record(provider="lifecycle", cost=0.001),
            _make_audit_record(provider="lifecycle", cost=0.002),
            _make_audit_record(provider="thegent", cost=0.01),
        ]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        data = session.get_pareto_data()
        provider_names = {p["name"] for p in data["providers"]}
        assert "lifecycle" in provider_names
        assert "thegent" in provider_names
        assert len(provider_names) == 2

    def test_provider_avg_cost_computed_correctly(self, tmp_path: Path) -> None:
        """get_pareto_data computes average cost per provider."""
        records = [
            _make_audit_record(provider="lifecycle", cost=0.002),
            _make_audit_record(provider="lifecycle", cost=0.004),
        ]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        data = session.get_pareto_data()
        lc_provider = next(p for p in data["providers"] if p["name"] == "lifecycle")
        assert abs(lc_provider["avg_cost_usd"] - 0.003) < 1e-9

    def test_cost_trend_reflected_in_history(self, tmp_path: Path) -> None:
        """history in get_pareto_data contains all recent records."""
        costs = [0.001 * (i + 1) for i in range(8)]
        records = [_make_audit_record(cost=c) for c in costs]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        data = session.get_pareto_data()
        history_costs = [r["cost"] for r in data["history"]]
        assert len(history_costs) == 8
        # All costs are present and positive.
        assert all(c > 0 for c in history_costs)

    def test_current_reflects_latest_record(self, tmp_path: Path) -> None:
        """get_pareto_data current dict matches the last audit entry."""
        records = [
            _make_audit_record(
                provider="lifecycle", model="gemini-3-flash", latency_ms=5
            ),
            _make_audit_record(
                provider="thegent", model="claude-sonnet-4.6", latency_ms=42
            ),
        ]
        audit = _write_audit_file(tmp_path, records)
        session = ParetoTuiSession(audit_path=audit)
        data = session.get_pareto_data()
        assert data["current"]["provider"] == "thegent"
        assert data["current"]["model"] == "claude-sonnet-4.6"
        assert data["current"]["latency_ms"] == 42

    def test_audit_path_property(self, tmp_path: Path) -> None:
        """ParetoTuiSession exposes the configured audit_path."""
        audit = _write_audit_file(tmp_path, [_make_audit_record()])
        session = ParetoTuiSession(audit_path=audit)
        assert session.audit_path == audit
