"""Tests for FlashAgent — ultra-short-lived single-task LLM agents.

FR Traceability: FR-AGT-020 (flash agent lifecycle)
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.agents.flash_agent import (
    FlashAgent,
    FlashAgentConfig,
    FlashAgentResult,
    flash,
)

if TYPE_CHECKING:
    from contextlib import AbstractContextManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_litellm_response(content: str) -> MagicMock:
    """Build a minimal litellm response mock."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    response = MagicMock()
    response.choices = [choice]
    return response


def _patch_litellm(content: str = "Hello, world!") -> AbstractContextManager:
    """Patch litellm.acompletion to return a canned response."""
    response = _make_litellm_response(content)
    return patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=response,
    )


# ---------------------------------------------------------------------------
# FlashAgentConfig tests
# ---------------------------------------------------------------------------


def test_config_defaults():
    """FR-AGT-020: FlashAgentConfig defaults are correct."""
    cfg = FlashAgentConfig(task_prompt="do something")
    assert cfg.task_prompt == "do something"
    assert cfg.model == "claude-haiku-4.5"
    assert cfg.timeout_s == 30.0
    assert cfg.max_tokens == 1024
    assert cfg.capture_output is True


def test_config_custom_values():
    """FR-AGT-020: FlashAgentConfig respects overridden values."""
    cfg = FlashAgentConfig(
        task_prompt="summarise",
        model="gpt-4o-mini",
        timeout_s=10.0,
        max_tokens=256,
        capture_output=False,
    )
    assert cfg.model == "gpt-4o-mini"
    assert cfg.timeout_s == 10.0
    assert cfg.max_tokens == 256
    assert cfg.capture_output is False


# ---------------------------------------------------------------------------
# FlashAgentResult tests
# ---------------------------------------------------------------------------


def test_result_fields_populated():
    """FR-AGT-020: FlashAgentResult stores all expected fields."""
    result = FlashAgentResult(
        output="answer",
        success=True,
        elapsed_s=1.23,
        agent_id="abc12345",
    )
    assert result.output == "answer"
    assert result.success is True
    assert result.elapsed_s == pytest.approx(1.23)
    assert result.agent_id == "abc12345"


def test_result_failure_fields():
    """FR-AGT-020: FlashAgentResult stores failure state correctly."""
    result = FlashAgentResult(output="", success=False, elapsed_s=30.1, agent_id="dead0000")
    assert result.success is False
    assert result.output == ""
    assert result.elapsed_s > 30.0


# ---------------------------------------------------------------------------
# FlashAgent.run — success path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flash_agent_run_success():
    """FR-AGT-020: FlashAgent.run returns success result on normal completion."""
    with _patch_litellm("The answer is 42."):
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="What is the answer?")
        result = await agent.run(cfg)

    assert result.success is True
    assert result.output == "The answer is 42."
    assert result.elapsed_s >= 0.0
    assert len(result.agent_id) == 8


@pytest.mark.asyncio
async def test_flash_agent_run_populates_agent_id():
    """FR-AGT-020: Each run generates a unique agent_id."""
    with _patch_litellm("ok"):
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="ping")
        r1 = await agent.run(cfg)
        r2 = await agent.run(cfg)

    assert r1.agent_id != r2.agent_id
    assert len(r1.agent_id) == 8
    assert len(r2.agent_id) == 8


@pytest.mark.asyncio
async def test_flash_agent_run_elapsed_is_nonnegative():
    """FR-AGT-020: elapsed_s is always >= 0."""
    with _patch_litellm("done"):
        agent = FlashAgent()
        result = await agent.run(FlashAgentConfig(task_prompt="x"))

    assert result.elapsed_s >= 0.0


@pytest.mark.asyncio
async def test_flash_agent_passes_model_to_litellm():
    """FR-AGT-020: FlashAgent forwards the model parameter to litellm.acompletion."""
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=_make_litellm_response("resp"),
    ) as mock_complete:
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="test", model="gpt-4o-mini")
        await agent.run(cfg)

    call_kwargs = mock_complete.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_flash_agent_passes_max_tokens_to_litellm():
    """FR-AGT-020: FlashAgent forwards max_tokens to litellm.acompletion."""
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=_make_litellm_response("resp"),
    ) as mock_complete:
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="test", max_tokens=512)
        await agent.run(cfg)

    call_kwargs = mock_complete.call_args.kwargs
    assert call_kwargs["max_tokens"] == 512


@pytest.mark.asyncio
async def test_flash_agent_passes_prompt_as_user_message():
    """FR-AGT-020: Prompt is sent as a user message to litellm."""
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=_make_litellm_response("ok"),
    ) as mock_complete:
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="hello agent")
        await agent.run(cfg)

    messages = mock_complete.call_args.kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "hello agent"


@pytest.mark.asyncio
async def test_flash_agent_empty_content_returns_empty_string():
    """FR-AGT-020: If LLM returns None content, output is empty string (not None)."""
    response = _make_litellm_response(None)
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=response,
    ):
        agent = FlashAgent()
        result = await agent.run(FlashAgentConfig(task_prompt="empty"))

    assert isinstance(result.output, str)
    assert result.success is True


# ---------------------------------------------------------------------------
# FlashAgent.run — timeout path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flash_agent_timeout_returns_failure():
    """FR-AGT-020: FlashAgent returns success=False when LLM call exceeds timeout."""

    async def _slow(*args, **kwargs):
        await asyncio.sleep(10)
        return _make_litellm_response("late")

    with patch("thegent.agents.flash_agent.litellm.acompletion", side_effect=_slow):
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="slow task", timeout_s=0.05)
        result = await agent.run(cfg)

    assert result.success is False
    assert result.output == ""


