"""Tests for WL-050 Phase 5 Adaptive Scale components.

Covers:
  WP-5001: TailscaleComputePool, RemoteNodeClient, ComputePoolManager.expand()
  WP-5002: SyncthingWorkspaceSync.push / pull
  WP-5003: WatcherDaemon scale-up / scale-down decisions
  WP-5004: FederatedLoadBalancer node selection

# @trace WL-050 WP-5001 WP-5002 WP-5003 WP-5004
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from thegent.compute.offload import (
    ComputeNode,
    ComputePoolManager,
    FederatedLoadBalancer,
    RemoteNodeClient,
    RemoteNodeError,
    TailscaleComputePool,
)
from thegent.compute.syncthing import SyncthingError, SyncthingWorkspaceSync
from thegent.compute.tailscale import TailscaleError, TailscaleNode
from thegent.sitback.watchdog import WatcherDaemon

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_node(node_id: str = "node-1", latency: float = 0.0) -> ComputeNode:
    """Build a ComputeNode for testing."""
    return ComputeNode(
        node_id=node_id,
        base_url="http://100.64.0.1:9001",
        is_available=True,
        ema_latency_ms=latency,
    )


def _make_tailscale_node(hostname: str = "remote-host", ip: str = "100.64.0.2", online: bool = True) -> TailscaleNode:
    return TailscaleNode(hostname=hostname, ip=ip, os="linux", is_online=online)


def _make_agent_task() -> Any:
    from thegent.core.worker_pool import AgentTask

    return AgentTask(
        task_id="test-task-1",
        prompt="do something",
        cwd="/tmp",
    )


def _make_agent_result(task_id: str = "test-task-1") -> Any:
    from thegent.core.worker_pool import AgentResult

    return AgentResult(
        task_id=task_id,
        exit_code=0,
        stdout="done",
        stderr="",
    )


def _make_http_response(status_code: int = 200, json_body: Any = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if json_body is not None:
        resp.content = b"x"
        resp.json.return_value = json_body
    else:
        resp.content = b""
        resp.json.side_effect = ValueError("no body")
    if status_code >= 400:
        resp.text = f"HTTP {status_code}"
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# WP-5001: ComputeNode
# ---------------------------------------------------------------------------


class TestComputeNode:
    """Unit tests for ComputeNode EMA latency tracking.

    # @trace WL-050 WP-5001
    """

    def test_initial_latency_zero(self) -> None:
        """Default EMA latency is 0.0."""
        node = _make_node()
        assert node.ema_latency_ms == 0.0

    def test_first_update_sets_latency(self) -> None:
        """First update sets EMA to the observed value."""
        node = _make_node()
        node.update_latency(100.0)
        assert node.ema_latency_ms == 100.0

    def test_subsequent_updates_apply_ema(self) -> None:
        """Subsequent updates blend with the previous EMA."""
        node = _make_node()
        node.update_latency(100.0)
        node.update_latency(200.0)
        # EMA: 0.2 * 200 + 0.8 * 100 = 120
        assert abs(node.ema_latency_ms - 120.0) < 0.01

    def test_availability_flag(self) -> None:
        """is_available can be set."""
        node = _make_node()
        assert node.is_available is True
        node.is_available = False
        assert node.is_available is False


# ---------------------------------------------------------------------------
# WP-5001: RemoteNodeClient
# ---------------------------------------------------------------------------


class TestRemoteNodeClient:
    """Unit tests for RemoteNodeClient HTTP dispatch.

    # @trace WL-050 WP-5001
    """

    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        """Successful POST /execute returns populated AgentResult."""
        node = _make_node()
        task = _make_agent_task()
        resp_data = {
            "task_id": task.task_id,
            "exit_code": 0,
            "stdout": "hello",
            "stderr": "",
            "timed_out": False,
            "duration_ms": 50.0,
            "worker_pid": 1234,
        }
        resp = _make_http_response(200, resp_data)

        client = RemoteNodeClient(node, timeout_s=5.0)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=resp)
        mock_http.is_closed = False

        with patch.object(client, "_get_client", return_value=mock_http):
            result = await client.execute(task)

        assert result.exit_code == 0
        assert result.stdout == "hello"
        assert result.task_id == task.task_id
        mock_http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_http_error_raises(self) -> None:
        """HTTP 500 raises RemoteNodeError."""
        node = _make_node()
        task = _make_agent_task()
        resp = _make_http_response(500, {"error": "internal"})

        client = RemoteNodeClient(node, timeout_s=5.0)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=resp)
        mock_http.is_closed = False

        with patch.object(client, "_get_client", return_value=mock_http):
            with pytest.raises(RemoteNodeError, match="HTTP 500"):
                await client.execute(task)

    @pytest.mark.asyncio
    async def test_execute_connection_error_raises(self) -> None:
        """httpx.ConnectError raises RemoteNodeError."""
        node = _make_node()
        task = _make_agent_task()

        client = RemoteNodeClient(node, timeout_s=5.0)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_http.is_closed = False

        with patch.object(client, "_get_client", return_value=mock_http):
            with pytest.raises(RemoteNodeError, match="connection error"):
                await client.execute(task)

    @pytest.mark.asyncio
    async def test_execute_updates_node_latency(self) -> None:
        """Successful execute updates EMA latency on the ComputeNode."""
        node = _make_node()
        task = _make_agent_task()
        resp_data = {
            "task_id": task.task_id,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
            "duration_ms": 80.0,
            "worker_pid": 0,
        }
        resp = _make_http_response(200, resp_data)

        client = RemoteNodeClient(node, timeout_s=5.0)
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=resp)
        mock_http.is_closed = False

        with patch.object(client, "_get_client", return_value=mock_http):
            await client.execute(task)

        assert node.ema_latency_ms > 0.0

    @pytest.mark.asyncio
    async def test_execute_sets_auth_header(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Shared secret is passed as X-Compute-Token header."""
        monkeypatch.setenv("THGENT_COMPUTE_SHARED_SECRET", "super-secret")
        node = _make_node()
        client = RemoteNodeClient(node, timeout_s=5.0)
        # Force re-read of env by resetting the cached value
        client._secret = "super-secret"
        http_client = client._get_client()
        assert "X-Compute-Token" in http_client.headers
        assert http_client.headers["X-Compute-Token"] == "super-secret"
        await http_client.aclose()


