"""Unit tests for prune orphan-by-ppid logic."""

from __future__ import annotations

import pytest

from thegent.prune_utils import is_agent_in_cmd, is_orphan_by_ppid

pytestmark = pytest.mark.unit


class TestIsAgentInCmd:
    """Tests for is_agent_in_cmd."""

    def test_cursor_agent(self) -> None:
        assert is_agent_in_cmd("/usr/bin/cursor-agent --resume=abc") is True
        assert is_agent_in_cmd("cursor agent run") is True

    def test_claude_code(self) -> None:
        assert is_agent_in_cmd("/opt/claude-code/bin/claude") is True
        assert is_agent_in_cmd("claude code --model sonnet") is True

    def test_codex(self) -> None:
        assert is_agent_in_cmd("/usr/local/bin/codex") is True
        assert is_agent_in_cmd("codex run task") is True
        assert is_agent_in_cmd("/Users/kooshapari/.ante/bin/ante --model glm-5") is True
        assert is_agent_in_cmd("fanta --model MiniMax-M2.5") is True

    def test_non_agent(self) -> None:
        assert is_agent_in_cmd("node pyright-langserver") is False
        assert is_agent_in_cmd("npm exec @playwright/mcp") is False
        assert is_agent_in_cmd("") is False


class TestIsOrphanByPpid:
    """Tests for is_orphan_by_ppid."""

    def test_orphan_chain_to_init(self) -> None:
        # LSP (100) -> non-agent parent (50) -> init (1); no agent
        parent_map = {100: 50, 50: 1}
        cmd_map = {
            100: "node pyright",
            50: "/usr/libexec/non-agent-helper",
            1: "/sbin/init",
        }
        assert is_orphan_by_ppid(100, parent_map, cmd_map) is True

    def test_keep_when_agent_in_chain(self) -> None:
        # LSP (100) -> cursor-agent (50) -> ...
        parent_map = {100: 50, 50: 1}
        cmd_map = {
            100: "node pyright",
            50: "cursor-agent --resume=abc",
            1: "/sbin/init",
        }
        assert is_orphan_by_ppid(100, parent_map, cmd_map) is False

    def test_keep_when_claude_parent(self) -> None:
        parent_map = {200: 80, 80: 1}
        cmd_map = {200: "node cc-status", 80: "/opt/claude-code/bin/claude", 1: "init"}
        assert is_orphan_by_ppid(200, parent_map, cmd_map) is False

    def test_orphan_when_parent_unknown(self) -> None:
        parent_map = {}
        cmd_map = {}
        assert is_orphan_by_ppid(999, parent_map, cmd_map) is True
