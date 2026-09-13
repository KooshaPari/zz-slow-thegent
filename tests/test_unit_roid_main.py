"""Unit tests for roid command wiring and shim-link installation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.modules.pop("thegent", None)

from thegent.roid_main import (
    _MODEL_ALIAS,
    GEMINI_FLASH_MODEL,
    _run_droid_with_alias,
    app,
    default_roid,
)

runner = CliRunner()


def _mock_completed(returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    return proc


@patch("thegent.roid_main._resolve_droid_cmd", return_value="droid")
@patch("thegent.roid_main.subprocess.run")
def test_default_roid_uses_flash_model(mock_run: MagicMock, _mock_resolve: MagicMock) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["droid", "--model", GEMINI_FLASH_MODEL], check=False)


@patch("thegent.roid_main._resolve_droid_cmd", return_value="droid")
@patch("thegent.roid_main.subprocess.run")
def test_roid_flash_uses_flash_model(mock_run: MagicMock, _mock_resolve: MagicMock) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, ["flash"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["droid", "--model", GEMINI_FLASH_MODEL], check=False)


def test_roid_dex_alias_maps_to_codex_model() -> None:
    assert _MODEL_ALIAS["dex"] == "gpt-5.3-codex"


@pytest.mark.parametrize(
    ("model_alias", "canonical_model"),
    [
        ("dex", "gpt-5.3-codex"),
        ("high", "gpt-5.3-codex-high"),
        ("xhigh", "gpt-5.3-codex-xhigh"),
        ("flash", GEMINI_FLASH_MODEL),
    ],
)
def test_roid_alias_parity_table(model_alias: str, canonical_model: str) -> None:
    assert _MODEL_ALIAS[model_alias] == canonical_model


@patch("thegent.roid_main._resolve_droid_cmd", return_value="droid")
@patch("thegent.roid_main.subprocess.run")
def test_roid_mini_uses_gpt5_mini(mock_run: MagicMock, _mock_resolve: MagicMock) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, ["mini"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["droid", "--model", "gpt-5-mini"], check=False)


@patch("thegent.roid_main._resolve_droid_cmd", return_value="droid")
@patch("thegent.roid_main.subprocess.run")
@pytest.mark.parametrize(
    ("model_alias", "canonical_model"),
    [
        ("high", "gpt-5.3-codex-high"),
        ("xhigh", "gpt-5.3-codex-xhigh"),
    ],
)
def test_roid_high_xhigh_use_expected_canonical_models(
    mock_run: MagicMock, _mock_resolve: MagicMock, model_alias: str, canonical_model: str
) -> None:
    mock_run.return_value = _mock_completed(0)

    result = runner.invoke(app, [model_alias])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["droid", "--model", canonical_model], check=False)


def test_install_links_writes_roid_wrappers(tmp_path: Path) -> None:
    shims_bin = tmp_path / "thegent-shims"
    shims_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shims_bin.chmod(0o755)

    with patch("thegent.roid_main.shutil.which", return_value=None):
        result = runner.invoke(app, ["install-links", "--bin-dir", str(tmp_path)])

    assert result.exit_code == 0

    roid = tmp_path / "roid"
    assert roid.is_symlink()
    assert roid.resolve() == shims_bin.resolve()


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
def test_default_roid_callback_uses_flash_table_driven(ctx_args: list[str]) -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None, "args": ctx_args})()
    with patch("thegent.roid_main._run_droid_with_alias") as run_with_alias:
        default_roid(ctx, native=False)  # type: ignore[arg-type]
    run_with_alias.assert_called_once_with("flash", ctx_args)
    assert run_with_alias.call_args.args[1] == ctx_args


@pytest.mark.parametrize(
    ("passthrough_args", "expected_cmd"),
    [
        (["hello"], ["droid", "--model", "unknown-model", "hello"]),
        (["exec", "hello"], ["droid", "exec", "-m", "unknown-model", "hello"]),
    ],
)
@patch("thegent.roid_main._resolve_droid_cmd", return_value="droid")
@patch("thegent.roid_main.subprocess.run")
def test_roid_unknown_model_policy_passthrough(
    mock_run: MagicMock,
    _mock_resolve: MagicMock,
    passthrough_args: list[str],
    expected_cmd: list[str],
) -> None:
    mock_run.return_value = _mock_completed(0)

    _run_droid_with_alias("unknown-model", passthrough_args)

    mock_run.assert_called_once_with(expected_cmd, check=False)
    called_cmd = mock_run.call_args.args[0]
    assert called_cmd == expected_cmd
    if passthrough_args and passthrough_args[0] == "exec":
        assert called_cmd[3] == "unknown-model"
    else:
        assert called_cmd[2] == "unknown-model"


def test_roid_config_launches_tui_translation_layer() -> None:
    with patch("thegent.ux.models_providers_tui.run_models_providers_tui") as run_tui:
        result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    run_tui.assert_called_once_with()


def test_roid_config_legacy_uses_provider_form() -> None:
    with patch("thegent.provider_model_manager.run_provider_form") as run_legacy:
        result = runner.invoke(app, ["config", "--legacy"])
    assert result.exit_code == 0
    run_legacy.assert_called_once_with()
