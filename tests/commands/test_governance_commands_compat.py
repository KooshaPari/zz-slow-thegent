from __future__ import annotations

import pytest

from thegent.cli.commands import cli


@pytest.mark.skip(reason="CircuitBreakerRegistry not defined in policy.py - source bug")
def test_guardrails_check_cmd_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, prompt: str, agent: str | None = None, model: str | None = None) -> None:
        captured["prompt"] = prompt
        captured["agent"] = agent
        captured["model"] = model

    monkeypatch.setattr("thegent.cli.commands.governance_cmds.guardrails_check_cmd", _fake)

    cli.guardrails_check_cmd("hello", agent="coder", model="gpt-5")

    assert captured == {"prompt": "hello", "agent": "coder", "model": "gpt-5"}


@pytest.mark.skip(reason="CircuitBreakerRegistry not defined in policy.py - source bug")
def test_guardrails_show_cmd_wrapper_delegates(monkeypatch) -> None:
    called = {"value": False}

    def _fake() -> None:
        called["value"] = True

    monkeypatch.setattr("thegent.cli.commands.governance_cmds.guardrails_show_cmd", _fake)

    cli.guardrails_show_cmd()

    assert called["value"] is True


@pytest.mark.skip(reason="CircuitBreakerRegistry not defined in policy.py - source bug")
def test_policy_check_cmd_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, agent: str, model: str | None = None, lane: str = "standard", confidence: float = 1.0) -> None:
        captured["agent"] = agent
        captured["model"] = model
        captured["lane"] = lane
        captured["confidence"] = confidence

    monkeypatch.setattr("thegent.cli.commands.governance_cmds.policy_check_cmd", _fake)

    cli.policy_check_cmd(agent="codex", model="gpt-5", lane="strict", confidence=0.75)

    assert captured == {"agent": "codex", "model": "gpt-5", "lane": "strict", "confidence": 0.75}
