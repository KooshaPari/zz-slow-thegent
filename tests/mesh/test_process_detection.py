"""Tests for Phase 12: Process discovery, manifest, heartbeat, and stale cleanup.

Covers:
- TGNT-P12.1: /proc scanner with agent-specific patterns
- TGNT-P12.2: Agent manifest creation (YAML)
- TGNT-P12.3: Heartbeat monitor (touch-file)
- TGNT-P12.4: Stale agent cleanup
"""

from __future__ import annotations

import os
import stat
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
import yaml

from thegent.mesh.mesh import MeshManager
from thegent.mesh.process_detection import detect_agents, get_processes
from thegent.mesh.task_queue import MaildirQueue

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# TGNT-P12.1 - Process scanner / pattern matching
# ---------------------------------------------------------------------------


class TestGetProcesses:
    """Tests for get_processes() in process_detection.py."""

    # @trace TGNT-P12.1
    @patch("thegent.mesh.process_detection.platform")
    @patch("thegent.mesh.process_detection.subprocess")
    def test_darwin_ps_scan(self, mock_subprocess: MagicMock, mock_platform: MagicMock) -> None:
        """On macOS, get_processes parses ps output."""
        mock_platform.system.return_value = "Darwin"
        mock_subprocess.check_output.return_value = (
            b"  PID COMMAND\n    1 /sbin/launchd\n 1234 /usr/bin/claude-code --project foo\n 5678 cursor-agent serve\n"
        )
        mock_subprocess.STDOUT = -1
        mock_subprocess.CalledProcessError = Exception

        procs = get_processes()

        assert len(procs) == 3
        assert procs[0] == {"pid": 1, "cmd": "/sbin/launchd"}
        assert procs[1] == {"pid": 1234, "cmd": "/usr/bin/claude-code --project foo"}
        assert procs[2] == {"pid": 5678, "cmd": "cursor-agent serve"}

    # @trace TGNT-P12.1
    @patch("thegent.mesh.process_detection.platform")
    @patch("thegent.mesh.process_detection.os")
    def test_linux_proc_scan(self, mock_os: MagicMock, mock_platform: MagicMock, tmp_path: Path) -> None:
        """On Linux, get_processes reads /proc/<pid>/cmdline."""
        mock_platform.system.return_value = "Linux"
        mock_os.listdir.return_value = ["1", "42", "not_a_pid", "99"]

        # Build fake /proc cmdline data
        cmdlines = {
            "1": b"/sbin/init\x00",
            "42": b"claude-code\x00--project\x00bar",
            "99": b"",  # empty cmdline -> skipped
        }

        def fake_open(path: str, mode: str = "r") -> MagicMock:
            pid = path.split("/")[2]
            m = MagicMock()
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            m.read.return_value = cmdlines.get(pid, b"")
            return m

        import builtins

        with patch.object(builtins, "open", side_effect=fake_open):
            procs = get_processes()

        # pid=99 has empty cmdline, skipped
        assert len(procs) == 2
        assert procs[0]["pid"] == 1
        assert procs[1]["pid"] == 42
        assert "claude-code" in procs[1]["cmd"]

    # @trace TGNT-P12.1
    @patch("thegent.mesh.process_detection.platform")
    @patch("thegent.mesh.process_detection.subprocess")
    def test_darwin_ps_failure_returns_empty(self, mock_subprocess: MagicMock, mock_platform: MagicMock) -> None:
        """When ps fails, get_processes returns an empty list."""
        mock_platform.system.return_value = "Darwin"
        mock_subprocess.CalledProcessError = Exception
        mock_subprocess.STDOUT = -1
        mock_subprocess.check_output.side_effect = Exception("ps failed")

        procs = get_processes()
        assert procs == []


