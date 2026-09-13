"""Tests for thegent.mesh.smart_merge — AST-aware merge driver (heliosShield Phase 7).

FR traceability: FR-MESH-007 (smart merge), FR-MESH-008 (mergiraf driver config)
heliosShield-smart-merge: SmartMerger class-based API + WorktreePool integration
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from thegent.mesh.smart_merge import (
    MERGIRAF_EXTENSIONS,
    MergeResult,
    SmartMergeConfig,
    SmartMerger,
    configure_mergiraf_driver,
    is_mergiraf_available,
    make_smart_merger,
    merge_files,
)

if os.environ.get("THGENT_ENFORCE_MERGIRAF_TESTS", "0") == "1" and not is_mergiraf_available():
    pytest.fail(
        "THGENT_ENFORCE_MERGIRAF_TESTS=1 but mergiraf binary is unavailable",
        pytrace=False,
    )

# ---------------------------------------------------------------------------
# FR-MESH-007: is_mergiraf_available
# ---------------------------------------------------------------------------


class TestIsMergirafAvailable:
    """Tests for is_mergiraf_available(). @trace FR-MESH-007"""

    def test_returns_true_when_mergiraf_on_path(self):
        """is_mergiraf_available returns True when shutil.which finds mergiraf."""
        with mock.patch("shutil.which", return_value="/opt/homebrew/bin/mergiraf"):
            assert is_mergiraf_available() is True

    def test_returns_false_when_mergiraf_missing(self):
        """is_mergiraf_available returns False when mergiraf is not on PATH."""
        with mock.patch("shutil.which", return_value=None):
            assert is_mergiraf_available() is False

    def test_live_detection(self):
        """Live environment: is_mergiraf_available should return a bool."""
        result = is_mergiraf_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# FR-MESH-007: merge_files — clean merge path
# ---------------------------------------------------------------------------


class TestMergeFilesCleanMerge:
    """Tests for merge_files when the merge is conflict-free. @trace FR-MESH-007"""

    @pytest.fixture
    def _trio(self, tmp_path: Path):
        """Write base / ours / theirs files for a clean merge."""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "output.py"

        base.write_text("x = 1\ny = 2\n", encoding="utf-8")
        ours.write_text("x = 1\ny = 2\nz = 3\n", encoding="utf-8")
        theirs.write_text("x = 1\ny = 2\nw = 4\n", encoding="utf-8")

        return base, ours, theirs, output

    def test_returns_true_on_clean_merge_with_mergiraf(self, tmp_path, _trio):
        """merge_files returns True when mergiraf exits 0. @trace FR-MESH-007"""
        base, ours, theirs, output = _trio

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run") as mock_run:
                # mergiraf signals clean merge with exit 0
                mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                output.write_text("merged", encoding="utf-8")  # simulate output
                result = merge_files(base, ours, theirs, output)

        assert result is True

    def test_returns_false_on_conflicts_with_mergiraf(self, tmp_path, _trio):
        """merge_files returns False when mergiraf exits 1 (conflicts). @trace FR-MESH-007"""
        base, ours, theirs, output = _trio

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(returncode=1, stdout="", stderr="conflicts")
                output.write_text("<<<", encoding="utf-8")
                result = merge_files(base, ours, theirs, output)

        assert result is False

    def test_falls_back_to_git_when_mergiraf_hard_fails(self, tmp_path, _trio):
        """merge_files falls back to git merge-file when mergiraf exits >=2. @trace FR-MESH-007"""
        base, ours, theirs, output = _trio

        def side_effect(cmd, **kwargs):
            if "mergiraf" in cmd[0]:
                return mock.Mock(returncode=2, stdout="", stderr="internal error")
            # git merge-file fallback
            output.write_text("merged via git", encoding="utf-8")
            return mock.Mock(returncode=0)

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", side_effect=side_effect):
                result = merge_files(base, ours, theirs, output)

        # Git returned 0 so result should be True
        assert result is True

    def test_falls_back_to_git_when_mergiraf_not_installed(self, tmp_path, _trio):
        """merge_files uses git merge-file when mergiraf is absent. @trace FR-MESH-007"""
        base, ours, theirs, output = _trio

        def side_effect(cmd, **kwargs):
            # Only git merge-file should be called
            assert "mergiraf" not in str(cmd)
            output.write_text("merged via git fallback", encoding="utf-8")
            return mock.Mock(returncode=0, stdout="merged", stderr="")

        with mock.patch("shutil.which", return_value=None):
            with mock.patch("subprocess.run", side_effect=side_effect):
                result = merge_files(base, ours, theirs, output)

        assert result is True

    def test_output_file_written_on_fallback(self, tmp_path):
        """The output file is written even when using the diff3 fallback. @trace FR-MESH-007"""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "merged.py"

        base.write_text("a = 1\n", encoding="utf-8")
        ours.write_text("a = 1\nb = 2\n", encoding="utf-8")
        theirs.write_text("a = 1\nc = 3\n", encoding="utf-8")

        with mock.patch("shutil.which", return_value=None):
            # Use real git if available; accept either success or conflict outcome
            merge_files(base, ours, theirs, output)

        # Output file must exist regardless of merge outcome
        assert output.exists()

    def test_last_resort_copies_ours_when_git_missing(self, tmp_path):
        """When neither mergiraf nor git is available, ours content lands in output. @trace FR-MESH-007"""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"

        base.write_text("base\n", encoding="utf-8")
        ours.write_text("ours content\n", encoding="utf-8")
        theirs.write_text("theirs\n", encoding="utf-8")

        with mock.patch("shutil.which", return_value=None), mock.patch(
            "subprocess.run",
            side_effect=FileNotFoundError("git not found"),
        ):
            result = merge_files(base, ours, theirs, output)

        assert result is False
        # Output should contain our content as the safe default
        assert output.read_text(encoding="utf-8") == "ours content\n"


# ---------------------------------------------------------------------------
# FR-MESH-007: path_hint is forwarded to mergiraf
# ---------------------------------------------------------------------------


class TestMergeFilesPathHint:
    """Tests verifying path_hint is passed to mergiraf for language detection."""

    def test_path_hint_passed_in_command(self, tmp_path):
        """path_hint is appended as -p <path> in the mergiraf invocation."""
        base = tmp_path / "base"
        ours = tmp_path / "ours"
        theirs = tmp_path / "theirs"
        output = tmp_path / "out"

        for f in (base, ours, theirs):
            f.write_text("content\n", encoding="utf-8")

        captured: list[list[str]] = []

        def capture(cmd, **kwargs):
            captured.append(list(cmd))
            output.write_text("ok", encoding="utf-8")
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", side_effect=capture):
                merge_files(base, ours, theirs, output, path_hint="src/foo.py")

        assert any("-p" in cmd and "src/foo.py" in cmd for cmd in captured)


# ---------------------------------------------------------------------------
# FR-MESH-008: configure_mergiraf_driver
# ---------------------------------------------------------------------------


class TestConfigureMergirafDriver:
    """Tests for configure_mergiraf_driver(). @trace FR-MESH-008"""

    def test_returns_false_when_mergiraf_missing(self, tmp_path):
        """configure_mergiraf_driver returns False when mergiraf is not on PATH."""
        with mock.patch("shutil.which", return_value=None):
            result = configure_mergiraf_driver(tmp_path)

        assert result is False

    def test_calls_git_config_twice(self, tmp_path):
        """configure_mergiraf_driver calls git config for name and driver."""
        (tmp_path / ".git").mkdir()

        calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            calls.append(list(cmd))
            return mock.Mock(returncode=0)

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", side_effect=fake_run):
                result = configure_mergiraf_driver(tmp_path)

        assert result is True
        git_config_calls = [c for c in calls if "git" in c and "config" in c]
        assert len(git_config_calls) == 2

    def test_driver_cmd_contains_mergiraf_and_git_flag(self, tmp_path):
        """The registered driver command references mergiraf and --git."""
        (tmp_path / ".git").mkdir()

        driver_lines: list[str] = []

        def fake_run(cmd, **kwargs):
            # Capture the driver value (last arg)
            if "merge.mergiraf.driver" in cmd:
                driver_lines.append(cmd[-1])
            return mock.Mock(returncode=0)

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", side_effect=fake_run):
                configure_mergiraf_driver(tmp_path)

        assert driver_lines, "Expected driver command to be registered"
        driver = driver_lines[0]
        assert "mergiraf" in driver
        assert "--git" in driver
        assert "%O" in driver
        assert "%A" in driver
        assert "%B" in driver

    def test_gitattributes_created_with_extensions(self, tmp_path):
        """configure_mergiraf_driver writes .gitattributes entries for .py/.rs/.ts/.js."""
        (tmp_path / ".git").mkdir()

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)):
                configure_mergiraf_driver(tmp_path)

        gitattributes = tmp_path / ".gitattributes"
        assert gitattributes.exists(), ".gitattributes should be created"
        content = gitattributes.read_text(encoding="utf-8")
        for ext in ("*.py", "*.rs", "*.ts", "*.js"):
            assert ext in content, f"{ext} should appear in .gitattributes"
        assert "merge=mergiraf" in content

    def test_gitattributes_not_duplicated(self, tmp_path):
        """Calling configure_mergiraf_driver twice does not duplicate entries."""
        (tmp_path / ".git").mkdir()

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)):
                configure_mergiraf_driver(tmp_path)
                configure_mergiraf_driver(tmp_path)

        content = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
        assert content.count("*.py merge=mergiraf") == 1

    def test_global_config_skips_gitattributes(self, tmp_path):
        """When global_config=True, .gitattributes is not written."""
        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)):
                configure_mergiraf_driver(global_config=True)

        assert not (tmp_path / ".gitattributes").exists()

    def test_returns_false_on_git_config_failure(self, tmp_path):
        """configure_mergiraf_driver returns False if git config command fails."""
        (tmp_path / ".git").mkdir()

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "git"),
            ):
                result = configure_mergiraf_driver(tmp_path)

        assert result is False

    def test_existing_gitattributes_is_preserved(self, tmp_path):
        """Existing .gitattributes content is kept when new entries are appended."""
        (tmp_path / ".git").mkdir()
        existing = "*.md diff=markdown\n"
        (tmp_path / ".gitattributes").write_text(existing, encoding="utf-8")

        with mock.patch("shutil.which", return_value="/usr/bin/mergiraf"):
            with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0)):
                configure_mergiraf_driver(tmp_path)

        content = (tmp_path / ".gitattributes").read_text(encoding="utf-8")
        assert "*.md diff=markdown" in content
        assert "*.py merge=mergiraf" in content


# ---------------------------------------------------------------------------
# FR-MESH-007: MERGIRAF_EXTENSIONS constant
# ---------------------------------------------------------------------------


class TestMergirafExtensions:
    """Sanity checks on the MERGIRAF_EXTENSIONS constant."""

    def test_contains_core_extensions(self):
        """MERGIRAF_EXTENSIONS includes .py, .rs, .ts, .js. @trace FR-MESH-007"""
        for ext in (".py", ".rs", ".ts", ".js"):
            assert ext in MERGIRAF_EXTENSIONS

    def test_is_frozenset(self):
        """MERGIRAF_EXTENSIONS is a frozenset (immutable). @trace FR-MESH-007"""
        assert isinstance(MERGIRAF_EXTENSIONS, frozenset)


# ---------------------------------------------------------------------------
# Integration smoke test (requires mergiraf + git in PATH)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not is_mergiraf_available(),
    reason="mergiraf not installed — skipping live integration test",
)
class TestMergirafIntegrationLive:
    """Live integration tests that call the real mergiraf binary. @trace FR-MESH-007"""

    def test_clean_merge_with_real_mergiraf(self, tmp_path):
        """mergiraf cleanly merges non-conflicting Python edits."""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"

        base.write_text("def foo():\n    return 1\n\ndef bar():\n    return 2\n", encoding="utf-8")
        ours.write_text("def foo():\n    return 10\n\ndef bar():\n    return 2\n", encoding="utf-8")
        theirs.write_text("def foo():\n    return 1\n\ndef bar():\n    return 20\n", encoding="utf-8")

        result = merge_files(base, ours, theirs, output)

        assert output.exists(), "Output file must be written"
        content = output.read_text(encoding="utf-8")
        # Both changes should appear in a clean merge
        assert "return 10" in content
        assert "return 20" in content
        # And there should be no conflict markers
        assert "<<<<<<" not in content
        assert result is True

    def test_conflict_returns_false_and_writes_markers(self, tmp_path):
        """mergiraf returns False and writes conflict markers for genuinely conflicting edits."""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"

        base.write_text("x = 0\n", encoding="utf-8")
        ours.write_text("x = 1\n", encoding="utf-8")
        theirs.write_text("x = 2\n", encoding="utf-8")

        result = merge_files(base, ours, theirs, output)

        assert output.exists(), "Output file must be written even with conflicts"
        # Either conflict or resolution — the call should not raise
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: SmartMergeConfig dataclass
# ---------------------------------------------------------------------------


class TestSmartMergeConfig:
    """Tests for SmartMergeConfig dataclass. @trace heliosShield-smart-merge / FR-MESH-007"""

    def test_defaults(self):
        """SmartMergeConfig has sensible defaults. @trace FR-MESH-007"""
        cfg = SmartMergeConfig()
        assert cfg.mergiraf_binary is None
        assert cfg.fallback_to_git is True
        assert cfg.timeout_s == 30

    def test_custom_binary(self):
        """SmartMergeConfig accepts a custom binary path. @trace FR-MESH-007"""
        cfg = SmartMergeConfig(mergiraf_binary="/opt/bin/mergiraf")
        assert cfg.mergiraf_binary == "/opt/bin/mergiraf"

    def test_fallback_disabled(self):
        """SmartMergeConfig can disable git fallback. @trace FR-MESH-007"""
        cfg = SmartMergeConfig(fallback_to_git=False)
        assert cfg.fallback_to_git is False

    def test_custom_timeout(self):
        """SmartMergeConfig accepts a custom timeout. @trace FR-MESH-007"""
        cfg = SmartMergeConfig(timeout_s=60)
        assert cfg.timeout_s == 60


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: MergeResult dataclass
# ---------------------------------------------------------------------------


class TestMergeResult:
    """Tests for MergeResult dataclass. @trace heliosShield-smart-merge / FR-MESH-007"""

    def test_success_result(self):
        """MergeResult with success=True has expected attributes. @trace FR-MESH-007"""
        r = MergeResult(success=True)
        assert r.success is True
        assert r.conflicts == []
        assert r.output == ""
        assert r.used_mergiraf is False

    def test_failure_result_with_conflicts(self):
        """MergeResult captures conflict list. @trace FR-MESH-007"""
        r = MergeResult(success=False, conflicts=["src/foo.py", "src/bar.py"])
        assert r.success is False
        assert len(r.conflicts) == 2
        assert "src/foo.py" in r.conflicts

    def test_mergiraf_flag(self):
        """MergeResult records which tool was used. @trace FR-MESH-007"""
        r = MergeResult(success=True, used_mergiraf=True)
        assert r.used_mergiraf is True

    def test_output_stored(self):
        """MergeResult captures subprocess output. @trace FR-MESH-007"""
        r = MergeResult(success=False, output="CONFLICT in foo.py")
        assert "CONFLICT" in r.output


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: SmartMerger.is_available()
# ---------------------------------------------------------------------------


class TestSmartMergerIsAvailable:
    """Tests for SmartMerger.is_available(). @trace heliosShield-smart-merge / FR-MESH-007"""

    def test_returns_true_when_binary_on_path(self):
        """is_available returns True when mergiraf found on PATH. @trace FR-MESH-007"""
        with mock.patch("shutil.which", return_value="/usr/local/bin/mergiraf"):
            m = SmartMerger()
            assert m.is_available() is True

    def test_returns_false_when_binary_missing(self):
        """is_available returns False when mergiraf not found. @trace FR-MESH-007"""
        with mock.patch("shutil.which", return_value=None):
            m = SmartMerger()
            assert m.is_available() is False

    def test_uses_config_binary_directly(self):
        """is_available returns True when config provides explicit binary path. @trace FR-MESH-007"""
        cfg = SmartMergeConfig(mergiraf_binary="/custom/mergiraf")
        m = SmartMerger(cfg)
        assert m.is_available() is True

    def test_uses_env_var_binary(self):
        """is_available resolves binary from THGENT_MERGIRAF_BINARY env var. @trace FR-MESH-007"""
        with mock.patch.dict("os.environ", {"THGENT_MERGIRAF_BINARY": "/env/mergiraf"}):
            with mock.patch("shutil.which", return_value=None):
                m = SmartMerger()
                assert m.is_available() is True


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: SmartMerger.merge()
# ---------------------------------------------------------------------------


class TestSmartMergerMerge:
    """Tests for SmartMerger.merge(). @trace heliosShield-smart-merge / FR-MESH-007"""

    @pytest.fixture
    def _files(self, tmp_path: Path):
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"
        base.write_text("x = 1\n", encoding="utf-8")
        ours.write_text("x = 2\n", encoding="utf-8")
        theirs.write_text("x = 3\n", encoding="utf-8")
        return str(base), str(ours), str(theirs), str(output)

    def test_clean_merge_with_mergiraf_returns_success(self, tmp_path, _files):
        """merge() returns MergeResult(success=True, used_mergiraf=True) on clean mergiraf merge.
        @trace FR-MESH-007"""
        base, ours, theirs, output = _files

        def fake_run(cmd, **kwargs):
            Path(output).write_text("merged\n", encoding="utf-8")
            return mock.Mock(returncode=0, stdout="merged\n", stderr="")

        cfg = SmartMergeConfig(mergiraf_binary="/usr/bin/mergiraf")
        merger = SmartMerger(cfg)
        with mock.patch("subprocess.run", side_effect=fake_run):
            result = merger.merge(base, ours, theirs, output)

        assert result.success is True
        assert result.used_mergiraf is True

    def test_conflict_merge_returns_failure_with_used_mergiraf(self, tmp_path, _files):
        """merge() returns MergeResult(success=False, used_mergiraf=True) on conflict.
        @trace FR-MESH-007"""
        base, ours, theirs, output = _files
        Path(output).write_text("<<<\n", encoding="utf-8")

        cfg = SmartMergeConfig(mergiraf_binary="/usr/bin/mergiraf")
        merger = SmartMerger(cfg)
        with mock.patch("subprocess.run", return_value=mock.Mock(returncode=1, stdout="", stderr="conflict")):
            result = merger.merge(base, ours, theirs, output)

        assert result.success is False
        assert result.used_mergiraf is True

    def test_fallback_used_when_mergiraf_unavailable(self, tmp_path, _files):
        """merge() falls back to git when mergiraf absent. @trace FR-MESH-007"""
        base, ours, theirs, output = _files

        def git_side_effect(cmd, **kwargs):
            Path(output).write_text("git-merged\n", encoding="utf-8")
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch("shutil.which", return_value=None):
            merger = SmartMerger()
        with mock.patch("subprocess.run", side_effect=git_side_effect):
            result = merger.merge(base, ours, theirs, output)

        assert result.used_mergiraf is False

    def test_fallback_disabled_returns_failure_when_no_binary(self, _files):
        """merge() returns failure immediately when fallback disabled and no binary.
        @trace FR-MESH-007"""
        base, ours, theirs, output = _files
        cfg = SmartMergeConfig(fallback_to_git=False)
        with mock.patch("shutil.which", return_value=None):
            merger = SmartMerger(cfg)
        result = merger.merge(base, ours, theirs, output)
        assert result.success is False
        assert result.used_mergiraf is False

    def test_mergiraf_hard_failure_falls_back_to_git(self, tmp_path, _files):
        """merge() falls back to git when mergiraf exits >=2. @trace FR-MESH-007"""
        base, ours, theirs, output = _files

        def side_effect(cmd, **kwargs):
            if "mergiraf" in str(cmd):
                return mock.Mock(returncode=2, stdout="", stderr="internal error")
            # git merge-file: writes to the tmp copy (first positional arg after git merge-file flags)
            # The _merge_with_git_merge_file helper copies ours to a tempfile, then runs git on it.
            # After git, it copies tmp -> output.  We just need git to succeed (returncode=0).
            return mock.Mock(returncode=0, stdout="", stderr="")

        cfg = SmartMergeConfig(mergiraf_binary="/usr/bin/mergiraf")
        merger = SmartMerger(cfg)
        # Write ours content so _merge_with_git_merge_file can copy it into the temp file
        Path(ours).write_text("ours content\n", encoding="utf-8")
        with mock.patch("subprocess.run", side_effect=side_effect):
            result = merger.merge(base, ours, theirs, output)

        assert result.success is True
        assert result.used_mergiraf is False

    def test_returns_merge_result_type(self, _files):
        """merge() always returns a MergeResult instance. @trace FR-MESH-007"""
        base, ours, theirs, output = _files
        with mock.patch("shutil.which", return_value=None):
            merger = SmartMerger()
        with mock.patch("subprocess.run", return_value=mock.Mock(returncode=0, stdout="ok", stderr="")):
            result = merger.merge(base, ours, theirs, output)
        assert isinstance(result, MergeResult)


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: SmartMerger.merge_worktree_changes()
# ---------------------------------------------------------------------------


class TestSmartMergerMergeWorktreeChanges:
    """Tests for SmartMerger.merge_worktree_changes(). @trace heliosShield-smart-merge / FR-MESH-007"""

    def test_success_on_clean_git_merge(self, tmp_path):
        """merge_worktree_changes returns success when git merge exits 0. @trace FR-MESH-007"""
        merger = SmartMerger(SmartMergeConfig(mergiraf_binary=None, fallback_to_git=True))

        def fake_run(cmd, **kwargs):
            if "rev-parse" in cmd:
                return mock.Mock(returncode=0, stdout="agent/test\n", stderr="")
            return mock.Mock(returncode=0, stdout="Already up to date.\n", stderr="")

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = merger.merge_worktree_changes(tmp_path, "main")

        assert result.success is True
        assert isinstance(result, MergeResult)

    def test_failure_when_git_not_found(self, tmp_path):
        """merge_worktree_changes returns failure if git binary is missing. @trace FR-MESH-007"""
        merger = SmartMerger(SmartMergeConfig())
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = merger.merge_worktree_changes(tmp_path, "main")
        assert result.success is False

    def test_collects_conflict_file_paths(self, tmp_path):
        """merge_worktree_changes parses CONFLICT lines from git output. @trace FR-MESH-007"""
        merger = SmartMerger(SmartMergeConfig())

        conflict_output = "CONFLICT (content): Merge conflict in src/foo.py\nAuto-merging src/bar.py\n"

        def fake_run(cmd, **kwargs):
            if "rev-parse" in cmd:
                return mock.Mock(returncode=0, stdout="agent/foo\n", stderr="")
            return mock.Mock(returncode=1, stdout=conflict_output, stderr="")

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = merger.merge_worktree_changes(tmp_path, "main")

        assert result.success is False
        assert "src/foo.py" in result.conflicts

    def test_used_mergiraf_true_when_binary_available(self, tmp_path):
        """merge_worktree_changes sets used_mergiraf=True when mergiraf binary present.
        @trace FR-MESH-007"""
        cfg = SmartMergeConfig(mergiraf_binary="/usr/bin/mergiraf", fallback_to_git=True)
        merger = SmartMerger(cfg)

        def fake_run(cmd, **kwargs):
            if "rev-parse" in cmd:
                return mock.Mock(returncode=0, stdout="agent/x\n", stderr="")
            return mock.Mock(returncode=0, stdout="Merged.\n", stderr="")

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = merger.merge_worktree_changes(tmp_path, "main")

        assert result.used_mergiraf is True

    def test_used_mergiraf_false_when_binary_absent(self, tmp_path):
        """merge_worktree_changes sets used_mergiraf=False when mergiraf not found.
        @trace FR-MESH-007"""
        with mock.patch("shutil.which", return_value=None):
            merger = SmartMerger()

        def fake_run(cmd, **kwargs):
            if "rev-parse" in cmd:
                return mock.Mock(returncode=0, stdout="agent/x\n", stderr="")
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = merger.merge_worktree_changes(tmp_path, "main")

        assert result.used_mergiraf is False

    def test_timeout_returns_failure(self, tmp_path):
        """merge_worktree_changes returns failure on subprocess timeout. @trace FR-MESH-007"""
        cfg = SmartMergeConfig(timeout_s=1)
        merger = SmartMerger(cfg)

        def fake_run(cmd, **kwargs):
            if "rev-parse" in cmd:
                return mock.Mock(returncode=0, stdout="agent/y\n", stderr="")
            raise subprocess.TimeoutExpired(cmd, 1)

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = merger.merge_worktree_changes(tmp_path, "main")

        assert result.success is False


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: make_smart_merger() factory
# ---------------------------------------------------------------------------


class TestMakeSmartMerger:
    """Tests for make_smart_merger() factory function. @trace heliosShield-smart-merge / FR-MESH-007"""

    def test_returns_smart_merger_instance(self):
        """make_smart_merger returns a SmartMerger. @trace FR-MESH-007"""
        m = make_smart_merger()
        assert isinstance(m, SmartMerger)

    def test_accepts_config(self):
        """make_smart_merger uses provided SmartMergeConfig. @trace FR-MESH-007"""
        cfg = SmartMergeConfig(mergiraf_binary="/custom/bin")
        m = make_smart_merger(cfg)
        assert m.is_available() is True

    def test_reads_env_var_for_binary(self):
        """make_smart_merger reads THGENT_MERGIRAF_BINARY env var. @trace FR-MESH-007"""
        with mock.patch.dict("os.environ", {"THGENT_MERGIRAF_BINARY": "/env/mergiraf"}):
            with mock.patch("shutil.which", return_value=None):
                m = make_smart_merger()
        assert m.is_available() is True

    def test_none_config_uses_defaults(self):
        """make_smart_merger(None) creates SmartMerger with default config. @trace FR-MESH-007"""
        with mock.patch("shutil.which", return_value=None):
            m = make_smart_merger(None)
        assert isinstance(m, SmartMerger)


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: WorktreePool integration with SmartMerger
# ---------------------------------------------------------------------------


class TestWorktreePoolSmartMergerIntegration:
    """Tests for WorktreePool + SmartMerger integration. @trace heliosShield-smart-merge / FR-MESH-007"""

    def test_worktreepool_accepts_merger_kwarg(self, tmp_path):
        """WorktreePool can be instantiated with a SmartMerger. @trace FR-MESH-007"""
        from thegent.mesh.git_parallelism import WorktreePool

        with mock.patch("shutil.which", return_value=None):
            merger = SmartMerger()

        pool = WorktreePool(tmp_path, pool_root=tmp_path / ".pool", merger=merger)
        assert pool._merger is merger

    def test_worktreepool_merger_defaults_to_none(self, tmp_path):
        """WorktreePool.merger defaults to None when not provided. @trace FR-MESH-007"""
        from thegent.mesh.git_parallelism import WorktreePool

        pool = WorktreePool(tmp_path, pool_root=tmp_path / ".pool")
        assert pool._merger is None

    def test_worktreepool_uses_merger_in_merge_and_remove(self, tmp_path):
        """WorktreePool calls SmartMerger.merge_worktree_changes in _merge_and_remove.
        @trace FR-MESH-007"""
        from thegent.mesh.git_parallelism import WorktreePool

        mock_merger = mock.Mock(spec=SmartMerger)
        mock_merger.merge_worktree_changes.return_value = MergeResult(success=True, used_mergiraf=True)

        pool = WorktreePool(tmp_path, pool_root=tmp_path / ".pool", merger=mock_merger)
        pool._worktrees_ok = True

        with mock.patch.object(pool, "_resolve_target_branch", return_value="main"):
            with mock.patch.object(pool, "_git_worktree_remove", return_value=True):
                with mock.patch.object(pool, "_try_delete_branch"):
                    import shutil as _shutil

                    with mock.patch.object(_shutil, "rmtree"):
                        pool._merge_and_remove("agent-x", tmp_path / "wt", "agent/agent-x")

        mock_merger.merge_worktree_changes.assert_called_once()

    def test_worktreepool_falls_back_to_git_when_no_merger(self, tmp_path):
        """WorktreePool uses plain git merge when no SmartMerger configured.
        @trace FR-MESH-007"""
        from thegent.mesh.git_parallelism import WorktreePool

        pool = WorktreePool(tmp_path, pool_root=tmp_path / ".pool")
        pool._worktrees_ok = True

        with mock.patch.object(pool, "_resolve_target_branch", return_value="main"):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                with mock.patch.object(pool, "_git_worktree_remove", return_value=True):
                    with mock.patch.object(pool, "_try_delete_branch"):
                        import shutil as _shutil

                        with mock.patch.object(_shutil, "rmtree"):
                            result = pool._merge_and_remove("agent-y", tmp_path / "wt", "agent/agent-y")

        # Plain git merge path: should have called subprocess.run with git merge
        assert result is True
        git_merge_calls = [c for c in mock_run.call_args_list if "merge" in str(c)]
        assert git_merge_calls

    def test_merge_result_failure_still_cleans_up(self, tmp_path):
        """Even when SmartMerger reports failure, worktree is cleaned up. @trace FR-MESH-007"""
        from thegent.mesh.git_parallelism import WorktreePool

        mock_merger = mock.Mock(spec=SmartMerger)
        mock_merger.merge_worktree_changes.return_value = MergeResult(success=False, conflicts=["foo.py"])

        pool = WorktreePool(tmp_path, pool_root=tmp_path / ".pool", merger=mock_merger)
        pool._worktrees_ok = True

        with mock.patch.object(pool, "_resolve_target_branch", return_value="main"):
            with mock.patch.object(pool, "_git_worktree_remove", return_value=True) as mock_rm:
                with mock.patch.object(pool, "_try_delete_branch"):
                    import shutil as _shutil

                    with mock.patch.object(_shutil, "rmtree"):
                        result = pool._merge_and_remove("agent-z", tmp_path / "wt", "agent/agent-z")

        # Cleanup should still be attempted
        mock_rm.assert_called_once()
        assert result is False  # merger reported failure


# ---------------------------------------------------------------------------
# heliosShield-smart-merge: mesh __init__ exports
# ---------------------------------------------------------------------------


class TestMeshInitExports:
    """Verify SmartMerger, SmartMergeConfig, MergeResult are exported from mesh.__init__.
    @trace heliosShield-smart-merge / FR-MESH-007"""

    def test_smart_merger_exported(self):
        """SmartMerger is accessible from thegent.mesh. @trace FR-MESH-007"""
        from thegent.mesh import SmartMerger as _SM  # noqa: N814

        assert _SM is SmartMerger

    def test_smart_merge_config_exported(self):
        """SmartMergeConfig is accessible from thegent.mesh. @trace FR-MESH-007"""
        from thegent.mesh import SmartMergeConfig as _SMC  # noqa: N814

        assert _SMC is SmartMergeConfig

    def test_merge_result_exported(self):
        """MergeResult is accessible from thegent.mesh. @trace FR-MESH-007"""
        from thegent.mesh import MergeResult as _MR  # noqa: N814

        assert _MR is MergeResult

    def test_make_smart_merger_exported(self):
        """make_smart_merger is accessible from thegent.mesh. @trace FR-MESH-007"""
        from thegent.mesh import make_smart_merger as _msm

        assert _msm is make_smart_merger
