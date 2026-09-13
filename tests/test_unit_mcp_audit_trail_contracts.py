"""Tests for AUDIT-N+15 MCP server audit trail and gate contracts.

Covers:
  AT-001  AuditEntry frozen dataclass contract
  AT-002  MCPAuditTrail record + recent round-trip
  AT-003  MCPAuditTrail query filtering
  AT-004  MCPAuditTrail summary stats
  AT-005  MCPAuditTrail max_entries eviction
  AT-006  MCPAuditTrail thread safety (concurrent record)
  AT-007  MCPAuditTrail clear
  AT-008  AuditEntry payload hashing determinism
  AT-009  Contract validation — observe_summary happy path
  AT-010  Contract validation — observe_summary missing required key
  AT-011  Contract validation — contract_health_gate happy path
  AT-012  Contract validation — health_trend happy path
  AT-013  Contract validation — unknown contract name
  AT-014  list_contracts returns all registered contracts
  AT-015  AuditEntry kind enum values
"""

from __future__ import annotations

import hashlib
import threading

import pytest

from thegent.mcp.server.mcp_audit_trail import (
    AuditEntry,
    AuditEntryKind,
    MCPAuditTrail,
    _stable_json,
)
from thegent.mcp.server.mcp_server_contracts import (
    OBSERVE_SUMMARY_CONTRACT,
    SCHEMA_VERSION,
    get_contract,
    list_contracts,
    validate_payload,
)


# ------------------------------------------------------------------
# AT-001 — AuditEntry frozen dataclass contract
# ------------------------------------------------------------------
class TestAuditEntryContract:
    """AT-001: AuditEntry is immutable and serialisable."""

    def test_frozen(self) -> None:
        entry = AuditEntry(
            seq=1,
            ts=1.0,
            kind=AuditEntryKind.TOOL_INVOCATION,
            operation="run",
            agent="test",
            session_id=None,
            outcome="ok",
        )
        with pytest.raises(AttributeError):
            entry.seq = 2  # type: ignore[misc]

    def test_to_dict_minimal(self) -> None:
        entry = AuditEntry(
            seq=1,
            ts=100.0,
            kind=AuditEntryKind.GATE_CHECK,
            operation="gate",
            agent="ci",
            session_id="s-1",
            outcome="pass",
        )
        d = entry.to_dict()
        assert d["seq"] == 1
        assert d["kind"] == "gate_check"
        assert d["outcome"] == "pass"
        assert "duration_ms" not in d
        assert "payload_hash" not in d

    def test_to_dict_full(self) -> None:
        entry = AuditEntry(
            seq=5,
            ts=200.0,
            kind=AuditEntryKind.ERROR,
            operation="thegent_run",
            agent="writer",
            session_id="s-2",
            outcome="error",
            duration_ms=12.345,
            payload_hash="abc123",
            error_message="timeout",
            extra={"retry": True},
        )
        d = entry.to_dict()
        assert d["duration_ms"] == 12.345
        assert d["payload_hash"] == "abc123"
        assert d["error_message"] == "timeout"
        assert d["extra"] == {"retry": True}


# ------------------------------------------------------------------
# AT-002 — MCPAuditTrail record + recent round-trip
# ------------------------------------------------------------------
class TestAuditTrailRecord:
    """AT-002: Record and retrieve audit entries."""

    def test_record_and_recent(self) -> None:
        trail = MCPAuditTrail(max_entries=100)
        e1 = trail.record(
            kind=AuditEntryKind.TOOL_INVOCATION,
            operation="thegent_run",
            agent="writer_standard",
            session_id="s-abc",
            outcome="ok",
            duration_ms=42.1,
        )
        assert e1.seq == 1
        assert e1.operation == "thegent_run"

        e2 = trail.record(
            kind=AuditEntryKind.RESOURCE_READ,
            operation="resource_observe_summary",
            agent="dashboard",
            outcome="ok",
        )
        assert e2.seq == 2

        recent = trail.recent(n=10)
        assert len(recent) == 2
        assert recent[0].seq == 1
        assert recent[1].seq == 2

    def test_record_empty_trail(self) -> None:
        trail = MCPAuditTrail()
        assert trail.recent() == []


# ------------------------------------------------------------------
# AT-003 — MCPAuditTrail query filtering
# ------------------------------------------------------------------
class TestAuditTrailQuery:
    """AT-003: Query filtering by kind, operation, agent, outcome."""

    def _populate(self) -> MCPAuditTrail:
        trail = MCPAuditTrail(max_entries=1000)
        trail.record(kind=AuditEntryKind.TOOL_INVOCATION, operation="run", agent="a", outcome="ok")
        trail.record(kind=AuditEntryKind.TOOL_INVOCATION, operation="run", agent="b", outcome="error")
        trail.record(kind=AuditEntryKind.GATE_CHECK, operation="gate", agent="a", outcome="pass")
        trail.record(kind=AuditEntryKind.RESOURCE_READ, operation="read", agent="c", outcome="ok")
        return trail

    def test_filter_by_kind(self) -> None:
        trail = self._populate()
        gates = trail.query(kind=AuditEntryKind.GATE_CHECK)
        assert len(gates) == 1
        assert gates[0].operation == "gate"

    def test_filter_by_agent(self) -> None:
        trail = self._populate()
        agent_a = trail.query(agent="a")
        assert len(agent_a) == 2

    def test_filter_by_outcome(self) -> None:
        trail = self._populate()
        errors = trail.query(outcome="error")
        assert len(errors) == 1
        assert errors[0].agent == "b"

    def test_filter_combined(self) -> None:
        trail = self._populate()
        results = trail.query(kind=AuditEntryKind.TOOL_INVOCATION, outcome="ok")
        assert len(results) == 1
        assert results[0].agent == "a"


