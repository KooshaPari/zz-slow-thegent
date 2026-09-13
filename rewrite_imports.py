#!/usr/bin/env python3
"""Rewrite `from thegent.X` / `import thegent.X` imports in the three
workspace packages, mapping old monorepo modules to their new package names.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-to-package mapping (first-segment after 'thegent.')
# More specific patterns must come before shorter ones.
# ---------------------------------------------------------------------------
MODULE_TO_PKG: list[tuple[str, str]] = [
    # thegent_core
    ("domain", "thegent_core"),
    ("ports", "thegent_core"),
    ("config", "thegent_core"),
    ("constants", "thegent_core"),
    ("contracts", "thegent_core"),
    ("models", "thegent_core"),
    # thegent_execution
    ("execution", "thegent_execution"),
    ("process", "thegent_execution"),
    ("isolation", "thegent_execution"),
    ("shell", "thegent_execution"),
    ("muxless", "thegent_execution"),
    ("session", "thegent_execution"),
    # thegent_agents
    ("agents", "thegent_agents"),
    ("swarm", "thegent_agents"),
    ("team", "thegent_agents"),
    ("teammates", "thegent_agents"),
    ("mesh", "thegent_agents"),
    ("coordination", "thegent_agents"),
    # thegent_protocols
    ("protocols", "thegent_protocols"),
    ("acp", "thegent_protocols"),
    ("mcp", "thegent_protocols"),
    ("sdk", "thegent_protocols"),
    ("ipc", "thegent_protocols"),
    ("api_client", "thegent_protocols"),
    # thegent_skills
    ("skills", "thegent_skills"),
    ("tools", "thegent_skills"),
    ("hooks", "thegent_skills"),
    ("rules", "thegent_skills"),
    # thegent_observability
    ("telemetry", "thegent_observability"),
    ("metrics", "thegent_observability"),
    ("monitoring", "thegent_observability"),
    ("observability", "thegent_observability"),
    ("trace", "thegent_observability"),
    ("logging_utils", "thegent_observability"),
    # thegent_planning
    ("planning", "thegent_planning"),
    ("phases", "thegent_planning"),
    ("work_packages", "thegent_planning"),
    ("design", "thegent_planning"),
    ("research", "thegent_planning"),
    # thegent_bench
    ("bench", "thegent_bench"),
    ("evals", "thegent_bench"),
    ("evaluation", "thegent_bench"),
    ("phench", "thegent_bench"),
    # thegent_audit
    ("audit_v2", "thegent_audit"),
    ("audit", "thegent_audit"),
    ("forensics", "thegent_audit"),
    ("governance", "thegent_audit"),
    ("govern", "thegent_audit"),
    ("security_utils", "thegent_audit"),
    ("security", "thegent_audit"),
    ("verification", "thegent_audit"),
    # thegent_sync
    ("sync", "thegent_sync"),
    ("autosync", "thegent_sync"),
    ("integrations", "thegent_sync"),
    ("integration", "thegent_sync"),
    # thegent_routing  (provider_* top-level names)
    ("cost", "thegent_routing"),
    ("economy", "thegent_routing"),
    ("provider", "thegent_routing"),
    ("providers", "thegent_routing"),
    ("routing", "thegent_routing"),
    ("provider_model_manager_cliproxy", "thegent_routing"),
    ("provider_model_manager_io", "thegent_routing"),
    ("provider_model_manager_sorting", "thegent_routing"),
    ("provider_model_manager", "thegent_routing"),
    ("provider_model_scoring", "thegent_routing"),
    ("provider_crud", "thegent_routing"),
    ("provider_forms", "thegent_routing"),
    ("provider_search", "thegent_routing"),
    # thegent_platform
    ("desktop", "thegent_platform"),
    ("gpu", "thegent_platform"),
    ("native", "thegent_platform"),
    ("tray", "thegent_platform"),
    ("platform_paths", "thegent_platform"),
    # thegent_cli
    ("cli", "thegent_cli"),
    ("commands", "thegent_cli"),
    ("tui", "thegent_cli"),
    ("ui", "thegent_cli"),
    ("ux", "thegent_cli"),
    # use_cases (not in mapping; treat as thegent_core for now)
    ("use_cases", "thegent_core"),
    # core infra/utility modules
    ("config_defaults", "thegent_core"),
    ("config_parsers", "thegent_core"),
    ("output_parser", "thegent_core"),
    ("utils", "thegent_core"),
    ("infra", "thegent_core"),
    ("cache", "thegent_core"),
]

# Build a dict for O(1) lookup: first_segment -> new_pkg
_SEG_TO_PKG: dict[str, str] = {}
for seg, pkg in MODULE_TO_PKG:
    if seg not in _SEG_TO_PKG:
        _SEG_TO_PKG[seg] = pkg

# Regex: match import lines only
# Group 1: "from " or "import "
# Group 2: "thegent."
# Group 3: rest of dotted module path (e.g. "config.settings")
_IMPORT_RE = re.compile(
    r"^(\s*(?:from|import)\s+)"  # leading whitespace + from/import keyword
    r"(thegent)"  # the old top-level package
    r"(\.[A-Za-z0-9_.]+)",  # .module.submodule...
    re.MULTILINE,
)


def rewrite_line(m: re.Match) -> str:
    """Return the rewritten import string."""
    prefix = m.group(1)  # e.g. "from " or "import "
    # m.group(2) == "thegent"
    rest = m.group(3)  # e.g. ".config.settings"

    # First segment after 'thegent.'
    parts = rest.lstrip(".").split(".")
    first = parts[0]

    new_pkg = _SEG_TO_PKG.get(first)
    if new_pkg is None:
        # Unknown segment — leave unchanged and warn
        return m.group(0)

    # Determine which package the *file being rewritten* belongs to, so we
    # can decide whether to strip the first segment or keep it.
    # Strategy: the new package name maps to a top-level Python package; the
    # old "thegent.X.Y" becomes "new_pkg.X.Y" where X is the first segment
    # ONLY if X is NOT the top-level of new_pkg (i.e., cross-package).
    # For same-package: "thegent.config.settings" in thegent_core → "thegent_core.config.settings"
    # For cross-package top-level module: "thegent.provider_forms" in thegent_routing → "thegent_routing.provider_forms"
    # The rest already includes the first segment, so just swap "thegent" → new_pkg.
    new_import = prefix + new_pkg + rest
    return new_import


def rewrite_file(path: Path) -> int:
    """Rewrite a single file. Returns the number of lines changed."""
    original = path.read_text(encoding="utf-8")
    rewritten = _IMPORT_RE.sub(rewrite_line, original)
    if rewritten == original:
        return 0
    path.write_text(rewritten, encoding="utf-8")
    return (
        original.count("\n")
        - rewritten.count("\n")
        + len(
            [
                l
                for l in rewritten.splitlines()
                if l != original.splitlines()[original.splitlines().index(l)]
                if False
            ]
        )
    )


def count_changes(original: str, rewritten: str) -> int:
    orig_lines = original.splitlines()
    new_lines = rewritten.splitlines()
    return sum(1 for a, b in zip(orig_lines, new_lines, strict=False) if a != b) + abs(
        len(orig_lines) - len(new_lines)
    )


def process_directory(root: Path) -> None:
    files = sorted(root.rglob("*.py"))
    total_files = 0
    total_changes = 0
    for f in files:
        original = f.read_text(encoding="utf-8")
        rewritten = _IMPORT_RE.sub(rewrite_line, original)
        if rewritten != original:
            changes = count_changes(original, rewritten)
            total_changes += changes
            total_files += 1
            f.write_text(rewritten, encoding="utf-8")


BASE = Path(
    "/Users/kooshapari/CodeProjects/Phenotype/repos/thegent-wtrees/workspace/packages"
)

PACKAGES = [
    BASE / "thegent-core/src/thegent_core",
    BASE / "thegent-observability/src/thegent_observability",
    BASE / "thegent-routing/src/thegent_routing",
]

for pkg_dir in PACKAGES:
    process_directory(pkg_dir)
