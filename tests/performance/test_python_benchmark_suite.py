from __future__ import annotations

from pathlib import Path

import orjson as json

# scripts.benchmark_python_suite module was removed.
import pytest

pytest.importorskip(
    "scripts.benchmark_python_suite",
    reason=("scripts.benchmark_python_suite module removed; benchmark suite tests skipped"),
)
from scripts.benchmark_python_suite import run_suite  # noqa: E402


@pytest.mark.requirement("WL-236")
def test_run_suite_emits_expected_shape() -> None:
    payload = run_suite(iterations=1000, mode="cold")
    assert payload["suite"] == "python-benchmark-suite-v1"
    assert payload["mode"] == "cold"
    assert isinstance(payload["benchmarks"], list)
    assert len(payload["benchmarks"]) >= 3
    for row in payload["benchmarks"]:
        assert row["iterations"] > 0
        assert row["elapsed_seconds"] >= 0
        assert row["avg_microseconds"] >= 0


@pytest.mark.requirement("WL-236")
def test_run_suite_can_be_serialized(tmp_path: Path) -> None:
    payload = run_suite(iterations=500, mode="warm")
    out = tmp_path / "bench.json"
    out.write_text(json.dumps(payload).decode(), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["suite"] == "python-benchmark-suite-v1"
    assert loaded["mode"] == "warm"


def test_run_suite_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="mode must be 'cold' or 'warm'"):
        run_suite(iterations=100, mode="invalid")
