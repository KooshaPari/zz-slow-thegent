"""Internationalization (i18n) helpers for thegent.

This is a deliberately small, dependency-free stub that the rest of the
codebase can call into without pulling in ``gettext`` translate catalogs
at runtime. The goals are:

* Provide a stable ``_()`` lookup function so callers can begin writing
  translatable strings today.
* Make it easy to instrument the cockpit and other UX surfaces with
  locale-aware labels later (without rewriting call sites).
* Keep the import graph cheap — no catalog loading on the hot path.

The stub is intentionally a no-op for unknown locales so existing
English strings keep working unmodified. To enable real translation,
call :func:`set_locale` with a locale name and provide a dict to
:func:`register_catalog` mapping message-ids to translated strings.

**Traces to**: WP-4010 (i18n scaffolding), L17 I18n/A11y (audit scorecard).
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Final

# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

_DEFAULT_LOCALE: Final[str] = "en"
_VALID_LOCALES: Final[frozenset[str]] = frozenset({"en", "en-US", "en-GB", "fr", "de", "es", "ja"})


def _gettext_gettext(message: str) -> str:
    """Return the translated string for ``message`` (alias for ``_()``).

    Falls back to the input string if no catalog is registered for the
    current locale. This stub always returns the input unless
    :func:`register_catalog` has been called with a non-empty catalog.
    """
    with _lock:
        catalog = _catalogs.get(_current_locale, {})
    return catalog.get(message, message)


# Conventional alias for gettext-style call sites.
_ = _gettext_gettext


def get_locale() -> str:
    """Return the current locale code (default ``"en"``)."""
    with _lock:
        return _current_locale


def set_locale(locale: str) -> None:
    """Switch the active locale.

    Unknown locales are kept as-is so that downstream renderers can
    handle them, but :func:`available_locales` will not list them.
    Use :func:`validate_locale` to assert a locale is supported.
    """
    global _current_locale
    with _lock:
        _current_locale = locale


def available_locales() -> tuple[str, ...]:
    """Return a sorted tuple of locales with a registered catalog."""
    with _lock:
        return tuple(sorted(_catalogs.keys()))


def supported_locales() -> tuple[str, ...]:
    """Return a sorted tuple of locales the stub recognizes as valid."""
    return tuple(sorted(_VALID_LOCALES))


def validate_locale(locale: str) -> bool:
    """Return True if ``locale`` is in the supported set."""
    return locale in _VALID_LOCALES


def register_catalog(locale: str, catalog: Mapping[str, str]) -> int:
    """Register / merge a translation catalog for ``locale``.

    Returns the number of new message-ids added by this call.
    """
    with _lock:
        existing = _catalogs.setdefault(locale, {})
        before = len(existing)
        existing.update(catalog)
        return len(existing) - before


def reset_catalogs() -> None:
    """Clear all registered catalogs. Intended for tests."""
    with _lock:
        _catalogs.clear()


# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_lock = RLock()
_current_locale: str = _DEFAULT_LOCALE
_catalogs: dict[str, dict[str, str]] = {}


__all__ = [
    "_",
    "_gettext_gettext",
    "available_locales",
    "get_locale",
    "register_catalog",
    "reset_catalogs",
    "set_locale",
    "supported_locales",
    "validate_locale",
]