# ---------------------------------------------------------------------------
# WP-5001: TailscaleComputePool
# ---------------------------------------------------------------------------


class TestTailscaleComputePool:
    """Unit tests for TailscaleComputePool.

    # @trace WL-050 WP-5001
    """

    def test_refresh_discovers_online_nodes(self) -> None:
        """refresh() builds ComputeNode entries for online peers."""
        ts_mgr = MagicMock()
        ts_mgr.is_available.return_value = True
        ts_mgr.get_online_nodes.return_value = [
            _make_tailscale_node("worker-a", "100.64.0.2"),
            _make_tailscale_node("worker-b", "100.64.0.3"),
        ]

        pool = TailscaleComputePool(tailscale_manager=ts_mgr, worker_port=9001)
        nodes = pool.refresh()

        assert len(nodes) == 2
        ids = {n.node_id for n in nodes}
        assert ids == {"worker-a", "worker-b"}

    def test_refresh_filters_by_hostname_pattern(self) -> None:
        """hostname_pattern filters out non-matching peers."""
        ts_mgr = MagicMock()
        ts_mgr.is_available.return_value = True
        ts_mgr.get_online_nodes.return_value = [
            _make_tailscale_node("gpu-worker-1"),
            _make_tailscale_node("cpu-node-99"),
        ]

        pool = TailscaleComputePool(tailscale_manager=ts_mgr, hostname_pattern="gpu")
        nodes = pool.refresh()

        assert len(nodes) == 1
        assert nodes[0].node_id == "gpu-worker-1"

    def test_refresh_preserves_existing_node_latency(self) -> None:
        """Refreshing keeps EMA latency on already-known nodes."""
        ts_mgr = MagicMock()
        ts_mgr.is_available.return_value = True
        ts_mgr.get_online_nodes.return_value = [_make_tailscale_node("worker-a")]

        pool = TailscaleComputePool(tailscale_manager=ts_mgr)
        pool.refresh()
        # Manually set latency on the discovered node
        pool._nodes["worker-a"].ema_latency_ms = 42.0

        # Refresh again — existing node should be reused
        pool.refresh()
        assert pool._nodes["worker-a"].ema_latency_ms == 42.0

    def test_refresh_returns_empty_when_tailscale_unavailable(self) -> None:
        """refresh() returns [] when tailscale binary is absent (enabled flag NOT set)."""
        ts_mgr = MagicMock()
        ts_mgr.is_available.return_value = False

        pool = TailscaleComputePool(tailscale_manager=ts_mgr)
        nodes = pool.refresh()
        assert nodes == []

    def test_refresh_raises_when_tailscale_required_but_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """refresh() raises TailscaleError when THGENT_TAILSCALE_ENABLED=1 and binary absent."""
        monkeypatch.setenv("THGENT_TAILSCALE_ENABLED", "1")
        ts_mgr = MagicMock()
        ts_mgr.is_available.return_value = False

        pool = TailscaleComputePool(tailscale_manager=ts_mgr)
        with pytest.raises(TailscaleError, match="THGENT_TAILSCALE_ENABLED"):
            pool.refresh()

    def test_add_node_registers_manually(self) -> None:
        """add_node() registers a compute node bypassing Tailscale discovery."""
        pool = TailscaleComputePool(tailscale_manager=MagicMock())
        node = _make_node("manual-node")
        pool.add_node(node)
        assert "manual-node" in {n.node_id for n in pool.get_nodes()}

    def test_remove_node_deregisters(self) -> None:
        """remove_node() removes a previously registered node."""
        pool = TailscaleComputePool(tailscale_manager=MagicMock())
        node = _make_node("manual-node")
        pool.add_node(node)
        pool.remove_node("manual-node")
        assert "manual-node" not in {n.node_id for n in pool.get_nodes()}


