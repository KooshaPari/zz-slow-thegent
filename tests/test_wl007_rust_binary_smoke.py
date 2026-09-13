from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CARGO_WORKDIR = ROOT / "crates"
HELP_TIMEOUT_SECONDS = 90
HELP_TIMEOUT_SECONDS = 180


def _has_rust_toolchain() -> bool:
    return shutil.which("cargo") is not None and shutil.which("rustc") is not None


def _run_help(bin_name: str) -> subprocess.CompletedProcess[str]:
    cmd = ["cargo", "run", "-q", "-p", "thegent-hooks", "--bin", bin_name, "--", "--help"]
    try:
        return subprocess.run(
            cmd,
            cwd=CARGO_WORKDIR,
            text=True,
            capture_output=True,
            check=False,
            timeout=HELP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"{bin_name} --help timed out after {HELP_TIMEOUT_SECONDS}s: {exc}")
        pytest.skip(f"{bin_name} --help timed out after {HELP_TIMEOUT_SECONDS}s on this host: {exc}")


pytestmark = pytest.mark.skipif(not _has_rust_toolchain(), reason="Rust toolchain (cargo + rustc) is required")


@pytest.mark.parametrize("bin_name", ["quality-gate", "security-pipeline"])
def test_wl007_rust_hook_binaries_help_callable(bin_name: str) -> None:
    result = _run_help(bin_name)

    output = f"{result.stdout}\n{result.stderr}"
    # Current binaries do not expose a clap-style --help and instead parse stdin JSON.
    # We still verify the entrypoint is callable via its deterministic parse-error response.
    assert result.returncode in {0, 124}, output
    if result.returncode == 0:
        assert "Usage" in output or "USAGE" in output
    else:
        assert f"{bin_name}: invalid input JSON" in output
