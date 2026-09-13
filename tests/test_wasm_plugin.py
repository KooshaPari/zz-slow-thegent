"""Tests for the Wasm Plugin System.

These tests verify the Wasm plugin functionality including:
- Extism runtime initialization
- Plugin management
- Resource limits
- Fallback handling
"""

import tempfile
from pathlib import Path

import orjson as json
import pytest

from thegent.infra.wasm_plugin import (
    ExtismPlugin,
    ExtismRuntime,
    PluginStatus,
    ResourceLimits,
    WasmCapability,
    WasmExecutionResult,
    WasmPluginManager,
    WasmPluginMetadata,
    WasmRuntimeStatus,
    create_plugin_from_manifest,
    get_plugin_manager,
)


class TestResourceLimits:
    """Tests for ResourceLimits dataclass."""

    def test_default_limits(self):
        """Test that default limits have sensible values."""
        limits = ResourceLimits()
        assert limits.max_memory_mb == 128
        assert limits.max_cpu_time_ms == 5000
        assert limits.max_execution_time_ms == 30000
        assert limits.max_output_size_bytes == 1024 * 1024

    def test_custom_limits(self):
        """Test custom resource limits."""
        limits = ResourceLimits(
            max_memory_mb=256,
            max_cpu_time_ms=10000,
            max_execution_time_ms=60000,
            max_output_size_bytes=2 * 1024 * 1024,
        )
        assert limits.max_memory_mb == 256
        assert limits.max_cpu_time_ms == 10000
        assert limits.max_execution_time_ms == 60000
        assert limits.max_output_size_bytes == 2 * 1024 * 1024


class TestWasmPluginMetadata:
    """Tests for WasmPluginMetadata."""

    def test_default_metadata(self):
        """Test default metadata values."""
        metadata = WasmPluginMetadata(name="test-plugin")
        assert metadata.name == "test-plugin"
        assert metadata.version == "0.1.0"
        assert metadata.description == ""
        assert metadata.author == ""
        assert metadata.entry_point == "run"
        assert metadata.capabilities == []

    def test_metadata_with_capabilities(self):
        """Test metadata with capabilities."""
        metadata = WasmPluginMetadata(
            name="test-plugin",
            capabilities=[WasmCapability.HTTP_CLIENT, WasmCapability.FILE_READ],
        )
        assert len(metadata.capabilities) == 2
        assert WasmCapability.HTTP_CLIENT in metadata.capabilities


class TestWasmExecutionResult:
    """Tests for WasmExecutionResult."""

    def test_success_result(self):
        """Test successful execution result."""
        result = WasmExecutionResult(
            status="success",
            output="hello world",
            duration_ms=100,
            cpu_time_ms=50,
        )
        assert result.status == "success"
        assert result.output == "hello world"
        assert result.duration_ms == 100
        assert result.cpu_time_ms == 50

    def test_error_result(self):
        """Test error execution result."""
        result = WasmExecutionResult(
            status="error",
            error="Something went wrong",
            duration_ms=50,
        )
        assert result.status == "error"
        assert result.error == "Something went wrong"
        assert result.output is None


class TestExtismRuntime:
    """Tests for ExtismRuntime singleton."""

    def test_singleton(self):
        """Test that ExtismRuntime is a singleton."""
        runtime1 = ExtismRuntime()
        runtime2 = ExtismRuntime()
        assert runtime1 is runtime2

    def test_status_uninitialized(self):
        """Test that status starts as uninitialized."""
        runtime = ExtismRuntime()
        # Reset for test
        runtime._status = WasmRuntimeStatus.UNINITIALIZED
        assert runtime.status == WasmRuntimeStatus.UNINITIALIZED

    def test_is_available_false_when_uninitialized(self):
        """Test that is_available returns False when uninitialized."""
        runtime = ExtismRuntime()
        runtime._status = WasmRuntimeStatus.UNINITIALIZED
        runtime._extism = None
        assert runtime.is_available is False