# ---------------------------------------------------------------------------
# WP-5001: ComputePoolManager.expand
# ---------------------------------------------------------------------------


class TestComputePoolManagerExpand:
    """Unit tests for ComputePoolManager pool expansion.

    # @trace WL-050 WP-5001
    """

    def test_expand_adds_remote_nodes(self) -> None:
        """expand(2) adds up to 2 nodes from TailscaleComputePool."""
        ts_pool = TailscaleComputePool(tailscale_manager=MagicMock())
        ts_pool._nodes = {
            "node-a": _make_node("node-a"),
            "node-b": _make_node("node-b"),
            "node-c": _make_node("node-c"),
        }

        with patch.object(ts_pool, "refresh", return_value=list(ts_pool._nodes.values())):
            mgr = ComputePoolManager(compute_pool=ts_pool)
            added = mgr.expand(2)

        assert len(added) == 2

    def test_expand_does_not_duplicate_existing_nodes(self) -> None:
        """expand() skips nodes already present in the load balancer."""
        ts_pool = TailscaleComputePool(tailscale_manager=MagicMock())
        node_a = _make_node("node-a")
        ts_pool._nodes = {"node-a": node_a, "node-b": _make_node("node-b")}

        mgr = ComputePoolManager(compute_pool=ts_pool)
        # Pre-populate with node-a
        mgr._load_balancer.add_node(node_a)

        with patch.object(ts_pool, "refresh", return_value=list(ts_pool._nodes.values())):
            added = mgr.expand(2)

        added_ids = {n.node_id for n in added}
        assert "node-a" not in added_ids
        assert "node-b" in added_ids

    def test_expand_returns_empty_when_no_nodes_available(self) -> None:
        """expand() returns [] when Tailscale pool is empty."""
        ts_pool = TailscaleComputePool(tailscale_manager=MagicMock())

        with patch.object(ts_pool, "refresh", return_value=[]):
            mgr = ComputePoolManager(compute_pool=ts_pool)
            added = mgr.expand(2)

        assert added == []

    def test_expand_respects_n_nodes_limit(self) -> None:
        """expand(1) adds at most 1 node even when more are available."""
        ts_pool = TailscaleComputePool(tailscale_manager=MagicMock())
        ts_pool._nodes = {f"node-{i}": _make_node(f"node-{i}") for i in range(5)}

        with patch.object(ts_pool, "refresh", return_value=list(ts_pool._nodes.values())):
            mgr = ComputePoolManager(compute_pool=ts_pool)
            added = mgr.expand(1)

        assert len(added) == 1


