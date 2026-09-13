"""Unit tests for clode command wiring and shim-link installation."""

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

import thegent.clode_main as clode_main_module
from thegent.clode_main import (
    _CLODE_BYPASS_FLAG,
    _GLM_POLICY_COUNTER,
    _MODEL_ALIAS,
    _resolve_clode_token,
    _run_claude_interactive,
    _run_claude_print,
    _run_sitback_codex,
    _run_sitback_droid,
    app,
    sitback_cmd,
)

runner = CliRunner()

SITBACK_ENV_AGENT = "THGENT_SITBACK_AGENT"
SITBACK_ENV_PROFILE = "THGENT_SITBACK_PROFILE"
SITBACK_ENV_SKILL = "THGENT_SITBACK_SKILL"
SITBACK_ENV_TMUX = "THGENT_SITBACK_TMUX"
SITBACK_ENV_NO_DASHBOARD = "THGENT_SITBACK_NO_DASHBOARD"

INVALID_AGENT_ALLOWED_TOKENS = (
    "claude",
    "codex",
    "droid",
    "antigma",
    "clode",
    "dex",
    "roid",
    "anen",
    "fanta",
)


def _assert_invalid_agent_tokens(stdout: str) -> None:
    assert "Invalid --agent" in stdout
    missing_tokens = sorted(token for token in INVALID_AGENT_ALLOWED_TOKENS if token not in stdout)
    assert not missing_tokens, f"Missing tokens in invalid-agent output: {missing_tokens}"


class _SitbackSettings:
    mcp_host = "127.0.0.1"
    mcp_port = 3847


class _HealthyResp:
    is_success = True


def _mock_sitback_health() -> tuple[Any, Any]:
    return (
        patch.object(clode_main_module, "_get_settings", return_value=_SitbackSettings()),
        patch("httpx.get", return_value=_HealthyResp()),
    )


def _ensure_sitback_registered() -> None:
    if not any(command.name == "sitback" for command in app.registered_commands):
        app.command("sitback")(sitback_cmd)


def _assert_sitback_env_contract(
    env: dict[str, str],
    *,
    expected_agent: str,
    no_dashboard: bool,
) -> None:
    assert env[SITBACK_ENV_AGENT] == expected_agent
    if no_dashboard:
        assert env[SITBACK_ENV_NO_DASHBOARD] == "1"
    else:
        assert SITBACK_ENV_NO_DASHBOARD not in env


def test_resolve_clode_token_valid_policies_and_backends() -> None:
    _GLM_POLICY_COUNTER["glm"] = 0
    assert _resolve_clode_token("glm", "auto", "round_robin") == "nim"
    assert _resolve_clode_token("glm", "kilo", "cheapest") == "kilo"
    assert _resolve_clode_token("glm", "openrouter", "cheapest") == "openrouter"
    assert _resolve_clode_token("glm", "auto", "cheapest") == "nim"


def test_resolve_clode_token_round_robin_cycles() -> None:
    _GLM_POLICY_COUNTER["glm"] = 0
    assert _resolve_clode_token("glm", "auto", "round_robin") == "nim"
    assert _resolve_clode_token("glm", "auto", "round_robin") == "kilo"
    assert _resolve_clode_token("glm", "auto", "round_robin") == "minimax"
    assert _resolve_clode_token("glm", "auto", "round_robin") == "glm"


def test_resolve_clode_token_invalid_policy_exits() -> None:
    with pytest.raises(typer.Exit):
        _resolve_clode_token("glm", "auto", "bad-policy")


def test_resolve_clode_token_unknown_prefer_falls_back_to_policy() -> None:
    assert _resolve_clode_token("glm", "rocket", "prefer_direct") == "glm:prefer_direct"


def test_install_links_bin_dir_missing_errors(tmp_path: Path) -> None:
    missing = tmp_path / "missing-dir"
    target = missing / "subdir"
    result = runner.invoke(app, ["install-links", "--bin-dir", str(target)])
    assert result.exit_code == 1


