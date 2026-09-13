"""Integration tests for Runtime Dispatcher.

Tests the performance dispatcher functionality including:
- JSON dispatcher selection based on runtime
- TOML dispatcher selection
- Runtime detection and feature detection
- Performance module registration and selection
"""

from unittest.mock import MagicMock, patch

import pytest

from thegent.infra.runtime_dispatcher import (
    HAS_EXTISM,
    HAS_FREETHREADING,
    HAS_MOJO,
    HAS_ORJSON,
    HAS_RTOML,
    HAS_RUST_ROUTER,
    HAS_TOMLI,
    HAS_UJSON,
    IS_PYPY,
    PYTHON_VERSION,
    MojoDispatcher,
    PerformanceModule,
    WasmDispatcher,
    get_json_dumps,
    get_json_loads,
    get_router,
    get_runtime_status,
    get_toml_loads,
    json_dumps_dispatcher,
    json_loads_dispatcher,
    router_dispatcher,
    toml_loads_dispatcher,
)


class TestPerformanceModule:
    """Tests for PerformanceModule base class."""

    def test_module_creation(self):
        """Test PerformanceModule creation."""
        module = PerformanceModule("test_module")
        assert module.name == "test_module"
        assert module._implementations == {}
        assert module._selected is None

    def test_register_implementation(self):
        """Test registering implementations."""
        module = PerformanceModule("test")
        impl = MagicMock()
        module.register("python", impl)
        assert "python" in module._implementations
        assert module._implementations["python"] is impl

    def test_get_impl_returns_registered(self):
        """Test get_impl returns registered implementation."""
        module = PerformanceModule("test")
        impl = MagicMock()
        module.register("python", impl)
        result = module.get_impl()
        assert result is impl

    def test_get_impl_selects_native_first_on_cpython(self):
        """Test that native is selected first on CPython."""
        module = PerformanceModule("test")

        native_impl = MagicMock()
        python_impl = MagicMock()

        module.register("native", native_impl)
        module.register("python", python_impl)

        with patch("thegent.infra.runtime_dispatcher.IS_PYPY", False):
            result = module.get_impl()
            assert result is native_impl

    def test_get_impl_selects_pypy_on_pypy(self):
        """Test that pypy implementation is selected on PyPy."""
        module = PerformanceModule("test")

        pypy_impl = MagicMock()
        native_impl = MagicMock()
        python_impl = MagicMock()

        module.register("pypy", pypy_impl)
        module.register("native", native_impl)
        module.register("python", python_impl)

        with patch("thegent.infra.runtime_dispatcher.IS_PYPY", True):
            # Reset selection to test selection logic
            module._selected = None
            result = module.get_impl()
            assert result is pypy_impl


class TestJsonDispatcher:
    """Tests for JSON dispatchers."""

    def test_json_dumps_dispatcher_exists(self):
        """Test json_dumps_dispatcher is defined."""
        assert json_dumps_dispatcher is not None
        assert json_dumps_dispatcher.name == "json_dumps"

    def test_json_loads_dispatcher_exists(self):
        """Test json_loads_dispatcher is defined."""
        assert json_loads_dispatcher is not None
        assert json_loads_dispatcher.name == "json_loads"

    def test_get_json_dumps_returns_callable(self):
        """Test get_json_dumps returns a callable."""
        func = get_json_dumps()
        assert callable(func)

    def test_get_json_loads_returns_callable(self):
        """Test get_json_loads returns a callable."""
        func = get_json_loads()
        assert callable(func)

    def test_json_dumps_with_simple_object(self):
        """Test JSON dumps with simple object."""
        func = get_json_dumps()
        result = func({"key": "value"})
        assert "key" in result
        assert "value" in result

    def test_json_loads_with_simple_string(self):
        """Test JSON loads with simple string."""
        func = get_json_loads()
        result = func('{"key": "value"}')
        assert result["key"] == "value"

    def test_json_loads_with_bytes(self):
        """Test JSON loads with bytes input."""
        func = get_json_loads()
        result = func(b'{"key": "value"}')
        assert result["key"] == "value"


class TestTomlDispatcher:
    """Tests for TOML dispatchers."""

    def test_toml_loads_dispatcher_exists(self):
        """Test toml_loads_dispatcher is defined."""
        assert toml_loads_dispatcher is not None
        assert toml_loads_dispatcher.name == "toml_loads"

    def test_get_toml_loads_returns_callable(self):
        """Test get_toml_loads returns a callable."""
        func = get_toml_loads()
        assert callable(func)

    def test_toml_loads_parses_valid_toml(self):
        """Test TOML loads with valid TOML string."""
        func = get_toml_loads()
        toml_str = """
[section]
key = "value"
number = 42
"""
        result = func(toml_str)
        assert "section" in result
        assert result["section"]["key"] == "value"
        assert result["section"]["number"] == 42


class TestRouterDispatcher:
    """Tests for router dispatcher."""

    def test_router_dispatcher_exists(self):
        """Test router_dispatcher is defined."""
        assert router_dispatcher is not None

    def test_get_router_returns_impl(self):
        """Test get_router returns implementation."""
        router = get_router()
        # Router may be None if rust_router not available
        # Just verify we get something back
        assert router is not None or not HAS_RUST_ROUTER


