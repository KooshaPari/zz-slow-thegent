# @trace WL-131 B90-W3-F3
"""Migration benchmark report and baseline validation for WL-131."""

from pathlib import Path

import orjson as json

REPO_ROOT = Path(__file__).parent.parent
REPORT = REPO_ROOT / "docs/reports/2026-02-21-B90-W3-F3-migration-benchmark.md"
BASELINE_JSON = REPO_ROOT / "benchmarks/baseline-wl131-parse-model-suffix.json"


def test_f3_report_exists():
    assert REPORT.exists(), f"Report not found: {REPORT}"


def test_f3_report_mentions_baseline():
    text = REPORT.read_text()
    assert "0.158" in text or "baseline" in text.lower() or "Python baseline" in text, (
        "Report must mention the baseline value (0.158) or 'baseline'"
    )


def test_f3_report_mentions_maturin_or_rust():
    text = REPORT.read_text()
    assert "maturin" in text or "Rust" in text, "Report must mention 'maturin' or 'Rust'"


def test_f3_baseline_json_exists():
    assert BASELINE_JSON.exists(), f"Baseline JSON not found: {BASELINE_JSON}"


def test_f3_baseline_json_is_valid():
    data = json.loads(BASELINE_JSON.read_text())
    assert isinstance(data, dict), "Baseline JSON must be a JSON object"
    assert "per_call_us" in data or "elapsed_s" in data, "Baseline JSON must contain timing data"
