# tests/research_engine/test_deps.py
# @trace FR-RE-001
import importlib

import pytest


@pytest.mark.parametrize(
    "mod",
    [
        "apscheduler",
        "feedparser",
        "arxiv",
        "scholarly",
    ],
)
def test_dep_importable(mod: str) -> None:
    importlib.import_module(mod)
