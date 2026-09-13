"""Unit tests for agent and droid registry."""

from pathlib import Path

import pytest

from thegent.agents import get_runner, list_agent_names, list_droid_names
from thegent.agents.codex_proxy import CodexProxyRunner
from thegent.agents.cursor_api_runner import CursorApiRunner
from thegent.agents.direct_agents import DirectAgentRunner


@pytest.mark.unit
class TestListAgentNames:
    """Tests for list_agent_names."""

    def test_returns_all_agents(self) -> None:
        # @trace FR-AGT-007
        """Returns expected agent names."""
        names = list_agent_names()
        expected = {
            "gemini",
            "codex",
            "copilot",
            "cursor-agent",
            "cursor-api",
            "claude",
            "antigravity",
            "minimax",
            "glm",
            "zen",
            "summarizer",
            "cliproxy",
            "roo",
            "kilo",
            "opencode",
        }
        assert set(names) == expected
        assert len(names) == len(expected)


@pytest.mark.unit
class TestListDroidNames:
    """Tests for list_droid_names."""

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        # @trace FR-AGT-007
        """Empty dir returns empty list."""
        assert list_droid_names(tmp_path) == []

    def test_returns_md_stems(self, tmp_path: Path) -> None:
        # @trace FR-AGT-007
        """Returns stem of each .md file."""
        (tmp_path / "plan-orchestrator.md").touch()
        (tmp_path / "code-reviewer.md").touch()
        (tmp_path / "readme.md").touch()
        names = list_droid_names(tmp_path)
        assert "plan-orchestrator" in names
        assert "code-reviewer" in names
        assert "readme" in names
        assert len(names) == 3

    def test_ignores_non_md(self, tmp_path: Path) -> None:
        # @trace FR-AGT-007
        """Ignores non-.md files."""
        (tmp_path / "foo.md").touch()
        (tmp_path / "bar.txt").touch()
        names = list_droid_names(tmp_path)
        assert names == ["foo"]

    def test_nonexistent_dir_returns_empty(self) -> None:
        # @trace FR-AGT-007
        """Nonexistent dir returns empty list."""
        assert list_droid_names(Path("/nonexistent/path/xyz")) == []


@pytest.mark.unit
class TestGetRunner:
    """Tests for get_runner."""

    def test_returns_direct_runner_for_gemini(self) -> None:
        # @trace FR-AGT-007
        """Returns CodexProxyRunner for gemini (proxy path)."""
        runner = get_runner("gemini")
        assert runner is not None
        assert isinstance(runner, CodexProxyRunner)
        assert runner.agent_name == "gemini"

    def test_cursor_label_resolves_to_cursor_agent(self) -> None:
        # @trace FR-AGT-007
        """Label 'cursor' resolves to cursor-agent runner."""
        runner = get_runner("cursor")
        assert runner is not None
        assert isinstance(runner, DirectAgentRunner)
        assert runner.agent_name == "cursor-agent"

    def test_returns_none_for_unknown(self) -> None:
        # @trace FR-AGT-007
        """Returns None for unknown agent name."""
        assert get_runner("unknown-agent") is None

    def test_returns_proxy_runner_for_minimax_glm(self) -> None:
        # @trace FR-AGT-007
        """Returns CodexProxyRunner for minimax/glm (same backend as antigravity)."""
        for agent in ("minimax", "glm"):
            runner = get_runner(agent)
            assert runner is not None
            assert isinstance(runner, CodexProxyRunner)
            assert runner.agent_name == agent

    def test_all_agents_have_runners(self) -> None:
        # @trace FR-AGT-007
        """Every list_agent_names entry has a runner."""
        proxy_agents = {"antigravity", "minimax", "glm", "cliproxy", "roo", "kilo"}
        proxy_agents.update({"gemini", "codex", "copilot", "claude", "zen", "summarizer"})
        cursor_api_agents = {"cursor-api"}
        for name in list_agent_names():
            runner = get_runner(name)
            assert runner is not None, f"Missing runner for {name}"
            if name in proxy_agents:
                assert isinstance(runner, CodexProxyRunner)
            elif name in cursor_api_agents:
                assert isinstance(runner, CursorApiRunner)
            else:
                assert isinstance(runner, DirectAgentRunner)

    def test_returns_cursor_api_runner_for_cursor_api(self) -> None:
        # @trace FR-AGT-007
        """Returns CursorApiRunner for cursor-api."""
        runner = get_runner("cursor-api")
        assert runner is not None
        assert isinstance(runner, CursorApiRunner)

    def test_raises_runtime_error_when_teammate_runner_fails(self, monkeypatch) -> None:
        """Unexpected teammate errors fail loudly via RuntimeError."""
        # @trace WL-3008

        class _CrashyTeammateRunner:
            def __init__(self, teammate_id: str) -> None:
                raise RuntimeError("teammate backend failure")

        import thegent.agents.teammate_runner as teammate_runner_module

        monkeypatch.setattr(teammate_runner_module, "TeammateRunner", _CrashyTeammateRunner)
        with pytest.raises(RuntimeError, match="Failed to create teammate runner"):
            get_runner("custom-teammate")


@pytest.mark.unit
class TestGetFallbackAgents:
    """Tests for get_fallback_agents() edge cases."""

    def test_fallback_for_gemini_excludes_self(self) -> None:
        # @trace FR-AGT-008
        """Fallback chain for gemini does not include gemini."""
        from thegent.agents.registry import get_fallback_agents

        fallbacks = get_fallback_agents("gemini")
        assert "gemini" not in fallbacks
        assert len(fallbacks) > 0

    def test_fallback_for_unknown_agent_empty(self) -> None:
        # @trace FR-AGT-008
        """Unknown agent returns empty fallback list."""
        from thegent.agents.registry import get_fallback_agents

        fallbacks = get_fallback_agents("nonexistent-agent")
        assert fallbacks == []

    def test_fallback_for_alias_resolves(self) -> None:
        # @trace FR-AGT-008
        """Alias 'cursor' resolves to cursor-agent fallback chain."""
        from thegent.agents.registry import get_fallback_agents

        fallbacks = get_fallback_agents("cursor")
        # 'cursor' aliases to 'cursor-agent', which has a fallback chain
        assert len(fallbacks) > 0
        assert "cursor-agent" not in fallbacks


@pytest.mark.unit
class TestResolveAgent:
    """Tests for resolve_agent() with unknown and alias inputs."""

    def test_resolve_unknown_returns_same(self) -> None:
        # @trace FR-AGT-007
        """Unknown agent name returns same name (passthrough)."""
        from thegent.agents.registry import resolve_agent

        assert resolve_agent("unknown-xyz") == "unknown-xyz"

    def test_resolve_cursor_alias(self) -> None:
        # @trace FR-AGT-007
        """'cursor' resolves to 'cursor-agent'."""
        from thegent.agents.registry import resolve_agent

        assert resolve_agent("cursor") == "cursor-agent"


@pytest.mark.unit
class TestListAgentNamesEdgeCases:
    """Edge case tests for list_agent_names()."""

    def test_list_agent_names_returns_list_type(self) -> None:
        # @trace FR-AGT-007
        """list_agent_names returns a list (not tuple/set)."""
        names = list_agent_names()
        assert isinstance(names, list)

    def test_list_agent_names_no_duplicates(self) -> None:
        # @trace FR-AGT-007
        """list_agent_names has no duplicate entries."""
        names = list_agent_names()
        assert len(names) == len(set(names))
