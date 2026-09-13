from __future__ import annotations

from types import SimpleNamespace

from thegent.cli.commands import impl


def test_wl125_resolve_agent_model_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *, agent: str, model: str | None, mode: str, settings: object
    ) -> str | None:
        captured["agent"] = agent
        captured["model"] = model
        captured["mode"] = mode
        captured["settings"] = settings
        return "model-from-helper"

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_model_helpers.resolve_agent_model", _fake
    )

    settings = SimpleNamespace(default_codex_model="codex-mini")
    resolved = impl._resolve_agent_model("codex", None, "full", settings)

    assert resolved == "model-from-helper"
    assert captured["agent"] == "codex"
    assert captured["model"] is None
    assert captured["mode"] == "full"
    assert captured["settings"] is settings


def test_wl120_wavex_validate_explicit_ollama_provider_wrapper_delegates(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake(*, provider: str | None, model: str | None) -> str | None:
        captured["provider"] = provider
        captured["model"] = model
        return "mock-ollama-error"

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_model_helpers.validate_explicit_ollama_provider",
        _fake,
    )

    result = impl._validate_explicit_ollama_provider(
        provider="ollama-local", model="llama3.3"
    )

    assert result == "mock-ollama-error"
    assert captured == {"provider": "ollama-local", "model": "llama3.3"}