def test_install_links_writes_and_skips_without_force(tmp_path: Path) -> None:
    shims_bin = tmp_path / "thegent-shims"
    shims_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shims_bin.chmod(0o755)

    # First write should create clode link.
    with patch("thegent.clode_main.shutil.which", return_value=None):
        result = runner.invoke(app, ["install-links", "--bin-dir", str(tmp_path)])
    assert result.exit_code == 0
    wrapper = tmp_path / "clode"
    assert wrapper.is_symlink()
    assert wrapper.resolve() == shims_bin.resolve()

    # Without --force, existing files should be preserved.
    prewrite_target = (tmp_path / "clode").resolve()
    with patch("thegent.clode_main.shutil.which", return_value=None):
        result = runner.invoke(app, ["install-links", "--bin-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "clode").resolve() == prewrite_target


def test_install_links_force_rewrites_existing(tmp_path: Path) -> None:
    shims_bin = tmp_path / "thegent-shims"
    shims_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    shims_bin.chmod(0o755)

    target = tmp_path / "clode"
    target.write_text("legacy", encoding="utf-8")
    target.chmod(0o644)

    with patch("thegent.clode_main.shutil.which", return_value=None):
        result = runner.invoke(app, ["install-links", "--bin-dir", str(tmp_path), "--force"])
    assert result.exit_code == 0
    assert (tmp_path / "clode").is_symlink()
    assert (tmp_path / "clode").resolve() == shims_bin.resolve()


def test_clode_max_and_glm_aliases_forward_expected_token() -> None:
    with patch("thegent.clode_main._run_claude_interactive") as run_interactive:
        result = runner.invoke(
            app,
            ["max"],
        )
        assert result.exit_code == 0
        _, kwargs = run_interactive.call_args
        assert run_interactive.call_args[0][0] == "auto"
        assert kwargs["model_override"] == "minimax-m2.5"

    with patch("thegent.clode_main._run_claude_interactive") as run_interactive:
        result = runner.invoke(
            app,
            ["glm", "--policy", "cheapest", "--prefer", "kilo"],
        )
        assert result.exit_code == 0
        assert run_interactive.call_args[0][0] == "kilo"
        assert run_interactive.call_args.kwargs["model_override"] == "MiniMax-M2.5"

    with patch("thegent.clode_main._run_claude_interactive") as run_interactive:
        result = runner.invoke(
            app,
            ["glm", "--prefer", "openrouter"],
        )
        assert result.exit_code == 0
        assert run_interactive.call_args[0][0] == "openrouter"
        assert run_interactive.call_args.kwargs["model_override"] == "anthropic/claude-sonnet-4-20250514"


def test_clode_max_accepts_force_aliases() -> None:
    with patch("thegent.clode_main._run_claude_interactive") as run_interactive:
        result = runner.invoke(app, ["max", "--force"])
        assert result.exit_code == 0
        assert run_interactive.call_count == 1
        _, kwargs = run_interactive.call_args
        assert "--model" in kwargs["extra_args"]
        assert "minimax-m2.5" in kwargs["extra_args"]
        assert "--force" not in kwargs["extra_args"]


def test_clode_print_mode_uses_dangerous_skip_permissions_flag() -> None:
    with (
        patch("thegent.clode_main._is_triggered_by_agent_process", return_value=False),
        patch("thegent.clode_main._ensure_provider_configured"),
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={"ANTHROPIC_BASE_URL": "http://127.0.0.1:8317", "CLAUDE_CONFIG_DIR": "/tmp/claude-config"},
        ),
        patch("thegent.clode_main._ensure_claude_config_isolation"),
        patch("thegent.clode_main.wrap_with_caffeinate", side_effect=lambda cmd, _: cmd),
        patch("thegent.clode_main._ensure_claude_installed", return_value="/usr/bin/claude"),
        patch("thegent.clode_main.subprocess.run", return_value=type("RunResult", (), {"returncode": 0})()) as run,
    ):
        with pytest.raises(typer.Exit) as exit_info:
            _run_claude_print("minimax", "hi", model_override="MiniMax-M2.5")
        assert exit_info.value.exit_code == 0
        assert run.call_count == 1
        assert _CLODE_BYPASS_FLAG in run.call_args.args[0]


def test_clode_provider_default_to_interactive() -> None:
    with (
        patch("thegent.clode_main._get_claude_env", return_value={"ANTHROPIC_MODEL": "glm-5"}),
        patch("thegent.clode_main._run_claude_interactive") as run_interactive,
    ):
        result = runner.invoke(app, ["nim"])
        assert result.exit_code == 0
        assert run_interactive.call_args[0][0] == "nim"
        assert run_interactive.call_args.kwargs["model_override"] == "glm-5"


def test_clode_aliases_include_codex_tiers() -> None:
    assert _MODEL_ALIAS["dex"] == "gpt-5.3-codex"
    assert _MODEL_ALIAS["high"] == "gpt-5.3-codex-high"
    assert _MODEL_ALIAS["xhigh"] == "gpt-5.3-codex-xhigh"


def test_clode_high_and_xhigh_commands_forward_models() -> None:
    with patch("thegent.clode_main._run_claude_interactive") as run_interactive:
        result = runner.invoke(app, ["high"])
        assert result.exit_code == 0
        _, kwargs = run_interactive.call_args
        assert run_interactive.call_args[0][0] == "auto"
        assert kwargs["model_override"] == "gpt-5.3-codex-high"

    with patch("thegent.clode_main._run_claude_interactive") as run_interactive:
        result = runner.invoke(app, ["xhigh"])
        assert result.exit_code == 0
        _, kwargs = run_interactive.call_args
        assert run_interactive.call_args[0][0] == "auto"
        assert kwargs["model_override"] == "gpt-5.3-codex-xhigh"


def test_clode_root_defaults_to_flash_interactive() -> None:
    with patch("thegent.clode_main._run_claude_interactive") as run_interactive:
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert run_interactive.call_args[0][0] == "auto"
        assert run_interactive.call_args.kwargs["model_override"] == "gemini-3-flash"


def test_clode_run_and_bg_delegate_to_claude_cmd() -> None:
    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={"ANTHROPIC_MODEL": "glm-5", "CLAUDE_CONFIG_DIR": "/tmp/claude-config"},
        ),
        patch("thegent.cli.run_cmd") as run_cmd,
    ):
        result = runner.invoke(app, ["nim", "run", "hello world"])
        assert result.exit_code == 0
        run_cmd.assert_called_once()
        _, kwargs = run_cmd.call_args
        assert kwargs["agent"] == "interactive_agent"
        assert kwargs["prompt"] == "hello world"
        assert kwargs["mode"] == "write"
        assert kwargs["timeout"] == 90

    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={"ANTHROPIC_MODEL": "glm-5", "CLAUDE_CONFIG_DIR": "/tmp/claude-config"},
        ),
        patch("thegent.cli.bg_cmd") as bg_cmd,
    ):
        result = runner.invoke(app, ["nim", "bg", "hello world", "--owner", "me"])
        assert result.exit_code == 0
        bg_cmd.assert_called_once()
        _, kwargs = bg_cmd.call_args
        assert kwargs["agent"] == "interactive_agent"
        assert kwargs["prompt"] == "hello world"
        assert kwargs["owner"] == "me"


