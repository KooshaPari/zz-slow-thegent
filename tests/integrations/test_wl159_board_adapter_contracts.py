"""Adapter contract tests for GitHub/Linear board adapters."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from thegent.sync.board_adapters import GitHubBoardAdapter, LinearBoardAdapter


def test_github_adapter_sync_payload_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    """GitHub adapter sends item_id/title/status payload entries expected by sync transport."""
    captured: dict[str, list[dict[str, str]]] = {}

    def fake_sync_to_github(config, payload):
        captured["payload"] = payload
        return {"synced": 1, "failed": 0, "errors": []}

    monkeypatch.setattr(
        "thegent.integrations.gh_project_sync.sync_to_github", fake_sync_to_github
    )
    adapter = GitHubBoardAdapter()

    result = adapter.sync(
        board_id="org:42",
        work_stream_items=[
            {"id": "WL-159", "title": "Board Item", "status": "IN PROGRESS"},
            {"id": "WL-160", "title": "Second", "status": "COMPLETED"},
        ],
    )

    assert result["synced"] == 2
    assert captured["payload"][0] == {
        "item_id": "WL-159",
        "id": "WL-159",
        "title": "[WL-159] Board Item",
        "status": "IN PROGRESS",
    }
    assert captured["payload"][1] == {
        "item_id": "WL-160",
        "id": "WL-160",
        "title": "[WL-160] Second",
        "status": "COMPLETED",
    }


def test_github_adapter_fetch_remote_status_filters_and_maps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GitHub read path filters to requested items and maps item_id/status."""

    def fake_sync_from_github(config):
        _ = config
        return {
            "items": [
                {"item_id": "WL-160", "status": "COMPLETED"},
                {"item_id": "WL-999", "status": "BACKLOG"},
            ]
        }

    monkeypatch.setattr(
        "thegent.integrations.gh_project_sync.sync_from_github", fake_sync_from_github
    )
    adapter = GitHubBoardAdapter()

    status_map = adapter.fetch_remote_status(
        board_id="org:42",
        work_stream_items=[
            {"id": "WL-159", "title": "A", "status": "BACKLOG"},
            {"id": "WL-160", "title": "B", "status": "BACKLOG"},
        ],
    )

    assert status_map == {"WL-160": "COMPLETED"}


def test_github_adapter_fetch_remote_status_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transient failures on read path are retried before success."""
    call_count = SimpleNamespace(count=0)

    def fake_sync_from_github(config):
        _ = config
        call_count.count += 1
        if call_count.count == 1:
            raise RuntimeError("transient")
        return {"items": [{"item_id": "WL-159", "status": "IN PROGRESS"}]}

    monkeypatch.setattr(
        "thegent.integrations.gh_project_sync.sync_from_github", fake_sync_from_github
    )
    adapter = GitHubBoardAdapter()

    status_map = adapter.fetch_remote_status(
        board_id="org:42",
        work_stream_items=[{"id": "WL-159", "title": "A", "status": "BACKLOG"}],
    )

    assert status_map == {"WL-159": "IN PROGRESS"}
    assert call_count.count == 2


def test_github_adapter_fetch_remote_status_requires_board_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid GitHub locator surfaces as a user-visible error."""
    adapter = GitHubBoardAdapter()
    with pytest.raises(ValueError, match="GitHub board ID is required"):
        adapter.sync(board_id="", work_stream_items=[])


def test_linear_adapter_sync_payload_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    """Linear adapter maps payload fields for create/update upsert path."""
    created: list[tuple[str, str, str]] = []
    updated: list[tuple[str, str, str]] = []

    monkeypatch.setattr(
        "thegent.sync.board_adapters.os.getenv",
        lambda key, default=None: {"THGENT_LINEAR_API_KEY": "token"}.get(key, default),
    )
    monkeypatch.setattr(
        "thegent.sync.board_adapters.LinearBoardAdapter._resolve_team_id",
        lambda self, token, team_key: "team-id",
    )

    def fake_find_issue_id(
        _self: LinearBoardAdapter, token: str, team_key: str, title: str
    ) -> str | None:
        assert token == "token"
        assert team_key == "OPS"
        if title.startswith("[WL-160]"):
            return "ISSUE-1"
        return None

    def fake_create_issue(
        _self: LinearBoardAdapter,
        token: str,
        team_id: str,
        title: str,
        description: str,
    ) -> None:
        created.append((token, team_id, title))
        assert "WL: WL-161" in description

    def fake_update_issue(
        _self: LinearBoardAdapter,
        token: str,
        issue_id: str,
        title: str,
        description: str,
    ) -> None:
        updated.append((token, issue_id, title))
        assert "WL: WL-160" in description

    monkeypatch.setattr(
        "thegent.sync.board_adapters.LinearBoardAdapter._find_issue_id",
        fake_find_issue_id,
    )
    monkeypatch.setattr(
        "thegent.sync.board_adapters.LinearBoardAdapter._create_issue",
        fake_create_issue,
    )
    monkeypatch.setattr(
        "thegent.sync.board_adapters.LinearBoardAdapter._update_issue",
        fake_update_issue,
    )

    adapter = LinearBoardAdapter()
    result = adapter.sync(
        board_id="OPS",
        work_stream_items=[
            {"id": "WL-160", "title": "Existing", "status": "IN PROGRESS"},
            {"id": "WL-161", "title": "New", "status": "BACKLOG"},
        ],
    )

    assert result["synced"] == 2
    assert updated == [("token", "ISSUE-1", "[WL-160] Existing")]
    assert created == [("token", "team-id", "[WL-161] New")]


def test_linear_adapter_fetch_remote_status_filters_and_maps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linear read path filters to requested items and maps item_id/status."""
    monkeypatch.setenv("THGENT_LINEAR_API_KEY", "token")
    monkeypatch.setattr(
        "thegent.integrations.linear_graphql.sync_from_linear",
        lambda config: {
            "items": [
                {"item_id": "WL-160", "status": "COMPLETED"},
                {"item_id": "WL-999", "status": "BACKLOG"},
            ]
        },
    )

    adapter = LinearBoardAdapter()
    status_map = adapter.fetch_remote_status(
        board_id="OPS",
        work_stream_items=[{"id": "WL-160", "title": "A", "status": "IN PROGRESS"}],
    )

    assert status_map == {"WL-160": "COMPLETED"}


def test_linear_adapter_fetch_remote_status_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transient failures on Linear read path are retried before success."""
    call_count = SimpleNamespace(count=0)

    def fake_sync_from_linear(config):
        _ = config
        call_count.count += 1
        if call_count.count == 1:
            raise RuntimeError("transient")
        return {"items": [{"item_id": "WL-160", "status": "IN PROGRESS"}]}

    monkeypatch.setenv("THGENT_LINEAR_API_KEY", "token")
    monkeypatch.setattr(
        "thegent.integrations.linear_graphql.sync_from_linear", fake_sync_from_linear
    )

    adapter = LinearBoardAdapter()
    status_map = adapter.fetch_remote_status(
        board_id="OPS",
        work_stream_items=[{"id": "WL-160", "title": "A", "status": "BACKLOG"}],
    )

    assert status_map == {"WL-160": "IN PROGRESS"}
    assert call_count.count == 2


def test_linear_adapter_sync_requires_api_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linear sync should fail clearly if API token is absent."""
    monkeypatch.delenv("THGENT_LINEAR_API_KEY", raising=False)
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    adapter = LinearBoardAdapter()

    with pytest.raises(
        RuntimeError, match="Linear sync requires THGENT_LINEAR_API_KEY"
    ):
        adapter.sync(board_id="OPS", work_stream_items=[])