class TestRuntimeStatus:
    """Tests for runtime status detection."""

    def test_get_runtime_status_returns_dict(self):
        """Test get_runtime_status returns proper structure."""
        status = get_runtime_status()

        assert isinstance(status, dict)
        assert "implementation" in status
        assert "version" in status
        assert "freethreading" in status
        assert "jit" in status
        assert "active_extensions" in status

    def test_runtime_status_implementation(self):
        """Test runtime status implementation value."""
        status = get_runtime_status()
        assert status["implementation"] in ("cpython", "pypy", "py", "indy")

    def test_runtime_status_version_format(self):
        """Test runtime status version format."""
        status = get_runtime_status()
        version = status["version"]
        # Version should be like "3.12"
        assert "." in version
        parts = version.split(".")
        assert len(parts) >= 2

    def test_runtime_status_freethreading(self):
        """Test freethreading status is boolean."""
        status = get_runtime_status()
        assert isinstance(status["freethreading"], bool)

    def test_runtime_status_jit(self):
        """Test JIT status is boolean."""
        status = get_runtime_status()
        assert isinstance(status["jit"], bool)

    def test_runtime_status_extensions(self):
        """Test active extensions are boolean."""
        status = get_runtime_status()
        extensions = status["active_extensions"]

        assert isinstance(extensions, dict)
        assert "orjson" in extensions
        assert "ujson" in extensions
        assert "rtoml" in extensions
        assert "rust_router" in extensions

        for value in extensions.values():
            assert isinstance(value, bool)


class TestWasmDispatcher:
    """Tests for Wasm dispatcher."""

    def test_wasm_dispatcher_class_exists(self):
        """Test WasmDispatcher class exists."""
        assert WasmDispatcher is not None

    def test_wasm_dispatcher_has_static_method(self):
        """Test WasmDispatcher has call_plugin method."""
        assert hasattr(WasmDispatcher, "call_plugin")
        assert callable(WasmDispatcher.call_plugin)

    def test_wasm_dispatcher_raises_when_not_available(self):
        """Test WasmDispatcher raises error when Extism not available."""
        if not HAS_EXTISM:
            with pytest.raises(ImportError):
                WasmDispatcher.call_plugin("/fake/path.wasm", "run", b"input")


class TestMojoDispatcher:
    """Tests for Mojo dispatcher."""

    def test_mojo_dispatcher_class_exists(self):
        """Test MojoDispatcher class exists."""
        assert MojoDispatcher is not None

    def test_mojo_dispatcher_is_class(self):
        """Test MojoDispatcher is a class."""
        assert isinstance(MojoDispatcher, type)


class TestRuntimeDetection:
    """Tests for runtime detection constants."""

    def test_is_pypy_is_boolean(self):
        """Test IS_PYPY is a boolean."""
        assert isinstance(IS_PYPY, bool)

    def test_python_version_is_tuple(self):
        """Test PYTHON_VERSION is a tuple."""
        assert isinstance(PYTHON_VERSION, tuple)
        assert len(PYTHON_VERSION) >= 2

    def test_has_freethreading_is_boolean(self):
        """Test HAS_FREETHREADING is a boolean."""
        assert isinstance(HAS_FREETHREADING, bool)

    def test_extension_flags_are_booleans(self):
        """Test all extension flags are booleans."""
        assert isinstance(HAS_ORJSON, bool)
        assert isinstance(HAS_UJSON, bool)
        assert isinstance(HAS_RTOML, bool)
        assert isinstance(HAS_TOMLI, bool)
        assert isinstance(HAS_RUST_ROUTER, bool)
        assert isinstance(HAS_EXTISM, bool)
        assert isinstance(HAS_MOJO, bool)


class TestDispatcherIntegration:
    """Integration tests for dispatcher functionality."""

    def test_json_roundtrip(self):
        """Test JSON dumps and loads roundtrip."""
        dumps = get_json_dumps()
        loads = get_json_loads()

        original = {"string": "hello", "number": 42, "list": [1, 2, 3]}

        dumped = dumps(original)
        loaded = loads(dumped)

        assert loaded == original

    def test_json_with_unicode(self):
        """Test JSON handles unicode correctly."""
        dumps = get_json_dumps()
        loads = get_json_loads()

        original = {"emoji": "🎉", "unicode": "café"}

        dumped = dumps(original)
        loaded = loads(dumped)

        assert loaded["emoji"] == "🎉"
        assert loaded["unicode"] == "café"

    def test_toml_with_nested_tables(self):
        """Test TOML handles nested tables."""
        func = get_toml_loads()

        toml_str = """
[database]
server = "192.168.1.1"
ports = [8000, 8001, 8002]

[database.connection]
max = 100
timeout = 30
"""
        result = func(toml_str)
        assert result["database"]["server"] == "192.168.1.1"
        assert result["database"]["ports"] == [8000, 8001, 8002]
        assert result["database"]["connection"]["max"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
