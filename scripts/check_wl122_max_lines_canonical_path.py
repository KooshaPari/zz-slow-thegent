#!/usr/bin/env python3
"""WL-122 CI check: enforce canonical max-lines task invocation path."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CANONICAL_TASK = "task quality:max-lines"
TASKFILE_TASK_KEY = "quality:max-lines:"
TASKFILE_GATE_CMD = "sh scripts/max-lines-gate.sh"
FORBIDDEN_CI_DIRECT_CALL = "scripts/max-lines-gate.sh"
CANONICAL_CHECK_CMD = "check_wl122_max_lines_canonical_path.py --strict"
WL117_METADATA_CHECK_CMD = "check_extension_package_metadata.py --strict"
PRECOMMIT_MAX_LINES_HOOK = "- id: max-lines-gate"
PRECOMMIT_CANONICAL_ENTRY_PATTERN = re.compile(
    r"^\s*entry:\s*task quality:max-lines\s*$", re.MULTILINE
)
TASK_SETUP_ACTION = "arduino/setup-task@v2"


def build_report(
    *, ci_text: str, taskfile_text: str, precommit_text: str
) -> dict[str, object]:
    errors: list[str] = []

    if TASKFILE_TASK_KEY not in taskfile_text:
        errors.append("Taskfile.yml is missing task `quality:max-lines`.")
    if TASKFILE_GATE_CMD not in taskfile_text:
        errors.append("Taskfile.yml is missing canonical max-lines gate command.")

    canonical_count = ci_text.count(CANONICAL_TASK)
    wl122_checker_count = ci_text.count(CANONICAL_CHECK_CMD)
    wl117_checker_count = ci_text.count(WL117_METADATA_CHECK_CMD)
    if canonical_count == 0:
        errors.append("CI workflow does not invoke `task quality:max-lines`.")
    elif canonical_count > 1:
        errors.append(
            f"CI workflow must invoke `{CANONICAL_TASK}` exactly once (found {canonical_count})."
        )
    if canonical_count >= 1 and TASK_SETUP_ACTION not in ci_text:
        errors.append(
            "CI workflow must install Task runner via `arduino/setup-task@v2` before max-lines gate."
        )
    if FORBIDDEN_CI_DIRECT_CALL in ci_text:
        errors.append("CI workflow must not call scripts/max-lines-gate.sh directly.")
    if wl122_checker_count == 0:
        errors.append(
            "CI workflow must run WL-122 canonical-path checker in strict mode."
        )
    elif wl122_checker_count > 1:
        errors.append(
            "CI workflow must run WL-122 canonical-path checker exactly once."
        )
    if wl117_checker_count == 0:
        errors.append(
            "CI workflow must run WL-117 extension metadata checker in strict mode."
        )
    elif wl117_checker_count > 1:
        errors.append(
            "CI workflow must run WL-117 extension metadata checker exactly once."
        )
    if wl122_checker_count == 1 and wl117_checker_count == 1:
        if ci_text.index(CANONICAL_CHECK_CMD) > ci_text.index(WL117_METADATA_CHECK_CMD):
            errors.append(
                "CI workflow must run WL-122 checker before WL-117 metadata checker."
            )
    if wl122_checker_count == 1 and canonical_count == 1:
        if ci_text.index(CANONICAL_CHECK_CMD) > ci_text.index(CANONICAL_TASK):
            errors.append(
                "CI workflow must run WL-122 checker before WL-122 max-lines gate."
            )
    if wl117_checker_count == 1 and canonical_count == 1:
        if ci_text.index(WL117_METADATA_CHECK_CMD) > ci_text.index(CANONICAL_TASK):
            errors.append(
                "CI workflow must run WL-117 metadata checker before WL-122 max-lines gate."
            )

    if PRECOMMIT_MAX_LINES_HOOK not in precommit_text:
        errors.append(".pre-commit-config.yaml is missing `max-lines-gate` hook.")
    elif precommit_text.count(PRECOMMIT_MAX_LINES_HOOK) > 1:
        errors.append(
            ".pre-commit-config.yaml must declare `max-lines-gate` hook exactly once."
        )
    canonical_entry_count = len(
        PRECOMMIT_CANONICAL_ENTRY_PATTERN.findall(precommit_text)
    )
    if canonical_entry_count == 0:
        errors.append(
            ".pre-commit-config.yaml max-lines hook must invoke `task quality:max-lines`."
        )
    elif canonical_entry_count > 1:
        errors.append(
            ".pre-commit-config.yaml must define canonical `entry: task quality:max-lines` exactly once."
        )
    if FORBIDDEN_CI_DIRECT_CALL in precommit_text:
        errors.append(
            ".pre-commit-config.yaml must not call scripts/max-lines-gate.sh directly."
        )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": [],
        "canonical_invocations": canonical_count,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ci",
        type=Path,
        default=Path(".github/workflows/ci.yml"),
        help="Path to CI workflow YAML.",
    )
    parser.add_argument(
        "--taskfile", type=Path, default=Path("Taskfile.yml"), help="Path to Taskfile."
    )
    parser.add_argument(
        "--precommit",
        type=Path,
        default=Path(".pre-commit-config.yaml"),
        help="Path to pre-commit config.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--strict", action="store_true", help="Exit non-zero when contract checks fail."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    report = build_report(
        ci_text=args.ci.read_text(encoding="utf-8"),
        taskfile_text=args.taskfile.read_text(encoding="utf-8"),
        precommit_text=args.precommit.read_text(encoding="utf-8"),
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("WL-122 canonical max-lines CI path check")
        print(f"- ok: {report['ok']}")
        print(f"- canonical invocations: {report['canonical_invocations']}")
        for warning in report["warnings"]:
            print(f"- warning: {warning}")
        for error in report["errors"]:
            print(f"- error: {error}")

    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
