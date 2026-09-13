"""Unit tests for sync conflict surfacing.

# @trace WL-204
"""

from __future__ import annotations

import pytest

from thegent.sync.conflicts import (
    SyncConflict,
    recommend_action,
    render_conflict_surface,
)


@pytest.mark.requirement("WL-204")
def test_recommend_action_uses_remote_when_local_empty():
    conflict = SyncConflict(
        conflict_id="c1",
        wl_id="WL-204",
        field="priority",
        local_value="",
        remote_value="P1",
        connector="github",
    )
    assert recommend_action(conflict) == "adopt_remote"


@pytest.mark.requirement("WL-204")
def test_render_conflict_surface_only_shows_unresolved():
    unresolved = SyncConflict(
        conflict_id="c1",
        wl_id="WL-204",
        field="status",
        local_value="BACKLOG",
        remote_value="IN PROGRESS",
        connector="linear",
    )
    resolved = SyncConflict(
        conflict_id="c2",
        wl_id="WL-204",
        field="owner",
        local_value="alice",
        remote_value="bob",
        connector="github",
        resolved=True,
    )
    lines = render_conflict_surface([unresolved, resolved])
    assert len(lines) == 1
    assert "c1" in lines[0]
    assert "action=manual_review" in lines[0]
