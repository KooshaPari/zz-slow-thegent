"""PTY holder for headless interactive sessions (WP-9007)."""

import os
import pty
import select
import socket
import subprocess
import threading
from pathlib import Path
from typing import cast


class PTYHolder:
    """Wraps a process in a PTY and exposes it via a Unix socket."""

    def __init__(
        self,
        socket_path: Path,
        cmd: list[str],
        cwd: str | None = None,
        env: dict | None = None,
    ) -> None:
        self.socket_path = socket_path
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.master_fd: int | None = None
        self.proc: subprocess.Popen | None = None
        self.server_sock: socket.socket | None = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the process and the proxy server."""
        self.master_fd, slave_fd = pty.openpty()

        # Start child process
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=self.cwd,
            env=self.env,
            start_new_session=True,
        )
        os.close(slave_fd)

        # Start Unix socket server
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        self.server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_sock.bind(str(self.socket_path))
        self.server_sock.listen(1)
        self.server_sock.settimeout(1.0)

        # Start proxy threads
        threading.Thread(target=self._socket_listener, daemon=True).start()
        threading.Thread(target=self._pty_to_stdout, daemon=True).start()

    def _socket_listener(self):
        """Wait for an attachment via the Unix socket."""
        while not self._stop_event.is_set():
            try:
                conn, _ = self.server_sock.accept()
                self._handle_connection(conn)
            except TimeoutError:  # noqa: PERF203 - intentional per-item error handling
                continue
            except Exception:
                break

    def _handle_connection(self, conn: socket.socket):
        """Proxy between the socket and the PTY master."""
        conn.setblocking(False)
        assert self.master_fd is not None, "PTY master_fd must be set before handling connections"
        master_fd: int = cast("int", self.master_fd)

        while not self._stop_event.is_set():
            r, _, _ = select.select([master_fd, conn], [], [], 0.1)
            if not r:
                if self.proc.poll() is not None:
                    break
                continue

            if master_fd in r:
                data = os.read(master_fd, 1024)
                if not data:
                    break
                conn.sendall(data)

            if conn in r:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    os.write(master_fd, data)
                except Exception:
                    break
        conn.close()

    def _pty_to_stdout(self):
        """Mirror PTY output to the holder's stdout (so thegent logs work)."""
        import sys

        assert self.master_fd is not None, "PTY master_fd must be set before mirroring stdout"
        master_fd: int = cast("int", self.master_fd)

        while not self._stop_event.is_set():
            try:
                # Use a small timeout or non-blocking read to allow checking stop_event
                # but os.read on PTY master is usually blocking.
                # We can use select here too.
                r, _, _ = select.select([master_fd], [], [], 0.5)
                if not r:
                    if self.proc.poll() is not None:
                        break
                    continue

                data = os.read(master_fd, 1024)
                if not data:
                    break
                # Write to stdout so the launcher (bg_impl) captures it into the log file
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            except Exception:
                break

    def stop(self):
        self._stop_event.set()
        if self.server_sock:
            self.server_sock.close()
        if self.socket_path.exists():
            self.socket_path.unlink()
        if self.proc:
            self.proc.terminate()


def wrap_with_holdpty(cmd: list[str], session_id: str, socket_path: Path) -> list[str]:
    """Return a command that runs the original command via holdpty holder."""
    # Since we need a long-running holder, we might want a separate CLI command
    # thegent internal holdpty --socket PATH -- cmd...
    return [
        "python3",
        "-m",
        "thegent.utils.holdpty",
        "--socket",
        str(socket_path),
        "--session-id",
        session_id,
        "--",
        *cmd,
    ]
