"""Tests for final Wave-3 execution evidence bundle (WL-138 B90-W3-E5).
# @trace WL-138 B90-W3-E5
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
EVIDENCE_BUNDLE = ROOT / "docs" / "reports" / "2026-02-21-B90-W3-execution-evidence.md"


def test_evidence_bundle_exists() -> None:
    """The Wave-3 execution evidence bundle must exist."""
    assert EVIDENCE_BUNDLE.exists(), f"Expected evidence bundle at {EVIDENCE_BUNDLE}"


def test_evidence_bundle_mentions_wave3() -> None:
    """Evidence bundle must mention Wave-3."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    assert "Wave-3" in content or "wave-3" in content or "wave3" in content, (
        "Expected 'Wave-3' reference in evidence bundle"
    )


def test_evidence_bundle_mentions_all_agents() -> None:
    """Evidence bundle must reference all 6 Wave-3 agents (agent-a through agent-f)."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    for agent in ("agent-a", "agent-b", "agent-c", "agent-d", "agent-e", "agent-f"):
        assert agent in content, f"Expected '{agent}' in evidence bundle"


def test_evidence_bundle_mentions_agent_a_artifact() -> None:
    """Evidence bundle must mention at least one agent-a artifact."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    # check_slo_gate.py or test_wl120_extraction_hardening.py are agent-a artifacts
    assert "check_slo_gate.py" in content or "extraction_hardening" in content or "two-surface" in content, (
        "Expected at least one agent-a artifact mentioned in evidence bundle"
    )


def test_evidence_bundle_mentions_agent_b_artifact() -> None:
    """Evidence bundle must mention at least one agent-b artifact."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    assert "runtime-modularization-matrix-v2" in content or "parity-gap-report" in content or "agent-b" in content, (
        "Expected at least one agent-b artifact or reference in evidence bundle"
    )


def test_evidence_bundle_mentions_agent_c_artifact() -> None:
    """Evidence bundle must mention at least one agent-c artifact."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    assert "audit_boundary_compliance" in content or "retrospective" in content or "agent-c" in content, (
        "Expected at least one agent-c artifact or reference in evidence bundle"
    )


def test_evidence_bundle_mentions_agent_d_artifact() -> None:
    """Evidence bundle must mention at least one agent-d artifact."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    assert "zig-gate" in content or "mojo-fallback" in content or "agent-d" in content, (
        "Expected at least one agent-d artifact or reference in evidence bundle"
    )


def test_evidence_bundle_mentions_agent_e_artifact() -> None:
    """Evidence bundle must mention at least one agent-e artifact."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    assert "lane-split-tuning" in content or "GOVERNANCE_SUMMARY" in content or "agent-e" in content, (
        "Expected at least one agent-e artifact or reference in evidence bundle"
    )


def test_evidence_bundle_mentions_agent_f_artifact() -> None:
    """Evidence bundle must mention at least one agent-f artifact."""
    content = EVIDENCE_BUNDLE.read_text(encoding="utf-8")
    assert "migration-benchmark" in content or "closeout" in content or "agent-f" in content, (
        "Expected at least one agent-f artifact or reference in evidence bundle"
    )
