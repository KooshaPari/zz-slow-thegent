from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "benchmark-quality-gate-rust.sh"


def test_wl007_benchmark_quality_gate_rust_help_exits_zero() -> None:
    result = subprocess.run(
        [str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0
    assert "WL-007 Rust Quality/Security Benchmark" in result.stdout
    assert "Usage:" in result.stdout
    assert "Required Tools:" in result.stdout


def test_wl007_benchmark_quality_gate_rust_unknown_option_exits_nonzero() -> None:
    result = subprocess.run(
        [str(SCRIPT_PATH), "--bogus-option"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode != 0
    assert "unknown option" in result.stderr
    assert "Usage:" in result.stdout


def test_wl007_benchmark_quality_gate_rust_missing_deps_exit_nonzero(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "dirname").symlink_to("/usr/bin/dirname")

    env = os.environ.copy()
    env["PATH"] = str(fake_bin)
    result = subprocess.run(
        ["/bin/zsh", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )

    assert result.returncode == 1
    assert "missing required dependency" in result.stderr
    assert "hyperfine" in result.stderr
