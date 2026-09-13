"""Unit tests for WL-097: TestPassVetterCheck + RuffVetterCheck.

Both checks:
  - Extract changed .py files from a unified diff in `output`.
  - Run the tool via subprocess.run (mocked in all tests below).
  - Fail fast: non-zero exit = passed=False.
  - No silent error handling.

All tests annotated with # @trace WL-097.
"""

from __future__ import annotations

import asyncio
import subprocess
from unittest.mock import MagicMock, patch

from thegent.govern.vetter.checks import RuffVetterCheck, TestPassVetterCheck
from thegent.govern.vetter.models import VetterCheck, VetterCheckResult

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

_DIFF_TWO_PY = (
    "--- a/foo.py\n+++ b/foo.py\n@@ -1,3 +1,4 @@\n+x = 1\n--- a/bar.py\n+++ b/bar.py\n@@ -5,2 +5,3 @@\n+y = 2\n"
)

_DIFF_NO_PY = "--- a/README.md\n+++ b/README.md\n@@ -1 +1,2 @@\n+## new section\n"

_DIFF_ONE_PY = "--- a/module.py\n+++ b/module.py\n@@ -10,3 +10,4 @@\n+z = 3\n"

RUN_ID = "run-wl097"
CONTEXT: dict = {}


def _mock_proc(returncode: int, stdout: bytes = b"", stderr: bytes = b"") -> MagicMock:
    """Build a mock CompletedProcess-like object."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


# ===========================================================================
# TestPassVetterCheck — construction
# ===========================================================================


def test_test_pass_vetter_check_default_name():
    # @trace WL-097
    check = TestPassVetterCheck()
    assert check.name == "test_pass_vetter"


def test_test_pass_vetter_check_default_runner():
    # @trace WL-097
    check = TestPassVetterCheck()
    assert check.test_runner == "pytest"


def test_test_pass_vetter_check_default_scope():
    # @trace WL-097
    check = TestPassVetterCheck()
    assert check.scope == "changed_files"


def test_test_pass_vetter_check_default_timeout():
    # @trace WL-097
    check = TestPassVetterCheck()
    assert check.timeout_seconds == 120


def test_test_pass_vetter_check_implements_protocol():
    # @trace WL-097
    check = TestPassVetterCheck()
    assert isinstance(check, VetterCheck)


def test_test_pass_vetter_check_custom_params():
    # @trace WL-097
    check = TestPassVetterCheck(test_runner="python -m pytest", scope="all", timeout_seconds=60)
    assert check.test_runner == "python -m pytest"
    assert check.scope == "all"
    assert check.timeout_seconds == 60


# ===========================================================================
# TestPassVetterCheck — pass paths
# ===========================================================================


def test_test_pass_vetter_check_passes_on_zero_exit():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0, b"1 passed")) as mock_run:
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.passed is True
    assert result.check_name == "test_pass_vetter"
    assert isinstance(result, VetterCheckResult)
    mock_run.assert_called_once()


def test_test_pass_vetter_check_passes_includes_changed_files_in_cmd():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_TWO_PY, CONTEXT))

    cmd = mock_run.call_args[0][0]
    assert "foo.py" in cmd
    assert "bar.py" in cmd


def test_test_pass_vetter_check_passes_message_empty_on_success():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0, b"ok")):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.message == ""


def test_test_pass_vetter_check_passes_no_py_files_runs_full_suite():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        result = asyncio.run(check.check(RUN_ID, _DIFF_NO_PY, CONTEXT))

    assert result.passed is True
    cmd = mock_run.call_args[0][0]
    # No extra .py file args beyond the base pytest + extra_args
    assert "foo.py" not in cmd
    assert result.metadata["files_tested"] == []


def test_test_pass_vetter_check_metadata_contains_returncode():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.metadata["returncode"] == 0


# ===========================================================================
# TestPassVetterCheck — fail paths
# ===========================================================================


def test_test_pass_vetter_check_fails_on_nonzero_exit():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, b"FAILED", b""),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.passed is False


def test_test_pass_vetter_check_fail_message_contains_output():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, b"AssertionError: expected 1 got 2", b""),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert "AssertionError" in result.message


def test_test_pass_vetter_check_fail_metadata_returncode():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(2, b"error", b""),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.metadata["returncode"] == 2


def test_test_pass_vetter_check_fail_stderr_included_in_message():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, b"", b"ModuleNotFoundError: no module named foo"),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert "ModuleNotFoundError" in result.message


def test_test_pass_vetter_check_fail_message_truncated_to_2000():
    # @trace WL-097
    check = TestPassVetterCheck()
    long_output = b"x" * 5000
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, long_output, b""),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert len(result.message) <= 2000


# ===========================================================================
# TestPassVetterCheck — timeout path
# ===========================================================================


def test_test_pass_vetter_check_timeout_returns_passed_false():
    # @trace WL-097
    check = TestPassVetterCheck(timeout_seconds=5)
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=5),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.passed is False


def test_test_pass_vetter_check_timeout_message_mentions_seconds():
    # @trace WL-097
    check = TestPassVetterCheck(timeout_seconds=30)
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=30),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert "30s" in result.message


def test_test_pass_vetter_check_timeout_metadata_flag():
    # @trace WL-097
    check = TestPassVetterCheck(timeout_seconds=10)
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=10),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.metadata.get("timeout") is True


# ===========================================================================
# RuffVetterCheck — construction
# ===========================================================================


def test_ruff_vetter_check_default_name():
    # @trace WL-097
    check = RuffVetterCheck()
    assert check.name == "ruff_vetter"


def test_ruff_vetter_check_default_fix_mode_false():
    # @trace WL-097
    check = RuffVetterCheck()
    assert check.fix_mode is False


def test_ruff_vetter_check_default_select_rules_empty():
    # @trace WL-097
    check = RuffVetterCheck()
    assert check.select_rules == []


def test_ruff_vetter_check_implements_protocol():
    # @trace WL-097
    check = RuffVetterCheck()
    assert isinstance(check, VetterCheck)


def test_ruff_vetter_check_custom_params():
    # @trace WL-097
    check = RuffVetterCheck(fix_mode=True, select_rules=["E", "F"])
    assert check.fix_mode is True
    assert check.select_rules == ["E", "F"]


# ===========================================================================
# RuffVetterCheck — no Python files in diff
# ===========================================================================


def test_ruff_vetter_check_skips_when_no_py_files():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run") as mock_run:
        result = asyncio.run(check.check(RUN_ID, _DIFF_NO_PY, CONTEXT))

    assert result.passed is True
    mock_run.assert_not_called()


def test_ruff_vetter_check_skip_message_mentions_ruff():
    # @trace WL-097
    check = RuffVetterCheck()
    result = asyncio.run(check.check(RUN_ID, _DIFF_NO_PY, CONTEXT))
    assert "ruff" in result.message.lower()


# ===========================================================================
# RuffVetterCheck — pass paths
# ===========================================================================


def test_ruff_vetter_check_passes_on_zero_exit():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.passed is True


def test_ruff_vetter_check_passes_message_empty_on_success():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.message == ""


def test_ruff_vetter_check_passes_cmd_includes_changed_files():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_TWO_PY, CONTEXT))

    cmd = mock_run.call_args[0][0]
    assert "foo.py" in cmd
    assert "bar.py" in cmd


def test_ruff_vetter_check_metadata_contains_files_checked():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert "module.py" in result.metadata["files_checked"]


def test_ruff_vetter_check_select_rules_added_to_cmd():
    # @trace WL-097
    check = RuffVetterCheck(select_rules=["E501", "F401"])
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    cmd = mock_run.call_args[0][0]
    assert "--select" in cmd
    assert "E501,F401" in cmd


def test_ruff_vetter_check_fix_mode_adds_fix_flag():
    # @trace WL-097
    check = RuffVetterCheck(fix_mode=True)
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    cmd = mock_run.call_args[0][0]
    assert "--fix" in cmd


def test_ruff_vetter_check_no_fix_flag_when_fix_mode_false():
    # @trace WL-097
    check = RuffVetterCheck(fix_mode=False)
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    cmd = mock_run.call_args[0][0]
    assert "--fix" not in cmd


# ===========================================================================
# RuffVetterCheck — fail paths
# ===========================================================================


def test_ruff_vetter_check_fails_on_nonzero_exit():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, b"module.py:1:1: E302 expected 2 blank lines", b""),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.passed is False


def test_ruff_vetter_check_fail_message_contains_lint_output():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, b"E302 expected 2 blank lines", b""),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert "E302" in result.message


def test_ruff_vetter_check_fail_metadata_returncode():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, b"lint error", b""),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert result.metadata["returncode"] == 1


def test_ruff_vetter_check_fail_stderr_included_in_message():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch(
        "thegent.govern.vetter.checks.subprocess.run",
        return_value=_mock_proc(1, b"", b"error: no such file"),
    ):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert "no such file" in result.message


def test_ruff_vetter_check_result_is_vetter_check_result():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)):
        result = asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, CONTEXT))

    assert isinstance(result, VetterCheckResult)


# ===========================================================================
# Cross-cutting: cwd propagation
# ===========================================================================


def test_test_pass_vetter_check_passes_cwd_from_context():
    # @trace WL-097
    check = TestPassVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, {"cwd": "/tmp/project"}))

    kwargs = mock_run.call_args[1]
    assert kwargs["cwd"] == "/tmp/project"


def test_ruff_vetter_check_passes_cwd_from_context():
    # @trace WL-097
    check = RuffVetterCheck()
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, {"cwd": "/tmp/project"}))

    kwargs = mock_run.call_args[1]
    assert kwargs["cwd"] == "/tmp/project"


def test_test_pass_vetter_check_instance_cwd_overrides_context():
    # @trace WL-097
    check = TestPassVetterCheck(cwd="/override")
    with patch("thegent.govern.vetter.checks.subprocess.run", return_value=_mock_proc(0)) as mock_run:
        asyncio.run(check.check(RUN_ID, _DIFF_ONE_PY, {"cwd": "/context-cwd"}))

    kwargs = mock_run.call_args[1]
    assert kwargs["cwd"] == "/override"
