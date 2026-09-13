from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from conftest import _load_script_module

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_wl120_wl136_loc_trend.py"
MODULE = _load_script_module("generate_wl120_wl136_loc_trend", SCRIPT_PATH)


def _snapshots() -> list[dict[str, object]]:
    return [
        {
            "date": "2026-02-19",
            "source": "git_commit",
            "commit": "a" * 40,
            "total_loc": 3000,
            "core_boundary_loc": 700,
        },
        {
            "date": "2026-02-20",
            "source": "git_commit",
            "commit": "b" * 40,
            "total_loc": 2800,
            "core_boundary_loc": 650,
        },
        {
            "date": "2026-02-21",
            "source": "git_commit",
            "commit": "c" * 40,
            "total_loc": 2600,
            "core_boundary_loc": 600,
        },
    ]


def test_build_payload_has_expected_schema_and_trend_flags() -> None:
    dates = [dt.date(2026, 2, 19), dt.date(2026, 2, 20), dt.date(2026, 2, 21)]
    payload = MODULE._build_payload(
        generated_at="2026-02-21T00:00:00Z",
        dates=dates,
        snapshots=_snapshots(),
    )

    assert set(payload.keys()) == {
        "generated_at",
        "scope",
        "method",
        "snapshots",
        "trend",
    }
    assert payload["generated_at"] == "2026-02-21T00:00:00Z"
    assert isinstance(payload["scope"], dict)
    assert isinstance(payload["method"], dict)
    assert isinstance(payload["snapshots"], list)
    assert isinstance(payload["trend"], dict)
    assert payload["trend"]["total_loc_values"] == [3000, 2800, 2600]
    assert payload["trend"]["core_boundary_loc_values"] == [700, 650, 600]
    assert payload["trend"]["wl120_three_day_decline_met"] is True
    assert payload["trend"]["wl136_core_decline_met"] is True


def test_validate_snapshot_dates_accepts_strictly_increasing_dates() -> None:
    MODULE._validate_snapshot_dates(_snapshots())


def test_validate_snapshot_dates_rejects_duplicate_dates() -> None:
    dup = _snapshots()
    dup[2]["date"] = "2026-02-20"
    with pytest.raises(RuntimeError, match="unique"):
        MODULE._validate_snapshot_dates(dup)


def test_validate_snapshot_dates_rejects_descending_dates() -> None:
    bad = _snapshots()
    bad[0]["date"] = "2026-02-22"
    with pytest.raises(RuntimeError, match="ascending"):
        MODULE._validate_snapshot_dates(bad)