# ---------------------------------------------------------------------------
# WP-5001: ComputePoolManager.shrink
# ---------------------------------------------------------------------------


class TestComputePoolManagerShrink:
    """Unit tests for ComputePoolManager.shrink().

    # @trace WL-050 WP-5001
    """

    def test_shrink_releases_long_idle_nodes(self) -> None:
        """shrink() releases nodes that have been idle > 5 minutes."""
        ts_pool = TailscaleComputePool(tailscale_manager=MagicMock())
        mgr = ComputePoolManager(compute_pool=ts_pool)

        node = _make_node("idle-node")
        mgr._load_balancer.add_node(node)
        ts_pool._nodes["idle-node"] = node
        # Backdate idle_since by 400 seconds
        mgr._remote_idle_since["idle-node"] = time.monotonic() - 400.0

        released = mgr.shrink()
        assert "idle-node" in released
        remaining_ids = {n.node_id for n in mgr._load_balancer._nodes}
        assert "idle-node" not in remaining_ids

    def test_shrink_keeps_recently_idle_nodes(self) -> None:
        """shrink() keeps nodes that became idle < 5 minutes ago."""
        ts_pool = TailscaleComputePool(tailscale_manager=MagicMock())
        mgr = ComputePoolManager(compute_pool=ts_pool)

        node = _make_node("fresh-idle")
        mgr._load_balancer.add_node(node)
        # Mark as idle only 60 seconds ago
        mgr._remote_idle_since["fresh-idle"] = time.monotonic() - 60.0

        released = mgr.shrink()
        assert "fresh-idle" not in released

    def test_shrink_does_nothing_when_no_idle_nodes(self) -> None:
        """shrink() returns [] when no remote nodes are tracked as idle."""
        mgr = ComputePoolManager()
        released = mgr.shrink()
        assert released == []

    def test_mark_remote_idle_and_busy(self) -> None:
        """mark_remote_idle sets idle time; mark_remote_busy clears it."""
        mgr = ComputePoolManager()
        mgr.mark_remote_idle("node-x")
        assert "node-x" in mgr._remote_idle_since

        mgr.mark_remote_busy("node-x")
        assert "node-x" not in mgr._remote_idle_since


# ---------------------------------------------------------------------------
# WP-5002: SyncthingWorkspaceSync
# ---------------------------------------------------------------------------


