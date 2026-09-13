"""Unified login flows for CLIProxyAPIPlus providers.

Lives in the use_case layer so the ``thegent.agents.cliproxy_manager``
shim can stay under the L1 CC threshold. Re-exports ``run_login`` and
``run_login_unified`` plus the ``_LOGIN_FLAGS`` table that the test
suite imports via the shim.

Sub-routines are split to keep every function at CC ≤ 12:

* ``_preflight_login``        — early-return on cached credentials.
* ``_resolve_factory_key``    — pick up factory API key (auto or confirmed).
* ``_prompt_for_api_key``     — interactive manual entry (browser + key).
* ``_persist_and_restart``    — write the key back to config + reload proxy.
* ``_run_oauth_login``        — invoke ``cliproxy -provider-login`` once.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import Any

from thegent.config.settings import ThegentSettings
from thegent.domain.provider_config import OAUTH_ONLY_PROVIDERS
from thegent.infra.fast_yaml_parser import yaml_dumps, yaml_load
from thegent.infra.shim_subprocess import run as shim_run
from thegent.use_cases.manage_cliproxy_config import (
    PROVIDER_LOGIN_CONFIG,
    _ensure_config,
    _get_factory_api_key,
    _has_oauth_credentials,
    _has_provider_credentials,
    _inject_api_key_into_cliproxy,
)
from thegent.use_cases.manage_cliproxy_runtime import (
    _CLIPROXY_NOT_FOUND_MSG,
    _binary_available,
    _resolve_binary,
    ensure_proxy_running,
    kill_proxy,
)

_LOG = logging.getLogger(__name__)

# CLIProxyAPIPlus -login flags (OAuth providers).
_LOGIN_FLAGS: dict[str, str] = {
    "claude": "-claude-login",
    "codex": "-codex-login",
    "gemini": "-login",
    "minimax": "-minimax-login",
    "qwen": "-qwen-login",
    "glm": "-iflow-login",
    "iflow": "-iflow-login",
    "iflow-cookie": "-iflow-cookie",
    "kimi": "-kimi-login",
    "roo": "-roo-login",
    "kilo": "-kilo-login",
    "copilot": "-github-copilot-login",
    "antigravity": "-antigravity-login",
    "kiro": "-kiro-login",
    "kiro-google": "-kiro-google-login",
    "kiro-aws": "-kiro-aws-login",
    "kiro-aws-authcode": "-kiro-aws-authcode",
    "kiro-import": "-kiro-import",
}


def _load_config(config_path: Path) -> dict[str, Any]:
    """Load existing YAML config or return ``{}``."""
    raw = yaml_load(config_path) if config_path.exists() else {}
    return dict(raw) if isinstance(raw, dict) else {}


def _preflight_login(config: dict[str, Any], provider: str, *, skip_if_configured: bool) -> bool:
    """Return True when the caller should skip the login flow entirely."""
    if not skip_if_configured:
        return False
    if not _has_provider_credentials(config, provider):
        return False
    _LOG.info(
        "Skipping login for provider=%s since credentials already exist in cliproxy config.",
        provider,
    )
    return True


def _resolve_factory_key(
    provider: str,
    display_name: str,
    factory_path: str,
    factory_key: str,
    prompt_fn: Callable[[str], str],
    *,
    skip_if_configured: bool,
) -> tuple[str | None, bool]:
    """Resolve an API key from the factory config.

    Returns ``(key, user_declined)``. ``user_declined`` is True when the
    user explicitly said 'no' to the confirmation prompt (only relevant
    in non-skip mode).
    """
    if skip_if_configured:
        _LOG.info("Using API key for %s from factory config at %s.", display_name, factory_path)
        return factory_key, False

    try:
        resp = prompt_fn(f"  Found {display_name} API key in {factory_path}. Use it? [Y/n]: ").strip().lower()
    except Exception as exc:
        _LOG.error("Failed to read factory-key confirmation for %s: %s", provider, exc)
        return None, True  # treat as failure signal

    if resp in ("", "y", "yes"):
        _LOG.info("Using factory API key for %s after confirmation.", display_name)
        return factory_key, False

    _LOG.info(
        "Skipping factory API key for %s after user declined confirmation.",
        display_name,
    )
    return None, False


def _open_login_url(url: str, display_name: str) -> None:
    """Best-effort browser open for the login landing page."""
    if not url:
        _LOG.warning(
            "No login URL configured for %s, proceeding to manual key entry.",
            display_name,
        )
        return
    try:
        if not webbrowser.open(url):
            _LOG.warning("Browser failed to open login URL for %s: %s", display_name, url)
    except Exception as exc:
        _LOG.warning("Could not open browser for %s login URL %s: %s", display_name, url, exc)


def _log_instructions(display_name: str, instructions: list[str]) -> None:
    """Surface the provider's login instructions, if any."""
    if not instructions:
        _LOG.debug("No login instructions configured for %s.", display_name)
        return
    _LOG.info("Login instructions for %s:", display_name)
    for idx, line in enumerate(instructions, start=1):
        _LOG.info("%d) %s", idx, line)


