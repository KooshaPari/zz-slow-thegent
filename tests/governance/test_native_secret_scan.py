"""Tests for native_secret_scan: BKM-07 hook-dispatcher integration.

Covers:
  - Python fallback implementation (always available, no binary needed)
  - Binary integration path (when hook-dispatcher is present)
  - SecretMatch dataclass shape
  - Masking correctness
  - All named pattern types

Traces to: FR-SEC-001 (secret detection), FR-GOV-006 (native binary integration)
"""

from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest

from thegent.governance.native_secret_scan import (
    SecretMatch,
    _mask,
    _python_scan,
    _run_binary,
    scan_secrets,
    scan_secrets_file,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# _mask helper
# ---------------------------------------------------------------------------


def test_mask_short_string() -> None:
    """Strings of 8 chars or fewer are fully masked.

    Traces to: FR-SEC-001
    """
    assert _mask("tooshort") == "****"
    assert _mask("ab") == "****"


def test_mask_long_string() -> None:
    """Longer strings show first 4 + last 2 chars.

    Traces to: FR-SEC-001
    """
    result = _mask("sk-ant-ABCDEFGHIJKLMNO")
    assert result.startswith("sk-a")
    assert result.endswith("NO")
    assert "****" in result
    # The raw secret is never in the output
    assert "ABCDEFGHIJKLM" not in result


def test_mask_exactly_nine_chars() -> None:
    """Nine-char string masks correctly (boundary case).

    Traces to: FR-SEC-001
    """
    result = _mask("123456789")
    assert result == "1234****89"


# ---------------------------------------------------------------------------
# _python_scan: empty and clean content
# ---------------------------------------------------------------------------


def test_python_scan_empty_content() -> None:
    """Empty content returns no matches.

    Traces to: FR-SEC-001
    """
    assert _python_scan("") == []


def test_python_scan_clean_content() -> None:
    """Normal source code without secrets returns no matches.

    Traces to: FR-SEC-001
    """
    content = """
def greet(name: str) -> str:
    return f"Hello, {name}!"

x = 42
"""
    assert _python_scan(content) == []


# ---------------------------------------------------------------------------
# _python_scan: pattern coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("content", "expected_kind"),
    [
        # OpenAI
        ("sk-" + "a" * 48, "openai_api_key"),
        # OpenAI project key
        ("sk-proj-" + "b" * 48, "openai_proj_key"),
        # Anthropic
        ("sk-ant-" + "c" * 90, "anthropic_api_key"),
        # Google Cloud
        ("AIza" + "d" * 35, "google_cloud_key"),
        # Slack
        ("xoxb-123456789012345", "slack_token"),
        # Private key block
        ("-----BEGIN RSA PRIVATE KEY-----", "private_key_block"),
        # Square
        ("sq0atp-" + "e" * 22, "square_access_token"),
        # AWS access key
        ("AKIA" + "F" * 16, "aws_access_key_id"),
        # GitHub PAT
        ("ghp_" + "g" * 36, "github_pat"),
        # GitHub OAuth
        ("gho_" + "h" * 36, "github_oauth"),
        # GitHub App token
        ("ghs_" + "i" * 36, "github_app_token"),
        # Generic hex secret
        ("password=" + "a1b2c3d4e5" * 4, "generic_hex_secret"),
    ],
)
def test_python_scan_detects_pattern(content: str, expected_kind: str) -> None:
    """Each named secret pattern is detected by the Python fallback.

    Traces to: FR-SEC-001
    """
    matches = _python_scan(content)
    assert matches, f"Expected match for {expected_kind!r} in: {content[:40]!r}"
    kinds = {m.kind for m in matches}
    assert expected_kind in kinds, f"Expected kind {expected_kind!r}, got {kinds}"


def test_python_scan_returns_correct_line_number() -> None:
    """The line number reported is 1-based and accurate.

    Traces to: FR-SEC-001
    """
    content = "line one\nline two\nghp_" + "x" * 36 + "\nline four"
    matches = _python_scan(content)
    assert len(matches) == 1
    assert matches[0].line == 3


def test_python_scan_masked_secret_not_raw() -> None:
    """The masked field never contains the raw secret value.

    Traces to: FR-SEC-001
    """
    raw_key = "ghp_" + "Z" * 36
    matches = _python_scan(raw_key)
    assert matches
    assert raw_key not in matches[0].masked
    assert "****" in matches[0].masked


