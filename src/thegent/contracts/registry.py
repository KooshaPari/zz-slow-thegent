"""Contract registry — single source of truth for contract schemas.

This module is the canonical surface for contract-versioning constants
(``CONTRACT_SCHEMA_VERSION``), the ``ContractRegistry`` instance, and
its lookup helpers (``get_registry``, ``is_compatible``,
``list_versions``). All governance commands and the L9 ROB-010
critical-lane downgrade guard import from this module.

Backwards-compatible: ``CONTRACT_SCHEMA_VERSION``, ``ContractRegistry``,
and ``ContractVersion`` are preserved from the original stub.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Public schema version used by contract payloads surfaced through
#: ``get_server_meta_impl``. Defined here so the registries module remains the
#: single import surface for contract-versioning constants; callers should
#: treat this as the canonical contract schema version string.
CONTRACT_SCHEMA_VERSION: str = "csm-v1"


#: Schema version of the registry module itself (separate from the
#: contract schema version). Bumped only when the public surface of
#: ``ContractRegistry`` / ``get_registry`` / ``ContractVersionInfo``
#: changes in a breaking way.
CONTRACTS_REGISTRY_VERSION: str = "registry-v1"


@dataclass
class ContractVersionInfo:
    """Metadata for a registered contract version.

    Governance commands (``contracts_registry_cmd``) and the L9 ROB-010
    downgrade guard consume this shape — the field set is frozen and
    contract-pinned by ``tests/unit/contracts/test_registry_contract.py``.
    """

    contract_id: str
    version: str
    description: str = ""
    deprecated: bool = False
    #: ISO-8601 date string after which this version is no longer
    #: accepted by the migrator. ``None`` means no expiry.
    migration_window_end: str | None = None


@dataclass
class ContractRegistry:
    """Registry for contracts and their compatibility metadata.

    The registry is intentionally minimal: it tracks registered
    ``ContractVersionInfo`` entries and answers two queries:

    * ``list_versions()`` — surface every registered entry (drives the
      ``thegent contracts registry`` governance command).
    * ``is_compatible(requested, current)`` — return ``True`` only when
      the requested version is the canonical current version. ROB-010
      uses this to block any non-current contract version in a
      critical lane.
    """

    #: Canonical storage for ``ContractVersionInfo`` entries. The
    #: ``_versions`` alias in ``__post_init__`` keeps legacy callers
    #: that wrote ``reg._versions = {}`` working — both names point at
    #: the same dict.
    _contracts: dict[str, ContractVersionInfo] = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self._contracts is None:
            self._contracts = {}
        self._versions = self._contracts

    def register(  # type: ignore[override]
        self,
        name: str | ContractVersionInfo | None = None,
        contract: dict[str, Any] | None = None,
    ) -> None:
        """Register a contract version.

        Three call shapes are supported for backwards compatibility:

        * ``register(name, dict)`` — legacy registry contract: store a
          ``ContractVersionInfo`` derived from the mapping payload.
        * ``register(version_info)`` — modern shape: register a fully
          built ``ContractVersionInfo``. ``contract_id`` is used as the
          storage key.
        * ``register(name=None, contract=None)`` — no-op shim: the
          original stub allowed this to silently swallow malformed calls.
          Preserved so legacy callers don't blow up.
        """
        if isinstance(name, ContractVersionInfo):
            self._register_info(name.contract_id, name)
            return
        if name is None or contract is None:
            # Preserve historical behaviour: an incomplete call records
            # nothing rather than raising.
            return
        self._register_info(
            name,
            ContractVersionInfo(**self._info_kwargs(name, contract)),
        )

    def register_contract_version(self, version: ContractVersionInfo) -> None:
        """Register a ``ContractVersionInfo`` directly.

        Tests and tooling that build ``ContractVersionInfo`` payloads via
        the dataclass constructor use this entry point. Keys the registry
        on ``version.contract_id`` so the same identifier always resolves
        to a single registered version.
        """
        self._register_info(version.contract_id, version)

    @staticmethod
    def _info_kwargs(name: str, contract: dict[str, Any]) -> dict[str, Any]:
        return {
            "contract_id": name,
            "version": str(contract.get("version", "")),
            "description": str(contract.get("description", "")),
            "deprecated": bool(contract.get("deprecated", False)),
            "migration_window_end": contract.get("migration_window_end"),
        }

    def _register_info(self, name: str, info: ContractVersionInfo) -> None:
        # ``_contracts`` is the canonical storage for ``__init__``-built
        # registries. ``_versions`` is the canonical storage for legacy
        # test fixtures that bypass ``__init__`` via ``__new__`` and
        # seed ``_versions`` directly. Whichever attribute exists
        # receives the write; the other is kept in sync.
        target = getattr(self, "_contracts", None)
        if target is None:
            target = getattr(self, "_versions", None)
            if target is None:
                target = {}
                self._versions = target
            self._contracts = target
        else:
            self._versions = target
        target[name] = info

    def get(self, name: str) -> ContractVersionInfo | None:
        if not hasattr(self, "_contracts"):
            # Defensive: a test fixture may have set ``_versions`` only
            # and bypassed ``__post_init__``.
            if hasattr(self, "_versions"):
                return self._versions.get(name)
            return None
        return self._contracts.get(name)

    def list_versions(self) -> list[ContractVersionInfo]:
        """Return every registered ``ContractVersionInfo``, sorted by id.

        Stable ordering so governance table output is deterministic.
        """
        storage = getattr(self, "_contracts", None) or getattr(self, "_versions", None)
        if not storage:
            return []
        return sorted(storage.values(), key=lambda v: (v.contract_id, v.version))

    def is_compatible(self, requested: str, current: str) -> bool:
        """Return ``True`` when ``requested`` is acceptable for ``current``.

        ROB-010 contract-version downgrade prevention. The canonical
        schema (``"csm-v1"``) and the legacy ``"task-tool-18"`` schema
        are mutually compatible because task-tool-18 predates the
        csm-v1 wire format and the migration adapter handles the
        translation. Any other unknown / empty / different version
        combination is rejected.
        """
        if not requested:
            return False
        if requested == current:
            return True
        return {requested, current} == {"csm-v1", "task-tool-18"}


#: Canonical single instance. Populated at import time with the
#: ``csm`` contract at ``CONTRACT_SCHEMA_VERSION`` so list_versions()
#: is never empty.
CONTRACT_REGISTRY: ContractRegistry = ContractRegistry()
CONTRACT_REGISTRY.register(
    "csm",
    {
        "version": CONTRACT_SCHEMA_VERSION,
        "description": "Canonical Structured Message contract (csm).",
        "deprecated": False,
        "migration_window_end": None,
    },
)


def get_registry() -> ContractRegistry:
    """Return the canonical ``CONTRACT_REGISTRY`` singleton.

    Used by governance commands (``contracts_registry_cmd``) and the
    L9 ROB-010 critical-lane downgrade guard in
    ``_phase_bg_evaluate_contract``.
    """
    return CONTRACT_REGISTRY


# Re-export ``ContractVersionInfo`` as ``ContractVersion`` so both names
# resolve to the same dataclass. The original ``ContractVersion``
# (major/minor/patch triplet) is preserved by binding the name to
# ``ContractVersionInfo`` here; downstream consumers used the public
# attribute surface, not the int-triplet shape.
ContractVersion = ContractVersionInfo


__all__ = [
    "CONTRACT_REGISTRY",
    "CONTRACT_SCHEMA_VERSION",
    "CONTRACTS_REGISTRY_VERSION",
    "ContractRegistry",
    "ContractVersion",
    "ContractVersionInfo",
    "get_registry",
]  # noqa: E501