def test_clode_run_global_forwards_remote_to_run_cmd() -> None:
    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={"ANTHROPIC_MODEL": "glm-5", "CLAUDE_CONFIG_DIR": "/tmp/claude-config"},
        ),
        patch("thegent.clode_main.run_cmd") as run_cmd,
    ):
        result = runner.invoke(app, ["run", "nim", "hello world", "--remote", "10.0.0.2"])
    assert result.exit_code == 0
    _, kwargs = run_cmd.call_args
    assert kwargs["remote"] == "10.0.0.2"
    assert kwargs["prompt"] == "hello world"


def test_clode_bg_global_forwards_remote_to_bg_cmd() -> None:
    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={"ANTHROPIC_MODEL": "glm-5", "CLAUDE_CONFIG_DIR": "/tmp/claude-config"},
        ),
        patch("thegent.clode_main.bg_cmd") as bg_cmd,
    ):
        result = runner.invoke(app, ["bg", "nim", "hello world", "--remote", "10.0.0.3", "--owner", "qa"])
    assert result.exit_code == 0
    _, kwargs = bg_cmd.call_args
    assert kwargs["remote"] == "10.0.0.3"
    assert kwargs["owner"] == "qa"
    assert kwargs["prompt"] == "hello world"


def test_clode_run_bg_accept_codex_tiers() -> None:
    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={
                "ANTHROPIC_MODEL": "gpt-5.3-codex-high",
                "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
            },
        ),
        patch("thegent.clode_main.run_cmd") as run_cmd,
    ):
        result = runner.invoke(app, ["run", "high", "ship it"])
        assert result.exit_code == 0
        _, kwargs = run_cmd.call_args
        assert kwargs["model"] == "gpt-5.3-codex-high"

    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={
                "ANTHROPIC_MODEL": "gpt-5.3-codex-xhigh",
                "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
            },
        ),
        patch("thegent.clode_main.bg_cmd") as bg_cmd,
    ):
        result = runner.invoke(app, ["bg", "xhigh", "ship it", "--owner", "qa"])
        assert result.exit_code == 0
        _, kwargs = bg_cmd.call_args
        assert kwargs["model"] == "gpt-5.3-codex-xhigh"
        assert kwargs["owner"] == "qa"


