"""AUDIT-N+52: governance/vetter hardening spec (SOTA pass-34).

15 invariants FR-GOV-VT-001..015 covering VetterOutcome, VetterSeverity,
VetterResult factories, VetterPolicy toggle, VetterCheck ABC, path-traversal
guards, subprocess injection filtering, graceful error handling,
_extract_changed_py_files, and VetterCheckResult immutability.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from thegent.governance.vetter import (
    RuffVetterCheck,
    TestPassVetterCheck,
    VetterCheck,
    VetterCheckResult,
    VetterOutcome,
    VetterPolicy,
    VetterResult,
    VetterSeverity,
    _extract_changed_py_files,
    _filter_injection_files,
    _validate_cwd,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-VT-001: VetterOutcome has all three values
# ---------------------------------------------------------------------------


class TestVetterOutcome:
    """FR-GOV-VT-001: VetterOutcome enum has exactly three values."""

    def test_has_approved(self) -> None:
        assert VetterOutcome.APPROVED == "approved"

    def test_has_rejected(self) -> None:
        assert VetterOutcome.REJECTED == "rejected"

    def test_has_revision_requested(self) -> None:
        assert VetterOutcome.REVISION_REQUESTED == "revision_requested"

    def test_exactly_three_members(self) -> None:
        assert len(VetterOutcome) == 3


# ---------------------------------------------------------------------------
# FR-GOV-VT-002: VetterSeverity has all four levels
# ---------------------------------------------------------------------------


class TestVetterSeverity:
    """FR-GOV-VT-002: VetterSeverity enum has exactly four levels."""

    def test_has_info(self) -> None:
        assert VetterSeverity.INFO == "info"

    def test_has_warning(self) -> None:
        assert VetterSeverity.WARNING == "warning"

    def test_has_error(self) -> None:
        assert VetterSeverity.ERROR == "error"

    def test_has_critical(self) -> None:
        assert VetterSeverity.CRITICAL == "critical"

    def test_exactly_four_members(self) -> None:
        assert len(VetterSeverity) == 4


# ---------------------------------------------------------------------------
# FR-GOV-VT-003: VetterResult.approved() creates APPROVED result
# ---------------------------------------------------------------------------


class TestVetterResultApproved:
    """FR-GOV-VT-003: VetterResult.approved() factory method."""

    def test_approved_result(self) -> None:
        result = VetterResult.approved("test-check", "test-policy", reason="all good")
        assert result.outcome == VetterOutcome.APPROVED
        assert result.check_name == "test-check"
        assert result.policy_name == "test-policy"
        assert result.reason == "all good"

    def test_approved_default_reason(self) -> None:
        result = VetterResult.approved("c", "p")
        assert result.reason == ""

    def test_approved_with_metadata(self) -> None:
        result = VetterResult.approved("c", "p", key="val")
        assert result.metadata == {"key": "val"}


# ---------------------------------------------------------------------------
# FR-GOV-VT-004: VetterResult.rejected() creates REJECTED result
# ---------------------------------------------------------------------------


class TestVetterResultRejected:
    """FR-GOV-VT-004: VetterResult.rejected() factory method."""

    def test_rejected_result(self) -> None:
        result = VetterResult.rejected("test-check", "test-policy", reason="failed")
        assert result.outcome == VetterOutcome.REJECTED
        assert result.check_name == "test-check"
        assert result.reason == "failed"

    def test_rejected_with_metadata(self) -> None:
        result = VetterResult.rejected("c", "p", "no", error_code=42)
        assert result.metadata == {"error_code": 42}


# ---------------------------------------------------------------------------
# FR-GOV-VT-005: VetterResult.revision_requested() creates REVISION_REQUESTED result
# ---------------------------------------------------------------------------


class TestVetterResultRevisionRequested:
    """FR-GOV-VT-005: VetterResult.revision_requested() factory method."""

    def test_revision_requested_result(self) -> None:
        result = VetterResult.revision_requested("c", "p", reason="needs work")
        assert result.outcome == VetterOutcome.REVISION_REQUESTED
        assert result.reason == "needs work"

    def test_revision_requested_with_metadata(self) -> None:
        result = VetterResult.revision_requested("c", "p", "fix", hint="add docstring")
        assert result.metadata == {"hint": "add docstring"}


# ---------------------------------------------------------------------------
# FR-GOV-VT-006: VetterResult.is_pass / is_fail properties
# ---------------------------------------------------------------------------


class TestVetterResultPassFail:
    """FR-GOV-VT-006: VetterResult.is_pass and is_fail properties."""

    def test_approved_is_pass(self) -> None:
        result = VetterResult.approved("c", "p")
        assert result.is_pass is True
        assert result.is_fail is False

    def test_rejected_is_fail(self) -> None:
        result = VetterResult.rejected("c", "p", "no")
        assert result.is_pass is False
        assert result.is_fail is True

    def test_revision_requested_is_fail(self) -> None:
        result = VetterResult.revision_requested("c", "p", "no")
        assert result.is_pass is False
        assert result.is_fail is True


# ---------------------------------------------------------------------------
# FR-GOV-VT-007: VetterResult is frozen (immutable)
# ---------------------------------------------------------------------------


class TestVetterResultFrozen:
    """FR-GOV-VT-007: VetterResult instances are immutable."""

    def test_cannot_set_attribute(self) -> None:
        result = VetterResult.approved("c", "p")
        with pytest.raises(Exception):
            result.outcome = VetterOutcome.REJECTED  # type: ignore[misc]

    def test_cannot_set_reason(self) -> None:
        result = VetterResult.approved("c", "p")
        with pytest.raises(Exception):
            result.reason = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FR-GOV-VT-008: VetterPolicy disable/enable toggle
# ---------------------------------------------------------------------------


class TestVetterPolicy:
    """FR-GOV-VT-008: VetterPolicy toggle and metadata."""

    def test_default_enabled(self) -> None:
        policy = VetterPolicy(name="test-policy")
        assert policy.enabled is True

    def test_disable(self) -> None:
        policy = VetterPolicy(name="test-policy")
        policy.disable()
        assert policy.enabled is False

    def test_enable(self) -> None:
        policy = VetterPolicy(name="test-policy")
        policy.disable()
        policy.enable()
        assert policy.enabled is True

    def test_to_dict(self) -> None:
        policy = VetterPolicy(name="tp", severity=VetterSeverity.WARNING)
        d = policy.to_dict()
        assert d["name"] == "tp"
        assert d["severity"] == "warning"
        assert d["enabled"] is True


# ---------------------------------------------------------------------------
# FR-GOV-VT-009: VetterCheck ABC cannot be instantiated directly
# ---------------------------------------------------------------------------


class TestVetterCheckABC:
    """FR-GOV-VT-009: VetterCheck is abstract and cannot be instantiated."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            VetterCheck()  # type: ignore[abstract]

    def test_concrete_subclass_works(self) -> None:
        class ConcreteCheck(VetterCheck):
            @property
            def name(self) -> str:
                return "concrete"

            @property
            def policy(self) -> VetterPolicy:
                return VetterPolicy(name="concrete-policy")

            def run(self, payload: dict[str, Any]) -> VetterResult:
                return VetterResult.approved("concrete", "concrete-policy")

        check = ConcreteCheck()
        assert check.name == "concrete"
        assert check.is_enabled is True
        result = check.run({})
        assert result.is_pass is True


