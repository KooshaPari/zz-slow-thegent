"""Benchmark conftest — skip entire benchmarks/ suite if pytest-benchmark is not installed."""

from __future__ import annotations

import importlib.util

import pytest


def pytest_collection_modifyitems(items: list, config: pytest.Config) -> None:  # noqa: ARG001 -- config unused but required by pytest hook signature
    if importlib.util.find_spec("pytest_benchmark") is None:
        skip_marker = pytest.mark.skip(reason="pytest-benchmark not installed; run: uv pip install pytest-benchmark")
        for item in items:
            if item.fspath and "benchmarks" in str(item.fspath):
                item.add_marker(skip_marker)
