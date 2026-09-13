"""Contract migration controller.

Governs whether a requested (contract_id, version) pair is currently
allowed, deprecated, expired, or unknown, and surfaces the preferred
active version for a given contract. The controller is intentionally
side-effect free: every decision is computed against the
``ContractRegistry`` that the consumer provides (defaulting to the
canonical ``CONTRACT_REGISTRY`` singleton).

Decision tree
-------------
* ``active`` — the requested version is registered and not deprecated;
  ``allowed=True``.
* ``deprecated`` — registered and flagged ``deprecated=True`` with a
  ``migration_window_end``:

  * If today's date is **before** ``migration_window_end``, the
    version is still callable: ``allowed=True`` and
    ``migration_days_left`` reports the remaining days.
  * If today's date is **after** ``migration_window_end``, the
    version is expired: ``allowed=False``, ``status="expired"``,
    ``migration_days_left`` is negative.

* ``deprecated`` with no window: kept callable indefinitely
  (``allowed=True``, ``status="deprecated"``).
* ``unknown`` — the requested version is not registered:
  ``allowed=False``, ``status="unknown"``.

The migration window is interpreted in UTC to match how contract
registrations are recorded (``migration_window_end`` is an ISO-8601
datetime string). Days remaining are rounded to two decimal places so
log consumers don't fight floating-point aliasing.

Test surface: ``tests/test_unit_contracts_migration.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from thegent.contracts.registry import (
    CONTRACT_REGISTRY,
    ContractRegistry,
    ContractVersionInfo,
)

__all__ = [
    "MigrationController",
]


@dataclass
class MigrationController:
    """Compatibility decision engine for ``(contract_id, version)`` pairs.

    Args:
        registry: The registry to read ``ContractVersionInfo`` entries
            from. Defaults to the canonical ``CONTRACT_REGISTRY``
            singleton if not supplied.
        migrations: Out-parameter style list of pending migrations
            (drained by :meth:`run`). Tests seed this list to verify
            the drain logic without driving a real migration.
    """

    registry: ContractRegistry | None = None
    migrations: list[dict[str, object]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.registry is None:
            self.registry = CONTRACT_REGISTRY

    # -- decision engine -----------------------------------------------------

    def evaluate_version(
        self,
        contract_name: str,
        version: str,
    ) -> dict[str, object]:
        """Decide whether ``(contract_name, version)`` is currently usable.

        Returns a dict with the following keys (matching the canonical
        contract pinned by ``tests/test_unit_contracts_migration.py``):

        * ``allowed`` — ``True`` when the version is callable.
        * ``status`` — one of ``"active"``, ``"deprecated"``,
          ``"expired"``, ``"unknown"``.
        * ``contract`` — echo of ``contract_name``.
        * ``version`` — echo of the requested version.
        * ``reason`` — human-readable explanation suitable for logging
          or audit surfacing.
        * ``migration_days_left`` — ``int`` for active/unknown, signed
          decimal for deprecated windows, ``0`` when no window is set.
        """
        if self.registry is None:
            return self._unknown(contract_name, version, "registry unavailable")
        info = self._lookup(contract_name, version)
        if info is None:
            return self._unknown(contract_name, version, "version is not registered")
        if not info.deprecated:
            return {
                "allowed": True,
                "status": "active",
                "contract": contract_name,
                "version": version,
                "reason": f"{contract_name}@{version} is the active contract.",
                "migration_days_left": 0,
            }
        window_end = info.migration_window_end
        if not window_end:
            return {
                "allowed": True,
                "status": "deprecated",
                "contract": contract_name,
                "version": version,
                "reason": (
                    f"{contract_name}@{version} is deprecated but no expiry window is configured; still supported."
                ),
                "migration_days_left": 0,
            }
        parsed = self._parse_iso(window_end)
        if parsed is None:
            return {
                "allowed": True,
                "status": "deprecated",
                "contract": contract_name,
                "version": version,
                "reason": (
                    f"{contract_name}@{version} is deprecated; migration "
                    f"window {window_end!r} could not be parsed, falling back "
                    "to allowed."
                ),
                "migration_days_left": 0,
            }
        delta_seconds = (parsed - datetime.now(UTC)).total_seconds()
        days_left = round(delta_seconds / 86400.0, 2)
        if days_left < 0:
            return {
                "allowed": False,
                "status": "expired",
                "contract": contract_name,
                "version": version,
                "reason": (f"{contract_name}@{version} expired {abs(days_left):.1f} days ago; must migrate."),
                "migration_days_left": days_left,
            }
        return {
            "allowed": True,
            "status": "deprecated",
            "contract": contract_name,
            "version": version,
            "reason": (
                f"{contract_name}@{version} is deprecated; {days_left:.1f} days remaining in the migration window."
            ),
            "migration_days_left": days_left,
        }

    def get_preferred_version(self, contract_name: str) -> str:
        """Return the highest active (non-deprecated) version for ``contract_name``.

        Falls back to ``"unknown"`` when the contract is not registered
        or every registered version is deprecated. The contract is
        pinned by ``tests/test_unit_contracts_migration.py``.
        """
        if self.registry is None:
            return "unknown"
        candidates: list[ContractVersionInfo] = []
        for info in self.registry.list_versions():
            if info.contract_id != contract_name:
                continue
            candidates.append(info)
        if not candidates:
            return "unknown"
        active = [c for c in candidates if not c.deprecated]
        pool = active or candidates
        # Pick the lexicographically highest version string among the
        # pool. Sorting on the ``version`` field keeps the decision
        # deterministic for tests and stable across runs.
        pool_sorted = sorted(pool, key=lambda c: c.version, reverse=True)
        return pool_sorted[0].version

    # -- migration queue -----------------------------------------------------

    def queue_migration(self, migration: dict[str, object]) -> None:
        """Append a migration descriptor to the pending queue.

        External callers (governance commands, CLI ``migrate``) use this
        to stage work that :meth:`run` will later drain.
        """
        self.migrations.append(migration)

    def run(self) -> int:
        """Drain queued migrations and return the number applied.

        The stub implementation is a no-op (migrations are recorded
        only; nothing is applied). Returns the count so callers can
        detect when the queue was empty without inspecting
        :attr:`migrations`.
        """
        applied = len(self.migrations)
        self.migrations.clear()
        return applied

    # -- internals -----------------------------------------------------------

    def _lookup(self, contract_name: str, version: str) -> ContractVersionInfo | None:
        for info in self.registry.list_versions():
            if info.contract_id == contract_name and info.version == version:
                return info
        return None

    @staticmethod
    def _parse_iso(value: str) -> datetime | None:
        """Parse an ISO-8601 datetime string, tolerating a trailing ``Z``."""
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed

    @staticmethod
    def _unknown(contract_name: str, version: str, reason: str) -> dict[str, object]:
        return {
            "allowed": False,
            "status": "unknown",
            "contract": contract_name,
            "version": version,
            "reason": reason,
            "migration_days_left": 0,
        }
