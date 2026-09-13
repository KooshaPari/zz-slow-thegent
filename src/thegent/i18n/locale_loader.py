"""Locale catalog loader for ``src.thegent.i18n``.

This module turns on-disk ``.yaml`` translation catalogs (one file per
locale under ``locales/``) into the in-memory catalog dictionaries
consumed by :func:`thegent.i18n.register_catalog`.

Goals (WP-4011):

* Zero runtime dependency on ``gettext`` — the existing
  ``src.thegent.i18n`` stub already provides the lookup table.
* Catalog discovery is path-agnostic: tests can point at a tempdir of
  YAML files, while production code uses the ``locales/`` directory
  shipped alongside this module.
* Loader errors are surfaced as typed exceptions so the cockpit can
  render them without spelunking through PyYAML stack traces.

**Traces to**: WP-4011 (locale scaffolding), L17 I18n/A11y
(audit scorecard), L30 Onboarding (locale catalog ships out of the
box so first-run users see translated chrome).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LocaleError(ValueError):
    """Base error raised by the locale loader."""


class LocaleNotFoundError(LocaleError, FileNotFoundError):
    """Raised when a requested locale has no YAML catalog on disk."""


class LocaleParseError(LocaleError):
    """Raised when a locale YAML file is malformed (not a mapping)."""


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LocaleFile:
    """A single locale YAML file resolved to (locale-code, catalog-dict)."""

    locale: str
    path: Path
    catalog: Mapping[str, str]


def locales_dir() -> Path:
    """Return the canonical ``locales/`` directory shipped with the package.

    The directory may not yet exist if no catalogs have been shipped; in
    that case the loader will raise :class:`LocaleNotFoundError` for any
    request.
    """
    return Path(__file__).resolve().parent / "locales"


def discover_locales(directory: Path | None = None) -> tuple[str, ...]:
    """Return a sorted tuple of locale codes available under ``directory``.

    Only ``*.yaml`` / ``*.yml`` files are considered; non-mapping YAML
    payloads are silently skipped (the parse error is raised on demand
    via :func:`load_catalog`).
    """
    base = (directory or locales_dir()).resolve()
    if not base.exists():
        return ()
    codes: list[str] = []
    for candidate in sorted(base.glob("*.y*ml")):
        if candidate.stem:
            codes.append(candidate.stem)
    return tuple(codes)


def _read_catalog(path: Path) -> Mapping[str, str]:
    """Parse a YAML catalog file and assert it is a string→string mapping."""
    if not path.exists():
        raise LocaleNotFoundError(f"Locale catalog not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if loaded is None:
        return {}
    if not isinstance(loaded, Mapping):
        raise LocaleParseError(
            f"Locale catalog {path} must be a YAML mapping, got {type(loaded).__name__}"
        )
    catalog: dict[str, str] = {}
    for key, value in loaded.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise LocaleParseError(
                f"Locale catalog {path} keys/values must be strings (key={key!r} value={value!r})"
            )
        catalog[key] = value
    return catalog


def load_catalog(locale: str, directory: Path | None = None) -> LocaleFile:
    """Load a single locale YAML file and return a :class:`LocaleFile`.

    Raises :class:`LocaleNotFoundError` if the file is missing and
    :class:`LocaleParseError` if the YAML is malformed.
    """
    base = (directory or locales_dir()).resolve()
    for suffix in (".yaml", ".yml"):
        candidate = base / f"{locale}{suffix}"
        if candidate.exists():
            return LocaleFile(
                locale=locale, path=candidate, catalog=_read_catalog(candidate)
            )
    raise LocaleNotFoundError(f"No locale catalog found for {locale!r} under {base}")


def load_all(directory: Path | None = None) -> list[LocaleFile]:
    """Load every locale YAML file under ``directory`` (sorted by locale)."""
    base = (directory or locales_dir()).resolve()
    if not base.exists():
        return []
    return [load_catalog(code, base) for code in discover_locales(base)]


def register_all(directory: Path | None = None) -> dict[str, int]:
    """Load every locale YAML file and register it with ``thegent.i18n``.

    Returns a ``{locale: new-message-ids}`` mapping so callers can
    surface the catalog size in the cockpit.
    """
    # Local import keeps the loader usable even if the i18n stub
    # failed to import (e.g. during interpreter startup tweaks).
    from thegent import i18n

    totals: dict[str, int] = {}
    for locale_file in load_all(directory):
        added = i18n.register_catalog(locale_file.locale, locale_file.catalog)
        totals[locale_file.locale] = added
    return totals


def bundle_message_ids(directory: Path | None = None) -> set[str]:
    """Return the union of every message-id across all locale catalogs.

    Useful for the cockpit's "translation completeness" meter: the
    caller can compare this set to the set of keys present in a given
    locale's catalog to compute coverage.
    """
    bundle: set[str] = set()
    for locale_file in load_all(directory):
        bundle.update(locale_file.catalog)
    return bundle


def coverage(
    locale: str,
    *,
    directory: Path | None = None,
    message_ids: Iterable[str] | None = None,
) -> tuple[int, int]:
    """Return ``(translated, total)`` counts for ``locale``.

    ``total`` defaults to the union of every message-id shipped across
    all locale catalogs. A locale with full coverage returns
    ``(total, total)``.
    """
    bundle: set[str]
    bundle = bundle_message_ids(directory) if message_ids is None else set(message_ids)
    if not bundle:
        return (0, 0)
    try:
        catalog = load_catalog(locale, directory).catalog
    except LocaleNotFoundError:
        return (0, len(bundle))
    translated = sum(1 for key in bundle if key in catalog)
    return (translated, len(bundle))


__all__ = [
    "LocaleError",
    "LocaleFile",
    "LocaleNotFoundError",
    "LocaleParseError",
    "bundle_message_ids",
    "coverage",
    "discover_locales",
    "load_all",
    "load_catalog",
    "locales_dir",
    "register_all",
]
