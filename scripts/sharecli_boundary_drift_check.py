"""Reporter for the staged thegent -> sharecli boundary drift check."""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from pathlib import Path
from typing import Any, NamedTuple

DEFAULT_CONFIG = "config/sharecli_boundary_drift_allowlist.toml"
DRIFT_SPEC = "docs/specs/contracts/sharecli-boundary-drift-check.md"
CONTRACT_SPEC = "docs/specs/contracts/sharecli-boundary-contracts.md"

IGNORED_PREFIXES = (
    "docs/",
    "apps/byteport/backend/api/.archive/thegent-test-deduplication/",
)

SUBSTRATE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("thegent_cli_share", "queue"),
    ("thegent.mesh.task_queue", "queue"),
    ("thegent.mesh.smart_merge", "merge-worktree"),
    ("thegent.mesh.git_parallelism", "merge-worktree"),
    ("thegent.mesh.worktree", "merge-worktree"),
    ("thegent_gitops", "merge-worktree"),
    ("thegent.mesh.process_detection", "process-health"),
    ("thegent.mesh.resources", "execution-safety"),
    ("thegent.mesh.sandbox", "execution-safety"),
    ("thegent.mesh.injection", "execution-safety"),
    ("thegent.mesh.mesh", "execution-safety"),
)

SCAN_FILES = (
    "src/thegent/mesh/cli.py",
    "src/thegent/mesh/main.py",
    "src/thegent/mesh/mesh.py",
    "src/thegent/mesh/agent_patterns.py",
    "src/thegent/mesh/audit.py",
    "src/thegent/mesh/observability.py",
)

SCAN_DIRS = (
    "src/thegent/governance",
    "src/thegent_gitops",
)


class AllowEntry(NamedTuple):
    path: str
    symbol: str
    lane: str
    sunset_gate: str
    reason: str


class Finding(NamedTuple):
    path: str
    line: int
    pattern: str
    lane: str
    severity: str
    allowlisted: bool
    sunset_gate: str


def _to_posix(path: Path) -> str:
    return path.as_posix()


def _relative_path(path: Path, root: Path) -> str:
    return _to_posix(path.resolve().relative_to(root.resolve()))


def _is_ignored(relative_path: str) -> bool:
    return any(relative_path == prefix.rstrip("/") or relative_path.startswith(prefix) for prefix in IGNORED_PREFIXES)


def _load_config(config_path: Path) -> tuple[list[AllowEntry], set[str]]:
    if not config_path.exists():
        return [], set()

    with config_path.open("rb") as handle:
        payload = tomllib.load(handle)

    section = payload.get("sharecli_boundary", {})
    enforced_lanes = set(section.get("enforced_lanes", []))
    entries = [
        AllowEntry(
            path=str(item.get("path", "")),
            symbol=str(item.get("symbol", "")),
            lane=str(item.get("lane", "")),
            sunset_gate=str(item.get("sunset_gate", "")),
            reason=str(item.get("reason", "")),
        )
        for item in section.get("allow", [])
    ]
    return entries, enforced_lanes


def _import_matches(import_name: str, pattern: str) -> bool:
    return import_name == pattern or import_name.startswith(pattern + ".")


def _allow_matches(entry: AllowEntry, relative_path: str, import_name: str, lane: str) -> bool:
    return (
        entry.path == relative_path
        and entry.lane == lane
        and entry.sunset_gate
        and _import_matches(import_name, entry.symbol)
    )


def _extract_imports(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.lineno, node.module))
    return sorted(imports)


def _scan_roots(root: Path) -> list[Path]:
    files: set[Path] = set()
    for rel in SCAN_FILES:
        candidate = root / rel
        if candidate.exists():
            files.add(candidate)
    for rel in SCAN_DIRS:
        candidate = root / rel
        if candidate.exists():
            files.update(candidate.rglob("*.py"))
    return sorted(files)


def _severity(lane: str, allowlisted: bool, enforced_lanes: set[str]) -> str:
    if lane in enforced_lanes and not allowlisted:
        return "fail"
    return "warn" if allowlisted else "info"


def _finding_for_import(
    relative_path: str,
    line: int,
    import_name: str,
    lane: str,
    allowlist: list[AllowEntry],
    enforced_lanes: set[str],
) -> Finding:
    matched_entry = next(
        (entry for entry in allowlist if _allow_matches(entry, relative_path, import_name, lane)),
        None,
    )
    allowlisted = matched_entry is not None
    sunset_gate = matched_entry.sunset_gate if matched_entry else ""
    return Finding(
        path=relative_path,
        line=line,
        pattern=import_name,
        lane=lane,
        severity=_severity(lane, allowlisted, enforced_lanes),
        allowlisted=allowlisted,
        sunset_gate=sunset_gate,
    )