class TestSyncthingWorkspaceSync:
    """Unit tests for SyncthingWorkspaceSync push/pull.

    # @trace WL-050 WP-5002
    """

    @pytest.mark.asyncio
    async def test_push_creates_new_folder(self) -> None:
        """push() calls add_folder when folder does not yet exist."""
        syncthing_mgr = AsyncMock()
        syncthing_mgr.get_folders.return_value = []
        syncthing_mgr.add_folder.return_value = True

        sync = SyncthingWorkspaceSync(manager=syncthing_mgr)
        folder_id = await sync.push("/workspace/myproject", ["DEV1", "DEV2"])

        assert folder_id == "thegent-ws-myproject"
        syncthing_mgr.add_folder.assert_called_once_with(
            folder_id="thegent-ws-myproject",
            path="/workspace/myproject",
            label="thegent workspace: /workspace/myproject",
            device_ids=["DEV1", "DEV2"],
        )

    @pytest.mark.asyncio
    async def test_push_skips_existing_folder(self) -> None:
        """push() does not call add_folder when folder already exists."""
        from thegent.compute.syncthing import SyncthingFolder

        syncthing_mgr = AsyncMock()
        syncthing_mgr.get_folders.return_value = [
            SyncthingFolder(folder_id="thegent-ws-myproject", path="/workspace/myproject", label="ws")
        ]

        sync = SyncthingWorkspaceSync(manager=syncthing_mgr)
        folder_id = await sync.push("/workspace/myproject", ["DEV1"])

        assert folder_id == "thegent-ws-myproject"
        syncthing_mgr.add_folder.assert_not_called()

    @pytest.mark.asyncio
    async def test_pull_returns_true_when_synced(self) -> None:
        """pull() returns True when completion reaches threshold."""
        syncthing_mgr = AsyncMock()
        syncthing_mgr.completion.return_value = {"completion": 100.0}

        sync = SyncthingWorkspaceSync(manager=syncthing_mgr, poll_interval_s=0.01)
        result = await sync.pull("my-folder", device_id="DEV1", timeout_s=5.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_pull_returns_false_on_timeout(self) -> None:
        """pull() returns False when sync does not complete within timeout."""
        syncthing_mgr = AsyncMock()
        # Always return incomplete
        syncthing_mgr.completion.return_value = {"completion": 50.0}

        sync = SyncthingWorkspaceSync(manager=syncthing_mgr, poll_interval_s=0.05)
        result = await sync.pull("my-folder", device_id="DEV1", timeout_s=0.2)

        assert result is False

    @pytest.mark.asyncio
    async def test_pull_uses_sync_status_when_no_device_id(self) -> None:
        """pull() uses sync_status endpoint when device_id is None."""
        syncthing_mgr = AsyncMock()
        syncthing_mgr.sync_status.return_value = {"state": "idle"}

        sync = SyncthingWorkspaceSync(manager=syncthing_mgr, poll_interval_s=0.01)
        result = await sync.pull("my-folder", timeout_s=5.0)

        assert result is True
        syncthing_mgr.sync_status.assert_called()
        syncthing_mgr.completion.assert_not_called()

    @pytest.mark.asyncio
    async def test_pull_propagates_syncthing_error(self) -> None:
        """pull() propagates SyncthingError from the API calls."""
        syncthing_mgr = AsyncMock()
        syncthing_mgr.completion.side_effect = SyncthingError("API down")

        sync = SyncthingWorkspaceSync(manager=syncthing_mgr, poll_interval_s=0.01)
        with pytest.raises(SyncthingError, match="API down"):
            await sync.pull("my-folder", device_id="DEV1", timeout_s=5.0)


# ---------------------------------------------------------------------------
# WP-5003: WatcherDaemon scale-up / scale-down
# ---------------------------------------------------------------------------


class TestWatcherDaemonScaleUp:
    """Unit tests for WatcherDaemon._check_scale_trigger (WP-5003).

    # @trace WL-050 WP-5003
    """

    @pytest.mark.asyncio
    async def test_scale_trigger_fires_when_depth_exceeds_threshold(self) -> None:
        """_check_scale_trigger calls expand(2) when depth > threshold."""
        pool_mgr = MagicMock()
        pool_mgr.expand.return_value = [_make_node("new-node")]

        # Fake queue with depth 15 > default threshold 10
        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 15

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            scale_threshold=10,
        )
        await daemon._check_scale_trigger()

        pool_mgr.expand.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_scale_trigger_does_not_fire_below_threshold(self) -> None:
        """_check_scale_trigger does NOT call expand when depth <= threshold."""
        pool_mgr = MagicMock()
        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 5

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            scale_threshold=10,
        )
        await daemon._check_scale_trigger()

        pool_mgr.expand.assert_not_called()

    @pytest.mark.asyncio
    async def test_scale_trigger_at_exact_threshold_does_not_fire(self) -> None:
        """_check_scale_trigger does not fire when depth == threshold."""
        pool_mgr = MagicMock()
        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 10

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            scale_threshold=10,
        )
        await daemon._check_scale_trigger()

        pool_mgr.expand.assert_not_called()

    @pytest.mark.asyncio
    async def test_scale_trigger_reads_prompt_queue_when_run_queue_absent(self) -> None:
        """_check_scale_trigger reads PromptQueue list_pending() when run_queue is None."""
        pool_mgr = MagicMock()
        pool_mgr.expand.return_value = []

        fake_prompt_queue = MagicMock()
        fake_prompt_queue.list_pending.return_value = ["p1"] * 12  # 12 items

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=None,
            prompt_queue=fake_prompt_queue,
            scale_threshold=10,
        )
        await daemon._check_scale_trigger()

        pool_mgr.expand.assert_called_once_with(2)


