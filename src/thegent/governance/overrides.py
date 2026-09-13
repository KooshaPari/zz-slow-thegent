# AUDIT-N+70: overrides hardening — all contracts verified
"""WP-3003: Override path with TTL and revalidation (FR-011)."""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from thegent.config import ThegentSettings
from thegent.integrations.base import SerializableMixin

_log = logging.getLogger(__name__)


# Reject ``policy_id`` values that would let an override escape its
# override_dir via the filename interpolation in ``_save_override``
# (``overrides.py:114``).  The same shape is enforced at the public
# ``PolicyEngine.register_override`` surface (see ``policy_engine.py``)
# but the manager itself is reachable from CLI surfaces and direct
# callers, so the guard must live here too. Mirrors the
# ``FederatedPolicyEngine`` path-traversal contract.
class PolicyOverridePathError(ValueError):
    """Raised when a ``policy_id`` would escape the override directory."""


def _validate_policy_id(policy_id: str) -> None:
    """Reject ``policy_id`` values that interpolate into a traversal path.

    Empty strings, ``/``, ``\\``, parent-directory references (``..``),
    and NUL bytes are all rejected before any state is mutated. The
    guard fails closed: a rejected ``policy_id`` raises
    :class:`PolicyOverridePathError` and leaves no override file behind.
    """
    if not isinstance(policy_id, str):  # defensive — surface config drift
        raise PolicyOverridePathError(
            f"policy_id must be a string, got {type(policy_id).__name__}"
        )
    if not policy_id:
        raise PolicyOverridePathError("policy_id must be a non-empty string")
    if "/" in policy_id or "\\" in policy_id:
        raise PolicyOverridePathError(
            f"policy_id contains path separator: {policy_id!r}"
        )
    if ".." in policy_id:
        raise PolicyOverridePathError(
            f"policy_id contains '..' sequence: {policy_id!r}"
        )
    if "\x00" in policy_id:
        raise PolicyOverridePathError(f"policy_id contains NUL byte: {policy_id!r}")


@dataclass
class PolicyOverride(SerializableMixin):
    """An active override for a governance policy."""

    policy_id: str
    reason: str
    by: str
    expires_at: float
    created_at: float
    metadata: dict[str, Any]

    def is_active(self) -> bool:
        """Check if the override is still valid."""
        return time.time() < self.expires_at


class OverrideManager:
    """Manages temporary policy overrides."""

    def __init__(self, settings: ThegentSettings | None = None) -> None:
        self.settings = settings or ThegentSettings()
        self.override_dir = self.settings.session_dir / "overrides"
        self.override_dir.mkdir(parents=True, exist_ok=True)

    def apply_override(
        self,
        policy_id: str,
        reason: str,
        by: str,
        duration_minutes: int = 60,
        metadata: dict[str, Any | None] | None = None,
    ) -> PolicyOverride:
        """Create a new temporary override.

        ``policy_id`` is validated against path-traversal shapes
        (see :func:`_validate_policy_id`) before any file is written so
        a malicious or malformed id cannot escape ``override_dir`` via
        the ``<policy_id>.json`` filename interpolation in
        :meth:`_save_override`. Callers that need richer rejection
        should layer their own validation on top.
        """
        _validate_policy_id(policy_id)
        now = time.time()
        expires_at = now + (duration_minutes * 60)

        override = PolicyOverride(
            policy_id=policy_id,
            reason=reason,
            by=by,
            expires_at=expires_at,
            created_at=now,
            metadata=metadata or {},
        )

        self._save_override(override)
        _log.info(
            "Applied override for policy %s by %s for %d min",
            policy_id,
            by,
            duration_minutes,
        )
        return override

    def get_override(self, policy_id: str) -> PolicyOverride | None:
        """Get an active override for a policy.

        ``policy_id`` is validated against path-traversal shapes so a
        rejected id cannot read arbitrary JSON files inside
        ``override_dir``. A rejected id returns ``None`` (no override
        exists) so the caller does not have to distinguish between
        "no override" and "bad id" at the call site.
        """
        try:
            _validate_policy_id(policy_id)
        except PolicyOverridePathError:
            _log.warning("rejecting get_override for unsafe policy_id: %r", policy_id)
            return None
        p = self.override_dir / f"{policy_id}.json"
        if not p.exists():
            return None

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            override = cast("PolicyOverride", PolicyOverride.from_dict(data))

            if override.is_active():
                return override
            # WP-3003: Emit governance.override.expired when override has expired
            _log.info(
                "governance.override.expired policy_id=%s by=%s expires_at=%s",
                policy_id,
                override.by,
                override.expires_at,
            )
            # Cleanup expired override
            p.unlink()
            return None
        except Exception as e:
            _log.error("Failed to load override %s: %s", policy_id, e)
            return None

    def cleanup_expired(self) -> int:
        """Remove all expired overrides from disk.

        Skips files whose name contains a path-traversal shape (defense
        in depth: under normal operation only ``apply_override`` writes
        into ``override_dir`` and it already validates, but a manual
        operator action or a previous-version leftover could leave a
        bad filename behind). Such files are logged at warning level
        and left untouched for human review.
        """
        count = 0
        for f in self.override_dir.glob("*.json"):
            if self._is_traversal_filename(f):
                _log.warning(
                    "cleanup_expired: skipping suspicious filename in override_dir: %s",
                    f.name,
                )
                continue
            if self._cleanup_if_expired(f):
                count += 1
        return count

    @staticmethod
    def _is_traversal_filename(path: Path) -> bool:
        """Return True when ``path.name`` would be unsafe to load.

        Mirrors :func:`_validate_policy_id` on the basename only:
        a stem that contains ``..`` or a name that contains a path
        separator or NUL byte is flagged.
        """
        name = path.name
        if not name:
            return True
        if "/" in name or "\\" in name or "\x00" in name:
            return True
        return ".." in Path(name).stem

    def _cleanup_if_expired(self, f: Path) -> bool:
        """Helper to check and cleanup a single override file."""
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            override = cast("PolicyOverride", PolicyOverride.from_dict(data))
            if not override.is_active():
                f.unlink()
                return True
        except Exception as e:
            _log.error("Failed to cleanup override %s: %s", f, e)
        return False

    def _save_override(self, override: PolicyOverride) -> None:
        """Save override to disk.

        ``policy_id`` is revalidated here as a defense-in-depth measure:
        :meth:`apply_override` already validates upstream, but
        ``_save_override`` is also reachable from test fixtures and
        refactors, so the guard must live at the file boundary too.
        """
        _validate_policy_id(override.policy_id)
        p = self.override_dir / f"{override.policy_id}.json"
        p.write_text(json.dumps(override.to_dict(), indent=2), encoding="utf-8")
