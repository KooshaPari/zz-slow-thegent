"""CLIProxyAPIPlus lifecycle: config generation and proxy process management.

DEPRECATED: This module is now a thin shim for backward compatibility.
New code should use the decomposed modules:

- ``thegent.use_cases.manage_cliproxy`` — Business logic (provider config,
  credentials)
- ``thegent.use_cases.manage_cliproxy_runtime`` — Process management
  (binary resolution, reachability checks, subprocess startup, port-kill)
- ``thegent.ports.driven.cliproxy`` — Port interfaces
- ``thegent.adapters.driven.cliproxy_http`` — HTTP client adapter

Unified login flow: open URL + prompt for API key for all providers.
Preflight check for existing credentials. Setup uses the same flow.
Provider/model definitions from internal JSON (no factory config dependency).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx
import orjson as json

from thegent.config import ThegentSettings
from thegent.infra.fast_subprocess import run_subprocess_optimized
from thegent.use_cases.manage_cliproxy_config import (  # noqa: F401
    _CLIPROXY_DATA_DIR,
    _FACTORY_PROVIDER_PATTERNS,
    _OAUTH_AUTH_PREFIXES,
    _PROVIDER_PATCHERS,
    PROVIDER_LOGIN_CONFIG,
    ProviderDefinitionsLoadError,
    _build_provider_login_config,
    _ensure_config,
    _get_claude_aliases,
    _get_factory_api_key,
    _get_provider_definitions,
    _has_oauth_credentials,
    _has_provider_credentials,
    _inject_api_key_into_cliproxy,
    _inject_cursor_into_cliproxy,
    _inject_kiro_into_cliproxy,
    _load_json,
    _patch_glm_provider,
    _patch_kilo_provider,
    _patch_minimax_provider,
    _patch_provider_aliases,
    _patch_roo_provider,
    _resolve_claude_aliases,
)
from thegent.use_cases.manage_cliproxy_login import (  # noqa: F401
    _LOGIN_FLAGS,
    run_login,
    run_login_unified,
)

# Re-export process-management primitives from the use_case layer so callers
# that imported them via this module keep working without changes.
from thegent.use_cases.manage_cliproxy_runtime import (  # noqa: F401
    _CLIPROXY_NOT_FOUND_MSG,
    _PROXY_CHECK_TIMEOUT,
    _PROXY_READY_TIMEOUT,
    _adapter_script_path,
    _binary_available,
    _is_adapter_fallback_allowed,
    _is_adapter_running,
    _is_proxy_reachable,
    _resolve_binary,
    _start_proxy_and_wait,
    _start_raw_proxy,
    adapter_script_path,
    binary_available,
    ensure_proxy_running,
    is_adapter_fallback_allowed,
    is_adapter_running,
    is_proxy_reachable,
    kill_proxy,
    resolve_binary,
    start_proxy_managed,
)

_LOG = logging.getLogger(__name__)

_CLIPROXY_DATA_DIR = Path(__file__).parent / "cliproxy_data"

_LAST_PROVIDER_METRICS_STATUS: dict[str, Any] = {
    "status": "not_requested",
    "metrics": None,
}

# ---------------------------------------------------------------------------
# Provider metrics fetch (kept here because the test suite imports it via
# ``thegent.agents.cliproxy_manager``).
# ---------------------------------------------------------------------------


def fetch_provider_metrics(
    settings: ThegentSettings | None = None,
) -> dict[str, dict] | None:
    """Fetch per-provider metrics from CLIProxyAPIPlus GET /v1/metrics/providers."""
    global _LAST_PROVIDER_METRICS_STATUS  # noqa: PLW0603
    settings = settings or ThegentSettings()
    url = f"http://127.0.0.1:{settings.cliproxy_port}/v1/metrics/providers"
    try:
        resp = httpx.get(url, timeout=2)
    except httpx.TimeoutException as exc:
        _LAST_PROVIDER_METRICS_STATUS = {
            "status": "timeout",
            "metrics": None,
            "error_type": type(exc).__name__,
            "detail": str(exc)[:200],
        }
        return None
    except httpx.NetworkError as exc:
        _LAST_PROVIDER_METRICS_STATUS = {
            "status": "network_error",
            "metrics": None,
            "error_type": type(exc).__name__,
            "detail": str(exc)[:200],
        }
        return None
    except httpx.HTTPError as exc:
        _LAST_PROVIDER_METRICS_STATUS = {
            "status": "http_error",
            "metrics": None,
            "error_type": type(exc).__name__,
            "detail": str(exc)[:200],
        }
        return None

    if not resp.is_success:
        _LAST_PROVIDER_METRICS_STATUS = {
            "status": "endpoint_unavailable",
            "metrics": None,
            "http_status": resp.status_code,
        }
        return None

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        _LAST_PROVIDER_METRICS_STATUS = {
            "status": "invalid_json",
            "metrics": None,
            "error_type": type(exc).__name__,
            "detail": str(exc)[:200],
        }
        return None

    if isinstance(data, dict):
        _LAST_PROVIDER_METRICS_STATUS = {
            "status": "ok",
            "metrics": data,
            "provider_count": len(data),
        }
        return data

    _LAST_PROVIDER_METRICS_STATUS = {
        "status": "invalid_payload_shape",
        "metrics": None,
        "payload_type": type(data).__name__,
    }
    return None


def get_last_provider_metrics_status() -> dict[str, Any]:
    """Return status metadata from the latest provider metrics fetch."""
    return dict(_LAST_PROVIDER_METRICS_STATUS)


# ---------------------------------------------------------------------------
# LaunchAgent service (macOS)
# ---------------------------------------------------------------------------

_PROXY_PLIST_LABEL = "com.thegent.cliproxy"


def _proxy_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{_PROXY_PLIST_LABEL}.plist"


def proxy_service_install(settings: ThegentSettings) -> tuple[bool, str]:
    """Install proxy as launchd service (macOS). Runs at login, restarts on crash."""
    import platform

    if platform.system() != "Darwin":
        return False, "launchd only supported on macOS. Use systemd on Linux."
    binary = _resolve_binary(settings)
    if not _binary_available(binary):
        return False, _CLIPROXY_NOT_FOUND_MSG
    config_path = _ensure_config(settings)
    plist_path = _proxy_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    log_dir = Path.home() / ".cache" / "thegent"
    log_dir.mkdir(parents=True, exist_ok=True)
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>Label</key>
<string>{_PROXY_PLIST_LABEL}</string>
<key>ProgramArguments</key>
<array>
<string>{binary}</string>
<string>-config</string>
<string>{config_path}</string>
</array>
<key>RunAtLoad</key>
<true/>
<key>KeepAlive</key>
<true/>
<key>StandardOutPath</key>
<string>{log_dir}/cliproxy.log</string>
<key>StandardErrorPath</key>
<string>{log_dir}/cliproxy.err</string>
</dict>
</plist>
"""
    plist_path.write_text(plist)
    return True, f"Installed to {plist_path}. Run: thegent cliproxy service start"


