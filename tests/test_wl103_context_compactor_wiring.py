from __future__ import annotations

from pathlib import Path

from thegent.agents.codex_proxy import CodexProxyRunner
from thegent.agents.context_compactor import ContextCompactionResult


def test_wl103_prepare_litellm_messages_compacts_large_skill_context() -> None:
    runner = CodexProxyRunner(agent_name="codex", use_litellm_router=False)
    runner.activated_skills = {"large-skill": "S" * 1200}

    messages, compaction = runner._prepare_litellm_messages(
        prompt="summarize",
        cwd=Path("/tmp/project"),
        mode="write",
        model="gpt-5.3-codex-spark",
        context_window_max=200,
    )

    assert compaction.compacted is True
    assert messages[0]["role"] == "system"
    assert "Summary of prior context" in messages[0]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "summarize"


def test_wl103_litellm_run_result_surfaces_context_usage_ratio(monkeypatch) -> None:
    class _Message:
        content = "ok"

    class _Choice:
        message = _Message()

    class _Response:
        choices = (_Choice(),)

    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setattr("litellm.completion", lambda **_kwargs: _Response())

    runner = CodexProxyRunner(agent_name="codex", use_litellm_router=False)
    runner.activated_skills = {"large-skill": "S" * 1200}

    result = runner._execute_litellm_api(
        prompt="summarize",
        cwd=Path("/tmp/project"),
        mode="write",
        timeout=5,
        provider="minimax",
        model="gpt-5.3-codex-spark",
    )

    assert result.exit_code == 0
    assert result.context_usage_ratio is not None
    assert result.context_usage_ratio > 0


def test_wl103_litellm_run_result_clamps_context_usage_ratio_to_one(
    monkeypatch,
) -> None:
    class _Message:
        content = "ok"

    class _Choice:
        message = _Message()

    class _Response:
        choices = (_Choice(),)

    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setattr("litellm.completion", lambda **_kwargs: _Response())

    runner = CodexProxyRunner(agent_name="codex", use_litellm_router=False)
    monkeypatch.setattr(
        runner,
        "_prepare_litellm_messages",
        lambda **_kwargs: (
            [{"role": "user", "content": "summarize"}],
            ContextCompactionResult(
                turns=[{"role": "user", "content": "summarize"}],
                usage_ratio=1.4,
                compacted=False,
            ),
        ),
    )

    result = runner._execute_litellm_api(
        prompt="summarize",
        cwd=Path("/tmp/project"),
        mode="write",
        timeout=5,
        provider="minimax",
        model="gpt-5.3-codex-spark",
    )

    assert result.exit_code == 0
    assert result.context_usage_ratio == 1.0
    assert result.context_tokens_used == 50_000