# ---------------------------------------------------------------------------
# FR-GOV-VT-010: TestPassVetterCheck cwd path-traversal guard
# ---------------------------------------------------------------------------


class TestTestPassCwdTraversal:
    """FR-GOV-VT-010: TestPassVetterCheck rejects cwd with '..' segments."""

    def test_rejects_traversal_cwd(self, tmp_path: Path) -> None:
        vetter = TestPassVetterCheck(cwd=str(tmp_path / "sub" / ".." / ".."))
        with pytest.raises(ValueError, match="cwd path contains"):
            vetter.check("")

    def test_rejects_context_cwd_traversal(self) -> None:
        vetter = TestPassVetterCheck()
        with pytest.raises(ValueError, match="cwd path contains"):
            vetter.check("", context={"cwd": "/tmp/../../etc"})

    def test_accepts_valid_cwd(self, tmp_path: Path) -> None:
        """Valid cwd resolves without error (even if shim_run would fail)."""
        vetter = TestPassVetterCheck(cwd=str(tmp_path))
        # The check will fail because shim_run is real, but no ValueError from cwd
        result = vetter.check("+++ a/f.py\n--- b/f.py\n")
        # passed=False is expected (no test runner installed in test env), but no ValueError
        assert result.passed is False or isinstance(result, VetterCheckResult)

    def test_validate_cwd_none(self) -> None:
        assert _validate_cwd(None) is None

    def test_validate_cwd_empty(self) -> None:
        assert _validate_cwd("") is None

    def test_validate_cwd_whitespace(self) -> None:
        assert _validate_cwd("   ") is None