def test_clode_run_dex_uses_canonical_model_value() -> None:
    with (
        patch("thegent.clode_main._resolve_provider_for_model", return_value="codex") as resolve_provider,
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={
                "ANTHROPIC_MODEL": "gpt-5.3-codex",
                "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
            },
        ) as get_env,
        patch("thegent.clode_main.run_cmd") as run_cmd,
    ):
        result = runner.invoke(app, ["run", "dex", "ship it"])
        assert result.exit_code == 0
        resolve_provider.assert_called_once_with("dex")
        get_env.assert_called_once_with("codex", model_override="gpt-5.3-codex")
        _, kwargs = run_cmd.call_args
        assert kwargs["model"] == "gpt-5.3-codex"


def test_clode_bg_dex_uses_canonical_model_value() -> None:
    with (
        patch("thegent.clode_main._resolve_provider_for_model", return_value="codex") as resolve_provider,
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={
                "ANTHROPIC_MODEL": "gpt-5.3-codex",
                "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
            },
        ) as get_env,
        patch("thegent.clode_main.bg_cmd") as bg_cmd,
    ):
        result = runner.invoke(app, ["bg", "dex", "ship it", "--owner", "qa"])
        assert result.exit_code == 0
        resolve_provider.assert_called_once_with("dex")
        get_env.assert_called_once_with("codex", model_override="gpt-5.3-codex")
        _, kwargs = bg_cmd.call_args
        assert kwargs["model"] == "gpt-5.3-codex"
        assert kwargs["owner"] == "qa"


def test_clode_run_high_uses_canonical_model_value() -> None:
    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={
                "ANTHROPIC_MODEL": "gpt-5.3-codex-high",
                "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
            },
        ),
        patch("thegent.clode_main.run_cmd") as run_cmd,
    ):
        result = runner.invoke(app, ["run", "high", "ship it"])
        assert result.exit_code == 0
        _, kwargs = run_cmd.call_args
        assert kwargs["model"] == "gpt-5.3-codex-high"


