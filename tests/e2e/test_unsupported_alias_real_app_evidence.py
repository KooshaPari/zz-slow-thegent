"""Evidence contracts for deliberately unsupported canonical alias targets."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

from tests.e2e.command_surface import command_path_exists
from tests.e2e.test_cli_alias_rewrite_contract import (
    _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES,
)

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app


def test_unsupported_canonical_targets_are_absent_on_real_app() -> None:
    assert _DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES
    for path in sorted(_DELIBERATELY_UNSUPPORTED_CANONICAL_PREFIXES):
        assert not command_path_exists(app, list(path)), (
            f"Unsupported canonical target unexpectedly resolves on real app; remove from unsupported set: {path!r}"
        )