class TestWatcherDaemonScaleDown:
    """Unit tests for WatcherDaemon._check_scale_down (WP-5003).

    # @trace WL-050 WP-5003
    """

    @pytest.mark.asyncio
    async def test_scale_down_fires_when_idle_and_shallow_queue(self) -> None:
        """_check_scale_down calls shrink() when conditions are met."""
        pool_mgr = MagicMock()
        pool_mgr.shrink.return_value = ["old-node"]
        # Expose internal dict for the daemon to inspect
        pool_mgr._remote_idle_since = {"old-node": time.monotonic() - 400.0}

        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 1  # depth < scale_down_depth=2

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            scale_down_depth=2,
            idle_threshold_s=300.0,
        )
        await daemon._check_scale_down()

        pool_mgr.shrink.assert_called_once()

    @pytest.mark.asyncio
    async def test_scale_down_does_not_fire_when_queue_deep(self) -> None:
        """_check_scale_down does not call shrink() when queue depth >= scale_down_depth."""
        pool_mgr = MagicMock()
        pool_mgr._remote_idle_since = {"old-node": time.monotonic() - 400.0}

        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 5  # >= scale_down_depth=2

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            scale_down_depth=2,
            idle_threshold_s=300.0,
        )
        await daemon._check_scale_down()

        pool_mgr.shrink.assert_not_called()

    @pytest.mark.asyncio
    async def test_scale_down_does_not_fire_when_nodes_not_idle_long_enough(self) -> None:
        """_check_scale_down defers when remote nodes haven't been idle 5 minutes."""
        pool_mgr = MagicMock()
        # idle for only 60 seconds
        pool_mgr._remote_idle_since = {"node-x": time.monotonic() - 60.0}

        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 0

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            scale_down_depth=2,
            idle_threshold_s=300.0,
        )
        await daemon._check_scale_down()

        pool_mgr.shrink.assert_not_called()

    @pytest.mark.asyncio
    async def test_scale_down_does_not_fire_when_no_idle_nodes(self) -> None:
        """_check_scale_down does nothing when _remote_idle_since is empty."""
        pool_mgr = MagicMock()
        pool_mgr._remote_idle_since = {}

        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 0

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            scale_down_depth=2,
            idle_threshold_s=300.0,
        )
        await daemon._check_scale_down()

        pool_mgr.shrink.assert_not_called()