class TestDetectAgents:
    """Tests for detect_agents() pattern matching."""

    # @trace TGNT-P12.1
    @patch("thegent.mesh.process_detection.get_processes")
    def test_detect_claude_agent(self, mock_procs: MagicMock) -> None:
        """Detects Claude agent from process list."""
        mock_procs.return_value = [
            {"pid": 100, "cmd": "/usr/bin/claude-code --project test"},
            {"pid": 200, "cmd": "/bin/bash"},
        ]
        patterns = {"claude": r"claude-code|clode", "cursor": r"cursor-agent"}

        found = detect_agents(patterns)

        assert len(found) == 1
        assert found[0]["agent"] == "claude"
        assert found[0]["pid"] == 100

    # @trace TGNT-P12.1
    @patch("thegent.mesh.process_detection.get_processes")
    def test_detect_multiple_agent_types(self, mock_procs: MagicMock) -> None:
        """Detects multiple different agent types."""
        mock_procs.return_value = [
            {"pid": 10, "cmd": "claude-code serve"},
            {"pid": 20, "cmd": "cursor-agent --port 8080"},
            {"pid": 30, "cmd": "aider --model gpt-4"},
            {"pid": 40, "cmd": "/bin/ls"},
        ]
        patterns = {
            "claude": r"claude-code",
            "cursor": r"cursor-agent|cursor",
            "aider": r"aider",
        }

        found = detect_agents(patterns)

        agent_names = {a["agent"] for a in found}
        assert agent_names == {"claude", "cursor", "aider"}
        assert len(found) == 3

    # @trace TGNT-P12.1
    @patch("thegent.mesh.process_detection.get_processes")
    def test_detect_case_insensitive(self, mock_procs: MagicMock) -> None:
        """Pattern matching is case-insensitive."""
        mock_procs.return_value = [
            {"pid": 50, "cmd": "CLAUDE-CODE --debug"},
        ]
        patterns = {"claude": r"claude-code"}

        found = detect_agents(patterns)
        assert len(found) == 1
        assert found[0]["agent"] == "claude"

    # @trace TGNT-P12.1
    @patch("thegent.mesh.process_detection.get_processes")
    def test_no_agents_detected(self, mock_procs: MagicMock) -> None:
        """Returns empty list when no agent patterns match."""
        mock_procs.return_value = [
            {"pid": 1, "cmd": "/sbin/init"},
            {"pid": 2, "cmd": "/usr/sbin/sshd"},
        ]
        patterns = {"claude": r"claude-code", "cursor": r"cursor-agent"}

        found = detect_agents(patterns)
        assert found == []

    # @trace SCLI-P1.2
    @patch("thegent.mesh.process_detection.get_processes")
    def test_invalid_regex_raises_value_error(self, mock_procs: MagicMock) -> None:
        """Invalid pattern config fails loudly with agent key context."""
        mock_procs.return_value = [{"pid": 1, "cmd": "claude-code"}]
        patterns = {"claude": r"[unterminated"}

        with pytest.raises(ValueError, match="claude"):
            detect_agents(patterns)


# ---------------------------------------------------------------------------
# TGNT-P12.1 - MeshManager.discover_agents (psutil-based)
# ---------------------------------------------------------------------------


class TestMeshManagerDiscoverAgents:
    """Tests for MeshManager.discover_agents using psutil."""

    # @trace TGNT-P12.1
    @patch("thegent.mesh.mesh.psutil.process_iter")
    def test_discover_agents_matches_patterns(self, mock_iter: MagicMock, tmp_path: Path) -> None:
        """discover_agents finds processes matching patterns."""
        proc1 = MagicMock()
        proc1.info = {"pid": 111, "name": "node", "cmdline": ["claude-code", "--project", "x"]}
        proc2 = MagicMock()
        proc2.info = {"pid": 222, "name": "bash", "cmdline": ["/bin/bash"]}
        mock_iter.return_value = [proc1, proc2]

        mgr = MeshManager(mesh_root=tmp_path / "mesh")
        found = mgr.discover_agents(["claude-code"])

        assert len(found) == 1
        assert found[0]["pid"] == 111


# ---------------------------------------------------------------------------
# TGNT-P12.2 - Agent manifest creation (YAML)
# ---------------------------------------------------------------------------


