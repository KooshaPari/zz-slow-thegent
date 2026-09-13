from pathlib import Path
from unittest.mock import patch

from thegent.platform_paths import get_config_dir
from thegent.thg_platform import Platform


def test_get_config_dir_macos(monkeypatch):
    """Test get_config_dir on macOS."""
    monkeypatch.delenv("THGENT_CONFIG_DIR", raising=False)
    with patch("thegent.platform_paths.detect_platform") as mock_detect:
        mock_detect.return_value = Platform.MACOS
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/Users/testuser")

            # Mock mkdir to avoid creating real directories
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                config_dir = get_config_dir()

                assert config_dir == Path(
                    "/Users/testuser/Library/Application Support/thegent"
                )
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_get_config_dir_windows(monkeypatch):
    """Test get_config_dir on Windows."""
    monkeypatch.delenv("THGENT_CONFIG_DIR", raising=False)
    with patch("thegent.platform_paths.detect_platform") as mock_detect:
        mock_detect.return_value = Platform.WINDOWS
        monkeypatch.setenv("APPDATA", "C:\\Users\\testuser\\AppData\\Roaming")
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            config_dir = get_config_dir()

            # Use string comparison to avoid platform-specific path separator issues in mock expectations
            assert (
                str(config_dir).replace("/", "\\")
                == "C:\\Users\\testuser\\AppData\\Roaming\\thegent"
            )
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_get_config_dir_linux(monkeypatch):
    """Test get_config_dir on Linux."""
    monkeypatch.delenv("THGENT_CONFIG_DIR", raising=False)
    with patch("thegent.platform_paths.detect_platform") as mock_detect:
        mock_detect.return_value = Platform.LINUX
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/home/testuser")
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                config_dir = get_config_dir()

                assert config_dir == Path("/home/testuser/.config/thegent")
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_get_config_dir_override(monkeypatch):
    """Test get_config_dir with THGENT_CONFIG_DIR override."""
    monkeypatch.setenv("THGENT_CONFIG_DIR", "/tmp/custom_config")
    with patch("pathlib.Path.mkdir"):
        config_dir = get_config_dir()
        assert config_dir == Path("/tmp/custom_config")
