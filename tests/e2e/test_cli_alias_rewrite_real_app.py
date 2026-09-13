"""Real-app contract tests for alias rewrite prefixes."""

from __future__ import annotations

import sys
from collections import Counter
from unittest.mock import MagicMock

from tests.e2e.cli_runner_compat import _ALIAS_REWRITE_PREFIXES
from tests.e2e.command_surface import command_path_exists
from tests.e2e.test_cli_alias_rewrite_contract import (
    _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES,
)

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

_REQUIRED_CANONICAL_FAMILIES: set[tuple[str, ...]] = {
    ("run", "logs"),
    ("run", "status"),
    ("run", "wait"),
    ("run", "stop"),
    ("run", "inspect"),
    ("run", "history"),
    ("run", "ps"),
    ("plan", "rollback"),
}


def test_every_canonical_new_prefix_resolves_on_real_app() -> None:
    canonical_new_prefixes = {new_prefix for _, new_prefix in _ALIAS_REWRITE_PREFIXES}
    assert canonical_new_prefixes

    unresolved_prefixes = {
        new_prefix for new_prefix in canonical_new_prefixes if not command_path_exists(app, list(new_prefix))
    }
    assert unresolved_prefixes <= _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES, (
        "Unexpected unresolved canonical alias targets on real app: "
        f"{sorted(unresolved_prefixes - _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES)!r}"
    )


def test_required_canonical_families_have_at_least_one_mapping() -> None:
    canonical_target_counts = Counter(new_prefix for _, new_prefix in _ALIAS_REWRITE_PREFIXES)
    missing_families = sorted(family for family in _REQUIRED_CANONICAL_FAMILIES if canonical_target_counts[family] < 1)
    assert not missing_families, (
        f"Each required canonical family must have at least one alias mapping; missing: {missing_families!r}"
    )


def test_no_old_prefix_equals_new_prefix() -> None:
    for old_prefix, new_prefix in _ALIAS_REWRITE_PREFIXES:
        assert old_prefix != new_prefix, (
            f"Alias rewrite must not keep the same prefix: {old_prefix!r} -> {new_prefix!r}"
        )
