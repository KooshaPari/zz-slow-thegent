from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "max-lines-gate.sh"


def _run_gate(*, impl: str, path: str = "/usr/bin:/bin") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["THEGENT_MAX_LINES_IMPL"] = impl
    env["PATH"] = path
    return subprocess.run(
        ["sh", str(SCRIPT)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_wl122_max_lines_gate_rejects_invalid_impl() -> None:
    result = _run_gate(impl="bogus")
    assert result.returncode == 2
    assert "invalid THEGENT_MAX_LINES_IMPL='bogus' (use rust|zig)" in result.stderr


def test_wl122_max_lines_gate_rust_fails_loud_when_unavailable() -> None:
    result = _run_gate(impl="rust")
    assert result.returncode == 2
    assert "Rust implementation unavailable" in result.stderr


def test_wl122_max_lines_gate_zig_fails_loud_when_unavailable() -> None:
    result = _run_gate(impl="zig")
    assert result.returncode == 2
    assert "Zig implementation unavailable" in result.stderr
