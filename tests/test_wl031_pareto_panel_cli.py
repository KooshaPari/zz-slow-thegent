"""WL-031 tests for `routing pareto-panel` CLI behavior."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from thegent.cli.apps.routing import app as routing_app

runner = CliRunner()


def _audit_record(
    provider: str, model: str, latency_ms: int, cost: float
) -> dict[str, object]:
    return {
        "timestamp": "2026-02-23T00:00:00Z",
        "decision_id": f"decision-{provider}-{latency_ms}",
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
        "cost": cost,
        "prev_hash": "",
        "hash": "abc123",
    }


def _write_audit(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_routing_pareto_panel_json_output(tmp_path: Path) -> None:
    audit = tmp_path / "routing_audit.jsonl"
    _write_audit(
        audit,
        [
            json.dumps(_audit_record("lifecycle", "gemini-3-flash", 15, 0.002)),
            json.dumps(_audit_record("thegent", "claude-sonnet-4.6", 40, 0.010)),
        ],
    )

    result = runner.invoke(
        routing_app, ["pareto-panel", "--audit", str(audit), "--format", "json"]
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["current"]["provider"] == "thegent"
    assert payload["current"]["model"] == "claude-sonnet-4.6"
    assert payload["parse_errors"] == []
    assert len(payload["providers"]) == 2


def test_routing_pareto_panel_rich_output(tmp_path: Path) -> None:
    audit = tmp_path / "routing_audit.jsonl"
    _write_audit(
        audit,
        [
            json.dumps(_audit_record("lifecycle", "gemini-3-flash", 10, 0.001)),
            json.dumps(_audit_record("thegent", "claude-sonnet-4.6", 25, 0.005)),
        ],
    )

    result = runner.invoke(
        routing_app, ["pareto-panel", "--audit", str(audit), "--format", "rich"]
    )

    assert result.exit_code == 0
    assert "Pareto Frontier Panel" in result.output
    assert "Current:" in result.output
    assert "provider=thegent" in result.output


def test_routing_pareto_panel_strict_rejects_malformed_row(tmp_path: Path) -> None:
    audit = tmp_path / "routing_audit.jsonl"
    _write_audit(
        audit,
        [
            "{not-json}",
            json.dumps(_audit_record("lifecycle", "gemini-3-flash", 12, 0.0012)),
        ],
    )

    result = runner.invoke(
        routing_app,
        ["pareto-panel", "--audit", str(audit), "--strict", "--format", "json"],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert "Malformed JSON in audit file" in str(result.exception)


def test_routing_pareto_panel_non_strict_skips_malformed_row(tmp_path: Path) -> None:
    audit = tmp_path / "routing_audit.jsonl"
    _write_audit(
        audit,
        [
            "{not-json}",
            json.dumps(_audit_record("lifecycle", "gemini-3-flash", 14, 0.0014)),
        ],
    )

    result = runner.invoke(
        routing_app,
        ["pareto-panel", "--audit", str(audit), "--no-strict", "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["current"]["provider"] == "lifecycle"
    assert payload["history"]
    assert payload["parse_errors"] == ["line 1"]
