"""WL-179 Linear GraphQL sync integration tests with deterministic fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from thegent.integrations.connector_mapping_cache import ConnectorMappingCache
from thegent.integrations.linear_graphql import (
    LinearGraphQLConfig,
    LinearGraphQLError,
    sync_from_linear,
    sync_to_linear,
)


@dataclass
class _FakeResponse:
    status_code: int
    payload: dict[str, Any]
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.payload


def test_wl179_sync_to_linear_upsert(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """# @trace WL-179"""
    posted_queries: list[str] = []
    posted_inputs: list[dict[str, Any]] = []
    team_bundle = {
        "data": {
            "teams": {
                "nodes": [
                    {
                        "id": "TEAM_1",
                        "key": "OPS",
                        "states": {
                            "nodes": [
                                {"id": "S_UNSTARTED", "name": "Todo", "type": "unstarted"},
                                {"id": "S_STARTED", "name": "In Progress", "type": "started"},
                                {"id": "S_DONE", "name": "Done", "type": "completed"},
                            ]
                        },
                        "issues": {
                            "nodes": [
                                {
                                    "id": "ISSUE_1",
                                    "identifier": "OPS-1",
                                    "title": "[WL-1790] Existing item",
                                    "state": {"id": "S_UNSTARTED", "name": "Todo", "type": "unstarted"},
                                }
                            ]
                        },
                    }
                ]
            }
        }
    }

    def fake_post(url: str, headers: dict[str, str], timeout: float, **kwargs: Any) -> _FakeResponse:
        assert url.endswith("/graphql")
        assert headers["Authorization"] == "api_key"
        assert timeout == 30.0
        payload = kwargs["json"]
        query = payload["query"]
        posted_queries.append(query)
        variables = payload.get("variables", {})
        if "query TeamBundle" in query:
            return _FakeResponse(status_code=200, payload=team_bundle)
        if "mutation CreateIssue" in query:
            posted_inputs.append(variables["input"])
            return _FakeResponse(
                status_code=200,
                payload={"data": {"issueCreate": {"success": True, "issue": {"id": "ISSUE_2"}}}},
            )
        if "mutation UpdateIssue" in query:
            posted_inputs.append(variables["input"])
            return _FakeResponse(
                status_code=200,
                payload={"data": {"issueUpdate": {"success": True, "issue": {"id": "ISSUE_1"}}}},
            )
        raise AssertionError(f"unexpected query: {query}")

    monkeypatch.setattr("httpx.post", fake_post)

    cache_path = tmp_path / "connector_mapping_cache.json"
    config = LinearGraphQLConfig(api_key="api_key", team_key="OPS", mapping_cache_path=cache_path)
    result = sync_to_linear(
        config,
        [
            {"item_id": "WL-1790", "title": "Existing item", "status": "IN PROGRESS"},
            {"item_id": "WL-1791", "title": "Create me", "status": "BACKLOG"},
        ],
    )

    assert result["items_updated"] == 1
    assert result["items_created"] == 1
    assert result["errors"] == []
    assert any("query TeamBundle" in q for q in posted_queries)
    assert any(inp.get("stateId") == "S_STARTED" for inp in posted_inputs)
    assert any(inp.get("stateId") == "S_UNSTARTED" for inp in posted_inputs)
    cache = ConnectorMappingCache(cache_file=cache_path)
    assert cache.get("linear", "state:unstarted") == "S_UNSTARTED"
    assert cache.get("linear", "state:started") == "S_STARTED"
    assert cache.get("linear", "state:completed") == "S_DONE"


def test_wl179_linear_schema_drift_detected_via_cached_state_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """# @trace WL-179"""
    team_bundle = {
        "data": {
            "teams": {
                "nodes": [
                    {
                        "id": "TEAM_1",
                        "key": "OPS",
                        "states": {
                            "nodes": [
                                {"id": "S_UNSTARTED_V2", "name": "Todo", "type": "unstarted"},
                                {"id": "S_STARTED", "name": "In Progress", "type": "started"},
                                {"id": "S_DONE", "name": "Done", "type": "completed"},
                            ]
                        },
                        "issues": {"nodes": []},
                    }
                ]
            }
        }
    }

    cache_path = tmp_path / "connector_mapping_cache.json"
    posted_queries: list[str] = []
    cache = ConnectorMappingCache(cache_file=cache_path)
    cache.bootstrap(
        "linear",
        {
            "state:unstarted": "S_UNSTARTED_OLD",
            "state:started": "S_STARTED",
            "state:completed": "S_DONE",
        },
    )

    def fake_post(url: str, headers: dict[str, str], timeout: float, **kwargs: Any) -> _FakeResponse:
        _ = headers, timeout
        assert url.endswith("/graphql")
        payload = kwargs["json"]
        query = payload["query"]
        posted_queries.append(query)
        if "query TeamBundle" in query:
            return _FakeResponse(status_code=200, payload=team_bundle)
        raise AssertionError(f"unexpected query: {query}")

    monkeypatch.setattr("httpx.post", fake_post)

    with pytest.raises(LinearGraphQLError, match="Linear schema drift"):
        sync_to_linear(
            LinearGraphQLConfig(api_key="api_key", team_key="OPS", mapping_cache_path=cache_path),
            [{"item_id": "WL-1794", "title": "Drifted item", "status": "BACKLOG"}],
        )

    assert len(posted_queries) == 1
    assert "mutation CreateIssue" not in posted_queries[0]


def test_wl179_sync_from_linear_status_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    """# @trace WL-179"""
    team_bundle = {
        "data": {
            "teams": {
                "nodes": [
                    {
                        "id": "TEAM_1",
                        "key": "OPS",
                        "states": {"nodes": []},
                        "issues": {
                            "nodes": [
                                {
                                    "id": "ISSUE_10",
                                    "identifier": "OPS-10",
                                    "title": "[WL-1792] Done item",
                                    "state": {"name": "Done", "type": "completed"},
                                },
                                {
                                    "id": "ISSUE_11",
                                    "identifier": "OPS-11",
                                    "title": "[WL-1793] Active item",
                                    "state": {"name": "In Progress", "type": "started"},
                                },
                            ]
                        },
                    }
                ]
            }
        }
    }

    def fake_post(url: str, headers: dict[str, str], timeout: float, **kwargs: Any) -> _FakeResponse:
        assert url.endswith("/graphql")
        assert headers["Authorization"] == "api_key"
        assert timeout == 30.0
        payload = kwargs["json"]
        assert "query TeamBundle" in payload["query"]
        return _FakeResponse(status_code=200, payload=team_bundle)

    monkeypatch.setattr("httpx.post", fake_post)

    result = sync_from_linear(LinearGraphQLConfig(api_key="api_key", team_key="OPS"))
    by_item_id = {item["item_id"]: item for item in result["items"]}

    assert result["items_imported"] == 2
    assert by_item_id["WL-1792"]["status"] == "COMPLETED"
    assert by_item_id["WL-1793"]["status"] == "IN PROGRESS"
