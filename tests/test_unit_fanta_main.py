"""Unit tests for fanta first-class CLI entrypoint."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from thegent.fanta_main import _MODEL_ALIAS, GEMINI_FLASH_MODEL, app, default_fanta

runner = CliRunner()


def _normalized_output(output: str) -> str:
    return " ".join(output.split())


def test_fanta_help_mentions_fanta_harness() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Antigma-backed interactive harness (fanta)." in _normalized_output(result.output)


def test_fanta_install_links_writes_symlinks(tmp_path: Path) -> None:
    shims_bin = tmp_path / "thegent-shims"
    shims_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shims_bin.chmod(0o755)

    with patch("thegent.fanta_main.shutil.which", return_value=None):
        result = runner.invoke(app, ["install-links", "--bin-dir", str(tmp_path)])
    assert result.exit_code == 0
    normalized_output = _normalized_output(result.output)
    assert "Installed" in normalized_output
    assert "fanta -> thegent-shims" in normalized_output
    assert "antigma -> thegent-shims" in normalized_output

    fanta = tmp_path / "fanta"
    antigma = tmp_path / "antigma"
    assert fanta.is_symlink()
    assert antigma.is_symlink()
    assert fanta.resolve() == shims_bin.resolve()
    assert antigma.resolve() == shims_bin.resolve()


def _mock_completed(returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    return proc


@pytest.mark.parametrize(
    ("model_alias", "canonical_model"),
    [
        ("dex", "gpt-5.3-codex"),
        ("high", "gpt-5.3-codex-high"),
        ("xhigh", "gpt-5.3-codex-xhigh"),
        ("flash", GEMINI_FLASH_MODEL),
    ],
)
def test_fanta_alias_parity_table(model_alias: str, canonical_model: str) -> None:
    assert _MODEL_ALIAS[model_alias] == canonical_model


@patch("thegent.fanta_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.fanta_main.subprocess.run")
def test_fanta_default_routes_to_flash(mock_run: MagicMock, _mock_resolve: MagicMock) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["anen", "--model", "gemini-3-flash"], check=False)


@patch("thegent.fanta_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.fanta_main.subprocess.run")
@pytest.mark.parametrize(
    ("runner_args", "expected_cmd"),
    [
        (["high"], ["anen", "--model", "gpt-5.3-codex-high"]),
        (["xhigh"], ["anen", "--model", "gpt-5.3-codex-xhigh"]),
        (["exec", "-m", "high", "hello world"], ["anen", "exec", "-m", "gpt-5.3-codex-high", "hello world"]),
        (["exec", "-m", "xhigh", "hello world"], ["anen", "exec", "-m", "gpt-5.3-codex-xhigh", "hello world"]),
    ],
)
def test_fanta_high_xhigh_use_expected_canonical_models(
    mock_run: MagicMock, _mock_resolve: MagicMock, runner_args: list[str], expected_cmd: list[str]
) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, runner_args)

    assert result.exit_code == 0
    mock_run.assert_called_once_with(expected_cmd, check=False)


@pytest.mark.parametrize(
    "ctx_args",
    [
        ["unknown-token", "hello"],
        ["dex", "hello"],
        ["high", "hello"],
        ["xhigh", "hello"],
        [],
    ],
)
def test_fanta_default_callback_uses_flash_table_driven(ctx_args: list[str]) -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None, "args": ctx_args})()
    with patch("thegent.fanta_main._run_anen_with_alias") as run_with_alias:
        default_fanta(ctx)  # type: ignore[arg-type]
    run_with_alias.assert_called_once_with("flash", ctx_args)
    assert run_with_alias.call_args.args[1] == ctx_args


@pytest.mark.parametrize("unknown_model", ["unknown-model", "totally-new-model"])
@patch("thegent.fanta_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.fanta_main.subprocess.run")
def test_fanta_unknown_model_policy_passthrough_exec(
    mock_run: MagicMock, _mock_resolve: MagicMock, unknown_model: str
) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, ["exec", "-m", unknown_model, "hello world"])

    assert result.exit_code == 0
    assert "Unknown model" not in _normalized_output(result.output)
    mock_run.assert_called_once_with(["anen", "exec", "-m", unknown_model, "hello world"], check=False)
    called_cmd = mock_run.call_args.args[0]
    assert called_cmd[3] == unknown_model


def test_fanta_config_launches_tui_translation_layer() -> None:
    with patch("thegent.ux.models_providers_tui.run_models_providers_tui") as run_tui:
        result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    run_tui.assert_called_once_with()


def test_fanta_config_legacy_uses_provider_form() -> None:
    with patch("thegent.provider_model_manager.run_provider_form") as run_legacy:
        result = runner.invoke(app, ["config", "--legacy"])
    assert result.exit_code == 0
    run_legacy.assert_called_once_with()
