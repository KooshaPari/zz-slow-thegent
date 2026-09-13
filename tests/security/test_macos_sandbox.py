"""Tests for thegent.security.macos_sandbox.

@trace FR-SEC-001  macOS sandbox profile management
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.security.macos_sandbox import (
    SANDBOX_LEVEL_ENV_VAR,
    SANDBOX_PROFILE_DIR,
    MacOSSandbox,
    SandboxLevel,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sandbox() -> MacOSSandbox:
    """Return a MacOSSandbox pointing at the real profile dir."""
    return MacOSSandbox(profile_dir=SANDBOX_PROFILE_DIR)


@pytest.fixture
def sandbox_with_custom_profiles(tmp_path: Path) -> MacOSSandbox:
    """Return a MacOSSandbox backed by minimal stub profiles in tmp_path."""
    for level in (SandboxLevel.READONLY, SandboxLevel.RESTRICTED, SandboxLevel.NETWORKED):
        stub = tmp_path / f"{level.value}.sb"
        stub.write_text(
            f"(version 1)\n(deny default)\n; {level.value} stub\n"
            "(allow file-read*)\n"
            '(allow file-write* (subpath "PROJECT_ROOT_PLACEHOLDER"))\n'
        )
    return MacOSSandbox(profile_dir=tmp_path)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path / "myproject"


# ---------------------------------------------------------------------------
# 1. SandboxLevel enum
# ---------------------------------------------------------------------------


def test_sandbox_level_values_are_lowercase_strings() -> None:
    """@trace FR-SEC-001  SandboxLevel enum values are lowercase strings."""
    assert SandboxLevel.NONE.value == "none"
    assert SandboxLevel.READONLY.value == "readonly"
    assert SandboxLevel.RESTRICTED.value == "restricted"
    assert SandboxLevel.NETWORKED.value == "networked"
    assert SandboxLevel.FULL.value == "full"


def test_sandbox_level_roundtrip() -> None:
    """@trace FR-SEC-001  SandboxLevel can be constructed from its value string."""
    for level in SandboxLevel:
        assert SandboxLevel(level.value) is level


def test_sandbox_level_invalid_value_raises() -> None:
    """@trace FR-SEC-001  Invalid level string raises ValueError."""
    with pytest.raises(ValueError):
        SandboxLevel("superstrict")


# ---------------------------------------------------------------------------
# 2. MacOSSandbox.is_sandbox_available
# ---------------------------------------------------------------------------


def test_is_sandbox_available_false_on_linux(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  is_sandbox_available returns False on Linux."""
    with patch("thegent.security.macos_sandbox.platform.system", return_value="Linux"):
        assert sandbox.is_sandbox_available() is False


