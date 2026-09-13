"""Tests for the Wasm Sandbox enhancements.

These tests verify:
- Sandbox configuration
- Resource usage tracking
- Timeout handling
- Fallback mechanism
- Support detection
"""


import pytest

from thegent.infra.sandbox import (
    ResourceUsage,
    SandboxConfig,
    SandboxFeature,
    SandboxStatus,
    WasmSandbox,
    check_wasm_support,
    create_sandboxed_executor,
)


class TestSandboxConfig:
    """Tests for SandboxConfig."""

    def test_default_config(self):
        """Test default sandbox configuration."""
        config = SandboxConfig()
        assert config.max_memory_mb == 128
        assert config.allow_network is False
        assert config.allow_filesystem is False
        assert config.timeout_ms == 30000
        assert config.enable_wasi is True
        assert config.allowed_paths == []

    def test_custom_config(self):
        """Test custom sandbox configuration."""
        config = SandboxConfig(
            max_memory_mb=256,
            allow_network=True,
            allow_filesystem=True,
            timeout_ms=60000,
            enable_wasi=False,
            allowed_paths=["/tmp", "/var/tmp"],
            env_vars={"MY_VAR": "value"},
        )
        assert config.max_memory_mb == 256
        assert config.allow_network is True
        assert config.allow_filesystem is True
        assert config.timeout_ms == 60000
        assert config.enable_wasi is False
        assert config.allowed_paths == ["/tmp", "/var/tmp"]
        assert config.env_vars["MY_VAR"] == "value"


class TestSandboxStatus:
    """Tests for SandboxStatus enum."""

    def test_status_values(self):
        """Test that all expected status values exist."""
        assert SandboxStatus.INITIALIZED.value == "initialized"
        assert SandboxStatus.READY.value == "ready"
        assert SandboxStatus.RUNNING.value == "running"
        assert SandboxStatus.TIMEOUT.value == "timeout"
        assert SandboxStatus.ERROR.value == "error"
        assert SandboxStatus.TERMINATED.value == "terminated"


class TestResourceUsage:
    """Tests for ResourceUsage dataclass."""

    def test_default_usage(self):
        """Test default resource usage."""
        usage = ResourceUsage()
        assert usage.memory_peak_mb == 0
        assert usage.cpu_time_ms == 0
        assert usage.wall_time_ms == 0
        assert usage.read_bytes == 0
        assert usage.write_bytes == 0

    def test_custom_usage(self):
        """Test custom resource usage."""
        usage = ResourceUsage(
            memory_peak_mb=128.5,
            cpu_time_ms=500,
            wall_time_ms=600,
            read_bytes=1024,
            write_bytes=512,
        )
        assert usage.memory_peak_mb == 128.5
        assert usage.cpu_time_ms == 500
        assert usage.wall_time_ms == 600
        assert usage.read_bytes == 1024
        assert usage.write_bytes == 512


class TestWasmSandbox:
    """Tests for WasmSandbox class."""

    def test_sandbox_creation(self):
        """Test creating a sandbox."""
        sandbox = WasmSandbox("test-sandbox-1")
        assert sandbox.sandbox_id == "test-sandbox-1"
        assert sandbox.status == SandboxStatus.INITIALIZED

    def test_sandbox_with_config(self):
        """Test creating a sandbox with custom config."""
        config = SandboxConfig(
            max_memory_mb=256,
            timeout_ms=60000,
        )
        sandbox = WasmSandbox("test-sandbox-2", config)
        assert sandbox.config.max_memory_mb == 256
        assert sandbox.config.timeout_ms == 60000

    def test_check_extism(self):
        """Test Extism availability check."""
        sandbox = WasmSandbox("test-sandbox-3")
        # Just check it returns a boolean
        assert isinstance(sandbox.is_available(), bool)

    def test_run_nonexistent_wasm(self):
        """Test running a non-existent Wasm file."""
        sandbox = WasmSandbox("test-sandbox-4")
        result = sandbox.run_function(
            "/nonexistent/path/plugin.wasm",
            "run",
            "test input",
        )
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_context_manager(self):
        """Test sandbox as context manager."""
        with WasmSandbox("test-sandbox-5") as sandbox:
            assert sandbox.status in (SandboxStatus.INITIALIZED, SandboxStatus.READY)
        # After exiting context, status should be terminated
        assert sandbox.status == SandboxStatus.TERMINATED

    def test_multiple_runs(self):
        """Test running multiple functions in sequence."""
        sandbox = WasmSandbox("test-sandbox-6")
        # Run with non-existent wasm - should fail
        result1 = sandbox.run_function("/fake.wasm", "run", "input1")
        assert result1["status"] == "error"

        # Try again - should also fail
        result2 = sandbox.run_function("/fake.wasm", "run", "input2")
        assert result2["status"] == "error"

    def test_shutdown(self):
        """Test explicit shutdown."""
        sandbox = WasmSandbox("test-sandbox-7")
        sandbox.shutdown()
        assert sandbox.status == SandboxStatus.TERMINATED

    def test_fallback_function(self):
        """Test fallback function is called when Wasm fails."""
        sandbox = WasmSandbox("test-sandbox-8")

        def fallback(input_data):
            return {
                "status": "success",
                "result": f"fallback processed: {input_data}",
            }

        result = sandbox.run_function(
            "/nonexistent.wasm",
            "run",
            "test",
            fallback_fn=fallback,
        )
        assert result["status"] == "success"
        assert "fallback processed" in result["result"]
        assert result.get("fallback") is True