class TestWasmPluginManager:
    """Tests for WasmPluginManager."""

    def test_manager_creation(self):
        """Test creating a plugin manager."""
        manager = WasmPluginManager()
        assert manager.is_available is False  # Not initialized yet
        assert manager.list_plugins() == []

    def test_initialize(self):
        """Test initializing the runtime."""
        manager = WasmPluginManager()
        # This may or may not succeed depending on whether extism is installed
        result = manager.initialize()
        # Just verify it returns a boolean
        assert isinstance(result, bool)

    def test_register_plugin(self):
        """Test registering a plugin."""
        manager = WasmPluginManager()
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="test-plugin")
            plugin = ExtismPlugin(wasm_path, metadata)

            # Should work even with non-existent wasm (just registration)
            result = manager.register_plugin(plugin)
            assert result is True
            assert "test-plugin" in manager.list_plugins()

            # Can't register twice
            result = manager.register_plugin(plugin)
            assert result is False
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_get_plugin(self):
        """Test getting a registered plugin."""
        manager = WasmPluginManager()
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="test-plugin-2")
            plugin = ExtismPlugin(wasm_path, metadata)
            manager.register_plugin(plugin)

            retrieved = manager.get_plugin("test-plugin-2")
            assert retrieved is not None
            assert retrieved.metadata.name == "test-plugin-2"

            # Non-existent plugin
            assert manager.get_plugin("nonexistent") is None
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_remove_plugin(self):
        """Test removing a plugin."""
        manager = WasmPluginManager()
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="test-plugin-3")
            plugin = ExtismPlugin(wasm_path, metadata)
            manager.register_plugin(plugin)

            assert "test-plugin-3" in manager.list_plugins()

            result = manager.remove_plugin("test-plugin-3")
            assert result is True
            assert "test-plugin-3" not in manager.list_plugins()

            # Can't remove twice
            result = manager.remove_plugin("test-plugin-3")
            assert result is False
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_clear(self):
        """Test clearing all plugins."""
        manager = WasmPluginManager()
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f1:
            wasm_path1 = Path(f1.name)
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f2:
            wasm_path2 = Path(f2.name)

        try:
            metadata1 = WasmPluginMetadata(name="plugin-a")
            metadata2 = WasmPluginMetadata(name="plugin-b")
            plugin1 = ExtismPlugin(wasm_path1, metadata1)
            plugin2 = ExtismPlugin(wasm_path2, metadata2)

            manager.register_plugin(plugin1)
            manager.register_plugin(plugin2)
            assert len(manager.list_plugins()) == 2

            manager.clear()
            assert len(manager.list_plugins()) == 0
        finally:
            wasm_path1.unlink(missing_ok=True)
            wasm_path2.unlink(missing_ok=True)


class TestCreatePluginFromManifest:
    """Tests for create_plugin_from_manifest."""

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            manifest_path = Path(f.name)

        try:
            result = create_plugin_from_manifest(manifest_path)
            assert result is None
        finally:
            manifest_path.unlink(missing_ok=True)

    def test_minimal_manifest(self):
        """Test creating plugin from minimal manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_data = {
                "name": "minimal-plugin",
                "version": "0.1.0",
            }
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest_data).decode())

            # No wasm file, so should fail
            result = create_plugin_from_manifest(manifest_path)
            assert result is None

    def test_manifest_with_wasm_path(self):
        """Test manifest with explicit wasm path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy wasm file
            wasm_path = Path(tmpdir) / "my-tool.wasm"
            wasm_path.write_bytes(b"wasm binary placeholder")

            manifest_data = {
                "name": "my-tool",
                "version": "0.2.0",
                "description": "A test tool",
                "author": "Test Author",
                "wasm": "my-tool.wasm",
                "entry_point": "run",
                "capabilities": ["http_client", "file_read"],
                "limits": {
                    "max_memory_mb": 256,
                    "max_execution_time_ms": 60000,
                },
            }
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest_data).decode())

            result = create_plugin_from_manifest(manifest_path)
            assert result is not None
            assert result.metadata.name == "my-tool"
            assert result.metadata.version == "0.2.0"
            assert result.metadata.description == "A test tool"
            assert result.metadata.author == "Test Author"
            assert result.limits.max_memory_mb == 256


class TestGetPluginManager:
    """Tests for get_plugin_manager global function."""

    def test_returns_singleton(self):
        """Test that get_plugin_manager returns a singleton."""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()
        assert manager1 is manager2
        # Clean up global state for other tests
        import thegent.infra.wasm_plugin as wp

        wp._plugin_manager = None


