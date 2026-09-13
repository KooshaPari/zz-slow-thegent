"""Unit tests for DiskMonitor, DiskIoStats, and DiskQueueSample.

@trace FR-RESOURCE-001
"""

from __future__ import annotations

import time
from dataclasses import fields
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from thegent.resources.disk import DiskIoStats, DiskMonitor, DiskQueueSample

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_counters(
    read_count: int = 100,
    write_count: int = 50,
    read_bytes: int = 1024,
    write_bytes: int = 512,
    read_time: int = 200,
    write_time: int = 100,
    busy_time: int | None = 150,
) -> SimpleNamespace:
    """Build a mock psutil disk_io_counters named-tuple equivalent."""
    ns = SimpleNamespace(
        read_count=read_count,
        write_count=write_count,
        read_bytes=read_bytes,
        write_bytes=write_bytes,
        read_time=read_time,
        write_time=write_time,
    )
    if busy_time is not None:
        ns.busy_time = busy_time
    return ns


# ---------------------------------------------------------------------------
# DiskIoStats dataclass
# ---------------------------------------------------------------------------


class TestDiskIoStatsDataclass:
    """Tests for DiskIoStats field definitions and defaults."""

    def test_required_fields_present(self) -> None:
        stat = DiskIoStats(
            device="sda",
            read_count=1,
            write_count=2,
            read_bytes=100,
            write_bytes=200,
            read_time_ms=10,
            write_time_ms=20,
        )
        assert stat.device == "sda"
        assert stat.busy_time_ms is None

    def test_busy_time_ms_optional_none(self) -> None:
        stat = DiskIoStats(
            device="disk0",
            read_count=0,
            write_count=0,
            read_bytes=0,
            write_bytes=0,
            read_time_ms=0,
            write_time_ms=0,
        )
        assert stat.busy_time_ms is None

    def test_busy_time_ms_can_be_set(self) -> None:
        stat = DiskIoStats(
            device="nvme0",
            read_count=10,
            write_count=5,
            read_bytes=4096,
            write_bytes=2048,
            read_time_ms=50,
            write_time_ms=25,
            busy_time_ms=60,
        )
        assert stat.busy_time_ms == 60

    def test_field_names(self) -> None:
        names = {f.name for f in fields(DiskIoStats)}
        expected = {
            "device",
            "read_count",
            "write_count",
            "read_bytes",
            "write_bytes",
            "read_time_ms",
            "write_time_ms",
            "busy_time_ms",
        }
        assert expected.issubset(names)


# ---------------------------------------------------------------------------
# DiskQueueSample dataclass
# ---------------------------------------------------------------------------


class TestDiskQueueSampleDataclass:
    """Tests for DiskQueueSample field definitions and defaults."""

    def test_fields_populated(self) -> None:
        sample = DiskQueueSample(device="sda", queue_depth=0.5, utilization_pct=50.0)
        assert sample.device == "sda"
        assert sample.queue_depth == 0.5
        assert sample.utilization_pct == 50.0

    def test_timestamp_defaults_to_now(self) -> None:
        before = time.time()
        sample = DiskQueueSample(device="sda", queue_depth=0.0, utilization_pct=0.0)
        after = time.time()
        assert before <= sample.timestamp <= after

    def test_explicit_timestamp(self) -> None:
        ts = 1_700_000_000.0
        sample = DiskQueueSample(
            device="nvme0", queue_depth=1.2, utilization_pct=75.0, timestamp=ts
        )
        assert sample.timestamp == ts

    def test_field_names(self) -> None:
        names = {f.name for f in fields(DiskQueueSample)}
        assert {"device", "queue_depth", "utilization_pct", "timestamp"}.issubset(names)


# ---------------------------------------------------------------------------
# DiskMonitor.get_io_stats
# ---------------------------------------------------------------------------


