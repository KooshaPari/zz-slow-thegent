"""Unit tests for multi-runtime diagnostics helpers."""

import subprocess
from unittest.mock import patch

import pytest

from thegent.infra.multi_runtime_diagnostics import (
    RuntimeStatus,
    check_cpython_313,
    check_cpython_314,
    check_hardware,
    check_mojo,
    check_network_latency,
    check_zig,
)


def _completed_process(*, returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    """Build a simple completed process object."""
    return subprocess.CompletedProcess(args=(), returncode=returncode, stdout=stdout, stderr=stderr)


class TestRuntimeStatus:
    """Tests for RuntimeStatus defaults."""

    def test_defaults_set_optimal_when_available(self):
        status = RuntimeStatus(name="Test", available=True)

        assert status.performance_tier == "optimal"

    def test_defaults_set_unavailable_when_offline(self):
        status = RuntimeStatus(name="Test", available=False)

        assert status.performance_tier == "unavailable"

    def test_explicit_performance_tier_is_preserved(self):
        status = RuntimeStatus(name="Test", available=True, performance_tier="degraded")

        assert status.performance_tier == "degraded"


class TestChecks:
    """Tests for check_* helpers."""

    def test_check_mojo_records_probe_error(self):
        with patch(
            "thegent.infra.multi_runtime_diagnostics.run_subprocess_optimized",
            side_effect=RuntimeError("mojo missing"),
        ):
            result = check_mojo()

        assert result.available is False
        assert result.performance_tier == "unavailable"
        assert "Mojo check failed: mojo missing" in result.issues

    def test_check_zig_records_probe_error(self):
        with patch(
            "thegent.infra.multi_runtime_diagnostics.run_subprocess_optimized",
            side_effect=RuntimeError("zig missing"),
        ):
            result = check_zig()

        assert result.available is False
        assert result.performance_tier == "unavailable"
        assert "Zig check failed: zig missing" in result.issues

    def test_check_cpython_313_records_orjson_probe_error(self):
        with patch(
            "thegent.infra.multi_runtime_diagnostics.run_subprocess_optimized",
            side_effect=[
                _completed_process(returncode=0, stdout="Python 3.13.0\n"),
                RuntimeError("orjson missing"),
            ],
        ):
            result = check_cpython_313()

        assert result.available is True
        assert result.performance_tier == "good"
        assert "orjson probe failed: orjson missing" in result.issues

    def test_check_cpython_314_records_orjson_probe_error(self):
        with patch(
            "thegent.infra.multi_runtime_diagnostics.run_subprocess_optimized",
            side_effect=[
                _completed_process(returncode=0, stdout="Python 3.14.0\n"),
                RuntimeError("orjson missing"),
            ],
        ):
            result = check_cpython_314()

        assert result.available is True
        assert result.performance_tier == "optimal"
        assert "orjson probe failed: orjson missing" in result.issues


class TestHardware:
    """Tests for hardware feature detection."""

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="x86_64")
    @patch("platform.release", return_value="linux")
    @patch("pathlib.Path.exists", side_effect=RuntimeError("io_uring permission denied"))
    def test_check_hardware_records_io_uring_probe_error(self, *_):
        result = check_hardware()

        assert result["platform"] == "Linux"
        assert result["arch"] == "x86_64"
        assert result["io_uring_available"] is False
        assert result["io_uring_error"] == "io_uring permission denied"


class TestNetworkLatency:
    """Tests for latency check behavior."""

    @patch("thegent.infra.multi_runtime_diagnostics.run_subprocess_optimized")
    @patch(
        "time.perf_counter",
        side_effect=[
            0.0,
            0.001,
            0.002,
            0.003,
            0.004,
            0.005,
            0.006,
            0.007,
            0.008,
            0.009,
        ],
    )
    def test_check_network_latency_success(self, *_):
        result = check_network_latency("127.0.0.1")

        assert result["avg_ms"] == pytest.approx(1.0)
        assert result["jitter_ms"] == pytest.approx(0.0)
        assert result["errors"] == []

    @patch(
        "thegent.infra.multi_runtime_diagnostics.run_subprocess_optimized",
        side_effect=RuntimeError("ping missing"),
    )
    @patch(
        "time.perf_counter",
        side_effect=[
            0.0,
            0.001,
            0.002,
            0.003,
            0.004,
            0.005,
            0.006,
            0.007,
            0.008,
            0.009,
        ],
    )
    def test_check_network_latency_collects_errors_when_unavailable(self, *_):
        result = check_network_latency("127.0.0.1")

        assert result["avg_ms"] == -1.0
        assert result["jitter_ms"] == -1.0
        assert len(result["errors"]) == 5
        assert all(item == "ping missing" for item in result["errors"])