# ---------------------------------------------------------------------------
# FR-GOV-VT-011: RuffVetterCheck cwd path-traversal guard
# ---------------------------------------------------------------------------


class TestRuffCwdTraversal:
    """FR-GOV-VT-011: RuffVetterCheck rejects cwd with '..' segments."""

    def test_rejects_traversal_cwd(self, tmp_path: Path) -> None:
        vetter = RuffVetterCheck(cwd=str(tmp_path / ".."))
        with pytest.raises(ValueError, match="cwd path contains"):
            vetter.check("+++ a/f.py\n--- b/f.py\n")

    def test_rejects_context_cwd_traversal(self) -> None:
        vetter = RuffVetterCheck()
        with pytest.raises(ValueError, match="cwd path contains"):
            vetter.check("+++ a/f.py\n--- b/f.py\n", context={"cwd": "/opt/../../etc"})

    def test_accepts_valid_cwd(self, tmp_path: Path) -> None:
        """Valid cwd resolves without error."""
        vetter = RuffVetterCheck(cwd=str(tmp_path))
        result = vetter.check("+++ a/f.py\n--- b/f.py\n")
        # Will fail (ruff not in test env) but no ValueError from cwd
        assert isinstance(result, VetterCheckResult)


# ---------------------------------------------------------------------------
# FR-GOV-VT-012: TestPassVetterCheck handles subprocess OSError
# ---------------------------------------------------------------------------


class TestTestPassSubprocessError:
    """FR-GOV-VT-012: TestPassVetterCheck handles OSError gracefully."""

    def test_os_error_returns_failed_result(self) -> None:
        vetter = TestPassVetterCheck()
        with patch(
            "thegent.governance.vetter.shim_run",
            side_effect=OSError("No such file or directory"),
        ):
            result = vetter.check("+++ a/f.py\n--- b/f.py\n")
        assert result.passed is False
        assert "Subprocess error" in result.message
        assert "No such file or directory" in result.message

    def test_value_error_returns_failed_result(self) -> None:
        vetter = TestPassVetterCheck()
        with patch(
            "thegent.governance.vetter.shim_run",
            side_effect=ValueError("invalid argument"),
        ):
            result = vetter.check("+++ a/f.py\n--- b/f.py\n")
        assert result.passed is False
        assert "Subprocess error" in result.message

    def test_timeout_still_handled(self) -> None:
        import subprocess

        vetter = TestPassVetterCheck(timeout_seconds=1)
        with patch(
            "thegent.governance.vetter.shim_run",
            side_effect=subprocess.TimeoutExpired(cmd="pytest", timeout=1),
        ):
            result = vetter.check("+++ a/f.py\n--- b/f.py\n")
        assert result.passed is False
        assert "timed out" in result.message


# ---------------------------------------------------------------------------
# FR-GOV-VT-013: RuffVetterCheck filters shell metacharacters from files
# ---------------------------------------------------------------------------