class TestCheckWasmSupport:
    """Tests for check_wasm_support function."""

    def test_support_info_structure(self):
        """Test that check_wasm_support returns expected structure."""
        info = check_wasm_support()

        assert "extism" in info
        assert "wasmer" in info
        assert "wasmtime" in info

        # All should be booleans
        assert isinstance(info["extism"], bool)
        assert isinstance(info["wasmer"], bool)
        assert isinstance(info["wasmtime"], bool)


class TestCreateSandboxedExecutor:
    """Tests for create_sandboxed_executor function."""

    def test_create_with_defaults(self):
        """Test creating executor with default config."""
        executor = create_sandboxed_executor()
        assert isinstance(executor, WasmSandbox)
        assert executor.config.max_memory_mb == 128
        assert executor.config.timeout_ms == 30000
        executor.shutdown()

    def test_create_with_custom_config(self):
        """Test creating executor with custom config."""
        config = SandboxConfig(
            max_memory_mb=512,
            timeout_ms=120000,
        )
        executor = create_sandboxed_executor(config)
        assert executor.config.max_memory_mb == 512
        assert executor.config.timeout_ms == 120000
        executor.shutdown()


class TestSandboxFeature:
    """Tests for SandboxFeature enum."""

    def test_feature_values(self):
        """Test that all expected features exist."""
        assert SandboxFeature.NETWORK.value == "network"
        assert SandboxFeature.FILESYSTEM_READ.value == "filesystem_read"
        assert SandboxFeature.FILESYSTEM_WRITE.value == "filesystem_write"
        assert SandboxFeature.ENVIRONMENT.value == "environment"
        assert SandboxFeature.HTTP.value == "http"
        assert SandboxFeature.RANDOM.value == "random"


