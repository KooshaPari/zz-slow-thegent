"""Unit tests for MoralUI (WP-29003)."""

import pytest

from thegent.ux.moral_ui import ArbitrationResult, MoralDilemma, MoralUI


@pytest.mark.unit
class TestMoralUI:
    """MoralUI (WP-29003)."""

    def test_present_and_resolve_dilemma(self) -> None:
        # @trace FR-UX-001
        """Can present and resolve a moral dilemma."""
        ui = MoralUI()
        dilemma = MoralDilemma(
            id="d1",
            description="Agent wants to lie to save power.",
            conflicting_principles=["Honesty", "Efficiency"],
            proposed_options=[
                {"id": "o1", "text": "Lie"},
                {"id": "o2", "text": "Tell truth"},
            ],
            context={"agent_id": "agent-1"},
        )

        ui.present_dilemma(dilemma)
        assert "d1" in ui.active_dilemmas

        result = ArbitrationResult(
            dilemma_id="d1",
            selected_option_id="o2",
            reasoning="Honesty is more important.",
            arbitrator_id="human-1",
        )

        success = ui.resolve_dilemma(result)
        assert success is True
        assert "d1" not in ui.active_dilemmas

    def test_resolve_unknown_dilemma(self) -> None:
        # @trace FR-UX-001
        """Resolving unknown dilemma returns False."""
        ui = MoralUI()
        result = ArbitrationResult(
            dilemma_id="unknown",
            selected_option_id="o1",
            reasoning="N/A",
            arbitrator_id="human-1",
        )
        success = ui.resolve_dilemma(result)
        assert success is False