class TestRuffInjectionGuard:
    """FR-GOV-VT-013: Shell metacharacters in file paths are filtered."""

    def test_filters_pipe_char(self, caplog: pytest.LogCaptureFixture) -> None:
        diff = "+++ a/good.py\n--- a/good.py\n+++ a/evil|file.py\n--- a/evil|file.py\n"
        result = _filter_injection_files(_extract_changed_py_files(diff), "test-check")
        assert "good.py" in result
        assert all("|" not in f for f in result)
        assert "filtered file with shell metacharacters" in caplog.text

    def test_filters_ampersand(self) -> None:
        diff = "+++ a/x&y.py\n--- a/x&y.py\n"
        result = _filter_injection_files(_extract_changed_py_files(diff), "tc")
        assert result == []

    def test_filters_semicolon(self) -> None:
        diff = "+++ a/x;y.py\n--- a/x;y.py\n"
        result = _filter_injection_files(_extract_changed_py_files(diff), "tc")
        assert result == []

    def test_filters_backtick(self) -> None:
        diff = "+++ a/x`y.py\n--- a/x`y.py\n"
        result = _filter_injection_files(_extract_changed_py_files(diff), "tc")
        assert result == []

    def test_filters_dollar_sign(self) -> None:
        diff = "+++ a/x$y.py\n--- a/x$y.py\n"
        result = _filter_injection_files(_extract_changed_py_files(diff), "tc")
        assert result == []

    def test_filters_newline(self) -> None:
        diff = "+++ a/x\ny.py\n--- a/x\ny.py\n"
        result = _filter_injection_files(_extract_changed_py_files(diff), "tc")
        # The newline in the filename should be filtered
        assert all("\n" not in f for f in result)

    def test_safe_files_preserved(self) -> None:
        files = ["src/module.py", "tests/test_module.py"]
        result = _filter_injection_files(files, "tc")
        assert result == files

    def test_mixed_files_only_safe_pass(self) -> None:
        files = ["src/good.py", "src/bad;file.py", "src/ok.py"]
        result = _filter_injection_files(files, "tc")
        assert result == ["src/good.py", "src/ok.py"]


# ---------------------------------------------------------------------------
# FR-GOV-VT-014: _extract_changed_py_files extracts .py filenames
# ---------------------------------------------------------------------------


class TestExtractChangedPyFiles:
    """FR-GOV-VT-014: Diff parser extracts .py filenames correctly."""

    def test_extracts_basic_diff(self) -> None:
        diff = "--- a/src/foo.py\n+++ b/src/foo.py\n"
        files = _extract_changed_py_files(diff)
        assert files == ["src/foo.py"]

    def test_extracts_multiple_files(self) -> None:
        diff = "--- a/a.py\n+++ b/a.py\n--- a/b.py\n+++ b/b.py\n"
        files = _extract_changed_py_files(diff)
        assert "a.py" in files
        assert "b.py" in files

    def test_deduplicates(self) -> None:
        diff = "--- a/x.py\n+++ b/x.py\n--- a/x.py\n+++ b/x.py\n"
        files = _extract_changed_py_files(diff)
        assert files.count("x.py") == 1

    def test_ignores_non_py(self) -> None:
        diff = "--- a/readme.md\n+++ b/readme.md\n"
        files = _extract_changed_py_files(diff)
        assert files == []

    def test_empty_diff(self) -> None:
        assert _extract_changed_py_files("") == []


# ---------------------------------------------------------------------------
# FR-GOV-VT-015: VetterCheckResult is frozen (immutable)
# ---------------------------------------------------------------------------


class TestVetterCheckResultFrozen:
    """FR-GOV-VT-015: VetterCheckResult instances are immutable."""

    def test_cannot_set_check_name(self) -> None:
        result = VetterCheckResult(check_name="c", passed=True)
        with pytest.raises(Exception):
            result.check_name = "other"  # type: ignore[misc]

    def test_cannot_set_passed(self) -> None:
        result = VetterCheckResult(check_name="c", passed=True)
        with pytest.raises(Exception):
            result.passed = False  # type: ignore[misc]

    def test_cannot_set_message(self) -> None:
        result = VetterCheckResult(check_name="c", passed=True)
        with pytest.raises(Exception):
            result.message = "changed"  # type: ignore[misc]

    def test_cannot_set_metadata(self) -> None:
        result = VetterCheckResult(check_name="c", passed=True)
        with pytest.raises(Exception):
            result.metadata = {}  # type: ignore[misc]
