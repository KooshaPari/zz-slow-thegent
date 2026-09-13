"""Base types, constants, and standalone helpers for codex_proxy.

Exception classes, retry configuration, model mapping, instance tracking,
and utility functions extracted from the codex_proxy monolith.
"""

import logging
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from thegent.agents.base import RunResult
from thegent.agents.resilience import TransientAgentError, is_retryable, with_retry
from thegent.utils import strip_ansi

logger = logging.getLogger(__name__)
_MALLOC_STACK_NOISE = "MallocStackLogging: can't turn off malloc stack logging because it was not enabled."
_LITELLM_CONTEXT_WINDOW_MAX = 50_000

# Provider-specific retry configuration for LiteLLM API calls
# These settings are optimized for each provider's rate limits and behavior
_PROVIDER_RETRY_CONFIG: dict[str, dict] = {
    "minimax": {
        "max_attempts": 5,
        "min_wait": 2.0,
        "max_wait": 120.0,  # MiniMax can have longer backoff
        "backoff_multiplier": 2.0,
    },
    "glm": {
        "max_attempts": 4,
        "min_wait": 2.0,
        "max_wait": 60.0,
        "backoff_multiplier": 1.5,
    },
    "nim": {
        "max_attempts": 3,
        "min_wait": 1.0,
        "max_wait": 30.0,
        "backoff_multiplier": 1.5,
    },
    "kilo": {
        "max_attempts": 3,
        "min_wait": 1.0,
        "max_wait": 30.0,
        "backoff_multiplier": 1.5,
    },
}


def _get_provider_retry_config(provider: str) -> dict:
    """Get retry configuration for a specific provider."""
    return _PROVIDER_RETRY_CONFIG.get(
        provider,
        {
            "max_attempts": 3,
            "min_wait": 1.0,
            "max_wait": 30.0,
            "backoff_multiplier": 1.5,
        },
    )


# Instance tracking for concurrent execution monitoring
_instance_counter = 0
_instance_counter_lock = threading.Lock()


def _normalize_context_usage_ratio(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class CodexResult:
    """Structured result from Codex execution with token usage and model info.

    # @trace FR-AGT-001
    """

    text: str
    exit_code: int
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""
    duration_ms: int = 0
    instance_id: str = ""
    error_type: str | None = None


class CodexInstanceError(Exception):
    """Raised when concurrent instance limit exceeded."""


class CodexAuthError(Exception):
    """Raised on authentication failures."""


class CodexSandboxError(Exception):
    """Raised on sandbox/permission errors."""


class CodexModelError(Exception):
    """Raised on model-specific errors."""


# Agent -> default model. All proxy agents use CLIProxyAPIPlus (merged into one proxy).
_PROXY_MODEL: dict[str, str] = {
    "claude": "claude-opus-4.6",
    "codex": "gpt-5.3-codex-spark",
    "gemini": "gemini-3-flash",
    "copilot": "gpt-5-mini",
    "antigravity": "gemini-3-flash",
    "minimax": "minimax-m2.5",
    "glm": "glm-5",
    "cliproxy": "gemini-3-flash",  # generic proxy fallback
    "kilo": "minimax-m2.5",
    "kiro": "claude-haiku-4.5",
    "nim": "step-3.5-flash",
    "roo": "roo-default",
    "zen": "glm-5",
    "summarizer": "gemini-3-flash",
}


def _get_next_instance_id() -> str:
    """Get unique instance ID and increment counter.

    # @trace FR-AGT-002
    """
    global _instance_counter  # noqa: PLW0603
    with _instance_counter_lock:
        _instance_counter += 1
        return f"codex-{uuid4().hex[:8]}"


def _check_and_track_instance(max_concurrent: int) -> None:
    """Verify concurrent instance count doesn't exceed max.

    Raises CodexInstanceError if limit exceeded.

    # @trace FR-AGT-002
    """
    with _instance_counter_lock:
        if _instance_counter > max_concurrent:  # type: ignore[operator]  # noqa: PLW0603
            raise CodexInstanceError(
                f"Concurrent instance limit ({max_concurrent}) exceeded. Current: {_instance_counter}"
            )


def _create_isolated_home(instance_id: str, base_dir: Path | None = None) -> Path:
    """Create isolated CODEX_HOME directory for instance.

    Args:
        instance_id: Unique instance identifier
        base_dir: Optional base directory; defaults to ~/.codex/agents/

    Returns:
        Path to isolated home directory

    # @trace FR-AGT-001
    """
    if base_dir is None:
        base_dir = Path.home() / ".codex" / "agents"
    isolated_home = base_dir / instance_id
    isolated_home.mkdir(parents=True, exist_ok=True)
    return isolated_home


def _write_config_override(config_overrides: dict[str, str], temp_dir: Path) -> Path:
    """Write temporary config.toml with overrides.

    Args:
        config_overrides: Config key-value pairs
        temp_dir: Temporary directory for config file

    Returns:
        Path to written config file

    # @trace FR-AGT-004
    """
    config_path = temp_dir / "config.toml"
    lines = []
    for key, value in config_overrides.items():
        # Basic TOML formatting; quote string values
        if isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, int | float):
            lines.append(f"{key} = {value}")
        else:
            lines.append(f'{key} = "{value}"')
    config_path.write_text("\n".join(lines))
    return config_path


