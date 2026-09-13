"""Unit tests for pre-work hard-gate parity on MCP start surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import orjson as json
import pytest

pytest.importorskip("fastmcp", reason="fastmcp required for MCP server tests")

import thegent.mcp.server as _mcp_mod

if TYPE_CHECKING:
    from fastmcp.tools.tool import ToolResult


def _json_content(result: ToolResult | str) -> Any:
    if isinstance(result, str):
        return json.loads(result)
    content = result.content
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(content, list) and len(content) > 0:
        text = getattr(content[0], "text", str(content[0]))
        return json.loads(text)
    return json.loads(str(content))


def _blocked_payload() -> dict[str, Any]:
    return {
        "governance_blocked": True,
        "error": "Pre-work hard gate blocked new work start: missing or stale verification evidence.",
        "remediation": "Refresh async/build/e2e verification evidence and retry.",
        "governance_block": {
            "gate": "WP-HG-05.pre_work_hard_gate",
            "remediation_steps": ["step-1", "step-2"],
        },
        "next_items": [],
        "count": 0,
        "sources_checked": [],
    }


@pytest.mark.unit
def test_thegent_do_next_returns_governance_block_payload() -> None:
    """MCP do_next preserves governance_blocked contract from do_next_impl."""
    with patch("thegent.mcp.server.do_next_impl", return_value=_blocked_payload()):
        result = _mcp_mod.thegent_do_next(limit=3)

    data = _json_content(result)
    assert data["governance_blocked"] is True
    assert data["count"] == 0
    assert data["governance_block"]["gate"] == "WP-HG-05.pre_work_hard_gate"
    assert data["remediation"]


@pytest.mark.unit
def test_thegent_plan_get_next_returns_governance_block_error() -> None:
    """MCP get-next wrapper returns blocked payload with remediation when gate fails."""
    with patch("thegent.mcp.server.do_next_impl", return_value=_blocked_payload()):
        result = _mcp_mod.thegent_plan_get_next()

    data = _json_content(result)
    assert data["exit_code"] == 1
    assert data["governance_blocked"] is True
    assert data["error"].startswith("Pre-work hard gate blocked")
    assert data["remediation"]
