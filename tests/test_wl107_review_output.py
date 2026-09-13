"""WL-107 focused tests for structured review output validation."""

from __future__ import annotations

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.agents.review_output import parse_review_output, validate_review_output
from thegent.cli.apps.main import app

runner = CliRunner()


def test_validate_review_output_accepts_valid_payload() -> None:
    payload = {
        "summary": "Two actionable findings.",
        "overall_rating": 72,
        "issues": [
            {
                "file": "src/main.py",
                "line": 12,
                "severity": "high",
                "message": "Potential null dereference.",
                "suggestion": "Guard `obj` before access.",
            }
        ],
    }

    validated = validate_review_output(payload)

    assert validated["summary"] == payload["summary"]
    assert validated["overall_rating"] == 72
    assert validated["issues"][0]["severity"] == "high"


def test_validate_review_output_rejects_legacy_rating_alias() -> None:
    payload = {
        "summary": "Two actionable findings.",
        "rating": 72,
        "issues": [],
    }

    with pytest.raises(ValueError, match="missing required keys: overall_rating"):
        validate_review_output(payload)


def test_validate_review_output_trims_string_fields() -> None:
    payload = {
        "summary": "  Two actionable findings.  ",
        "overall_rating": 72,
        "issues": [
            {
                "file": "  src/main.py  ",
                "line": 12,
                "severity": "high",
                "message": "  Potential null dereference. ",
                "suggestion": " Guard `obj` before access.  ",
            }
        ],
    }

    validated = validate_review_output(payload)

    assert validated["summary"] == "Two actionable findings."
    assert validated["issues"][0]["file"] == "src/main.py"
    assert validated["issues"][0]["message"] == "Potential null dereference."
    assert validated["issues"][0]["suggestion"] == "Guard `obj` before access."


def test_validate_review_output_rejects_invalid_severity() -> None:
    payload = {
        "summary": "x",
        "overall_rating": 80,
        "issues": [
            {
                "file": "src/a.py",
                "line": 1,
                "severity": "urgent",
                "message": "bad",
                "suggestion": "fix",
            }
        ],
    }

    with pytest.raises(ValueError, match="severity must be one of"):
        validate_review_output(payload)


def test_validate_review_output_rejects_boolean_issue_line() -> None:
    payload = {
        "summary": "x",
        "overall_rating": 80,
        "issues": [
            {
                "file": "src/a.py",
                "line": True,
                "severity": "high",
                "message": "bad",
                "suggestion": "fix",
            }
        ],
    }

    with pytest.raises(ValueError, match=r"issues\[0\]\.line must be an integer >= 1"):
        validate_review_output(payload)


def test_validate_review_output_rejects_issue_with_missing_fields() -> None:
    payload = {
        "summary": "x",
        "overall_rating": 80,
        "issues": [
            {
                "file": "src/a.py",
                "line": 1,
                "severity": "high",
                "message": "bad",
            }
        ],
    }

    with pytest.raises(ValueError, match="missing required keys"):
        validate_review_output(payload)


def test_validate_review_output_rejects_issue_with_extra_fields() -> None:
    payload = {
        "summary": "x",
        "overall_rating": 80,
        "issues": [
            {
                "file": "src/a.py",
                "line": 1,
                "severity": "high",
                "message": "bad",
                "suggestion": "fix",
                "column": 9,
            }
        ],
    }

    with pytest.raises(ValueError, match="unsupported keys"):
        validate_review_output(payload)


def test_validate_review_output_rejects_unsupported_top_level_keys() -> None:
    payload = {
        "summary": "x",
        "overall_rating": 80,
        "rating": 60,
        "issues": [],
    }

    with pytest.raises(ValueError, match="unsupported keys: rating"):
        validate_review_output(payload)


def test_parse_review_output_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_review_output("{invalid")


def test_review_cli_exit_code_zero_without_issues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kwargs: {
            "exit_code": 0,
            "stdout": '{"summary":"ok","overall_rating":100,"issues":[]}',
        },
    )

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 0


def test_review_cli_exit_code_one_with_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kwargs: {
            "exit_code": 0,
            "stdout": (
                '{"summary":"issues","overall_rating":70,"issues":[{"file":"a.py","line":1,'
                '"severity":"high","message":"m","suggestion":"s"}]}'
            ),
        },
    )

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 1


def test_review_cli_exit_code_one_with_issues_json_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kwargs: {
            "exit_code": 0,
            "stdout": (
                '{"summary":"issues","overall_rating":70,"issues":[{"file":"a.py","line":1,'
                '"severity":"high","message":"m","suggestion":"s"}]}'
            ),
        },
    )

    result = runner.invoke(app, ["review", "check this", "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["issues"][0]["file"] == "a.py"


def test_review_cli_exit_code_two_on_contract_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kwargs: {"exit_code": 0, "stdout": "not-json"},
    )

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 2
    assert "Review output validation failed" in result.stdout


def test_review_cli_propagates_nonzero_run_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kwargs: {"exit_code": 7, "stderr": "runner failed"},
    )

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 7
    assert "Review run failed" in result.stdout


def test_review_cli_json_contract_includes_context_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kwargs: {
            "exit_code": 0,
            "stdout": '{"summary":"ok","overall_rating":100,"issues":[]}',
            "context_usage": {
                "used": 700,
                "max": 1000,
                "ratio": 0.7,
                "display": "700/1k",
                "level": "yellow",
            },
        },
    )

    result = runner.invoke(app, ["review", "check this", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "summary": "ok",
        "overall_rating": 100,
        "issues": [],
        "context_usage": {
            "used": 700,
            "max": 1000,
            "ratio": 0.7,
            "display": "700/1k",
            "level": "yellow",
        },
    }