class TestManifest:
    """Tests for agent manifest creation."""

    # @trace TGNT-P12.2
    def test_register_agent_creates_yaml(self, tmp_path: Path) -> None:
        """register_agent writes a valid YAML manifest."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")

        mgr.register_agent("agent-001", {"type": "claude", "pid": 1234, "capabilities": ["code", "test"]})

        manifest_path = mgr.agents_dir / "agent-001.yaml"
        assert manifest_path.exists()

        data = yaml.safe_load(manifest_path.read_text())
        assert data["id"] == "agent-001"
        assert data["type"] == "claude"
        assert data["pid"] == 1234
        assert data["capabilities"] == ["code", "test"]
        assert "registered_at" in data

    # @trace TGNT-P12.2
    def test_register_agent_with_status_and_odd(self, tmp_path: Path) -> None:
        """Manifest includes status and ODD (operational design domain)."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")

        mgr.register_agent(
            "agent-002",
            {
                "type": "cursor",
                "pid": 5678,
                "capabilities": ["edit"],
                "odd": "backend-only",
                "status": "active",
            },
        )

        manifest_path = mgr.agents_dir / "agent-002.yaml"
        data = yaml.safe_load(manifest_path.read_text())
        assert data["odd"] == "backend-only"
        assert data["status"] == "active"

    # @trace TGNT-P12.2
    def test_register_agent_overwrites_existing(self, tmp_path: Path) -> None:
        """Re-registering an agent overwrites its manifest."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")

        mgr.register_agent("agent-003", {"type": "codex", "pid": 100})
        mgr.register_agent("agent-003", {"type": "codex", "pid": 200})

        data = yaml.safe_load((mgr.agents_dir / "agent-003.yaml").read_text())
        assert data["pid"] == 200


class TestMeshInit:
    """SCLI-P1.4 mesh directory initialization contract."""

    # @trace SCLI-P1.4
    def test_mesh_init_creates_required_directories(self, tmp_path: Path) -> None:
        mgr = MeshManager(mesh_root=tmp_path / "mesh")
        assert mgr.agents_dir.is_dir()
        assert mgr.queue_dir.is_dir()
        assert mgr.tasks_dir.is_dir()
        assert mgr.intents_dir.is_dir()
        assert mgr.locks_dir.is_dir()
        assert mgr.metrics_dir.is_dir()

    # @trace SCLI-P1.4
    def test_mesh_init_sets_sticky_bit_on_shared_dirs(self, tmp_path: Path) -> None:
        mgr = MeshManager(mesh_root=tmp_path / "mesh")
        queue_mode = mgr.queue_dir.stat().st_mode
        locks_mode = mgr.locks_dir.stat().st_mode
        assert queue_mode & stat.S_ISVTX
        assert locks_mode & stat.S_ISVTX


# ---------------------------------------------------------------------------
# TGNT-P12.3 - Heartbeat monitor
# ---------------------------------------------------------------------------


class TestHeartbeat:
    """Tests for heartbeat touch-file mechanism."""

    # @trace TGNT-P12.3
    def test_heartbeat_creates_file(self, tmp_path: Path) -> None:
        """heartbeat() creates a .heartbeat file."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")

        mgr.heartbeat("agent-hb1")

        hb_path = mgr.agents_dir / "agent-hb1.heartbeat"
        assert hb_path.exists()

    # @trace TGNT-P12.3
    def test_heartbeat_updates_mtime(self, tmp_path: Path) -> None:
        """Successive heartbeat() calls update the file mtime."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")

        mgr.heartbeat("agent-hb2")
        hb_path = mgr.agents_dir / "agent-hb2.heartbeat"
        mtime1 = hb_path.stat().st_mtime

        # Ensure measurable time difference
        time.sleep(0.05)
        mgr.heartbeat("agent-hb2")
        mtime2 = hb_path.stat().st_mtime

        assert mtime2 >= mtime1


# ---------------------------------------------------------------------------
# TGNT-P12.4 - Stale agent cleanup
# ---------------------------------------------------------------------------


class TestStaleCleanup:
    """Tests for stale agent cleanup."""

    # @trace TGNT-P12.4
    def test_cleanup_removes_stale_agent(self, tmp_path: Path) -> None:
        """cleanup_stale removes agents whose heartbeat exceeds threshold."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")

        # Register and heartbeat
        mgr.register_agent("stale-001", {"type": "claude", "pid": 999})
        mgr.heartbeat("stale-001")

        # Backdate the heartbeat file by 20 seconds
        hb_path = mgr.agents_dir / "stale-001.heartbeat"
        old_time = time.time() - 20
        import os

        os.utime(hb_path, (old_time, old_time))

        mgr.cleanup_stale(threshold=15)

        assert not hb_path.exists()
        assert not (mgr.agents_dir / "stale-001.yaml").exists()

    # @trace TGNT-P12.4
    def test_cleanup_keeps_fresh_agent(self, tmp_path: Path) -> None:
        """cleanup_stale does NOT remove agents with recent heartbeats."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")

        mgr.register_agent("fresh-001", {"type": "cursor", "pid": 888})
        mgr.heartbeat("fresh-001")

        mgr.cleanup_stale(threshold=15)

        assert (mgr.agents_dir / "fresh-001.heartbeat").exists()
        assert (mgr.agents_dir / "fresh-001.yaml").exists()

    # @trace TGNT-P12.4
    def test_cleanup_mixed_stale_and_fresh(self, tmp_path: Path) -> None:
        """Only stale agents are cleaned up; fresh ones survive."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")
        import os

        # Stale agent
        mgr.register_agent("old-agent", {"type": "codex", "pid": 1})
        mgr.heartbeat("old-agent")
        old_hb = mgr.agents_dir / "old-agent.heartbeat"
        old_time = time.time() - 30
        os.utime(old_hb, (old_time, old_time))

        # Fresh agent
        mgr.register_agent("new-agent", {"type": "claude", "pid": 2})
        mgr.heartbeat("new-agent")

        mgr.cleanup_stale(threshold=15)

        # Stale removed
        assert not old_hb.exists()
        assert not (mgr.agents_dir / "old-agent.yaml").exists()

        # Fresh kept
        assert (mgr.agents_dir / "new-agent.heartbeat").exists()
        assert (mgr.agents_dir / "new-agent.yaml").exists()

    # @trace TGNT-P12.4
    def test_cleanup_heartbeat_without_manifest(self, tmp_path: Path) -> None:
        """cleanup_stale handles stale heartbeat with no manifest gracefully."""
        mgr = MeshManager(mesh_root=tmp_path / "mesh")
        import os

        # Create heartbeat but no manifest
        hb_path = mgr.agents_dir / "orphan.heartbeat"
        hb_path.touch()
        old_time = time.time() - 30
        os.utime(hb_path, (old_time, old_time))

        # Should not raise
        mgr.cleanup_stale(threshold=15)
        assert not hb_path.exists()

    # @trace TGNT-P12.4
    def test_cleanup_reclaims_stale_agent_tasks(self, tmp_path: Path) -> None:
        """cleanup_stale moves in-flight tasks owned by stale agents back to new/."""
        mesh_root = tmp_path / "mesh"
        mgr = MeshManager(mesh_root=mesh_root)
        queue = MaildirQueue(mesh_root / "queue")

        queue.enqueue({"work": "stale-agent-task"})
        stale_task = queue.dequeue(owner="stale-agent")
        assert stale_task is not None

        queue.enqueue({"work": "other-agent-task"})
        active_task = queue.dequeue(owner="active-agent")
        assert active_task is not None

        mgr.register_agent("stale-agent", {"type": "claude", "pid": 123})
        mgr.register_agent("active-agent", {"type": "claude", "pid": 456})
        mgr.heartbeat("stale-agent")
        mgr.heartbeat("active-agent")

        stale_hb = mgr.agents_dir / "stale-agent.heartbeat"
        active_hb = mgr.agents_dir / "active-agent.heartbeat"
        old_time = time.time() - 30
        os.utime(stale_hb, (old_time, old_time))
        fresh_time = time.time()
        os.utime(active_hb, (fresh_time, fresh_time))

        reclaimed = mgr.cleanup_stale(threshold=15)
        assert reclaimed == 1
        assert (queue._new / stale_task["id"]).exists()
        assert not (queue._cur / stale_task["id"]).exists()
        assert (queue._cur / active_task["id"]).exists()
