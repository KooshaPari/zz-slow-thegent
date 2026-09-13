"""Unit tests for anen command wiring and shim-link installation."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.modules.pop("thegent", None)

from thegent.anen_main import (
    _MODEL_ALIAS,
    GEMINI_FLASH_MODEL,
    _run_anen_with_alias,
    app,
    default_anen,
)

runner = CliRunner()


def _normalized_output(output: str) -> str:
    return " ".join(output.split())


def _mock_completed(returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    return proc


@patch("thegent.anen_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.anen_main.subprocess.run")
def test_default_anen_uses_flash_model(mock_run: MagicMock, _mock_resolve: MagicMock) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["anen", "--model", GEMINI_FLASH_MODEL], check=False)


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
def test_default_anen_callback_uses_flash_table_driven(ctx_args: list[str]) -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None, "args": ctx_args})()
    with patch("thegent.anen_main._run_anen_with_alias") as run_with_alias:
        default_anen(ctx)  # type: ignore[arg-type]
    run_with_alias.assert_called_once_with("flash", ctx_args)
    assert run_with_alias.call_args.args[1] == ctx_args


@pytest.mark.parametrize(
    ("model_alias", "canonical_model"),
    [
        ("dex", "gpt-5.3-codex"),
        ("high", "gpt-5.3-codex-high"),
        ("xhigh", "gpt-5.3-codex-xhigh"),
        ("flash", GEMINI_FLASH_MODEL),
    ],
)
def test_anen_alias_parity_table(model_alias: str, canonical_model: str) -> None:
    assert _MODEL_ALIAS[model_alias] == canonical_model


@patch("thegent.anen_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.anen_main.subprocess.run")
def test_anen_max_exec_sets_headless_model_flag(mock_run: MagicMock, _mock_resolve: MagicMock) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, ["exec", "-m", "max", "hello world"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["anen", "exec", "-m", "MiniMax-M2.5", "hello world"], check=False)


@patch("thegent.anen_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.anen_main.subprocess.run")
@pytest.mark.parametrize(
    ("runner_args", "expected_cmd"),
    [
        (["high"], ["anen", "--model", "gpt-5.3-codex-high"]),
        (["xhigh"], ["anen", "--model", "gpt-5.3-codex-xhigh"]),
        (["exec", "-m", "high", "hello world"], ["anen", "exec", "-m", "gpt-5.3-codex-high", "hello world"]),
        (["exec", "-m", "xhigh", "hello world"], ["anen", "exec", "-m", "gpt-5.3-codex-xhigh", "hello world"]),
    ],
)
def test_anen_high_xhigh_use_expected_canonical_models(
    mock_run: MagicMock, _mock_resolve: MagicMock, runner_args: list[str], expected_cmd: list[str]
) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, runner_args)

    assert result.exit_code == 0
    mock_run.assert_called_once_with(expected_cmd, check=False)


def test_install_links_writes_anen_wrappers(tmp_path: Path) -> None:
    shims_bin = tmp_path / "thegent-shims"
    shims_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shims_bin.chmod(0o755)

    with patch("thegent.anen_main.shutil.which", return_value=None):
        result = runner.invoke(app, ["install-links", "--bin-dir", str(tmp_path)])

    assert result.exit_code == 0
    normalized_output = " ".join(result.output.split())
    assert "Installed" in normalized_output
    assert "fanta -> thegent-shims" in normalized_output
    assert "antigma -> thegent-shims" in normalized_output

    antigma = tmp_path / "antigma"
    fanta = tmp_path / "fanta"
    assert antigma.is_symlink()
    assert fanta.is_symlink()
    assert antigma.resolve() == shims_bin.resolve()
    assert fanta.resolve() == shims_bin.resolve()


def test_resolve_anen_cmd_skips_thegent_wrapper(tmp_path: Path, monkeypatch) -> None:
    wrapper = tmp_path / "ante-wrapper"
    wrapper.write_text('#!/usr/bin/env sh\nexec thegent anen "$@"\n', encoding="utf-8")
    wrapper.chmod(0o755)

    native = tmp_path / "ante-native"
    native.write_text("#!/usr/bin/env sh\necho ok\n", encoding="utf-8")
    native.chmod(0o755)

    monkeypatch.delenv("THGENT_NATIVE_ANEN_BIN", raising=False)
    monkeypatch.delenv("THGENT_NATIVE_ANTE_BIN", raising=False)

    def _which(name: str) -> str:
        if name == "ante":
            return str(wrapper)
        return ""

    monkeypatch.setattr("shutil.which", _which)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", [str(wrapper)])
    monkeypatch.setattr(os, "access", lambda *_: True)
    (tmp_path / ".ante" / "bin").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".ante" / "bin" / "ante").symlink_to(native)

    from thegent.anen_main import _resolve_anen_cmd

    assert Path(_resolve_anen_cmd()).resolve() == native.resolve()


@pytest.mark.parametrize(
    ("runner_args", "expected_cmd"),
    [
        (["unknown-model", "hello world"], ["anen", "--model", "unknown-model", "hello world"]),
        (["exec", "-m", "unknown-model", "hello world"], ["anen", "exec", "-m", "unknown-model", "hello world"]),
    ],
)
@patch("thegent.anen_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.anen_main.subprocess.run")
def test_anen_unknown_model_policy_passthrough(
    mock_run: MagicMock,
    _mock_resolve: MagicMock,
    runner_args: list[str],
    expected_cmd: list[str],
) -> None:
    mock_run.return_value = _mock_completed(0)

    if runner_args[0] == "unknown-model":
        _run_anen_with_alias(runner_args[0], runner_args[1:])
    else:
        result = runner.invoke(app, runner_args)
        assert result.exit_code == 0

    mock_run.assert_called_once_with(expected_cmd, check=False)
    called_cmd = mock_run.call_args.args[0]
    assert called_cmd == expected_cmd
    if runner_args[0] == "unknown-model":
        assert called_cmd[2] == "unknown-model"
    else:
        assert called_cmd[3] == "unknown-model"


@patch("thegent.anen_main._resolve_anen_cmd", return_value="anen")
@patch("thegent.anen_main.subprocess.run")
def test_anen_unknown_model_passthrough_cli_has_no_rejection_message(
    mock_run: MagicMock,
    _mock_resolve: MagicMock,
) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, ["exec", "-m", "unknown-model", "hello"])

    assert result.exit_code == 0
    assert "Unknown model" not in _normalized_output(result.output)
    mock_run.assert_called_once_with(["anen", "exec", "-m", "unknown-model", "hello"], check=False)
