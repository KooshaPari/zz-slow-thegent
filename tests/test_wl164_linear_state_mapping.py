"""Tests for WL-164: explicit Linear state mapping table validation."""

from __future__ import annotations

import pytest

from thegent.integrations.linear_graphql import (
    LinearGraphQLError,
    build_linear_state_mapping,
)


@pytest.mark.requirement("WL-164")
def test_build_linear_state_mapping_requires_todo_in_progress_done() -> None:
    """Missing required Linear state types must fail loudly."""
    states = [
        {"id": "state_unstarted", "name": "Todo", "type": "unstarted"},
        {"id": "state_started", "name": "In Progress", "type": "started"},
    ]
    with pytest.raises(LinearGraphQLError, match="missing required state type mappings"):
        build_linear_state_mapping(states)


@pytest.mark.requirement("WL-164")
def test_build_linear_state_mapping_returns_explicit_table() -> None:
    """All required state types should produce an explicit mapping table."""
    states = [
        {"id": "state_unstarted", "name": "Todo", "type": "unstarted"},
        {"id": "state_started", "name": "In Progress", "type": "started"},
        {"id": "state_completed", "name": "Done", "type": "completed"},
    ]
    mapping = build_linear_state_mapping(states)
    assert mapping == {
        "unstarted": "state_unstarted",
        "started": "state_started",
        "completed": "state_completed",
    }