def _prompt_for_api_key(
    provider: str,
    display_name: str,
    instructions: list[str],
    url: str,
    prompt_fn: Callable[[str], str],
) -> str | None:
    """Surface instructions + browser-open, then prompt for the API key.

    Returns ``""`` on skip (Enter pressed), ``None`` on prompt failure.
    """
    _log_instructions(display_name, instructions)
    _open_login_url(url, display_name)
    try:
        return prompt_fn(f"Enter {display_name} API key (or press Enter to skip): ").strip()
    except Exception as exc:
        _LOG.error("Failed to read API key input for %s: %s", provider, exc)
        return None


def _persist_and_restart(
    config: dict[str, Any],
    config_path: Path,
    provider: str,
    display_name: str,
    key: str,
    cfg: dict[str, Any],
    settings: ThegentSettings,
) -> int:
    """Write the new key to the YAML config and hot-reload the proxy.

    Returns the run_login_unified exit code (0 = ok, 2 = persist failure).
    """
    try:
        _inject_api_key_into_cliproxy(config, provider, key, cfg)
        config_path.write_text(yaml_dumps(config, default_flow_style=False, sort_keys=False))
    except Exception as exc:
        _LOG.error("Failed to persist API key for %s to %s: %s", display_name, config_path, exc)
        return 2

    if kill_proxy(settings):
        _LOG.info("Restarting cliproxy after updating API key for %s.", display_name)
        try:
            base_url = ensure_proxy_running(settings)
            _LOG.debug("cliproxy ready at %s", base_url)
        except Exception as exc:
            _LOG.error("Failed to restart cliproxy after login for %s: %s", display_name, exc)
            return 2
    else:
        _LOG.info("cliproxy not running; skipping restart for %s.", display_name)

    return 0


def _resolve_key_flow(
    provider_lower: str,
    display_name: str,
    cfg: dict[str, Any],
    prompt_fn: Callable[[str], str],
    *,
    skip_if_configured: bool,
) -> str | None:
    """Acquire the API key from factory or interactive prompt.

    Returns the resolved key, "" on user-skip, or None on prompt failure.
    """
    factory_key, factory_path = _get_factory_api_key(provider_lower)
    key: str | None = None
    if factory_key and factory_path:
        key, _ = _resolve_factory_key(
            provider_lower,
            display_name,
            factory_path,
            factory_key,
            prompt_fn,
            skip_if_configured=skip_if_configured,
        )

    if not key:
        result = _prompt_for_api_key(
            provider_lower,
            display_name,
            cfg.get("instructions", []),
            cfg.get("url", ""),
            prompt_fn,
        )
        if result is None:
            return None
        key = result

    if not key:
        _LOG.info("No API key provided for %s; returning skip.", display_name)
        return ""
    return key


def _normalise_provider(provider: str) -> str:
    """Lower-case and validate the provider name; raise on unknown."""
    provider_lower = provider.lower()
    if provider_lower not in PROVIDER_LOGIN_CONFIG:
        raise ValueError(f"Unknown provider: {provider}. Supported: {', '.join(sorted(PROVIDER_LOGIN_CONFIG))}")
    return provider_lower


def _load_cfg_or_skip(
    settings: ThegentSettings,
    provider_lower: str,
    skip_if_configured: bool,
) -> tuple[Path, dict[str, Any], dict[str, Any], str] | int:
    """Return (config_path, config, cfg, display_name) or 0 to skip login."""
    config_path = _ensure_config(settings)
    config = _load_config(config_path)
    cfg = PROVIDER_LOGIN_CONFIG[provider_lower]
    if _preflight_login(config, provider_lower, skip_if_configured=skip_if_configured):
        return 0
    return config_path, config, cfg, cfg.get("display_name", provider_lower)