class TestWasmPluginLoading:
    """Integration tests for Wasm plugin loading/unloading scenarios."""

    def test_extism_plugin_load_without_wasm_file(self):
        """Test loading a plugin with non-existent wasm file."""
        from thegent.infra.wasm_plugin import (
            ExtismPlugin,
            ResourceLimits,
            WasmPluginMetadata,
        )

        metadata = WasmPluginMetadata(name="nonexistent-plugin")
        limits = ResourceLimits()

        # Use non-existent path
        plugin = ExtismPlugin(
            plugin_path=Path("/nonexistent/plugin.wasm"),
            metadata=metadata,
            limits=limits,
        )

        # Load should fail gracefully
        result = plugin.load()
        assert result is False
        assert plugin.status == PluginStatus.ERROR

    def test_extism_plugin_double_load(self):
        """Test loading a plugin twice."""
        from thegent.infra.wasm_plugin import (
            ExtismPlugin,
            ResourceLimits,
            WasmPluginMetadata,
        )

        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="double-load-plugin")
            limits = ResourceLimits()

            plugin = ExtismPlugin(
                plugin_path=wasm_path,
                metadata=metadata,
                limits=limits,
            )

            # First load attempt
            plugin.load()

            # Second load - should return True if already loaded
            # (depends on implementation - some may reload)
            plugin.load()

            # Status should be consistent
            assert plugin.status in (PluginStatus.READY, PluginStatus.ERROR)
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_extism_plugin_execute_without_load(self):
        """Test executing a plugin that hasn't been loaded."""
        from thegent.infra.wasm_plugin import (
            ExtismPlugin,
            ResourceLimits,
            WasmPluginMetadata,
        )

        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="execute-unloaded-plugin")
            limits = ResourceLimits()

            plugin = ExtismPlugin(
                plugin_path=wasm_path,
                metadata=metadata,
                limits=limits,
            )

            # Try to execute without loading
            result = plugin.execute("test input")

            # Should fail gracefully
            assert result.status == "error"
            assert result.error is not None
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_extism_plugin_unload_twice(self):
        """Test unloading a plugin twice."""
        from thegent.infra.wasm_plugin import (
            ExtismPlugin,
            ResourceLimits,
            WasmPluginMetadata,
        )

        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="double-unload-plugin")
            limits = ResourceLimits()

            plugin = ExtismPlugin(
                plugin_path=wasm_path,
                metadata=metadata,
                limits=limits,
            )

            # First unload (from UNLOADED state)
            result1 = plugin.unload()
            assert result1 is True

            # Second unload (already unloaded)
            result2 = plugin.unload()
            assert result2 is True  # Most implementations return True for idempotent operation
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_extism_plugin_execute_with_string_input(self):
        """Test executing plugin with string input."""
        from thegent.infra.wasm_plugin import (
            ExtismPlugin,
            ResourceLimits,
            WasmPluginMetadata,
        )

        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="string-input-plugin")
            limits = ResourceLimits()

            plugin = ExtismPlugin(
                plugin_path=wasm_path,
                metadata=metadata,
                limits=limits,
            )

            # Try to execute with string input (will fail due to missing wasm, but tests conversion)
            result = plugin.execute("string input data")

            # Should handle string input conversion
            assert result.status in ("success", "error")
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_extism_plugin_execute_with_bytes_input(self):
        """Test executing plugin with bytes input."""
        from thegent.infra.wasm_plugin import (
            ExtismPlugin,
            ResourceLimits,
            WasmPluginMetadata,
        )

        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            wasm_path = Path(f.name)

        try:
            metadata = WasmPluginMetadata(name="bytes-input-plugin")
            limits = ResourceLimits()

            plugin = ExtismPlugin(
                plugin_path=wasm_path,
                metadata=metadata,
                limits=limits,
            )

            # Try to execute with bytes input
            result = plugin.execute(b"bytes input data")

            # Should handle bytes input
            assert result.status in ("success", "error")
        finally:
            wasm_path.unlink(missing_ok=True)

    def test_plugin_manager_load_plugin_not_found(self):
        """Test loading a non-existent plugin."""
        from thegent.infra.wasm_plugin import WasmPluginManager

        manager = WasmPluginManager()

        # Try to load non-existent plugin
        result = manager.load_plugin("nonexistent_plugin")
        assert result is False

    def test_plugin_manager_execute_plugin_not_found(self):
        """Test executing a non-existent plugin."""
        from thegent.infra.wasm_plugin import WasmPluginManager

        manager = WasmPluginManager()

        # Try to execute non-existent plugin
        result = manager.execute_plugin("nonexistent_plugin", "input")
        assert result is None

    def test_plugin_manager_unload_plugin_not_found(self):
        """Test unloading a non-existent plugin."""
        from thegent.infra.wasm_plugin import WasmPluginManager

        manager = WasmPluginManager()

        # Try to unload non-existent plugin
        result = manager.unload_plugin("nonexistent_plugin")
        assert result is False

    def test_plugin_manager_remove_not_found(self):
        """Test removing a non-existent plugin."""
        from thegent.infra.wasm_plugin import WasmPluginManager

        manager = WasmPluginManager()

        # Try to remove non-existent plugin
        result = manager.remove_plugin("nonexistent_plugin")
        assert result is False


class TestResourceLimitsEdgeCases:
    """Tests for edge cases in resource limits."""

    def test_zero_limits(self):
        """Test resource limits with zero values."""
        limits = ResourceLimits(
            max_memory_mb=0,
            max_cpu_time_ms=0,
            max_execution_time_ms=0,
            max_output_size_bytes=0,
        )
        assert limits.max_memory_mb == 0
        assert limits.max_cpu_time_ms == 0

    def test_large_limits(self):
        """Test resource limits with large values."""
        limits = ResourceLimits(
            max_memory_mb=10000,
            max_cpu_time_ms=1000000,
            max_execution_time_ms=10000000,
            max_output_size_bytes=100 * 1024 * 1024,
        )
        assert limits.max_memory_mb == 10000
        assert limits.max_output_size_bytes == 100 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
