"""thegent.contracts.csm — Canonical Structured Message package.

Backwards-compat re-export layer that unifies the legacy stub-era
imports (``from thegent.contracts.csm import CSMPhase, CSMStatus,
CanonicalStructuredMessage``) with the v1 canonical implementation
defined in :mod:`thegent.contracts.csm.v1`.

Every symbol exported by this module is owned by ``v1``. New code
should prefer importing from the versioned path
(``thegent.contracts.csm.v1``) for explicitness, but legacy callers
keep working unchanged.
"""

from __future__ import annotations

from thegent.contracts.csm.v1 import (
    CanonicalStructuredMessage,
    CSMPhase,
    CSMStatus,
    get_csm,
)

__all__ = [
    "CSMPhase",
    "CSMStatus",
    "CanonicalStructuredMessage",
    "get_csm",
]
