"""WL-107: Tests for thegent review command and review_impl().

Covers:
- review_impl() structured output, sandbox_mode, allowed_tools metadata
- review_impl() raises ValueError on invalid JSON output from agent
- review_impl() returns error dict when underlying run fails
- CLI exit codes: 0 (no issues), 1 (issues found), 2 (bad format / schema violation)
- CLI rich output rendering
- CLI JSON output rendering with context_usage passthrough
- CLI --model and --agent option forwarding
- review.py standalone app (review run sub-command)
- _REVIEW_ALLOWED_TOOLS and _REVIEW_SCHEMA_PREAMBLE constants

# @trace WL-107
"""

from __future__ import annotations

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.cli.apps.main import app
from thegent.cli.apps.review import app as review_app

runner = CliRunner()

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_CLEAN_RESPONSE = {
    "exit_code": 0,
    "stdout": '{"summary":"All good.","overall_rating":100,"issues":[]}',
}

_ISSUE_RESPONSE = {
    "exit_code": 0,
    "stdout": json.dumps(
        {
            "summary": "Found issues.",
            "overall_rating": 60,
            "issues": [
                {
                    "file": "src/foo.py",
                    "line": 42,
                    "severity": "high",
                    "message": "Null dereference risk.",
                    "suggestion": "Guard before access.",
                }
            ],
        }
    ).decode(),
}

_FAILED_RESPONSE = {
    "exit_code": 2,
    "stderr": "Agent crashed.",
    "error": "Agent crashed.",
}


# ---------------------------------------------------------------------------
# review_impl() unit tests
# ---------------------------------------------------------------------------


def test_review_impl_returns_sandbox_mode_read_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl must advertise sandbox_mode=read_only in result. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    assert result["sandbox_mode"] == "read_only"


def test_review_impl_returns_allowed_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl must include allowed_tools list in result. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    assert "read_file" in result["allowed_tools"]
    assert "glob" in result["allowed_tools"]
    assert "grep" in result["allowed_tools"]
    assert "web_search" in result["allowed_tools"]


def test_review_impl_exit_code_zero_no_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl exit_code=0 when issues list is empty. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    assert result["exit_code"] == 0
    assert result["issues"] == []


def test_review_impl_exit_code_one_with_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl exit_code=1 when issues are found. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _ISSUE_RESPONSE)

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    assert result["exit_code"] == 1
    assert len(result["issues"]) == 1


def test_review_impl_structured_issue_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl normalizes and returns all required issue fields. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _ISSUE_RESPONSE)

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    issue = result["issues"][0]
    assert issue["file"] == "src/foo.py"
    assert issue["line"] == 42
    assert issue["severity"] == "high"
    assert issue["message"] == "Null dereference risk."
    assert issue["suggestion"] == "Guard before access."


def test_review_impl_raises_on_invalid_json_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl raises ValueError when agent returns non-JSON. # @trace WL-107"""
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kw: {"exit_code": 0, "stdout": "not-json"},
    )

    from thegent.cli.commands.impl import review_impl

    with pytest.raises(ValueError, match="not valid JSON"):
        review_impl(prompt="check code")


