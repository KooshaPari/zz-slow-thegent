"""WL-115 bench CLI wiring tests."""

from __future__ import annotations

from pathlib import Path

import orjson as json
from typer.testing import CliRunner

from thegent.bench.store import load_bench_records
from thegent.main import app

runner = CliRunner()


def test_bench_run_persists_one_row(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    result = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--results-path",
            str(target),
        ],
    )

    assert result.exit_code == 0
    records = load_bench_records(path=target)
    assert len(records) == 1
    assert records[0].suite == "smoke"
    assert records[0].test_id == "smoke-001"
    assert records[0].harness == "codex"


def test_bench_run_rejects_unknown_suite() -> None:
    result = runner.invoke(app, ["bench", "run", "--suite", "unknown-suite"])
    assert result.exit_code == 1
    assert "Unsupported benchmark suite" in result.stdout


def test_bench_run_supports_output_format_json(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    result = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--results-path",
            str(target),
            "--output-format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["suite"] == "smoke"
    assert payload["harness"] == "codex"
    assert payload["results_path"] == str(target)


def test_bench_run_normalizes_output_format_aliases(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    result = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--results-path",
            str(target),
            "--output-format",
            "  JSON  ",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["suite"] == "smoke"


def test_bench_compare_rejects_unknown_output_format(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    run_a = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--run-id",
            "run-a",
            "--results-path",
            str(target),
        ],
    )
    run_b = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "claude",
            "--run-id",
            "run-b",
            "--results-path",
            str(target),
        ],
    )
    assert run_a.exit_code == 0
    assert run_b.exit_code == 0

    compare = runner.invoke(
        app,
        [
            "bench",
            "compare",
            "--suite",
            "smoke",
            "--results-path",
            str(target),
            "--output-format",
            "xml",
        ],
    )
    assert compare.exit_code == 1
    assert "Unsupported output format" in compare.stdout


def test_bench_compare_returns_delta_between_harnesses(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    run_a = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--run-id",
            "run-a",
            "--results-path",
            str(target),
        ],
    )
    run_b = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "claude",
            "--run-id",
            "run-b",
            "--results-path",
            str(target),
        ],
    )
    assert run_a.exit_code == 0
    assert run_b.exit_code == 0

    compare = runner.invoke(
        app,
        [
            "bench",
            "compare",
            "--suite",
            "smoke",
            "--baseline-harness",
            "codex",
            "--candidate-harness",
            "claude",
            "--results-path",
            str(target),
            "--output-format",
            "json",
        ],
    )

    assert compare.exit_code == 0
    payload = json.loads(compare.stdout)
    assert payload["suite"] == "smoke"
    assert payload["baseline_harness"] == "codex"
    assert payload["candidate_harness"] == "claude"
    assert payload["baseline_run_id"] == "run-a"
    assert payload["candidate_run_id"] == "run-b"
    assert "latency_delta_sec" in payload
    assert "winner_margin_sec" in payload
    assert "winner_margin_pct" in payload
    assert payload["winner_margin_sec"] >= 0
    assert payload["winner_margin_pct"] >= 0
    assert payload["winner_harness"] in {"codex", "claude", "tie"}
    assert payload["winner_reason"] in {"lower_latency", "equal_latency"}


def test_bench_compare_normalizes_harness_selector_case(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    run_a = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "Codex",
            "--run-id",
            "run-a",
            "--results-path",
            str(target),
        ],
    )
    run_b = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "CLAUDE",
            "--run-id",
            "run-b",
            "--results-path",
            str(target),
        ],
    )
    assert run_a.exit_code == 0
    assert run_b.exit_code == 0

    compare = runner.invoke(
        app,
        [
            "bench",
            "compare",
            "--suite",
            "smoke",
            "--baseline-harness",
            "codeX",
            "--candidate-harness",
            "claude",
            "--results-path",
            str(target),
            "--output-format",
            "json",
        ],
    )

    assert compare.exit_code == 0
    payload = json.loads(compare.stdout)
    assert payload["baseline_harness"].lower() == "codex"
    assert payload["candidate_harness"].lower() == "claude"


def test_bench_compare_renders_table_in_rich_mode(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    run_a = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--run-id",
            "run-a",
            "--results-path",
            str(target),
        ],
    )
    run_b = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "claude",
            "--run-id",
            "run-b",
            "--results-path",
            str(target),
        ],
    )
    assert run_a.exit_code == 0
    assert run_b.exit_code == 0

    compare = runner.invoke(
        app,
        [
            "bench",
            "compare",
            "--suite",
            "smoke",
            "--baseline-harness",
            "codex",
            "--candidate-harness",
            "claude",
            "--results-path",
            str(target),
        ],
    )

    assert compare.exit_code == 0
    assert "Benchmark Compare" in compare.stdout
    assert "Latency (sec)" in compare.stdout
    assert "run-a" in compare.stdout
    assert "run-b" in compare.stdout
    assert "Winner" in compare.stdout
    assert "Winner Margin" in compare.stdout


def test_bench_compare_rejects_same_baseline_and_candidate_harness(
    tmp_path: Path,
) -> None:
    target = tmp_path / "bench-results.jsonl"
    run_a = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--run-id",
            "run-a",
            "--results-path",
            str(target),
        ],
    )
    run_b = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "claude",
            "--run-id",
            "run-b",
            "--results-path",
            str(target),
        ],
    )
    assert run_a.exit_code == 0
    assert run_b.exit_code == 0

    compare = runner.invoke(
        app,
        [
            "bench",
            "compare",
            "--suite",
            "smoke",
            "--baseline-harness",
            "codeX",
            "--candidate-harness",
            "CODEx",
            "--results-path",
            str(target),
            "--output-format",
            "json",
        ],
    )
    assert compare.exit_code == 1
    assert "Baseline and candidate harness must be different" in compare.stdout


def test_bench_compare_requires_two_harness_rows(tmp_path: Path) -> None:
    target = tmp_path / "bench-results.jsonl"
    run_one = runner.invoke(
        app,
        [
            "bench",
            "run",
            "--suite",
            "smoke",
            "--harness",
            "codex",
            "--run-id",
            "run-a",
            "--results-path",
            str(target),
        ],
    )
    assert run_one.exit_code == 0

    compare = runner.invoke(app, ["bench", "compare", "--suite", "smoke", "--results-path", str(target)])
    assert compare.exit_code == 1
    assert "Need at least two harness results" in compare.stdout
