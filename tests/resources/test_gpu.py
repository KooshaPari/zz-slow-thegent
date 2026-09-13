"""Tests for thegent.resources.gpu — GpuMonitor, GpuInfo, GpuMonitorError.

All subprocess and pynvml calls are mocked so the suite never relies on
GPU hardware being present.

@trace FR-RES-002
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from thegent.resources.gpu import GpuInfo, GpuMonitor, GpuMonitorError

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_pynvml_handle(
    name: str = "Tesla T4",
    util_gpu: int = 45,
    mem_used: int = 2 * 1024 * 1024 * 1024,
    mem_total: int = 16 * 1024 * 1024 * 1024,
    temp: float = 68.0,
) -> SimpleNamespace:
    """Build a fake pynvml device handle namespace."""
    handle = SimpleNamespace(
        _name=name,
        _util=util_gpu,
        _mem_used=mem_used,
        _mem_total=mem_total,
        _temp=temp,
    )
    return handle


def _build_pynvml_mock(
    device_count: int = 1,
    names: list[str] | None = None,
    utils: list[int] | None = None,
    mem_useds: list[int] | None = None,
    mem_totals: list[int] | None = None,
    temps: list[float] | None = None,
) -> MagicMock:
    """Return a fully-configured pynvml mock module."""
    names = names or ["Tesla T4"] * device_count
    utils = utils or [50] * device_count
    mem_useds = mem_useds or [2 * 1024 * 1024 * 1024] * device_count
    mem_totals = mem_totals or [16 * 1024 * 1024 * 1024] * device_count
    temps = temps or [70.0] * device_count

    pynvml = MagicMock()
    pynvml.NVML_TEMPERATURE_GPU = 0
    pynvml.nvmlDeviceGetCount.return_value = device_count

    handles = []
    for i in range(device_count):
        handle = MagicMock()
        pynvml.nvmlDeviceGetHandleByIndex.side_effect = lambda idx: handles[idx]
        pynvml.nvmlDeviceGetName.side_effect = lambda h: h._name
        util_obj = MagicMock()
        util_obj.gpu = utils[i]
        pynvml.nvmlDeviceGetUtilizationRates.side_effect = lambda h: h._util_obj
        mem_obj = MagicMock()
        mem_obj.used = mem_useds[i]
        mem_obj.total = mem_totals[i]
        pynvml.nvmlDeviceGetMemoryInfo.side_effect = lambda h: h._mem_obj
        pynvml.nvmlDeviceGetTemperature.side_effect = lambda h, _flag: h._temp_val

        handle._name = names[i]
        handle._util_obj = util_obj
        handle._mem_obj = mem_obj
        handle._temp_val = temps[i]
        handles.append(handle)

    pynvml.nvmlDeviceGetHandleByIndex.side_effect = lambda idx: handles[idx]
    return pynvml


def _nvidia_smi_output(entries: list[dict]) -> str:
    """Render a list of dicts into nvidia-smi CSV format."""
    lines = []
    for e in entries:
        lines.append(
            ", ".join(
                [
                    str(e.get("index", 0)),
                    e.get("name", "Tesla T4"),
                    str(e.get("util", 50)),
                    str(e.get("mem_used", 2048)),
                    str(e.get("mem_total", 16384)),
                    str(e.get("temp", 70)),
                ]
            )
        )
    return "\n".join(lines) + "\n"


@pytest.fixture
def monitor() -> GpuMonitor:
    """Return a fresh GpuMonitor for each test."""
    return GpuMonitor()


# ---------------------------------------------------------------------------
# GpuInfo dataclass
# ---------------------------------------------------------------------------


class TestGpuInfo:
    """FR-RES-002: GpuInfo stores GPU device fields correctly."""

    def test_required_fields(self) -> None:
        info = GpuInfo(
            device_id=0,
            name="RTX 4090",
            utilization_pct=75.0,
            memory_used_mb=8192.0,
            memory_total_mb=24576.0,
        )
        assert info.device_id == 0
        assert info.name == "RTX 4090"
        assert info.utilization_pct == 75.0
        assert info.memory_used_mb == 8192.0
        assert info.memory_total_mb == 24576.0
        assert info.temperature_c is None

    def test_optional_temperature(self) -> None:
        info = GpuInfo(
            device_id=1,
            name="A100",
            utilization_pct=0.0,
            memory_used_mb=0.0,
            memory_total_mb=40960.0,
            temperature_c=65.5,
        )
        assert info.temperature_c == 65.5

    def test_zero_utilization_valid(self) -> None:
        info = GpuInfo(
            device_id=0,
            name="Idle GPU",
            utilization_pct=0.0,
            memory_used_mb=500.0,
            memory_total_mb=8192.0,
        )
        assert info.utilization_pct == 0.0

    def test_full_utilization_valid(self) -> None:
        info = GpuInfo(
            device_id=0,
            name="Busy GPU",
            utilization_pct=100.0,
            memory_used_mb=8000.0,
            memory_total_mb=8192.0,
        )
        assert info.utilization_pct == 100.0


# ---------------------------------------------------------------------------
# _parse_nvidia_smi_output
# ---------------------------------------------------------------------------


class TestParseNvidiaSmiOutput:
    """FR-RES-002: nvidia-smi CSV parsing handles all edge cases."""

    def test_single_gpu_all_fields(self, monitor: GpuMonitor) -> None:
        output = "0, Tesla T4, 45, 2048, 16384, 68\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 1
        g = gpus[0]
        assert g.device_id == 0
        assert g.name == "Tesla T4"
        assert g.utilization_pct == 45.0
        assert g.memory_used_mb == 2048.0
        assert g.memory_total_mb == 16384.0
        assert g.temperature_c == 68.0

    def test_multiple_gpus(self, monitor: GpuMonitor) -> None:
        output = _nvidia_smi_output(
            [
                {
                    "index": 0,
                    "name": "GPU-0",
                    "util": 10,
                    "mem_used": 1024,
                    "mem_total": 8192,
                    "temp": 55,
                },
                {
                    "index": 1,
                    "name": "GPU-1",
                    "util": 80,
                    "mem_used": 6000,
                    "mem_total": 8192,
                    "temp": 85,
                },
            ]
        )
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 2
        assert gpus[0].device_id == 0
        assert gpus[1].device_id == 1
        assert gpus[1].utilization_pct == 80.0

    def test_temperature_na_produces_none(self, monitor: GpuMonitor) -> None:
        output = "0, Tesla T4, 45, 2048, 16384, N/A\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 1
        assert gpus[0].temperature_c is None

    def test_temperature_bracket_na_produces_none(self, monitor: GpuMonitor) -> None:
        output = "0, Tesla T4, 45, 2048, 16384, [N/A]\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert gpus[0].temperature_c is None

    def test_missing_temperature_column(self, monitor: GpuMonitor) -> None:
        output = "0, Tesla T4, 45, 2048, 16384\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 1
        assert gpus[0].temperature_c is None

    def test_empty_output_returns_empty(self, monitor: GpuMonitor) -> None:
        gpus = monitor._parse_nvidia_smi_output("")
        assert gpus == []

    def test_blank_lines_skipped(self, monitor: GpuMonitor) -> None:
        output = "\n\n0, A100, 20, 4096, 40960, 60\n\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 1

    def test_malformed_line_skipped(self, monitor: GpuMonitor) -> None:
        output = "bad_line\n0, Tesla T4, 45, 2048, 16384, 68\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 1
        assert gpus[0].name == "Tesla T4"

    def test_too_few_columns_skipped(self, monitor: GpuMonitor) -> None:
        output = "0, Tesla T4, 45, 2048\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert gpus == []

    def test_non_numeric_index_skipped(self, monitor: GpuMonitor) -> None:
        output = "X, Bad GPU, 45, 2048, 16384, 68\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert gpus == []

    def test_float_memory_values(self, monitor: GpuMonitor) -> None:
        output = "0, TestGPU, 33.5, 1024.0, 8192.0, 72.0\n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 1
        assert gpus[0].utilization_pct == 33.5
        assert gpus[0].memory_used_mb == 1024.0

    def test_whitespace_around_fields_stripped(self, monitor: GpuMonitor) -> None:
        output = " 0 ,  Tesla T4  ,  50 ,  2048 ,  16384 ,  70 \n"
        gpus = monitor._parse_nvidia_smi_output(output)
        assert len(gpus) == 1
        assert gpus[0].name == "Tesla T4"
        assert gpus[0].utilization_pct == 50.0


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """FR-RES-002: is_available() detection logic."""

    def test_available_via_pynvml(self, monitor: GpuMonitor) -> None:
        pynvml_mock = MagicMock()
        with patch("thegent.resources.gpu._import_pynvml", return_value=pynvml_mock):
            assert monitor.is_available() is True
            pynvml_mock.nvmlInit.assert_called()
            pynvml_mock.nvmlShutdown.assert_called()

    def test_available_via_nvidia_smi_when_pynvml_absent(
        self, monitor: GpuMonitor
    ) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="0\n", stderr=""
        )
        with patch(
            "thegent.resources.gpu._import_pynvml", side_effect=ImportError("no pynvml")
        ):
            with patch("thegent.resources.gpu._run_subprocess", return_value=completed):
                assert monitor.is_available() is True

    def test_not_available_when_both_absent(self, monitor: GpuMonitor) -> None:
        with patch(
            "thegent.resources.gpu._import_pynvml", side_effect=ImportError("no pynvml")
        ):
            with patch(
                "thegent.resources.gpu._run_subprocess",
                side_effect=FileNotFoundError("nvidia-smi not found"),
            ):
                assert monitor.is_available() is False

    def test_not_available_when_nvidia_smi_returns_nonzero(
        self, monitor: GpuMonitor
    ) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error"
        )
        with patch(
            "thegent.resources.gpu._import_pynvml", side_effect=ImportError("no pynvml")
        ):
            with patch("thegent.resources.gpu._run_subprocess", return_value=completed):
                assert monitor.is_available() is False


# ---------------------------------------------------------------------------
# get_gpus — pynvml path
# ---------------------------------------------------------------------------


class TestGetGpusPynvml:
    """FR-RES-002: get_gpus() pynvml code path."""

    def test_single_gpu_pynvml(self, monitor: GpuMonitor) -> None:
        pynvml = _build_pynvml_mock(
            device_count=1,
            names=["Tesla T4"],
            utils=[55],
            mem_useds=[3 * 1024 * 1024 * 1024],
            mem_totals=[16 * 1024 * 1024 * 1024],
            temps=[72.0],
        )
        with patch("thegent.resources.gpu._import_pynvml", return_value=pynvml):
            gpus = monitor.get_gpus()
        assert len(gpus) == 1
        g = gpus[0]
        assert g.device_id == 0
        assert g.name == "Tesla T4"
        assert g.utilization_pct == 55.0
        assert abs(g.memory_used_mb - 3072.0) < 1.0
        assert abs(g.memory_total_mb - 16384.0) < 1.0
        assert g.temperature_c == 72.0

    def test_two_gpus_pynvml(self, monitor: GpuMonitor) -> None:
        pynvml = _build_pynvml_mock(
            device_count=2,
            names=["GPU-A", "GPU-B"],
            utils=[30, 70],
            temps=[60.0, 80.0],
        )
        with patch("thegent.resources.gpu._import_pynvml", return_value=pynvml):
            gpus = monitor.get_gpus()
        assert len(gpus) == 2
        assert gpus[0].name == "GPU-A"
        assert gpus[1].name == "GPU-B"

    def test_pynvml_bytes_name_decoded(self, monitor: GpuMonitor) -> None:
        pynvml = _build_pynvml_mock(device_count=1)
        pynvml.nvmlDeviceGetName.side_effect = lambda _h: b"Tesla T4"
        with patch("thegent.resources.gpu._import_pynvml", return_value=pynvml):
            gpus = monitor.get_gpus()
        assert gpus[0].name == "Tesla T4"

    def test_pynvml_temperature_error_yields_none(self, monitor: GpuMonitor) -> None:
        pynvml = _build_pynvml_mock(device_count=1)
        pynvml.nvmlDeviceGetTemperature.side_effect = Exception("sensor error")
        with patch("thegent.resources.gpu._import_pynvml", return_value=pynvml):
            gpus = monitor.get_gpus()
        assert gpus[0].temperature_c is None

    def test_pynvml_nvmlinit_called(self, monitor: GpuMonitor) -> None:
        pynvml = _build_pynvml_mock(device_count=0)
        with patch("thegent.resources.gpu._import_pynvml", return_value=pynvml):
            monitor.get_gpus()
        pynvml.nvmlInit.assert_called()
        pynvml.nvmlShutdown.assert_called()

    def test_pynvml_shutdown_called_on_exception(self, monitor: GpuMonitor) -> None:
        pynvml = _build_pynvml_mock(device_count=1)
        pynvml.nvmlDeviceGetCount.side_effect = RuntimeError("boom")
        with patch("thegent.resources.gpu._import_pynvml", return_value=pynvml):
            with pytest.raises(GpuMonitorError):
                monitor.get_gpus()
        pynvml.nvmlShutdown.assert_called()


# ---------------------------------------------------------------------------
# get_gpus — nvidia-smi path
# ---------------------------------------------------------------------------


class TestGetGpusNvidiaSmi:
    """FR-RES-002: get_gpus() nvidia-smi fallback path."""

    def _patch_no_pynvml(self):
        return patch(
            "thegent.resources.gpu._import_pynvml",
            side_effect=ImportError("no pynvml"),
        )

    def test_single_gpu_via_smi(self, monitor: GpuMonitor) -> None:
        smi_out = "0, RTX 3090, 30, 4096, 24576, 65\n"
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=smi_out, stderr=""
        )
        with self._patch_no_pynvml():
            with patch("thegent.resources.gpu._run_subprocess", return_value=completed):
                gpus = monitor.get_gpus()
        assert len(gpus) == 1
        assert gpus[0].name == "RTX 3090"
        assert gpus[0].utilization_pct == 30.0

    def test_no_gpu_returns_empty_list(self, monitor: GpuMonitor) -> None:
        with (
            self._patch_no_pynvml(),
            patch(
                "thegent.resources.gpu._run_subprocess",
                side_effect=FileNotFoundError("nvidia-smi not found"),
            ),
        ):
            gpus = monitor.get_gpus()
        assert gpus == []

    def test_nonzero_returncode_returns_empty(self, monitor: GpuMonitor) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=9, stdout="", stderr="driver error"
        )
        with self._patch_no_pynvml():
            with patch("thegent.resources.gpu._run_subprocess", return_value=completed):
                gpus = monitor.get_gpus()
        assert gpus == []

    def test_timeout_raises_gpu_monitor_error(self, monitor: GpuMonitor) -> None:
        with (
            self._patch_no_pynvml(),
            patch(
                "thegent.resources.gpu._run_subprocess",
                side_effect=subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=10),
            ),
            pytest.raises(GpuMonitorError, match="timed out"),
        ):
            monitor.get_gpus()

    def test_smi_multiple_gpus(self, monitor: GpuMonitor) -> None:
        smi_out = _nvidia_smi_output(
            [
                {"index": 0, "util": 10, "temp": 55},
                {"index": 1, "util": 90, "temp": 88},
            ]
        )
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=smi_out, stderr=""
        )
        with self._patch_no_pynvml():
            with patch("thegent.resources.gpu._run_subprocess", return_value=completed):
                gpus = monitor.get_gpus()
        assert len(gpus) == 2
        assert gpus[1].utilization_pct == 90.0


# ---------------------------------------------------------------------------
# get_total_utilization
# ---------------------------------------------------------------------------


class TestGetTotalUtilization:
    """FR-RES-002: get_total_utilization() aggregation."""

    def test_no_gpus_returns_zero(self, monitor: GpuMonitor) -> None:
        with patch.object(monitor, "get_gpus", return_value=[]):
            assert monitor.get_total_utilization() == 0.0

    def test_single_gpu_returns_its_utilization(self, monitor: GpuMonitor) -> None:
        gpu = GpuInfo(0, "GPU", 60.0, 1000.0, 8000.0)
        with patch.object(monitor, "get_gpus", return_value=[gpu]):
            assert monitor.get_total_utilization() == 60.0

    def test_multiple_gpus_returns_average(self, monitor: GpuMonitor) -> None:
        gpus = [
            GpuInfo(0, "GPU-0", 40.0, 1000.0, 8000.0),
            GpuInfo(1, "GPU-1", 80.0, 1000.0, 8000.0),
        ]
        with patch.object(monitor, "get_gpus", return_value=gpus):
            assert monitor.get_total_utilization() == 60.0

    def test_all_zero_utilization(self, monitor: GpuMonitor) -> None:
        gpus = [
            GpuInfo(0, "GPU-0", 0.0, 0.0, 8000.0),
            GpuInfo(1, "GPU-1", 0.0, 0.0, 8000.0),
        ]
        with patch.object(monitor, "get_gpus", return_value=gpus):
            assert monitor.get_total_utilization() == 0.0

    def test_three_gpus_average(self, monitor: GpuMonitor) -> None:
        gpus = [
            GpuInfo(0, "GPU-0", 30.0, 0.0, 8000.0),
            GpuInfo(1, "GPU-1", 60.0, 0.0, 8000.0),
            GpuInfo(2, "GPU-2", 90.0, 0.0, 8000.0),
        ]
        with patch.object(monitor, "get_gpus", return_value=gpus):
            assert monitor.get_total_utilization() == 60.0


# ---------------------------------------------------------------------------
# GpuMonitorError
# ---------------------------------------------------------------------------


class TestGpuMonitorError:
    """FR-RES-002: GpuMonitorError is an Exception subclass."""

    def test_is_exception_subclass(self) -> None:
        assert issubclass(GpuMonitorError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(GpuMonitorError, match="test error"):
            raise GpuMonitorError("test error")

    def test_chained_exception(self) -> None:
        cause = ValueError("root cause")
        with pytest.raises(GpuMonitorError) as exc_info:
            raise GpuMonitorError("wrapped") from cause
        assert exc_info.value.__cause__ is cause