def test_review_impl_accepts_fenced_json_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl accepts ```json fenced payloads from model output. # @trace WL-107"""
    fenced = """```json
{"summary":"All good.","overall_rating":100,"issues":[]}
```"""
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kw: {"exit_code": 0, "stdout": fenced},
    )

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    assert result["exit_code"] == 0
    assert result["issues"] == []


def test_review_impl_raises_when_stdout_is_not_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl raises ValueError when stdout is not a JSON string. # @trace WL-107"""
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kw: {"exit_code": 0, "stdout": None},
    )

    from thegent.cli.commands.impl import review_impl

    with pytest.raises(ValueError, match="must be a JSON string"):
        review_impl(prompt="check code")


def test_review_impl_rejects_boolean_overall_rating(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl rejects bool overall_rating to preserve integer contract. # @trace WL-107"""
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kw: {"exit_code": 0, "stdout": '{"summary":"ok","overall_rating":true,"issues":[]}'},
    )

    from thegent.cli.commands.impl import review_impl

    with pytest.raises(ValueError, match="overall_rating"):
        review_impl(prompt="check code")


def test_review_impl_returns_error_dict_on_run_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl returns error dict when underlying run_impl fails. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _FAILED_RESPONSE)

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    assert result["exit_code"] == 2
    assert "Agent crashed" in result["error"]
    assert result["issues"] == []


def test_review_impl_passes_agent_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl forwards agent and model kwargs to run_impl. # @trace WL-107"""
    captured: dict[str, object] = {}

    def _spy_run_impl(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return _CLEAN_RESPONSE

    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", _spy_run_impl)

    from thegent.cli.commands.impl import review_impl

    review_impl(prompt="check code", agent="codex", model="gpt-4o")
    assert captured.get("agent") == "codex"
    assert captured.get("model") == "gpt-4o"


def test_review_impl_injects_schema_preamble(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl prepends schema preamble to the user prompt. # @trace WL-107"""
    captured: dict[str, object] = {}

    def _spy_run_impl(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return _CLEAN_RESPONSE

    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", _spy_run_impl)

    from thegent.cli.commands.impl import review_impl

    review_impl(prompt="my prompt")
    prompt_sent = str(captured.get("prompt", ""))
    assert "overall_rating" in prompt_sent
    assert "my prompt" in prompt_sent


def test_review_impl_context_usage_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    """review_impl passes context_usage from run_impl through to result. # @trace WL-107"""
    ctx = {"used": 500, "max": 1000, "ratio": 0.5, "display": "500/1k", "level": "green"}
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kw: {**_CLEAN_RESPONSE, "context_usage": ctx},
    )

    from thegent.cli.commands.impl import review_impl

    result = review_impl(prompt="check code")
    assert result["context_usage"] == ctx


# ---------------------------------------------------------------------------
# CLI top-level `thegent review` tests
# ---------------------------------------------------------------------------


def test_cli_review_exit_code_zero_no_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review exits 0 when no issues found. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 0


def test_cli_review_exit_code_one_with_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review exits 1 when issues found. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _ISSUE_RESPONSE)

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 1


def test_cli_review_exit_code_two_on_invalid_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review exits 2 on unsupported --format value. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    result = runner.invoke(app, ["review", "check this", "--format", "xml"])

    assert result.exit_code == 2
    assert "Unsupported --format" in result.stdout


def test_cli_review_exit_code_two_on_schema_violation(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review exits 2 when agent returns invalid review JSON. # @trace WL-107"""
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kw: {"exit_code": 0, "stdout": "not-json"},
    )

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 2
    assert "Review output validation failed" in result.stdout


def test_cli_review_json_format_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review --format json outputs valid JSON with correct keys. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    result = runner.invoke(app, ["review", "check this", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["summary"] == "All good."
    assert payload["overall_rating"] == 100
    assert payload["issues"] == []


def test_cli_review_json_includes_context_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review --format json includes context_usage when present. # @trace WL-107"""
    ctx = {"used": 700, "max": 1000, "ratio": 0.7, "display": "700/1k", "level": "yellow"}
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_impl",
        lambda **_kw: {**_CLEAN_RESPONSE, "context_usage": ctx},
    )

    result = runner.invoke(app, ["review", "check this", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["context_usage"] == ctx


def test_cli_review_rich_output_no_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review rich mode prints 'No issues found' when clean. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    result = runner.invoke(app, ["review", "check this"])

    assert "No issues found" in result.stdout


def test_cli_review_rich_output_shows_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review rich mode lists issues with file/line/severity. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _ISSUE_RESPONSE)

    result = runner.invoke(app, ["review", "check this"])

    assert "src/foo.py" in result.stdout
    assert "42" in result.stdout
    # Rich console strips markup tags like [high] when rendering to plain text in tests;
    # assert on message text which is always present.
    assert "Null dereference risk" in result.stdout


def test_cli_review_propagates_agent_option(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review --agent forwards agent to review_impl. # @trace WL-107"""
    captured: dict[str, object] = {}

    def _spy(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return _CLEAN_RESPONSE

    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", _spy)

    runner.invoke(app, ["review", "check this", "--agent", "codex"])

    assert captured.get("agent") == "codex"


def test_cli_review_propagates_model_option(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review --model forwards model to review_impl. # @trace WL-107"""
    captured: dict[str, object] = {}

    def _spy(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return _CLEAN_RESPONSE

    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", _spy)

    runner.invoke(app, ["review", "check this", "--model", "gpt-4o"])

    assert captured.get("model") == "gpt-4o"


def test_cli_review_run_failure_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    """thegent review propagates non-zero exit when run_impl fails. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _FAILED_RESPONSE)

    result = runner.invoke(app, ["review", "check this"])

    assert result.exit_code == 2
    assert "Review run failed" in result.stdout


# ---------------------------------------------------------------------------
# Standalone review.py app tests
# ---------------------------------------------------------------------------


def test_review_app_run_subcommand_exits_zero_no_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """review app exits 0 when no issues (Typer collapses single-command group). # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    # Typer collapses a single-command Typer group so the prompt is passed directly.
    result = runner.invoke(review_app, ["check-code"])

    assert result.exit_code == 0


def test_review_app_run_subcommand_exits_one_with_issues(monkeypatch: pytest.MonkeyPatch) -> None:
    """review app exits 1 when issues found. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _ISSUE_RESPONSE)

    result = runner.invoke(review_app, ["check-code"])

    assert result.exit_code == 1


def test_review_app_run_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """review app --format json outputs valid JSON. # @trace WL-107"""
    monkeypatch.setattr("thegent.cli.commands.impl.run_impl", lambda **_kw: _CLEAN_RESPONSE)

    result = runner.invoke(review_app, ["check-code", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "summary" in payload
    assert "overall_rating" in payload
    assert "issues" in payload


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_review_allowed_tools_constant() -> None:
    """_REVIEW_ALLOWED_TOOLS contains the required read-only tools. # @trace WL-107"""
    from thegent.cli.commands.impl import _REVIEW_ALLOWED_TOOLS

    assert set(_REVIEW_ALLOWED_TOOLS) == {"read_file", "glob", "grep", "web_search"}


def test_review_schema_preamble_constant() -> None:
    """_REVIEW_SCHEMA_PREAMBLE includes all required output keys. # @trace WL-107"""
    from thegent.cli.commands.impl import _REVIEW_SCHEMA_PREAMBLE

    for key in ("summary", "overall_rating", "issues", "file", "line", "severity", "message", "suggestion"):
        assert key in _REVIEW_SCHEMA_PREAMBLE
