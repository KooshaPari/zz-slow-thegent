from __future__ import annotations

import pytest

# scripts.check_python_benchmark_regression module was removed.
pytest.importorskip(
    "scripts.check_python_benchmark_regression",
    reason=(
        "scripts.check_python_benchmark_regression module removed; "
        "benchmark regression tests skipped"
    ),
)
from scripts.check_python_benchmark_regression import (  # noqa: E402
    find_regressions,
)


def _payload(avg_a: float, avg_b: float) -> dict[str, object]:
    return {
        "suite": "python-benchmark-suite-v1",
        "benchmarks": [
            {"label": "a", "avg_microseconds": avg_a},
            {"label": "b", "avg_microseconds": avg_b},
        ],
    }


def test_find_regressions_detects_excess_slowdown() -> None:
    baseline = _payload(10.0, 20.0)
    current = _payload(11.0, 25.0)
    regressions = find_regressions(baseline, current, max_regression_pct=15.0)
    assert len(regressions) == 1
    assert regressions[0]["label"] == "b"


def test_find_regressions_ignores_within_threshold() -> None:
    baseline = _payload(10.0, 20.0)
    current = _payload(10.5, 22.0)
    regressions = find_regressions(baseline, current, max_regression_pct=15.0)
    assert regressions == []


def test_find_regressions_rejects_duplicate_labels() -> None:
    baseline = {
        "benchmarks": [
            {"label": "dup", "avg_microseconds": 10.0},
            {"label": "dup", "avg_microseconds": 11.0},
        ]
    }
    current = {"benchmarks": [{"label": "dup", "avg_microseconds": 10.5}]}

    with pytest.raises(ValueError, match="duplicate benchmark label"):
        find_regressions(baseline, current, max_regression_pct=10.0)


def test_find_regressions_rejects_empty_labels() -> None:
    baseline = {"benchmarks": [{"label": " ", "avg_microseconds": 10.0}]}
    current = _payload(10.0, 20.0)
    with pytest.raises(ValueError, match="label must be non-empty"):
        find_regressions(baseline, current, max_regression_pct=10.0)


def test_find_regressions_rejects_non_string_labels() -> None:
    baseline = {"benchmarks": [{"label": 123, "avg_microseconds": 10.0}]}
    current = _payload(10.0, 20.0)
    with pytest.raises(ValueError, match="label must be a string"):
        find_regressions(baseline, current, max_regression_pct=10.0)


def test_find_regressions_rejects_non_list_benchmarks() -> None:
    baseline = {"benchmarks": {"label": "a", "avg_microseconds": 10.0}}
    current = _payload(10.0, 20.0)

    with pytest.raises(ValueError, match="must be a list"):
        find_regressions(baseline, current, max_regression_pct=10.0)


def test_find_regressions_can_require_complete_baseline() -> None:
    baseline = _payload(10.0, 20.0)
    current = {
        "suite": "python-benchmark-suite-v1",
        "benchmarks": [{"label": "a", "avg_microseconds": 10.0}],
    }
    regressions = find_regressions(
        baseline,
        current,
        max_regression_pct=15.0,
        require_complete_baseline=True,
    )
    assert regressions == [
        {
            "label": "b",
            "baseline_avg_us": 20.0,
            "current_avg_us": None,
            "delta_pct": None,
            "reason": "missing_from_current",
        }
    ]


@pytest.mark.parametrize("invalid_avg", [float("nan"), float("inf"), -1.0])
def test_find_regressions_rejects_non_finite_or_negative_averages(
    invalid_avg: float,
) -> None:
    baseline = {"benchmarks": [{"label": "a", "avg_microseconds": invalid_avg}]}
    current = {"benchmarks": [{"label": "a", "avg_microseconds": 1.0}]}
    with pytest.raises(ValueError, match="finite and >= 0"):
        find_regressions(baseline, current, max_regression_pct=10.0)


def test_find_regressions_rejects_non_positive_baseline_average() -> None:
    baseline = {"benchmarks": [{"label": "a", "avg_microseconds": 0.0}]}
    current = {"benchmarks": [{"label": "a", "avg_microseconds": 1.0}]}
    with pytest.raises(ValueError, match="baseline avg_microseconds must be > 0"):
        find_regressions(baseline, current, max_regression_pct=10.0)


def test_find_regressions_rejects_boolean_average_value() -> None:
    baseline = {"benchmarks": [{"label": "a", "avg_microseconds": True}]}
    current = {"benchmarks": [{"label": "a", "avg_microseconds": 1.0}]}
    with pytest.raises(ValueError, match="avg_microseconds must be numeric"):
        find_regressions(baseline, current, max_regression_pct=10.0)


def test_find_regressions_allows_zero_current_average() -> None:
    baseline = {"benchmarks": [{"label": "a", "avg_microseconds": 10.0}]}
    current = {"benchmarks": [{"label": "a", "avg_microseconds": 0.0}]}
    assert find_regressions(baseline, current, max_regression_pct=10.0) == []


@pytest.mark.parametrize("invalid_threshold", [float("nan"), float("inf"), -0.1])
def test_find_regressions_rejects_invalid_max_regression_pct(
    invalid_threshold: float,
) -> None:
    baseline = _payload(10.0, 20.0)
    current = _payload(10.0, 20.0)
    with pytest.raises(ValueError, match="max_regression_pct must be finite and >= 0"):
        find_regressions(baseline, current, max_regression_pct=invalid_threshold)