# ------------------------------------------------------------------
# AT-004 — MCPAuditTrail summary stats
# ------------------------------------------------------------------
class TestAuditTrailSummary:
    """AT-004: Summary returns aggregate stats."""

    def test_summary_basic(self) -> None:
        trail = MCPAuditTrail(max_entries=500)
        trail.record(kind=AuditEntryKind.TOOL_INVOCATION, operation="run", agent="a", outcome="ok", duration_ms=10.0)
        trail.record(kind=AuditEntryKind.ERROR, operation="run", agent="a", outcome="error", duration_ms=5.0)

        s = trail.summary()
        assert s["total_entries"] == 2
        assert s["max_entries"] == 500
        assert s["by_kind"]["tool_invocation"] == 1
        assert s["by_kind"]["error"] == 1
        assert s["error_count"] == 1
        assert s["avg_duration_ms"] == 7.5
        assert s["oldest_seq"] == 1
        assert s["newest_seq"] == 2

    def test_summary_empty(self) -> None:
        trail = MCPAuditTrail()
        s = trail.summary()
        assert s["total_entries"] == 0
        assert s["avg_duration_ms"] is None
        assert s["p99_duration_ms"] is None


# ------------------------------------------------------------------
# AT-005 — MCPAuditTrail max_entries eviction
# ------------------------------------------------------------------
class TestAuditTrailEviction:
    """AT-005: Oldest entries are evicted when max_entries exceeded."""

    def test_eviction(self) -> None:
        trail = MCPAuditTrail(max_entries=5)
        for i in range(10):
            trail.record(
                kind=AuditEntryKind.TOOL_INVOCATION,
                operation=f"op_{i}",
                agent="a",
                outcome="ok",
            )
        recent = trail.recent(n=100)
        assert len(recent) == 5
        # Oldest surviving should be seq 6 (first 5 evicted)
        assert recent[0].seq == 6
        assert recent[0].operation == "op_5"


