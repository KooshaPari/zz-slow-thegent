from __future__ import annotations

from pathlib import Path

import orjson as json

from thegent.mcp.server.tools_locking_planning import thegent_plan_incorporate_impl
from thegent.mcp.server.tools_workstream_lsp import (
    workstream_claim_tool_impl,
    workstream_complete_tool_impl,
)


def _extract_json_content(content: object) -> dict[str, object]:
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(content, list) and content:
        text = getattr(content[0], "text", None)
        if isinstance(text, str):
            return json.loads(text)
    raise TypeError(f"Unsupported ToolResult content type: {type(content)!r}")


def test_workstream_claim_tool_impl_wraps_claim_result() -> None:
    calls: list[tuple[str, str]] = []

    def _claim(item_id: str, agent_id: str) -> dict[str, object]:
        calls.append((item_id, agent_id))
        return {"success": True, "item_id": item_id, "agent_id": agent_id}

    result = workstream_claim_tool_impl(
        item_id="WL-9", agent_id="agent-sync", claim_impl=_claim
    )

    assert calls == [("WL-9", "agent-sync")]
    assert result.structured_content == {
        "success": True,
        "item_id": "WL-9",
        "agent_id": "agent-sync",
    }
    assert _extract_json_content(result.content) == result.structured_content
    assert result.meta and result.meta["execution_time_ms"] >= 0


def test_workstream_complete_tool_impl_wraps_complete_result() -> None:
    calls: list[tuple[str, str]] = []

    def _complete(item_id: str, agent_id: str) -> dict[str, object]:
        calls.append((item_id, agent_id))
        return {"success": True, "completed": item_id, "agent": agent_id}

    result = workstream_complete_tool_impl(
        item_id="WL-10", agent_id="agent-sync", complete_impl=_complete
    )

    assert calls == [("WL-10", "agent-sync")]
    assert result.structured_content == {
        "success": True,
        "completed": "WL-10",
        "agent": "agent-sync",
    }
    assert _extract_json_content(result.content) == result.structured_content
    assert result.meta and result.meta["execution_time_ms"] >= 0


def test_workstream_sync_plan_incorporate_forwards_cd_and_dry_run() -> None:
    calls: list[tuple[Path | None, bool]] = []

    def _incorporate(*, cd: Path | None, dry_run: bool) -> dict[str, object]:
        calls.append((cd, dry_run))
        return {"merged": 3, "dry_run": dry_run, "target": str(cd) if cd else "cwd"}

    result = thegent_plan_incorporate_impl(
        cd="/tmp/workstream-sync", dry_run=True, incorporate_impl=_incorporate
    )

    assert calls == [(Path("/tmp/workstream-sync"), True)]
    assert result.structured_content == {
        "merged": 3,
        "dry_run": True,
        "target": "/tmp/workstream-sync",
    }
    assert _extract_json_content(result.content) == result.structured_content
    assert result.meta and result.meta["execution_time_ms"] >= 0


# noqa: PT018