def _resolve_codex() -> str:
    """Resolve codex CLI path."""
    found = shutil.which("codex")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / "codex"
    if local.exists():
        return str(local)
    return "codex"


def _isolate_codex_state(agent_index: int, shared_auth: Path | None = None) -> Path:
    """Prepare isolated Codex state directory for multi-agent use.

    Each agent gets its own ~/.codex home to avoid SQLite contention.
    Auth token is symlinked from shared location to reduce duplication.

    Args:
        agent_index: Unique agent identifier (0-9 for pool of 10)
        shared_auth: Path to shared auth file (e.g., ~/.codex/auth)

    Returns:
        Path to isolated Codex home directory

    # @trace FR-AGT-005
    """
    instance_home = Path(tempfile.gettempdir()) / f"codex-agent-{agent_index}"
    instance_home.mkdir(parents=True, exist_ok=True)

    codex_dir = instance_home / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)

    # Link auth if provided (read-only, shared token)
    if shared_auth and shared_auth.exists():
        auth_link = codex_dir / "auth"
        if not auth_link.exists():
            with suppress(OSError, FileExistsError):
                auth_link.symlink_to(shared_auth)

    return instance_home


def _build_config_flags(config: dict[str, str | int | bool] | None) -> list[str]:
    """Build -c flags for Codex config injection.

    Args:
        config: Dict of config key=value pairs

    Returns:
        List of ['-c', 'key=value', '-c', 'key=value', ...] flags

    # @trace FR-AGT-004
    """
    flags = []
    if not config:
        return flags

    for key, value in config.items():
        if isinstance(value, bool):
            val_str = "true" if value else "false"
        elif isinstance(value, str):
            val_str = value
        else:
            val_str = str(value)
        flags.extend(["-c", f"{key}={val_str}"])

    return flags


def _is_ignorable_stderr_line(line: str) -> bool:
    return _MALLOC_STACK_NOISE in line