def test_is_sandbox_available_false_on_windows(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  is_sandbox_available returns False on Windows."""
    with patch("thegent.security.macos_sandbox.platform.system", return_value="Windows"):
        assert sandbox.is_sandbox_available() is False


def test_is_sandbox_available_true_when_exec_present(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  is_sandbox_available True when sandbox-exec is in PATH."""
    sandbox._sandbox_exec = None
    with (
        patch("thegent.security.macos_sandbox.platform.system", return_value="Darwin"),
        patch("thegent.security.macos_sandbox.shutil.which", return_value="/usr/bin/sandbox-exec"),
    ):
        assert sandbox.is_sandbox_available() is True


def test_is_sandbox_available_false_when_exec_missing(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  is_sandbox_available False when sandbox-exec not in PATH."""
    sandbox._sandbox_exec = None
    with (
        patch("thegent.security.macos_sandbox.platform.system", return_value="Darwin"),
        patch("thegent.security.macos_sandbox.shutil.which", return_value=None),
    ):
        assert sandbox.is_sandbox_available() is False


def test_is_sandbox_available_caches_result(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  Second call uses cached result without re-checking shutil.which."""
    sandbox._sandbox_exec = "/usr/bin/sandbox-exec"
    with (
        patch("thegent.security.macos_sandbox.platform.system", return_value="Darwin"),
        patch("thegent.security.macos_sandbox.shutil.which") as mock_which,
    ):
        result = sandbox.is_sandbox_available()
        mock_which.assert_not_called()
    assert result is True


# ---------------------------------------------------------------------------
# 3. get_profile_path
# ---------------------------------------------------------------------------


def test_get_profile_path_none_for_none_level(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  get_profile_path returns None for NONE level."""
    assert sandbox.get_profile_path(SandboxLevel.NONE) is None


def test_get_profile_path_none_for_full_level(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  get_profile_path returns None for FULL level."""
    assert sandbox.get_profile_path(SandboxLevel.FULL) is None


def test_get_profile_path_returns_path_for_readonly(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  get_profile_path returns a Path for READONLY."""
    p = sandbox.get_profile_path(SandboxLevel.READONLY)
    assert p is not None
    assert p.name == "readonly.sb"


def test_get_profile_path_returns_path_for_restricted(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  get_profile_path returns a Path for RESTRICTED."""
    p = sandbox.get_profile_path(SandboxLevel.RESTRICTED)
    assert p is not None
    assert p.name == "restricted.sb"


def test_get_profile_path_returns_path_for_networked(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  get_profile_path returns a Path for NETWORKED."""
    p = sandbox.get_profile_path(SandboxLevel.NETWORKED)
    assert p is not None
    assert p.name == "networked.sb"


def test_get_profile_path_returns_none_for_missing_file(tmp_path: Path) -> None:
    """@trace FR-SEC-001  get_profile_path returns None when template file is absent."""
    empty_dir = tmp_path / "empty_profiles"
    empty_dir.mkdir()
    s = MacOSSandbox(profile_dir=empty_dir)
    assert s.get_profile_path(SandboxLevel.READONLY) is None


# ---------------------------------------------------------------------------
# 4. generate_profile
# ---------------------------------------------------------------------------


def test_generate_profile_raises_for_none(sandbox: MacOSSandbox, project_root: Path) -> None:
    """@trace FR-SEC-001  generate_profile raises ValueError for NONE."""
    with pytest.raises(ValueError, match="none"):
        sandbox.generate_profile(SandboxLevel.NONE, project_root)


def test_generate_profile_raises_for_full(sandbox: MacOSSandbox, project_root: Path) -> None:
    """@trace FR-SEC-001  generate_profile raises ValueError for FULL."""
    with pytest.raises(ValueError, match="full"):
        sandbox.generate_profile(SandboxLevel.FULL, project_root)


def test_generate_profile_readonly_contains_deny_default(sandbox: MacOSSandbox, project_root: Path) -> None:
    """@trace FR-SEC-001  READONLY profile contains (deny default)."""
    profile = sandbox.generate_profile(SandboxLevel.READONLY, project_root)
    assert "(deny default)" in profile


def test_generate_profile_readonly_contains_file_read_allow(sandbox: MacOSSandbox, project_root: Path) -> None:
    """@trace FR-SEC-001  READONLY profile allows file-read*."""
    profile = sandbox.generate_profile(SandboxLevel.READONLY, project_root)
    assert "(allow file-read*)" in profile


def test_generate_profile_readonly_denies_network(sandbox: MacOSSandbox, project_root: Path) -> None:
    """@trace FR-SEC-001  READONLY profile denies network."""
    profile = sandbox.generate_profile(SandboxLevel.READONLY, project_root)
    assert "(deny network*)" in profile


def test_generate_profile_restricted_substitutes_project_root(
    sandbox_with_custom_profiles: MacOSSandbox, tmp_path: Path
) -> None:
    """@trace FR-SEC-001  RESTRICTED profile replaces PROJECT_ROOT_PLACEHOLDER."""
    root = tmp_path / "agent_work"
    profile = sandbox_with_custom_profiles.generate_profile(SandboxLevel.RESTRICTED, root)
    assert "PROJECT_ROOT_PLACEHOLDER" not in profile
    assert str(root.resolve()) in profile


def test_generate_profile_networked_substitutes_project_root(
    sandbox_with_custom_profiles: MacOSSandbox, tmp_path: Path
) -> None:
    """@trace FR-SEC-001  NETWORKED profile replaces PROJECT_ROOT_PLACEHOLDER."""
    root = tmp_path / "agent_net_work"
    profile = sandbox_with_custom_profiles.generate_profile(SandboxLevel.NETWORKED, root)
    assert "PROJECT_ROOT_PLACEHOLDER" not in profile
    assert str(root.resolve()) in profile


def test_generate_profile_raises_when_template_missing(tmp_path: Path, project_root: Path) -> None:
    """@trace FR-SEC-001  generate_profile raises FileNotFoundError for missing template."""
    s = MacOSSandbox(profile_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        s.generate_profile(SandboxLevel.READONLY, project_root)


def test_generate_profile_networked_contains_port_443(sandbox: MacOSSandbox, project_root: Path) -> None:
    """@trace FR-SEC-001  NETWORKED profile allows outbound TCP 443."""
    profile = sandbox.generate_profile(SandboxLevel.NETWORKED, project_root)
    assert "443" in profile


# ---------------------------------------------------------------------------
# 5. apply_to_command
# ---------------------------------------------------------------------------


def test_apply_to_command_none_returns_original(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  apply_to_command NONE returns original command unchanged."""
    cmd = ["claude", "--foo"]
    result = sandbox.apply_to_command(cmd, SandboxLevel.NONE)
    assert result == cmd


def test_apply_to_command_full_returns_original(sandbox: MacOSSandbox) -> None:
    """@trace FR-SEC-001  apply_to_command FULL returns original command unchanged."""
    cmd = ["my-agent", "--trusted"]
    result = sandbox.apply_to_command(cmd, SandboxLevel.FULL)
    assert result == cmd


def test_apply_to_command_returns_original_when_exec_unavailable(sandbox: MacOSSandbox, tmp_path: Path) -> None:
    """@trace FR-SEC-001  Falls back to original command when sandbox-exec absent."""
    sandbox._sandbox_exec = None
    with patch("thegent.security.macos_sandbox.platform.system", return_value="Linux"):
        cmd = ["agent", "run"]
        result = sandbox.apply_to_command(cmd, SandboxLevel.READONLY, project_root=tmp_path)
    assert result == cmd


def test_apply_to_command_wraps_with_sandbox_exec(sandbox_with_custom_profiles: MacOSSandbox, tmp_path: Path) -> None:
    """@trace FR-SEC-001  apply_to_command prepends sandbox-exec -f <profile>."""
    with (
        patch("thegent.security.macos_sandbox.platform.system", return_value="Darwin"),
        patch(
            "thegent.security.macos_sandbox.shutil.which",
            return_value="/usr/bin/sandbox-exec",
        ),
    ):
        cmd = ["my-tool", "--flag"]
        result = sandbox_with_custom_profiles.apply_to_command(cmd, SandboxLevel.READONLY, project_root=tmp_path)
    assert result[0] == "sandbox-exec"
    assert result[1] == "-f"
    profile_path = Path(result[2])
    assert profile_path.suffix == ".sb"
    assert profile_path.exists()
    assert result[3:] == cmd


def test_apply_to_command_profile_file_contains_profile_text(
    sandbox_with_custom_profiles: MacOSSandbox, tmp_path: Path
) -> None:
    """@trace FR-SEC-001  Profile temp file contains deny default."""
    with (
        patch("thegent.security.macos_sandbox.platform.system", return_value="Darwin"),
        patch(
            "thegent.security.macos_sandbox.shutil.which",
            return_value="/usr/bin/sandbox-exec",
        ),
    ):
        result = sandbox_with_custom_profiles.apply_to_command(["agent"], SandboxLevel.READONLY, project_root=tmp_path)
    profile_content = Path(result[2]).read_text()
    assert "(deny default)" in profile_content


def test_apply_to_command_restricted_uses_cwd_as_default_root(
    sandbox_with_custom_profiles: MacOSSandbox, tmp_path: Path
) -> None:
    """@trace FR-SEC-001  Without project_root, RESTRICTED uses cwd."""
    with (
        patch("thegent.security.macos_sandbox.platform.system", return_value="Darwin"),
        patch(
            "thegent.security.macos_sandbox.shutil.which",
            return_value="/usr/bin/sandbox-exec",
        ),
        patch("thegent.security.macos_sandbox.Path.cwd", return_value=tmp_path),
    ):
        result = sandbox_with_custom_profiles.apply_to_command(["agent"], SandboxLevel.RESTRICTED)
    assert result[0] == "sandbox-exec"


# ---------------------------------------------------------------------------
# 6. level_from_env
# ---------------------------------------------------------------------------


def test_level_from_env_returns_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """@trace FR-SEC-001  level_from_env returns NONE when env var absent."""
    monkeypatch.delenv(SANDBOX_LEVEL_ENV_VAR, raising=False)
    assert MacOSSandbox.level_from_env() is SandboxLevel.NONE


def test_level_from_env_returns_correct_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """@trace FR-SEC-001  level_from_env parses 'networked' correctly."""
    monkeypatch.setenv(SANDBOX_LEVEL_ENV_VAR, "networked")
    assert MacOSSandbox.level_from_env() is SandboxLevel.NETWORKED


def test_level_from_env_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    """@trace FR-SEC-001  level_from_env is case-insensitive."""
    monkeypatch.setenv(SANDBOX_LEVEL_ENV_VAR, "READONLY")
    assert MacOSSandbox.level_from_env() is SandboxLevel.READONLY


def test_level_from_env_invalid_defaults_to_none(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """@trace FR-SEC-001  Unknown level logs a warning and defaults to NONE."""
    monkeypatch.setenv(SANDBOX_LEVEL_ENV_VAR, "superstrict")
    with caplog.at_level(logging.WARNING, logger="thegent.security.macos_sandbox"):
        level = MacOSSandbox.level_from_env()
    assert level is SandboxLevel.NONE
    assert "superstrict" in caplog.text


def test_level_from_env_empty_string_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """@trace FR-SEC-001  Empty string env var returns NONE."""
    monkeypatch.setenv(SANDBOX_LEVEL_ENV_VAR, "")
    assert MacOSSandbox.level_from_env() is SandboxLevel.NONE


# ---------------------------------------------------------------------------
# 7. SANDBOX_PROFILE_DIR constant
# ---------------------------------------------------------------------------


def test_sandbox_profile_dir_exists() -> None:
    """@trace FR-SEC-001  SANDBOX_PROFILE_DIR exists in the package."""
    assert SANDBOX_PROFILE_DIR.is_dir()


def test_sandbox_profile_dir_contains_all_templates() -> None:
    """@trace FR-SEC-001  All expected .sb template files are present."""
    expected = {"readonly.sb", "restricted.sb", "networked.sb"}
    present = {f.name for f in SANDBOX_PROFILE_DIR.glob("*.sb")}
    assert expected <= present


# ---------------------------------------------------------------------------
# 8. from_env factory
# ---------------------------------------------------------------------------


def test_from_env_returns_macos_sandbox_instance() -> None:
    """@trace FR-SEC-001  from_env() returns a MacOSSandbox instance."""
    instance = MacOSSandbox.from_env()
    assert isinstance(instance, MacOSSandbox)


def test_from_env_uses_default_profile_dir() -> None:
    """@trace FR-SEC-001  from_env() uses the package SANDBOX_PROFILE_DIR."""
    instance = MacOSSandbox.from_env()
    assert instance._profile_dir == SANDBOX_PROFILE_DIR


# ---------------------------------------------------------------------------
# 9. Idempotency / no mutation of original cmd
# ---------------------------------------------------------------------------


def test_apply_to_command_does_not_mutate_original(sandbox_with_custom_profiles: MacOSSandbox, tmp_path: Path) -> None:
    """@trace FR-SEC-001  apply_to_command does not mutate the caller's cmd list."""
    original = ["agent", "--verbose"]
    copy_before = list(original)
    with (
        patch("thegent.security.macos_sandbox.platform.system", return_value="Darwin"),
        patch(
            "thegent.security.macos_sandbox.shutil.which",
            return_value="/usr/bin/sandbox-exec",
        ),
    ):
        sandbox_with_custom_profiles.apply_to_command(original, SandboxLevel.READONLY, project_root=tmp_path)
    assert original == copy_before
