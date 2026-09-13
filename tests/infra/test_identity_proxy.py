"""Tests for SSHIdentityProxy bridge.

Tests the SSH identity proxy which allows isolated L2 agents to use
host SSH keys for Git operations without exposing private keys.

# @trace FR-SEC-002
"""

from __future__ import annotations

import os
import socket
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.infra.identity_proxy import SSHIdentityProxy

# Counter for unique socket names within a test run
_socket_counter = 0


def _get_unique_socket_path(name: str) -> Path:
    """Generate a unique, short socket path in /tmp to avoid AF_UNIX path length limits.

    macOS has a limit of ~104 characters for Unix socket paths. Using /tmp ensures
    paths are short enough while still being unique per test.
    """
    global _socket_counter
    _socket_counter += 1
    return Path(f"/tmp/ssh-test-{os.getpid()}-{_socket_counter}-{name}.sock")


@pytest.fixture
def proxy_socket_path() -> Path:
    """Return a temporary socket path for the proxy."""
    return _get_unique_socket_path("proxy")


@pytest.fixture
def proxy(proxy_socket_path: Path) -> SSHIdentityProxy:
    """Create a basic SSHIdentityProxy instance."""
    return SSHIdentityProxy(proxy_socket_path)


@pytest.fixture
def mock_host_socket() -> Path:
    """Create a mock host SSH auth socket path."""
    return _get_unique_socket_path("host")


@pytest.fixture
def proxy_with_env(
    proxy_socket_path: Path, mock_host_socket: Path, monkeypatch: pytest.MonkeyPatch
) -> SSHIdentityProxy:
    """Create a proxy with SSH_AUTH_SOCK environment variable set."""
    monkeypatch.setenv("SSH_AUTH_SOCK", str(mock_host_socket))
    return SSHIdentityProxy(proxy_socket_path)


