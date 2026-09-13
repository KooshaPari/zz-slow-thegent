"""Codex via CLIProxyAPIPlus — multi-agent support.

Facade shim — re-exports from focused sub-modules.
"""

import shutil  # noqa: F401 — re-exported so test patches (codex_proxy.shutil) still work
import subprocess  # noqa: F401
from pathlib import Path  # noqa: F401

from thegent.agents.cliproxy_manager import ensure_proxy_running  # noqa: F401
from thegent.agents.codex_proxy_adapter import CodexProxyAdapter  # noqa: F401
from thegent.agents.codex_proxy_base import (  # noqa: F401
    _PROVIDER_RETRY_CONFIG,
    _PROXY_MODEL,
    CodexAuthError,
    CodexInstanceError,
    CodexModelError,
    CodexResult,
    CodexSandboxError,
    _build_config_flags,
    _check_and_track_instance,
    _create_isolated_home,
    _get_next_instance_id,
    _get_provider_retry_config,
    _is_ignorable_stderr_line,
    _isolate_codex_state,
    _normalize_context_usage_ratio,
    _parse_jsonl_output,
    _resolve_codex,
    _run_with_activity_monitoring,
    _run_with_retry,
    _write_config_override,
)
from thegent.agents.codex_proxy_runner import CodexProxyRunner  # noqa: F401

__all__ = [
    "CodexAuthError",
    "CodexInstanceError",
    "CodexModelError",
    "CodexProxyAdapter",
    "CodexProxyRunner",
    "CodexResult",
    "CodexSandboxError",
]