class TestGetIoStats:
    """Tests for DiskMonitor.get_io_stats()."""

    def test_returns_all_devices(self) -> None:
        counters = {
            "sda": _make_counters(read_count=10, write_count=5),
            "sdb": _make_counters(read_count=20, write_count=10),
        }
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters", return_value=counters
        ):
            stats = monitor.get_io_stats()
        devices = {s.device for s in stats}
        assert devices == {"sda", "sdb"}

    def test_filters_by_device_name(self) -> None:
        counters = {
            "sda": _make_counters(read_count=10),
            "sdb": _make_counters(read_count=99),
        }
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters", return_value=counters
        ):
            stats = monitor.get_io_stats(device="sda")
        assert len(stats) == 1
        assert stats[0].device == "sda"

    def test_device_filter_no_match_returns_empty(self) -> None:
        counters = {"sda": _make_counters()}
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters", return_value=counters
        ):
            stats = monitor.get_io_stats(device="nvme9")
        assert stats == []

    def test_maps_counters_to_dataclass_fields(self) -> None:
        c = _make_counters(
            read_count=111,
            write_count=222,
            read_bytes=333,
            write_bytes=444,
            read_time=555,
            write_time=666,
            busy_time=777,
        )
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters", return_value={"disk0": c}
        ):
            stats = monitor.get_io_stats()
        s = stats[0]
        assert s.device == "disk0"
        assert s.read_count == 111
        assert s.write_count == 222
        assert s.read_bytes == 333
        assert s.write_bytes == 444
        assert s.read_time_ms == 555
        assert s.write_time_ms == 666
        assert s.busy_time_ms == 777

    def test_busy_time_none_when_not_on_counters(self) -> None:
        c = SimpleNamespace(
            read_count=1,
            write_count=2,
            read_bytes=3,
            write_bytes=4,
            read_time=5,
            write_time=6,
        )
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters", return_value={"sda": c}
        ):
            stats = monitor.get_io_stats()
        assert stats[0].busy_time_ms is None

    def test_psutil_exception_returns_empty(self) -> None:
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters",
            side_effect=OSError("fail"),
        ):
            stats = monitor.get_io_stats()
        assert stats == []

    def test_none_return_from_psutil_handled(self) -> None:
        monitor = DiskMonitor()
        with patch("thegent.resources.disk.psutil.disk_io_counters", return_value=None):
            stats = monitor.get_io_stats()
        assert stats == []


# ---------------------------------------------------------------------------
# DiskMonitor.list_devices
# ---------------------------------------------------------------------------


class TestListDevices:
    """Tests for DiskMonitor.list_devices()."""

    def test_returns_sorted_device_names(self) -> None:
        counters = {
            "sdb": _make_counters(),
            "sda": _make_counters(),
            "nvme0": _make_counters(),
        }
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters", return_value=counters
        ):
            devices = monitor.list_devices()
        assert devices == sorted(counters.keys())

    def test_empty_when_no_devices(self) -> None:
        monitor = DiskMonitor()
        with patch("thegent.resources.disk.psutil.disk_io_counters", return_value={}):
            devices = monitor.list_devices()
        assert devices == []

    def test_psutil_exception_returns_empty(self) -> None:
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters",
            side_effect=RuntimeError("oops"),
        ):
            devices = monitor.list_devices()
        assert devices == []

    def test_none_return_handled(self) -> None:
        monitor = DiskMonitor()
        with patch("thegent.resources.disk.psutil.disk_io_counters", return_value=None):
            devices = monitor.list_devices()
        assert devices == []

    def test_single_device(self) -> None:
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_io_counters",
            return_value={"disk0": _make_counters()},
        ):
            devices = monitor.list_devices()
        assert devices == ["disk0"]


# ---------------------------------------------------------------------------
# DiskMonitor.get_disk_usage
# ---------------------------------------------------------------------------


