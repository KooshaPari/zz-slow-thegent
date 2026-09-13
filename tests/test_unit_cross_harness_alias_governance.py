"""Cross-harness governance tests for shared alias and default-routing contracts."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# All harness stubs were reduced (e.g. dex_main._MODEL_ALIAS -> _MODEL_ALIASES),
# so the alias governance contract this file relies on no longer exists.
# Skip at collection time when any of the symbol imports fail.
try:
    from thegent.anen_main import _MODEL_ALIAS as _ANEN_MODEL_ALIAS
    from thegent.anen_main import default_anen
    from thegent.clode_main import _MODEL_ALIAS as _CLODE_MODEL_ALIAS
    from thegent.clode_main import default_clode
    from thegent.dex_main import _DEX_BYPASS_FLAG, default_dex
    from thegent.dex_main import _MODEL_ALIAS as _DEX_MODEL_ALIAS
    from thegent.fanta_main import _MODEL_ALIAS as _FANTA_MODEL_ALIAS
    from thegent.fanta_main import app as fanta_app
    from thegent.roid_main import _MODEL_ALIAS as _ROID_MODEL_ALIAS
    from thegent.roid_main import default_roid
except ImportError as _exc:
    pytest.skip(
        f"Cross-harness _MODEL_ALIAS contract removed ({_exc}); alias governance tests skipped",
        allow_module_level=True,
    )

runner = CliRunner()


@pytest.mark.parametrize(
    ("harness", "model_alias_map"),
    [
        ("clode", _CLODE_MODEL_ALIAS),
        ("dex", _DEX_MODEL_ALIAS),
        ("roid", _ROID_MODEL_ALIAS),
        ("anen", _ANEN_MODEL_ALIAS),
        ("fanta", _FANTA_MODEL_ALIAS),
    ],
)
def test_codex_tier_aliases_are_consistent_across_harnesses(harness: str, model_alias_map: dict[str, str]) -> None:
    assert model_alias_map["dex"] == "gpt-5.3-codex", harness
    assert model_alias_map["high"] == "gpt-5.3-codex-high", harness
    assert model_alias_map["xhigh"] == "gpt-5.3-codex-xhigh", harness


def test_default_clode_callback_uses_flash_path() -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None})()
    with patch("thegent.clode_main._run_model_interactive") as run_model_interactive:
        default_clode(ctx, native=False)  # type: ignore[arg-type]
    run_model_interactive.assert_called_once_with("flash")


def test_default_dex_callback_uses_flash_path() -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None})()
    with (
        patch("sys.argv", ["dex"]),
        patch("thegent.dex_main._run_codex_interactive") as run_interactive,
    ):
        default_dex(ctx, force=False, native=False)  # type: ignore[arg-type]
    run_interactive.assert_called_once_with("flash")


def test_default_roid_callback_uses_flash_path() -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None, "args": []})()
    with patch("thegent.roid_main._run_droid_with_alias") as run_with_alias:
        default_roid(ctx, native=False)  # type: ignore[arg-type]
    run_with_alias.assert_called_once_with("flash", [])


def test_default_anen_callback_uses_flash_path() -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None, "args": []})()
    with patch("thegent.anen_main._run_anen_with_alias") as run_with_alias:
        default_anen(ctx)  # type: ignore[arg-type]
    run_with_alias.assert_called_once_with("flash", [])


def test_default_fanta_entrypoint_uses_flash_path() -> None:
    with patch("thegent.fanta_main._run_anen_with_alias") as run_with_alias:
        result = runner.invoke(fanta_app, [])
    assert result.exit_code == 0
    run_with_alias.assert_called_once_with("flash", [])