def proxy_service_uninstall() -> tuple[bool, str]:
    """Remove proxy launchd service."""
    import platform

    if platform.system() != "Darwin":
        return False, "launchd only on macOS"
    plist_path = _proxy_plist_path()
    run_subprocess_optimized(
        ["launchctl", "unload", str(plist_path)], check=False, capture_output=True
    )
    if plist_path.exists():
        plist_path.unlink()
    return True, "Uninstalled"


def proxy_service_start() -> tuple[bool, str]:
    """Start proxy launchd service."""
    import platform

    if platform.system() != "Darwin":
        return False, "launchd only on macOS"
    plist_path = _proxy_plist_path()
    if not plist_path.exists():
        return False, "Service not installed. Run: thegent cliproxy service install"
    run_subprocess_optimized(
        ["launchctl", "load", str(plist_path)], capture_output=True, check=True
    )
    return True, "Started"


def proxy_service_stop() -> tuple[bool, str]:
    """Stop proxy launchd service."""
    import platform

    if platform.system() != "Darwin":
        return False, "launchd only on macOS"
    plist_path = _proxy_plist_path()
    if not plist_path.exists():
        return False, "Service not installed"
    run_subprocess_optimized(
        ["launchctl", "unload", str(plist_path)], check=False, capture_output=True
    )
    return True, "Stopped"


__all__ = [
    "PROVIDER_LOGIN_CONFIG",
    "ProviderDefinitionsLoadError",
    "_LOGIN_FLAGS",
    "_binary_available",
    "_ensure_config",
    "_get_factory_api_key",
    "_get_provider_definitions",
    "_has_oauth_credentials",
    "_has_provider_credentials",
    "_inject_api_key_into_cliproxy",
    "_inject_cursor_into_cliproxy",
    "_inject_kiro_into_cliproxy",
    "_is_proxy_reachable",
    "_patch_provider_aliases",
    "_resolve_binary",
    "adapter_script_path",
    "binary_available",
    "ensure_proxy_running",
    "fetch_provider_metrics",
    "get_last_provider_metrics_status",
    "is_adapter_fallback_allowed",
    "is_adapter_running",
    "is_proxy_reachable",
    "kill_proxy",
    "proxy_service_install",
    "proxy_service_start",
    "proxy_service_stop",
    "proxy_service_uninstall",
    "resolve_binary",
    "run_login",
    "run_login_unified",
    "start_proxy_managed",
]
