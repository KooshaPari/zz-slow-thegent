# @trace WL-133 B90-W2-D5
"""Deterministic fixture tests for the Mojo score_rank_v1 kernel.

Loads tests/mojo/fixtures/score_deterministic_v1.json and for each case:
  - Runs the Python bridge reference formula.
  - Verifies output matches the expected fixture output.
  - If Mojo is available, dispatches through the actual MojoBridge and
    verifies the result matches the fixture (cross-runtime parity).

If Mojo is not available, the cross-runtime dispatch tests are skipped.

# @trace WL-133 B90-W2-D5
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import orjson as json
import pytest

# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "score_deterministic_v1.json"


def _load_fixtures() -> dict[str, Any]:
    if not FIXTURES_PATH.exists():
        pytest.fail(f"Fixture file missing: {FIXTURES_PATH}")
    return json.loads(FIXTURES_PATH.read_text())


# ---------------------------------------------------------------------------
# Python reference implementation
# (mirrors build_provider_score_kernel_script formula)
# Formula: score = floor((0.4*quality + 0.35*cost + 0.25*latency) * 1000) / 1000
#          bounded to [0.0, 1.0]
# ---------------------------------------------------------------------------


def _python_score(cost: float, quality: float, latency: float) -> dict[str, Any]:
    """Python reference implementation of calculate_provider_score."""
    raw = (0.4 * quality) + (0.35 * cost) + (0.25 * latency)
    bounded = max(0.0, min(1.0, raw))
    score = math.floor(bounded * 1000.0) / 1000.0
    return {"score": score, "success": True}


# ---------------------------------------------------------------------------
# D5-1: Fixture file exists and has expected structure
# ---------------------------------------------------------------------------


def test_fixture_file_exists() -> None:
    """score_deterministic_v1.json must exist."""
    assert FIXTURES_PATH.exists(), f"Missing fixture file: {FIXTURES_PATH}"


def test_fixture_file_valid_json() -> None:
    """score_deterministic_v1.json must be valid JSON."""
    data = _load_fixtures()
    assert isinstance(data, dict), "Fixture root must be a dict"


def test_fixture_file_has_required_fields() -> None:
    """Fixture must have version, kernel, and cases fields."""
    data = _load_fixtures()
    for field in ("version", "kernel", "cases"):
        assert field in data, f"Fixture missing required field: {field}"


def test_fixture_has_at_least_five_cases() -> None:
    """Fixture must have at least 5 deterministic cases."""
    data = _load_fixtures()
    assert len(data["cases"]) >= 5, f"Expected >= 5 fixture cases, got {len(data['cases'])}"


def test_fixture_kernel_name() -> None:
    """Fixture kernel must be score_rank_v1."""
    data = _load_fixtures()
    assert data["kernel"] == "score_rank_v1", f"Expected kernel='score_rank_v1', got {data['kernel']!r}"


# ---------------------------------------------------------------------------
# D5-2: Python bridge reference formula matches all non-error fixtures
# ---------------------------------------------------------------------------


def test_python_reference_all_success_cases() -> None:
    """Python reference formula must match expected output for all success cases."""
    data = _load_fixtures()
    failures: list[str] = []

    for case in data["cases"]:
        inp = case["input"]
        expected = case["expected_output"]
        cid = case["case_id"]

        # Skip error-expected cases
        if not expected.get("success", True):
            continue

        # Only process cases that have all three required args
        if not all(k in inp for k in ("cost_score", "quality_score", "latency_score")):
            continue

        result = _python_score(
            cost=inp["cost_score"],
            quality=inp["quality_score"],
            latency=inp["latency_score"],
        )

        if result["score"] != expected["score"]:
            failures.append(f"{cid}: expected score={expected['score']}, got={result['score']} (input={inp})")
        if result["success"] is not expected["success"]:
            failures.append(f"{cid}: expected success={expected['success']}, got={result['success']}")

    assert not failures, "Python reference formula failures:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# D5-3: F7 — contract-missing case raises ValueError
# ---------------------------------------------------------------------------


def test_f7_contract_missing_raises_value_error() -> None:
    """F7: omitting quality_score from the contract must raise ValueError."""
    from thegent.infra.mojo_bridge import validate_kernel_contract

    args_missing_quality = {"cost_score": 0.5, "latency_score": 0.5}
    with pytest.raises(ValueError, match="quality_score"):
        validate_kernel_contract("math", "calculate_provider_score", args_missing_quality)


def test_f7_fixture_marks_as_failure() -> None:
    """The det_007 fixture case must mark success=false (error expected)."""
    data = _load_fixtures()
    case_007 = next((c for c in data["cases"] if c["case_id"] == "det_007"), None)
    assert case_007 is not None, "det_007 fixture case missing"
    assert case_007["expected_output"]["success"] is False, "det_007 must have success=false (contract-missing case)"


# ---------------------------------------------------------------------------
# D5-4: MojoBridge cross-runtime dispatch (skip if Mojo unavailable)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mojo_bridge_dispatch_success_cases() -> None:
    """When Mojo is available, MojoBridge.dispatch must match fixture expected output."""
    from thegent.infra.mojo_bridge import MojoBridge, MojoTask

    bridge = MojoBridge()
    if not bridge.is_available:
        pytest.skip("Mojo kernel not available; skipping cross-runtime dispatch parity")

    data = _load_fixtures()

    for case in data["cases"]:
        inp = case["input"]
        expected = case["expected_output"]
        cid = case["case_id"]

        if not expected.get("success", True):
            continue
        if not all(k in inp for k in ("cost_score", "quality_score", "latency_score")):
            continue

        task = MojoTask(
            task_id=cid,
            module="math",
            function="calculate_provider_score",
            args=inp,
            timeout=10.0,
        )
        result = await bridge.dispatch(task)

        assert result.get("success") is True, f"{cid}: MojoBridge dispatch returned success=False: {result}"
        assert result.get("score") == expected["score"], (
            f"{cid}: score mismatch: expected={expected['score']}, got={result.get('score')}"
        )


# ---------------------------------------------------------------------------
# D5-5: Upper and lower bound edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cost", "quality", "latency", "expected_score"),
    [
        (1.2, 1.2, 1.2, 1.0),  # F5: above upper bound -> clamped to 1.0
        (-0.5, 0.2, 0.1, 0.0),  # F6: negative -> clamped to 0.0
        (0.0, 0.0, 0.0, 0.0),  # F2: all zeros -> exactly 0.0
        (1.0, 1.0, 1.0, 1.0),  # F1: all ones -> exactly 1.0
    ],
)
def test_python_boundary_cases(cost: float, quality: float, latency: float, expected_score: float) -> None:
    """Python reference must correctly clamp boundary cases."""
    result = _python_score(cost=cost, quality=quality, latency=latency)
    assert result["score"] == expected_score, (
        f"Boundary case failed: cost={cost}, quality={quality}, latency={latency}: "
        f"expected={expected_score}, got={result['score']}"
    )
