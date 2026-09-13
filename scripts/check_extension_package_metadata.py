#!/usr/bin/env python3
"""WL-117 extension package metadata sanity checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
README_NPM_RUN_RE = re.compile(r"npm run ([a-zA-Z0-9:_-]+)")
MANDATORY_RUN_STEPS = ("lint", "test")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _load_package_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: package.json root must be an object")
    return data


def _extract_quickstart_commands(readme_text: str) -> list[str]:
    if "## Run Steps" not in readme_text:
        return []
    return README_NPM_RUN_RE.findall(readme_text)


def validate_extension_package(extension_dir: Path) -> list[str]:
    errors: list[str] = []
    package_path = extension_dir / "package.json"
    if not package_path.exists():
        return [f"{extension_dir}: missing package.json"]

    try:
        package = _load_package_json(package_path)
    except Exception as exc:
        return [f"{package_path}: failed to parse JSON ({exc})"]
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}

    for key in ("name", "displayName", "description"):
        if not _is_non_empty_string(package.get(key)):
            errors.append(f"{package_path}: `{key}` must be a non-empty string")

    version = package.get("version")
    if not _is_non_empty_string(version) or not SEMVER_RE.match(str(version)):
        errors.append(f"{package_path}: `version` must be plain semver (x.y.z)")

    engines = package.get("engines")
    if not isinstance(engines, dict) or not _is_non_empty_string(engines.get("vscode")):
        errors.append(f"{package_path}: `engines.vscode` must be set")

    main_entry = package.get("main")
    if not _is_non_empty_string(main_entry):
        errors.append(f"{package_path}: `main` must be a non-empty string path")
    else:
        main_path = extension_dir / str(main_entry)
        if not main_path.exists():
            errors.append(f"{package_path}: `main` points to missing file: {main_entry}")

    activation_events = package.get("activationEvents")
    if not isinstance(activation_events, list) or not activation_events:
        errors.append(f"{package_path}: `activationEvents` must be a non-empty list")
        normalized_events: set[str] = set()
    else:
        normalized_events = {str(item).strip() for item in activation_events if _is_non_empty_string(item)}
        if len(normalized_events) != len(activation_events):
            errors.append(f"{package_path}: `activationEvents` entries must be unique non-empty strings")

    commands = (
        ((package.get("contributes") or {}).get("commands")) if isinstance(package.get("contributes"), dict) else None
    )
    if not isinstance(commands, list) or not commands:
        errors.append(f"{package_path}: `contributes.commands` must be a non-empty list")
    else:
        seen_command_ids: set[str] = set()
        for index, command in enumerate(commands):
            if not isinstance(command, dict):
                errors.append(f"{package_path}: command[{index}] must be an object")
                continue
            command_id = command.get("command")
            title = command.get("title")
            if not _is_non_empty_string(command_id):
                errors.append(f"{package_path}: command[{index}].command must be non-empty")
                continue
            if not _is_non_empty_string(title):
                errors.append(f"{package_path}: command[{index}].title must be non-empty")
            if command_id in seen_command_ids:
                errors.append(f"{package_path}: duplicate contributes.commands command id `{command_id}`")
            else:
                seen_command_ids.add(command_id)
            activation_name = f"onCommand:{command_id}"
            if normalized_events and activation_name not in normalized_events:
                errors.append(
                    f"{package_path}: missing activation event `{activation_name}` for command `{command_id}`"
                )

    readme_path = extension_dir / "README.md"
    if not readme_path.exists():
        errors.append(f"{extension_dir}: missing README.md")
    else:
        readme_text = readme_path.read_text(encoding="utf-8")
        run_commands = _extract_quickstart_commands(readme_text)
        if not run_commands:
            errors.append(f"{readme_path}: must include `## Run Steps` with at least one `npm run <script>` command")
        if len(run_commands) != len(set(run_commands)):
            errors.append(f"{readme_path}: Run Steps must not repeat the same `npm run <script>` command")
        run_set = set(run_commands)
        for mandatory_step in MANDATORY_RUN_STEPS:
            if mandatory_step not in run_set:
                errors.append(f"{readme_path}: Run Steps must include `npm run {mandatory_step}`")
        if "lint" in run_set and "test" in run_set and run_commands.index("lint") > run_commands.index("test"):
            errors.append(f"{readme_path}: Run Steps must list `npm run lint` before `npm run test`")
        for command in run_commands:
            if command not in scripts:
                errors.append(f"{readme_path}: references `npm run {command}` but package.json lacks scripts.{command}")

    return errors


def build_report(extensions_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    checked_extensions: list[str] = []
    extension_dirs = (
        sorted(path for path in extensions_root.iterdir() if path.is_dir()) if extensions_root.exists() else []
    )
    if not extension_dirs:
        errors.append(f"No extension directories found in {extensions_root}")
        return {"ok": False, "checked_extensions": checked_extensions, "errors": errors}

    for extension_dir in extension_dirs:
        checked_extensions.append(extension_dir.name)
        errors.extend(validate_extension_package(extension_dir))

    return {
        "ok": len(errors) == 0,
        "checked_extensions": checked_extensions,
        "errors": errors,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extensions-root",
        type=Path,
        default=Path("extensions"),
        help="Root directory containing extension packages.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if metadata checks fail.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    report = build_report(args.extensions_root)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("WL-117 extension package metadata check")
        print(f"- ok: {report['ok']}")
        print(
            f"- checked_extensions: {', '.join(report['checked_extensions']) if report['checked_extensions'] else 'none'}"
        )
        for error in report["errors"]:
            print(f"- error: {error}")

    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
