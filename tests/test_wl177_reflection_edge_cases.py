"""WL-177 parser/reflection edge-case tests."""

from __future__ import annotations

import pytest

from thegent.integrations.gh_project_sync import (
    _status_from_github,
    _status_to_github_option,
)
from thegent.integrations.linear_graphql import (
    LinearGraphQLError,
    _status_from_linear,
    _status_to_linear_type,
)
from thegent.integrations.workstream_autosync import WorkstreamItem, WorkstreamParser


def test_wl177_github_status_mapping_edge_values() -> None:
    """# @trace WL-177"""
    assert _status_to_github_option("  in progress  ") == "In Progress"
    assert _status_to_github_option("review") == "In Progress"
    assert _status_to_github_option("unknown_status") == "Todo"


def test_wl177_github_status_from_nested_option() -> None:
    """# @trace WL-177"""
    item = {
        "fieldValues": [
            {"field": "Status", "option": {"name": "Done"}},
        ]
    }
    assert _status_from_github(item) == "COMPLETED"


def test_wl177_linear_status_mapping_edge_values() -> None:
    """# @trace WL-177"""
    assert _status_to_linear_type("CLAIMED") == "started"
    assert _status_to_linear_type("done") == "completed"
    with pytest.raises(LinearGraphQLError, match="Unsupported local status"):
        _status_to_linear_type("mystery")


def test_wl177_linear_status_from_name_only() -> None:
    """# @trace WL-177"""
    assert _status_from_linear({"name": "In Progress"}) == "IN PROGRESS"
    assert _status_from_linear({"name": "Done"}) == "COMPLETED"
    assert _status_from_linear({}) == "BACKLOG"


def test_wl177_sync_sla_annotations_updates_and_appends() -> None:
    """# @trace WL-177"""
    text = "### [WL-701] Item One\n**Status:** BACKLOG\n**SLA:** 2h\n\n### [WL-702] Item Two\n**Status:** IN PROGRESS\n"
    items = [
        WorkstreamItem(
            item_id="WL-701",
            title="Item One",
            status="BACKLOG",
            priority="P1",
            area="test",
            sla_hours=6.0,
        ),
        WorkstreamItem(
            item_id="WL-702",
            title="Item Two",
            status="IN PROGRESS",
            priority="P1",
            area="test",
            sla_hours=3.5,
        ),
    ]

    updated = WorkstreamParser.sync_sla_annotations(text, items=items)
    assert "**SLA:** 6.0h" in updated
    assert "### [WL-702] Item Two\n**Status:** IN PROGRESS\n**SLA:** 3.5h" in updated
