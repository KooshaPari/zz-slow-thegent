"""Legacy import path for ``thegent.config_provider``.

The canonical implementation lives at
``thegent.governance.config_provider`` (and ``thegent.governance.config_provider_cp``).
This module re-exports the public surface so older imports -- e.g.
``from thegent.config_provider import get_config_provider`` -- continue to work
while pointing at the canonical, fully-tested implementation.

The previous stub here was incomplete (missing ``import os``, lacked
``provider_metadata`` contract, missing ``_attach_provider_metadata`` helper)
and caused ``NameError`` on every ``resolve()`` call. See
``tests/test_unit_config_provider.py`` for the contract this module now
satisfies.

# @trace AUDIT-N+86
"""

from __future__ import annotations

import importlib
from typing import Any

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ConfigProvider": ("thegent.governance.config_provider", "ConfigProvider"),
    "EnvConfigProvider": ("thegent.governance.config_provider", "EnvConfigProvider"),
    "_attach_provider_metadata": (
        "thegent.governance.config_provider",
        "_attach_provider_metadata",
    ),
    "get_config_provider": (
        "thegent.governance.config_provider",
        "get_config_provider",
    ),
    "get_last_provider_metadata": (
        "thegent.governance.config_provider",
        "get_last_provider_metadata",
    ),
    "ControlPlaneConfigProvider": (
        "thegent.governance.config_provider_cp",
        "ControlPlaneConfigProvider",
    ),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        mod = importlib.import_module(module_path)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    "ConfigProvider",
    "ControlPlaneConfigProvider",
    "EnvConfigProvider",
    "get_config_provider",
    "get_last_provider_metadata",
    "_attach_provider_metadata",
]
