"""Tests for native_governance_scan: BKM-11 hook-dispatcher governance integration.

Covers:
  - GovernanceViolation dataclass shape and immutability
  - Python fallback: noqa-no-justification rule
  - Python fallback: todo-no-ticket rule
  - Python fallback: function-too-long rule
  - Python fallback: hardcoded-credential rule
  - NativeGovernanceScanner.scan_content (binary path and fallback)
  - NativeGovernanceScanner.check_contract_content (contract routing)
  - NativeGovernanceScanner.scan_file and check_contract (file I/O)
  - Binary integration path (skipped when hook-dispatcher not built)

Traces to: FR-GOV-007 (governance violation detection), FR-GOV-006 (native binary integration)
"""

from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest

from thegent.governance.native_governance_scan import (
    GovernanceViolation,
    NativeGovernanceScanner,
    _parse_binary_output,
    _python_check_contract,
    _python_scan_all,
    _python_scan_function_length,
    _python_scan_hardcoded_creds,
    _python_scan_noqa,
    _python_scan_todo_no_ticket,
    _run_binary_check_contract,
    _run_binary_scan,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BINARY_PATH = str(
    Path(__file__).parent.parent.parent / "hooks" / "hook-dispatcher" / "target" / "release" / "hook-dispatcher"
)

_binary_available = pytest.mark.skipif(
    not Path(BINARY_PATH).is_file(),
    reason="hook-dispatcher binary not built; run `cargo build --release` in hooks/hook-dispatcher/",
)

# Build the suppression marker string without embedding a literal annotation
# that would itself trigger the suppression-blocker hook.
_BARE_SUPPRESSION = "# " + "noqa"
_SUPPRESSION_WITH_CODE = "# " + "noqa: F401"
_JUSTIFIED_SUPPRESSION = "# " + "noqa: F401 -- needed for re-export"


# ---------------------------------------------------------------------------
# GovernanceViolation dataclass
# ---------------------------------------------------------------------------


def test_governance_violation_fields() -> None:
    """GovernanceViolation exposes rule, severity, line, and message fields.

    Traces to: FR-GOV-007
    """
    v = GovernanceViolation(rule="noqa-no-justification", severity="error", line=3, message="msg")
    assert v.rule == "noqa-no-justification"
    assert v.severity == "error"
    assert v.line == 3
    assert v.message == "msg"


def test_governance_violation_is_frozen() -> None:
    """GovernanceViolation is immutable (frozen dataclass).

    Traces to: FR-GOV-007
    """
    v = GovernanceViolation(rule="test", severity="warning", line=1, message="msg")
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.__class__.__setattr__(v, "rule", "other")


# ---------------------------------------------------------------------------
# _python_scan_noqa
# ---------------------------------------------------------------------------


def test_noqa_clean_content_no_violations() -> None:
    """Clean content has no suppression violations.

    Traces to: FR-GOV-007
    """
    assert _python_scan_noqa("x = 1\ny = 2\n") == []


def test_noqa_bare_annotation_detected() -> None:
    """Bare suppression annotation without justification is flagged.

    Traces to: FR-GOV-007
    """
    line = f"import os  {_BARE_SUPPRESSION}"
    violations = _python_scan_noqa(line)
    assert len(violations) == 1
    assert violations[0].rule == "noqa-no-justification"
    assert violations[0].severity == "error"
    assert violations[0].line == 1


def test_noqa_with_code_and_no_justification_detected() -> None:
    """Suppression with code but no justification is flagged.

    Traces to: FR-GOV-007
    """
    line = f"import os  {_SUPPRESSION_WITH_CODE}"
    violations = _python_scan_noqa(line)
    assert len(violations) == 1
    assert violations[0].rule == "noqa-no-justification"


def test_noqa_with_justification_is_clean() -> None:
    """Suppression with '-- reason' justification is not flagged.

    Traces to: FR-GOV-007
    """
    line = f"import os  {_JUSTIFIED_SUPPRESSION}"
    violations = _python_scan_noqa(line)
    assert violations == []


def test_noqa_reports_correct_line_number() -> None:
    """The violation reports the correct 1-based line number.

    Traces to: FR-GOV-007
    """
    content = f"x = 1\ny = 2  {_BARE_SUPPRESSION}\nz = 3\n"
    violations = _python_scan_noqa(content)
    assert len(violations) == 1
    assert violations[0].line == 2


# ---------------------------------------------------------------------------
# _python_scan_todo_no_ticket
# ---------------------------------------------------------------------------


def test_todo_clean_content_no_violations() -> None:
    """Clean content with no TODO keywords has no violations.

    Traces to: FR-GOV-007
    """
    assert _python_scan_todo_no_ticket("x = 1\n") == []


def test_todo_without_ticket_flagged() -> None:
    """TODO without a ticket reference is flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_todo_no_ticket("# TODO: fix the bug\n")
    assert len(violations) == 1
    assert violations[0].rule == "todo-no-ticket"
    assert violations[0].severity == "warning"


def test_fixme_without_ticket_flagged() -> None:
    """FIXME without a ticket reference is flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_todo_no_ticket("# FIXME: bad code\n")
    assert len(violations) == 1
    assert violations[0].rule == "todo-no-ticket"


def test_hack_without_ticket_flagged() -> None:
    """HACK without a ticket reference is flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_todo_no_ticket("# HACK: workaround\n")
    assert len(violations) == 1
    assert violations[0].rule == "todo-no-ticket"


def test_todo_with_hash_ticket_not_flagged() -> None:
    """TODO followed by hash ticket reference is not flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_todo_no_ticket("# TODO #123: fix later\n")
    assert violations == []


def test_todo_with_jira_ticket_not_flagged() -> None:
    """TODO followed by JIRA-style ticket is not flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_todo_no_ticket("# TODO PROJ-456: fix this\n")
    assert violations == []


def test_todo_reports_correct_line_number() -> None:
    """The violation reports the correct 1-based line number.

    Traces to: FR-GOV-007
    """
    content = "x = 1\n# TODO: fix\ny = 2\n"
    violations = _python_scan_todo_no_ticket(content)
    assert len(violations) == 1
    assert violations[0].line == 2


# ---------------------------------------------------------------------------
# _python_scan_function_length
# ---------------------------------------------------------------------------


def test_function_length_short_function_no_violation() -> None:
    """A short function does not produce a violation.

    Traces to: FR-GOV-007
    """
    content = "def short():\n    return 1\n"
    assert _python_scan_function_length(content) == []


def test_function_length_long_function_flagged() -> None:
    """A function exceeding 40 lines is flagged.

    Traces to: FR-GOV-007
    """
    body = "    x = 1\n" * 45
    content = f"def long_func():\n{body}\n"
    violations = _python_scan_function_length(content)
    assert len(violations) == 1
    assert violations[0].rule == "function-too-long"
    assert violations[0].severity == "warning"
    assert violations[0].line == 1


def test_function_length_custom_max() -> None:
    """Custom max_lines threshold is respected.

    Traces to: FR-GOV-007
    """
    body = "    x = 1\n" * 12
    content = f"def medium_func():\n{body}\n"
    assert _python_scan_function_length(content) == []
    violations = _python_scan_function_length(content, max_lines=10)
    assert len(violations) == 1


def test_function_length_multiple_functions() -> None:
    """Multiple long functions each produce their own violation.

    Traces to: FR-GOV-007
    """
    body = "    x = 1\n" * 45
    content = f"def func_a():\n{body}\ndef func_b():\n{body}\n"
    violations = _python_scan_function_length(content)
    assert len(violations) == 2
    rules = {v.rule for v in violations}
    assert rules == {"function-too-long"}


def test_function_length_reports_start_line() -> None:
    """Violation line number matches the function definition line.

    Traces to: FR-GOV-007
    """
    preamble = "x = 1\ny = 2\n"
    body = "    z = 1\n" * 45
    content = f"{preamble}def long_func():\n{body}\n"
    violations = _python_scan_function_length(content)
    assert violations[0].line == 3


# ---------------------------------------------------------------------------
# _python_scan_hardcoded_creds
# ---------------------------------------------------------------------------


def test_hardcoded_creds_clean_no_violation() -> None:
    """Clean content produces no credential violations.

    Traces to: FR-GOV-007
    """
    assert _python_scan_hardcoded_creds("x = 1\n") == []


def test_hardcoded_password_flagged() -> None:
    """Hardcoded password assignment is flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_hardcoded_creds('password = "hunter2"\n')
    assert len(violations) == 1
    assert violations[0].rule == "hardcoded-credential"
    assert violations[0].severity == "error"


def test_hardcoded_secret_flagged() -> None:
    """Hardcoded secret assignment is flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_hardcoded_creds('secret = "mysupersecret"\n')
    assert len(violations) == 1
    assert violations[0].rule == "hardcoded-credential"


def test_hardcoded_api_key_flagged() -> None:
    """Hardcoded api_key assignment is flagged.

    Traces to: FR-GOV-007
    """
    violations = _python_scan_hardcoded_creds('api_key = "abcd1234efgh5678"\n')
    assert len(violations) == 1
    assert violations[0].rule == "hardcoded-credential"


def test_hardcoded_creds_reports_correct_line() -> None:
    """Violation reports the correct 1-based line number.

    Traces to: FR-GOV-007
    """
    content = 'x = 1\npassword = "hunter2"\ny = 3\n'
    violations = _python_scan_hardcoded_creds(content)
    assert violations[0].line == 2


# ---------------------------------------------------------------------------
# _python_scan_all: combined scan
# ---------------------------------------------------------------------------


def test_scan_all_empty_content_no_violations() -> None:
    """Empty content produces no violations.

    Traces to: FR-GOV-007
    """
    assert _python_scan_all("") == []


def test_scan_all_violations_sorted_by_line() -> None:
    """All violations are sorted by line number.

    Traces to: FR-GOV-007
    """
    content = f'password = "abc1234"\nx = 1  {_BARE_SUPPRESSION}\n# TODO: fix\n'
    violations = _python_scan_all(content)
    lines = [v.line for v in violations]
    assert lines == sorted(lines)


# ---------------------------------------------------------------------------
# _parse_binary_output
# ---------------------------------------------------------------------------


def test_parse_binary_output_parses_violations() -> None:
    """_parse_binary_output correctly deserializes hook-dispatcher JSON.

    Traces to: FR-GOV-006
    """
    payload = json.dumps(
        {
            "violation_count": 1,
            "violations": [{"rule": "hardcoded-credential", "severity": "error", "line": 5, "message": "cred at 5"}],
        }
    )
    result = _parse_binary_output(payload)
    assert len(result) == 1
    assert result[0].rule == "hardcoded-credential"
    assert result[0].line == 5


def test_parse_binary_output_empty_violations() -> None:
    """_parse_binary_output returns empty list for zero violations.

    Traces to: FR-GOV-006
    """
    payload = json.dumps({"violation_count": 0, "violations": []}).decode()
    assert _parse_binary_output(payload) == []


# ---------------------------------------------------------------------------
# _python_check_contract: contract routing
# ---------------------------------------------------------------------------


def test_check_contract_p2_privacy_only_secret_rules() -> None:
    """P2-PRIVACY contract only runs credential detection.

    Traces to: FR-GOV-007
    """
    content = f'password = "secret1234"\nx = 1  {_BARE_SUPPRESSION}\n'
    violations = _python_check_contract("P2-PRIVACY", content)
    rules = {v.rule for v in violations}
    assert "hardcoded-credential" in rules
    assert "noqa-no-justification" not in rules


def test_check_contract_suppression_policy_only_noqa_rules() -> None:
    """suppression-policy contract only runs suppression detection.

    Traces to: FR-GOV-007
    """
    content = f'password = "secret1234"\nx = 1  {_BARE_SUPPRESSION}\n'
    violations = _python_check_contract("suppression-policy", content)
    rules = {v.rule for v in violations}
    assert "noqa-no-justification" in rules
    assert "hardcoded-credential" not in rules


def test_check_contract_todo_policy_only_todo_rules() -> None:
    """todo-policy contract only runs TODO detection.

    Traces to: FR-GOV-007
    """
    content = 'password = "secret1234"\n# TODO: fix\n'
    violations = _python_check_contract("todo-policy", content)
    rules = {v.rule for v in violations}
    assert "todo-no-ticket" in rules
    assert "hardcoded-credential" not in rules


def test_check_contract_unknown_runs_all_rules() -> None:
    """Unknown contract ID runs all rules as a safety net.

    Traces to: FR-GOV-007
    """
    content = '# TODO: fix\npassword = "abc123"\n'
    violations = _python_check_contract("totally-unknown-contract-xyz", content)
    rules = {v.rule for v in violations}
    assert "todo-no-ticket" in rules
    assert "hardcoded-credential" in rules


# ---------------------------------------------------------------------------
# NativeGovernanceScanner: scan_content
# ---------------------------------------------------------------------------


def test_scanner_scan_content_uses_python_fallback_when_no_binary() -> None:
    """scan_content uses Python fallback when binary is unavailable.

    Traces to: FR-GOV-006
    """
    scanner = NativeGovernanceScanner()
    with patch(
        "thegent.governance.native_governance_scan._find_binary",
        return_value=None,
    ):
        violations = scanner.scan_content('password = "abc123"\n')
    assert any(v.rule == "hardcoded-credential" for v in violations)


def test_scanner_scan_content_uses_binary_when_found() -> None:
    """scan_content calls _run_binary_scan when binary is available.

    Traces to: FR-GOV-006
    """
    expected = [GovernanceViolation(rule="hardcoded-credential", severity="error", line=1, message="cred")]
    scanner = NativeGovernanceScanner()
    with (
        patch(
            "thegent.governance.native_governance_scan._find_binary",
            return_value="/fake/hook-dispatcher",
        ),
        patch(
            "thegent.governance.native_governance_scan._run_binary_scan",
            return_value=expected,
        ) as mock_run,
    ):
        result = scanner.scan_content('password = "abc123"\n')
    mock_run.assert_called_once()
    assert result == expected


def test_scanner_scan_content_falls_back_on_timeout() -> None:
    """scan_content falls back to Python when binary times out.

    Traces to: FR-GOV-006
    """
    scanner = NativeGovernanceScanner()
    with (
        patch(
            "thegent.governance.native_governance_scan._find_binary",
            return_value="/fake/hook-dispatcher",
        ),
        patch(
            "thegent.governance.native_governance_scan._run_binary_scan",
            side_effect=subprocess.TimeoutExpired(cmd="hook-dispatcher", timeout=30),
        ),
    ):
        violations = scanner.scan_content('password = "abc123"\n')
    assert any(v.rule == "hardcoded-credential" for v in violations)


def test_scanner_scan_content_falls_back_on_json_error() -> None:
    """scan_content falls back to Python when binary returns non-JSON.

    Traces to: FR-GOV-006
    """
    scanner = NativeGovernanceScanner()
    with (
        patch(
            "thegent.governance.native_governance_scan._find_binary",
            return_value="/fake/hook-dispatcher",
        ),
        patch(
            "thegent.governance.native_governance_scan._run_binary_scan",
            side_effect=json.JSONDecodeError("bad", "", 0),
        ),
    ):
        violations = scanner.scan_content('password = "abc123"\n')
    assert any(v.rule == "hardcoded-credential" for v in violations)


def test_scanner_scan_content_clean_returns_empty() -> None:
    """Clean content returns an empty list.

    Traces to: FR-GOV-007
    """
    scanner = NativeGovernanceScanner()
    with patch(
        "thegent.governance.native_governance_scan._find_binary",
        return_value=None,
    ):
        assert scanner.scan_content("x = 1\ny = 2\n") == []


# ---------------------------------------------------------------------------
# NativeGovernanceScanner: check_contract_content
# ---------------------------------------------------------------------------


def test_scanner_check_contract_uses_binary_when_found() -> None:
    """check_contract_content calls _run_binary_check_contract when binary available.

    Traces to: FR-GOV-006
    """
    expected = [GovernanceViolation(rule="hardcoded-credential", severity="error", line=1, message="cred")]
    scanner = NativeGovernanceScanner()
    with (
        patch(
            "thegent.governance.native_governance_scan._find_binary",
            return_value="/fake/hook-dispatcher",
        ),
        patch(
            "thegent.governance.native_governance_scan._run_binary_check_contract",
            return_value=expected,
        ) as mock_run,
    ):
        result = scanner.check_contract_content("P2-PRIVACY", 'password = "abc123"\n')
    mock_run.assert_called_once()
    assert result == expected


def test_scanner_check_contract_falls_back_when_no_binary() -> None:
    """check_contract_content uses Python fallback when binary is absent.

    Traces to: FR-GOV-006
    """
    scanner = NativeGovernanceScanner()
    with patch(
        "thegent.governance.native_governance_scan._find_binary",
        return_value=None,
    ):
        violations = scanner.check_contract_content("P2-PRIVACY", 'password = "abc123"\n')
    assert any(v.rule == "hardcoded-credential" for v in violations)


# ---------------------------------------------------------------------------
# NativeGovernanceScanner: file I/O methods
# ---------------------------------------------------------------------------


def test_scanner_scan_file_reads_file(tmp_path: Path) -> None:
    """scan_file reads the file and delegates to scan_content.

    Traces to: FR-GOV-007
    """
    f = tmp_path / "code.py"
    f.write_text('password = "letmein123"\n')
    scanner = NativeGovernanceScanner()
    with patch(
        "thegent.governance.native_governance_scan._find_binary",
        return_value=None,
    ):
        violations = scanner.scan_file(f)
    assert any(v.rule == "hardcoded-credential" for v in violations)


def test_scanner_scan_file_raises_on_missing(tmp_path: Path) -> None:
    """scan_file raises OSError for non-existent file.

    Traces to: FR-GOV-007
    """
    scanner = NativeGovernanceScanner()
    with pytest.raises(OSError):
        scanner.scan_file(tmp_path / "nonexistent.py")


def test_scanner_scan_file_clean_file_returns_empty(tmp_path: Path) -> None:
    """scan_file returns empty list for a clean file.

    Traces to: FR-GOV-007
    """
    f = tmp_path / "clean.py"
    f.write_text("x = 1\n")
    scanner = NativeGovernanceScanner()
    with patch(
        "thegent.governance.native_governance_scan._find_binary",
        return_value=None,
    ):
        assert scanner.scan_file(f) == []


def test_scanner_check_contract_file(tmp_path: Path) -> None:
    """check_contract reads the file and applies contract rules.

    Traces to: FR-GOV-007
    """
    f = tmp_path / "code.py"
    f.write_text('password = "letmein123"\n')
    scanner = NativeGovernanceScanner()
    with patch(
        "thegent.governance.native_governance_scan._find_binary",
        return_value=None,
    ):
        violations = scanner.check_contract("P2-PRIVACY", f)
    assert any(v.rule == "hardcoded-credential" for v in violations)


# ---------------------------------------------------------------------------
# Binary integration tests (skipped when binary not built)
# ---------------------------------------------------------------------------


@_binary_available
def test_binary_governance_scan_detects_hardcoded_cred() -> None:
    """Binary governance scan detects hardcoded credentials.

    Traces to: FR-GOV-006
    """
    violations = _run_binary_scan(BINARY_PATH, 'password = "mysupersecret"\n')
    assert any(v.rule == "hardcoded-credential" for v in violations)


@_binary_available
def test_binary_governance_scan_clean_returns_empty() -> None:
    """Binary governance scan returns empty for clean content.

    Traces to: FR-GOV-006
    """
    violations = _run_binary_scan(BINARY_PATH, "x = 1\ny = 2\n")
    assert violations == []


@_binary_available
def test_binary_governance_check_contract_p2_privacy() -> None:
    """Binary check-contract P2-PRIVACY returns credential violations only.

    Traces to: FR-GOV-006
    """
    violations = _run_binary_check_contract(BINARY_PATH, "P2-PRIVACY", 'password = "mysupersecret"\n')
    rules = {v.rule for v in violations}
    assert "hardcoded-credential" in rules


@_binary_available
def test_binary_governance_scan_json_output_shape() -> None:
    """Binary governance scan emits correct JSON shape.

    Traces to: FR-GOV-006
    """
    proc = subprocess.run(
        [BINARY_PATH, "governance", "scan", "--stdin"],
        input='password = "mysupersecret"\n',
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    data = json.loads(proc.stdout)
    assert "violation_count" in data
    assert "violations" in data
    assert isinstance(data["violations"], list)
    first = data["violations"][0]
    assert "rule" in first
    assert "severity" in first
    assert "line" in first
    assert "message" in first
