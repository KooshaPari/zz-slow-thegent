"""Tests for SHM system wrapper (BKM-05).

Tests cover SHMSystem singleton, native extension handling,
fallback behavior, and all circuit breaker / XP methods.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.state.shm import SHMSystem, get_shm_system


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before and after each test."""
    SHMSystem._instance = None
    SHMSystem._interface = None
    yield
    SHMSystem._instance = None
    SHMSystem._interface = None


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    """Create a temporary session directory."""
    return tmp_path / "session"


class TestSHMSystemSingleton:
    """Tests for singleton pattern."""

    def test_singleton_returns_same_instance(self, session_dir: Path) -> None:
        """Verify singleton returns the same instance."""
        instance1 = SHMSystem(session_dir)
        instance2 = SHMSystem(session_dir / "other")

        assert instance1 is instance2

    def test_singleton_ignores_different_session_dir(self, session_dir: Path) -> None:
        """Verify singleton ignores subsequent different session_dir."""
        instance1 = SHMSystem(session_dir)
        instance2 = SHMSystem(session_dir / "different")

        # Both should be the same instance
        assert instance1 is instance2
        # The session_dir should be from the first call
        assert instance1.session_dir == session_dir


class TestSHMSystemInit:
    """Tests for SHMSystem initialization."""

    def test_creates_shm_path(self, session_dir: Path) -> None:
        """Verify shm_path is set correctly."""
        shm = SHMSystem(session_dir)
        assert shm.session_dir == session_dir
        assert shm.shm_path == session_dir / "state.shm"

    @patch("thegent.config.ThegentSettings")
    def test_native_disabled_by_default(self, mock_settings: MagicMock, session_dir: Path) -> None:
        """Verify native SHM is disabled when settings say so."""
        mock_settings.return_value.use_native_shm = False
        shm = SHMSystem(session_dir)

        assert shm.use_native is False
        assert shm._interface is None

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_but_no_extension(self, mock_settings: MagicMock, session_dir: Path) -> None:
        """Verify fallback when native extension is not installed (ImportError)."""
        mock_settings.return_value.use_native_shm = True

        # Ensure the module isn't cached
        original = sys.modules.get("thegent_shm")
        sys.modules.pop("thegent_shm", None)

        try:
            shm = SHMSystem(session_dir)
            assert shm._interface is None
        finally:
            if original is not None:
                sys.modules["thegent_shm"] = original

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_with_exception(self, mock_settings: MagicMock, session_dir: Path) -> None:
        """Verify exception during native init is caught."""
        mock_settings.return_value.use_native_shm = True

        # Create a mock module that raises an exception
        mock_shm_module = MagicMock()
        mock_shm_module.py_init_shm.side_effect = RuntimeError("init failed")

        original = sys.modules.get("thegent_shm")
        try:
            sys.modules["thegent_shm"] = mock_shm_module
            shm = SHMSystem(session_dir)
            assert shm._interface is None
        finally:
            if original is not None:
                sys.modules["thegent_shm"] = original
            else:
                sys.modules.pop("thegent_shm", None)

    @patch("thegent.config.ThegentSettings")
    def test_native_enabled_success_path(self, mock_settings: MagicMock, session_dir: Path) -> None:
        """Verify native SHM is initialized when extension is available."""
        mock_settings.return_value.use_native_shm = True

        # Create mock module and interface
        mock_interface = MagicMock()
        mock_shm_module = MagicMock()
        mock_shm_module.SHMInterface.return_value = mock_interface
        mock_shm_module.py_init_shm = MagicMock()

        original = sys.modules.get("thegent_shm")
        try:
            sys.modules["thegent_shm"] = mock_shm_module
            shm = SHMSystem(session_dir)
            mock_shm_module.py_init_shm.assert_called_once()
            mock_shm_module.SHMInterface.assert_called_once()
            assert shm._interface is mock_interface
        finally:
            if original is not None:
                sys.modules["thegent_shm"] = original
            else:
                sys.modules.pop("thegent_shm", None)


class TestSHMSystemIsNativeActive:
    """Tests for is_native_active method."""

    def test_returns_false_when_no_interface(self, session_dir: Path) -> None:
        """Verify False when interface is None."""
        shm = SHMSystem(session_dir)
        assert shm.is_native_active() is False

    def test_returns_true_when_interface_exists(self, session_dir: Path) -> None:
        """Verify True when interface is set."""
        shm = SHMSystem(session_dir)
        shm._interface = MagicMock()

        assert shm.is_native_active() is True


