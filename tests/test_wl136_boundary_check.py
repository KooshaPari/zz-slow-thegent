"""WL-136 B90-W2-A3: Core vs tooling boundary import checks.

Core modules: contract-derived core zones from `config/thegent_core_boundary.toml`
Tooling modules: cli/apps, cli/commands, mcp, tui, ux, infra

Rule: core modules MUST NOT import from tooling modules.
This test fails loudly (not skips) on any detected violation.
"""
# @trace WL-136 B90-W2-A3

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

# --- Configuration ---

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src" / "thegent"
_BOUNDARY_CONFIG = _REPO_ROOT / "config" / "thegent_core_boundary.toml"
_CORE_ZONE_KEYS: tuple[str, ...] = ("core", "queue", "config")


def _resolve_zone_to_paths(zone_module: str) -> list[Path]:
    """Resolve zone module to existing source paths under src/thegent."""
    if not zone_module.startswith("thegent."):
        return []

    rel = zone_module.removeprefix("thegent.").replace(".", "/")
    candidates = [_SRC_ROOT / rel, _SRC_ROOT / f"{rel}.py"]
    return [path for path in candidates if path.exists()]


def _load_core_module_paths() -> list[Path]:
    """Load core-zone paths from the canonical core-boundary config."""
    if not _BOUNDARY_CONFIG.exists():
        return []

    with _BOUNDARY_CONFIG.open("rb") as handle:
        config = tomllib.load(handle)
    zones = config.get("core_boundary", {}).get("zones", {})

    resolved_paths: list[Path] = []
    for zone_key in _CORE_ZONE_KEYS:
        zone_module = zones.get(zone_key)
        if isinstance(zone_module, str):
            resolved_paths.extend(_resolve_zone_to_paths(zone_module))
    # Preserve deterministic order and remove duplicates
    return sorted(set(resolved_paths))


# Core module source paths (resolved from config/thegent_core_boundary.toml)
CORE_MODULE_PATHS: list[Path] = _load_core_module_paths()

# Tooling import prefixes that core modules must not import
TOOLING_IMPORT_PREFIXES: tuple[str, ...] = (
    "thegent.cli",
    "thegent.mcp",
    "thegent.tui",
    "thegent.ux",
    "thegent.infra",
)


def _collect_python_files(path: Path) -> list[Path]:
    """Collect all .py files under a path (file or directory)."""
    if path.is_file():
        return [path] if path.suffix == ".py" else []
    return sorted(path.rglob("*.py"))


def _extract_imports(source_file: Path) -> list[str]:
    """Extract all imported module names from a Python source file via AST."""
    try:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    except SyntaxError:
        return []

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return sorted(imports)


def _find_boundary_violations() -> list[dict[str, str]]:
    """Scan core module files and return any tooling import violations."""
    violations: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for core_path in CORE_MODULE_PATHS:
        if not core_path.exists():
            continue
        py_files = _collect_python_files(core_path)
        for py_file in py_files:
            # Skip __pycache__ and test files
            if "__pycache__" in str(py_file):
                continue
            imports = _extract_imports(py_file)
            for imp in imports:
                for tooling_prefix in TOOLING_IMPORT_PREFIXES:
                    if imp == tooling_prefix or imp.startswith(tooling_prefix + "."):
                        key = (str(py_file.relative_to(_REPO_ROOT)), imp, tooling_prefix)
                        if key in seen:
                            continue
                        seen.add(key)
                        violations.append(
                            {
                                "file": str(py_file.relative_to(_REPO_ROOT)),
                                "import": imp,
                                "violates": tooling_prefix,
                            }
                        )
                        break  # one violation per import per file

    return violations


# --- Tests ---


def test_core_boundary_config_exists() -> None:
    """Canonical core-boundary config used by this checker must exist."""
    assert _BOUNDARY_CONFIG.exists(), f"WL-136: Missing boundary config: {_BOUNDARY_CONFIG}"


def test_core_modules_do_not_import_tooling_no_violations_detected() -> None:
    """Core modules must not import from tooling surfaces.

    Fails loudly with violation details if any are found.
    """
    violations = _find_boundary_violations()

    if violations:
        lines = [
            f"\nWL-136 BOUNDARY VIOLATION: {len(violations)} core->tooling import(s) detected:",
        ]
        for v in violations:
            lines.append(f"  {v['file']}: imports '{v['import']}' (tooling prefix: {v['violates']})")
        lines.append(
            "\nFix: remove tooling imports from core modules. "
            "Move shared logic to a boundary-neutral helper or inject via dependency."
        )
        raise AssertionError("\n".join(lines))


def test_core_module_paths_exist() -> None:
    """Configured core module paths referenced in this test must exist in the repo."""
    missing = [p for p in CORE_MODULE_PATHS if not p.exists()]
    if missing:
        raise AssertionError(
            f"WL-136: Configured core module paths not found: {[str(p) for p in missing]}. "
            "Update config/thegent_core_boundary.toml zone mappings if modules were relocated."
        )


def test_tooling_prefix_list_is_non_empty() -> None:
    """Tooling prefix list must not be empty (guard against accidental clearing)."""
    assert len(TOOLING_IMPORT_PREFIXES) >= 4, "WL-136: TOOLING_IMPORT_PREFIXES must define at least cli, mcp, tui, ux"


def test_boundary_check_scans_at_least_one_core_file() -> None:
    """Boundary check must scan at least one Python file from core modules."""
    files_scanned = []
    for core_path in CORE_MODULE_PATHS:
        if core_path.exists():
            files_scanned.extend(_collect_python_files(core_path))
    assert len(files_scanned) > 0, "WL-136: No core module Python files found to scan. Check that _SRC_ROOT is correct."
