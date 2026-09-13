"""WL-178 GitHub sync integration tests with deterministic gh fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson as json
import pytest

from thegent.integrations.connector_mapping_cache import ConnectorMappingCache
from thegent.integrations.gh_project_sync import (
    GHProjectConfig,
    GHProjectSyncError,
    sync_from_github,
    sync_to_github,
)


@pytest.fixture
def wl178_config(tmp_path: Path) -> GHProjectConfig:
    """# @trace WL-178"""
    return GHProjectConfig(
        enabled=True,
        owner="acme",
        number=42,
        direction="bidirectional",
        standalone_mode=False,
        mapping_cache_path=tmp_path / "connector_mapping_cache.json",
    )


def test_wl178_push_upsert_path(monkeypatch: pytest.MonkeyPatch, wl178_config: GHProjectConfig) -> None:
    """# @trace WL-178"""
    calls: list[list[str]] = []

    def fake_run(args: list[str], capture: bool = True) -> tuple[int, str, str]:
        _ = capture
        calls.append(args)
        if args[:3] == ["project", "view", "42"]:
            return 0, json.dumps({"id": "PVT_1", "title": "Ops", "url": "https://example", "items": []}).decode(), ""
        if args[:3] == ["project", "item-list", "42"]:
            payload = [{"id": "ITM_1", "content": {"title": "[WL-1780] Existing item"}}]
            return 0, json.dumps(payload).decode(), ""
        if args[:3] == ["project", "field-list", "42"]:
            payload = [
                {
                    "id": "F_STATUS",
                    "name": "Status",
                    "options": [
                        {"id": "OPT_TODO", "name": "Todo"},
                        {"id": "OPT_PROGRESS", "name": "In Progress"},
                        {"id": "OPT_DONE", "name": "Done"},
                    ],
                },
                {
                    "id": "F_PRIORITY",
                    "name": "Priority",
                    "options": [
                        {"id": "P1", "name": "P1"},
                        {"id": "P2", "name": "P2"},
                        {"id": "P3", "name": "P3"},
                    ],
                },
            ]
            return 0, json.dumps(payload).decode(), ""
        if args[:2] == ["project", "item-create"]:
            return 0, json.dumps({"id": "ITM_2"}).decode(), ""
        if args[:2] == ["project", "item-edit"]:
            return 0, "{}", ""
        raise AssertionError(f"unexpected gh args: {args}")

    monkeypatch.setattr("thegent.integrations.gh_project_sync._run_gh_command", fake_run)

    result = sync_to_github(
        wl178_config,
        [
            {"item_id": "WL-1780", "title": "Existing item", "status": "IN PROGRESS"},
            {"item_id": "WL-1781", "title": "New item", "status": "BACKLOG"},
        ],
    )

    assert result["items_updated"] == 1
    assert result["items_created"] == 1
    assert result["errors"] == []
    assert any(cmd[:2] == ["project", "item-create"] for cmd in calls)
    assert any(cmd[:2] == ["project", "item-edit"] and "--single-select-option-id" in cmd for cmd in calls)
    cache = ConnectorMappingCache(cache_file=wl178_config.mapping_cache_path)
    assert cache.get("github", "field:status") == "F_STATUS"
    assert cache.get("github", "field:priority") == "F_PRIORITY"


def test_wl178_pull_normalizes_status(monkeypatch: pytest.MonkeyPatch, wl178_config: GHProjectConfig) -> None:
    """# @trace WL-178"""
    payload: list[dict[str, Any]] = [
        {
            "id": "ITM_A",
            "content": {"title": "[WL-1782] Track me"},
            "fieldValues": [{"field": "Status", "option": {"name": "Done"}}],
        },
        {
            "id": "ITM_B",
            "content": {"title": "[WL-1783] Start me"},
            "fieldValues": [{"field": "Status", "option": {"name": "In Progress"}}],
        },
    ]

    def fake_run(args: list[str], capture: bool = True) -> tuple[int, str, str]:
        _ = capture
        if args[:3] == ["project", "item-list", "42"]:
            return 0, json.dumps(payload).decode(), ""
        raise AssertionError(f"unexpected gh args: {args}")

    monkeypatch.setattr("thegent.integrations.gh_project_sync._run_gh_command", fake_run)

    result = sync_from_github(wl178_config)
    by_id = {entry["item_id"]: entry for entry in result["items"]}

    assert result["items_imported"] == 2
    assert by_id["WL-1782"]["status"] == "COMPLETED"
    assert by_id["WL-1783"]["status"] == "IN PROGRESS"


def test_wl178_sync_to_github_fails_fast_on_missing_status_field(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """# @trace WL-178"""
    wl_config = GHProjectConfig(
        enabled=True,
        owner="acme",
        number=42,
        direction="bidirectional",
        standalone_mode=False,
        mapping_cache_path=tmp_path / "connector_mapping_cache.json",
    )
    calls: list[list[str]] = []

    def fake_run(args: list[str], capture: bool = True) -> tuple[int, str, str]:
        calls.append(args)
        _ = capture
        if args[:3] == ["project", "view", "42"]:
            return 0, json.dumps({"id": "PVT_1", "items": []}).decode(), ""
        if args[:3] == ["project", "item-list", "42"]:
            return 0, json.dumps([]).decode(), ""
        if args[:3] == ["project", "field-list", "42"]:
            return (
                0,
                json.dumps(
                    [{"id": "F_PRIORITY", "name": "Priority", "options": [{"id": "P1", "name": "P1"}]}],
                ).decode(),
                "",
            )
        raise AssertionError(f"unexpected gh args: {args}")

    monkeypatch.setattr("thegent.integrations.gh_project_sync._run_gh_command", fake_run)

    with pytest.raises(GHProjectSyncError, match="required single-select field 'status' is missing"):
        sync_to_github(
            wl_config,
            [{"item_id": "WL-1784", "title": "Needs status", "status": "BACKLOG"}],
        )

    assert not any(cmd[:2] == ["project", "item-create"] for cmd in calls)
    assert not any(cmd[:2] == ["project", "item-edit"] for cmd in calls)