class TestSHMSystemRecordFailure:
    """Tests for record_failure method."""

    def test_noop_without_interface(self, session_dir: Path) -> None:
        """Verify no-op when interface is None."""
        shm = SHMSystem(session_dir)
        # Should not raise
        shm.record_failure("target-1", "agent")

    def test_calls_interface_with_agent_category(self, session_dir: Path) -> None:
        """Verify interface is called with correct category index."""
        shm = SHMSystem(session_dir)
        mock_interface = MagicMock()
        shm._interface = mock_interface

        shm.record_failure("target-1", "agent")

        mock_interface.record_failure.assert_called_once_with("target-1", 0)

    def test_calls_interface_with_non_agent_category(self, session_dir: Path) -> None:
        """Verify non-agent category uses index 1."""
        shm = SHMSystem(session_dir)
        mock_interface = MagicMock()
        shm._interface = mock_interface

        shm.record_failure("target-1", "other")

        mock_interface.record_failure.assert_called_once_with("target-1", 1)


class TestSHMSystemIsOpen:
    """Tests for is_open method (circuit breaker)."""

    def test_returns_false_without_interface(self, session_dir: Path) -> None:
        """Verify False when interface is None."""
        shm = SHMSystem(session_dir)
        assert shm.is_open("target-1") is False

    def test_calls_interface_with_agent_category(self, session_dir: Path) -> None:
        """Verify interface is called with correct parameters."""
        shm = SHMSystem(session_dir)
        mock_interface = MagicMock()
        mock_interface.is_open.return_value = True
        shm._interface = mock_interface

        result = shm.is_open(
            target="target-1",
            category="agent",
            threshold=3,
            window_s=60,
            recovery_s=30,
        )

        assert result is True
        mock_interface.is_open.assert_called_once_with("target-1", 0, 3, 60, 30)

    def test_calls_interface_with_non_agent_category(self, session_dir: Path) -> None:
        """Verify non-agent category uses index 1."""
        shm = SHMSystem(session_dir)
        mock_interface = MagicMock()
        mock_interface.is_open.return_value = False
        shm._interface = mock_interface

        result = shm.is_open("target-1", category="other")

        assert result is False
        mock_interface.is_open.assert_called_once_with("target-1", 1, 5, 300, 60)


class TestSHMSystemAwardXP:
    """Tests for award_xp method."""

    def test_noop_without_interface(self, session_dir: Path) -> None:
        """Verify no-op when interface is None."""
        shm = SHMSystem(session_dir)
        # Should not raise
        shm.award_xp(100)

    def test_calls_interface(self, session_dir: Path) -> None:
        """Verify interface is called."""
        shm = SHMSystem(session_dir)
        mock_interface = MagicMock()
        shm._interface = mock_interface

        shm.award_xp(150)

        mock_interface.award_xp.assert_called_once_with(150)


class TestSHMSystemGetXPState:
    """Tests for get_xp_state method."""

    def test_returns_none_without_interface(self, session_dir: Path) -> None:
        """Verify None when interface is None."""
        shm = SHMSystem(session_dir)
        assert shm.get_xp_state() is None

    def test_returns_interface_result(self, session_dir: Path) -> None:
        """Verify interface result is returned."""
        shm = SHMSystem(session_dir)
        mock_interface = MagicMock()
        mock_interface.get_xp_state.return_value = {"level": 5, "xp": 1000}
        shm._interface = mock_interface

        result = shm.get_xp_state()

        assert result == {"level": 5, "xp": 1000}


class TestSHMSystemSetLevel:
    """Tests for set_level method."""

    def test_noop_without_interface(self, session_dir: Path) -> None:
        """Verify no-op when interface is None."""
        shm = SHMSystem(session_dir)
        # Should not raise
        shm.set_level(10)

    def test_calls_interface(self, session_dir: Path) -> None:
        """Verify interface is called."""
        shm = SHMSystem(session_dir)
        mock_interface = MagicMock()
        shm._interface = mock_interface

        shm.set_level(25)

        mock_interface.set_level.assert_called_once_with(25)


class TestGetSHMSystem:
    """Tests for get_shm_system factory function."""

    def test_returns_shm_instance(self, session_dir: Path) -> None:
        """Verify factory returns SHMSystem instance."""
        result = get_shm_system(session_dir)
        assert isinstance(result, SHMSystem)

    def test_returns_singleton(self, session_dir: Path) -> None:
        """Verify factory returns the same singleton instance."""
        result1 = get_shm_system(session_dir)
        result2 = get_shm_system(session_dir / "other")

        assert result1 is result2
