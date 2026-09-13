"""Runtime/process-management for the CLIProxyAPIPlus subprocess.

This module owns the *external* side of the cliproxy lifecycle:

- binary resolution + PATH lookup,
- proxy reachability + adapter surface probing,
- subprocess startup (raw proxy and adapter-launched variants) with a
  bounded readiness poll,
- port-based process termination.

Metrics fetch + status memo live in
:mod:`thegent.use_cases.manage_cliproxy_metrics` to keep this file under
the L1 500L soft cap.

All public callables are also re-exported from
:mod:`thegent.agents.cliproxy_manager` for backwards compatibility.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

from thegent.config import ThegentSettings
from thegent.infra.fast_subprocess import run_subprocess_optimized

_LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROXY_READY_TIMEOUT = 5  # iterations * 0.5s ⇒ ~2.5s default window
_PROXY_CHECK_TIMEOUT = 2  # seconds for each reachability HEAD

_CLIPROXY_NOT_FOUND_MSG = (
    "cli-proxy-api-plus not found. Install from "
    "https://github.com/kooshapari/cliproxyapi-plusplus/releases "
    "(e.g. CLIProxyAPIPlus_*_darwin_arm64.tar.gz -> extract to ~/.local/bin). "
    "Or set THGENT_CLIPROXY_BINARY=/path/to/cli-proxy-api-plus"
)


# ---------------------------------------------------------------------------
# Binary resolution
# ---------------------------------------------------------------------------


def _which(cmd: str) -> str | None:
    import shutil

    return shutil.which(cmd)


def resolve_binary(settings: ThegentSettings) -> str:
    """Resolve the CLIProxyAPIPlus binary path.

    Honours ``settings.cliproxy_binary`` (THGENT_CLIPROXY_BINARY) and
    accepts absolute paths, ``~``-prefixed paths, or bare command names
    resolvable via :func:`shutil.which` / ``~/.local/bin``.
    """
    cmd = settings.cliproxy_binary
    if "/" in cmd or "~" in cmd:
        expanded = str(Path(cmd).expanduser())
        if Path(expanded).exists():
            return expanded
        return cmd
    found = _which(cmd)
    if found:
        return found
    local = Path.home() / ".local" / "bin" / cmd
    if local.exists():
        return str(local)
    return cmd


def binary_available(binary: str) -> bool:
    """True when ``binary`` is an existing path or resolvable on PATH."""
    return Path(binary).exists() or _which(binary) is not None


# ---------------------------------------------------------------------------
# Reachability + adapter probing
# ---------------------------------------------------------------------------


def _check_path(base: str, path: str) -> bool:
    """Probe a single URL path for proxy reachability (best-effort HEAD)."""
    try:
        resp = httpx.get(
            f"{base}{path}",
            headers={"Authorization": "Bearer sk-dummy"},
            timeout=_PROXY_CHECK_TIMEOUT,
        )
        if resp.is_success:
            return True
    except Exception as exc:  # noqa: BLE001 — probe must never raise
        _LOG.debug("Proxy reachability check failed for %s: %s", f"{base}{path}", exc)
    return False


def is_proxy_reachable(base_url: str) -> bool:
    """True when any of ``/v1/models``, ``/models``, or ``/`` answers 2xx."""
    base = base_url.rstrip("/")
    paths = ("/models", "/") if base.endswith("/v1") else ("/v1/models", "/models", "/")
    return any(_check_path(base, path) for path in paths)


def is_adapter_running(base_url: str) -> bool:
    """True when the server at ``base_url`` is the Responses-API adapter.

    The adapter returns ``{"models": …}``; raw CLIProxy returns
    ``{"data": …}``. A 2xx with the wrong shape ⇒ not the adapter.
    """
    try:
        base = base_url.rstrip("/")
        url = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
        resp = httpx.get(url, timeout=2)
        if not resp.is_success:
            return False
        data = resp.json()
        if not isinstance(data, dict):
            return False
        return "models" in data
    except Exception:  # noqa: BLE001 — probing only
        return False


# ---------------------------------------------------------------------------
# Adapter launcher path resolution
# ---------------------------------------------------------------------------


def adapter_script_path() -> Path | None:
    """Path to ``start_proxy_with_adapter.py`` if shipped with the resources."""
    from thegent.utils import get_resource_path

    try:
        script = get_resource_path("scripts/start_proxy_with_adapter.py")
        return script if script.exists() else None
    except Exception:  # noqa: BLE001 — optional resource
        return None


def is_adapter_fallback_allowed() -> bool:
    """True unless the operator pinned strict-adapter mode."""
    return os.environ.get("THGENT_CLIPROXY_STRICT_ADAPTER", "").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }


# ---------------------------------------------------------------------------
# Process startup
# ---------------------------------------------------------------------------


def _start_raw_proxy(settings: ThegentSettings, base_url: str) -> str:
    """Start raw CLIProxyAPIPlus (no Responses adapter) and return the base URL."""
    binary = resolve_binary(settings)
    # Local import to avoid a circular dep through the back-compat shim.
    from thegent.agents.cliproxy_manager import _ensure_config

    config_path = _ensure_config(settings)
    _start_proxy_and_wait(binary, config_path, base_url, settings, use_adapter=False)
    return base_url


def _start_proxy_and_wait(
    binary: str,
    config_path: Path,
    base_url: str,
    settings: ThegentSettings,
    use_adapter: bool = False,
) -> subprocess.Popen[bytes]:
    """Start the proxy subprocess and wait until it answers, or raise."""
    script = adapter_script_path()
    if use_adapter and script is not None:
        env = os.environ.copy()
        env.setdefault("THGENT_CLIPROXY_PORT", str(settings.cliproxy_port))

        # Capture stderr only when debug is enabled to diagnose startup failures.
        stderr_target = subprocess.PIPE if settings.debug else None

        proc = subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(script.parent.parent),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=stderr_target,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            text=bool(stderr_target),
        )
    else:
        # cli-proxy-api-plus does not support a -debug CLI flag.
        # Keep stderr capture for diagnostics but avoid passing unsupported args.
        args = [binary, "-config", str(config_path)]
        stderr_target = subprocess.PIPE if settings.debug else None

        proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=stderr_target,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=os.environ.copy(),
            text=bool(stderr_target),
        )

    # Ready timeout: adapter script has its own internal timeouts, so we should be slightly longer
    wait_iterations = _PROXY_READY_TIMEOUT * 4  # ~10s total
    for _ in range(wait_iterations):
        time.sleep(0.5)
        if is_proxy_reachable(base_url):
            if not use_adapter or is_adapter_running(base_url):
                return proc
        if proc.poll() is not None:
            err_msg = ""
            if stderr_target:
                _, err = proc.communicate()
                err_msg = f"\nStderr: {err}"

            hint = ""
            if use_adapter:
                hint = "\nHint: Try THGENT_CLIPROXY_ADAPTER=0 for direct proxy without adapter."

            raise RuntimeError(
                f"CLIProxyAPIPlus exited with code {proc.returncode}. "
                f"Check config at {config_path}.{err_msg}{hint}\n"
                "Run with THGENT_DEBUG=1 for detailed logs."
            )

    proc.kill()
    raise RuntimeError(
        f"CLIProxyAPIPlus did not become ready within {wait_iterations * 0.5}s. "
        f"Port {settings.cliproxy_port} may be in use."
    )


def ensure_proxy_running(settings: ThegentSettings) -> str:
    """Start the proxy if it isn't reachable; return its base URL.

    Honours ``THGENT_CLIPROXY_ADAPTER=1`` for the Responses-API surface
    and ``THGENT_CLIPROXY_STRICT_ADAPTER=1`` to fail closed when the
    adapter launcher is missing or misbehaving.
    """
    port = settings.cliproxy_port
    use_adapter = settings.cliproxy_adapter and os.environ.get("THGENT_TESTING") != "1"
    fallback_allowed = is_adapter_fallback_allowed()
    base_url = f"http://127.0.0.1:{port}/v1"
    if is_proxy_reachable(base_url):
        # When adapter is requested, enforce adapter semantics and fail closed.
        if use_adapter:
            if is_adapter_running(base_url):
                return base_url
            kill_proxy(settings)
        else:
            return base_url

    binary = resolve_binary(settings)
    if not binary_available(binary):
        raise FileNotFoundError(_CLIPROXY_NOT_FOUND_MSG)

    if use_adapter:
        # Start using the adapter script; no silent fallback to raw proxy.
        from thegent.utils import get_resource_path, is_dev_mode

        script_path = get_resource_path("scripts/start_proxy_with_adapter.py")
        if not script_path.exists():
            if fallback_allowed:
                _LOG.warning(
                    "CLIProxy adapter launcher missing; using raw proxy mode for compatibility. "
                    "Set THGENT_CLIPROXY_STRICT_ADAPTER=1 to fail hard."
                )
                return _start_raw_proxy(settings, base_url)
            raise RuntimeError(
                "CLIProxy adapter is enabled but adapter launcher is missing. "
                "Expected scripts/start_proxy_with_adapter.py in thegent resources."
            )

        env = os.environ.copy()
        # If we're installed, we might not need to set PYTHONPATH
        # but for dev mode it's crucial.
        if is_dev_mode():
            env["PYTHONPATH"] = str(script_path.parents[1] / "src")

        env.setdefault("THGENT_CLIPROXY_ADAPTER", "1")
        subprocess.Popen(
            [sys.executable, str(script_path)],
            env=env,
            cwd=str(script_path.parents[1]),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        # Wait for adapter and verify it's actually the adapter surface.
        for _ in range(_PROXY_READY_TIMEOUT * 4):
            time.sleep(0.5)
            if is_proxy_reachable(base_url) and is_adapter_running(base_url):
                return base_url

        if fallback_allowed:
            _LOG.warning(
                "CLIProxy adapter failed to expose /v1/responses; using raw proxy mode for compatibility. "
                "Set THGENT_CLIPROXY_STRICT_ADAPTER=1 to fail hard."
            )
            return _start_raw_proxy(settings, base_url)
        raise RuntimeError(
            f"CLIProxy adapter is enabled, but /v1/responses adapter surface did not become ready at {base_url}."
        )

    from thegent.agents.cliproxy_manager import _ensure_config

    config_path = _ensure_config(settings)

    _start_proxy_and_wait(binary, config_path, base_url, settings, use_adapter=False)
    return base_url


def start_proxy_managed(
    settings: ThegentSettings,
) -> tuple[subprocess.Popen[bytes] | None, str]:
    """Start proxy and return ``(proc, base_url)`` for lifecycle management.

    Caller must terminate ``proc`` on shutdown. Skips when the proxy is
    already reachable (returns ``(None, base_url)``). Uses the adapter
    surface when ``THGENT_CLIPROXY_ADAPTER=1``.
    """
    base_url = f"http://127.0.0.1:{settings.cliproxy_port}/v1"
    if is_proxy_reachable(base_url):
        if settings.cliproxy_adapter and not is_adapter_running(base_url):
            kill_proxy(settings)
        else:
            return (None, base_url)

    binary = resolve_binary(settings)
    if not binary_available(binary):
        raise FileNotFoundError(_CLIPROXY_NOT_FOUND_MSG)

    from thegent.agents.cliproxy_manager import _ensure_config

    config_path = _ensure_config(settings)
    use_adapter = settings.cliproxy_adapter
    strict_adapter = os.environ.get("THGENT_CLIPROXY_STRICT_ADAPTER", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    try:
        proc = _start_proxy_and_wait(binary, config_path, base_url, settings, use_adapter=use_adapter)
    except RuntimeError as exc:
        if use_adapter and not strict_adapter:
            _LOG.warning("Adapter startup failed; falling back to raw proxy mode: %s", exc)
            kill_proxy(settings)
            proc = _start_proxy_and_wait(binary, config_path, base_url, settings, use_adapter=False)
        else:
            raise
    return (proc, base_url)


# ---------------------------------------------------------------------------
# Process termination
# ---------------------------------------------------------------------------


def kill_proxy(settings: ThegentSettings) -> bool:
    """Kill the proxy process listening on ``cliproxy_port``. Returns True on hit.

    Uses ``lsof -ti :<port>`` to find PIDs by port; works regardless of
    how the proxy was started (subprocess, launchd, manual).
    """
    try:
        result = run_subprocess_optimized(
            ["lsof", "-ti", f":{settings.cliproxy_port}"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0 or not result.stdout:
            return False
        stdout_text = (
            result.stdout if isinstance(result.stdout, str) else result.stdout.decode("utf-8", errors="replace")
        )
        if not stdout_text.strip():
            return False
        pids = [p.strip() for p in stdout_text.strip().split("\n") if p.strip()]
        for pid in pids:
            run_subprocess_optimized(["kill", "-9", pid], capture_output=True, timeout=2, check=False)
        return bool(pids)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


__all__ = [
    # constants
    "_PROXY_READY_TIMEOUT",
    "_PROXY_CHECK_TIMEOUT",
    "_CLIPROXY_NOT_FOUND_MSG",
    # binary resolution
    "resolve_binary",
    "binary_available",
    # reachability + adapter probing
    "is_proxy_reachable",
    "is_adapter_running",
    # adapter launcher
    "adapter_script_path",
    "is_adapter_fallback_allowed",
    # startup
    "_start_raw_proxy",
    "_start_proxy_and_wait",
    "ensure_proxy_running",
    "start_proxy_managed",
    # termination
    "kill_proxy",
    # underscore-prefixed aliases for back-compat with the legacy
    # ``thegent.agents.cliproxy_manager`` shim and its in-package callers.
    "_resolve_binary",
    "_binary_available",
    "_is_proxy_reachable",
    "_is_adapter_running",
    "_adapter_script_path",
    "_is_adapter_fallback_allowed",
]


# ---------------------------------------------------------------------------
# Back-compat aliases
# ---------------------------------------------------------------------------

_resolve_binary = resolve_binary
_binary_available = binary_available
_is_proxy_reachable = is_proxy_reachable
_is_adapter_running = is_adapter_running
_adapter_script_path = adapter_script_path
_is_adapter_fallback_allowed = is_adapter_fallback_allowed
