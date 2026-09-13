"""Tests for thegent.resources.network — NetworkMonitor, NetworkStats, BandwidthSample.

All psutil calls are mocked so the suite never performs real I/O or sleeps.

@trace FR-RES-001
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from thegent.resources.network import BandwidthSample, NetworkMonitor, NetworkStats

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_counter(
    bytes_sent: int = 1000,
    bytes_recv: int = 2000,
    packets_sent: int = 10,
    packets_recv: int = 20,
) -> MagicMock:
    """Return a mock object that mimics a psutil snetio named-tuple."""
    c = MagicMock()
    c.bytes_sent = bytes_sent
    c.bytes_recv = bytes_recv
    c.packets_sent = packets_sent
    c.packets_recv = packets_recv
    return c


@pytest.fixture
def monitor() -> NetworkMonitor:
    """Return a fresh NetworkMonitor for each test."""
    return NetworkMonitor()


# ---------------------------------------------------------------------------
# NetworkStats dataclass
# ---------------------------------------------------------------------------


class TestNetworkStats:
    """FR-RES-001: NetworkStats dataclass holds interface counter snapshot."""

    def test_fields_stored_correctly(self) -> None:
        t = time.time()
        stats = NetworkStats(
            interface="eth0",
            bytes_sent=100,
            bytes_recv=200,
            packets_sent=5,
            packets_recv=10,
            timestamp=t,
        )
        assert stats.interface == "eth0"
        assert stats.bytes_sent == 100
        assert stats.bytes_recv == 200
        assert stats.packets_sent == 5
        assert stats.packets_recv == 10
        assert stats.timestamp == t

    def test_timestamp_defaults_to_now(self) -> None:
        before = time.time()
        stats = NetworkStats(
            interface="lo",
            bytes_sent=0,
            bytes_recv=0,
            packets_sent=0,
            packets_recv=0,
        )
        after = time.time()
        assert before <= stats.timestamp <= after


# ---------------------------------------------------------------------------
# BandwidthSample dataclass
# ---------------------------------------------------------------------------


class TestBandwidthSample:
    """FR-RES-001: BandwidthSample dataclass holds computed bandwidth values."""

    def test_fields_stored_correctly(self) -> None:
        t = time.time()
        sample = BandwidthSample(
            interface="eth0",
            send_bps=1024.0,
            recv_bps=2048.0,
            timestamp=t,
        )
        assert sample.interface == "eth0"
        assert sample.send_bps == pytest.approx(1024.0)
        assert sample.recv_bps == pytest.approx(2048.0)
        assert sample.timestamp == t

    def test_timestamp_defaults_to_now(self) -> None:
        before = time.time()
        sample = BandwidthSample(interface="lo", send_bps=0.0, recv_bps=0.0)
        after = time.time()
        assert before <= sample.timestamp <= after


# ---------------------------------------------------------------------------
# NetworkMonitor.get_stats
# ---------------------------------------------------------------------------


class TestGetStats:
    """FR-RES-001: get_stats returns NetworkStats per interface."""

    def test_returns_stats_for_all_interfaces(self, monitor: NetworkMonitor) -> None:
        fake_counters = {
            "eth0": _make_counter(bytes_sent=100, bytes_recv=200, packets_sent=1, packets_recv=2),
            "lo": _make_counter(bytes_sent=0, bytes_recv=0, packets_sent=0, packets_recv=0),
        }
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = fake_counters
            result = monitor.get_stats()

        assert len(result) == 2
        ifaces = {s.interface for s in result}
        assert ifaces == {"eth0", "lo"}

    def test_returns_single_interface_when_specified(self, monitor: NetworkMonitor) -> None:
        fake_counters = {
            "eth0": _make_counter(bytes_sent=500, bytes_recv=600),
            "lo": _make_counter(bytes_sent=10, bytes_recv=20),
        }
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = fake_counters
            result = monitor.get_stats(interface="eth0")

        assert len(result) == 1
        assert result[0].interface == "eth0"
        assert result[0].bytes_sent == 500
        assert result[0].bytes_recv == 600

    def test_ignores_unknown_interface(self, monitor: NetworkMonitor) -> None:
        fake_counters = {"eth0": _make_counter()}
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = fake_counters
            result = monitor.get_stats(interface="nonexistent0")

        assert result == []

    def test_returns_empty_when_psutil_unavailable(self, monitor: NetworkMonitor) -> None:
        with patch("thegent.resources.network._PSUTIL_AVAILABLE", False):
            result = monitor.get_stats()
        assert result == []

    def test_returns_empty_on_psutil_exception(self, monitor: NetworkMonitor) -> None:
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.side_effect = RuntimeError("access denied")
            result = monitor.get_stats()

        assert result == []

    def test_stats_packet_counts_populated(self, monitor: NetworkMonitor) -> None:
        fake_counters = {
            "wlan0": _make_counter(packets_sent=99, packets_recv=101),
        }
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = fake_counters
            result = monitor.get_stats()

        assert result[0].packets_sent == 99
        assert result[0].packets_recv == 101

    def test_timestamp_is_recent(self, monitor: NetworkMonitor) -> None:
        fake_counters = {"eth0": _make_counter()}
        before = time.time()
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = fake_counters
            result = monitor.get_stats()
        after = time.time()
        assert before <= result[0].timestamp <= after


# ---------------------------------------------------------------------------
# NetworkMonitor.sample_bandwidth
# ---------------------------------------------------------------------------


class _TwoSampleContext:
    """Patch helper that returns *before* counters on first call, *after* on second."""

    def __init__(
        self,
        before: dict[str, dict[str, int]],
        after: dict[str, dict[str, int]],
        elapsed: float = 1.0,
    ) -> None:
        self._before = before
        self._after = after
        self._elapsed = elapsed
        self._patches: list = []

    def _make_counters(self, data: dict[str, dict[str, int]]) -> dict[str, MagicMock]:
        return {
            iface: _make_counter(
                bytes_sent=vals["bytes_sent"],
                bytes_recv=vals["bytes_recv"],
                packets_sent=vals.get("packets_sent", 0),
                packets_recv=vals.get("packets_recv", 0),
            )
            for iface, vals in data.items()
        }

    def __enter__(self) -> _TwoSampleContext:
        before_data = self._make_counters(self._before)
        after_data = self._make_counters(self._after)

        call_count = [0]

        def net_io_side_effect(pernic: bool = False) -> dict:
            call_count[0] += 1
            return before_data if call_count[0] == 1 else after_data

        t0 = 1_000_000.0
        time_call_count = [0]

        def fake_time() -> float:
            time_call_count[0] += 1
            return t0 if time_call_count[0] <= 1 else t0 + self._elapsed

        mock_psutil = MagicMock()
        mock_psutil.net_io_counters.side_effect = net_io_side_effect

        self._patches = [
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil", mock_psutil),
            patch("thegent.resources.network.time.sleep"),
            patch("thegent.resources.network.time.time", side_effect=fake_time),
        ]
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *args: object) -> None:
        for p in reversed(self._patches):
            p.stop()


class TestSampleBandwidth:
    """FR-RES-001: sample_bandwidth calculates BPS from two counter samples."""

    def test_bandwidth_calculated_correctly(self, monitor: NetworkMonitor) -> None:
        before = {"eth0": {"bytes_sent": 0, "bytes_recv": 0}}
        after = {"eth0": {"bytes_sent": 1000, "bytes_recv": 2000}}
        with _TwoSampleContext(before, after, elapsed=1.0):
            samples = monitor.sample_bandwidth(interval_s=0.001)

        assert len(samples) == 1
        s = samples[0]
        assert s.interface == "eth0"
        assert s.send_bps == pytest.approx(1000.0, rel=0.01)
        assert s.recv_bps == pytest.approx(2000.0, rel=0.01)

    def test_returns_empty_when_psutil_unavailable(self, monitor: NetworkMonitor) -> None:
        with patch("thegent.resources.network._PSUTIL_AVAILABLE", False):
            result = monitor.sample_bandwidth()
        assert result == []

    def test_returns_empty_when_no_interfaces(self, monitor: NetworkMonitor) -> None:
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
            patch("thegent.resources.network.time.sleep"),
        ):
            mock_psutil.net_io_counters.return_value = {}
            result = monitor.sample_bandwidth()
        assert result == []

    def test_clamps_negative_interval(self, monitor: NetworkMonitor) -> None:
        before = {"lo": {"bytes_sent": 0, "bytes_recv": 0}}
        after = {"lo": {"bytes_sent": 500, "bytes_recv": 500}}
        with _TwoSampleContext(before, after, elapsed=1.0):
            samples = monitor.sample_bandwidth(interval_s=-5.0)
        assert len(samples) == 1

    def test_clamps_zero_interval(self, monitor: NetworkMonitor) -> None:
        before = {"lo": {"bytes_sent": 0, "bytes_recv": 0}}
        after = {"lo": {"bytes_sent": 100, "bytes_recv": 200}}
        with _TwoSampleContext(before, after, elapsed=1.0):
            samples = monitor.sample_bandwidth(interval_s=0.0)
        assert len(samples) == 1

    def test_multiple_interfaces(self, monitor: NetworkMonitor) -> None:
        before = {
            "eth0": {"bytes_sent": 0, "bytes_recv": 0},
            "lo": {"bytes_sent": 0, "bytes_recv": 0},
        }
        after = {
            "eth0": {"bytes_sent": 3000, "bytes_recv": 6000},
            "lo": {"bytes_sent": 100, "bytes_recv": 200},
        }
        with _TwoSampleContext(before, after, elapsed=1.0):
            samples = monitor.sample_bandwidth(interval_s=0.001)

        assert len(samples) == 2
        by_iface = {s.interface: s for s in samples}
        assert by_iface["eth0"].send_bps == pytest.approx(3000.0, rel=0.01)
        assert by_iface["lo"].recv_bps == pytest.approx(200.0, rel=0.01)

    def test_interface_disappears_between_samples(self, monitor: NetworkMonitor) -> None:
        """Interface present in before but absent in after is silently skipped."""
        before = {
            "eth0": {"bytes_sent": 0, "bytes_recv": 0},
            "vpn0": {"bytes_sent": 0, "bytes_recv": 0},
        }
        after = {
            "eth0": {"bytes_sent": 500, "bytes_recv": 1000},
        }
        with _TwoSampleContext(before, after, elapsed=1.0):
            samples = monitor.sample_bandwidth(interval_s=0.001)

        ifaces = {s.interface for s in samples}
        assert "vpn0" not in ifaces
        assert "eth0" in ifaces

    def test_timestamp_comes_from_after_sample(self, monitor: NetworkMonitor) -> None:
        before = {"eth0": {"bytes_sent": 0, "bytes_recv": 0}}
        after = {"eth0": {"bytes_sent": 1000, "bytes_recv": 2000}}
        with _TwoSampleContext(before, after, elapsed=2.0):
            samples = monitor.sample_bandwidth(interval_s=0.001)
        assert samples[0].timestamp == pytest.approx(1_000_002.0, abs=0.1)


# ---------------------------------------------------------------------------
# NetworkMonitor.get_total_bandwidth
# ---------------------------------------------------------------------------


class TestGetTotalBandwidth:
    """FR-RES-001: get_total_bandwidth sums send/recv BPS across all interfaces."""

    def test_sum_across_interfaces(self, monitor: NetworkMonitor) -> None:
        sample_a = BandwidthSample(interface="eth0", send_bps=1000.0, recv_bps=2000.0)
        sample_b = BandwidthSample(interface="lo", send_bps=100.0, recv_bps=200.0)

        with patch.object(monitor, "sample_bandwidth", return_value=[sample_a, sample_b]):
            send, recv = monitor.get_total_bandwidth()

        assert send == pytest.approx(1100.0)
        assert recv == pytest.approx(2200.0)

    def test_returns_zero_when_no_samples(self, monitor: NetworkMonitor) -> None:
        with patch.object(monitor, "sample_bandwidth", return_value=[]):
            send, recv = monitor.get_total_bandwidth()

        assert send == 0.0
        assert recv == 0.0

    def test_single_interface_passthrough(self, monitor: NetworkMonitor) -> None:
        sample = BandwidthSample(interface="wlan0", send_bps=512.0, recv_bps=1024.0)
        with patch.object(monitor, "sample_bandwidth", return_value=[sample]):
            send, recv = monitor.get_total_bandwidth()
        assert send == pytest.approx(512.0)
        assert recv == pytest.approx(1024.0)

    def test_returns_zeros_when_psutil_unavailable(self, monitor: NetworkMonitor) -> None:
        with patch("thegent.resources.network._PSUTIL_AVAILABLE", False):
            send, recv = monitor.get_total_bandwidth()
        assert send == 0.0
        assert recv == 0.0

    def test_return_type_is_tuple(self, monitor: NetworkMonitor) -> None:
        with patch.object(monitor, "sample_bandwidth", return_value=[]):
            result = monitor.get_total_bandwidth()
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# NetworkMonitor.list_interfaces
# ---------------------------------------------------------------------------


class TestListInterfaces:
    """FR-RES-001: list_interfaces returns available interface names."""

    def test_lists_all_interfaces(self, monitor: NetworkMonitor) -> None:
        fake_counters = {
            "eth0": _make_counter(),
            "lo": _make_counter(),
            "wlan0": _make_counter(),
        }
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = fake_counters
            ifaces = monitor.list_interfaces()

        assert set(ifaces) == {"eth0", "lo", "wlan0"}

    def test_returns_empty_when_psutil_unavailable(self, monitor: NetworkMonitor) -> None:
        with patch("thegent.resources.network._PSUTIL_AVAILABLE", False):
            assert monitor.list_interfaces() == []

    def test_returns_empty_on_exception(self, monitor: NetworkMonitor) -> None:
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.side_effect = OSError("permission denied")
            assert monitor.list_interfaces() == []

    def test_empty_when_no_interfaces_found(self, monitor: NetworkMonitor) -> None:
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = {}
            assert monitor.list_interfaces() == []

    def test_returns_list_type(self, monitor: NetworkMonitor) -> None:
        fake_counters = {"eth0": _make_counter()}
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = fake_counters
            result = monitor.list_interfaces()
        assert isinstance(result, list)

    def test_include_diagnostics_distinguishes_empty_from_error(self, monitor: NetworkMonitor) -> None:
        with (
            patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
            patch("thegent.resources.network._psutil") as mock_psutil,
        ):
            mock_psutil.net_io_counters.return_value = {}
            payload_empty = monitor.list_interfaces(include_diagnostics=True)

            mock_psutil.net_io_counters.side_effect = OSError("permission denied")
            payload_error = monitor.list_interfaces(include_diagnostics=True)

        assert payload_empty["status"] == "empty"
        assert payload_empty["interfaces"] == []
        assert payload_error["status"] == "error"
        assert payload_error["error"]["type"] == "OSError"

    def test_include_diagnostics_reports_psutil_unavailable(self, monitor: NetworkMonitor) -> None:
        with patch("thegent.resources.network._PSUTIL_AVAILABLE", False):
            payload = monitor.list_interfaces(include_diagnostics=True)

        assert payload["status"] == "unavailable"
        assert payload["interfaces"] == []
        assert payload["error"]["type"] == "psutil_unavailable"


# ---------------------------------------------------------------------------
# Package-level exports
# ---------------------------------------------------------------------------


class TestPackageExports:
    """FR-RES-001: resources package exports the network types."""

    def test_exports_present(self) -> None:
        from thegent.resources import BandwidthSample, NetworkMonitor, NetworkStats

        assert NetworkMonitor is not None
        assert NetworkStats is not None
        assert BandwidthSample is not None

    def test_all_contains_expected_names(self) -> None:
        import thegent.resources as pkg

        assert "NetworkMonitor" in pkg.__all__
        assert "NetworkStats" in pkg.__all__
        assert "BandwidthSample" in pkg.__all__
