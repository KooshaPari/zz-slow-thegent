"""Tests for thegent.compute.tailscale.

Covers:
- TailscaleNode dataclass construction
- TailscaleConfig environment variable loading
- TailscaleManager.is_available()
- TailscaleManager.list_nodes() — success, failure, binary absent, timeout, bad JSON
- TailscaleManager._parse_status() — full peer list, empty peers, missing fields, tags
- TailscaleManager.ping_node() — success, failure, timeout, binary absent
- TailscaleManager.get_online_nodes() — filters correctly
- Package-level __init__ exports
"""

from __future__ import annotations

import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.compute import TailscaleConfig as ExportedConfig
from thegent.compute import TailscaleManager as ExportedManager
from thegent.compute import TailscaleNode as ExportedNode
from thegent.compute.tailscale import (
    TailscaleConfig,
    TailscaleError,
    TailscaleManager,
    TailscaleNode,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_status_json(peers: dict[str, Any] | None = None) -> str:
    """Return a minimal ``tailscale status --json`` payload."""
    return json.dumps({"Version": "1.60.0", "Peer": peers or {}}).decode()


def _make_peer(
    hostname: str = "myhost",
    ips: list[str] | None = None,
    os_name: str = "linux",
    online: bool = True,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "HostName": hostname,
        "TailscaleIPs": ips if ips is not None else ["100.64.0.1"],
        "OS": os_name,
        "Online": online,
        "Tags": tags,
    }


# ---------------------------------------------------------------------------
# TailscaleNode
# ---------------------------------------------------------------------------


class TestTailscaleNode:
    """Unit tests for the TailscaleNode dataclass."""

    # @trace FR-COMPUTE-001
    def test_construction_defaults(self) -> None:
        """TailscaleNode sets all fields correctly."""
        node = TailscaleNode(
            hostname="mac-studio",
            ip="100.64.0.1",
            os="darwin",
            is_online=True,
        )
        assert node.hostname == "mac-studio"
        assert node.ip == "100.64.0.1"
        assert node.os == "darwin"
        assert node.is_online is True
        assert node.tags == []

    # @trace FR-COMPUTE-001
    def test_construction_with_tags(self) -> None:
        """TailscaleNode stores provided tags."""
        node = TailscaleNode(
            hostname="win-pc",
            ip="100.64.0.2",
            os="windows",
            is_online=False,
            tags=["tag:compute", "tag:gpu"],
        )
        assert node.tags == ["tag:compute", "tag:gpu"]
        assert node.is_online is False


# ---------------------------------------------------------------------------
# TailscaleConfig
# ---------------------------------------------------------------------------


class TestTailscaleConfig:
    """Unit tests for TailscaleConfig pydantic-settings model."""

    # @trace FR-COMPUTE-002
    def test_defaults(self) -> None:
        """Default values apply when env vars are absent."""
        cfg = TailscaleConfig()
        assert cfg.api_key is None
        assert cfg.tailnet == "personal"
        assert cfg.timeout_s == 10.0

    # @trace FR-COMPUTE-002
    def test_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_TAILSCALE_API_KEY populates api_key."""
        monkeypatch.setenv("THGENT_TAILSCALE_API_KEY", "tskey-abc123")
        cfg = TailscaleConfig()
        assert cfg.api_key == "tskey-abc123"

    # @trace FR-COMPUTE-002
    def test_tailnet_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_TAILSCALE_TAILNET populates tailnet."""
        monkeypatch.setenv("THGENT_TAILSCALE_TAILNET", "myorg.github")
        cfg = TailscaleConfig()
        assert cfg.tailnet == "myorg.github"


# ---------------------------------------------------------------------------
# TailscaleManager.is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """Tests for TailscaleManager.is_available()."""

    # @trace FR-COMPUTE-003
    @patch("thegent.compute.tailscale.shutil.which")
    def test_returns_true_when_binary_found(self, mock_which: MagicMock) -> None:
        """is_available() returns True when shutil.which finds the binary."""
        mock_which.return_value = "/usr/local/bin/tailscale"
        mgr = TailscaleManager()
        assert mgr.is_available() is True
        mock_which.assert_called_once_with("tailscale")

    # @trace FR-COMPUTE-003
    @patch("thegent.compute.tailscale.shutil.which")
    def test_returns_false_when_binary_absent(self, mock_which: MagicMock) -> None:
        """is_available() returns False when shutil.which returns None."""
        mock_which.return_value = None
        mgr = TailscaleManager()
        assert mgr.is_available() is False


# ---------------------------------------------------------------------------
# TailscaleManager.list_nodes
# ---------------------------------------------------------------------------


class TestListNodes:
    """Tests for TailscaleManager.list_nodes()."""

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value=None)
    def test_returns_empty_when_binary_absent(self, _mock: MagicMock) -> None:
        """list_nodes returns [] and does NOT raise when tailscale missing."""
        mgr = TailscaleManager()
        assert mgr.list_nodes() == []

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_parses_single_peer(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """list_nodes parses a single peer correctly."""
        status = _make_status_json({"nodekey:aaa": _make_peer("mac-studio", ["100.64.0.1"], "darwin", True)})
        mock_run.return_value = MagicMock(returncode=0, stdout=status, stderr="")

        nodes = TailscaleManager().list_nodes()

        assert len(nodes) == 1
        assert nodes[0].hostname == "mac-studio"
        assert nodes[0].ip == "100.64.0.1"
        assert nodes[0].os == "darwin"
        assert nodes[0].is_online is True

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_parses_multiple_peers(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """list_nodes returns all peers."""
        peers = {
            "nodekey:aaa": _make_peer("mac", ["100.64.0.1"], "darwin", True),
            "nodekey:bbb": _make_peer("winpc", ["100.64.0.2"], "windows", False),
        }
        mock_run.return_value = MagicMock(returncode=0, stdout=_make_status_json(peers), stderr="")

        nodes = TailscaleManager().list_nodes()

        assert len(nodes) == 2
        hostnames = {n.hostname for n in nodes}
        assert hostnames == {"mac", "winpc"}

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_raises_on_nonzero_exit(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """list_nodes raises TailscaleError when the command exits non-zero."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not connected")

        with pytest.raises(TailscaleError, match="exited with 1"):
            TailscaleManager().list_nodes()

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_raises_on_bad_json(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """list_nodes raises TailscaleError when JSON cannot be parsed."""
        mock_run.return_value = MagicMock(returncode=0, stdout="not json{{", stderr="")

        with pytest.raises(TailscaleError, match="Could not parse"):
            TailscaleManager().list_nodes()

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch(
        "thegent.compute.tailscale.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="tailscale", timeout=10),
    )
    def test_raises_on_timeout(self, _run: MagicMock, _which: MagicMock) -> None:
        """list_nodes raises TailscaleError when subprocess times out."""
        with pytest.raises(TailscaleError, match="timed out"):
            TailscaleManager().list_nodes()

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run", side_effect=OSError("exec failed"))
    def test_raises_on_os_error(self, _run: MagicMock, _which: MagicMock) -> None:
        """list_nodes raises TailscaleError on OSError from subprocess."""
        with pytest.raises(TailscaleError, match="Failed to run tailscale"):
            TailscaleManager().list_nodes()

    # @trace FR-COMPUTE-004
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_empty_peer_dict(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """list_nodes returns [] when Peer section is empty."""
        mock_run.return_value = MagicMock(returncode=0, stdout=_make_status_json({}), stderr="")
        assert TailscaleManager().list_nodes() == []


# ---------------------------------------------------------------------------
# TailscaleManager._parse_status  (static method, unit-tested directly)
# ---------------------------------------------------------------------------


class TestParseStatus:
    """Unit tests for the internal _parse_status static method."""

    # @trace FR-COMPUTE-005
    def test_peer_with_tags(self) -> None:
        """Tags from the JSON are stored on the node."""
        peers = {"nodekey:x": _make_peer(tags=["tag:compute", "tag:gpu"])}
        raw = _make_status_json(peers)
        nodes = TailscaleManager._parse_status(raw)
        assert nodes[0].tags == ["tag:compute", "tag:gpu"]

    # @trace FR-COMPUTE-005
    def test_peer_with_null_tags(self) -> None:
        """Null tags are treated as an empty list."""
        peers = {"nodekey:x": _make_peer(tags=None)}
        raw = _make_status_json(peers)
        nodes = TailscaleManager._parse_status(raw)
        assert nodes[0].tags == []

    # @trace FR-COMPUTE-005
    def test_peer_missing_hostname_uses_key(self) -> None:
        """Peer with no HostName falls back to the peer key."""
        raw = json.dumps(
            {
                "Peer": {
                    "nodekey:fallback": {
                        "TailscaleIPs": ["100.1.2.3"],
                        "OS": "linux",
                        "Online": True,
                    }
                }
            }
        ).decode()
        nodes = TailscaleManager._parse_status(raw)
        assert nodes[0].hostname == "nodekey:fallback"

    # @trace FR-COMPUTE-005
    def test_peer_no_ips(self) -> None:
        """Peer with no TailscaleIPs gets an empty ip string."""
        peers = {
            "nodekey:x": {
                "HostName": "noip",
                "TailscaleIPs": [],
                "OS": "linux",
                "Online": True,
            }
        }
        nodes = TailscaleManager._parse_status(json.dumps({"Peer": peers}).decode())
        assert nodes[0].ip == ""

    # @trace FR-COMPUTE-005
    def test_peer_uses_first_ip(self) -> None:
        """When multiple IPs are present, the first is used."""
        peers = {"nodekey:x": _make_peer(ips=["100.64.0.1", "fd7a::1"])}
        nodes = TailscaleManager._parse_status(_make_status_json(peers))
        assert nodes[0].ip == "100.64.0.1"

    # @trace FR-COMPUTE-005
    def test_raises_on_non_dict_root(self) -> None:
        """_parse_status raises TailscaleError when root is not a dict."""
        with pytest.raises(TailscaleError, match="root is not an object"):
            TailscaleManager._parse_status(json.dumps([1, 2, 3]).decode())

    # @trace FR-COMPUTE-005
    def test_skips_non_dict_peer_entries(self) -> None:
        """Non-dict peer entries are skipped without raising."""
        raw = json.dumps({"Peer": {"bad": "not-a-dict", "nodekey:good": _make_peer("ok")}}).decode()
        nodes = TailscaleManager._parse_status(raw)
        assert len(nodes) == 1
        assert nodes[0].hostname == "ok"

    # @trace FR-COMPUTE-005
    def test_online_false_peer(self) -> None:
        """Offline peers are parsed with is_online=False."""
        peers = {"nodekey:x": _make_peer("offline-pc", online=False)}
        nodes = TailscaleManager._parse_status(_make_status_json(peers))
        assert nodes[0].is_online is False


# ---------------------------------------------------------------------------
# TailscaleManager.ping_node
# ---------------------------------------------------------------------------


class TestPingNode:
    """Tests for TailscaleManager.ping_node()."""

    # @trace FR-COMPUTE-006
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_ping_success(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """ping_node returns True on exit code 0."""
        mock_run.return_value = MagicMock(returncode=0, stdout="pong", stderr="")
        assert TailscaleManager().ping_node("mac-studio") is True

    # @trace FR-COMPUTE-006
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_ping_failure(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """ping_node returns False on non-zero exit code."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="no route to host")
        assert TailscaleManager().ping_node("winpc") is False

    # @trace FR-COMPUTE-006
    @patch("thegent.compute.tailscale.shutil.which", return_value=None)
    def test_ping_raises_when_binary_absent(self, _which: MagicMock) -> None:
        """ping_node raises TailscaleError when binary is missing."""
        with pytest.raises(TailscaleError, match="binary not found"):
            TailscaleManager().ping_node("any-host")

    # @trace FR-COMPUTE-006
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch(
        "thegent.compute.tailscale.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="tailscale", timeout=10),
    )
    def test_ping_returns_false_on_timeout(self, _run: MagicMock, _which: MagicMock) -> None:
        """ping_node returns False (not raises) on timeout."""
        assert TailscaleManager().ping_node("slow-host") is False

    # @trace FR-COMPUTE-006
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run", side_effect=OSError("exec failed"))
    def test_ping_raises_on_os_error(self, _run: MagicMock, _which: MagicMock) -> None:
        """ping_node raises TailscaleError on OSError."""
        with pytest.raises(TailscaleError, match="Failed to run tailscale ping"):
            TailscaleManager().ping_node("some-host")


# ---------------------------------------------------------------------------
# TailscaleManager.get_online_nodes
# ---------------------------------------------------------------------------


class TestGetOnlineNodes:
    """Tests for TailscaleManager.get_online_nodes()."""

    # @trace FR-COMPUTE-007
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_filters_offline_nodes(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """get_online_nodes returns only online nodes."""
        peers = {
            "nodekey:on": _make_peer("online-mac", online=True),
            "nodekey:off": _make_peer("offline-win", online=False),
        }
        mock_run.return_value = MagicMock(returncode=0, stdout=_make_status_json(peers), stderr="")

        online = TailscaleManager().get_online_nodes()

        assert len(online) == 1
        assert online[0].hostname == "online-mac"

    # @trace FR-COMPUTE-007
    @patch("thegent.compute.tailscale.shutil.which", return_value=None)
    def test_returns_empty_when_no_binary(self, _which: MagicMock) -> None:
        """get_online_nodes returns [] gracefully when tailscale absent."""
        assert TailscaleManager().get_online_nodes() == []

    # @trace FR-COMPUTE-007
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_all_offline(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """get_online_nodes returns [] when all peers are offline."""
        peers = {
            "nodekey:a": _make_peer("node-a", online=False),
            "nodekey:b": _make_peer("node-b", online=False),
        }
        mock_run.return_value = MagicMock(returncode=0, stdout=_make_status_json(peers), stderr="")
        assert TailscaleManager().get_online_nodes() == []

    # @trace FR-COMPUTE-007
    @patch("thegent.compute.tailscale.shutil.which", return_value="/usr/bin/tailscale")
    @patch("thegent.compute.tailscale.subprocess.run")
    def test_all_online(self, mock_run: MagicMock, _which: MagicMock) -> None:
        """get_online_nodes returns all nodes when all are online."""
        peers = {
            "nodekey:a": _make_peer("node-a", online=True),
            "nodekey:b": _make_peer("node-b", online=True),
        }
        mock_run.return_value = MagicMock(returncode=0, stdout=_make_status_json(peers), stderr="")
        online = TailscaleManager().get_online_nodes()
        assert len(online) == 2


# ---------------------------------------------------------------------------
# Package __init__ exports
# ---------------------------------------------------------------------------


class TestPackageExports:
    """Verify that compute/__init__.py re-exports Tailscale symbols."""

    # @trace FR-COMPUTE-008
    def test_tailscale_manager_exported(self) -> None:
        """TailscaleManager is importable from thegent.compute."""
        assert ExportedManager is TailscaleManager

    # @trace FR-COMPUTE-008
    def test_tailscale_node_exported(self) -> None:
        """TailscaleNode is importable from thegent.compute."""
        assert ExportedNode is TailscaleNode

    # @trace FR-COMPUTE-008
    def test_tailscale_config_exported(self) -> None:
        """TailscaleConfig is importable from thegent.compute."""
        assert ExportedConfig is TailscaleConfig
