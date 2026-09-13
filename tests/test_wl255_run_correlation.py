"""Tests for WL-255: Run Correlation IDs.

Tests the correlation tracking system for run-level tracing and observability.

# @trace WL-255
"""

from __future__ import annotations

import pytest


@pytest.mark.requirement("WL-255")
class TestCorrelationContext:
    """Tests for CorrelationContext dataclass."""

    def test_create_with_defaults(self):
        """# @trace WL-255 — CorrelationContext can be created with defaults."""
        from thegent.integrations.run_correlation import CorrelationContext

        ctx = CorrelationContext(run_id="run-1")
        assert ctx.run_id == "run-1"
        assert ctx.parent_id is None
        assert ctx.trace_ids == []

    def test_create_with_parent_id(self):
        """# @trace WL-255 — CorrelationContext can be created with parent_id."""
        from thegent.integrations.run_correlation import CorrelationContext

        ctx = CorrelationContext(run_id="run-2", parent_id="run-1")
        assert ctx.run_id == "run-2"
        assert ctx.parent_id == "run-1"
        assert ctx.trace_ids == []

    def test_trace_ids_independent_between_instances(self):
        """# @trace WL-255 — trace_ids list is independent between instances."""
        from thegent.integrations.run_correlation import CorrelationContext

        ctx1 = CorrelationContext(run_id="run-1")
        ctx2 = CorrelationContext(run_id="run-2")

        ctx1.trace_ids.append("trace-1")
        assert ctx1.trace_ids == ["trace-1"]
        assert ctx2.trace_ids == []


@pytest.mark.requirement("WL-255")
class TestRunCorrelationTracker:
    """Tests for RunCorrelationTracker."""

    def test_start_run_creates_context(self):
        """# @trace WL-255 — start_run creates a new correlation context."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        ctx = tracker.start_run("run-1")

        assert ctx.run_id == "run-1"
        assert ctx.parent_id is None
        assert ctx.trace_ids == []

    def test_start_run_with_parent(self):
        """# @trace WL-255 — start_run with parent_id sets parent relationship."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        tracker.start_run("run-1")
        ctx = tracker.start_run("run-2", parent_id="run-1")

        assert ctx.run_id == "run-2"
        assert ctx.parent_id == "run-1"

    def test_add_trace_to_run(self):
        """# @trace WL-255 — add_trace appends trace_id to a run."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        tracker.start_run("run-1")
        tracker.add_trace("run-1", "trace-1")

        ctx = tracker.get("run-1")
        assert "trace-1" in ctx.trace_ids

    def test_add_multiple_traces(self):
        """# @trace WL-255 — add_trace can be called multiple times."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        tracker.start_run("run-1")
        tracker.add_trace("run-1", "trace-1")
        tracker.add_trace("run-1", "trace-2")
        tracker.add_trace("run-1", "trace-3")

        ctx = tracker.get("run-1")
        assert ctx.trace_ids == ["trace-1", "trace-2", "trace-3"]

    def test_add_trace_to_nonexistent_run_raises_keyerror(self):
        """# @trace WL-255 — add_trace raises KeyError for nonexistent run."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        with pytest.raises(KeyError, match="not found"):
            tracker.add_trace("nonexistent", "trace-1")

    def test_get_existing_run(self):
        """# @trace WL-255 — get returns the correct CorrelationContext."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        tracker.start_run("run-1")
        tracker.add_trace("run-1", "trace-1")

        ctx = tracker.get("run-1")
        assert ctx.run_id == "run-1"
        assert ctx.trace_ids == ["trace-1"]

    def test_get_nonexistent_run_raises_keyerror(self):
        """# @trace WL-255 — get raises KeyError for nonexistent run."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        with pytest.raises(KeyError, match="not found"):
            tracker.get("nonexistent")

    def test_children_returns_all_child_runs(self):
        """# @trace WL-255 — children returns all runs with given parent_id."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        tracker.start_run("parent-1")
        tracker.start_run("child-1", parent_id="parent-1")
        tracker.start_run("child-2", parent_id="parent-1")
        tracker.start_run("child-3", parent_id="parent-1")
        tracker.start_run("child-4", parent_id="parent-2")

        children = tracker.children("parent-1")
        assert len(children) == 3
        assert all(c.parent_id == "parent-1" for c in children)
        assert {c.run_id for c in children} == {"child-1", "child-2", "child-3"}

    def test_children_empty_for_parent_with_no_children(self):
        """# @trace WL-255 — children returns empty list for parent with no children."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        tracker.start_run("parent-1")
        children = tracker.children("parent-1")
        assert children == []

    def test_multiple_independent_hierarchies(self):
        """# @trace WL-255 — tracker handles multiple independent run hierarchies."""
        from thegent.integrations.run_correlation import RunCorrelationTracker

        tracker = RunCorrelationTracker()
        # First hierarchy
        tracker.start_run("parent-1")
        tracker.start_run("child-1a", parent_id="parent-1")
        tracker.start_run("child-1b", parent_id="parent-1")

        # Second hierarchy
        tracker.start_run("parent-2")
        tracker.start_run("child-2a", parent_id="parent-2")

        # Verify isolation
        assert len(tracker.children("parent-1")) == 2
        assert len(tracker.children("parent-2")) == 1
        assert {c.run_id for c in tracker.children("parent-1")} == {
            "child-1a",
            "child-1b",
        }
        assert {c.run_id for c in tracker.children("parent-2")} == {"child-2a"}
