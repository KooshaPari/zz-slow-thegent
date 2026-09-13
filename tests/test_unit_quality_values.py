from __future__ import annotations

import orjson as json

from thegent.models.quality_values import (
    get_model_quality_for_role,
    get_model_quality_index,
)


def _write_benchmarks(path):
    payload = {
        "version": 2,
        "benchmark_categories": {
            "reasoning": ["r1"],
            "agentic_coding": ["c1"],
        },
        "benchmarks_by_task_type": {
            "r1": {
                "task_type": "reasoning",
                "metric": "percent",
                "scores": {"m1": 90.0, "m2": 30.0},
            },
            "c1": {
                "task_type": "agentic_coding",
                "metric": "percent",
                "scores": {"m1": 40.0, "m2": 95.0},
            },
        },
    }
    path.write_text(json.dumps(payload).decode(), encoding="utf-8")


def test_quality_index_uses_task_type_benchmarks_when_legacy_keys_missing(tmp_path):
    bench_path = tmp_path / "benchmarks.json"
    _write_benchmarks(bench_path)

    m1 = get_model_quality_index("m1", benchmarks_path=bench_path)
    m2 = get_model_quality_index("m2", benchmarks_path=bench_path)

    assert 0.0 <= m1 <= 1.0
    assert 0.0 <= m2 <= 1.0
    assert m1 != m2


def test_quality_for_role_respects_task_type_weighting(tmp_path):
    bench_path = tmp_path / "benchmarks.json"
    _write_benchmarks(bench_path)

    reasoning_m1 = get_model_quality_for_role("m1", {"reasoning": 1.0}, benchmarks_path=bench_path)
    reasoning_m2 = get_model_quality_for_role("m2", {"reasoning": 1.0}, benchmarks_path=bench_path)
    coding_m1 = get_model_quality_for_role("m1", {"coding": 1.0}, benchmarks_path=bench_path)
    coding_m2 = get_model_quality_for_role("m2", {"coding": 1.0}, benchmarks_path=bench_path)

    assert reasoning_m1 > reasoning_m2
    assert coding_m2 > coding_m1