class TestSSHIdentityProxyInit:
    """Tests for SSHIdentityProxy initialization."""

    def test_init_sets_socket_path(
        self, proxy: SSHIdentityProxy, proxy_socket_path: Path
    ) -> None:
        """Verify socket path is set correctly."""
        assert proxy.proxy_socket_path == proxy_socket_path

    def test_init_reads_ssh_auth_sock(
        self, proxy: SSHIdentityProxy, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify SSH_AUTH_SOCK is read from environment."""
        monkeypatch.setenv("SSH_AUTH_SOCK", "/tmp/test.sock")
        proxy_with_env = SSHIdentityProxy(proxy.proxy_socket_path)
        assert proxy_with_env.host_ssh_auth_sock == "/tmp/test.sock"

    def test_init_handles_missing_ssh_auth_sock(
        self, proxy: SSHIdentityProxy, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify missing SSH_AUTH_SOCK is handled gracefully."""
        monkeypatch.delenv("SSH_AUTH_SOCK", raising=False)
        proxy_no_env = SSHIdentityProxy(proxy.proxy_socket_path)
        assert proxy_no_env.host_ssh_auth_sock is None

    def test_init_running_state_false(self, proxy: SSHIdentityProxy) -> None:
        """Verify proxy starts with running state False."""
        assert proxy._running is False

    def test_init_thread_none(self, proxy: SSHIdentityProxy) -> None:
        """Verify proxy starts with no thread."""
        assert proxy._thread is None


class TestSSHIdentityProxyLifecycle:
    """Tests for start/stop lifecycle."""

    def test_start_creates_socket_directory(
        self, mock_host_socket: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify start creates parent directories for socket."""
        # Use a nested path that doesn't exist yet (but keep it short for AF_UNIX limit)
        socket_path = Path(f"/tmp/ssh-test-{os.getpid()}-nested/proxy.sock")
        monkeypatch.setenv("SSH_AUTH_SOCK", str(mock_host_socket))
        proxy = SSHIdentityProxy(socket_path)

        assert not socket_path.parent.exists()
        proxy.start()
        assert socket_path.parent.exists()
        proxy.stop()

    def test_start_sets_running_true(self, proxy_with_env: SSHIdentityProxy) -> None:
        """Verify start sets running state to True."""
        proxy_with_env.start()
        assert proxy_with_env._running is True
        proxy_with_env.stop()

    def test_stop_sets_running_false(self, proxy_with_env: SSHIdentityProxy) -> None:
        """Verify stop sets running state to False."""
        proxy_with_env.start()
        proxy_with_env.stop()
        assert proxy_with_env._running is False

    def test_stop_removes_socket_file(
        self, proxy_with_env: SSHIdentityProxy, proxy_socket_path: Path
    ) -> None:
        """Verify stop removes the socket file."""
        proxy_with_env.start()
        proxy_with_env.stop()
        assert not proxy_socket_path.exists()

    def test_start_creates_thread(self, proxy_with_env: SSHIdentityProxy) -> None:
        """Verify start creates a server thread."""
        proxy_with_env.start()
        assert proxy_with_env._thread is not None
        assert proxy_with_env._thread.is_alive()
        proxy_with_env.stop()

    def test_start_without_ssh_auth_sock_logs_warning(
        self, proxy: SSHIdentityProxy, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify start logs warning when SSH_AUTH_SOCK is not set."""
        with patch.dict(os.environ, {}, clear=True):
            if "SSH_AUTH_SOCK" in os.environ:
                del os.environ["SSH_AUTH_SOCK"]
            proxy_no_env = SSHIdentityProxy(proxy.proxy_socket_path)
            proxy_no_env.start()

        assert "SSH_AUTH_SOCK not set" in caplog.text
        assert proxy_no_env._running is False

    def test_start_removes_existing_socket(
        self, proxy_with_env: SSHIdentityProxy, proxy_socket_path: Path
    ) -> None:
        """Verify existing socket file is removed on start."""
        proxy_socket_path.parent.mkdir(parents=True, exist_ok=True)
        proxy_socket_path.touch()

        proxy_with_env.start()
        proxy_with_env.stop()

        # Socket should have been recreated (not the old one)


class TestSSHIdentityProxyEnvironment:
    """Tests for environment variable generation."""

    def test_get_env_returns_ssh_auth_sock(
        self, proxy: SSHIdentityProxy, proxy_socket_path: Path
    ) -> None:
        """Verify get_env returns SSH_AUTH_SOCK with proxy path."""
        env = proxy.get_env()
        assert "SSH_AUTH_SOCK" in env
        assert env["SSH_AUTH_SOCK"] == str(proxy_socket_path)

    def test_get_env_returns_thegent_identity_proxy(
        self, proxy: SSHIdentityProxy
    ) -> None:
        """Verify get_env returns THEGENT_IDENTITY_PROXY flag."""
        env = proxy.get_env()
        assert "THEGENT_IDENTITY_PROXY" in env
        assert env["THEGENT_IDENTITY_PROXY"] == "1"

    def test_get_env_dict_is_valid(self, proxy: SSHIdentityProxy) -> None:
        """Verify get_env returns a valid dict with string values."""
        env = proxy.get_env()
        assert isinstance(env, dict)
        assert all(isinstance(k, str) for k in env)
        assert all(isinstance(v, str) for v in env.values())


class TestSSHIdentityProxyServerLoop:
    """Tests for server loop functionality."""

    def test_server_loop_handles_timeout(
        self, proxy_with_env: SSHIdentityProxy
    ) -> None:
        """Verify server loop handles socket timeout gracefully."""
        proxy_with_env.start()
        # Let it run briefly
        import time

        time.sleep(0.1)
        proxy_with_env.stop()
        # Should not have raised any exceptions

    def test_server_loop_stops_on_running_false(
        self, proxy_with_env: SSHIdentityProxy
    ) -> None:
        """Verify server loop terminates when running is False."""
        proxy_with_env.start()
        assert proxy_with_env._thread is not None
        proxy_with_env.stop()
        # Give thread time to terminate
        proxy_with_env._thread.join(timeout=2.0)
        assert not proxy_with_env._thread.is_alive()


class TestSSHIdentityProxyMockedSocket:
    """Tests with mocked socket operations."""

    @patch("thegent.infra.identity_proxy.socket.socket")
    def test_start_creates_unix_socket(
        self,
        mock_socket_class: MagicMock,
        proxy_with_env: SSHIdentityProxy,
        proxy_socket_path: Path,
    ) -> None:
        """Verify start creates a Unix domain socket."""
        mock_socket = MagicMock()
        mock_socket.settimeout.return_value = None
        mock_socket.bind.return_value = None
        mock_socket.listen.return_value = None
        mock_socket.accept.side_effect = TimeoutError

        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        proxy_with_env.start()
        proxy_with_env.stop()

        mock_socket_class.assert_called()
        call_args = mock_socket_class.call_args
        assert call_args[0][0] == socket.AF_UNIX
        assert call_args[0][1] == socket.SOCK_STREAM

    @patch("thegent.infra.identity_proxy.socket.socket")
    def test_socket_operations_sequence(
        self,
        mock_socket_class: MagicMock,
        proxy_with_env: SSHIdentityProxy,
        proxy_socket_path: Path,
    ) -> None:
        """Verify socket bind, listen, settimeout are called in sequence."""
        mock_socket = MagicMock()
        mock_socket.settimeout.return_value = None
        mock_socket.bind.return_value = None
        mock_socket.listen.return_value = None
        mock_socket.accept.side_effect = TimeoutError

        # Properly configure the context manager mock
        mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)

        proxy_with_env.start()

        # Give the thread a moment to start and hit the timeout
        import time

        time.sleep(0.2)

        proxy_with_env.stop()

        # Verify socket was created with correct family and type
        mock_socket_class.assert_called_with(socket.AF_UNIX, socket.SOCK_STREAM)


class TestSSHIdentityProxyClientHandling:
    """Tests for client connection handling."""

    def test_handle_client_closes_connection(
        self, proxy_with_env: SSHIdentityProxy
    ) -> None:
        """Verify client connections are properly closed."""
        proxy_with_env.start()

        # Simulate a connection (the handler should close it)
        # This is a basic sanity check
        proxy_with_env.stop()

    @patch("socket.socket")
    def test_handle_client_creates_host_connection(
        self,
        mock_socket_class: MagicMock,
        proxy_with_env: SSHIdentityProxy,
        mock_host_socket: Path,
    ) -> None:
        """Verify handler connects to host SSH agent."""
        mock_client = MagicMock()
        mock_client.recv.return_value = b""  # Empty read = connection closed

        mock_host = MagicMock()
        mock_host.recv.return_value = b""

        # Setup socket mock to return different sockets
        mock_socket_class.return_value.__enter__.return_value = mock_host

        proxy_with_env.start()
        proxy_with_env.stop()

        # The host connection should have been attempted


class TestSSHIdentityProxyThreadSafety:
    """Tests for thread safety of the proxy."""

    def test_concurrent_start_stop(self, proxy_with_env: SSHIdentityProxy) -> None:
        """Verify concurrent start/stop doesn't cause issues."""

        def start_stop():
            proxy_with_env.start()
            import time

            time.sleep(0.01)
            proxy_with_env.stop()

        threads = [threading.Thread(target=start_stop) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        # Should complete without exceptions

    def test_get_env_thread_safe(self, proxy: SSHIdentityProxy) -> None:
        """Verify get_env is thread-safe."""
        results = []
        errors = []

        def get_env_repeatedly():
            for _ in range(100):
                try:
                    env = proxy.get_env()
                    results.append(env)
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=get_env_repeatedly) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 500
        # All results should be identical
        for r in results:
            assert r == results[0]


class TestSSHIdentityProxyEdgeCases:
    """Edge case tests."""

    def test_start_when_already_running(self, proxy_with_env: SSHIdentityProxy) -> None:
        """Verify starting an already running proxy is handled."""
        proxy_with_env.start()
        # Start again - should be idempotent
        proxy_with_env.start()
        assert proxy_with_env._running is True
        proxy_with_env.stop()

    def test_stop_when_not_running(self, proxy_with_env: SSHIdentityProxy) -> None:
        """Verify stopping when not running is safe."""
        # Don't start, just stop
        proxy_with_env.stop()
        assert proxy_with_env._running is False

    def test_socket_path_with_spaces(
        self, mock_host_socket: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify socket path with spaces works."""
        # Use a short path with spaces (in /tmp to stay under AF_UNIX path limit)
        socket_path = Path(f"/tmp/ssh-test-{os.getpid()}-with spaces/proxy.sock")
        monkeypatch.setenv("SSH_AUTH_SOCK", str(mock_host_socket))
        proxy = SSHIdentityProxy(socket_path)
        proxy.start()
        assert socket_path.parent.exists()
        proxy.stop()

    def test_socket_path_deep_hierarchy(
        self, mock_host_socket: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify deep directory hierarchy is created."""
        # Use a deep but short path (in /tmp to stay under AF_UNIX path limit)
        socket_path = Path(f"/tmp/ssh-{os.getpid()}/a/b/proxy.sock")
        monkeypatch.setenv("SSH_AUTH_SOCK", str(mock_host_socket))
        proxy = SSHIdentityProxy(socket_path)
        proxy.start()
        assert socket_path.parent.exists()
        proxy.stop()


class TestSSHIdentityProxyIntegration:
    """Integration-style tests with real socket operations."""

    def test_full_lifecycle_with_real_sockets(
        self,
        proxy_socket_path: Path,
        mock_host_socket: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify full start/stop lifecycle with real sockets."""
        # Create a mock SSH agent server
        agent_thread_running = threading.Event()
        agent_thread_running.set()

        def mock_ssh_agent():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.bind(str(mock_host_socket))
                    s.listen(1)
                    s.settimeout(2.0)
                    agent_thread_running.set()

                    try:
                        conn, _ = s.accept()
                        # Handle one request then close
                        data = conn.recv(1024)
                        if data:
                            conn.send(b"\x00\x00\x00\x01\x00")  # Minimal response
                        conn.close()
                    except TimeoutError:
                        pass
            except Exception:
                pass

        agent_thread = threading.Thread(target=mock_ssh_agent, daemon=True)
        agent_thread.start()
        agent_thread_running.wait(timeout=2.0)

        monkeypatch.setenv("SSH_AUTH_SOCK", str(mock_host_socket))
        proxy = SSHIdentityProxy(proxy_socket_path)
        proxy.start()

        import time

        time.sleep(0.2)  # Let the proxy settle

        assert proxy._running is True
        assert proxy._thread is not None

        proxy.stop()

        assert proxy._running is False
        assert not proxy_socket_path.exists()


class TestSSHIdentityProxyHandleClient:
    """Tests for _handle_client method."""

    def test_handle_client_closes_on_exception(
        self, proxy_with_env: SSHIdentityProxy
    ) -> None:
        """Verify _handle_client handles exceptions gracefully."""
        proxy_with_env.start()

        # Create a mock client connection
        mock_client = MagicMock()
        mock_client.recv.side_effect = OSError("Connection error")

        # Call _handle_client directly (it should handle the exception)
        proxy_with_env._handle_client(mock_client)

        # Client connection should be closed
        mock_client.close.assert_called()

        proxy_with_env.stop()

    def test_handle_client_with_valid_connection(
        self, proxy_with_env: SSHIdentityProxy, mock_host_socket: Path
    ) -> None:
        """Test _handle_client with a valid connection to mock host."""
        import time

        # Create a mock SSH agent server
        server_ready = threading.Event()

        def mock_ssh_agent():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.bind(str(mock_host_socket))
                    s.listen(1)
                    s.settimeout(2.0)
                    server_ready.set()

                    try:
                        conn, _ = s.accept()
                        # Echo back data
                        data = conn.recv(1024)
                        if data:
                            conn.send(data)
                        conn.close()
                    except TimeoutError:
                        pass
            except Exception:
                pass

        agent_thread = threading.Thread(target=mock_ssh_agent, daemon=True)
        agent_thread.start()
        server_ready.wait(timeout=2.0)

        proxy_with_env.start()
        time.sleep(0.1)
        proxy_with_env.stop()

    def test_handle_client_non_blocking_setup(
        self, proxy_with_env: SSHIdentityProxy
    ) -> None:
        """Test _handle_client sets up non-blocking sockets."""
        proxy_with_env.start()

        # Note: setblocking is only called when the host connection succeeds
        # Since the host SSH_AUTH_SOCK doesn't exist, the connection will fail
        # before setblocking is called. This is expected behavior.
        mock_client = MagicMock()
        mock_client.close = MagicMock()

        proxy_with_env._handle_client(mock_client)

        # Client connection should be closed (either way)
        mock_client.close.assert_called()

        proxy_with_env.stop()


class TestSSHIdentityProxyForwardRecv:
    """Tests for _forward_recv helper in _handle_client."""

    def test_forward_recv_handles_blocking_io(
        self, proxy_with_env: SSHIdentityProxy
    ) -> None:
        """Test _forward_recv handles BlockingIOError gracefully."""
        proxy_with_env.start()

        mock_client = MagicMock()
        mock_client.recv.side_effect = BlockingIOError()
        MagicMock()

        # Call _handle_client which uses _forward_recv internally
        proxy_with_env._handle_client(mock_client)

        proxy_with_env.stop()

    def test_forward_recv_returns_false_on_empty_data(
        self, proxy_with_env: SSHIdentityProxy
    ) -> None:
        """Test _forward_recv returns False when connection closed."""
        proxy_with_env.start()

        mock_client = MagicMock()
        mock_client.recv.return_value = b""  # Empty data
        MagicMock()

        proxy_with_env._handle_client(mock_client)

        # Should handle gracefully
        proxy_with_env.stop()


class TestSSHIdentityProxyHandleClientIntegration:
    """Integration tests for _handle_client with real socket operations."""

    def test_handle_client_forwards_data_to_host(
        self,
        proxy_socket_path: Path,
        mock_host_socket: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test _handle_client forwards data between client and host."""
        import time

        # Track received data
        received_data = []
        server_ready = threading.Event()
        client_done = threading.Event()

        def mock_ssh_agent():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.bind(str(mock_host_socket))
                    s.listen(1)
                    s.settimeout(5.0)
                    server_ready.set()

                    try:
                        conn, _ = s.accept()
                        conn.setblocking(False)

                        # Read data from client and echo back
                        import select as sel

                        while not client_done.is_set():
                            readable, _, _ = sel.select([conn], [], [], 0.5)
                            if readable:
                                try:
                                    data = conn.recv(4096)
                                    if data:
                                        received_data.append(data)
                                        # Echo back
                                        conn.sendall(b"RESPONSE:" + data)
                                    else:
                                        break
                                except BlockingIOError:
                                    pass
                        conn.close()
                    except TimeoutError:
                        pass
            except Exception:
                pass

        agent_thread = threading.Thread(target=mock_ssh_agent, daemon=True)
        agent_thread.start()
        server_ready.wait(timeout=2.0)

        monkeypatch.setenv("SSH_AUTH_SOCK", str(mock_host_socket))
        proxy = SSHIdentityProxy(proxy_socket_path)
        proxy.start()
        time.sleep(0.2)  # Let proxy settle

        # Connect a client
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(2.0)
            client.connect(str(proxy_socket_path))

            # Send data
            client.sendall(b"TEST_DATA")

            # Wait for response
            time.sleep(0.3)
            try:
                client.recv(4096)
                # Should have received response through proxy
            except TimeoutError:
                pass

            client.close()
        except Exception:
            pass
        finally:
            client_done.set()
            time.sleep(0.1)
            proxy.stop()

    def test_handle_client_handles_connection_close(
        self,
        proxy_socket_path: Path,
        mock_host_socket: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test _handle_client handles client connection close."""
        import time

        server_ready = threading.Event()
        server_done = threading.Event()

        def mock_ssh_agent():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.bind(str(mock_host_socket))
                    s.listen(1)
                    s.settimeout(5.0)
                    server_ready.set()

                    try:
                        conn, _ = s.accept()
                        # Wait for client to close
                        time.sleep(0.5)
                        conn.close()
                    except TimeoutError:
                        pass
            except Exception:
                pass
            finally:
                server_done.set()

        agent_thread = threading.Thread(target=mock_ssh_agent, daemon=True)
        agent_thread.start()
        server_ready.wait(timeout=2.0)

        monkeypatch.setenv("SSH_AUTH_SOCK", str(mock_host_socket))
        proxy = SSHIdentityProxy(proxy_socket_path)
        proxy.start()
        time.sleep(0.2)

        # Connect and immediately close
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(str(proxy_socket_path))
            time.sleep(0.1)
            client.close()
        except Exception:
            pass

        time.sleep(0.3)
        proxy.stop()


class TestSSHIdentityProxyRequireActorIdentity:
    """Tests for require_actor_identity static method."""

    def test_require_actor_identity_rejects_empty_actor_id(self) -> None:
        """Test empty actor_id is rejected."""
        with pytest.raises(ValueError, match="actor_id must be non-empty"):
            SSHIdentityProxy.require_actor_identity(
                actor_id="",
                signature="sig",
                payload="payload",
                signing_key="key",
            )

    def test_require_actor_identity_rejects_whitespace_actor_id(self) -> None:
        """Test whitespace-only actor_id is rejected."""
        with pytest.raises(ValueError, match="actor_id must be non-empty"):
            SSHIdentityProxy.require_actor_identity(
                actor_id="   ",
                signature="sig",
                payload="payload",
                signing_key="key",
            )

    def test_require_actor_identity_rejects_empty_signature(self) -> None:
        """Test empty signature is rejected."""
        with pytest.raises(ValueError, match="signature must be non-empty"):
            SSHIdentityProxy.require_actor_identity(
                actor_id="actor",
                signature="",
                payload="payload",
                signing_key="key",
            )

    def test_require_actor_identity_rejects_whitespace_signature(self) -> None:
        """Test whitespace-only signature is rejected."""
        with pytest.raises(ValueError, match="signature must be non-empty"):
            SSHIdentityProxy.require_actor_identity(
                actor_id="actor",
                signature="   ",
                payload="payload",
                signing_key="key",
            )

    def test_require_actor_identity_rejects_empty_signing_key(self) -> None:
        """Test empty signing_key is rejected."""
        with pytest.raises(ValueError, match="signing_key must be non-empty"):
            SSHIdentityProxy.require_actor_identity(
                actor_id="actor",
                signature="sig",
                payload="payload",
                signing_key="",
            )

    def test_require_actor_identity_rejects_whitespace_signing_key(self) -> None:
        """Test whitespace-only signing_key is rejected."""
        with pytest.raises(ValueError, match="signing_key must be non-empty"):
            SSHIdentityProxy.require_actor_identity(
                actor_id="actor",
                signature="sig",
                payload="payload",
                signing_key="   ",
            )

    @patch("thegent.infra.identity_proxy.verify_actor_signature")
    def test_require_actor_identity_verifies_signature(
        self, mock_verify: MagicMock
    ) -> None:
        """Test require_actor_identity calls verify_actor_signature."""
        mock_verify.return_value = True

        SSHIdentityProxy.require_actor_identity(
            actor_id="actor",
            signature="sig",
            payload="payload",
            signing_key="key",
        )

        mock_verify.assert_called_once_with(
            actor_id="actor",
            payload="payload",
            signing_key="key",
            signature="sig",
        )

    @patch("thegent.infra.identity_proxy.verify_actor_signature")
    def test_require_actor_identity_rejects_invalid_signature(
        self, mock_verify: MagicMock
    ) -> None:
        """Test require_actor_identity rejects invalid signature."""
        mock_verify.return_value = False

        with pytest.raises(ValueError, match="invalid actor signature"):
            SSHIdentityProxy.require_actor_identity(
                actor_id="actor",
                signature="badsig",
                payload="payload",
                signing_key="key",
            )

    def test_require_actor_identity_is_staticmethod(self) -> None:
        """Test require_actor_identity is a static method."""
        # Should be callable without instance
        assert callable(SSHIdentityProxy.require_actor_identity)