def test_clode_bg_xhigh_uses_canonical_model_value() -> None:
    with (
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={
                "ANTHROPIC_MODEL": "gpt-5.3-codex-xhigh",
                "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
            },
        ),
        patch("thegent.clode_main.bg_cmd") as bg_cmd,
    ):
        result = runner.invoke(app, ["bg", "xhigh", "ship it", "--owner", "qa"])
        assert result.exit_code == 0
        _, kwargs = bg_cmd.call_args
        assert kwargs["model"] == "gpt-5.3-codex-xhigh"
        assert kwargs["owner"] == "qa"


def test_sitback_codex_defaults_to_dex_model_alias() -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
    ):
        sitback_cmd(
            agent="codex",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill=None,
            profile="medium",
            tmux=False,
            no_dashboard=True,
            tui=False,
        )
        run_codex.assert_called_once()
        assert run_codex.call_args[0][0] == "dex"


def test_sitback_codex_includes_yolo_and_bypass_flags_when_not_agent() -> None:
    with (
        patch("thegent.clode_main.wrap_with_caffeinate", side_effect=lambda cmd, _: cmd),
        patch("thegent.clode_main.os.execvpe") as execvpe,
        patch("thegent.clode_main.shutil.which", return_value="/usr/bin/codex"),
        patch("thegent.clode_main._is_triggered_by_agent_process", return_value=False),
        patch("thegent.dex_main._resolve_provider_for_model", return_value="copilot"),
        patch("thegent.dex_main._get_codex_env", return_value={"OPENAI_BASE_URL": "http://127.0.0.1:8317"}),
    ):
        _run_sitback_codex("max", {"OPENAI_BASE_URL": "http://127.0.0.1:8317"}, tmux=False)
        command = execvpe.call_args.args[1]
        assert "--yolo" in command
        assert "--dangerously-bypass-approvals-and-sandbox" in command


def test_sitback_droid_does_not_force_codex_or_droid_bypass_flags() -> None:
    with (
        patch("thegent.clode_main.wrap_with_caffeinate", side_effect=lambda cmd, _: cmd),
        patch("thegent.clode_main.os.execvpe") as execvpe,
        patch("thegent.clode_main.shutil.which", return_value="/usr/bin/droid"),
    ):
        _run_sitback_droid("flash", {"OPENAI_BASE_URL": "http://127.0.0.1:8317"}, tmux=False)
        command = execvpe.call_args.args[1]
        assert "--dangerously-bypass-approvals-and-sandbox" not in command
        assert "--dangerously-skip-permissions" not in command


def test_sitback_droid_defaults_to_flash_model_alias() -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_droid") as run_droid,
    ):
        sitback_cmd(
            agent="droid",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill=None,
            profile="medium",
            tmux=False,
            no_dashboard=True,
            tui=False,
        )
        run_droid.assert_called_once()
        assert run_droid.call_args[0][0] == "flash"


def test_sitback_fanta_defaults_to_flash_model_alias() -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_anen") as run_anen,
    ):
        sitback_cmd(
            agent="fanta",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill=None,
            profile="medium",
            tmux=False,
            no_dashboard=True,
            tui=False,
        )
        run_anen.assert_called_once()
        assert run_anen.call_args[0][0] == "flash"


@pytest.mark.parametrize(
    ("agent", "launcher_attr", "expected_model_alias", "expected_harness"),
    [
        ("codex", "_run_sitback_codex", "dex", "codex"),
        ("droid", "_run_sitback_droid", "flash", "droid"),
        ("fanta", "_run_sitback_anen", "flash", "antigma"),
    ],
)
def test_sitback_top_level_cli_wiring_no_dashboard_defaults(
    agent: str,
    launcher_attr: str,
    expected_model_alias: str,
    expected_harness: str,
) -> None:
    _ensure_sitback_registered()
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
        patch.object(clode_main_module, "_run_sitback_droid") as run_droid,
        patch.object(clode_main_module, "_run_sitback_anen") as run_anen,
    ):
        result = runner.invoke(app, ["sitback", "--agent", agent, "--no-dashboard"])
        assert result.exit_code == 0

        launchers = {
            "_run_sitback_codex": run_codex,
            "_run_sitback_droid": run_droid,
            "_run_sitback_anen": run_anen,
        }
        for path, launcher in launchers.items():
            if path == launcher_attr:
                launcher.assert_called_once()
            else:
                launcher.assert_not_called()

        selected = launchers[launcher_attr]
        assert selected.call_args.args[0] == expected_model_alias
        _assert_sitback_env_contract(
            selected.call_args.args[1],
            expected_agent=expected_harness,
            no_dashboard=True,
        )
        assert selected.call_args.args[2] is False