class TestSandboxResourceLimits:
    """Integration tests for sandbox resource limits."""

    def test_config_env_vars(self):
        """Test sandbox config with environment variables."""
        config = SandboxConfig(
            env_vars={"KEY": "value", "ANOTHER": "value2"},
        )
        assert config.env_vars["KEY"] == "value"
        assert config.env_vars["ANOTHER"] == "value2"

    def test_config_allowed_paths(self):
        """Test sandbox config with allowed paths."""
        config = SandboxConfig(
            allowed_paths=["/tmp", "/var/tmp", "/home/user"],
        )
        assert len(config.allowed_paths) == 3
        assert "/tmp" in config.allowed_paths

    def test_config_wasi_disabled(self):
        """Test sandbox config with WASI disabled."""
        config = SandboxConfig(enable_wasi=False)
        assert config.enable_wasi is False

    def test_config_wasi_enabled(self):
        """Test sandbox config with WASI enabled."""
        config = SandboxConfig(enable_wasi=True)
        assert config.enable_wasi is True

    def test_sandbox_with_all_features_disabled(self):
        """Test sandbox with all features disabled."""
        config = SandboxConfig(
            allow_network=False,
            allow_filesystem=False,
        )
        sandbox = WasmSandbox("test-restricted", config)
        assert sandbox.config.allow_network is False
        assert sandbox.config.allow_filesystem is False
        sandbox.shutdown()

    def test_sandbox_with_all_features_enabled(self):
        """Test sandbox with all features enabled."""
        config = SandboxConfig(
            allow_network=True,
            allow_filesystem=True,
            allowed_paths=["/tmp"],
        )
        sandbox = WasmSandbox("test-permissive", config)
        assert sandbox.config.allow_network is True
        assert sandbox.config.allow_filesystem is True
        sandbox.shutdown()

    def test_sandbox_timeout_variations(self):
        """Test sandbox with different timeout values."""
        # Very short timeout
        config_short = SandboxConfig(timeout_ms=100)
        sandbox_short = WasmSandbox("test-timeout-short", config_short)
        assert sandbox_short.config.timeout_ms == 100
        sandbox_short.shutdown()

        # Very long timeout
        config_long = SandboxConfig(timeout_ms=600000)
        sandbox_long = WasmSandbox("test-timeout-long", config_long)
        assert sandbox_long.config.timeout_ms == 600000
        sandbox_long.shutdown()

    def test_sandbox_memory_limits(self):
        """Test sandbox with different memory limits."""
        # Small memory
        config_small = SandboxConfig(max_memory_mb=64)
        sandbox_small = WasmSandbox("test-mem-small", config_small)
        assert sandbox_small.config.max_memory_mb == 64
        sandbox_small.shutdown()

        # Large memory
        config_large = SandboxConfig(max_memory_mb=1024)
        sandbox_large = WasmSandbox("test-mem-large", config_large)
        assert sandbox_large.config.max_memory_mb == 1024
        sandbox_large.shutdown()

    def test_sandbox_unique_ids(self):
        """Test that sandboxes get unique IDs."""
        sandbox1 = WasmSandbox("id-test-1")
        sandbox2 = WasmSandbox("id-test-2")

        assert sandbox1.sandbox_id != sandbox2.sandbox_id
        sandbox1.shutdown()
        sandbox2.shutdown()

    def test_run_function_with_empty_input(self):
        """Test run function with empty input."""
        sandbox = WasmSandbox("test-empty-input")

        result = sandbox.run_function(
            "/nonexistent.wasm",
            "run",
            "",  # Empty string
        )

        assert result["status"] == "error"
        assert "duration_ms" in result
        sandbox.shutdown()

    def test_run_function_with_nonexistent_function(self):
        """Test run function with non-existent function name."""
        sandbox = WasmSandbox("test-bad-func")

        result = sandbox.run_function(
            "/nonexistent.wasm",
            "nonexistent_function",
            "input",
        )

        assert result["status"] == "error"
        sandbox.shutdown()

    def test_multiple_sandboxes_concurrent(self):
        """Test creating multiple sandboxes concurrently."""
        sandboxes = []
        for i in range(5):
            sandbox = WasmSandbox(f"concurrent-{i}")
            sandboxes.append(sandbox)

        # All should have valid status
        for sb in sandboxes:
            assert sb.status == SandboxStatus.INITIALIZED

        # Clean up
        for sb in sandboxes:
            sb.shutdown()

    def test_sandbox_reuse_after_shutdown(self):
        """Test that new sandbox can be created after shutdown."""
        sandbox1 = WasmSandbox("reuse-test-1")
        sandbox1.shutdown()

        sandbox2 = WasmSandbox("reuse-test-2")
        assert sandbox2.status == SandboxStatus.INITIALIZED
        sandbox2.shutdown()

    def test_fallback_function_with_dict(self):
        """Test fallback function returns dict with status."""
        sandbox = WasmSandbox("test-fallback-dict")

        def fallback(input_data):
            return {
                "status": "success",
                "result": {"nested": "value"},
            }

        result = sandbox.run_function(
            "/nonexistent.wasm",
            "run",
            "test",
            fallback_fn=fallback,
        )

        assert result["status"] == "success"
        assert result.get("fallback") is True
        sandbox.shutdown()

    def test_fallback_function_raises_exception(self):
        """Test fallback function that raises exception."""
        sandbox = WasmSandbox("test-fallback-error")

        def bad_fallback(input_data):
            raise RuntimeError("Fallback failed!")

        result = sandbox.run_function(
            "/nonexistent.wasm",
            "run",
            "test",
            fallback_fn=bad_fallback,
        )

        assert result["status"] == "error"
        assert "fallback failed" in result["error"].lower()
        sandbox.shutdown()

    def test_check_wasm_support_extism_version(self):
        """Test check_wasm_support includes extism version when available."""
        info = check_wasm_support()

        # If extism is available, version info should be present
        if info["extism"]:
            assert "extism_version" in info

    def test_check_wasm_support_all_runtimes(self):
        """Test check_wasm_support checks all runtime types."""
        info = check_wasm_support()

        # Should have all three runtimes
        assert "extism" in info
        assert "wasmer" in info
        assert "wasmtime" in info

    def test_create_sandbox_unique_id_format(self):
        """Test that create_sandboxed_executor creates valid UUID format."""
        executor1 = create_sandboxed_executor()
        executor2 = create_sandboxed_executor()

        # IDs should be different
        assert executor1.sandbox_id != executor2.sandbox_id

        # IDs should be short (8 chars based on implementation)
        assert len(executor1.sandbox_id) == 8

        executor1.shutdown()
        executor2.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