def test_python_scan_one_match_per_line() -> None:
    """Only one match is emitted per line even if multiple patterns could match.

    Traces to: FR-SEC-001
    """
    # Line with both an OpenAI key and generic secret pattern
    line = "sk-" + "a" * 48 + " password=" + "b" * 20
    matches = _python_scan(line)
    # Should only capture the first matching pattern
    assert len(matches) == 1


def test_python_scan_multiline() -> None:
    """Secrets on different lines each produce a separate match.

    Traces to: FR-SEC-001
    """
    content = "AKIA" + "F" * 16 + "\nnormal line\nghp_" + "g" * 36 + "\n"
    matches = _python_scan(content)
    assert len(matches) == 2
    kinds = {m.kind for m in matches}
    assert "aws_access_key_id" in kinds
    assert "github_pat" in kinds


# ---------------------------------------------------------------------------
# SecretMatch dataclass
# ---------------------------------------------------------------------------


def test_secret_match_is_frozen() -> None:
    """SecretMatch instances are immutable (frozen dataclass).

    Traces to: FR-SEC-001
    """
    sm = SecretMatch(kind="test", line=1, masked="****")
    # Frozen dataclasses raise FrozenInstanceError on attribute assignment.
    # We call setattr via the class to invoke the frozen guard.
    with pytest.raises(dataclasses.FrozenInstanceError):
        sm.__class__.__setattr__(sm, "kind", "other")


def test_secret_match_fields() -> None:
    """SecretMatch exposes kind, line, and masked fields.

    Traces to: FR-SEC-001
    """
    sm = SecretMatch(kind="aws_access_key_id", line=5, masked="AKIA****ID")
    assert sm.kind == "aws_access_key_id"
    assert sm.line == 5
    assert sm.masked == "AKIA****ID"


# ---------------------------------------------------------------------------
# scan_secrets: delegates to binary when present
# ---------------------------------------------------------------------------


def test_scan_secrets_uses_python_fallback_when_no_binary() -> None:
    """When no binary is found, scan_secrets uses the Python fallback.

    Traces to: FR-GOV-006
    """
    with patch(
        "thegent.governance.native_secret_scan._find_binary",
        return_value=None,
    ):
        matches = scan_secrets("ghp_" + "x" * 36)
        assert matches
        assert matches[0].kind == "github_pat"


def test_scan_secrets_uses_binary_when_found() -> None:
    """When the binary is found, scan_secrets calls _run_binary.

    Traces to: FR-GOV-006
    """
    expected = [SecretMatch(kind="github_pat", line=1, masked="ghp_****36")]
    with (
        patch(
            "thegent.governance.native_secret_scan._find_binary",
            return_value="/fake/hook-dispatcher",
        ),
        patch(
            "thegent.governance.native_secret_scan._run_binary",
            return_value=expected,
        ) as mock_run,
    ):
        result = scan_secrets("ghp_" + "x" * 36)
    mock_run.assert_called_once()
    assert result == expected


def test_scan_secrets_falls_back_on_binary_timeout() -> None:
    """When binary times out, scan_secrets falls back to Python scan.

    Traces to: FR-GOV-006
    """
    with (
        patch(
            "thegent.governance.native_secret_scan._find_binary",
            return_value="/fake/hook-dispatcher",
        ),
        patch(
            "thegent.governance.native_secret_scan._run_binary",
            side_effect=subprocess.TimeoutExpired(cmd="hook-dispatcher", timeout=30),
        ),
    ):
        matches = scan_secrets("ghp_" + "y" * 36)
        # Python fallback still detects the secret
        assert matches
        assert matches[0].kind == "github_pat"


def test_scan_secrets_falls_back_on_json_error() -> None:
    """When binary returns non-JSON, scan_secrets falls back to Python scan.

    Traces to: FR-GOV-006
    """
    with (
        patch(
            "thegent.governance.native_secret_scan._find_binary",
            return_value="/fake/hook-dispatcher",
        ),
        patch(
            "thegent.governance.native_secret_scan._run_binary",
            side_effect=json.JSONDecodeError("bad", "", 0),
        ),
    ):
        matches = scan_secrets("ghp_" + "z" * 36)
        assert matches
        assert matches[0].kind == "github_pat"