def test_sitback_top_level_cli_wiring_codex_high_alias_passthrough() -> None:
    _ensure_sitback_registered()
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
        patch.object(clode_main_module, "_run_sitback_droid") as run_droid,
        patch.object(clode_main_module, "_run_sitback_anen") as run_anen,
    ):
        result = runner.invoke(
            app,
            ["sitback", "--agent", "codex", "--model", "high", "--no-dashboard"],
        )
        assert result.exit_code == 0
        run_codex.assert_called_once()
        run_droid.assert_not_called()
        run_anen.assert_not_called()
        assert run_codex.call_args.args[0] == "high"
        _assert_sitback_env_contract(
            run_codex.call_args.args[1],
            expected_agent="codex",
            no_dashboard=True,
        )
        assert run_codex.call_args.args[2] is False


def test_sitback_top_level_cli_invalid_agent_contract_text_and_exit() -> None:
    result = runner.invoke(app, ["sitback", "--agent", "invalid-harness", "--no-dashboard"])
    assert result.exit_code == 1
    _assert_invalid_agent_tokens(result.stdout)


def test_sitback_direct_no_dashboard_flag_propagates_to_env() -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
    ):
        sitback_cmd(
            agent="codex",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill=None,
            profile="medium",
            tmux=False,
            no_dashboard=True,
            tui=False,
        )
        run_codex.assert_called_once()
        env_with_flag = run_codex.call_args.args[1]
        assert env_with_flag[SITBACK_ENV_NO_DASHBOARD] == "1"


def test_sitback_direct_tmux_env_key_absent_when_flag_false() -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
    ):
        sitback_cmd(
            agent="codex",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill=None,
            profile="medium",
            tmux=False,
            no_dashboard=True,
            tui=False,
        )
        run_codex.assert_called_once()
        env_without_tmux = run_codex.call_args.args[1]
        assert SITBACK_ENV_TMUX not in env_without_tmux
        assert env_without_tmux[SITBACK_ENV_NO_DASHBOARD] == "1"


@pytest.mark.parametrize(
    ("tmux", "profile", "skill"),
    [
        (False, "medium", None),
        (True, "medium", None),
        (False, "full", "thegent-skills"),
    ],
)
def test_sitback_direct_no_dashboard_flag_always_set_when_passed(
    tmux: bool,
    profile: str,
    skill: str | None,
) -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
    ):
        sitback_cmd(
            agent="codex",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill=skill,
            profile=profile,
            tmux=tmux,
            no_dashboard=True,
            tui=False,
        )
        run_codex.assert_called_once()
        env_with_flag = run_codex.call_args.args[1]
        assert env_with_flag[SITBACK_ENV_NO_DASHBOARD] == "1"


def test_sitback_direct_tmux_flag_propagates_to_env() -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
    ):
        sitback_cmd(
            agent="codex",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill=None,
            profile="medium",
            tmux=True,
            no_dashboard=True,
            tui=False,
        )
        run_codex.assert_called_once()
        env_with_tmux = run_codex.call_args.args[1]
        assert env_with_tmux[SITBACK_ENV_TMUX] == "1"


