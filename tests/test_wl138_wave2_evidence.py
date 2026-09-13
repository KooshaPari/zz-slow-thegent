"""Tests verifying Wave-2 execution log exists and is complete.

# @trace WL-138 B90-W2-F5
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTION_LOG = ROOT / "docs" / "reports" / "2026-02-21-B90-W2-execution-log.md"

EXPECTED_AGENTS = ["agent-a", "agent-b", "agent-c", "agent-d", "agent-e", "agent-f"]


class TestWave2ExecutionLog:
    """The Wave-2 execution log must exist and reference all 6 agents."""

    # @trace WL-138 B90-W2-F5

    def test_execution_log_exists(self) -> None:
        """docs/reports/2026-02-21-B90-W2-execution-log.md must exist."""
        assert EXECUTION_LOG.exists(), (
            f"Wave-2 execution log not found: {EXECUTION_LOG}"
        )

    def test_execution_log_mentions_all_agents(self) -> None:
        """Execution log must reference all 6 Wave-2 agents."""
        content = EXECUTION_LOG.read_text(encoding="utf-8")
        for agent in EXPECTED_AGENTS:
            assert agent in content, (
                f"Execution log must mention '{agent}' — it is missing"
            )

    def test_execution_log_has_wave3_prerequisites(self) -> None:
        """Execution log must include a Wave-3 prerequisites section."""
        content = EXECUTION_LOG.read_text(encoding="utf-8")
        assert "Wave-3" in content, (
            "Execution log must include Wave-3 prerequisites section"
        )
