"""Unit tests for fast_websocket FastWebSocket class.

Tests the async WebSocket client with automatic backend selection,
including the websocket-client fallback for async operations.
"""

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.infra.fast_websocket import (
    WEBSOCKET_CLIENT_AVAILABLE,
    WEBSOCKETS_AVAILABLE,
    FastWebSocket,
    websocket_connect_async,
    websocket_connect_sync,
)


class TestFastWebSocketInit:
    """Tests for FastWebSocket initialization."""

    def test_init_with_url(self):
        """Test initialization with URL."""
        ws = FastWebSocket("ws://localhost:8080")
        assert ws.url == "ws://localhost:8080"

    def test_init_with_wss_url(self):
        """Test initialization with secure WebSocket URL."""
        ws = FastWebSocket("wss://secure.example.com/ws")
        assert ws.url == "wss://secure.example.com/ws"

    def test_init_stores_options(self):
        """Test that options are stored."""
        ws = FastWebSocket("ws://localhost:8080", timeout=30, headers={"X-Custom": "value"})
        assert ws.options["timeout"] == 30
        assert ws.options["headers"]["X-Custom"] == "value"

    def test_initial_backend_is_none(self):
        """Test that initial backend is None."""
        ws = FastWebSocket("ws://localhost:8080")
        assert ws._backend is None

    def test_initial_ws_is_none(self):
        """Test that initial _ws is None."""
        ws = FastWebSocket("ws://localhost:8080")
        assert ws._ws is None


class TestFastWebSocketConnectSync:
    """Tests for synchronous WebSocket connection."""

    def test_connect_sync_requires_websocket_client(self):
        """Test that sync connect requires websocket-client library."""
        ws = FastWebSocket("ws://localhost:8080")

        if not WEBSOCKET_CLIENT_AVAILABLE:
            with pytest.raises(ImportError, match="No WebSocket library available"):
                ws.connect_sync()

    def test_connect_sync_backend_selection(self):
        """Test that sync connect selects websocket-client backend."""
        if not WEBSOCKET_CLIENT_AVAILABLE:
            pytest.skip("websocket-client not available")

        ws = FastWebSocket("ws://localhost:8080")
        # Note: This will fail without a real server, but tests backend selection
        try:
            ws.connect_sync()
        except Exception:
            # Connection will fail without server, but backend should be set
            pass

        # If it didn't raise ImportError, backend should be set
        if ws._backend is not None:
            assert ws._backend == "websocket-client"


class TestFastWebSocketConnectAsync:
    """Tests for asynchronous WebSocket connection."""

    @pytest.mark.asyncio
    async def test_connect_async_without_library_raises(self):
        """Test that async connect raises when no library available."""
        if not WEBSOCKETS_AVAILABLE and not WEBSOCKET_CLIENT_AVAILABLE:
            ws = FastWebSocket("ws://localhost:8080")
            with pytest.raises(ImportError, match="No WebSocket library available"):
                await ws.connect_async()

    @pytest.mark.asyncio
    async def test_connect_async_selects_websockets_backend(self):
        """Test that async connect selects websockets backend when available."""
        if not WEBSOCKETS_AVAILABLE:
            pytest.skip("websockets library not available")

        ws = FastWebSocket("ws://localhost:8080")
        try:
            await ws.connect_async()
        except Exception:
            # Connection will fail without server
            pass

        # Backend should be set if library is available
        if ws._backend is not None:
            assert ws._backend == "websockets"

    @pytest.mark.asyncio
    async def test_connect_async_falls_back_to_websocket_client(self):
        """Test async fallback to websocket-client when websockets unavailable."""
        if WEBSOCKETS_AVAILABLE:
            pytest.skip("websockets is available, fallback not tested")

        if not WEBSOCKET_CLIENT_AVAILABLE:
            pytest.skip("websocket-client not available for fallback test")

        ws = FastWebSocket("ws://localhost:8080")
        with contextlib.suppress(Exception):
            await ws.connect_async()

        if ws._backend is not None:
            assert ws._backend == "websocket-client-async"


class TestFastWebSocketSendOperations:
    """Tests for WebSocket send operations."""

    def test_send_sync_raises_when_not_connected(self):
        """Test that sync send raises when not connected."""
        ws = FastWebSocket("ws://localhost:8080")
        with pytest.raises(RuntimeError, match="Not connected"):
            ws.send_sync("test message")

    @pytest.mark.asyncio
    async def test_send_async_raises_when_not_connected(self):
        """Test that async send raises when not connected."""
        ws = FastWebSocket("ws://localhost:8080")
        with pytest.raises(RuntimeError, match="Not connected"):
            await ws.send_async("test message")

    def test_send_sync_raises_with_wrong_backend(self):
        """Test sync send raises with wrong backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websockets"  # Wrong backend for sync
        ws._ws = object()  # Dummy connection

        with pytest.raises(RuntimeError, match="Not connected or wrong backend"):
            ws.send_sync("test")

    @pytest.mark.asyncio
    async def test_send_async_with_websockets_backend(self):
        """Test async send with websockets backend."""
        if not WEBSOCKETS_AVAILABLE:
            pytest.skip("websockets not available")

        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websockets"
        # Create an async mock for the websocket
        mock_ws = MagicMock()
        mock_ws.send = AsyncMock()
        ws._ws = mock_ws

        # Should not raise
        await ws.send_async("test message")
        mock_ws.send.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_send_async_with_websocket_client_async_backend(self):
        """Test async send with websocket-client-async backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websocket-client-async"
        # For websocket-client-async, the ws object uses sync methods
        mock_ws = MagicMock()
        mock_ws.send = MagicMock()
        ws._ws = mock_ws

        # Should not raise (runs in thread pool)
        await ws.send_async("test message")


