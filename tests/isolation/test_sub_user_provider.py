"""Tests for SubUserIsolationProvider."""

import os
import tempfile

import pytest

from thegent.isolation.exceptions import ExecutionContextError
from thegent.isolation.sub_user_provider import SubUserIsolationProvider


@pytest.fixture
def temp_base_dir():
    """Temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def provider(temp_base_dir):
    """Create a SubUserIsolationProvider for testing."""
    return SubUserIsolationProvider(base_home_dir=temp_base_dir)


class TestAllocation:
    """Test tenant allocation."""

    def test_allocate_tenant_creates_context(self, provider):
        """Allocation creates a valid TenantContext."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        assert ctx.tenant_id == "test-tenant-1"
        assert ctx.agent_id == "agent-1"
        assert ctx.uid is not None
        assert ctx.gid is not None
        assert ctx.home_dir is not None

    def test_allocate_tenant_idempotent(self, provider):
        """Same tenant ID returns same context."""
        ctx1 = provider.allocate_tenant("test-tenant-1", "agent-1")
        ctx2 = provider.allocate_tenant("test-tenant-1", "agent-1")
        assert ctx1.uid == ctx2.uid
        assert ctx1.gid == ctx2.gid
        assert ctx1.home_dir == ctx2.home_dir

    def test_multiple_tenants_different_uids(self, provider):
        """Different tenants get different UIDs."""
        ctx1 = provider.allocate_tenant("tenant-1", "agent-1")
        ctx2 = provider.allocate_tenant("tenant-2", "agent-1")
        # UIDs should be different
        assert ctx1.uid != ctx2.uid

    def test_allocate_creates_home_directory(self, provider, temp_base_dir):
        """Home directory is created during allocation."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        assert os.path.isdir(ctx.home_dir)
        assert ctx.home_dir.startswith(temp_base_dir)


class TestExecution:
    """Test command execution in tenant context."""

    def test_execute_simple_command(self, provider):
        """Simple command executes successfully."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        result = provider.execute_in_context(ctx, ["echo", "hello"])
        assert result["returncode"] == 0
        assert "hello" in result["stdout"]

    def test_execute_sets_env_vars(self, provider):
        """Environment variables are set during execution."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        # Execute command that prints env var
        result = provider.execute_in_context(ctx, ["sh", "-c", "echo $THEGENT_TENANT_ID"])
        assert result["returncode"] == 0
        assert "test-tenant-1" in result["stdout"]

    def test_execute_with_timeout(self, provider):
        """Command timeout is enforced."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        with pytest.raises(ExecutionContextError):
            provider.execute_in_context(ctx, ["sleep", "100"], timeout_sec=1)

    def test_execute_error_handling(self, provider):
        """Command errors are captured."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        result = provider.execute_in_context(ctx, ["sh", "-c", "exit 42"])
        assert result["returncode"] == 42


class TestCleanup:
    """Test tenant cleanup."""

    def test_cleanup_releases_context(self, provider, temp_base_dir):
        """Cleanup removes allocated resources."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        home_dir = ctx.home_dir
        assert os.path.isdir(home_dir)

        provider.cleanup_tenant(ctx)
        # Home dir should be cleaned up
        assert not os.path.exists(home_dir)

    def test_cleanup_idempotent(self, provider):
        """Cleanup can be called multiple times."""
        ctx = provider.allocate_tenant("test-tenant-1", "agent-1")
        provider.cleanup_tenant(ctx)
        # Should not raise
        provider.cleanup_tenant(ctx)
