"""Tests for opt-in Phase 2 hook runtime migration path."""

from __future__ import annotations

import os
import re
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _run_bash(script: str, env: dict[str, str], stdin_payload: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", script],
        input=stdin_payload,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def _write_runtime_stub(path: Path, *, fail_cache_key: bool = False) -> None:
    cache_key_block = "exit 2" if fail_cache_key else 'echo "runtime-cache-key"'
    path.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
cmd="${{1:-}}"
shift || true
case "$cmd" in
  init)
    cat >/dev/null
    cat <<'EOF'
PROJECT_DIR=/runtime/project
TOOL_NAME=Write
FILE_PATH=runtime.py
SESSION_ID=runtime-session
CWD=/runtime/project
VERIFY_DIR=/runtime/project/.claude/verification
QA_STATE=/runtime/project/.claude/qa-state.json
QUALITY_CONFIG=/runtime/project/.claude/quality.json
CHANGE_LOG=/runtime/project/.claude/session-changes.log
STOP_ACTIVE=false
INPUT={{}}
TOOL_CONTENT=runtime-content
TOOL_NEW_STRING=runtime-new
TOOL_OLD_STRING=runtime-old
EOF
    ;;
  cache-key)
    {cache_key_block}
    ;;
  cache-check)
    exit 0
    ;;
  cache-read)
    echo "runtime-cached-output"
    ;;
  cache-write)
    exit 0
    ;;
  changed-files)
    printf "a.py\\nb.py\\n"
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_hook_init_full_uses_opt_in_rust_runtime(tmp_path: Path) -> None:
    runtime_bin = tmp_path / "thegent-hooks-stub"
    _write_runtime_stub(runtime_bin)

    env = os.environ.copy()
    env["THGENT_HOOK_USE_RUST_RUNTIME"] = "1"
    env["THGENT_HOOK_RUST_RUNTIME_PATH"] = str(runtime_bin)

    cmd = """
source hooks/lib/common.sh
hook_init_full
printf '%s|%s|%s|%s' "$PROJECT_DIR" "$TOOL_NAME" "$FILE_PATH" "$TOOL_CONTENT"
"""
    proc = _run_bash(cmd, env=env, stdin_payload='{"tool_name":"Edit","cwd":"/tmp/project"}')
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "/runtime/project|Write|runtime.py|runtime-content"


def test_hook_cache_key_uses_rust_runtime_when_enabled(tmp_path: Path) -> None:
    runtime_bin = tmp_path / "thegent-hooks-stub"
    _write_runtime_stub(runtime_bin)

    env = os.environ.copy()
    env["THGENT_HOOK_USE_RUST_RUNTIME"] = "1"
    env["THGENT_HOOK_RUST_RUNTIME_PATH"] = str(runtime_bin)
    env["HEAD_SHA"] = "abc123"
    env["CHANGED_FILES_SORTED"] = "a.py\nb.py"

    cmd = """
source hooks/lib/common.sh
hook_cache_key quality-gate
"""
    proc = _run_bash(cmd, env=env)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "runtime-cache-key"


def test_hook_cache_key_falls_back_to_shell_when_runtime_fails(tmp_path: Path) -> None:
    runtime_bin = tmp_path / "thegent-hooks-stub"
    _write_runtime_stub(runtime_bin, fail_cache_key=True)

    env = os.environ.copy()
    env["THGENT_HOOK_USE_RUST_RUNTIME"] = "1"
    env["THGENT_HOOK_RUST_RUNTIME_PATH"] = str(runtime_bin)
    env["HEAD_SHA"] = "abc123"
    env["CHANGED_FILES_SORTED"] = "a.py\nb.py"

    cmd = """
source hooks/lib/common.sh
hook_cache_key quality-gate
"""
    proc = _run_bash(cmd, env=env)
    assert proc.returncode == 0, proc.stderr
    value = proc.stdout.strip()
    assert value != "runtime-cache-key"
    assert re.fullmatch(r"[0-9a-f]{64}", value), value
