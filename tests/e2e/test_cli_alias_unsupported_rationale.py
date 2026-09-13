"""Rationale contracts for deliberately unsupported canonical alias targets."""

from __future__ import annotations

from tests.e2e.test_cli_alias_rewrite_contract import (
    _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES,
)

_UNSUPPORTED_CANONICAL_RATIONALE: dict[tuple[str, ...], str] = {
    ("run", "inspect"): "real app currently lacks a stable run inspect command path",
    ("run", "status"): "real app currently lacks a stable run status command path",
    ("run", "wait"): "real app currently lacks a stable run wait command path",
}


def test_unsupported_canonical_targets_have_explicit_rationale_map() -> None:
    assert _UNSUPPORTED_CANONICAL_RATIONALE
    assert set(_UNSUPPORTED_CANONICAL_RATIONALE) == _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES


def test_unsupported_canonical_rationale_entries_are_non_empty() -> None:
    for target, rationale in _UNSUPPORTED_CANONICAL_RATIONALE.items():
        assert target
        assert all(isinstance(part, str) and part for part in target)
        assert isinstance(rationale, str)
        assert rationale.strip()