# ------------------------------------------------------------------
# AT-006 — MCPAuditTrail thread safety
# ------------------------------------------------------------------
class TestAuditTrailThreadSafety:
    """AT-006: Concurrent record calls don't corrupt state."""

    def test_concurrent_record(self) -> None:
        trail = MCPAuditTrail(max_entries=500)
        errors: list[Exception] = []

        def _worker(n: int) -> None:
            try:
                for _ in range(50):
                    trail.record(
                        kind=AuditEntryKind.TOOL_INVOCATION,
                        operation=f"op_{n}",
                        agent=f"agent_{n}",
                        outcome="ok",
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert trail.summary()["total_entries"] == 200


# ------------------------------------------------------------------
# AT-007 — MCPAuditTrail clear
# ------------------------------------------------------------------
class TestAuditTrailClear:
    """AT-007: clear() empties the trail and returns evicted count."""

    def test_clear(self) -> None:
        trail = MCPAuditTrail()
        trail.record(kind=AuditEntryKind.GATE_CHECK, operation="g", agent="a", outcome="ok")
        trail.record(kind=AuditEntryKind.GATE_CHECK, operation="g", agent="a", outcome="ok")
        count = trail.clear()
        assert count == 2
        assert trail.recent() == []


# ------------------------------------------------------------------
# AT-008 — AuditEntry payload hashing determinism
# ------------------------------------------------------------------
class TestPayloadHashDeterminism:
    """AT-008: Same payload always produces the same hash."""

    def test_deterministic_hash(self) -> None:
        trail = MCPAuditTrail()
        payload = {"status": "ok", "items": [1, 2, 3]}
        e1 = trail.record(kind=AuditEntryKind.TOOL_INVOCATION, operation="x", agent="a", outcome="ok", payload=payload)
        e2 = trail.record(kind=AuditEntryKind.TOOL_INVOCATION, operation="x", agent="a", outcome="ok", payload=payload)
        assert e1.payload_hash == e2.payload_hash
        assert e1.payload_hash is not None
        assert len(e1.payload_hash) == 16  # truncated sha256

    def test_different_payload_different_hash(self) -> None:
        trail = MCPAuditTrail()
        e1 = trail.record(kind=AuditEntryKind.TOOL_INVOCATION, operation="x", agent="a", outcome="ok", payload={"a": 1})
        e2 = trail.record(kind=AuditEntryKind.TOOL_INVOCATION, operation="x", agent="a", outcome="ok", payload={"a": 2})
        assert e1.payload_hash != e2.payload_hash


# ------------------------------------------------------------------
# AT-009 — Contract validation: observe_summary happy path
# ------------------------------------------------------------------
class TestObserveSummaryContract:
    """AT-009: observe_summary payload passes contract validation."""

    def test_valid_payload(self) -> None:
        payload = {
            "status": "ok",
            "payload_type": "observe_summary",
            "payload_schema_version": "1.0",
            "alerts": [],
            "drift": {"within_budget": True},
            "escalation": {"past_sla_count": 0},
            "trend_summary": {"enabled": False},
            "generated_query": {"top_escalations": 5},
        }
        errors = validate_payload("observe_summary", payload)
        assert errors == []

    def test_contract_has_required_keys(self) -> None:
        assert len(OBSERVE_SUMMARY_CONTRACT.required_keys) >= 8


# ------------------------------------------------------------------
# AT-010 — Contract validation: missing required key
# ------------------------------------------------------------------
class TestObserveSummaryContractMissing:
    """AT-010: Missing required key produces validation error."""

    def test_missing_status(self) -> None:
        payload = {
            "payload_type": "observe_summary",
            "payload_schema_version": "1.0",
            "alerts": [],
            "drift": {},
            "escalation": {},
            "trend_summary": {},
            "generated_query": {},
        }
        errors = validate_payload("observe_summary", payload)
        assert any("missing_required: status" in e for e in errors)


# ------------------------------------------------------------------
# AT-011 — Contract validation: contract_health_gate happy path
# ------------------------------------------------------------------
class TestContractHealthGateContract:
    """AT-011: contract_health_gate payload passes validation."""

    def test_valid_payload(self) -> None:
        payload = {
            "status": "ok",
            "policy_profile": "standard",
            "decision_reasons": ["allow"],
            "total": 10,
            "healthy_count": 8,
            "unhealthy_count": 1,
            "blocked_count": 1,
        }
        errors = validate_payload("contract_health_gate", payload)
        assert errors == []


# ------------------------------------------------------------------
# AT-012 — Contract validation: health_trend happy path
# ------------------------------------------------------------------
class TestHealthTrendContract:
    """AT-012: health_trend payload passes validation."""

    def test_valid_payload(self) -> None:
        payload = {
            "status": "ok",
            "payload_type": "session_contract_health_report",
            "schema_version": "1.0",
            "trend_payload_type": "health_trend",
            "generated_at_utc": "2026-07-20T00:00:00Z",
            "snapshot_count": 30,
            "snapshot_ids_hash": "abc123",
        }
        errors = validate_payload("health_trend", payload)
        assert errors == []


# ------------------------------------------------------------------
# AT-013 — Contract validation: unknown contract name
# ------------------------------------------------------------------
class TestUnknownContract:
    """AT-013: Unknown contract name returns error."""

    def test_unknown(self) -> None:
        errors = validate_payload("nonexistent", {})
        assert len(errors) == 1
        assert "unknown_contract" in errors[0]


# ------------------------------------------------------------------
# AT-014 — list_contracts returns all registered contracts
# ------------------------------------------------------------------
class TestListContracts:
    """AT-014: list_contracts() returns all 3 registered contracts."""

    def test_list_contracts(self) -> None:
        result = list_contracts()
        assert set(result.keys()) == {"observe_summary", "contract_health_gate", "health_trend"}
        for info in result.values():
            assert info["schema_version"] == SCHEMA_VERSION

    def test_get_contract(self) -> None:
        c = get_contract("observe_summary")
        assert c is OBSERVE_SUMMARY_CONTRACT

    def test_get_contract_unknown(self) -> None:
        assert get_contract("nope") is None


# ------------------------------------------------------------------
# AT-015 — AuditEntry kind enum values
# ------------------------------------------------------------------
class TestAuditEntryKind:
    """AT-015: AuditEntryKind values are stable."""

    def test_values(self) -> None:
        assert AuditEntryKind.TOOL_INVOCATION.value == "tool_invocation"
        assert AuditEntryKind.RESOURCE_READ.value == "resource_read"
        assert AuditEntryKind.GATE_CHECK.value == "gate_check"
        assert AuditEntryKind.ERROR.value == "error"

    def test_all_members(self) -> None:
        assert len(AuditEntryKind) == 4


# ------------------------------------------------------------------
# _stable_json determinism
# ------------------------------------------------------------------
class TestStableJson:
    """Verify _stable_json is deterministic and sorted."""

    def test_sorted_keys(self) -> None:
        result = _stable_json({"z": 1, "a": 2})
        assert result == '{"a":2,"z":1}'

    def test_deterministic(self) -> None:
        payload = {"b": [3, 1], "a": "hello"}
        assert _stable_json(payload) == _stable_json(payload)

    def test_hash_matches(self) -> None:
        payload = {"x": 1, "y": 2}
        raw = _stable_json(payload)
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        trail = MCPAuditTrail()
        entry = trail.record(kind=AuditEntryKind.GATE_CHECK, operation="t", agent="a", outcome="ok", payload=payload)
        assert entry.payload_hash == expected