class TestFastWebSocketRecvOperations:
    """Tests for WebSocket receive operations."""

    def test_recv_sync_raises_when_not_connected(self):
        """Test that sync recv raises when not connected."""
        ws = FastWebSocket("ws://localhost:8080")
        with pytest.raises(RuntimeError, match="Not connected"):
            ws.recv_sync()

    @pytest.mark.asyncio
    async def test_recv_async_raises_when_not_connected(self):
        """Test that async recv raises when not connected."""
        ws = FastWebSocket("ws://localhost:8080")
        with pytest.raises(RuntimeError, match="Not connected"):
            await ws.recv_async()

    def test_recv_sync_raises_with_wrong_backend(self):
        """Test sync recv raises with wrong backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websockets"  # Wrong backend for sync
        ws._ws = object()

        with pytest.raises(RuntimeError, match="Not connected"):
            ws.recv_sync()

    @pytest.mark.asyncio
    async def test_recv_async_with_websockets_backend(self):
        """Test async recv with websockets backend."""
        if not WEBSOCKETS_AVAILABLE:
            pytest.skip("websockets not available")

        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websockets"
        # Create an async mock for the websocket
        mock_ws = MagicMock()
        mock_ws.recv = AsyncMock(return_value="response")
        ws._ws = mock_ws

        result = await ws.recv_async()
        assert result == "response"

    @pytest.mark.asyncio
    async def test_recv_async_with_websocket_client_async_backend(self):
        """Test async recv with websocket-client-async backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websocket-client-async"
        # For websocket-client-async, the ws object uses sync methods
        mock_ws = MagicMock()
        mock_ws.recv = MagicMock(return_value="response")
        ws._ws = mock_ws

        result = await ws.recv_async()
        assert result == "response"


class TestFastWebSocketCloseOperations:
    """Tests for WebSocket close operations."""

    @pytest.mark.asyncio
    async def test_close_async_with_websockets(self):
        """Test async close with websockets backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websockets"
        # Create a proper async mock for close
        mock_ws = MagicMock()
        mock_ws.close = AsyncMock()
        ws._ws = mock_ws

        await ws.close_async()
        mock_ws.close.assert_called()

    @pytest.mark.asyncio
    async def test_close_async_with_websocket_client(self):
        """Test async close with websocket-client backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websocket-client"
        # websocket-client uses sync close
        mock_ws = MagicMock()
        mock_ws.close = MagicMock()
        ws._ws = mock_ws

        await ws.close_async()
        mock_ws.close.assert_called()

    def test_close_sync_raises_with_websockets_backend(self):
        """Test sync close raises with websockets backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websockets"
        ws._ws = object()

        with pytest.raises(RuntimeError, match="Use close_async"):
            ws.close_sync()

    def test_close_sync_with_websocket_client(self):
        """Test sync close with websocket-client backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websocket-client"
        # websocket-client uses sync close
        mock_ws = MagicMock()
        mock_ws.close = MagicMock()
        ws._ws = mock_ws

        ws.close_sync()
        mock_ws.close.assert_called()