class TestGetDiskUsage:
    """Tests for DiskMonitor.get_disk_usage()."""

    def test_default_path_is_root(self) -> None:
        usage = MagicMock(total=100, used=60, free=40, percent=60.0)
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_usage", return_value=usage
        ) as mock_du:
            result = monitor.get_disk_usage()
        mock_du.assert_called_once_with("/")
        assert result["total"] == 100
        assert result["used"] == 60
        assert result["free"] == 40
        assert result["percent"] == 60.0

    def test_custom_path(self) -> None:
        usage = MagicMock(total=500, used=250, free=250, percent=50.0)
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_usage", return_value=usage
        ) as mock_du:
            result = monitor.get_disk_usage("/home")
        mock_du.assert_called_once_with("/home")
        assert result["used"] == 250

    def test_oserror_returns_empty_dict(self) -> None:
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_usage",
            side_effect=OSError("no such path"),
        ):
            result = monitor.get_disk_usage("/nonexistent")
        assert result == {}

    def test_value_error_returns_empty_dict(self) -> None:
        monitor = DiskMonitor()
        with patch(
            "thegent.resources.disk.psutil.disk_usage", side_effect=ValueError("bad")
        ):
            result = monitor.get_disk_usage("/badpath")
        assert result == {}

    def test_result_keys(self) -> None:
        usage = MagicMock(total=1024, used=512, free=512, percent=50.0)
        monitor = DiskMonitor()
        with patch("thegent.resources.disk.psutil.disk_usage", return_value=usage):
            result = monitor.get_disk_usage()
        assert set(result.keys()) == {"total", "used", "free", "percent"}


# ---------------------------------------------------------------------------
# DiskMonitor.sample_queue_depth  (uses patch on get_io_stats)
# ---------------------------------------------------------------------------


