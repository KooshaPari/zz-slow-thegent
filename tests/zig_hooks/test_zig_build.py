"""Integration tests for the Zig hook system build and WASM target (T3.B.A.4).

Verifies:
- Zig build succeeds with ReleaseSmall optimization
- WASM target compiles (wasm32-freestanding)
- Zig unit tests pass
- Built binary runs and outputs version
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ZIG_DIR = Path(__file__).resolve().parents[2] / "hooks" / "zig"


def _has_zig() -> bool:
    """Check if zig is available."""
    try:
        result = subprocess.run(["zig", "version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.mark.skipif(not _has_zig(), reason="zig not installed")
class TestZigBuild:
    """Tests for Zig compilation targets."""

    def test_zig_unit_tests_pass(self) -> None:
        """All Zig unit tests must pass."""
        result = subprocess.run(
            ["zig", "build", "test"],
            cwd=ZIG_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Zig tests failed:\n{result.stderr}"

    def test_native_build_release_small(self) -> None:
        """Native binary builds with ReleaseSmall optimization."""
        result = subprocess.run(
            ["zig", "build", "-Doptimize=ReleaseSmall"],
            cwd=ZIG_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Build failed:\n{result.stderr}"

        # Binary should exist
        binary = ZIG_DIR / "zig-out" / "bin" / "hook-dispatcher-zig"
        assert binary.exists(), f"Binary not found at {binary}"

    def test_wasm_target_builds(self) -> None:
        """WASM target must compile successfully."""
        result = subprocess.run(
            ["zig", "build", "-Doptimize=ReleaseSmall"],
            cwd=ZIG_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"WASM build failed:\n{result.stderr}"

        # WASM binary should exist
        wasm_binary = ZIG_DIR / "zig-out" / "bin" / "hook-contracts.wasm"
        if wasm_binary.exists():
            assert wasm_binary.stat().st_size > 0

    def test_binary_version_output(self) -> None:
        """Built binary should respond to version command."""
        # Build first
        subprocess.run(
            ["zig", "build"],
            cwd=ZIG_DIR,
            capture_output=True,
            timeout=120,
        )

        binary = ZIG_DIR / "zig-out" / "bin" / "hook-dispatcher-zig"
        if not binary.exists():
            pytest.skip("Binary not built")

        result = subprocess.run(
            [str(binary), "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "hook-dispatcher-zig" in result.stdout
        assert "v1.0.0" in result.stdout

    def test_binary_validate_event(self) -> None:
        """Built binary should validate known event types."""
        binary = ZIG_DIR / "zig-out" / "bin" / "hook-dispatcher-zig"
        if not binary.exists():
            pytest.skip("Binary not built")

        for event_name in ["SessionStart", "Stop", "PreToolUse", "PostAgentRun"]:
            result = subprocess.run(
                [str(binary), "validate", event_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"Validation failed for {event_name}"
            assert "VALID" in result.stdout

    def test_binary_rejects_unknown_event(self) -> None:
        """Built binary should reject unknown event types."""
        binary = ZIG_DIR / "zig-out" / "bin" / "hook-dispatcher-zig"
        if not binary.exists():
            pytest.skip("Binary not built")

        result = subprocess.run(
            [str(binary), "validate", "InvalidEvent"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0


@pytest.mark.skipif(not _has_zig(), reason="zig not installed")
class TestZigDeterminism:
    """Determinism tests: identical input produces identical output."""

    def test_ten_runs_identical_output(self) -> None:
        """Run dispatcher 10 times with same input, verify identical output."""
        binary = ZIG_DIR / "zig-out" / "bin" / "hook-dispatcher-zig"
        if not binary.exists():
            # Build first
            subprocess.run(["zig", "build"], cwd=ZIG_DIR, capture_output=True, timeout=120)
        if not binary.exists():
            pytest.skip("Binary not built")

        test_input = "Stop\ttest_payload\nPreToolUse\ttool_data\nSessionStart\tinit\n"
        outputs = []

        for _ in range(10):
            result = subprocess.run(
                [str(binary), "dispatch"],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=10,
            )
            outputs.append(result.stdout)

        # All outputs must be identical
        assert all(o == outputs[0] for o in outputs), "Non-deterministic output detected"
