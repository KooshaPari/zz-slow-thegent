#!/usr/bin/env python3
"""Validate agent-fork lane report files against the shared contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_PHASES = {"analysis", "execution", "verification", "handoff"}
ALLOWED_FINDING_TYPES = {
    "discovery",
    "decision",
    "claim",
    "risk",
    "patch",
    "test",
    "question",
}
ALLOWED_SEVERITY = {"low", "med", "high", "critical"}
ALLOWED_STATUS = {"pass", "fail", "skip"}

REQUIRED_TOP_FIELDS = {
    "lane_id",
    "plan_id",
    "agent_context_version",
    "phase",
    "owner",
    "objective",
    "scope",
    "findings",
    "proposed_actions",
    "conflicts",
    "next_actions",
    "validation",
    "generated_at",
}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _iter_report_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)
    return files


def _ensure(cond: bool, message: str, errors: list[str], path: Path, field: str = "") -> None:
    if not cond:
        prefix = f"{path}:{field + ': ' if field else ''}"
        errors.append(prefix + message)


def _validate_string(value: Any, min_len: int, path: Path, field: str, errors: list[str]) -> bool:
    if not isinstance(value, str):
        errors.append(f"{path}:{field} must be a string")
        return False
    if len(value.strip()) < min_len:
        errors.append(f"{path}:{field} must be at least {min_len} chars")
        return False
    return True


def _validate_list(value: Any, min_len: int, path: Path, field: str, errors: list[str]) -> list[Any] | None:
    if not isinstance(value, list):
        errors.append(f"{path}:{field} must be a list")
        return None
    if len(value) < min_len:
        errors.append(f"{path}:{field} must include at least {min_len} items")
    return value


def _validate_findings(findings: Any, path: Path, errors: list[str]) -> None:
    if findings is None:
        return
    findings_list = _validate_list(findings, 1, path, "findings", errors)
    if findings_list is None:
        return

    for idx, item in enumerate(findings_list):
        prefix = f"findings[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{path}:{prefix} must be an object")
            continue
        required = {"file", "type", "summary", "severity", "evidence", "confidence"}
        for key in required:
            _ensure(key in item, f"missing required key {key}", errors, path, prefix)

        if "file" in item:
            _validate_string(item["file"], 1, path, f"{prefix}.file", errors)

        if item.get("type") not in ALLOWED_FINDING_TYPES:
            errors.append(f"{path}:{prefix}.type invalid ({item.get('type')})")

        if not _validate_string(item.get("summary", ""), 10, path, f"{prefix}.summary", errors):
            continue

        if item.get("severity") not in ALLOWED_SEVERITY:
            errors.append(f"{path}:{prefix}.severity invalid ({item.get('severity')})")

        evidence = _validate_list(item.get("evidence"), 1, path, f"{prefix}.evidence", errors)
        if evidence is None:
            continue
        for ev_idx, ev in enumerate(evidence):
            if not isinstance(ev, str) or not ev.strip():
                errors.append(f"{path}:{prefix}.evidence[{ev_idx}] must be a non-empty string")

        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            errors.append(f"{path}:{prefix}.confidence must be number between 0 and 1")


def _validate_conflicts(conflicts: Any, path: Path, errors: list[str]) -> None:
    if conflicts is None:
        return
    conflict_list = _validate_list(conflicts, 0, path, "conflicts", errors)
    if conflict_list is None:
        return
    for idx, item in enumerate(conflict_list):
        prefix = f"conflicts[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{path}:{prefix} must be an object")
            continue
        required = {"path", "type", "description", "severity", "recommended_owner"}
        for key in required:
            _ensure(key in item, f"missing required key {key}", errors, path, prefix)
        for field in required:
            _validate_string(item.get(field, ""), 1, path, f"{prefix}.{field}", errors)
        if item.get("severity") not in ALLOWED_SEVERITY:
            errors.append(f"{path}:{prefix}.severity invalid ({item.get('severity')})")


def _validate_validation_block(block: Any, path: Path, errors: list[str]) -> None:
    if not isinstance(block, dict):
        errors.append(f"{path}:validation must be an object")
        return

    for field in ("commands", "results"):
        _ensure(field in block, f"missing required key {field}", errors, path, "validation")

    commands = _validate_list(block.get("commands"), 1, path, "validation.commands", errors)
    if commands is None:
        return
    for idx, cmd in enumerate(commands):
        _validate_string(cmd, 1, path, f"validation.commands[{idx}]", errors)

    results = _validate_list(block.get("results"), 1, path, "validation.results", errors)
    if results is None:
        return
    for idx, item in enumerate(results):
        prefix = f"validation.results[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{path}:{prefix} must be an object")
            continue
        for key in ("command", "status", "notes"):
            _ensure(key in item, f"missing required key {key}", errors, path, prefix)
        _validate_string(item.get("command", ""), 1, path, f"{prefix}.command", errors)
        _validate_string(item.get("notes", ""), 1, path, f"{prefix}.notes", errors)
        if item.get("status") not in ALLOWED_STATUS:
            errors.append(f"{path}:{prefix}.status invalid ({item.get('status')})")


def _validate_report(payload: dict[str, Any], path: Path, errors: list[str]) -> None:
    for key in REQUIRED_TOP_FIELDS:
        _ensure(key in payload, f"missing required key {key}", errors, path)

    _validate_string(payload.get("lane_id", ""), 3, path, "lane_id", errors)
    _validate_string(payload.get("plan_id", ""), 3, path, "plan_id", errors)
    _validate_string(
        payload.get("agent_context_version", ""),
        1,
        path,
        "agent_context_version",
        errors,
    )

    if payload.get("phase") not in ALLOWED_PHASES:
        errors.append(f"{path}:phase must be one of {sorted(ALLOWED_PHASES)}")

    _validate_string(payload.get("owner", ""), 1, path, "owner", errors)
    _validate_string(payload.get("objective", ""), 5, path, "objective", errors)

    scope = _validate_list(payload.get("scope"), 1, path, "scope", errors)
    if scope is not None:
        for idx, item in enumerate(scope):
            _validate_string(item, 1, path, f"scope[{idx}]", errors)

    _validate_findings(payload.get("findings"), path, errors)
    _validate_list(payload.get("proposed_actions"), 0, path, "proposed_actions", errors)
    _validate_conflicts(payload.get("conflicts"), path, errors)
    _validate_list(payload.get("next_actions"), 0, path, "next_actions", errors)
    _validate_validation_block(payload.get("validation"), path, errors)

    if not _validate_string(payload.get("generated_at", ""), 1, path, "generated_at", errors):
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate agent fork lane report JSON files.")
    parser.add_argument("paths", nargs="+", help="Lane report files or directories")
    args = parser.parse_args()

    errors: list[str] = []
    for path in _iter_report_files(args.paths):
        if not path.exists():
            errors.append(f"Missing file: {path}")
            continue

        try:
            payload = _load_json(path)
        except Exception as exc:  # pragma: no cover - IO/parse path
            errors.append(f"{path}: invalid JSON - {exc}")
            continue

        if not isinstance(payload, dict):
            errors.append(f"{path}: report must be a JSON object")
            continue

        _validate_report(payload, path, errors)

    if errors:
        for _issue in errors:
            pass
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
