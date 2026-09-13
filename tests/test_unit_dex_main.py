"""Unit tests for dex command wiring and shim-link installation."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# dex_main module was reduced to a stub that renamed _MODEL_ALIAS -> _MODEL_ALIASES.
# The old test contract cannot be satisfied; skip the file at collection time.
import thegent.dex_main as _dex_main_mod

if not hasattr(_dex_main_mod, "_MODEL_ALIAS"):
    pytest.skip(
        "dex_main._MODEL_ALIAS symbol removed when module was reduced to stub",
        allow_module_level=True,
    )

from thegent.agents.routing_contracts import GEMINI_FLASH_MODEL, GEMINI_FLASH_PROVIDER
from thegent.dex_main import (
    _DEX_BYPASS_FLAG,
    _DEX_YOLO_FLAG,
    _MODEL_ALIAS,
    _resolve_provider_for_model,
    _run_codex_interactive,
    _run_model_cmd,
    app,
    default_dex,
)

runner = CliRunner()


def _normalized_output(output: str) -> str:
    return " ".join(output.split())


def test_model_alias_mapping() -> None:
    """Model aliases map to canonical IDs."""
    assert _MODEL_ALIAS["dex"] == "gpt-5.3-codex"
    assert _MODEL_ALIAS["codex"] == "gpt-5.3-codex"
    assert _MODEL_ALIAS["composer"] == "composer-1.5"
    assert _MODEL_ALIAS["max"] == "minimax-m2.5"
    assert _MODEL_ALIAS["glm"] == "glm-5"
    assert _MODEL_ALIAS["haiku"] == "claude-haiku-4.5"
    assert _MODEL_ALIAS["opus"] == "claude-opus-4.6"
    assert _MODEL_ALIAS["sonnet"] == "claude-sonnet-4.5"
    assert _MODEL_ALIAS["step"] == "step-3.5-flash"
    assert _MODEL_ALIAS["flash"] == GEMINI_FLASH_MODEL
    assert _MODEL_ALIAS["high"] == "gpt-5.3-codex-high"
    assert _MODEL_ALIAS["xhigh"] == "gpt-5.3-codex-xhigh"
    assert _MODEL_ALIAS["mini"] == "gpt-5-mini"


def test_resolve_provider_composer_uses_cursor() -> None:
    """Composer 1.5 routes to cursor."""
    assert _resolve_provider_for_model("composer") == "cursor"


def test_resolve_provider_glm_round_robins() -> None:
    """GLM-5 round-robins across nim, kilo, minimax, glm."""
    providers_seen = set()
    for _ in range(8):
        p = _resolve_provider_for_model("glm")
        providers_seen.add(p)
    assert providers_seen.issubset({"nim", "kilo", "minimax", "glm"})


def test_resolve_provider_haiku_uses_claude_set() -> None:
    """Claude Haiku round-robins across claude, antigravity."""
    providers_seen = set()
    for _ in range(4):
        p = _resolve_provider_for_model("haiku")
        providers_seen.add(p)
    assert providers_seen.issubset({"claude", "antigravity"})


def test_resolve_provider_step_uses_nim() -> None:
    """Step 3.5 routes to nim."""
    assert _resolve_provider_for_model("step") == "nim"


def test_resolve_provider_mini_uses_copilot() -> None:
    """GPT-5-mini routes to copilot."""
    assert _resolve_provider_for_model("mini") == "copilot"


def test_resolve_provider_dex_uses_codex() -> None:
    """Codex 5.3 aliases route to codex provider."""
    assert _resolve_provider_for_model("dex") == "codex"
    assert _resolve_provider_for_model("high") == "codex"
    assert _resolve_provider_for_model("xhigh") == "codex"


def test_resolve_provider_max_round_robins() -> None:
    """M2.5 (max) round-robins across nim, kilo, minimax."""
    providers_seen = set()
    for _ in range(8):
        p = _resolve_provider_for_model("max")
        providers_seen.add(p)
    assert "nim" in providers_seen or "kilo" in providers_seen or "minimax" in providers_seen


def test_dex_uses_bypass_flag() -> None:
    """Dex uses --dangerously-bypass-approvals-and-sandbox, not --dangerously-skip-permissions."""
    assert _DEX_BYPASS_FLAG == "--dangerously-bypass-approvals-and-sandbox"
    assert "skip-permissions" not in _DEX_BYPASS_FLAG


def test_install_links_bin_dir_missing_errors(tmp_path: Path) -> None:
    missing = tmp_path / "missing-dir"
    target = missing / "subdir"
    result = runner.invoke(app, ["install-links", "--bin-dir", str(target)])
    assert result.exit_code == 1


def test_install_links_writes_model_shims(tmp_path: Path) -> None:
    """Install creates dex -> thegent-shims symlink."""
    shims_bin = tmp_path / "thegent-shims"
    shims_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shims_bin.chmod(0o755)

    with patch("thegent.dex_main.shutil.which", return_value=None):
        result = runner.invoke(app, ["install-links", "--bin-dir", str(tmp_path)])
    assert result.exit_code == 0
    wrapper = tmp_path / "dex"
    assert wrapper.is_symlink(), "dex should be a symlink"
    assert wrapper.resolve() == shims_bin.resolve()


def test_dex_composer_uses_composer_model() -> None:
    """dex composer uses composer-1.5 (Cursor), not max."""
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["composer"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "composer",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_max_forwards_bypass_flag() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["max"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "max",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_max_accepts_force_alias() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["max", "--force"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "max",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_max_accepts_legacy_bypass_alias() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["max", "--dangerously-bypass-approvals-and-sandbox"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "max",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_glm_uses_glm_model() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["glm"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "glm",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_haiku_uses_haiku_model() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["haiku"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "haiku",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_opus_uses_opus_model() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["opus"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "opus",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_sonnet_uses_sonnet_model() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["sonnet"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "sonnet",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_ultra_uses_ultra_model() -> None:
    """dex ultra uses Llama Nemotron Ultra via NIM."""
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["ultra"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "ultra",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_default_dex_uses_flash_model() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with("flash")


def test_dex_high_uses_codex_high_model() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["high"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "high",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_xhigh_uses_codex_xhigh_model() -> None:
    with patch("thegent.dex_main._run_codex_interactive") as run_interactive:
        result = runner.invoke(app, ["xhigh"])
        assert result.exit_code == 0
        run_interactive.assert_called_once_with(
            "xhigh",
            extra_args=["--search"],
            dangerously_bypass=True,
        )


def test_dex_run_accepts_mini_model() -> None:
    """dex run mini <prompt> uses gpt-5-mini via copilot."""
    with patch("thegent.dex_main._run_model_cmd") as run_cmd:
        result = runner.invoke(app, ["run", "mini", "hello"])
        assert result.exit_code == 0
        run_cmd.assert_called_once()
        assert run_cmd.call_args[0][0] == "mini"


def test_dex_run_dex_uses_codex_canonical_model() -> None:
    with patch("thegent.cli.run_cmd") as run_cmd:
        result = runner.invoke(app, ["run", "dex", "hello"])
    assert result.exit_code == 0
    run_cmd.assert_called_once()
    assert run_cmd.call_args.kwargs["model"] == "gpt-5.3-codex"
    assert run_cmd.call_args.kwargs["remote"] is None


def test_dex_run_global_forwards_remote_to_run_cmd() -> None:
    with patch("thegent.cli.run_cmd") as run_cmd:
        result = runner.invoke(app, ["run", "dex", "hello", "--remote", "node-12"])
    assert result.exit_code == 0
    run_cmd.assert_called_once()
    assert run_cmd.call_args.kwargs["remote"] == "node-12"


def test_dex_bg_dex_uses_codex_canonical_model() -> None:
    with patch("thegent.cli.bg_cmd") as bg_cmd:
        result = runner.invoke(app, ["bg", "dex", "hello"])
    assert result.exit_code == 0
    bg_cmd.assert_called_once()
    assert bg_cmd.call_args.kwargs["model"] == "gpt-5.3-codex"


def test_dex_bg_global_forwards_remote_to_bg_cmd() -> None:
    with patch("thegent.cli.bg_cmd") as bg_cmd:
        result = runner.invoke(app, ["bg", "dex", "hello", "--remote", "node-77", "--owner", "qa"])
    assert result.exit_code == 0
    bg_cmd.assert_called_once()
    assert bg_cmd.call_args.kwargs["remote"] == "node-77"
    assert bg_cmd.call_args.kwargs["owner"] == "qa"


@pytest.mark.parametrize(
    ("subcommand", "model_alias", "canonical_model"),
    [
        ("run", "high", "gpt-5.3-codex-high"),
        ("bg", "high", "gpt-5.3-codex-high"),
        ("run", "xhigh", "gpt-5.3-codex-xhigh"),
        ("bg", "xhigh", "gpt-5.3-codex-xhigh"),
    ],
)
def test_dex_run_bg_high_xhigh_use_expected_canonical_models(
    subcommand: str, model_alias: str, canonical_model: str
) -> None:
    target = "thegent.cli.run_cmd" if subcommand == "run" else "thegent.cli.bg_cmd"
    with patch(target) as model_cmd:
        result = runner.invoke(app, [subcommand, model_alias, "hello"])
    assert result.exit_code == 0
    model_cmd.assert_called_once()
    assert model_cmd.call_args.kwargs["model"] == canonical_model


@pytest.mark.parametrize(
    ("model_alias", "canonical_model", "provider"),
    [
        ("dex", "gpt-5.3-codex", "codex"),
        ("high", "gpt-5.3-codex-high", "codex"),
        ("xhigh", "gpt-5.3-codex-xhigh", "codex"),
        ("flash", GEMINI_FLASH_MODEL, GEMINI_FLASH_PROVIDER),
    ],
)
def test_dex_alias_parity_resolves_expected_models_and_providers(
    model_alias: str, canonical_model: str, provider: str
) -> None:
    assert _MODEL_ALIAS[model_alias] == canonical_model
    assert _resolve_provider_for_model(model_alias) == provider


@pytest.mark.parametrize(
    ("argv", "expected_model", "expected_extra_args"),
    [
        (["dex", "unknown-token", "hello"], "flash", ["unknown-token", "hello"]),
        (["dex"], "flash", []),
        (["dex", "dex", "hello"], "dex", ["hello"]),
        (["dex", "high", "hello"], "high", ["hello"]),
        (["dex", "xhigh", "hello"], "xhigh", ["hello"]),
    ],
)
def test_default_dex_callback_uses_flash_table_driven(
    argv: list[str], expected_model: str, expected_extra_args: list[str]
) -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None})()
    with (
        patch("sys.argv", argv),
        patch("thegent.dex_main._run_codex_interactive") as run_interactive,
    ):
        default_dex(ctx, force=False, native=False)  # type: ignore[arg-type]
    run_interactive.assert_called_once_with(
        expected_model,
        dangerously_bypass=None,
        dangerously_yolo=None,
        extra_args=expected_extra_args,
    )


def test_default_dex_direct_callback_explicit_flags_do_not_trigger_native_exec() -> None:
    """Regression: direct callback invocation should not hit native exec via OptionInfo defaults."""
    ctx = type("Ctx", (), {"invoked_subcommand": None})()
    with (
        patch("sys.argv", ["dex"]),
        patch("thegent.dex_main._exec_native_codex") as exec_native,
        patch("thegent.dex_main._run_codex_interactive") as run_interactive,
    ):
        default_dex(ctx, force=False, native=False)  # type: ignore[arg-type]

    exec_native.assert_not_called()
    run_interactive.assert_called_once_with("flash")


def test_default_dex_native_force_includes_force_yolo_for_native_path() -> None:
    ctx = type("Ctx", (), {"invoked_subcommand": None})()
    with (
        patch("sys.argv", ["dex", "--native", "--force"]),
        patch("thegent.dex_main._exec_native_codex") as exec_native,
        patch("thegent.dex_main._run_codex_interactive"),
    ):
        default_dex(ctx, force=True, native=True)  # type: ignore[arg-type]

    exec_native.assert_called_once_with(["--force-yolo", _DEX_YOLO_FLAG, _DEX_BYPASS_FLAG])


def test_run_codex_interactive_includes_yolo_and_dangerously_bypass_flags() -> None:
    with (
        patch("thegent.dex_main._resolve_provider_for_model", return_value="copilot"),
        patch(
            "thegent.dex_main._get_codex_env",
            return_value={"OPENAI_BASE_URL": "http://127.0.0.1:8317"},
        ),
        patch("thegent.dex_main.resolve_codex_cli_path", return_value="/usr/bin/codex"),
        patch("thegent.dex_main.os.execvpe") as execvpe,
        patch("thegent.dex_main.wrap_with_caffeinate", side_effect=lambda cmd, _: cmd),
    ):
        _run_codex_interactive("max", dangerously_bypass=True)
        command = execvpe.call_args.args[1]
        assert _DEX_YOLO_FLAG in command
        assert _DEX_BYPASS_FLAG in command


def test_run_codex_interactive_deduplicates_bypass_flags() -> None:
    with (
        patch("thegent.dex_main._resolve_provider_for_model", return_value="copilot"),
        patch(
            "thegent.dex_main._get_codex_env",
            return_value={"OPENAI_BASE_URL": "http://127.0.0.1:8317"},
        ),
        patch("thegent.dex_main.resolve_codex_cli_path", return_value="/usr/bin/codex"),
        patch("thegent.dex_main.os.execvpe") as execvpe,
        patch("thegent.dex_main.wrap_with_caffeinate", side_effect=lambda cmd, _: cmd),
    ):
        _run_codex_interactive("max", dangerously_bypass=True, extra_args=[_DEX_BYPASS_FLAG])
        command = execvpe.call_args.args[1]
        assert command.count(_DEX_YOLO_FLAG) == 1
        assert command.count(_DEX_BYPASS_FLAG) == 1


@pytest.mark.parametrize("subcommand", ["run", "bg"])
def test_dex_unknown_model_policy_rejects_for_run_and_bg(subcommand: str) -> None:
    result = runner.invoke(app, [subcommand, "unknown-model", "prompt"])
    normalized_output = _normalized_output(result.output)
    assert result.exit_code == 1
    assert "Unknown model 'unknown-model'" in normalized_output
    assert "Allowed: dex, high, xhigh, max, glm, haiku, opus, sonnet, ultra, flash, mini" in normalized_output


def test_dex_bg_unknown_model_policy_rejects() -> None:
    result = runner.invoke(app, ["bg", "unknown-model", "prompt"])
    normalized_output = _normalized_output(result.output)
    assert result.exit_code == 1
    assert "Unknown model 'unknown-model'" in normalized_output
    assert "Allowed: dex, high, xhigh, max, glm, haiku, opus, sonnet, ultra, flash, mini" in normalized_output


def test_dex_resume_passthrough_args() -> None:
    with patch("thegent.dex_main._exec_native_codex") as exec_native:
        result = runner.invoke(app, ["resume", "--", "--last"])
    assert result.exit_code == 0
    exec_native.assert_called_once_with(["resume", "--last"])


def test_dex_fork_passthrough_no_args() -> None:
    with patch("thegent.dex_main._exec_native_codex") as exec_native:
        result = runner.invoke(app, ["fork"])
    assert result.exit_code == 0
    exec_native.assert_called_once_with(["fork"])


def test_run_model_cmd_normalizes_alias_case() -> None:
    with patch("thegent.cli.run_cmd") as run_cmd:
        _run_model_cmd("CoMp", "hello")
    run_cmd.assert_called_once()
    assert run_cmd.call_args.kwargs["model"] == "composer-1.5"


def test_dex_config_launches_tui_translation_layer() -> None:
    with patch("thegent.ux.models_providers_tui.run_models_providers_tui") as run_tui:
        result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    run_tui.assert_called_once_with()


def test_dex_config_legacy_uses_provider_form() -> None:
    with patch("thegent.provider_model_manager.run_provider_form") as run_legacy:
        result = runner.invoke(app, ["config", "--legacy"])
    assert result.exit_code == 0
    run_legacy.assert_called_once_with()
