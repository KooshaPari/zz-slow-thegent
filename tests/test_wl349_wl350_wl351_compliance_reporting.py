# @trace WL-349 WL-350 WL-351
"""Targeted tests for governance rollup, telemetry, and queue automation."""

from __future__ import annotations

import pytest

from thegent.governance.compliance_reports import ComplianceReporter


def _sample_evidence() -> list[dict[str, object]]:
    return [
        {
            "evidence_id": "ev-1",
            "kind": "policy_evaluation",
            "actor": "agent-a",
            "timestamp_utc": "2026-02-23T01:00:00+00:00",
            "payload": {
                "requires_action": True,
                "severity": "high",
                "reason": "policy_violation",
            },
        },
        {
            "evidence_id": "ev-2",
            "kind": "human_approval",
            "actor": "agent-b",
            "timestamp_utc": "2026-02-23T01:01:00+00:00",
            "payload": {"requires_action": False},
        },
        {
            "evidence_id": "ev-3",
            "kind": "policy_evaluation",
            "actor": "agent-a",
            "timestamp_utc": "2026-02-23T01:02:00+00:00",
            "payload": {
                "requires_action": True,
                "severity": "critical",
                "reason": "blocked_gate",
            },
        },
    ]


@pytest.mark.requirement("WL-349")
def test_wl349_governance_rollup_is_deterministic() -> None:
    reporter = ComplianceReporter()
    rollup = reporter.generate_governance_rollup(_sample_evidence())
    assert rollup["total_records"] == 3
    assert rollup["action_required_records"] == 2
    assert rollup["by_kind"] == {"human_approval": 1, "policy_evaluation": 2}
    assert rollup["by_actor"] == {"agent-a": 2, "agent-b": 1}


@pytest.mark.requirement("WL-350")
def test_wl350_governance_telemetry_reflects_rollup_and_queue() -> None:
    reporter = ComplianceReporter()
    evidence = _sample_evidence()
    rollup = reporter.generate_governance_rollup(evidence)
    queue = reporter.build_governance_queue(evidence)
    telemetry = reporter.generate_governance_telemetry(rollup=rollup, queue=queue)
    assert telemetry["total_records"] == 3
    assert telemetry["unique_kinds"] == 2
    assert telemetry["unique_actors"] == 2
    assert telemetry["queue_depth"] == 2
    assert telemetry["action_required_records"] == 2


@pytest.mark.requirement("WL-351")
def test_wl351_governance_queue_orders_by_severity_then_time() -> None:
    reporter = ComplianceReporter()
    queue = reporter.build_governance_queue(_sample_evidence())
    assert [item["evidence_id"] for item in queue] == ["ev-3", "ev-1"]
    assert queue[0]["severity"] == "critical"
    assert queue[1]["severity"] == "high"


def test_invalid_report_format_raises_value_error() -> None:
    reporter = ComplianceReporter()
    with pytest.raises(ValueError, match="Unsupported compliance report format"):
        reporter.generate_report({"ok": True}, format="xml")