class TestWatcherDaemonLifecycle:
    """Tests for WatcherDaemon start/stop lifecycle.

    # @trace WL-050 WP-5003
    """

    @pytest.mark.asyncio
    async def test_start_creates_background_task(self) -> None:
        """start() returns a running asyncio.Task."""
        pool_mgr = MagicMock()
        pool_mgr._remote_idle_since = {}

        fake_queue = MagicMock()
        fake_queue.qsize.return_value = 0

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            run_queue=fake_queue,
            check_interval_s=9999,  # Very long interval — won't fire in test
        )
        task = daemon.start()
        assert not task.done()
        daemon.stop()
        # Allow cancellation to propagate
        await asyncio.sleep(0.01)
        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self) -> None:
        """stop() cancels the background task."""
        pool_mgr = MagicMock()
        pool_mgr._remote_idle_since = {}

        daemon = WatcherDaemon(
            pool_manager=pool_mgr,
            check_interval_s=9999,
        )
        task = daemon.start()
        daemon.stop()
        await asyncio.sleep(0.01)
        assert task.cancelled() or task.done()


# ---------------------------------------------------------------------------
# WP-5004: FederatedLoadBalancer
# ---------------------------------------------------------------------------


class TestFederatedLoadBalancer:
    """Unit tests for FederatedLoadBalancer.

    # @trace WL-050 WP-5004
    """

    def test_select_raises_when_no_nodes(self) -> None:
        """select_node raises RuntimeError when pool is empty."""
        lb = FederatedLoadBalancer()
        with pytest.raises(RuntimeError, match="no available compute nodes"):
            lb.select_node()

    def test_round_robin_without_latency(self) -> None:
        """select_node uses round-robin when nodes have no latency data."""
        nodes = [_make_node(f"node-{i}") for i in range(3)]
        lb = FederatedLoadBalancer(nodes=nodes)

        selected = [lb.select_node().node_id for _ in range(6)]
        # Should cycle through nodes in order
        assert selected == ["node-0", "node-1", "node-2", "node-0", "node-1", "node-2"]

    def test_prefers_lowest_latency_node(self) -> None:
        """select_node returns the node with the lowest EMA latency."""
        nodes = [
            _make_node("fast-node", latency=10.0),
            _make_node("slow-node", latency=200.0),
            _make_node("medium-node", latency=50.0),
        ]
        lb = FederatedLoadBalancer(nodes=nodes)

        selected = lb.select_node()
        assert selected.node_id == "fast-node"

    def test_skips_unavailable_nodes(self) -> None:
        """select_node skips nodes where is_available=False."""
        nodes = [
            _make_node("dead-node"),
            _make_node("live-node"),
        ]
        nodes[0].is_available = False
        lb = FederatedLoadBalancer(nodes=nodes)

        selected = lb.select_node()
        assert selected.node_id == "live-node"

    def test_raises_when_all_nodes_unavailable(self) -> None:
        """select_node raises RuntimeError when all nodes are unavailable."""
        nodes = [_make_node("dead")]
        nodes[0].is_available = False
        lb = FederatedLoadBalancer(nodes=nodes)

        with pytest.raises(RuntimeError, match="no available compute nodes"):
            lb.select_node()

    def test_add_node(self) -> None:
        """add_node adds a node to the balancer."""
        lb = FederatedLoadBalancer()
        lb.add_node(_make_node("new"))
        assert lb.select_node().node_id == "new"

    def test_remove_node(self) -> None:
        """remove_node removes a node from the balancer."""
        lb = FederatedLoadBalancer(nodes=[_make_node("a"), _make_node("b")])
        lb.remove_node("a")
        assert lb.select_node().node_id == "b"

    def test_set_nodes_replaces_all(self) -> None:
        """set_nodes replaces the entire node list."""
        lb = FederatedLoadBalancer(nodes=[_make_node("old")])
        lb.set_nodes([_make_node("new-1"), _make_node("new-2")])
        ids = {lb.select_node().node_id, lb.select_node().node_id}
        assert "old" not in ids


# ---------------------------------------------------------------------------
# WP-5001: ComputePoolManager submit with workspace sync
# ---------------------------------------------------------------------------


