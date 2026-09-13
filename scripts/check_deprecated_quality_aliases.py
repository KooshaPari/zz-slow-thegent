#!/usr/bin/env python3
"""Audit deprecated quality alias definitions for WL-123 migration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAPPING_PATH = ROOT / "config" / "deprecated_quality_aliases.json"

TASK_KEY_RE = re.compile(r"^\s{2}([A-Za-z0-9:-]+):\s*$")


def load_alias_mapping(mapping_path: Path) -> dict[str, object]:
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Alias mapping file must be a JSON object.")

    required = {"deprecated_aliases", "replacement_suggestions", "canonical_commands"}
    missing = sorted(required.difference(payload))
    if missing:
        raise ValueError(
            f"Alias mapping file missing required keys: {', '.join(missing)}"
        )

    deprecated_aliases = payload["deprecated_aliases"]
    replacement_suggestions = payload["replacement_suggestions"]
    canonical_commands = payload["canonical_commands"]
    if not isinstance(deprecated_aliases, list) or not all(
        isinstance(x, str) for x in deprecated_aliases
    ):
        raise ValueError("'deprecated_aliases' must be a list[str].")
    if not isinstance(replacement_suggestions, dict) or not all(
        isinstance(k, str) and isinstance(v, str)
        for k, v in replacement_suggestions.items()
    ):
        raise ValueError("'replacement_suggestions' must be a dict[str, str].")
    if not isinstance(canonical_commands, list) or not all(
        isinstance(x, str) for x in canonical_commands
    ):
        raise ValueError("'canonical_commands' must be a list[str].")

    return {
        "deprecated_aliases": deprecated_aliases,
        "replacement_suggestions": replacement_suggestions,
        "canonical_commands": canonical_commands,
    }


def extract_task_names(taskfile_text: str) -> set[str]:
    names: set[str] = set()
    for line in taskfile_text.splitlines():
        match = TASK_KEY_RE.match(line)
        if match:
            names.add(match.group(1))
    return names


def extract_task_names_with_includes(
    taskfile_path: Path, taskfile_text: str
) -> set[str]:
    names = extract_task_names(taskfile_text)
    taskfile_payload = yaml.safe_load(taskfile_text) or {}
    includes = taskfile_payload.get("includes", {})
    if not isinstance(includes, dict):
        return names

    for include_name, include_config in includes.items():
        if not isinstance(include_name, str) or not isinstance(include_config, dict):
            continue
        include_taskfile = include_config.get("taskfile")
        if not isinstance(include_taskfile, str):
            continue

        include_path = (taskfile_path.parent / include_taskfile).resolve()
        if not include_path.exists():
            continue

        include_payload = yaml.safe_load(include_path.read_text(encoding="utf-8")) or {}
        include_tasks = include_payload.get("tasks", {})
        if not isinstance(include_tasks, dict):
            continue

        for task_name in include_tasks:
            if isinstance(task_name, str):
                names.add(f"{include_name}:{task_name}")

    return names


def build_report(
    task_names: set[str],
    *,
    deprecated_aliases: list[str],
    replacement_suggestions_map: dict[str, str],
    canonical_commands: list[str],
) -> dict[str, object]:
    deprecated_present = sorted(
        alias for alias in deprecated_aliases if alias in task_names
    )
    canonical_missing = sorted(
        name for name in canonical_commands if name not in task_names
    )
    replacement_suggestions = {
        alias: replacement_suggestions_map[alias] for alias in deprecated_present
    }
    return {
        "deprecated_present": deprecated_present,
        "deprecated_count": len(deprecated_present),
        "replacement_suggestions": replacement_suggestions,
        "canonical_missing": canonical_missing,
        "canonical_missing_count": len(canonical_missing),
    }


def build_migration_entries(report: dict[str, object]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    replacement_suggestions = dict(report["replacement_suggestions"])
    canonical_missing = list(report["canonical_missing"])

    for legacy_alias in sorted(replacement_suggestions):
        entries.append(
            {
                "kind": "replacement",
                "deprecated_alias": legacy_alias,
                "canonical_command": str(replacement_suggestions[legacy_alias]),
            }
        )
    for command_name in canonical_missing:
        entries.append(
            {
                "kind": "canonical_missing",
                "canonical_command": str(command_name),
            }
        )
    return entries


def build_summary_payload(report: dict[str, object]) -> dict[str, object]:
    total_findings = build_total_findings_count(report)
    replacement_count = build_replacement_count(report)
    unmapped_deprecated_count = build_unmapped_deprecated_count(report)
    return {
        "ok": total_findings == 0,
        "deprecated_count": report["deprecated_count"],
        "replacement_count": replacement_count,
        "unmapped_deprecated_count": unmapped_deprecated_count,
        "canonical_missing_count": report["canonical_missing_count"],
        "total_findings": total_findings,
    }


def build_migration_payload(report: dict[str, object]) -> dict[str, object]:
    return {
        "replacement_suggestions": dict(report["replacement_suggestions"]),
        "canonical_missing": list(report["canonical_missing"]),
    }


def build_total_findings_count(report: dict[str, object]) -> int:
    return int(report["deprecated_count"]) + int(report["canonical_missing_count"])


def build_replacement_count(report: dict[str, object]) -> int:
    return len(dict(report["replacement_suggestions"]))


def build_unmapped_deprecated_count(report: dict[str, object]) -> int:
    deprecated_present = {str(alias) for alias in list(report["deprecated_present"])}
    mapped_aliases = {str(alias) for alias in dict(report["replacement_suggestions"])}
    return len(deprecated_present.difference(mapped_aliases))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--taskfile",
        type=Path,
        default=Path("Taskfile.yml"),
        help="Taskfile path to audit.",
    )
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=DEFAULT_MAPPING_PATH,
        help="JSON file containing deprecated alias migration mapping.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if deprecated aliases are still defined or canonical commands are missing.",
    )
    parser.add_argument(
        "--format",
        choices=[
            "text",
            "json",
            "migration",
            "migration-md",
            "migration-json",
            "migration-jsonl",
            "summary-json",
        ],
        default="text",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    text = args.taskfile.read_text(encoding="utf-8")
    task_names = extract_task_names_with_includes(args.taskfile, text)
    mapping = load_alias_mapping(args.mapping_file)
    report = build_report(
        task_names,
        deprecated_aliases=list(mapping["deprecated_aliases"]),
        replacement_suggestions_map=dict(mapping["replacement_suggestions"]),
        canonical_commands=list(mapping["canonical_commands"]),
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.format == "migration":
        print("WL-123 alias migration suggestions")
        if report["replacement_suggestions"]:
            for legacy, canonical in report["replacement_suggestions"].items():
                print(f"- {legacy} -> {canonical}")
        else:
            print("- No deprecated aliases found.")
        if report["canonical_missing"]:
            print("- Missing canonical commands:")
            for cmd in report["canonical_missing"]:
                print(f"  - {cmd}")
    elif args.format == "migration-md":
        print("| Deprecated alias | Canonical replacement |")
        print("|---|---|")
        if report["replacement_suggestions"]:
            for legacy, canonical in report["replacement_suggestions"].items():
                print(f"| `{legacy}` | `{canonical}` |")
        else:
            print("| _None_ | _None_ |")

        print()
        print("| Missing canonical commands |")
        print("|---|")
        if report["canonical_missing"]:
            for cmd in report["canonical_missing"]:
                print(f"| `{cmd}` |")
        else:
            print("| _None_ |")
    elif args.format == "migration-json":
        print(json.dumps(build_migration_payload(report), indent=2, sort_keys=True))
    elif args.format == "migration-jsonl":
        for entry in build_migration_entries(report):
            print(json.dumps(entry, sort_keys=True))
    elif args.format == "summary-json":
        print(json.dumps(build_summary_payload(report), sort_keys=True))
    else:
        print("WL-123 alias audit")
        print(f"- deprecated aliases present: {report['deprecated_count']}")
        print(f"- canonical commands missing: {report['canonical_missing_count']}")
        if report["deprecated_present"]:
            print("- deprecated list: " + ", ".join(report["deprecated_present"]))
            print("- suggested replacements:")
            for legacy, canonical in report["replacement_suggestions"].items():
                print(f"  - {legacy} -> {canonical}")
        if report["canonical_missing"]:
            print("- canonical missing: " + ", ".join(report["canonical_missing"]))

    if args.strict and (
        report["deprecated_count"] or report["canonical_missing_count"]
    ):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