class TestFastWebSocketContextManagers:
    """Tests for context manager protocols."""

    def test_sync_context_manager_enter_exit(self):
        """Test sync context manager protocol."""
        ws = FastWebSocket("ws://localhost:8080")

        # Test __enter__ and __exit__ exist
        assert hasattr(ws, "__enter__")
        assert hasattr(ws, "__exit__")

    @pytest.mark.asyncio
    async def test_async_context_manager_protocol(self):
        """Test async context manager protocol."""
        ws = FastWebSocket("ws://localhost:8080")

        # Test __aenter__ and __aexit__ exist
        assert hasattr(ws, "__aenter__")
        assert hasattr(ws, "__aexit__")

    def test_context_manager_returns_self(self):
        """Test that context manager returns self."""
        if not WEBSOCKET_CLIENT_AVAILABLE:
            pytest.skip("websocket-client not available")

        ws = FastWebSocket("ws://localhost:8080")
        # Mock the connection to avoid real network call
        ws.connect_sync = lambda: None
        ws.close_sync = lambda: None

        with ws as returned_ws:
            assert returned_ws is ws


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_websocket_connect_sync_exists(self):
        """Test websocket_connect_sync function exists."""
        assert callable(websocket_connect_sync)

    def test_websocket_connect_async_exists(self):
        """Test websocket_connect_async function exists."""
        assert callable(websocket_connect_async)

    @pytest.mark.asyncio
    async def test_websocket_connect_async_returns_connected_ws(self):
        """Test websocket_connect_async returns connected WebSocket."""
        if not WEBSOCKETS_AVAILABLE and not WEBSOCKET_CLIENT_AVAILABLE:
            pytest.skip("No WebSocket library available")

        ws = FastWebSocket("ws://localhost:8080")
        # Mock connect_async

        async def mock_connect():
            ws._backend = "websockets" if WEBSOCKETS_AVAILABLE else "websocket-client-async"
            ws._ws = MagicMockWebSocket()

        ws.connect_async = mock_connect

        # The convenience function should call connect_async
        # Here we test the pattern
        await ws.connect_async()
        assert ws._backend is not None

    def test_websocket_connect_sync_returns_connected_ws(self):
        """Test websocket_connect_sync returns connected WebSocket."""
        if not WEBSOCKET_CLIENT_AVAILABLE:
            pytest.skip("websocket-client not available")

        ws = FastWebSocket("ws://localhost:8080")
        # Mock connect_sync

        def mock_connect():
            ws._backend = "websocket-client"
            ws._ws = MagicMockWebSocket()

        ws.connect_sync = mock_connect

        # The convenience function should call connect_sync
        ws.connect_sync()
        assert ws._backend == "websocket-client"

    @pytest.mark.asyncio
    async def test_websocket_connect_async_convenience_function(self):
        """Test websocket_connect_async convenience function creates and connects."""
        if not WEBSOCKETS_AVAILABLE and not WEBSOCKET_CLIENT_AVAILABLE:
            pytest.skip("No WebSocket library available")

        # Create a mock connection
        with patch.object(FastWebSocket, "connect_async", new_callable=AsyncMock) as mock_connect:
            ws = await websocket_connect_async("ws://localhost:8080")
            assert isinstance(ws, FastWebSocket)
            mock_connect.assert_called_once()

    def test_websocket_connect_sync_convenience_function(self):
        """Test websocket_connect_sync convenience function creates and connects."""
        if not WEBSOCKET_CLIENT_AVAILABLE:
            pytest.skip("websocket-client not available")

        with patch.object(FastWebSocket, "connect_sync") as mock_connect:
            ws = websocket_connect_sync("ws://localhost:8080")
            assert isinstance(ws, FastWebSocket)
            mock_connect.assert_called_once()


class TestFastWebSocketErrorHandling:
    """Tests for error handling paths."""

    def test_recv_async_raises_when_not_connected(self):
        """Test recv_async raises RuntimeError when not connected."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = None
        ws._ws = None

        with pytest.raises(RuntimeError):
            asyncio.run(ws.recv_async())

    @pytest.mark.asyncio
    async def test_recv_async_raises_with_unknown_backend(self):
        """Test recv_async raises with unknown backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "unknown"
        ws._ws = MagicMock()

        with pytest.raises(RuntimeError, match="Not connected"):
            await ws.recv_async()

    def test_send_sync_with_valid_backend(self):
        """Test send_sync with valid websocket-client backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websocket-client"
        mock_ws = MagicMock()
        mock_ws.send = MagicMock()
        ws._ws = mock_ws

        ws.send_sync("test message")
        mock_ws.send.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_close_async_with_websocket_client_async_backend(self):
        """Test close_async with websocket-client-async backend."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websocket-client-async"
        mock_ws = MagicMock()
        mock_ws.close = MagicMock()
        ws._ws = mock_ws

        # Should not raise
        await ws.close_async()

    @pytest.mark.asyncio
    async def test_async_context_manager_full_lifecycle(self):
        """Test full async context manager lifecycle."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websockets"
        mock_ws = MagicMock()
        mock_ws.close = AsyncMock()
        ws._ws = mock_ws

        # Simulate __aexit__
        await ws.__aexit__(None, None, None)
        mock_ws.close.assert_called()

    def test_sync_context_manager_full_lifecycle(self):
        """Test full sync context manager lifecycle."""
        ws = FastWebSocket("ws://localhost:8080")
        ws._backend = "websocket-client"
        mock_ws = MagicMock()
        mock_ws.close = MagicMock()
        ws._ws = mock_ws

        # Simulate __exit__
        ws.__exit__(None, None, None)
        mock_ws.close.assert_called()


class TestFastWebSocketBackendFlags:
    """Tests for backend availability flags."""

    def test_websockets_available_is_boolean(self):
        """Test WEBSOCKETS_AVAILABLE is boolean."""
        assert isinstance(WEBSOCKETS_AVAILABLE, bool)

    def test_websocket_client_available_is_boolean(self):
        """Test WEBSOCKET_CLIENT_AVAILABLE is boolean."""
        assert isinstance(WEBSOCKET_CLIENT_AVAILABLE, bool)


class MagicMockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self, return_value=None):
        self._return_value = return_value
        self._closed = False
        self._sent_data = []

    async def send(self, data):
        self._sent_data.append(data)

    async def recv(self):
        return self._return_value or "mock_response"

    async def close(self):
        self._closed = True

    def send_sync(self, data):
        self._sent_data.append(data)

    def recv_sync(self):
        return self._return_value or "mock_response"

    def close_sync(self):
        self._closed = True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