class TestComputePoolManagerSubmit:
    """Integration-style tests for ComputePoolManager.submit().

    # @trace WL-050 WP-5001 WP-5002
    """

    @pytest.mark.asyncio
    async def test_submit_uses_local_pool_when_available(self) -> None:
        """submit() delegates to local pool when it is configured."""
        local_pool = AsyncMock()
        task = _make_agent_task()
        expected = _make_agent_result(task.task_id)
        local_pool.submit.return_value = expected

        mgr = ComputePoolManager(local_worker_pool=local_pool)
        result = await mgr.submit(task)

        assert result.task_id == task.task_id
        local_pool.submit.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_submit_delegates_to_remote_when_local_fails(self) -> None:
        """submit() falls through to remote when local pool raises."""
        task = _make_agent_task()
        expected = _make_agent_result(task.task_id)

        local_pool = AsyncMock()
        local_pool.submit.side_effect = RuntimeError("saturated")

        remote_client = AsyncMock()
        remote_client.execute.return_value = expected

        node = _make_node("remote-worker")
        mgr = ComputePoolManager(local_worker_pool=local_pool)
        mgr._load_balancer.add_node(node)
        mgr._remote_clients["remote-worker"] = remote_client

        result = await mgr.submit(task)

        assert result.task_id == task.task_id
        remote_client.execute.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_submit_raises_when_no_local_or_remote(self) -> None:
        """submit() raises RuntimeError when no remote workers are available."""
        task = _make_agent_task()
        mgr = ComputePoolManager()  # No local pool, no remote nodes

        with pytest.raises(RuntimeError, match="no remote compute nodes"):
            await mgr.submit(task)

    @pytest.mark.asyncio
    async def test_submit_triggers_workspace_sync(self) -> None:
        """submit() calls workspace sync push before remote dispatch."""
        task = _make_agent_task()
        expected = _make_agent_result(task.task_id)

        remote_client = AsyncMock()
        remote_client.execute.return_value = expected

        sync = AsyncMock(spec=SyncthingWorkspaceSync)
        sync.push.return_value = "folder-id"

        node = _make_node("synced-worker")
        mgr = ComputePoolManager(workspace_sync=sync)
        mgr._load_balancer.add_node(node)
        mgr._remote_clients["synced-worker"] = remote_client

        await mgr.submit(task, local_path="/workspace/project")

        sync.push.assert_called_once_with("/workspace/project", ["synced-worker"])

    @pytest.mark.asyncio
    async def test_submit_marks_node_idle_after_completion(self) -> None:
        """submit() marks the remote node idle after task completes."""
        task = _make_agent_task()
        expected = _make_agent_result(task.task_id)

        remote_client = AsyncMock()
        remote_client.execute.return_value = expected

        node = _make_node("my-node")
        mgr = ComputePoolManager()
        mgr._load_balancer.add_node(node)
        mgr._remote_clients["my-node"] = remote_client

        await mgr.submit(task)

        assert "my-node" in mgr._remote_idle_since


# ---------------------------------------------------------------------------
# Package-level __init__ exports
# ---------------------------------------------------------------------------


class TestComputeInitExports:
    """Verify that compute/__init__.py re-exports all new WL-050 symbols.

    # @trace WL-050 WP-5001 WP-5002 WP-5004
    """

    def test_tailscale_compute_pool_exported(self) -> None:
        from thegent.compute import TailscaleComputePool as Exported

        assert Exported is TailscaleComputePool

    def test_remote_node_client_exported(self) -> None:
        from thegent.compute import RemoteNodeClient as Exported

        assert Exported is RemoteNodeClient

    def test_compute_pool_manager_exported(self) -> None:
        from thegent.compute import ComputePoolManager as Exported

        assert Exported is ComputePoolManager

    def test_federated_load_balancer_exported(self) -> None:
        from thegent.compute import FederatedLoadBalancer as Exported

        assert Exported is FederatedLoadBalancer

    def test_syncthing_workspace_sync_exported(self) -> None:
        from thegent.compute import SyncthingWorkspaceSync as Exported

        assert Exported is SyncthingWorkspaceSync

    def test_compute_node_exported(self) -> None:
        from thegent.compute import ComputeNode as Exported

        assert Exported is ComputeNode