def test_sitback_no_dashboard_keeps_profile_and_skill_env_keys() -> None:
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
    ):
        sitback_cmd(
            agent="codex",
            provider=None,
            model=None,
            dex=False,
            cd=None,
            skill="thegent-skills",
            profile="full",
            tmux=False,
            no_dashboard=True,
            tui=False,
        )
        run_codex.assert_called_once()
        env = run_codex.call_args.args[1]
        assert env[SITBACK_ENV_NO_DASHBOARD] == "1"
        assert env[SITBACK_ENV_PROFILE] == "full"
        assert env[SITBACK_ENV_SKILL] == "thegent-skills"


def test_sitback_dex_flag_parity_top_level_and_direct() -> None:
    _ensure_sitback_registered()
    settings_patch, health_patch = _mock_sitback_health()
    with (
        settings_patch,
        health_patch,
        patch.object(clode_main_module, "_run_sitback_codex") as run_codex,
        patch.object(clode_main_module, "_run_sitback_droid") as run_droid,
        patch.object(clode_main_module, "_run_sitback_anen") as run_anen,
    ):
        result = runner.invoke(app, ["sitback", "--dex", "--no-dashboard"])
        assert result.exit_code == 0
        run_codex.assert_called_once()
        run_droid.assert_not_called()
        run_anen.assert_not_called()
        top_level_model = run_codex.call_args.args[0]
        run_codex.reset_mock()

        sitback_cmd(
            agent="codex",
            provider=None,
            model=None,
            dex=True,
            cd=None,
            skill=None,
            profile="medium",
            tmux=False,
            no_dashboard=True,
            tui=False,
        )
        run_codex.assert_called_once()
        direct_model = run_codex.call_args.args[0]

    assert top_level_model == "dex"
    assert direct_model == "dex"


def test_run_claude_interactive_exec_path_and_env_handshake() -> None:
    fake_env = {
        "ANTHROPIC_BASE_URL": "http://127.0.0.1:3847/v1",
        "ANTHROPIC_API_KEY": "openrouter",
        "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
    }
    with (
        patch("thegent.clode_main._ensure_provider_configured"),
        patch("thegent.clode_main._get_claude_env", return_value=fake_env),
        patch("thegent.clode_main._ensure_claude_config_isolation"),
        patch("thegent.clode_main._ensure_claude_installed", return_value="/usr/bin/claude"),
        patch("thegent.clode_main._is_triggered_by_agent_process", return_value=True),
        patch("thegent.clode_main.wrap_with_caffeinate", side_effect=lambda cmd, _: cmd),
        patch("thegent.clode_main.os.execvpe") as execvpe,
    ):
        _run_claude_interactive("openrouter")
        execvpe.assert_called_once()
        args, _ = execvpe.call_args
        assert args[0] == "/usr/bin/claude"
        assert args[1] == ["/usr/bin/claude"]
        assert args[2]["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:3847/v1"
        assert args[2]["ANTHROPIC_API_KEY"] == "openrouter"


def test_run_claude_interactive_missing_binary_errors() -> None:
    with (
        patch("thegent.clode_main._ensure_provider_configured"),
        patch(
            "thegent.clode_main._get_claude_env",
            return_value={
                "ANTHROPIC_BASE_URL": "http://127.0.0.1:3847/v1",
                "ANTHROPIC_API_KEY": "nim",
                "CLAUDE_CONFIG_DIR": "/tmp/claude-config",
            },
        ),
        patch("thegent.clode_main._ensure_claude_config_isolation"),
        patch("thegent.clode_main._ensure_claude_installed", side_effect=typer.Exit(1)),
    ):
        with pytest.raises(typer.Exit):
            _run_claude_interactive("nim")


def test_clode_config_launches_tui_translation_layer() -> None:
    with patch("thegent.ux.models_providers_tui.run_models_providers_tui") as run_tui:
        result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    run_tui.assert_called_once_with()


def test_clode_config_legacy_uses_provider_form() -> None:
    with patch("thegent.provider_model_manager.run_provider_form") as run_legacy:
        result = runner.invoke(app, ["config", "--legacy"])
    assert result.exit_code == 0
    run_legacy.assert_called_once_with()
