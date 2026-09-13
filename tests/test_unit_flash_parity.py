"""Unit tests for dex/clode flash routing parity through cliproxy."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from thegent.agents.droid import CodexRunner
from thegent.agents.routing_contracts import GEMINI_FLASH_MODEL, GEMINI_FLASH_PROVIDER
from thegent.clode_main import _get_claude_env
from thegent.dex_main import _get_codex_env


def test_dex_flash_env_contract(monkeypatch, tmp_path):
    monkeypatch.delenv("THGENT_CLIPROXY_ADAPTER", raising=False)
    settings = SimpleNamespace(
        mcp_host="127.0.0.1",
        cliproxy_port=8317,
        cliproxy_config_path=tmp_path / "cliproxy.yaml",
    )
    monkeypatch.setattr("thegent.dex_main._get_settings", lambda: settings)
    monkeypatch.setattr(
        "thegent.agents.cliproxy_manager._ensure_config", lambda _settings: None
    )
    monkeypatch.setattr(
        "thegent.agents.cliproxy_manager.ensure_proxy_running", lambda _settings: None
    )
    monkeypatch.setattr(
        "thegent.agents.cliproxy_manager._has_provider_credentials",
        lambda _config, _provider: True,
    )

    env = _get_codex_env(GEMINI_FLASH_PROVIDER, GEMINI_FLASH_MODEL)
    assert env["OPENAI_API_KEY"] == GEMINI_FLASH_PROVIDER
    assert env["OPENAI_BASE_URL"] == "http://127.0.0.1:8317/v1"
    assert env["API_TIMEOUT_MS"] == "300000"
    assert env.get("THGENT_CLIPROXY_ADAPTER") == "1"


def test_clode_flash_env_contract(monkeypatch, tmp_path):
    monkeypatch.delenv("THGENT_CLIPROXY_ADAPTER", raising=False)
    settings = SimpleNamespace(
        mcp_host="127.0.0.1",
        cliproxy_port=8317,
        cache_dir=tmp_path / "cache",
    )
    monkeypatch.setattr("thegent.clode_main._get_settings", lambda: settings)
    monkeypatch.setattr(
        "thegent.agents.cliproxy_manager.ensure_proxy_running", lambda _settings: None
    )

    env = _get_claude_env(GEMINI_FLASH_PROVIDER, model_override=GEMINI_FLASH_MODEL)
    assert env["ANTHROPIC_API_KEY"] == GEMINI_FLASH_PROVIDER
    assert env["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:8317"
    assert env["ANTHROPIC_MODEL"] == GEMINI_FLASH_MODEL
    assert env["API_TIMEOUT_MS"] == "300000"
    assert env.get("THGENT_CLIPROXY_ADAPTER") == "1"


def test_dex_clode_flash_share_same_proxy_host_port(monkeypatch, tmp_path):
    codex_settings = SimpleNamespace(
        mcp_host="127.0.0.1",
        cliproxy_port=8317,
        cliproxy_config_path=tmp_path / "cliproxy.yaml",
    )
    clode_settings = SimpleNamespace(
        mcp_host="127.0.0.1",
        cliproxy_port=8317,
        cache_dir=tmp_path / "cache",
    )
    monkeypatch.setattr("thegent.dex_main._get_settings", lambda: codex_settings)
    monkeypatch.setattr("thegent.clode_main._get_settings", lambda: clode_settings)
    monkeypatch.setattr(
        "thegent.agents.cliproxy_manager._ensure_config", lambda _settings: None
    )
    monkeypatch.setattr(
        "thegent.agents.cliproxy_manager.ensure_proxy_running", lambda _settings: None
    )
    monkeypatch.setattr(
        "thegent.agents.cliproxy_manager._has_provider_credentials",
        lambda _config, _provider: True,
    )

    dex_env = _get_codex_env(GEMINI_FLASH_PROVIDER, GEMINI_FLASH_MODEL)
    clode_env = _get_claude_env(
        GEMINI_FLASH_PROVIDER, model_override=GEMINI_FLASH_MODEL
    )
    dex_url = urlparse(dex_env["OPENAI_BASE_URL"])
    clode_url = urlparse(clode_env["ANTHROPIC_BASE_URL"])
    assert (dex_url.hostname, dex_url.port) == (clode_url.hostname, clode_url.port)


def test_droid_codex_flash_uses_dex_proxy_env(tmp_path):
    droids_dir = tmp_path / "droids"
    droids_dir.mkdir()
    (droids_dir / "factory.md").write_text("# Factory Droid")
    runner = CodexRunner(
        "factory", droids_dir, codex_cmd="codex", model=GEMINI_FLASH_MODEL
    )

    fake_env = {
        "OPENAI_BASE_URL": "http://127.0.0.1:8317/v1",
        "OPENAI_API_KEY": GEMINI_FLASH_PROVIDER,
        "THGENT_CLIPROXY_ADAPTER": "1",
    }
    with (
        patch(
            "thegent.dex_main._resolve_provider_for_model",
            return_value=GEMINI_FLASH_PROVIDER,
        ) as resolve_provider,
        patch("thegent.dex_main._get_codex_env", return_value=fake_env) as get_env,
        patch("thegent.agents.droid.subprocess.run") as run_proc,
    ):
        run_proc.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        result = runner.run(prompt="do work", cwd=tmp_path, mode="read", timeout=10)
        assert result.exit_code == 0
        resolve_provider.assert_called_once_with(GEMINI_FLASH_MODEL)
        get_env.assert_called_once_with(GEMINI_FLASH_PROVIDER, GEMINI_FLASH_MODEL)
        assert run_proc.call_args.kwargs["env"] == fake_env


def test_droid_codex_non_flash_uses_dex_provider_resolution(tmp_path):
    droids_dir = tmp_path / "droids"
    droids_dir.mkdir()
    (droids_dir / "factory.md").write_text("# Factory Droid")
    model = "claude-haiku-4.5"
    runner = CodexRunner("factory", droids_dir, codex_cmd="codex", model=model)
    fake_env = {"OPENAI_BASE_URL": "http://127.0.0.1:8317/v1", "OPENAI_API_KEY": "nim"}

    with (
        patch(
            "thegent.dex_main._resolve_provider_for_model", return_value="nim"
        ) as resolve_provider,
        patch("thegent.dex_main._get_codex_env", return_value=fake_env) as get_env,
        patch("thegent.agents.droid.subprocess.run") as run_proc,
    ):
        run_proc.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        result = runner.run(prompt="do work", cwd=tmp_path, mode="read", timeout=10)
        assert result.exit_code == 0
        resolve_provider.assert_called_once_with(model)
        get_env.assert_called_once_with("nim", model)
        assert run_proc.call_args.kwargs["env"] == fake_env
