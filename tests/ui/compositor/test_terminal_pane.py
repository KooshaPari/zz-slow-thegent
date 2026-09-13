"""Tests for the TerminalPane widget (P1.3)."""

from thegent.ui.compositor import TerminalPane


class TestTerminalPaneInitialization:
    """Tests for TerminalPane initialization (P1.3 AC-1)."""

    def test_terminal_pane_initialization(self) -> None:
        """Test that a TerminalPane initializes correctly."""
        pane = TerminalPane("test-pane", "/tmp")
        assert pane.pane_id == "test-pane"
        assert pane.working_dir == "/tmp"
        assert pane.process is None
        assert pane.pty_master is None

    def test_terminal_pane_default_dir(self) -> None:
        """Test that TerminalPane uses current directory by default."""
        pane = TerminalPane("test-pane")
        assert pane.working_dir == "."

    def test_terminal_pane_with_name(self) -> None:
        """Test TerminalPane with display name."""
        pane = TerminalPane("test-pane", name="My Pane")
        assert pane.pane_id == "test-pane"

    def test_terminal_pane_placeholder_render(self) -> None:
        """Test that TerminalPane renders placeholder content (P1.3 AC-3)."""
        pane = TerminalPane("test-pane", "/tmp")
        rendered = pane._render_placeholder()
        assert "test-pane" in rendered
        assert "/tmp" in rendered


class TestTerminalPaneShellSpawning:
    """Tests for PTY allocation and shell spawning (P1.3 AC-2)."""

    def test_terminal_pane_spawn_shell_basic(self) -> None:
        """Test basic shell spawning with PTY (P1.3 AC-2)."""
        pane = TerminalPane("test-pane", "/tmp")
        pane.spawn_shell("/bin/sh")
        assert pane.process is not None
        assert pane.process.pid > 0
        pane.close()
        assert pane.process is None

    def test_terminal_pane_spawn_shell_nonexistent(self) -> None:
        """Test that spawning nonexistent shell falls back gracefully."""
        pane = TerminalPane("test-pane", "/tmp")
        # Should not raise, but should use fallback shell
        pane.spawn_shell("/nonexistent/shell")
        assert pane.process is not None  # Should spawn fallback shell
        pane.close()

    def test_terminal_pane_spawn_shell_invalid_cwd(self) -> None:
        """Test that invalid working directory is handled gracefully."""
        pane = TerminalPane("test-pane", "/nonexistent/dir")
        # Should not raise, should use home directory
        pane.spawn_shell("/bin/sh")
        assert pane.process is not None
        pane.close()

    def test_terminal_pane_close_without_process(self) -> None:
        """Test that close without process doesn't raise errors (P1.3 AC-4)."""
        pane = TerminalPane("test-pane")
        pane.close()  # Should not raise
        assert pane.process is None
        assert pane.pty_master is None


class TestTerminalPaneCleanup:
    """Tests for cleanup and resource management (P1.3 AC-4)."""

    def test_terminal_pane_cleanup_process(self) -> None:
        """Test that cleanup terminates process cleanly."""
        pane = TerminalPane("test-pane", "/tmp")
        pane.spawn_shell("/bin/sh")
        pane.close()
        # Should have cleaned up
        assert pane.process is None
        assert pane.pty_master is None

    def test_terminal_pane_multiple_close_calls(self) -> None:
        """Test that multiple close calls don't raise errors."""
        pane = TerminalPane("test-pane", "/tmp")
        pane.spawn_shell("/bin/sh")
        pane.close()
        pane.close()  # Second call should not raise
        assert True  # Successful if no exception
