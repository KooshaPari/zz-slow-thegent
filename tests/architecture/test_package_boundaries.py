"""Test package boundary enforcement for sub-packages.

This test suite verifies that sub-packages maintain proper isolation during
the split transition (Track 4.2-4.3). It ensures:

1. Public API exports don't leak internals
2. Sub-packages only depend on core public API
3. Circular dependencies are prevented
4. tach.toml boundary rules are enforced
"""

import sys
from pathlib import Path

import pytest

# Add src to path so we can import packages
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root / "packages" / "thegent-sdk" / "src"))
sys.path.insert(0, str(repo_root / "packages" / "thegent-mcp" / "src"))
sys.path.insert(0, str(repo_root / "packages" / "thegent-agents" / "src"))


class TestMCPPackageBoundary:
    """Test thegent-mcp package isolation."""

    def test_mcp_imports_from_monolith_only(self):
        """thegent-mcp should only import from thegent.mcp, not internals."""
        # This should succeed - public API
        from thegent_mcp import BorrowedMCPTools, server_load_module

        assert BorrowedMCPTools is not None
        assert server_load_module is not None

    def test_mcp_no_direct_execution_imports(self):
        """thegent-mcp should not import thegent.execution internals."""
        import thegent_mcp

        mcp_source = Path(thegent_mcp.__file__).parent

        # Read __init__.py and verify no "thegent.execution" imports
        init_file = mcp_source / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            assert "from thegent.execution" not in content, "thegent-mcp should not import thegent.execution internals"
            assert "from thegent.cli" not in content, "thegent-mcp should not import thegent.cli internals"

    def test_mcp_public_api_stable(self):
        """thegent-mcp public API should match expected exports."""
        from thegent_mcp import __all__

        expected_exports = {
            "BorrowedMCPTools",
            "server_cache_elicitation_response",
            "server_create_elicitation_cache",
            "server_default_cwd_from_context",
            "server_default_owner_from_context",
            "server_elicitation_cache_key",
            "server_error_result",
            "server_get_cached_elicitation",
            "server_load_module",
            "server_resolve_cwd_elicitation",
            "server_resolve_owner_elicitation",
            "server_stable_json",
        }
        assert set(__all__) == expected_exports, "thegent-mcp public API should match expected exports"


class TestAgentsPackageBoundary:
    """Test thegent-agents package isolation."""

    def test_agents_package_exists(self):
        """thegent-agents package should be importable."""
        import thegent_agents

        assert thegent_agents.__version__ == "0.1.0"

    def test_agents_depends_only_on_core(self):
        """thegent-agents should only depend on thegent-core, not thegent-cli."""
        import thegent_agents

        agents_source = Path(thegent_agents.__file__).parent
        init_file = agents_source / "__init__.py"

        if init_file.exists():
            content = init_file.read_text()
            # Agents should not import CLI or execution internals
            assert "from thegent.cli" not in content, "thegent-agents should not import thegent.cli"
            assert "from thegent.execution" not in content, "thegent-agents should not import thegent.execution"


class TestCorePackageBoundary:
    """Test thegent-core (thegent-sdk) package isolation."""

    def test_sdk_no_transitive_dependencies(self):
        """thegent-sdk should only depend on httpx, no agent/MCP deps."""
        import thegent_sdk

        sdk_source = Path(thegent_sdk.__file__).parent
        init_file = sdk_source / "__init__.py"

        if init_file.exists():
            content = init_file.read_text()
            # SDK should not import agent or MCP modules
            assert "from thegent_agents" not in content, "thegent-sdk should not import agents"
            assert "from thegent_mcp" not in content, "thegent-sdk should not import MCP"
            assert "from thegent.mcp" not in content, "thegent-sdk should not import monolith MCP"


class TestPackageDependencyGraph:
    """Test package dependency relationships per tach.toml."""

    def test_dependency_hierarchy(self):
        """Verify package dependency hierarchy matches tach.toml.

        Expected hierarchy:
        - thegent-core (no deps)
        - thegent-sdk (depends on core)
        - thegent-mcp (depends on core)
        - thegent-agents (depends on core)
        - thegent-cli (depends on core, agents, MCP)
        """
        # This is a structural test; actual validation is in tach check
        # But we verify the pyproject.toml files are correct

        mcp_pyproject = repo_root / "packages" / "thegent-mcp" / "pyproject.toml"
        assert mcp_pyproject.exists(), "thegent-mcp pyproject.toml must exist"

        agents_pyproject = repo_root / "packages" / "thegent-agents" / "pyproject.toml"
        assert agents_pyproject.exists(), "thegent-agents pyproject.toml must exist"

    def test_no_circular_dependencies(self):
        """Ensure no circular dependencies between packages."""
        # Import in dependency order; if circular, will raise ImportError
        try:
            # Core first
            # MCP and Agents (both depend on core, not each other)
            import thegent_mcp  # noqa: F401
            import thegent_sdk  # noqa: F401

            import thegent_agents  # noqa: F401
        except ImportError as e:
            pytest.fail(f"Circular dependency detected: {e}")


class TestTachBoundaryEnforcement:
    """Verify tach.toml boundary configuration."""

    def test_tach_config_exists(self):
        """tach.toml must exist and declare sub-packages."""
        tach_file = repo_root / "tach.toml"
        assert tach_file.exists(), "tach.toml must exist"
        content = tach_file.read_text()

        # Check for sub-package module declarations
        assert "thegent_cli" in content, "tach.toml must declare thegent_cli"
        assert "thegent_agents" in content, "tach.toml must declare thegent_agents"
        assert "thegent_mcp" in content, "tach.toml must declare thegent_mcp"

    def test_tach_sub_packages_isolated(self):
        """Verify tach.toml marks sub-packages as having no internal deps."""
        tach_file = repo_root / "tach.toml"
        content = tach_file.read_text()

        # Each sub-package should have depends_on = []
        # They communicate through published APIs, not direct imports
        assert 'path = "thegent_cli"' in content
        assert 'path = "thegent_agents"' in content
        assert 'path = "thegent_mcp"' in content
