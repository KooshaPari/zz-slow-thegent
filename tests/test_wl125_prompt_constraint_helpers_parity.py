from __future__ import annotations

from thegent.cli.commands import impl


def test_wl125_inject_time_constraint_wrapper_delegates_to_prompt_helper(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *,
        prompt: str,
        timeout: int,
        seconds_per_tool_call: float,
        summary_mode: bool = True,
    ) -> str:
        captured.update(
            {
                "prompt": prompt,
                "timeout": timeout,
                "seconds_per_tool_call": seconds_per_tool_call,
                "summary_mode": summary_mode,
            }
        )
        return "wrapped-prompt"

    monkeypatch.setattr(
        "thegent.cli.commands.impl.prompt_constraint_helpers.inject_time_constraint",
        _fake,
    )

    result = impl._inject_time_constraint("hello", 30, summary_mode=False)

    assert result == "wrapped-prompt"
    assert captured["prompt"] == "hello"
    assert captured["timeout"] == 30
    assert captured["seconds_per_tool_call"] == impl.SECONDS_PER_TOOL_CALL
    assert captured["summary_mode"] is False
