"""Tests for MacOSDesktopAutomation.

All subprocess calls are mocked so these tests run on any platform.

FR traceability: FR-AUTO-001 through FR-AUTO-007 (macOS desktop automation).
"""

# @trace FR-AUTO-001 FR-AUTO-002 FR-AUTO-003 FR-AUTO-004 FR-AUTO-005 FR-AUTO-006 FR-AUTO-007

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from thegent.automation.macos_desktop import (
    AutomationError,
    AutomationResult,
    MacOSDesktopAutomation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    """Create a mock CompletedProcess-like object."""
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """FR-AUTO-001: is_available reflects platform and binary presence."""

    def test_available_on_darwin_with_binary(self):
        """Returns True when platform is darwin and osascript is found."""
        automation = MacOSDesktopAutomation()
        with patch("sys.platform", "darwin"), patch("shutil.which", return_value="/usr/bin/osascript"):
            assert automation.is_available() is True

    def test_not_available_on_linux(self):
        """Returns False on Linux."""
        automation = MacOSDesktopAutomation()
        with patch("sys.platform", "linux"):
            assert automation.is_available() is False

    def test_not_available_on_windows(self):
        """Returns False on Windows."""
        automation = MacOSDesktopAutomation()
        with patch("sys.platform", "win32"):
            assert automation.is_available() is False

    def test_not_available_when_binary_missing(self):
        """Returns False when osascript binary is not on PATH."""
        automation = MacOSDesktopAutomation()
        with patch("sys.platform", "darwin"), patch("shutil.which", return_value=None):
            assert automation.is_available() is False


# ---------------------------------------------------------------------------
# run_applescript
# ---------------------------------------------------------------------------


class TestRunApplescript:
    """FR-AUTO-002: run_applescript wraps osascript -e."""

    @pytest.fixture
    def automation(self):
        return MacOSDesktopAutomation()

    def test_success(self, automation):
        """Successful run returns AutomationResult(success=True, output=...)."""
        proc = _make_proc(returncode=0, stdout="Finder\n")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc) as mock_run,
        ):
            result = automation.run_applescript('return "Finder"')

        assert result.success is True
        assert result.output == "Finder"
        assert result.error is None
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "osascript"
        assert args[1] == "-e"

    def test_failure_nonzero_exit(self, automation):
        """Non-zero returncode returns AutomationResult(success=False)."""
        proc = _make_proc(returncode=1, stdout="", stderr="execution error: -1728")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            result = automation.run_applescript("bad script")

        assert result.success is False
        assert result.error == "execution error: -1728"

    def test_failure_stderr_fallback(self, automation):
        """When stderr is empty, error message includes exit code."""
        proc = _make_proc(returncode=2, stdout="", stderr="")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            result = automation.run_applescript("bad script")

        assert result.success is False
        assert "2" in result.error  # exit code in message

    def test_timeout(self, automation):
        """TimeoutExpired returns AutomationResult(success=False, error=...timeout...)."""
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=5.0)),
        ):
            result = automation.run_applescript("delay 999", timeout_s=5.0)

        assert result.success is False
        assert "timed out" in result.error

    def test_non_macos_fallback(self, automation):
        """Returns graceful failure on non-macOS."""
        with patch.object(automation, "is_available", return_value=False):
            result = automation.run_applescript("return 1")

        assert result.success is False
        assert result.error == "Not macOS"
        assert result.output == ""

    def test_passes_timeout_to_subprocess(self, automation):
        """timeout_s parameter is forwarded to subprocess.run."""
        proc = _make_proc(returncode=0, stdout="ok")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc) as mock_run,
        ):
            automation.run_applescript("return 1", timeout_s=42.0)

        _, kwargs = mock_run.call_args
        assert kwargs.get("timeout") == 42.0

    def test_strips_trailing_newline(self, automation):
        """Output is stripped of leading/trailing whitespace."""
        proc = _make_proc(returncode=0, stdout="  Safari  \n")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            result = automation.run_applescript("return 1")

        assert result.output == "Safari"


# ---------------------------------------------------------------------------
# run_jxa
# ---------------------------------------------------------------------------


class TestRunJxa:
    """FR-AUTO-003: run_jxa wraps osascript -l JavaScript -e."""

    @pytest.fixture
    def automation(self):
        return MacOSDesktopAutomation()

    def test_jxa_success(self, automation):
        """JXA execution returns AutomationResult(success=True)."""
        proc = _make_proc(returncode=0, stdout="result")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc) as mock_run,
        ):
            result = automation.run_jxa("Application('Finder').activate()")

        assert result.success is True
        assert result.output == "result"
        args = mock_run.call_args[0][0]
        assert "-l" in args
        assert "JavaScript" in args

    def test_jxa_failure(self, automation):
        """JXA non-zero exit returns AutomationResult(success=False)."""
        proc = _make_proc(returncode=1, stderr="ReferenceError: bad")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            result = automation.run_jxa("bad()")

        assert result.success is False
        assert "ReferenceError" in result.error

    def test_jxa_timeout(self, automation):
        """TimeoutExpired in JXA mode returns graceful failure."""
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=3.0)),
        ):
            result = automation.run_jxa("while(true){}", timeout_s=3.0)

        assert result.success is False
        assert "timed out" in result.error

    def test_jxa_non_macos_fallback(self, automation):
        """Returns graceful failure on non-macOS."""
        with patch.object(automation, "is_available", return_value=False):
            result = automation.run_jxa("Application('Finder').activate()")

        assert result.success is False
        assert result.error == "Not macOS"


