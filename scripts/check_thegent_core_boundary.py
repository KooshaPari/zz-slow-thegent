#!/usr/bin/env python3
"""Validate import boundaries for thegent.core modules (WL-121 slice)."""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "thegent_core_boundary.toml"
CORE_DIR = ROOT / "src" / "thegent" / "core"


def _load_policy(config_path: Path) -> tuple[list[str], list[str]]:
    with config_path.open("rb") as fh:
        data = tomllib.load(fh)
    boundary = data["core_boundary"]
    allow = [str(prefix) for prefix in boundary["allow"]["imports"]]
    block = [str(prefix) for prefix in boundary.get("block", {}).get("imports", [])]
    return allow, block


def _iter_python_files(core_dir: Path) -> list[Path]:
    if not core_dir.is_dir():
        return []
    return sorted(p for p in core_dir.rglob("*.py") if "__pycache__" not in p.parts)


def _extract_imports(path: Path) -> list[str]:
    imports: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "thegent" or alias.name.startswith("thegent."):
                    imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or node.module is None:
                continue
            if node.module == "thegent" or node.module.startswith("thegent."):
                imports.append(node.module)
    return imports


def _is_allowed(import_path: str, allowed_prefixes: list[str]) -> bool:
    return any(
        import_path == prefix or import_path.startswith(f"{prefix}.")
        for prefix in allowed_prefixes
    )


def _is_blocked(import_path: str, blocked_prefixes: list[str]) -> bool:
    return any(
        import_path == prefix or import_path.startswith(f"{prefix}.")
        for prefix in blocked_prefixes
    )


def run_check(core_dir: Path, config_path: Path) -> tuple[bool, list[str]]:
    report = build_report(core_dir=core_dir, config_path=config_path)
    return report["ok"], report["violations"]


def build_report(core_dir: Path, config_path: Path) -> dict[str, object]:
    allowed_prefixes, blocked_prefixes = _load_policy(config_path)
    violations: list[str] = []
    file_count = 0
    import_count = 0

    for py_file in _iter_python_files(core_dir):
        file_count += 1
        for import_path in _extract_imports(py_file):
            import_count += 1
            try:
                rel_display = str(py_file.relative_to(ROOT))
            except ValueError:
                rel_display = str(py_file)
            if _is_blocked(import_path, blocked_prefixes) and not _is_allowed(
                import_path, allowed_prefixes
            ):
                violations.append(f"{rel_display}: blocked import '{import_path}'")
                continue
            if not _is_allowed(import_path, allowed_prefixes):
                violations.append(f"{rel_display}: disallowed import '{import_path}'")

    return {
        "ok": not violations,
        "violations": violations,
        "violation_count": len(violations),
        "allowed_prefixes": allowed_prefixes,
        "blocked_prefixes": blocked_prefixes,
        "file_count": file_count,
        "import_count": import_count,
    }


def build_violation_entries(report: dict[str, object]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for violation in list(report["violations"]):
        entries.append({"kind": "violation", "message": str(violation)})
    return entries


def build_json_payload(report: dict[str, object], mode: str) -> dict[str, object]:
    payload = dict(report)
    payload["mode"] = mode
    return payload


def build_summary_payload(report: dict[str, object], mode: str) -> dict[str, object]:
    blocked_count, disallowed_count = build_violation_kind_counts(report)
    violation_file_count = build_violation_file_count(report)
    clean_file_count = build_clean_file_count(
        report, violation_file_count=violation_file_count
    )
    return {
        "ok": bool(report["ok"]),
        "mode": mode,
        "violation_count": int(report["violation_count"]),
        "violation_file_count": violation_file_count,
        "clean_file_count": clean_file_count,
        "blocked_count": blocked_count,
        "disallowed_count": disallowed_count,
        "file_count": int(report["file_count"]),
        "import_count": int(report["import_count"]),
    }


def build_violation_kind_counts(report: dict[str, object]) -> tuple[int, int]:
    blocked_count = 0
    disallowed_count = 0
    for violation in list(report["violations"]):
        text = str(violation)
        if "blocked import" in text:
            blocked_count += 1
        elif "disallowed import" in text:
            disallowed_count += 1
    return blocked_count, disallowed_count


def build_violation_file_count(report: dict[str, object]) -> int:
    files: set[str] = set()
    for violation in list(report["violations"]):
        text = str(violation)
        file_part, separator, _ = text.partition(": ")
        if separator:
            files.add(file_part)
    return len(files)


def build_clean_file_count(
    report: dict[str, object], *, violation_file_count: int | None = None
) -> int:
    file_count = int(report["file_count"])
    counted_violation_files = violation_file_count
    if counted_violation_files is None:
        counted_violation_files = build_violation_file_count(report)
    return max(0, file_count - counted_violation_files)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--core-dir",
        type=Path,
        default=CORE_DIR,
        help="Core package directory to scan.",
    )
    parser.add_argument(
        "--config", type=Path, default=CONFIG_PATH, help="Boundary config TOML path."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on violations (CI mode). Default mode is advisory and exits zero.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "summary-json", "violations-jsonl"],
        default="text",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    report = build_report(core_dir=args.core_dir, config_path=args.config)
    bool(report["ok"])
    violations = list(report["violations"])
    mode = "strict" if args.strict else "advisory"

    if args.format == "json":
        print(json.dumps(build_json_payload(report, mode), indent=2, sort_keys=True))
    elif args.format == "summary-json":
        print(json.dumps(build_summary_payload(report, mode), sort_keys=True))
    elif args.format == "violations-jsonl":
        for entry in build_violation_entries(report):
            print(json.dumps(entry, sort_keys=True))
    elif violations:
        print(f"thegent-core boundary check found violations ({mode} mode):")
        for violation in violations:
            print(f"- {violation}")
    else:
        print("thegent-core boundary check passed.")

    if violations and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
