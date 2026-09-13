"""WP-10001: ConfigProvider protocol and implementations for Control Plane Phase 1.

Hardening (AUDIT-N+86 — SOTA pass-70)
--------------------------------------
Contract surface asserted by
``tests/test_unit_audit_n86_config_provider_hardening.py``
(``FR-GOV-CFG-001..015``).

This module is the **canonical** implementation. The legacy import path
``thegent.config_provider`` re-exports from here so callers get a single,
consistent implementation surface.

# @trace AUDIT-N+86
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from thegent.config import ThegentSettings

__all__ = [
    "ConfigProvider",
    "EnvConfigProvider",
    "get_config_provider",
    "get_last_provider_metadata",
    "_attach_provider_metadata",
]

logger = logging.getLogger(__name__)

# Process-local metadata tracked on the most recent get_config_provider() call.
_last_provider_metadata: dict[str, Any] = {}


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for configuration resolution with override semantics.

    Implementations expose a ``provider_metadata`` attribute (dict) populated
    by ``_attach_provider_metadata`` so observers can audit which source
    produced the active provider.
    """

    provider_metadata: dict[str, Any]

    def resolve(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        request_overrides: dict[str, Any] | None = None,
        keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Resolve config for a given context.

        Resolution order: request_overrides -> session -> tenant -> stamp -> global.
        """
        ...

    def get_tenant_config(self, tenant_id: str) -> dict[str, Any] | None:
        """Fetch raw configuration for a specific tenant."""
        ...


class EnvConfigProvider:
    """Standard implementation using local ThegentSettings (env vars).

    Ignores tenant/session isolation; merges request overrides onto base settings.
    """

    provider_metadata: dict[str, Any]

    def __init__(self) -> None:
        """Initialize the env provider with empty metadata."""
        self.provider_metadata: dict[str, Any] = {
            "source": "env",
            "control_plane_configured": False,
            "dependency_missing": False,
        }

    def resolve(
        self,
        tenant_id: str | None = None,
        session_id: str | None = None,
        request_overrides: dict[str, Any] | None = None,
        keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Resolve config from local ThegentSettings."""
        _ = (tenant_id, session_id)
        settings = ThegentSettings()
        # Filter keys if requested
        if keys:
            base = {k: getattr(settings, k) for k in keys if hasattr(settings, k)}
        else:
            base = settings.model_dump()

        # Merge overrides
        if request_overrides:
            base.update(request_overrides)

        return base

    def get_tenant_config(self, tenant_id: str) -> dict[str, Any] | None:
        """Env provider does not support multi-tenancy yet."""
        _ = tenant_id
        return None


def _attach_provider_metadata(
    provider: Any,
    metadata: dict[str, Any],
) -> Any:
    """Attach the ``provider_metadata`` dict to a provider, if mutable.

    Returns the provider unchanged whether or not attribute assignment
    succeeds (e.g. for ``__slots__``-only providers).
    """
    try:
        provider.provider_metadata = dict(metadata)
    except (AttributeError, TypeError):
        # Non-extensible provider (e.g. __slots__); nothing to attach.
        logger.debug("Provider %r does not accept metadata attribute", provider)
    return provider


def _record_metadata(metadata: dict[str, Any]) -> None:
    """Update the last_provider_metadata global."""
    global _last_provider_metadata
    _last_provider_metadata = dict(metadata)


def get_last_provider_metadata() -> dict[str, Any]:
    """Return metadata describing the most recent ``get_config_provider`` call."""
    return dict(_last_provider_metadata)


def get_config_provider() -> ConfigProvider:
    """Factory to get the active config provider based on settings.

    Resolution precedence:
    1. If ``THGENT_CONTROL_PLANE_URL`` is configured, attempt to instantiate
       ``ControlPlaneConfigProvider``; on ImportError fall back to ``EnvConfigProvider``.
    2. Otherwise, return ``EnvConfigProvider``.
    """
    # The contract is: only the THGENT_CONTROL_PLANE_URL env var triggers
    # the control-plane provider. Settings.control_plane_url is a server
    # bind address default and must NOT short-circuit local env resolution.
    import os

    cp_url = os.environ.get("THGENT_CONTROL_PLANE_URL")
    if cp_url:
        metadata: dict[str, Any] = {
            "source": "control_plane",
            "control_plane_configured": True,
            "dependency_missing": False,
        }
        try:
            from thegent.control_plane.client import ControlPlaneConfigProvider

            provider = ControlPlaneConfigProvider(cp_url)
        except ImportError as exc:
            logger.warning("control-plane provider import failed: %s; falling back to env", exc)
            metadata["source"] = "env"
            metadata["dependency_missing"] = True
            provider = EnvConfigProvider()
        _record_metadata(metadata)
        return _attach_provider_metadata(provider, metadata)

    metadata = {
        "source": "env",
        "control_plane_configured": False,
        "dependency_missing": False,
    }
    provider = EnvConfigProvider()
    _record_metadata(metadata)
    return _attach_provider_metadata(provider, metadata)