def run_login_unified(
    settings: ThegentSettings,
    provider: str,
    prompt_func: Callable[[str], str] | None = None,
    skip_if_configured: bool = True,
) -> int:
    """Unified login: open URL + prompt for API key. Returns 0/1/2.

    Preflight check for existing credentials. Auto-uses factory API key
    when ``skip_if_configured`` is True.
    """
    provider_lower = _normalise_provider(provider)
    loaded = _load_cfg_or_skip(settings, provider_lower, skip_if_configured)
    if loaded == 0:
        return 0
    config_path, config, cfg, display_name = loaded

    prompt_fn = prompt_func or input
    key = _resolve_key_flow(
        provider_lower,
        display_name,
        cfg,
        prompt_fn,
        skip_if_configured=skip_if_configured,
    )
    if key is None:
        return 2
    if not key:
        return 1
    return _persist_and_restart(
        config,
        config_path,
        provider_lower,
        display_name,
        key,
        cfg,
        settings,
    )


def _build_oauth_run_kwargs(provider_lower: str, timeout_seconds: int) -> dict[str, Any]:
    """Build the kwargs for the ``shim_run`` invocation of cliproxy -login."""
    requires_interactive_stdio = provider_lower == "minimax"
    kwargs: dict[str, Any] = {
        "check": False,
        "env": os.environ.copy(),
        "timeout": timeout_seconds,
        "close_fds": True,
    }
    if requires_interactive_stdio:
        kwargs["stdin"] = sys.stdin
        kwargs["stdout"] = sys.stdout
        kwargs["stderr"] = sys.stderr
    else:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    return kwargs


def _run_oauth_login(
    settings: ThegentSettings,
    provider_lower: str,
    login_timeout: int | None,
    *,
    force: bool,
) -> int:
    """Run ``cliproxy -<provider>-login`` once and return its exit code."""
    binary = _resolve_binary(settings)
    if not _binary_available(binary):
        raise FileNotFoundError(_CLIPROXY_NOT_FOUND_MSG)

    config_path = _ensure_config(settings)
    flag = _LOGIN_FLAGS[provider_lower]
    timeout_seconds = login_timeout if login_timeout is not None else int(os.environ.get("THGENT_LOGIN_TIMEOUT", "120"))

    if provider_lower == "minimax" and not sys.stdin.isatty():
        _LOG.error(
            "Provider %s login requires an interactive terminal. "
            "Use `thegent setup --minimax-key <KEY>` for non-interactive setup.",
            provider_lower,
        )
        return 2

    run_kwargs = _build_oauth_run_kwargs(provider_lower, timeout_seconds)
    try:
        proc = shim_run([binary, "-config", str(config_path), flag], **run_kwargs)
        return proc.returncode
    except subprocess.TimeoutExpired:
        _LOG.warning("Login timed out for provider=%s after %ss", provider_lower, timeout_seconds)
        return 124


def _route_login_path(
    settings: ThegentSettings,
    provider_lower: str,
    prompt_func: Callable[[str], str] | None,
    force: bool,
    login_timeout: int | None,
) -> int:
    """Dispatch a provider to its preferred login flow.

    Returns 0 on cached-credentials skip, or the exit code from the
    delegated login routine.
    """
    if provider_lower in _LOGIN_FLAGS:
        if not force and os.environ.get("THGENT_TESTING") != "1" and _has_oauth_credentials(settings, provider_lower):
            return 0
        return _run_oauth_login(
            settings,
            provider_lower,
            login_timeout,
            force=force,
        )

    if provider_lower in PROVIDER_LOGIN_CONFIG:
        return run_login_unified(
            settings,
            provider_lower,
            prompt_func=prompt_func,
            skip_if_configured=not force,
        )

    raise ValueError(
        f"Unknown provider: {provider_lower}. Supported: "
        f"{', '.join(sorted(set(PROVIDER_LOGIN_CONFIG) | set(_LOGIN_FLAGS)))}"
    )


def _prefers_unified_flow(provider_lower: str, force: bool) -> bool:
    """Decide whether ``run_login`` should route to the API-key flow."""
    # CLIP-BUG-08: Qwen OAuth endpoint is unstable; use API-key flow.
    if provider_lower == "qwen":
        return True
    if provider_lower not in OAUTH_ONLY_PROVIDERS and provider_lower not in _LOGIN_FLAGS:
        factory_key, _ = _get_factory_api_key(provider_lower)
        if factory_key and not force:
            return True
    return False


def run_login(
    settings: ThegentSettings,
    provider: str,
    prompt_func: Callable[[str], str] | None = None,
    force: bool = False,
    login_timeout: int | None = None,
) -> int:
    """Run login for provider. Returns exit code.

    Prefers OAuth via CLIProxy for providers that support it.
    Falls back to API-key flow for providers without OAuth (minimax, nim).
    """
    provider_lower = provider.lower()

    if _prefers_unified_flow(provider_lower, force):
        return run_login_unified(
            settings,
            provider_lower,
            prompt_func=prompt_func,
            skip_if_configured=not force,
        )

    return _route_login_path(settings, provider_lower, prompt_func, force, login_timeout)