@pytest.mark.asyncio
async def test_flash_agent_timeout_agent_id_still_populated():
    """FR-AGT-020: agent_id is populated even on timeout."""

    async def _slow(*args, **kwargs):
        await asyncio.sleep(10)
        return _make_litellm_response("late")

    with patch("thegent.agents.flash_agent.litellm.acompletion", side_effect=_slow):
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="slow", timeout_s=0.05)
        result = await agent.run(cfg)

    assert len(result.agent_id) == 8


@pytest.mark.asyncio
async def test_flash_agent_timeout_elapsed_s_populated():
    """FR-AGT-020: elapsed_s is populated (and >= timeout) on timeout."""

    async def _slow(*args, **kwargs):
        await asyncio.sleep(10)
        return _make_litellm_response("late")

    timeout = 0.05
    with patch("thegent.agents.flash_agent.litellm.acompletion", side_effect=_slow):
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="slow", timeout_s=timeout)
        result = await agent.run(cfg)

    assert result.elapsed_s >= timeout


# ---------------------------------------------------------------------------
# FlashAgent — model selection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flash_agent_default_model_is_haiku():
    """FR-AGT-020: Default model is claude-haiku-4.5."""
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=_make_litellm_response("resp"),
    ) as mock_complete:
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="test")
        await agent.run(cfg)

    assert mock_complete.call_args.kwargs["model"] == "claude-haiku-4.5"


@pytest.mark.asyncio
async def test_flash_agent_custom_model_forwarded():
    """FR-AGT-020: Custom model string is passed through to litellm."""
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=_make_litellm_response("resp"),
    ) as mock_complete:
        agent = FlashAgent()
        cfg = FlashAgentConfig(task_prompt="test", model="gemini-3-flash")
        await agent.run(cfg)

    assert mock_complete.call_args.kwargs["model"] == "gemini-3-flash"


# ---------------------------------------------------------------------------
# flash() convenience function
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flash_convenience_returns_result():
    """FR-AGT-020: flash() convenience function returns a FlashAgentResult."""
    with _patch_litellm("convenience result"):
        result = await flash("quick task")

    assert isinstance(result, FlashAgentResult)
    assert result.success is True
    assert result.output == "convenience result"


@pytest.mark.asyncio
async def test_flash_convenience_default_model():
    """FR-AGT-020: flash() uses claude-haiku-4.5 by default."""
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=_make_litellm_response("ok"),
    ) as mock_complete:
        await flash("hello")

    assert mock_complete.call_args.kwargs["model"] == "claude-haiku-4.5"


@pytest.mark.asyncio
async def test_flash_convenience_custom_model():
    """FR-AGT-020: flash() forwards custom model parameter."""
    with patch(
        "thegent.agents.flash_agent.litellm.acompletion",
        new_callable=AsyncMock,
        return_value=_make_litellm_response("ok"),
    ) as mock_complete:
        await flash("hello", model="gpt-4o-mini")

    assert mock_complete.call_args.kwargs["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_flash_convenience_custom_timeout():
    """FR-AGT-020: flash() forwards custom timeout_s parameter."""

    async def _slow(*args, **kwargs):
        await asyncio.sleep(10)
        return _make_litellm_response("late")

    with patch("thegent.agents.flash_agent.litellm.acompletion", side_effect=_slow):
        result = await flash("slow task", timeout_s=0.05)

    assert result.success is False


@pytest.mark.asyncio
async def test_flash_convenience_timeout_enforcement():
    """FR-AGT-020: flash() enforces timeout_s, not unlimited."""
    calls = []

    async def _slow(*args, **kwargs):
        await asyncio.sleep(5)
        calls.append(1)
        return _make_litellm_response("late")

    with patch("thegent.agents.flash_agent.litellm.acompletion", side_effect=_slow):
        result = await flash("task", timeout_s=0.1)

    assert result.success is False
    assert calls == []  # call never completed


# ---------------------------------------------------------------------------
# Agent ID format
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_id_is_hex_string():
    """FR-AGT-020: agent_id is an 8-character hex string (uuid4 short)."""
    with _patch_litellm("resp"):
        result = await flash("check id")

    assert len(result.agent_id) == 8
    int(result.agent_id, 16)  # raises ValueError if not valid hex


@pytest.mark.asyncio
async def test_agent_ids_unique_across_runs():
    """FR-AGT-020: Each flash() call produces a unique agent_id."""
    with _patch_litellm("resp"):
        r1 = await flash("run 1")
        r2 = await flash("run 2")
        r3 = await flash("run 3")

    ids = {r1.agent_id, r2.agent_id, r3.agent_id}
    assert len(ids) == 3


# ---------------------------------------------------------------------------
# Public API surface (import check)
# ---------------------------------------------------------------------------


def test_public_exports_from_agents_package():
    """FR-AGT-020: FlashAgent, FlashAgentConfig, FlashAgentResult, flash all exported."""
    from thegent.agents import FlashAgent as ImportedFlashAgent
    from thegent.agents import FlashAgentConfig as ImportedFlashAgentConfig
    from thegent.agents import FlashAgentResult as ImportedFlashAgentResult
    from thegent.agents import flash as flash_fn

    assert ImportedFlashAgent is FlashAgent
    assert ImportedFlashAgentConfig is FlashAgentConfig
    assert ImportedFlashAgentResult is FlashAgentResult
    assert flash_fn is flash
