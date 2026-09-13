"""AUDIT-N+54: governance/audit hardening spec (SOTA pass-38).

15 invariants FR-GOV-AU-001..015 covering verify_chain / query_events
path guards, limit validation, empty-registry handling, filter
semantics, and canonical ``__all__``.

Source: src/thegent/governance/audit.py

@trace AUDIT-N+54  FR-GOV-AU-001..015
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from thegent.governance import audit as _mod
from thegent.governance.audit import query_events, verify_chain

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-AU-001 / FR-GOV-AU-002 -- verify_chain path + empty registry
# ---------------------------------------------------------------------------


class TestVerifyChainBasics:
    """FR-GOV-AU-001/002."""

    def test_verify_chain_returns_dict(self, tmp_path: Path) -> None:
        result = verify_chain(tmp_path)
        assert isinstance(result, dict)

    def test_verify_chain_empty_registry_status(self, tmp_path: Path) -> None:
        result = verify_chain(tmp_path)
        assert result.get("status") == "empty" or result.get("entries") == 0

    def test_verify_chain_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            verify_chain(Path("relative/session"))


# ---------------------------------------------------------------------------
# FR-GOV-AU-003 -- verify_chain wires Auditor with registry path
# ---------------------------------------------------------------------------


class TestVerifyChainWiring:
    """FR-GOV-AU-003."""

    def test_constructs_auditor_with_registry_jsonl(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.Auditor") as mock_auditor:
            mock_auditor.return_value.verify_registry.return_value = {"verified": True}
            result = verify_chain(tmp_path)
            mock_auditor.assert_called_once_with(tmp_path / "run_registry.jsonl")
            assert result == {"verified": True}


# ---------------------------------------------------------------------------
# FR-GOV-AU-004 / FR-GOV-AU-005 -- query_events path + limit guards
# ---------------------------------------------------------------------------


class TestQueryEventsGuards:
    """FR-GOV-AU-004/005."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            query_events(Path("relative/session"))

    def test_rejects_non_positive_limit(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="limit"):
            query_events(tmp_path, limit=0)

    def test_rejects_negative_limit(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="limit"):
            query_events(tmp_path, limit=-5)


# ---------------------------------------------------------------------------
# FR-GOV-AU-006 / FR-GOV-AU-007 / FR-GOV-AU-008 -- query filters
# ---------------------------------------------------------------------------


class TestQueryEventsFilters:
    """FR-GOV-AU-006/007/008."""

    def _runs(self) -> list[dict[str, Any]]:
        return [
            {"run_id": "r1", "event": "start"},
            {"run_id": "r1", "event": "end"},
            {"run_id": "r2", "event": "start"},
            {"run_id": "r3"},  # missing event → defaults to "start"
        ]

    def test_filters_by_run_id(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.RunRegistry") as mock_reg:
            mock_reg.return_value.list_runs.return_value = self._runs()
            result = query_events(tmp_path, run_id="r1")
            assert all(r["run_id"] == "r1" for r in result)
            assert len(result) == 2

    def test_filters_by_event_type(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.RunRegistry") as mock_reg:
            mock_reg.return_value.list_runs.return_value = self._runs()
            result = query_events(tmp_path, event_type="start")
            assert all((r.get("event") or "start") == "start" for r in result)
            assert len(result) == 3

    def test_respects_limit(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.RunRegistry") as mock_reg:
            mock_reg.return_value.list_runs.return_value = self._runs()
            result = query_events(tmp_path, limit=1)
            assert len(result) == 1


# ---------------------------------------------------------------------------
# FR-GOV-AU-009 -- list_runs overfetch factor
# ---------------------------------------------------------------------------


class TestQueryEventsOverfetch:
    """FR-GOV-AU-009: list_runs is called with ``limit * 2``."""

    def test_list_runs_limit_is_double(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.RunRegistry") as mock_reg:
            mock_reg.return_value.list_runs.return_value = []
            query_events(tmp_path, limit=10)
            mock_reg.return_value.list_runs.assert_called_once_with(limit=20)


# ---------------------------------------------------------------------------
# FR-GOV-AU-010 / FR-GOV-AU-011 -- empty / missing event default
# ---------------------------------------------------------------------------


class TestQueryEventsDefaults:
    """FR-GOV-AU-010/011."""

    def test_empty_registry_returns_empty_list(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.RunRegistry") as mock_reg:
            mock_reg.return_value.list_runs.return_value = []
            assert query_events(tmp_path) == []

    def test_missing_event_defaults_to_start_for_filter(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.RunRegistry") as mock_reg:
            mock_reg.return_value.list_runs.return_value = [{"run_id": "r9"}]
            result = query_events(tmp_path, event_type="start")
            assert len(result) == 1


# ---------------------------------------------------------------------------
# FR-GOV-AU-012 -- RunRegistry constructed with session_dir
# ---------------------------------------------------------------------------


class TestQueryEventsWiring:
    """FR-GOV-AU-012."""

    def test_run_registry_gets_session_dir(self, tmp_path: Path) -> None:
        with patch("thegent.governance.audit.RunRegistry") as mock_reg:
            mock_reg.return_value.list_runs.return_value = []
            query_events(tmp_path)
            mock_reg.assert_called_once_with(tmp_path)


# ---------------------------------------------------------------------------
# FR-GOV-AU-013 / FR-GOV-AU-014 / FR-GOV-AU-015 -- __all__
# ---------------------------------------------------------------------------


class TestAuditAll:
    """FR-GOV-AU-013/014/015."""

    def test_all_contains_verify_chain(self) -> None:
        assert "verify_chain" in _mod.__all__

    def test_all_contains_query_events(self) -> None:
        assert "query_events" in _mod.__all__

    def test_all_exactly_two_symbols(self) -> None:
        assert sorted(_mod.__all__) == sorted(["query_events", "verify_chain"])
