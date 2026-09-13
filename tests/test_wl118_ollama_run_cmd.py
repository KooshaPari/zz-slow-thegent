"""WL-118 run/bg Ollama provider guard tests."""

from __future__ import annotations

from unittest.mock import patch


def test_run_impl_fails_fast_when_explicit_ollama_guard_fails() -> None:
    from thegent.cli.commands import impl as cli_impl

    with (
        patch(
            "thegent.models.catalog.resolve_route", return_value=("ollama", "llama3.3")
        ),
        patch(
            "thegent.cli.commands.impl._validate_explicit_ollama_provider",
            return_value="Ollama unavailable",
        ),
    ):
        result = cli_impl.run_impl(
            agent=None,
            prompt="hello",
            model="llama3.3",
            provider="ollama",
        )

    assert result["exit_code"] == 1
    assert "Ollama unavailable" in str(result.get("error"))
    assert str(result.get("run_id", "")).startswith("run_") or str(
        result.get("run_id", "")
    ).startswith("run_err_")


def test_bg_impl_fails_fast_when_explicit_ollama_guard_fails() -> None:
    from thegent.cli.commands import impl as cli_impl

    with (
        patch(
            "thegent.models.catalog.resolve_route", return_value=("ollama", "llama3.3")
        ),
        patch(
            "thegent.cli.commands.impl._validate_explicit_ollama_provider",
            return_value="No local models",
        ),
    ):
        result = cli_impl.bg_impl(
            agent=None,
            prompt="hello",
            cd=None,
            model="llama3.3",
            provider="ollama",
        )

    assert result["exit_code"] == 1
    assert result["session_id"] == "failed"
    assert "No local models" in str(result.get("error"))


def test_validate_explicit_ollama_provider_returns_model_install_message() -> None:
    from thegent.cli.commands.impl import _validate_explicit_ollama_provider

    with (
        patch(
            "thegent.utils.routing_impl.ollama_provider.assert_ollama_available",
            return_value=None,
        ),
        patch(
            "thegent.utils.routing_impl.ollama_provider.get_available_models",
            return_value=[],
        ),
    ):
        msg = _validate_explicit_ollama_provider(
            provider="ollama-local", model="llama3.3"
        )

    assert msg is not None
    assert "no local models are installed" in msg.lower()
    assert "ollama pull" in msg


def test_validate_explicit_ollama_provider_returns_none_when_model_is_installed() -> (
    None
):
    from thegent.cli.commands.impl import _validate_explicit_ollama_provider

    with (
        patch(
            "thegent.utils.routing_impl.ollama_provider.assert_ollama_available",
            return_value=None,
        ),
        patch(
            "thegent.utils.routing_impl.ollama_provider.get_available_models",
            return_value=["llama3.3", "mistral"],
        ),
    ):
        msg = _validate_explicit_ollama_provider(
            provider="ollama", model="ollama/llama3.3"
        )

    assert msg is None