# ---------------------------------------------------------------------------
# open_application
# ---------------------------------------------------------------------------


class TestOpenApplication:
    """FR-AUTO-004: open_application activates an app via AppleScript."""

    @pytest.fixture
    def automation(self):
        return MacOSDesktopAutomation()

    def test_open_application_success(self, automation):
        """Delegates to run_applescript with correct tell block."""
        proc = _make_proc(returncode=0, stdout="")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc) as mock_run,
        ):
            result = automation.open_application("Safari")

        assert result.success is True
        call_args = mock_run.call_args[0][0]
        script_arg = call_args[call_args.index("-e") + 1]
        assert "Safari" in script_arg
        assert "activate" in script_arg

    def test_open_application_failure(self, automation):
        """Propagates failure from run_applescript."""
        proc = _make_proc(returncode=1, stderr="App not found")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            result = automation.open_application("NonExistentApp999")

        assert result.success is False

    def test_open_application_non_macos(self, automation):
        """Returns graceful failure on non-macOS."""
        with patch.object(automation, "is_available", return_value=False):
            result = automation.open_application("Safari")

        assert result.success is False
        assert result.error == "Not macOS"


# ---------------------------------------------------------------------------
# get_frontmost_app
# ---------------------------------------------------------------------------


class TestGetFrontmostApp:
    """FR-AUTO-005: get_frontmost_app queries System Events."""

    @pytest.fixture
    def automation(self):
        return MacOSDesktopAutomation()

    def test_returns_app_name_on_success(self, automation):
        """Returns app name string when AppleScript succeeds."""
        proc = _make_proc(returncode=0, stdout="Finder\n")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            name = automation.get_frontmost_app()

        assert name == "Finder"

    def test_returns_none_on_failure(self, automation):
        """Returns None when AppleScript fails."""
        proc = _make_proc(returncode=1, stderr="error")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            name = automation.get_frontmost_app()

        assert name is None

    def test_returns_none_on_non_macos(self, automation):
        """Returns None on non-macOS platforms."""
        with patch.object(automation, "is_available", return_value=False):
            name = automation.get_frontmost_app()

        assert name is None

    def test_script_references_system_events(self, automation):
        """AppleScript query targets System Events process."""
        proc = _make_proc(returncode=0, stdout="Terminal")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc) as mock_run,
        ):
            automation.get_frontmost_app()

        call_args = mock_run.call_args[0][0]
        script = call_args[call_args.index("-e") + 1]
        assert "System Events" in script
        assert "frontmost" in script


# ---------------------------------------------------------------------------
# click_menu_item
# ---------------------------------------------------------------------------


class TestClickMenuItem:
    """FR-AUTO-006: click_menu_item clicks application menu items."""

    @pytest.fixture
    def automation(self):
        return MacOSDesktopAutomation()

    def test_click_menu_item_success(self, automation):
        """Returns success when osascript exits 0."""
        proc = _make_proc(returncode=0, stdout="")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc) as mock_run,
        ):
            result = automation.click_menu_item("Safari", "File", "New Window")

        assert result.success is True
        call_args = mock_run.call_args[0][0]
        script = call_args[call_args.index("-e") + 1]
        assert "Safari" in script
        assert "File" in script
        assert "New Window" in script

    def test_click_menu_item_failure(self, automation):
        """Propagates failure from run_applescript."""
        proc = _make_proc(returncode=1, stderr="menu item not found")
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc),
        ):
            result = automation.click_menu_item("Safari", "File", "Nonexistent")

        assert result.success is False

    def test_click_menu_item_non_macos(self, automation):
        """Returns graceful failure on non-macOS."""
        with patch.object(automation, "is_available", return_value=False):
            result = automation.click_menu_item("Safari", "File", "New Window")

        assert result.success is False
        assert result.error == "Not macOS"

    def test_click_menu_item_uses_system_events(self, automation):
        """Script includes System Events process tell block."""
        proc = _make_proc(returncode=0)
        with (
            patch.object(automation, "is_available", return_value=True),
            patch("subprocess.run", return_value=proc) as mock_run,
        ):
            automation.click_menu_item("TextEdit", "Edit", "Copy")

        call_args = mock_run.call_args[0][0]
        script = call_args[call_args.index("-e") + 1]
        assert "System Events" in script


# ---------------------------------------------------------------------------
# AutomationResult dataclass
# ---------------------------------------------------------------------------


class TestAutomationResult:
    """FR-AUTO-007: AutomationResult dataclass has correct default values."""

    def test_defaults(self):
        """error defaults to None."""
        r = AutomationResult(success=True, output="hello")
        assert r.error is None

    def test_explicit_error(self):
        """error can be set explicitly."""
        r = AutomationResult(success=False, output="", error="oops")
        assert r.error == "oops"

    def test_repr_contains_fields(self):
        """repr includes key fields for debugging."""
        r = AutomationResult(success=True, output="ok")
        rep = repr(r)
        assert "success" in rep
        assert "output" in rep


# ---------------------------------------------------------------------------
# AutomationError exception
# ---------------------------------------------------------------------------


class TestAutomationError:
    """AutomationError is a proper Exception subclass."""

    def test_is_exception(self):
        assert issubclass(AutomationError, Exception)

    def test_can_raise_and_catch(self):
        with pytest.raises(AutomationError, match="boom"):
            raise AutomationError("boom")