def test_scan_secrets_clean_returns_empty() -> None:
    """Clean content returns an empty list regardless of code path.

    Traces to: FR-SEC-001
    """
    with patch(
        "thegent.governance.native_secret_scan._find_binary",
        return_value=None,
    ):
        assert scan_secrets("hello world\nno secrets here\n") == []


# ---------------------------------------------------------------------------
# _run_binary: integration with actual binary (skipped when binary absent)
# ---------------------------------------------------------------------------


BINARY_PATH = str(
    Path(__file__).parent.parent.parent / "hooks" / "hook-dispatcher" / "target" / "release" / "hook-dispatcher"
)

_binary_available = pytest.mark.skipif(
    not Path(BINARY_PATH).is_file(),
    reason="hook-dispatcher binary not built; run `cargo build --release` in hooks/hook-dispatcher/",
)


@_binary_available
def test_run_binary_detects_github_pat() -> None:
    """_run_binary correctly calls the compiled binary and parses JSON output.

    Traces to: FR-GOV-006
    """
    content = "ghp_" + "A" * 36
    matches = _run_binary(BINARY_PATH, content)
    assert matches
    assert matches[0].kind == "github_pat"
    assert "****" in matches[0].masked
    assert content not in matches[0].masked


@_binary_available
def test_run_binary_clean_content_returns_empty() -> None:
    """Binary returns empty matches for clean content.

    Traces to: FR-GOV-006
    """
    matches = _run_binary(BINARY_PATH, "no secrets here at all\n")
    assert matches == []


@_binary_available
def test_run_binary_detects_aws_key() -> None:
    """Binary detects AWS access key IDs.

    Traces to: FR-SEC-001
    """
    content = "AKIA" + "B" * 16
    matches = _run_binary(BINARY_PATH, content)
    assert any(m.kind == "aws_access_key_id" for m in matches)


@_binary_available
def test_run_binary_detects_anthropic_key() -> None:
    """Binary detects Anthropic API keys.

    Traces to: FR-SEC-001
    """
    content = "sk-ant-" + "C" * 90
    matches = _run_binary(BINARY_PATH, content)
    assert any(m.kind == "anthropic_api_key" for m in matches)


@_binary_available
def test_run_binary_json_output_shape() -> None:
    """Binary JSON output contains found=True and a non-empty matches array.

    Traces to: FR-GOV-006
    """
    proc = subprocess.run(
        [BINARY_PATH, "scan-secrets", "--stdin"],
        input="ghp_" + "D" * 36,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    data = json.loads(proc.stdout)
    assert data["found"] is True
    assert isinstance(data["matches"], list)
    assert len(data["matches"]) >= 1
    match = data["matches"][0]
    assert "kind" in match
    assert "line" in match
    assert "masked" in match


# ---------------------------------------------------------------------------
# scan_secrets_file
# ---------------------------------------------------------------------------


def test_scan_secrets_file_reads_file(tmp_path: Path) -> None:
    """scan_secrets_file reads the file and delegates to scan_secrets.

    Traces to: FR-SEC-001
    """
    secret_file = tmp_path / "config.env"
    secret_file.write_text("github_token=ghp_" + "E" * 36 + "\n")

    with patch(
        "thegent.governance.native_secret_scan._find_binary",
        return_value=None,
    ):
        matches = scan_secrets_file(secret_file)

    assert matches
    assert any(m.kind == "github_pat" for m in matches)


def test_scan_secrets_file_raises_on_missing_file(tmp_path: Path) -> None:
    """scan_secrets_file raises OSError for a non-existent file.

    Traces to: FR-SEC-001
    """
    with pytest.raises(OSError):
        scan_secrets_file(tmp_path / "nonexistent.env")


def test_scan_secrets_file_clean_file_returns_empty(tmp_path: Path) -> None:
    """scan_secrets_file returns empty list for a clean file.

    Traces to: FR-SEC-001
    """
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x = 1\n")
    with patch(
        "thegent.governance.native_secret_scan._find_binary",
        return_value=None,
    ):
        assert scan_secrets_file(clean_file) == []
