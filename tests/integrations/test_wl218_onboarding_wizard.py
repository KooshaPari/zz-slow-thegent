"""Tests for thegent.integrations.onboarding_wizard — Autosync onboarding wizard.

@trace WL-218
"""

from __future__ import annotations

import pytest

from thegent.integrations.onboarding_wizard import (
    OnboardingStep,
    OnboardingWizard,
)


class TestOnboardingStep:
    """Test OnboardingStep dataclass. @trace WL-218"""

    @pytest.mark.requirement("WL-218")
    def test_create_step_default_completed(self) -> None:
        """Can create an OnboardingStep with default completed=False."""
        step = OnboardingStep(
            step_id="configure_connectors",
            title="Configure Connectors",
            description="Set up connectors",
        )

        assert step.step_id == "configure_connectors"
        assert step.title == "Configure Connectors"
        assert step.description == "Set up connectors"
        assert step.completed is False

    @pytest.mark.requirement("WL-218")
    def test_create_step_completed(self) -> None:
        """Can create an OnboardingStep with completed=True."""
        step = OnboardingStep(
            step_id="validate_auth",
            title="Validate Auth",
            description="Verify credentials",
            completed=True,
        )

        assert step.completed is True


class TestOnboardingWizard:
    """Test OnboardingWizard operations. @trace WL-218"""

    @pytest.fixture
    def wizard(self) -> OnboardingWizard:
        """Provide an OnboardingWizard instance."""
        return OnboardingWizard()

    @pytest.mark.requirement("WL-218")
    def test_steps_classvar_exists(self) -> None:
        """OnboardingWizard has STEPS ClassVar."""
        assert hasattr(OnboardingWizard, "STEPS")
        assert isinstance(OnboardingWizard.STEPS, list)

    @pytest.mark.requirement("WL-218")
    def test_steps_has_six_items(self) -> None:
        """STEPS list contains exactly 6 steps."""
        assert len(OnboardingWizard.STEPS) == 6

    @pytest.mark.requirement("WL-218")
    def test_steps_have_required_fields(self) -> None:
        """Each step in STEPS has required fields."""
        for step_dict in OnboardingWizard.STEPS:
            assert "step_id" in step_dict
            assert "title" in step_dict
            assert "description" in step_dict

    @pytest.mark.requirement("WL-218")
    def test_get_steps_returns_list(self, wizard: OnboardingWizard) -> None:
        """get_steps returns a list of OnboardingStep."""
        steps = wizard.get_steps()

        assert isinstance(steps, list)
        assert len(steps) == 6
        assert all(isinstance(s, OnboardingStep) for s in steps)

    @pytest.mark.requirement("WL-218")
    def test_get_steps_all_incomplete_initially(self, wizard: OnboardingWizard) -> None:
        """Initially, all steps are incomplete."""
        steps = wizard.get_steps()

        assert all(not s.completed for s in steps)

    @pytest.mark.requirement("WL-218")
    def test_complete_step_valid(self, wizard: OnboardingWizard) -> None:
        """Can complete a valid step."""
        wizard.complete_step("configure_connectors")
        steps = wizard.get_steps()

        assert steps[0].completed is True

    @pytest.mark.requirement("WL-218")
    def test_complete_step_invalid_raises(self, wizard: OnboardingWizard) -> None:
        """Raises KeyError when completing non-existent step."""
        with pytest.raises(KeyError, match="not found"):
            wizard.complete_step("invalid_step")

    @pytest.mark.requirement("WL-218")
    def test_complete_step_idempotent(self, wizard: OnboardingWizard) -> None:
        """Completing the same step twice is idempotent."""
        wizard.complete_step("validate_auth")
        wizard.complete_step("validate_auth")

        steps = wizard.get_steps()
        assert steps[1].completed is True

    @pytest.mark.requirement("WL-218")
    def test_next_incomplete_returns_first(self, wizard: OnboardingWizard) -> None:
        """next_incomplete returns the first incomplete step."""
        next_step = wizard.next_incomplete()

        assert next_step is not None
        assert next_step.step_id == "configure_connectors"

    @pytest.mark.requirement("WL-218")
    def test_next_incomplete_after_completing_one(
        self, wizard: OnboardingWizard
    ) -> None:
        """next_incomplete skips completed steps."""
        wizard.complete_step("configure_connectors")
        next_step = wizard.next_incomplete()

        assert next_step is not None
        assert next_step.step_id == "validate_auth"

    @pytest.mark.requirement("WL-218")
    def test_next_incomplete_returns_none_when_complete(
        self, wizard: OnboardingWizard
    ) -> None:
        """next_incomplete returns None when all steps are completed."""
        for step_dict in OnboardingWizard.STEPS:
            wizard.complete_step(step_dict["step_id"])

        assert wizard.next_incomplete() is None

    @pytest.mark.requirement("WL-218")
    def test_is_complete_false_initially(self, wizard: OnboardingWizard) -> None:
        """is_complete returns False initially."""
        assert wizard.is_complete() is False

    @pytest.mark.requirement("WL-218")
    def test_is_complete_true_when_all_done(self, wizard: OnboardingWizard) -> None:
        """is_complete returns True when all steps are completed."""
        for step_dict in OnboardingWizard.STEPS:
            wizard.complete_step(step_dict["step_id"])

        assert wizard.is_complete() is True

    @pytest.mark.requirement("WL-218")
    def test_progress_initial(self, wizard: OnboardingWizard) -> None:
        """progress returns (0, 6) initially."""
        completed, total = wizard.progress()

        assert completed == 0
        assert total == 6

    @pytest.mark.requirement("WL-218")
    def test_progress_after_completing_steps(self, wizard: OnboardingWizard) -> None:
        """progress returns correct counts as steps are completed."""
        wizard.complete_step("configure_connectors")
        wizard.complete_step("validate_auth")

        completed, total = wizard.progress()
        assert completed == 2
        assert total == 6

    @pytest.mark.requirement("WL-218")
    def test_progress_when_complete(self, wizard: OnboardingWizard) -> None:
        """progress returns (total, total) when all steps completed."""
        for step_dict in OnboardingWizard.STEPS:
            wizard.complete_step(step_dict["step_id"])

        completed, total = wizard.progress()
        assert completed == 6
        assert total == 6
        assert completed == total