class TestSampleQueueDepth:
    """Tests for DiskMonitor.sample_queue_depth()."""

    def test_utilization_with_busy_time(self) -> None:
        before = [DiskIoStats("sda", 100, 50, 1024, 512, 200, 100, busy_time_ms=500)]
        after = [DiskIoStats("sda", 110, 55, 2048, 1024, 250, 140, busy_time_ms=600)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert len(samples) == 1
        s = samples[0]
        assert s.device == "sda"
        # busy_delta = 600 - 500 = 100 ms out of 1000 ms => 10% utilization
        assert pytest.approx(s.utilization_pct, abs=1e-3) == 10.0

    def test_utilization_without_busy_time(self) -> None:
        before = [DiskIoStats("sda", 100, 50, 1024, 512, 200, 100, busy_time_ms=None)]
        after = [DiskIoStats("sda", 110, 55, 2048, 1024, 400, 200, busy_time_ms=None)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert len(samples) == 1
        s = samples[0]
        # (read_time delta 200 + write_time delta 100) = 300 ms / 1000 ms = 30%
        assert pytest.approx(s.utilization_pct, abs=1e-3) == 30.0

    def test_queue_depth_computed(self) -> None:
        # 10 ops in 1s, 50% utilization => queue_depth = 0.5 * 10 = 5.0
        before = [DiskIoStats("sda", 100, 0, 0, 0, 0, 0, busy_time_ms=0)]
        after = [DiskIoStats("sda", 110, 0, 0, 0, 0, 0, busy_time_ms=500)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert len(samples) == 1
        s = samples[0]
        assert pytest.approx(s.queue_depth, abs=1e-3) == 5.0

    def test_device_not_in_before_skipped(self) -> None:
        before: list[DiskIoStats] = []
        after = [DiskIoStats("sda", 10, 5, 0, 0, 0, 0)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert samples == []

    def test_multiple_devices(self) -> None:
        before = [
            DiskIoStats("sda", 100, 0, 0, 0, 0, 0, busy_time_ms=0),
            DiskIoStats("sdb", 200, 0, 0, 0, 0, 0, busy_time_ms=0),
        ]
        after = [
            DiskIoStats("sda", 110, 0, 0, 0, 0, 0, busy_time_ms=200),
            DiskIoStats("sdb", 205, 0, 0, 0, 0, 0, busy_time_ms=400),
        ]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert len(samples) == 2
        by_dev = {s.device: s for s in samples}
        assert pytest.approx(by_dev["sda"].utilization_pct, abs=1e-3) == 20.0
        assert pytest.approx(by_dev["sdb"].utilization_pct, abs=1e-3) == 40.0

    def test_zero_utilization_when_idle(self) -> None:
        before = [DiskIoStats("sda", 100, 50, 0, 0, 100, 50, busy_time_ms=500)]
        after = [DiskIoStats("sda", 100, 50, 0, 0, 100, 50, busy_time_ms=500)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert len(samples) == 1
        assert samples[0].utilization_pct == 0.0
        assert samples[0].queue_depth == 0.0

    def test_busy_time_clamped_to_elapsed(self) -> None:
        # busy_time delta > elapsed => should be clamped to 100%
        before = [DiskIoStats("sda", 100, 0, 0, 0, 0, 0, busy_time_ms=0)]
        after = [DiskIoStats("sda", 110, 0, 0, 0, 0, 0, busy_time_ms=5000)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert len(samples) == 1
        assert samples[0].utilization_pct <= 100.0

    def test_negative_busy_delta_clamped_to_zero(self) -> None:
        # Counter wrap-around: after < before for busy_time
        before = [DiskIoStats("sda", 100, 0, 0, 0, 0, 0, busy_time_ms=900)]
        after = [DiskIoStats("sda", 110, 0, 0, 0, 0, 0, busy_time_ms=100)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert len(samples) == 1
        assert samples[0].utilization_pct == 0.0

    def test_invalid_interval_coerced_to_one(self) -> None:
        before = [DiskIoStats("sda", 100, 0, 0, 0, 0, 0, busy_time_ms=0)]
        after = [DiskIoStats("sda", 110, 0, 0, 0, 0, 0, busy_time_ms=0)]

        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep") as mock_sleep,
        ):
            monitor.sample_queue_depth(interval_s=-5.0)
        # interval_s coerced to 1.0 -> time.sleep(1.0)
        mock_sleep.assert_called_once_with(1.0)

    def test_timestamp_is_set(self) -> None:
        before = [DiskIoStats("sda", 100, 0, 0, 0, 0, 0, busy_time_ms=0)]
        after = [DiskIoStats("sda", 110, 0, 0, 0, 0, 0, busy_time_ms=100)]

        monitor = DiskMonitor()
        t_before = time.time()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[before, after]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)
        t_after = time.time()

        assert len(samples) == 1
        assert t_before <= samples[0].timestamp <= t_after

    def test_returns_empty_when_no_devices(self) -> None:
        monitor = DiskMonitor()
        with (
            patch.object(monitor, "get_io_stats", side_effect=[[], []]),
            patch("thegent.resources.disk.time.sleep"),
        ):
            samples = monitor.sample_queue_depth(interval_s=1.0)

        assert samples == []


# ---------------------------------------------------------------------------
# psutil unavailable fallback
# ---------------------------------------------------------------------------


class TestPsutilFallback:
    """Tests that all methods return safe defaults when psutil is missing."""

    def test_get_io_stats_returns_empty_list(self) -> None:
        monitor = DiskMonitor()
        with patch("thegent.resources.disk._PSUTIL_AVAILABLE", False):
            stats = monitor.get_io_stats()
        assert stats == []

    def test_list_devices_returns_empty_list(self) -> None:
        monitor = DiskMonitor()
        with patch("thegent.resources.disk._PSUTIL_AVAILABLE", False):
            devices = monitor.list_devices()
        assert devices == []

    def test_get_disk_usage_returns_empty_dict(self) -> None:
        monitor = DiskMonitor()
        with patch("thegent.resources.disk._PSUTIL_AVAILABLE", False):
            usage = monitor.get_disk_usage("/")
        assert usage == {}

    def test_sample_queue_depth_returns_empty_list(self) -> None:
        monitor = DiskMonitor()
        with patch("thegent.resources.disk._PSUTIL_AVAILABLE", False):
            samples = monitor.sample_queue_depth(interval_s=0.001)
        assert samples == []


# ---------------------------------------------------------------------------
# Package-level exports
# ---------------------------------------------------------------------------


class TestPackageExports:
    """Confirm that resources/__init__.py re-exports disk classes."""

    def test_imports_from_package(self) -> None:
        import thegent.resources as pkg

        assert pkg.DiskIoStats is DiskIoStats
        assert pkg.DiskMonitor is DiskMonitor
        assert pkg.DiskQueueSample is DiskQueueSample

    def test_all_contains_disk_classes(self) -> None:
        import thegent.resources as mod

        assert "DiskIoStats" in mod.__all__
        assert "DiskMonitor" in mod.__all__
        assert "DiskQueueSample" in mod.__all__
