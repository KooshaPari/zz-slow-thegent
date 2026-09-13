"""Tests for virtual desktop automation module."""

import platform
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from thegent.automation.virtual_desktop import (
    DesktopConfig,
    DesktopSession,
    DesktopState,
    InputEvent,
    ScreenFrame,
    VirtualDesktopManager,
    get_desktop_manager,
)


class TestDesktopConfig:
    """Tests for DesktopConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DesktopConfig(agent_id="test-agent")

        assert config.agent_id == "test-agent"
        assert config.resolution == (1920, 1080)
        assert config.color_depth == 32
        assert config.dpi == 96
        assert config.memory_mb == 2048
        assert config.gpu_enabled is True
        assert config.audio_enabled is False
        assert config.network_bridge is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = DesktopConfig(
            agent_id="test-agent",
            resolution=(2560, 1440),
            memory_mb=4096,
            gpu_enabled=False,
        )

        assert config.resolution == (2560, 1440)
        assert config.memory_mb == 4096
        assert config.gpu_enabled is False


class TestInputEvent:
    """Tests for InputEvent."""

    def test_mouse_move_event(self):
        """Test mouse move event creation."""
        event = InputEvent(event_type="mouse_move", x=100, y=200)

        assert event.event_type == "mouse_move"
        assert event.x == 100
        assert event.y == 200

    def test_key_event(self):
        """Test key event creation."""
        event = InputEvent(event_type="key_down", key_code=65, key_char="a")

        assert event.event_type == "key_down"
        assert event.key_code == 65
        assert event.key_char == "a"

    def test_mouse_wheel_event(self):
        """Test mouse wheel event."""
        event = InputEvent(event_type="mouse_wheel", delta=120)

        assert event.event_type == "mouse_wheel"
        assert event.delta == 120


class TestScreenFrame:
    """Tests for ScreenFrame."""

    def test_frame_creation(self):
        """Test screen frame creation."""
        frame = ScreenFrame(
            timestamp=1234567890.0,
            width=1920,
            height=1080,
            bytes_per_pixel=4,
            data=b"x" * (1920 * 1080 * 4),
        )

        assert frame.width == 1920
        assert frame.height == 1080
        assert frame.size_bytes == 1920 * 1080 * 4

    def test_latency_calculation(self):
        """Test latency calculation."""
        frame = ScreenFrame(
            timestamp=time.time(),
            width=1920,
            height=1080,
            bytes_per_pixel=4,
            data=b"x" * 100,
        )

        # Should be very small latency since we just created it
        assert frame.latency_ms < 100


class TestDesktopSession:
    """Tests for DesktopSession."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        provider = MagicMock()
        provider.name = "test"
        provider.supports_gpu = True
        provider.capture_screen = AsyncMock(
            return_value=ScreenFrame(
                timestamp=0,
                width=1920,
                height=1080,
                bytes_per_pixel=4,
                data=b"x" * 100,
            )
        )
        provider.inject_input = AsyncMock(return_value=True)
        return provider

    @pytest.mark.asyncio
    async def test_session_creation(self, mock_provider):
        """Test session creation."""
        config = DesktopConfig(agent_id="test-agent")
        session = DesktopSession(
            agent_id="test-agent",
            desktop_id="desktop-1",
            provider=mock_provider,
            config=config,
        )

        assert session.agent_id == "test-agent"
        assert session.desktop_id == "desktop-1"
        assert session.state == DesktopState.CREATING

    @pytest.mark.asyncio
    async def test_session_start_stop(self, mock_provider):
        """Test session start and stop."""
        config = DesktopConfig(agent_id="test-agent")
        session = DesktopSession(
            agent_id="test-agent",
            desktop_id="desktop-1",
            provider=mock_provider,
            config=config,
        )

        await session.start()
        assert session.state == DesktopState.RUNNING

        await session.stop()
        assert session.state == DesktopState.STOPPED

    @pytest.mark.asyncio
    async def test_session_capture(self, mock_provider):
        """Test screen capture."""
        config = DesktopConfig(agent_id="test-agent")
        session = DesktopSession(
            agent_id="test-agent",
            desktop_id="desktop-1",
            provider=mock_provider,
            config=config,
        )

        frame = await session.capture()

        assert frame.width == 1920
        assert frame.height == 1080
        mock_provider.capture_screen.assert_called_once_with("desktop-1")

    @pytest.mark.asyncio
    async def test_session_inject(self, mock_provider):
        """Test input injection."""
        config = DesktopConfig(agent_id="test-agent")
        session = DesktopSession(
            agent_id="test-agent",
            desktop_id="desktop-1",
            provider=mock_provider,
            config=config,
        )

        event = InputEvent(event_type="mouse_move", x=100, y=200)
        result = await session.inject(event)

        assert result is True
        mock_provider.inject_input.assert_called_once_with("desktop-1", event)

    @pytest.mark.asyncio
    async def test_session_click(self, mock_provider):
        """Test click helper."""
        config = DesktopConfig(agent_id="test-agent")
        session = DesktopSession(
            agent_id="test-agent",
            desktop_id="desktop-1",
            provider=mock_provider,
            config=config,
        )

        await session.click(100, 200)

        # Should inject 3 events: move, down, up
        assert mock_provider.inject_input.call_count == 3


class TestVirtualDesktopManager:
    """Tests for VirtualDesktopManager."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test manager gets the right provider."""
        # This test just verifies the manager can be created
        # The actual provider depends on the platform
        manager = VirtualDesktopManager()

        assert manager._provider is not None
        assert manager._provider.name in ["windows", "linux", "darwin"]

    @pytest.mark.asyncio
    async def test_get_session_not_exists(self):
        """Test getting non-existent session returns None."""
        manager = VirtualDesktopManager()

        session = await manager.get_session("non-existent")

        assert session is None

    @pytest.mark.asyncio
    async def test_manager_uses_unsupported_platform_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """Unsupported platforms should use a concrete fallback provider."""
        monkeypatch.setattr(platform, "system", lambda: "Plan9")
        manager = VirtualDesktopManager()

        assert manager._provider.name == "unsupported:plan9"
        session = await manager.create_session("agent-fallback")

        frame = await session.capture()
        assert frame.width == 1920
        assert frame.height == 1080
        assert frame.size_bytes == 1920 * 1080 * 4
        assert await session.inject(InputEvent(event_type="mouse_move", x=10, y=10))
        assert not await session.inject(InputEvent(event_type="unknown", x=10, y=10))


def test_get_desktop_manager_singleton():
    """Test that get_desktop_manager returns singleton."""
    # Need to reset the global manager first
    import thegent.automation.virtual_desktop as vd

    original_manager = vd._manager
    vd._manager = None

    try:
        manager1 = get_desktop_manager()
        manager2 = get_desktop_manager()

        assert manager1 is manager2
    finally:
        vd._manager = original_manager