def _run_with_activity_monitoring(
    cmd: list[str],
    prompt: str,
    cwd: Path | None,
    env: dict[str, str],
    max_idle_seconds: int,
    max_wall_time: int,
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
) -> RunResult:
    """Run codex with activity-based hang detection.

    Kills only when no output for max_idle_seconds (hung) or max_wall_time
    exceeded (if > 0).
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    if proc.stdin:
        proc.stdin.write(prompt)
        proc.stdin.close()

    out_lines: list[str] = []
    err_lines: list[str] = []
    last_activity = {"t": time.monotonic()}
    lock = threading.Lock()

    def _on_chunk(_: str) -> None:
        with lock:
            last_activity["t"] = time.monotonic()

    def _drain(
        stream,
        collector: list[str],
        cb: Callable[[str], None] | None,
        filter_noise: bool,
    ) -> None:
        for line in stream:
            clean = strip_ansi(line)
            if filter_noise and _is_ignorable_stderr_line(clean):
                continue
            collector.append(clean)
            _on_chunk(clean)
            if cb:
                cb(clean.rstrip("\n"))

    t_out = threading.Thread(
        target=_drain, args=(proc.stdout, out_lines, on_stdout, False), daemon=True
    )
    t_err = threading.Thread(
        target=_drain, args=(proc.stderr, err_lines, on_stderr, True), daemon=True
    )
    t_out.start()
    t_err.start()

    start = time.monotonic()
    rc: int | None = None
    kill_reason: str | None = None

    while True:
        ret = proc.poll()
        if ret is not None:
            rc = ret
            break

        now = time.monotonic()
        with lock:
            idle = now - last_activity["t"]
        elapsed = now - start

        if max_wall_time > 0 and elapsed >= max_wall_time:
            proc.kill()
            rc = 124
            kill_reason = f"absolute wall time ({max_wall_time}s)"
            break
        if idle >= max_idle_seconds:
            proc.kill()
            rc = 124
            kill_reason = f"no output for {max_idle_seconds}s (hung)"
            break

        time.sleep(0.5)

    t_out.join(timeout=2)
    t_err.join(timeout=2)

    stderr_msg = ""
    if kill_reason:
        stderr_msg = f"Agent stopped: {kill_reason}"
        if err_lines:
            stderr_msg = "".join(err_lines) + "\n" + stderr_msg

    result = RunResult(
        exit_code=rc if rc is not None else 1,
        stdout="".join(out_lines),
        stderr=stderr_msg or "".join(err_lines),
        timed_out=rc == 124,
    )
    return result


@with_retry(max_attempts=4, min_wait=2.0, max_wait=60.0)
def _run_with_retry(
    cmd: list[str],
    prompt: str,
    cwd: Path | None,
    timeout: int,
    env: dict[str, str],
    max_idle_seconds: int,
    max_wall_time: int,
    live_output: bool = False,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
) -> RunResult:
    """Run codex subprocess with activity-based hang detection; raises TransientAgentError on retryable failure."""
    effective_wall = max(0, max_wall_time)
    result = _run_with_activity_monitoring(
        cmd,
        prompt,
        cwd,
        env,
        max_idle_seconds=max_idle_seconds,
        max_wall_time=effective_wall,
        on_stdout=on_stdout if live_output else None,
        on_stderr=on_stderr if live_output else None,
    )
    if result.exit_code != 0 and is_retryable(result):
        raise TransientAgentError(result)
    return result


def _parse_jsonl_output(output: str) -> tuple[str, int, int, str]:  # pyright: ignore[reportUnusedFunction]
    """Parse JSONL output from Codex. Returns (text, tokens_in, tokens_out, model).

    Handles:
    - Simple JSON lines with choices[0].text
    - Streaming deltas with choices[0].delta.content
    - Token usage from usage.prompt_tokens and usage.completion_tokens
    - Model name from model field
    - Mixed JSON and plain text lines (plain text is included in output)

    Args:
        output: JSONL string (multiple JSON objects separated by newlines)

    Returns:
        Tuple of (combined_text, prompt_tokens, completion_tokens, model_name)
        where tokens default to 0 and model defaults to ""
    """
    import json

    text = ""
    tokens_in = 0
    tokens_out = 0
    model = ""

    if not output:
        return text, tokens_in, tokens_out, model

    for line in output.split("\n"):
        if not line.strip():
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            # Handle plain text lines (e.g., stderr mixed in)
            text += line
            continue

        # Extract text from choices[0].text or choices[0].delta.content
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "text" in choice:
                text += choice["text"]
            elif "delta" in choice and "content" in choice["delta"]:
                text += choice["delta"]["content"]
            elif "message" in choice and "content" in choice["message"]:
                text += choice["message"]["content"]

        # Extract token usage (last occurrence wins)
        if "usage" in data:
            usage = data["usage"]
            if "prompt_tokens" in usage:
                tokens_in = usage["prompt_tokens"]
            if "completion_tokens" in usage:
                tokens_out = usage["completion_tokens"]

        # Extract model name (last occurrence wins)
        if "model" in data:
            model = data["model"]

    return text, tokens_in, tokens_out, model
