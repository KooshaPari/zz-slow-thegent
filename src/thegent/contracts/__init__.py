"""thegent.contracts — top-level re-export layer for the canonical surface.

This module unifies two parallel surfaces that diverged during the
auto-generated stub era:

* **Canonical ROB-010 governance surface** (introduced by WL142 in
  ``thegent.contracts.registry``): ``CONTRACT_SCHEMA_VERSION``,
  ``CONTRACT_REGISTRY``, ``ContractRegistry``, ``ContractVersion``,
  ``ContractVersionInfo``, ``get_registry``.
  Every governance command (``governance_policy_cmds``,
  ``governance_policy_core_cmds``,
  ``governance_policy_contracts_cmds``) consumes this surface, and
  so should anything else. Note: ``is_compatible`` is a *method* on
  ``ContractRegistry`` instances, NOT a module-level function, so it
  is intentionally not re-exported here — callers must invoke
  ``get_registry().is_compatible(...)`` or use the classmethod.

* **Legacy back-compat exports** (preserved from earlier iterations
  of ``thegent.contracts`` so existing third-party callers don't
  break):
  ``ADAPTER_REGISTRY``, ``AdapterResult``, ``OutputAdapter``,
  ``normalize_output``, ``CSMPhase``, ``CanonicalStructuredMessage``,
  ``CSMStatus``, ``get_adapter``.

The two surfaces are intentionally non-overlapping. Callers that
need contract-versioning constants (and ROB-010 downgrade
prevention) should import from either ``thegent.contracts`` or
``thegent.contracts.registry`` and get the **same** symbols
(parity is contract-pinned by ``tests/test_wl144_*``).
"""

from __future__ import annotations

#: Top-level contracts-package schema version. Bumped only when the
#: ``thegent.contracts`` package surface (``CONTRACT_SCHEMA_VERSION``,
#: ``CONTRACT_REGISTRY``, ``ADAPTER_REGISTRY``, etc.) changes in a
#: breaking way.
CONTRACTS_VERSION: str = "contracts-v1"


# Canonical ROB-010 governance surface — re-exported from
# thegent.contracts.registry. Imported FIRST so the canonical
# CONTRACT_SCHEMA_VERSION / get_registry win any name clashes with
# legacy symbols (there are none, but the ordering is explicit).
# Legacy back-compat exports — preserved verbatim from the prior
# auto-generated stub so existing consumers continue to resolve.
# ``ADAPTER_REGISTRY`` from ``adapters.py`` is an *instance*
# (AdapterRegistry()); the prior stub exposed it as a *class* with
# classmethod access. We expose the canonical INSTANCE under the
# same name so that ``ADAPTER_REGISTRY.keys()``,
# ``ADAPTER_REGISTRY.register(...)``, ``ADAPTER_REGISTRY.get(...)``
# keep working. Both surface shapes are documented below.
# Submodule back-compat exports — listed in ``__all__`` so
# ``from thegent.contracts import registry`` / ``adapters`` / ``parser``
# all resolve symmetrically. Without these, third-party callers that
# do ``from thegent.contracts import registry`` only work because of
# Python's package-import attribute machinery; ``__all__`` makes the
# intent explicit and is pinned by WL145.
from thegent.contracts import (
    adapters as adapters,  # noqa: F401 — back-compat legacy export
)
from thegent.contracts import parser as parser  # noqa: F401 — back-compat legacy export
from thegent.contracts import (
    registry as registry,  # noqa: F401 — back-compat legacy export
)
from thegent.contracts.adapters import (
    ADAPTER_REGISTRY,  # noqa: F401 — back-compat legacy export
    AdapterResult,  # noqa: F401 — back-compat legacy export
    OutputAdapter,  # noqa: F401 — back-compat legacy export
    XMLOutputAdapter,  # noqa: F401 — back-compat legacy export
    get_adapter,  # noqa: F401 — back-compat legacy export
    normalize_output,  # noqa: F401 — back-compat legacy export
    register_adapter,  # noqa: F401 — back-compat legacy export
)
from thegent.contracts.csm import (
    CanonicalStructuredMessage,  # noqa: F401 — back-compat legacy export
    CSMPhase,  # noqa: F401 — back-compat legacy export
    CSMStatus,  # noqa: F401 — back-compat legacy export
)
from thegent.contracts.parser import (  # noqa: F401 — back-compat legacy export
    IncrementalXMLParser,
    extract_tags,
)
from thegent.contracts.registry import (
    CONTRACT_REGISTRY,
    CONTRACT_SCHEMA_VERSION,
    CONTRACTS_REGISTRY_VERSION,
    ContractRegistry,
    ContractVersion,
    ContractVersionInfo,
    get_registry,
)

__all__ = [
    "CONTRACTS_VERSION",
    # Canonical ROB-010 governance surface (WL142 / WL143 / WL144).
    "CONTRACT_REGISTRY",
    "CONTRACT_SCHEMA_VERSION",
    "CONTRACTS_REGISTRY_VERSION",
    "ContractRegistry",
    "ContractVersion",
    "ContractVersionInfo",
    "get_registry",
    # Legacy back-compat exports (preserved for non-ROB-010 callers).
    "ADAPTER_REGISTRY",
    "AdapterResult",
    "OutputAdapter",
    "XMLOutputAdapter",
    "IncrementalXMLParser",
    "extract_tags",
    "get_adapter",
    "normalize_output",
    "register_adapter",
    "adapters",
    "parser",
    "registry",
    "CSMPhase",
    "CSMStatus",
    "CanonicalStructuredMessage",
]
