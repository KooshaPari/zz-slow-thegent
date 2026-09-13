"""Tests for Playwright browser recording and automation utilities.

Tests cover:
- Configuration validation
- Recorder initialization and lifecycle
- Interaction methods
- Feature recording
- Result serialization
"""

import tempfile
from pathlib import Path

import orjson as json
import pytest  # type: ignore
from pydantic_core import ValidationError

from thegent.doc_tools import (  # type: ignore
    PlaywrightRecorder,
    RecordingConfig,
    RecordingResult,
    ScreenshotOptions,
    VideoRecordingOptions,
)


def _mock_playwright(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakePage:
        async def close(self) -> None:
            return None

    class _FakeContext:
        def set_default_timeout(self, _value: int) -> None:
            return None

        def set_default_navigation_timeout(self, _value: int) -> None:
            return None

        async def new_page(self) -> _FakePage:
            return _FakePage()

        async def close(self) -> None:
            return None

    class _FakeBrowser:
        async def new_context(self, **_kwargs) -> _FakeContext:
            return _FakeContext()

        async def close(self) -> None:
            return None

    class _FakeBrowserType:
        async def launch(self, **_kwargs) -> _FakeBrowser:
            return _FakeBrowser()

    class _FakePlaywright:
        chromium = _FakeBrowserType()
        firefox = _FakeBrowserType()
        webkit = _FakeBrowserType()

        async def stop(self) -> None:
            return None

    class _FakeAsyncPlaywright:
        async def start(self) -> _FakePlaywright:
            return _FakePlaywright()

    monkeypatch.setattr("thegent.doc_tools.playwright_recorder.async_playwright", lambda: _FakeAsyncPlaywright())


class TestRecordingConfig:
    """Test RecordingConfig model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = RecordingConfig()

        assert config.base_url == "http://localhost:5173"
        assert config.browser == "chromium"
        assert config.headless is False
        assert config.viewport_width == 1280
        assert config.viewport_height == 720
        assert config.locale == "en-US"
        assert config.timezone_id == "America/New_York"

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = RecordingConfig(
            base_url="http://custom.local",
            browser="firefox",
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
        )

        assert config.base_url == "http://custom.local"
        assert config.browser == "firefox"
        assert config.headless is True
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080

    def test_invalid_browser(self) -> None:
        """Test that invalid browser raises validation error."""
        with pytest.raises(ValueError, match="Unknown browser"):
            RecordingConfig(browser="invalid_browser")

    def test_video_config(self) -> None:
        """Test video recording configuration."""
        config = RecordingConfig()
        assert isinstance(config.video, VideoRecordingOptions)
        assert config.video.fps == 30
        assert config.video.bitrate == 5000
        assert config.video.size["width"] == 1280
        assert config.video.size["height"] == 720

    def test_screenshot_config(self) -> None:
        """Test screenshot configuration."""
        config = RecordingConfig()
        assert isinstance(config.screenshot, ScreenshotOptions)
        assert config.screenshot.full_page is False
        assert config.screenshot.quality == 95

    def test_output_dir_creation(self) -> None:
        """Test that output directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "recordings"
            assert not output_dir.exists()
            _ = RecordingConfig(output_dir=output_dir)  # noqa: F841

            assert output_dir.exists()
            assert output_dir.is_dir()

    def test_config_validation(self) -> None:
        """Test config field validation."""
        # Valid quality
        ScreenshotOptions(quality=50)

        # Invalid quality
        with pytest.raises(ValueError):
            ScreenshotOptions(quality=0)
        with pytest.raises(ValueError):
            ScreenshotOptions(quality=101)

        # Valid FPS
        VideoRecordingOptions(fps=30)

        # Invalid FPS
        with pytest.raises(ValueError):
            VideoRecordingOptions(fps=10)


class TestRecordingResult:
    """Test RecordingResult dataclass."""

    def test_successful_result(self) -> None:
        """Test successful recording result."""
        result = RecordingResult(
            success=True,
            video_path=Path("recording.webm"),
            screenshot_paths=[Path("screenshot.png")],
            metadata={"feature": "test"},
            duration=5.0,
        )

        assert result.success is True
        assert result.error is None
        assert result.duration == 5.0
        assert len(result.screenshot_paths) == 1

    def test_failed_result(self) -> None:
        """Test failed recording result."""
        result = RecordingResult(
            success=False,
            error="Connection timeout",
        )

        assert result.success is False
        assert result.error == "Connection timeout"
        assert len(result.screenshot_paths) == 0

    def test_result_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = RecordingResult(
            success=True,
            screenshot_paths=[Path("test.png")],
            metadata={"key": "value"},
            duration=2.5,
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert len(result_dict["screenshot_paths"]) == 1
        assert result_dict["screenshot_paths"][0] == "test.png"
        assert result_dict["metadata"]["key"] == "value"
        assert result_dict["duration"] == 2.5

    def test_result_to_json(self) -> None:
        """Test serializing result to JSON."""
        result = RecordingResult(
            success=True,
            metadata={"feature": "demo"},
        )

        json_str = result.to_json()
        parsed = json.loads(json_str)

        assert parsed["success"] is True
        assert parsed["metadata"]["feature"] == "demo"
        assert "timestamp" in parsed

    def test_result_to_json_file(self) -> None:
        """Test saving result to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "result.json"
            result = RecordingResult(success=True, duration=1.0)

            result.to_json(output_file)

            assert output_file.exists()
            with open(output_file) as f:
                data = json.load(f)
            assert data["success"] is True

    def test_result_timestamp(self) -> None:
        """Test that result includes ISO timestamp."""
        result = RecordingResult(success=True)

        assert result.timestamp
        assert "T" in result.timestamp
        assert ":" in result.timestamp


class TestPlaywrightRecorder:
    """Test PlaywrightRecorder class (initialization only)."""

    def test_recorder_init(self) -> None:
        """Test recorder initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(output_dir=Path(tmpdir))
            recorder = PlaywrightRecorder(config)

            assert recorder.config == config
            assert recorder.browser is None
            assert recorder.page is None
            assert recorder.context is None

    def test_recorder_default_config(self) -> None:
        """Test recorder uses default config."""
        recorder = PlaywrightRecorder()

        assert recorder.config is not None
        assert recorder.config.browser == "chromium"
        assert recorder.config.base_url == "http://localhost:5173"

    def test_recorder_output_dir_created(self) -> None:
        """Test that recorder creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_recordings"
            config = RecordingConfig(output_dir=output_dir)
            PlaywrightRecorder(config)

            assert output_dir.exists()

    @pytest.mark.asyncio
    async def test_recorder_context_manager(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test recorder as async context manager."""
        _mock_playwright(monkeypatch)
        config = RecordingConfig(headless=True)

        async with PlaywrightRecorder(config) as recorder:
            assert recorder.browser is not None
            assert recorder.page is not None
            assert recorder.context is not None

        assert recorder.browser is not None

    @pytest.mark.asyncio
    async def test_recorder_launches_and_closes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test recorder launch and close."""
        _mock_playwright(monkeypatch)
        config = RecordingConfig(headless=True)
        recorder = PlaywrightRecorder(config)

        await recorder.launch()
        assert recorder.browser is not None
        assert recorder.page is not None

        await recorder.close()

    @pytest.mark.asyncio
    async def test_invalid_browser_type(self) -> None:
        """Test that invalid browser type raises error."""
        with pytest.raises(ValidationError, match="Unknown browser"):
            RecordingConfig(browser="unknown")


class TestInteractionMethods:
    """Test interaction methods (mock-based)."""

    @pytest.mark.asyncio
    async def test_navigate_without_launch_fails(self) -> None:
        """Test that navigate fails if browser not launched."""
        recorder = PlaywrightRecorder()

        with pytest.raises(RuntimeError, match="Browser not launched"):
            await recorder.navigate("/test")

    @pytest.mark.asyncio
    async def test_click_without_launch_fails(self) -> None:
        """Test that click fails if browser not launched."""
        recorder = PlaywrightRecorder()

        with pytest.raises(RuntimeError, match="Browser not launched"):
            await recorder.click("button")

    @pytest.mark.asyncio
    async def test_screenshot_without_launch_fails(self) -> None:
        """Test that screenshot fails if browser not launched."""
        recorder = PlaywrightRecorder()

        with pytest.raises(RuntimeError, match="Browser not launched"):
            await recorder.screenshot()

    @pytest.mark.asyncio
    async def test_wait_time(self) -> None:
        """Test wait method."""
        import time

        recorder = PlaywrightRecorder()

        start = time.time()
        await recorder.wait(100)
        elapsed = time.time() - start

        assert elapsed >= 0.09
        assert elapsed < 0.3


class TestRecordingResultIntegration:
    """Integration tests for recording results."""

    def test_multiple_screenshots_in_result(self) -> None:
        """Test result with multiple screenshots."""
        screenshots = [Path("shot1.png"), Path("shot2.png"), Path("shot3.png")]
        result = RecordingResult(
            success=True,
            screenshot_paths=screenshots,
            metadata={"steps": 3},
        )

        assert len(result.screenshot_paths) == 3
        result_dict = result.to_dict()
        assert len(result_dict["screenshot_paths"]) == 3

    def test_result_metadata_persistence(self) -> None:
        """Test that metadata persists through serialization."""
        metadata = {
            "feature": "demo",
            "browser": "chromium",
            "duration": 5.5,
            "interactions": 10,
        }
        result = RecordingResult(
            success=True,
            metadata=metadata,
        )

        json_str = result.to_json()
        parsed = json.loads(json_str)

        assert parsed["metadata"]["feature"] == "demo"
        assert parsed["metadata"]["browser"] == "chromium"
        assert parsed["metadata"]["duration"] == 5.5

    def test_result_error_message_preservation(self) -> None:
        """Test that error messages are preserved."""
        error_msg = "Failed to connect to localhost: Connection refused"
        result = RecordingResult(success=False, error=error_msg)

        assert result.error == error_msg
        result_dict = result.to_dict()
        assert result_dict["error"] == error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
