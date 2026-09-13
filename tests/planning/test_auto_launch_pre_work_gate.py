"""Unit tests for pre-work hard-gate enforcement in auto-launch start paths."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _blocked_payload() -> dict[str, object]:
    return {
        "governance_blocked": True,
        "error": "Pre-work hard gate blocked new work start: missing or stale verification evidence.",
        "remediation": "Refresh evidence and retry.",
        "governance_block": {
            "gate": "WP-HG-05.pre_work_hard_gate",
            "remediation_steps": ["step-1"],
        },
        "next_items": [],
        "count": 0,
        "sources_checked": [],
    }


def _make_system() -> object:
    from thegent.planning.auto_launch import AutoLaunchSystem

    with patch.object(AutoLaunchSystem, "__init__", lambda self, *a, **kw: None):
        system = AutoLaunchSystem.__new__(AutoLaunchSystem)
    system.db = MagicMock()
    system.record_event = MagicMock()
    system.launch_batch = AsyncMock()
    system.settings = SimpleNamespace(default_timeout=60, owner_tag="auto-launch")
    return system


@pytest.mark.unit
def test_try_launch_next_blocks_on_governance_gate() -> None:
    """Fallback do_next path records governance block and does not launch."""
    system = _make_system()
    system.db.get_ready_items.return_value = []

    with patch(
        "thegent.cli.commands.impl.do_next_impl", return_value=_blocked_payload()
    ):
        asyncio.get_event_loop().run_until_complete(system._try_launch_next())

    system.launch_batch.assert_not_called()
    system.record_event.assert_called_once()
    assert system.record_event.call_args.args[0] == "governance_blocked"


@pytest.mark.unit
def test_launch_item_blocks_before_bg_when_claim_gate_fails() -> None:
    """Auto-launch claim/start path stops before bg launch when gate blocks claim."""
    system = _make_system()

    claim_block = {
        "success": False,
        "governance_blocked": True,
        "error": "Pre-work hard gate blocked new work start: missing or stale verification evidence.",
        "remediation": "Refresh evidence and retry.",
        "governance_block": {"gate": "WP-HG-05.pre_work_hard_gate"},
    }

    with (
        patch(
            "thegent.cli.commands.impl.work_stream_claim_impl", return_value=claim_block
        ),
        patch("thegent.cli.commands.impl.bg_impl") as mock_bg_impl,
    ):
        asyncio.get_event_loop().run_until_complete(
            system._launch_item(
                {"item_id": "WP-1", "prompt_suggestion": "Do it"},
                "critical",
                "gpt-4o-mini",
                0.01,
            )
        )

    mock_bg_impl.assert_not_called()
    system.record_event.assert_called_once()
    assert system.record_event.call_args.args[0] == "claim_failed"