def _scan_python_imports(root: Path, allowlist: list[AllowEntry], enforced_lanes: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in _scan_roots(root):
        relative_path = _relative_path(path, root)
        if _is_ignored(relative_path):
            continue
        for line, import_name in _extract_imports(path):
            for pattern, lane in SUBSTRATE_PATTERNS:
                if _import_matches(import_name, pattern):
                    findings.append(
                        _finding_for_import(
                            relative_path,
                            line,
                            import_name,
                            lane,
                            allowlist,
                            enforced_lanes,
                        )
                    )
                    break
    return findings


def _scan_native_harness(root: Path, enforced_lanes: set[str]) -> list[Finding]:
    native_root = root / "crates" / "harness-native"
    if not native_root.exists():
        return []

    findings: list[Finding] = []
    for path in sorted(item for item in native_root.rglob("*") if item.is_file()):
        relative_path = _relative_path(path, root)
        if _is_ignored(relative_path):
            continue
        findings.append(
            Finding(
                path=relative_path,
                line=1,
                pattern="crates/harness-native",
                lane="native-harness",
                severity="fail" if "native-harness" in enforced_lanes else "info",
                allowlisted=False,
                sunset_gate="",
            )
        )
    return findings


def collect_findings(root: Path, config_path: Path, enforce_lanes: set[str] | None = None) -> list[Finding]:
    allowlist, configured_lanes = _load_config(config_path)
    enforced_lanes = configured_lanes | (enforce_lanes or set())
    findings = _scan_python_imports(root, allowlist, enforced_lanes)
    findings.extend(_scan_native_harness(root, enforced_lanes))
    return sorted(findings, key=lambda item: (item.path, item.line, item.pattern))


def _count_by(items: list[Finding], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(getattr(item, field))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def build_payload(findings: list[Finding], mode: str) -> dict[str, Any]:
    fail_count = sum(1 for item in findings if item.severity == "fail")
    return {
        "ok": fail_count == 0,
        "mode": mode,
        "finding_count": len(findings),
        "fail_count": fail_count,
        "counts_by_lane": _count_by(findings, "lane"),
        "counts_by_severity": _count_by(findings, "severity"),
        "findings": [item._asdict() for item in findings],
        "spec": DRIFT_SPEC,
        "contract": CONTRACT_SPEC,
    }


def build_summary_payload(findings: list[Finding], mode: str) -> dict[str, Any]:
    payload = build_payload(findings, mode)
    return {
        "ok": payload["ok"],
        "mode": payload["mode"],
        "finding_count": payload["finding_count"],
        "fail_count": payload["fail_count"],
        "counts_by_lane": payload["counts_by_lane"],
        "counts_by_severity": payload["counts_by_severity"],
    }


def _print_text(findings: list[Finding], mode: str) -> None:
    summary = build_summary_payload(findings, mode)
    print("ShareCLI boundary drift check")
    print(f"mode: {mode}")
    print(f"findings: {summary['finding_count']}")
    print(f"failures: {summary['fail_count']}")
    print(f"counts_by_lane: {json.dumps(summary['counts_by_lane'], sort_keys=True)}")
    print(f"counts_by_severity: {json.dumps(summary['counts_by_severity'], sort_keys=True)}")
    print(f"spec: {DRIFT_SPEC}")
    print(f"contract: {CONTRACT_SPEC}")

    failing = [item for item in findings if item.severity == "fail"]
    for item in failing[:5]:
        print(f"{item.path}:{item.line}: {item.lane}: {item.pattern}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Boundary allowlist config.")
    parser.add_argument("--format", choices=("text", "json", "summary-json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when fail findings exist.")
    parser.add_argument(
        "--enforce-lane",
        action="append",
        default=[],
        help="Treat a migration lane as enforced.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    config_path = (root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    mode = "strict" if args.strict else "reporter"
    findings = collect_findings(root, config_path, set(args.enforce_lane))

    if args.format == "json":
        print(json.dumps(build_payload(findings, mode), indent=2, sort_keys=True))
    elif args.format == "summary-json":
        print(json.dumps(build_summary_payload(findings, mode), sort_keys=True))
    else:
        _print_text(findings, mode)

    return 1 if args.strict and any(item.severity == "fail" for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
