"""Tests for ResourceIsolation (Phase 10 — per-agent resource isolation).

# @trace TGNT-P10.1 TMPDIR allocation
# @trace TGNT-P10.2 Dynamic port allocation
# @trace TGNT-P10.3 Environment variable isolation
"""

import socket
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.mesh.isolation import ResourceIsolation

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def isolation(tmp_path: Path) -> ResourceIsolation:
    """A fresh ResourceIsolation instance backed by a temporary directory."""
    return ResourceIsolation(mesh_root=tmp_path, agent_id="agent-001")


# ---------------------------------------------------------------------------
# 1. Per-agent TMPDIR allocation  (TGNT-P10.1)
# ---------------------------------------------------------------------------


class TestAllocateTmpdir:
    """allocate_tmpdir() creates a private, agent-scoped temporary directory."""

    # @trace TGNT-P10.1
    def test_tmpdir_created_with_correct_path(self, isolation: ResourceIsolation, tmp_path: Path) -> None:
        """TMPDIR is created at mesh_root/tmp/<agent_id>."""
        result = isolation.allocate_tmpdir()
        expected = tmp_path / "tmp" / "agent-001"
        assert result == expected
        assert result.is_dir()

    # @trace TGNT-P10.1
    def test_tmpdir_has_restricted_permissions(self, isolation: ResourceIsolation) -> None:
        """TMPDIR is created with mode 0o700 (owner-only access)."""
        result = isolation.allocate_tmpdir()
        mode = result.stat().st_mode & 0o777
        assert mode == 0o700

    # @trace TGNT-P10.1
    def test_tmpdir_cleaned_on_reallocation(self, isolation: ResourceIsolation) -> None:
        """Re-calling allocate_tmpdir() removes prior contents."""
        first = isolation.allocate_tmpdir()
        sentinel = first / "stale_file.txt"
        sentinel.write_text("old data")

        second = isolation.allocate_tmpdir()
        assert second == first
        assert not sentinel.exists()

    # @trace TGNT-P10.1
    def test_cleanup_removes_tmpdir(self, isolation: ResourceIsolation) -> None:
        """cleanup() removes the agent TMPDIR entirely."""
        tmpdir = isolation.allocate_tmpdir()
        assert tmpdir.exists()

        isolation.cleanup()
        assert not tmpdir.exists()

    # @trace TGNT-P10.1
    def test_cleanup_idempotent_when_no_tmpdir(self, isolation: ResourceIsolation) -> None:
        """cleanup() does not raise when TMPDIR was never created."""
        isolation.cleanup()  # must not raise


# ---------------------------------------------------------------------------
# 2. Dynamic port allocation  (TGNT-P10.2)
# ---------------------------------------------------------------------------


class TestAllocatePort:
    """allocate_port() finds an available TCP port via socket binding."""

    # @trace TGNT-P10.2
    def test_returns_port_in_range(self, isolation: ResourceIsolation) -> None:
        """Allocated port is within the requested range."""
        port = isolation.allocate_port(start_port=10000, end_port=20000)
        assert port is not None
        assert 10000 <= port < 20000

    # @trace TGNT-P10.2
    def test_returns_none_when_no_ports_available(self, isolation: ResourceIsolation) -> None:
        """Returns None when all ports in the range are occupied."""

        def always_raise(*_args, **_kwargs):
            raise OSError("port in use")

        with patch.object(socket.socket, "bind", side_effect=always_raise):
            result = isolation.allocate_port(start_port=10000, end_port=10003)
            assert result is None

    # @trace TGNT-P10.2
    def test_skips_occupied_ports(self, isolation: ResourceIsolation) -> None:
        """Skips ports that raise OSError and returns the first available one."""
        call_count = 0
        original_bind = socket.socket.bind

        def bind_fail_first_two(self_sock, addr):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise OSError("port in use")
            return original_bind(self_sock, addr)

        with patch.object(socket.socket, "bind", bind_fail_first_two):
            port = isolation.allocate_port(start_port=10000, end_port=10010)
            assert port == 10002
            assert call_count >= 3


# ---------------------------------------------------------------------------
# 3. Environment variable isolation  (TGNT-P10.3)
# ---------------------------------------------------------------------------


class TestGetIsolatedEnv:
    """get_isolated_env() returns agent-scoped environment variables."""

    # @trace TGNT-P10.3
    def test_sets_tmpdir_variants(self, isolation: ResourceIsolation) -> None:
        """All temp-dir env vars point to the agent's private TMPDIR."""
        env = isolation.get_isolated_env(base_env={})
        agent_tmp = str(isolation.agent_tmp)
        assert env["TMPDIR"] == agent_tmp
        assert env["TEMP"] == agent_tmp
        assert env["TMP"] == agent_tmp
        assert env["PYTHONTEMP"] == agent_tmp

    # @trace TGNT-P10.3
    def test_sets_agent_identity_vars(self, isolation: ResourceIsolation, tmp_path: Path) -> None:
        """AGENT_ID and MESH_ROOT are set correctly."""
        env = isolation.get_isolated_env(base_env={})
        assert env["AGENT_ID"] == "agent-001"
        assert env["MESH_ROOT"] == str(tmp_path)

    # @trace TGNT-P10.3
    def test_preserves_base_env(self, isolation: ResourceIsolation) -> None:
        """Base environment variables are carried through."""
        base = {"HOME": "/home/user", "PATH": "/usr/bin"}
        env = isolation.get_isolated_env(base_env=base)
        assert env["HOME"] == "/home/user"
        assert env["PATH"] == "/usr/bin"

    # @trace TGNT-P10.3
    def test_does_not_mutate_base_env(self, isolation: ResourceIsolation) -> None:
        """The original base_env dict is not modified."""
        base = {"HOME": "/home/user"}
        isolation.get_isolated_env(base_env=base)
        assert "AGENT_ID" not in base

    # @trace TGNT-P10.3
    def test_defaults_to_os_environ(self, isolation: ResourceIsolation) -> None:
        """When base_env is None, os.environ is used as the base."""
        env = isolation.get_isolated_env(base_env=None)
        # Should contain at least the agent-specific keys
        assert env["AGENT_ID"] == "agent-001"
        # Should also contain real env vars (PATH always exists)
        assert "PATH" in env

    # @trace TGNT-P10.3
    def test_two_agents_have_different_envs(self, tmp_path: Path) -> None:
        """Two ResourceIsolation instances produce distinct env scopes."""
        iso_a = ResourceIsolation(mesh_root=tmp_path, agent_id="agent-a")
        iso_b = ResourceIsolation(mesh_root=tmp_path, agent_id="agent-b")

        env_a = iso_a.get_isolated_env(base_env={})
        env_b = iso_b.get_isolated_env(base_env={})

        assert env_a["AGENT_ID"] != env_b["AGENT_ID"]
        assert env_a["TMPDIR"] != env_b["TMPDIR"]
