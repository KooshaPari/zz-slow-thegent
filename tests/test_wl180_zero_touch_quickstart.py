"""Tests for WL-180 Zero-Touch Operator Quick Start.

# @trace WL-180
"""

from __future__ import annotations

import pytest

from thegent.integrations.zero_touch_quickstart import (
    QuickStartStep,
    ZeroTouchQuickStart,
)


@pytest.mark.requirement("WL-180")
class TestQuickStartStep:
    """Tests for QuickStartStep dataclass."""

    def test_quick_start_step_creation(self) -> None:
        """QuickStartStep can be created with required fields."""
        step = QuickStartStep(step_id="s1", description="Install dependencies")
        assert step.step_id == "s1"
        assert step.description == "Install dependencies"
        assert step.completed is False

    def test_quick_start_step_completed(self) -> None:
        """QuickStartStep can be marked as completed."""
        step = QuickStartStep(
            step_id="s1", description="Install dependencies", completed=True
        )
        assert step.completed is True


@pytest.mark.requirement("WL-180")
class TestZeroTouchQuickStart:
    """Tests for ZeroTouchQuickStart class."""

    def test_add_step(self) -> None:
        """add_step() creates and stores a step."""
        qs = ZeroTouchQuickStart()
        step = qs.add_step("s1", "Install dependencies")

        assert isinstance(step, QuickStartStep)
        assert step.step_id == "s1"
        assert step.description == "Install dependencies"
        assert step.completed is False

    def test_add_multiple_steps(self) -> None:
        """add_step() can add multiple steps."""
        qs = ZeroTouchQuickStart()
        s1 = qs.add_step("s1", "Install dependencies")
        s2 = qs.add_step("s2", "Configure environment")
        s3 = qs.add_step("s3", "Start services")

        assert s1.step_id == "s1"
        assert s2.step_id == "s2"
        assert s3.step_id == "s3"

    def test_complete_step(self) -> None:
        """complete_step() marks a step as completed."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Install dependencies")

        qs.complete_step("s1")

        # Check by examining progress
        completed, total = qs.progress()
        assert completed == 1
        assert total == 1

    def test_complete_step_not_found(self) -> None:
        """complete_step() raises KeyError for unknown step."""
        qs = ZeroTouchQuickStart()

        with pytest.raises(KeyError, match="Step not found"):
            qs.complete_step("unknown")

    def test_complete_multiple_steps(self) -> None:
        """complete_step() can mark multiple steps as completed."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Install dependencies")
        qs.add_step("s2", "Configure environment")
        qs.add_step("s3", "Start services")

        qs.complete_step("s1")
        qs.complete_step("s3")

        completed, total = qs.progress()
        assert completed == 2
        assert total == 3

    def test_progress_empty(self) -> None:
        """progress() returns (0, 0) when no steps added."""
        qs = ZeroTouchQuickStart()
        completed, total = qs.progress()

        assert completed == 0
        assert total == 0

    def test_progress_no_completed(self) -> None:
        """progress() returns correct counts when no steps completed."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Step 1")
        qs.add_step("s2", "Step 2")
        qs.add_step("s3", "Step 3")

        completed, total = qs.progress()
        assert completed == 0
        assert total == 3

    def test_progress_all_completed(self) -> None:
        """progress() returns correct counts when all steps completed."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Step 1")
        qs.add_step("s2", "Step 2")
        qs.add_step("s3", "Step 3")

        qs.complete_step("s1")
        qs.complete_step("s2")
        qs.complete_step("s3")

        completed, total = qs.progress()
        assert completed == 3
        assert total == 3

    def test_progress_partial_completed(self) -> None:
        """progress() returns correct counts when some steps completed."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Step 1")
        qs.add_step("s2", "Step 2")
        qs.add_step("s3", "Step 3")
        qs.add_step("s4", "Step 4")

        qs.complete_step("s2")
        qs.complete_step("s4")

        completed, total = qs.progress()
        assert completed == 2
        assert total == 4

    def test_render_checklist_empty(self) -> None:
        """render_checklist() returns empty string for empty guide."""
        qs = ZeroTouchQuickStart()
        checklist = qs.render_checklist()
        assert checklist == ""

    def test_render_checklist_single_step_incomplete(self) -> None:
        """render_checklist() shows incomplete step with [ ]."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Install dependencies")

        checklist = qs.render_checklist()
        assert "[ ] s1: Install dependencies" in checklist

    def test_render_checklist_single_step_complete(self) -> None:
        """render_checklist() shows complete step with [x]."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Install dependencies")
        qs.complete_step("s1")

        checklist = qs.render_checklist()
        assert "[x] s1: Install dependencies" in checklist

    def test_render_checklist_mixed(self) -> None:
        """render_checklist() shows mix of complete and incomplete steps."""
        qs = ZeroTouchQuickStart()
        qs.add_step("s1", "Install dependencies")
        qs.add_step("s2", "Configure environment")
        qs.add_step("s3", "Start services")

        qs.complete_step("s1")
        qs.complete_step("s3")

        checklist = qs.render_checklist()
        lines = checklist.split("\n")

        assert len(lines) == 3
        assert "[x] s1: Install dependencies" in checklist
        assert "[ ] s2: Configure environment" in checklist
        assert "[x] s3: Start services" in checklist

    def test_render_checklist_sorted(self) -> None:
        """render_checklist() renders steps in sorted order."""
        qs = ZeroTouchQuickStart()
        qs.add_step("z-step", "Last step")
        qs.add_step("a-step", "First step")
        qs.add_step("m-step", "Middle step")

        checklist = qs.render_checklist()
        lines = checklist.split("\n")

        assert len(lines) == 3
        # Should be in sorted order
        assert "a-step" in lines[0]
        assert "m-step" in lines[1]
        assert "z-step" in lines[2]

    def test_render_checklist_format(self) -> None:
        """render_checklist() uses markdown checkbox format."""
        qs = ZeroTouchQuickStart()
        qs.add_step("setup", "Set up environment")
        qs.add_step("test", "Run tests")

        checklist = qs.render_checklist()

        # Should contain markdown checkboxes
        assert "[ ]" in checklist or "[x]" in checklist
        # Each line should have format: [checkbox] step_id: description
        for line in checklist.split("\n"):
            if line:
                assert ": " in line  # Should have step_id: description format
