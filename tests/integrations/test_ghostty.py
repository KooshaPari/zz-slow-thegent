"""Tests for thegent.integrations.ghostty — Ghostty terminal integration.

FR traceability: FR-IDE-002 (Ghostty terminal integration)

All filesystem operations use pytest's tmp_path fixture so the real
~/.config/ghostty/config file is never touched.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest import mock

import pytest

from thegent.integrations.ghostty import (
    GhosttyConfig,
    GhosttyError,
    GhosttyIntegration,
    _parse_config_file,
    _write_config_key,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Return path to a temp Ghostty config file (parent dir created)."""
    cfg = tmp_path / "ghostty" / "config"
    cfg.parent.mkdir(parents=True)
    return cfg


@pytest.fixture
def integration(tmp_path: Path) -> GhosttyIntegration:
    """GhosttyIntegration wired to a tmp config path."""
    return GhosttyIntegration(config_path=tmp_path / "ghostty" / "config")


# ---------------------------------------------------------------------------
# Tests: GhosttyError  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestGhosttyError:
    """GhosttyError is a proper Exception subclass. @trace FR-IDE-002"""

    def test_is_exception_subclass(self) -> None:
        """GhosttyError inherits from Exception. @trace FR-IDE-002"""
        assert issubclass(GhosttyError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """GhosttyError can be raised and caught. @trace FR-IDE-002"""
        with pytest.raises(GhosttyError, match="test"):
            raise GhosttyError("test")


# ---------------------------------------------------------------------------
# Tests: GhosttyConfig dataclass  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestGhosttyConfig:
    """Tests for GhosttyConfig dataclass defaults and construction. @trace FR-IDE-002"""

    def test_default_socket_path_is_none(self) -> None:
        """Default socket_path is None. @trace FR-IDE-002"""
        cfg = GhosttyConfig()
        assert cfg.socket_path is None

    def test_default_theme_is_dark(self) -> None:
        """Default theme is 'dark'. @trace FR-IDE-002"""
        cfg = GhosttyConfig()
        assert cfg.theme == "dark"

    def test_default_font_size_is_14(self) -> None:
        """Default font_size is 14. @trace FR-IDE-002"""
        cfg = GhosttyConfig()
        assert cfg.font_size == 14

    def test_custom_values_stored(self) -> None:
        """Custom values are stored correctly. @trace FR-IDE-002"""
        cfg = GhosttyConfig(
            socket_path="/tmp/ghostty.sock", theme="Dracula", font_size=16
        )
        assert cfg.socket_path == "/tmp/ghostty.sock"
        assert cfg.theme == "Dracula"
        assert cfg.font_size == 16

    def test_raw_not_part_of_repr(self) -> None:
        """Internal raw field is excluded from repr. @trace FR-IDE-002"""
        cfg = GhosttyConfig()
        assert "raw" not in repr(cfg)


# ---------------------------------------------------------------------------
# Tests: _parse_config_file  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestParseConfigFile:
    """Tests for the _parse_config_file helper. @trace FR-IDE-002"""

    def test_parses_simple_key_value(self, tmp_path: Path) -> None:
        """Simple 'key = value' lines are parsed correctly. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("theme = Dracula\nfont-size = 16\n")
        result = _parse_config_file(cfg)
        assert result["theme"] == "Dracula"
        assert result["font-size"] == "16"

    def test_ignores_comment_lines(self, tmp_path: Path) -> None:
        """Lines starting with '#' are ignored. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("# this is a comment\ntheme = dark\n")
        result = _parse_config_file(cfg)
        assert "# this is a comment" not in result
        assert result["theme"] == "dark"

    def test_ignores_lines_without_equals(self, tmp_path: Path) -> None:
        """Lines without '=' are skipped. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("no-equals-here\ntheme = light\n")
        result = _parse_config_file(cfg)
        assert "no-equals-here" not in result

    def test_first_occurrence_wins(self, tmp_path: Path) -> None:
        """First occurrence of a key is kept; duplicates are discarded. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("theme = first\ntheme = second\n")
        result = _parse_config_file(cfg)
        assert result["theme"] == "first"

    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        """Returns empty dict when the config file does not exist. @trace FR-IDE-002"""
        result = _parse_config_file(tmp_path / "nonexistent")
        assert result == {}

    def test_strips_whitespace_around_equals(self, tmp_path: Path) -> None:
        """Key and value are stripped of surrounding whitespace. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("  theme  =  light  \n")
        result = _parse_config_file(cfg)
        assert result["theme"] == "light"


# ---------------------------------------------------------------------------
# Tests: _write_config_key  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestWriteConfigKey:
    """Tests for the _write_config_key helper. @trace FR-IDE-002"""

    def test_appends_key_when_file_missing(self, tmp_path: Path) -> None:
        """When file does not exist, the key is appended. @trace FR-IDE-002"""
        cfg = tmp_path / "sub" / "config"
        _write_config_key(cfg, "theme", "dark")
        assert "theme = dark" in cfg.read_text()

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        """Parent directories are created if missing. @trace FR-IDE-002"""
        cfg = tmp_path / "a" / "b" / "config"
        _write_config_key(cfg, "font-size", "18")
        assert isinstance(cfg, Path)
        assert cfg.exists()

    def test_replaces_existing_key(self, tmp_path: Path) -> None:
        """Existing key is replaced in-place. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("theme = old\n")
        _write_config_key(cfg, "theme", "new")
        text = cfg.read_text()
        assert "theme = new" in text
        assert "theme = old" not in text

    def test_preserves_other_keys(self, tmp_path: Path) -> None:
        """Other keys are preserved when one key is updated. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("font-size = 14\ntheme = dark\n")
        _write_config_key(cfg, "theme", "light")
        text = cfg.read_text()
        assert "font-size = 14" in text

    def test_comment_lines_preserved(self, tmp_path: Path) -> None:
        """Comment lines are preserved when updating a key. @trace FR-IDE-002"""
        cfg = tmp_path / "config"
        cfg.write_text("# my comment\ntheme = dark\n")
        _write_config_key(cfg, "theme", "light")
        assert "# my comment" in cfg.read_text()


# ---------------------------------------------------------------------------
# Tests: is_available  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """Tests for GhosttyIntegration.is_available. @trace FR-IDE-002"""

    def test_true_when_term_program_is_ghostty(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns True when TERM_PROGRAM=ghostty. @trace FR-IDE-002"""
        with mock.patch.dict("os.environ", {"TERM_PROGRAM": "ghostty"}):
            assert integration.is_available() is True

    def test_case_insensitive_ghostty(self, integration: GhosttyIntegration) -> None:
        """Returns True when TERM_PROGRAM=Ghostty (case-insensitive). @trace FR-IDE-002"""
        with mock.patch.dict("os.environ", {"TERM_PROGRAM": "Ghostty"}):
            assert integration.is_available() is True

    def test_false_when_term_program_is_iterm(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns False when TERM_PROGRAM=iTerm.app. @trace FR-IDE-002"""
        with mock.patch.dict("os.environ", {"TERM_PROGRAM": "iTerm.app"}):
            assert integration.is_available() is False

    def test_false_when_term_program_absent(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns False when TERM_PROGRAM is not set. @trace FR-IDE-002"""
        env = {k: v for k, v in __import__("os").environ.items() if k != "TERM_PROGRAM"}
        with mock.patch.dict("os.environ", env, clear=True):
            assert integration.is_available() is False


# ---------------------------------------------------------------------------
# Tests: get_config  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestGetConfig:
    """Tests for GhosttyIntegration.get_config. @trace FR-IDE-002"""

    def test_defaults_when_no_config_file(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns defaults when config file is absent. @trace FR-IDE-002"""
        cfg = integration.get_config()
        assert cfg.theme == "dark"
        assert cfg.font_size == 14
        assert cfg.socket_path is None

    def test_reads_theme_from_config(self, config_file: Path) -> None:
        """Reads the theme from the config file. @trace FR-IDE-002"""
        config_file.write_text("theme = Dracula\n")
        integration = GhosttyIntegration(config_path=config_file)
        assert integration.get_config().theme == "Dracula"

    def test_reads_font_size_from_config(self, config_file: Path) -> None:
        """Reads font-size from the config file as an integer. @trace FR-IDE-002"""
        config_file.write_text("font-size = 20\n")
        integration = GhosttyIntegration(config_path=config_file)
        assert integration.get_config().font_size == 20

    def test_reads_socket_path_from_config(self, config_file: Path) -> None:
        """Reads socket-path from the config file. @trace FR-IDE-002"""
        config_file.write_text("socket-path = /tmp/ghostty.sock\n")
        integration = GhosttyIntegration(config_path=config_file)
        assert integration.get_config().socket_path == "/tmp/ghostty.sock"

    def test_invalid_font_size_keeps_default(self, config_file: Path) -> None:
        """Invalid font-size value keeps the default of 14. @trace FR-IDE-002"""
        config_file.write_text("font-size = large\n")
        integration = GhosttyIntegration(config_path=config_file)
        assert integration.get_config().font_size == 14

    def test_empty_socket_path_becomes_none(self, config_file: Path) -> None:
        """An empty socket-path value becomes None. @trace FR-IDE-002"""
        config_file.write_text("socket-path = \n")
        integration = GhosttyIntegration(config_path=config_file)
        assert integration.get_config().socket_path is None


# ---------------------------------------------------------------------------
# Tests: set_theme  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestSetTheme:
    """Tests for GhosttyIntegration.set_theme. @trace FR-IDE-002"""

    def test_writes_theme_to_new_file(
        self, integration: GhosttyIntegration, tmp_path: Path
    ) -> None:
        """Creates config file and writes theme. @trace FR-IDE-002"""
        assert integration.set_theme("light") is True
        cfg_path = tmp_path / "ghostty" / "config"
        assert "theme = light" in cfg_path.read_text()

    def test_updates_existing_theme(self, config_file: Path) -> None:
        """Updates theme in existing config file. @trace FR-IDE-002"""
        config_file.write_text("theme = dark\n")
        integration = GhosttyIntegration(config_path=config_file)
        assert integration.set_theme("light") is True
        assert "theme = light" in config_file.read_text()

    def test_returns_false_on_empty_theme(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns False when called with an empty string. @trace FR-IDE-002"""
        assert integration.set_theme("") is False

    def test_returns_false_on_oserror(self, integration: GhosttyIntegration) -> None:
        """Returns False when the write fails with OSError. @trace FR-IDE-002"""
        with mock.patch(
            "thegent.integrations.ghostty._write_config_key",
            side_effect=OSError("permission denied"),
        ):
            assert integration.set_theme("dark") is False

    def test_roundtrip_theme(self, config_file: Path) -> None:
        """set_theme then get_config returns the written theme. @trace FR-IDE-002"""
        integration = GhosttyIntegration(config_path=config_file)
        integration.set_theme("Monokai")
        assert integration.get_config().theme == "Monokai"


# ---------------------------------------------------------------------------
# Tests: open_tab  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestOpenTab:
    """Tests for GhosttyIntegration.open_tab. @trace FR-IDE-002"""

    def test_returns_true_on_success(self, integration: GhosttyIntegration) -> None:
        """Returns True when ghostty exits 0. @trace FR-IDE-002"""
        fake = mock.MagicMock()
        fake.returncode = 0
        with mock.patch(
            "thegent.integrations.ghostty._run_ghostty_open_tab", return_value=fake
        ):
            assert integration.open_tab() is True

    def test_returns_false_on_nonzero_exit(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns False when ghostty exits non-zero. @trace FR-IDE-002"""
        fake = mock.MagicMock()
        fake.returncode = 1
        fake.stderr = "error"
        with mock.patch(
            "thegent.integrations.ghostty._run_ghostty_open_tab", return_value=fake
        ):
            assert integration.open_tab() is False

    def test_returns_false_when_binary_not_found(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns False when the ghostty binary is not on PATH. @trace FR-IDE-002"""
        with mock.patch(
            "thegent.integrations.ghostty._run_ghostty_open_tab",
            side_effect=FileNotFoundError,
        ):
            assert integration.open_tab() is False

    def test_returns_false_on_timeout(self, integration: GhosttyIntegration) -> None:
        """Returns False when the subprocess times out. @trace FR-IDE-002"""
        with mock.patch(
            "thegent.integrations.ghostty._run_ghostty_open_tab",
            side_effect=subprocess.TimeoutExpired("ghostty", 10),
        ):
            assert integration.open_tab() is False

    def test_passes_command_argument(self, integration: GhosttyIntegration) -> None:
        """Command argument is forwarded to _run_ghostty_open_tab. @trace FR-IDE-002"""
        fake = mock.MagicMock()
        fake.returncode = 0
        with mock.patch(
            "thegent.integrations.ghostty._run_ghostty_open_tab", return_value=fake
        ) as mocked:
            integration.open_tab("htop")
            mocked.assert_called_once_with("htop")


# ---------------------------------------------------------------------------
# Tests: send_notification  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestSendNotification:
    """Tests for GhosttyIntegration.send_notification. @trace FR-IDE-002"""

    def test_returns_true_on_success(self, integration: GhosttyIntegration) -> None:
        """Returns True when osascript exits 0. @trace FR-IDE-002"""
        fake = mock.MagicMock()
        fake.returncode = 0
        with mock.patch(
            "thegent.integrations.ghostty._run_osascript_notification",
            return_value=fake,
        ):
            assert integration.send_notification("Title", "Body") is True

    def test_returns_false_when_osascript_not_found(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns False when osascript is not on PATH. @trace FR-IDE-002"""
        with mock.patch(
            "thegent.integrations.ghostty._run_osascript_notification",
            side_effect=FileNotFoundError,
        ):
            assert integration.send_notification("T", "B") is False

    def test_returns_false_on_nonzero_exit(
        self, integration: GhosttyIntegration
    ) -> None:
        """Returns False when osascript exits non-zero. @trace FR-IDE-002"""
        fake = mock.MagicMock()
        fake.returncode = 1
        fake.stderr = "error"
        with mock.patch(
            "thegent.integrations.ghostty._run_osascript_notification",
            return_value=fake,
        ):
            assert integration.send_notification("T", "B") is False

    def test_returns_false_on_timeout(self, integration: GhosttyIntegration) -> None:
        """Returns False when osascript times out. @trace FR-IDE-002"""
        with mock.patch(
            "thegent.integrations.ghostty._run_osascript_notification",
            side_effect=subprocess.TimeoutExpired("osascript", 10),
        ):
            assert integration.send_notification("T", "B") is False

    def test_quotes_escaped_in_title(self, integration: GhosttyIntegration) -> None:
        """Double-quotes in title are escaped before passing to osascript. @trace FR-IDE-002"""
        fake = mock.MagicMock()
        fake.returncode = 0
        with mock.patch(
            "thegent.integrations.ghostty._run_osascript_notification",
            return_value=fake,
        ) as mocked:
            integration.send_notification('Say "hello"', "body")
            call_args = mocked.call_args[0]
            assert '\\"hello\\"' in call_args[0]

    def test_quotes_escaped_in_body(self, integration: GhosttyIntegration) -> None:
        """Double-quotes in body are escaped before passing to osascript. @trace FR-IDE-002"""
        fake = mock.MagicMock()
        fake.returncode = 0
        with mock.patch(
            "thegent.integrations.ghostty._run_osascript_notification",
            return_value=fake,
        ) as mocked:
            integration.send_notification("title", 'Body with "quotes"')
            call_args = mocked.call_args[0]
            assert '\\"quotes\\"' in call_args[1]


# ---------------------------------------------------------------------------
# Tests: get_env_info  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestGetEnvInfo:
    """Tests for GhosttyIntegration.get_env_info. @trace FR-IDE-002"""

    def test_returns_dict(self, integration: GhosttyIntegration) -> None:
        """Returns a dict. @trace FR-IDE-002"""
        assert isinstance(integration.get_env_info(), dict)

    def test_contains_expected_keys(self, integration: GhosttyIntegration) -> None:
        """Result contains all expected env-var keys. @trace FR-IDE-002"""
        info = integration.get_env_info()
        for key in (
            "TERM_PROGRAM",
            "TERM",
            "COLORTERM",
            "TERM_PROGRAM_VERSION",
            "GHOSTTY_RESOURCES_DIR",
            "GHOSTTY_BIN_DIR",
        ):
            assert key in info

    def test_reflects_env_values(self, integration: GhosttyIntegration) -> None:
        """Values reflect the current environment. @trace FR-IDE-002"""
        with mock.patch.dict(
            "os.environ", {"TERM_PROGRAM": "ghostty", "COLORTERM": "truecolor"}
        ):
            info = integration.get_env_info()
        assert info["TERM_PROGRAM"] == "ghostty"
        assert info["COLORTERM"] == "truecolor"

    def test_absent_keys_return_empty_string(
        self, integration: GhosttyIntegration
    ) -> None:
        """Missing env vars produce empty-string values, not None. @trace FR-IDE-002"""
        env = {
            k: v
            for k, v in __import__("os").environ.items()
            if k not in ("GHOSTTY_RESOURCES_DIR", "GHOSTTY_BIN_DIR")
        }
        with mock.patch.dict("os.environ", env, clear=True):
            info = integration.get_env_info()
        assert info["GHOSTTY_RESOURCES_DIR"] == ""
        assert info["GHOSTTY_BIN_DIR"] == ""


# ---------------------------------------------------------------------------
# Tests: Non-ghostty environment fallback  @trace FR-IDE-002
# ---------------------------------------------------------------------------


class TestNonGhosttyEnvironment:
    """Tests for GhosttyIntegration behaviour outside Ghostty. @trace FR-IDE-002"""

    def test_is_available_false_in_vscode(
        self, integration: GhosttyIntegration
    ) -> None:
        """is_available returns False when running in VS Code. @trace FR-IDE-002"""
        with mock.patch.dict("os.environ", {"TERM_PROGRAM": "vscode"}):
            assert integration.is_available() is False

    def test_get_config_works_outside_ghostty(
        self, integration: GhosttyIntegration
    ) -> None:
        """get_config works even when not running inside Ghostty. @trace FR-IDE-002"""
        env = {k: v for k, v in __import__("os").environ.items() if k != "TERM_PROGRAM"}
        with mock.patch.dict("os.environ", env, clear=True):
            cfg = integration.get_config()
        assert isinstance(cfg, GhosttyConfig)

    def test_open_tab_returns_false_outside_ghostty(
        self, integration: GhosttyIntegration
    ) -> None:
        """open_tab returns False when ghostty binary is absent. @trace FR-IDE-002"""
        with mock.patch(
            "thegent.integrations.ghostty._run_ghostty_open_tab",
            side_effect=FileNotFoundError,
        ):
            assert integration.open_tab() is False

    def test_send_notification_returns_false_on_linux(
        self, integration: GhosttyIntegration
    ) -> None:
        """send_notification returns False on Linux where osascript is absent. @trace FR-IDE-002"""
        with mock.patch(
            "thegent.integrations.ghostty._run_osascript_notification",
            side_effect=FileNotFoundError,
        ):
            assert integration.send_notification("Title", "Body") is False

    def test_get_env_info_returns_all_keys_outside_ghostty(
        self, integration: GhosttyIntegration
    ) -> None:
        """get_env_info always returns all keys even outside Ghostty. @trace FR-IDE-002"""
        info = integration.get_env_info()
        assert len(info) == 6
