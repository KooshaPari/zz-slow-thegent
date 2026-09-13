"""OpenAPI surface inventory for the L15 audit lane.

This module loads the vendored :mod:`thegent.contracts.openapi` YAML and
exposes a small helper API so other code (CLI status, scorecards, CI
gates) can verify the public surface is intact.

Why a vendored YAML instead of auto-generation?  The MCP server uses
FastMCP which decorates functions as tools/resources without exposing
its routes through a FastAPI/Starlette ``openapi()`` call.  Auto-gen
would require pulling Starlette's introspection surface into the MCP
server — out of scope for this hardening pass.  The vendored spec is
the contract; future passes replace it with a generator.

Public surface
--------------

* :func:`load_spec` — load + minimally-validate the YAML.
* :func:`endpoint_count` — number of operations under ``paths``.
* :func:`cli_commands` — list of CLI entry points documented under
  ``x-cli-command`` (Typer entry points declared in ``pyproject.toml``).
* :func:`surface_summary` — return a small dict suitable for a scorecard
  row or a CLI ``status`` command.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_SPEC_PATH = Path(__file__).with_name("openapi.yaml")


@dataclass(slots=True, frozen=True)
class SurfaceSummary:
    """Summary metrics for the L15 audit lane."""

    openapi_version: str
    title: str
    version: str
    path_count: int
    operation_count: int
    cli_command_count: int
    endpoint_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict (JSON-friendly)."""
        return {
            "openapi_version": self.openapi_version,
            "title": self.title,
            "version": self.version,
            "path_count": self.path_count,
            "operation_count": self.operation_count,
            "cli_command_count": self.cli_command_count,
            "endpoint_count": self.endpoint_count,
        }


def load_spec(path: os.PathLike[str] | str | None = None) -> dict[str, Any]:
    """Load the vendored OpenAPI spec from YAML.

    Args:
        path: Optional override for the spec path. Defaults to
            ``openapi.yaml`` next to this module.

    Returns:
        Parsed YAML as a dict.

    Raises:
        FileNotFoundError: When the spec file does not exist.
        yaml.YAMLError: When the YAML is malformed.
    """
    spec_path = Path(path) if path is not None else _SPEC_PATH
    with spec_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"openapi spec at {spec_path} is not a mapping")
    return data


def _count_operations(paths: dict[str, Any]) -> int:
    """Count HTTP operations across all paths.

    Each path may declare ``get``, ``post``, ``put``, ``delete``, ``patch``,
    ``options``, ``head``. We sum them.
    """
    verbs = {"get", "post", "put", "delete", "patch", "options", "head"}
    total = 0
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for verb in path_item:
            if verb.lower() in verbs:
                total += 1
    return total


def endpoint_count(spec: dict[str, Any]) -> int:
    """Return the number of distinct HTTP operations in the spec.

    Args:
        spec: Parsed OpenAPI spec.

    Returns:
        Integer count of ``{verb, path}`` operations.
    """
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict):
        return 0
    return _count_operations(paths)


def cli_commands(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the CLI command inventory under ``x-cli-command``.

    Args:
        spec: Parsed OpenAPI spec.

    Returns:
        List of command dicts (``name``, ``description``, ``subcommands``).
    """
    commands = spec.get("x-cli-command") or []
    if not isinstance(commands, list):
        return []
    return [c for c in commands if isinstance(c, dict)]


def path_count(spec: dict[str, Any]) -> int:
    """Return the number of declared paths in the spec."""
    paths = spec.get("paths") or {}
    return len(paths) if isinstance(paths, dict) else 0


_VERBS = frozenset({"get", "post", "put", "delete", "patch", "options", "head"})


def list_endpoint_paths(spec: dict[str, Any]) -> tuple[str, ...]:
    """Return a sorted tuple of every path declared in the spec."""
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict):
        return ()
    return tuple(sorted(paths.keys()))


def list_endpoints(
    spec: dict[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Return ``[(verb, path, operation), ...]`` for every HTTP operation.

    Only HTTP verbs (per RFC 9110 + OpenAPI 3.1) are returned, in the
    order they appear in the YAML. Use this when you need to walk the
    full inventory rather than look up a single ``(path, verb)`` pair.
    """
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict):
        return []
    inventory: list[tuple[str, str, dict[str, Any]]] = []
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for verb, operation in path_item.items():
            if verb.lower() not in _VERBS or not isinstance(operation, dict):
                continue
            inventory.append((verb.lower(), str(path), operation))
    return inventory


def find_endpoint(
    spec: dict[str, Any],
    path: str,
    verb: str,
) -> dict[str, Any] | None:
    """Return the operation dict for ``(path, verb)`` or ``None``."""
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict):
        return None
    path_item = paths.get(path)
    if not isinstance(path_item, dict):
        return None
    operation = path_item.get(verb.lower())
    return operation if isinstance(operation, dict) else None


def schema_names(spec: dict[str, Any]) -> tuple[str, ...]:
    """Return a sorted tuple of every schema declared under ``components``."""
    components = spec.get("components") or {}
    schemas = components.get("schemas") or {}
    if not isinstance(schemas, dict):
        return ()
    return tuple(sorted(schemas.keys()))


def surface_summary(path: os.PathLike[str] | str | None = None) -> SurfaceSummary:
    """Build a summary suitable for a scorecard row.

    Args:
        path: Optional override for the spec path.

    Returns:
        :class:`SurfaceSummary` dataclass with title, version, counts.
    """
    spec = load_spec(path)
    info = spec.get("info") or {}
    return SurfaceSummary(
        openapi_version=str(spec.get("openapi") or "unknown"),
        title=str(info.get("title") or "untitled"),
        version=str(info.get("version") or "0.0.0"),
        path_count=path_count(spec),
        operation_count=endpoint_count(spec),
        cli_command_count=len(cli_commands(spec)),
        endpoint_count=endpoint_count(spec),
    )


__all__ = [
    "SurfaceSummary",
    "cli_commands",
    "endpoint_count",
    "find_endpoint",
    "list_endpoint_paths",
    "list_endpoints",
    "load_spec",
    "path_count",
    "schema_names",
    "surface_summary",
]
