"""Bench store module."""

from __future__ import annotations

from typing import Any


def load_bench_records(limit: int = 100) -> list[dict[str, Any]]:
    """Load benchmark records from storage."""
    return []


def append_bench_record(record: dict[str, Any]) -> None:
    """Append a benchmark record to storage."""


__all__ = ["load_bench_records", "append_bench_record"]
