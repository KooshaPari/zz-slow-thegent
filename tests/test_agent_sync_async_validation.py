"""Validate every agent returns successfully for both sync and async execution.

Runs run_impl directly (sync) and via asyncio.to_thread (async) for each agent.
Skips agents whose runner is unavailable (e.g. CLI not installed).
Skips proxy agents (antigravity, minimax, glm, cliproxy) when proxy returns 404/502/unknown provider.
See docs/guides/PROVIDER_SETUP_GUIDE.md "Quick start: get proxy agents passing".
"""

import asyncio
import re
from pathlib import Path

import pytest

from thegent.agents import get_runner, list_agent_names
from thegent.agents.registry import _PROXY_AGENTS
from thegent.cli.commands.impl import run_impl


def _runner_available(agent: str) -> bool:
    """Check if a runner exists for this agent."""
    return get_runner(agent) is not None


def _is_proxy_unavailable(result: dict, agent: str) -> bool:
    """True if failure appears due to proxy config/auth (404, 502, unknown provider)."""
    if result.get("exit_code") == 0:
        return False
    if agent not in _PROXY_AGENTS:
        return False
    stderr = result.get("stderr", "") or ""
    return bool(re.search(r"404|502|unknown provider|/v1/responses", stderr, re.IGNORECASE))


def _is_cursor_api_unavailable(result: dict, agent: str) -> bool:
    """True if failure due to cursor-api not running (agent requires cursor-api server)."""
    if result.get("exit_code") == 0:
        return False
    if agent != "cursor-api":
        return False
    stderr = result.get("stderr", "") or ""
    return bool(re.search(r"cursor-api not reachable|not reachable", stderr, re.IGNORECASE))


def _is_service_unavailable(result: dict, agent: str) -> bool:
    """True if failure appears to be environmental/service health rather than code regression."""
    if result.get("timed_out"):
        return True
    stderr = result.get("stderr", "") or ""
    stdout = result.get("stdout", "") or ""
    combined = f"{stderr}\n{stdout}"
    return bool(
        re.search(
            r"timed out|service unavailable|connection refused|429|rate limit|502|503|504|hit your limit|resets \d",
            combined,
            re.IGNORECASE,
        )
    )


# Minimal prompt: read-only, fast, low token cost
TRIVIAL_PROMPT = "Output only the number 1. Nothing else."


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.parametrize("agent", list_agent_names())
class TestAgentSyncAsyncSuccess:
    """Each agent returns exit_code 0 for both sync and async run_impl."""

    def test_sync_returns_success(self, agent: str, project_root: Path) -> None:
        # @trace FR-AGT-001
        """run_impl (sync) returns exit_code 0 for agent."""
        if not _runner_available(agent):
            pytest.skip(f"Runner not available for {agent}")

        result = run_impl(
            agent=agent,
            prompt=TRIVIAL_PROMPT,
            cd=project_root,
            mode="read-only",
            timeout=60,
            full=False,
        )

        if "error" in result:
            pytest.fail(f"run_impl error: {result['error']}")

        if _is_proxy_unavailable(result, agent):
            pytest.skip(
                f"Proxy agent {agent}: run `thegent mcp up`, `thegent cliproxy login antigravity` (or iflow for glm, "
                f"minimax for api-key). See PROVIDER_SETUP_GUIDE.md. "
                f"Stderr: {result.get('stderr', '')[:150]}"
            )
        if _is_cursor_api_unavailable(result, agent):
            pytest.skip(
                f"cursor-api agent requires cursor-api server at THGENT_CURSOR_API_URL: "
                f"{result.get('stderr', '')[:200]}"
            )
        if _is_service_unavailable(result, agent):
            pytest.skip(f"agent {agent} currently unavailable in this environment: {result.get('stderr', '')[:200]}")

        assert result.get("exit_code") == 0, (
            f"agent={agent} exit_code={result.get('exit_code')} stderr={result.get('stderr', '')[:500]}"
        )

    def test_async_returns_success(self, agent: str, project_root: Path) -> None:
        # @trace FR-AGT-001
        """asyncio.to_thread(run_impl) returns exit_code 0 for agent."""
        if not _runner_available(agent):
            pytest.skip(f"Runner not available for {agent}")

        async def _run() -> dict:
            return await asyncio.to_thread(
                run_impl,
                agent,
                TRIVIAL_PROMPT,
                project_root,
                "read-only",
                60,
                False,
                None,
                None,
            )

        result = asyncio.run(_run())

        if "error" in result:
            pytest.fail(f"run_impl (async) error: {result['error']}")

        if _is_proxy_unavailable(result, agent):
            pytest.skip(
                f"Proxy agent {agent}: run `thegent mcp up`, `thegent cliproxy login antigravity` (or iflow for glm, "
                f"minimax for api-key). See PROVIDER_SETUP_GUIDE.md. "
                f"Stderr: {result.get('stderr', '')[:150]}"
            )
        if _is_cursor_api_unavailable(result, agent):
            pytest.skip(
                f"cursor-api agent requires cursor-api server at THGENT_CURSOR_API_URL: "
                f"{result.get('stderr', '')[:200]}"
            )
        if _is_service_unavailable(result, agent):
            pytest.skip(f"agent {agent} currently unavailable in this environment: {result.get('stderr', '')[:200]}")

        assert result.get("exit_code") == 0, (
            f"agent={agent} exit_code={result.get('exit_code')} stderr={result.get('stderr', '')[:500]}"
        )
