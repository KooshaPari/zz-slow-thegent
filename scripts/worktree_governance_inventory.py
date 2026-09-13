#!/usr/bin/env python
"""Emit worktree inventory and conformance summary (W78-E01)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DEFAULT_PRIMARY_MARKER = ".thegent-primary-main"


@dataclass(frozen=True)
class WorktreeInventoryEntry:
    path: str
    branch: str
    mode: str
    required_root: str
    in_required_root: bool
    domain: str | None
    scale: str | None
    change_anchor: str | None
    state: str | None
    prunable: bool
    is_conformant: bool
    issues: list[str]


def _parse_git_worktree(path: Path) -> list[tuple[str, str, bool]]:
    try:
        text = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=path, text=True).splitlines()
    except Exception as exc:
        raise RuntimeError(f"git worktree list failed for {path}: {exc}") from exc

    entries: list[tuple[str, str, bool]] = []
    worktree_path: str | None = None
    branch = "(detached)"
    prunable = False

    for line in text:
        if line.startswith("worktree "):
            if worktree_path is not None:
                entries.append((worktree_path, branch, prunable))
            worktree_path = line.removeprefix("worktree ").strip()
            branch = "(detached)"
            prunable = False
            continue

        if line.startswith("branch ") and worktree_path:
            branch = line.removeprefix("branch ").removeprefix("refs/heads/").strip()
            continue

        if line.startswith("prunable ") and worktree_path:
            prunable = True
            continue

        if line.startswith("HEAD ") and worktree_path:
            continue

    if worktree_path is not None:
        entries.append((worktree_path, branch, prunable))
    return entries


def _conform(path: str, branch: str, root: Path, marker_path: Path) -> tuple[bool, list[str]]:
    resolved_path = Path(path).resolve()
    is_primary = resolved_path == root.resolve()
    issues: list[str] = []
    if is_primary:
        if not marker_path.exists():
            issues.append("primary marker missing")
    elif branch == "(detached)":
        issues.append("detached branch")
    try:
        resolved_path.relative_to(root.resolve())
    except ValueError:
        issues.append("path outside repository root")
    return not issues, issues


def _structured_lane_components(path: str, root: Path) -> tuple[str | None, str | None, str | None, str | None]:
    resolved_path = Path(path).resolve()
    try:
        relative = resolved_path.relative_to(root.resolve())
    except ValueError:
        return None, None, None, None

    parts = relative.parts
    if len(parts) < 5:
        return None, None, None, None
    if parts[0] != ".worktrees":
        return None, None, None, None
    if parts[-1] not in {"active", "review", "blocked", "integration", "done"}:
        return None, None, None, None
    return parts[1], parts[2], parts[3], parts[4]


def generate_inventory(*, repo_root: Path | None = None, marker: str = _DEFAULT_PRIMARY_MARKER) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    root = repo_root.resolve()
    required_root = (root / ".worktrees").resolve()
    entries = []

    marker_path = root / marker
    for path, branch, prunable in _parse_git_worktree(root):
        if "/.git/worktrees/" in path:
            continue
        is_ok, issues = _conform(path, branch, root, marker_path)
        domain, scale, change_anchor, state = _structured_lane_components(path, root)
        resolved_path = Path(path).resolve()
        in_required_root = resolved_path.is_relative_to(required_root)
        if in_required_root and resolved_path != root and domain is None:
            issues.append("legacy or malformed worktree inside structured root")
            is_ok = False
        mode = "lane" if in_required_root and domain is not None else "other"
        if resolved_path == root:
            mode = "primary"
        entries.append(
            WorktreeInventoryEntry(
                path=path,
                branch=branch,
                mode=mode,
                required_root=str(required_root),
                in_required_root=in_required_root,
                domain=domain,
                scale=scale,
                change_anchor=change_anchor,
                state=state,
                prunable=bool(prunable),
                is_conformant=is_ok,
                issues=issues,
            )
        )

    payload = {
        "schema_version": "governance.worktree.inventory.v1",
        "timestamp": datetime.now(UTC).isoformat(),
        "total": len(entries),
        "conformant": sum(1 for item in entries if item.is_conformant),
        "warn": sum(1 for item in entries if not item.is_conformant),
        "nonconformant": len(entries) - sum(1 for item in entries if item.is_conformant),
        "entries": [asdict(e) for e in entries],
    }
    return payload


def _write(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "worktree-governance-inventory.json"
    md_path = out_dir / "worktree-governance-inventory.md"
    json_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    md_lines = [
        "# Worktree Governance Inventory",
        "",
        f"- total: `{payload['total']}`",
        f"- conformant: `{payload['conformant']}`",
        f"- nonconformant: `{payload['nonconformant']}`",
    ]
    md_lines.append("")
    for entry in payload["entries"]:
        badge = "PASS" if entry["is_conformant"] else "WARN"
        issues = "; ".join(entry["issues"]) or "-"
        md_lines.append(f"- {badge} {entry['path']} ({entry['branch']}) :: {issues}")

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Emit worktree governance inventory artifact")
    parser.add_argument("--output-dir", default="docs/governance")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default="governance.worktree.inventory.v1")
    args = parser.parse_args()

    payload = generate_inventory(repo_root=Path(args.repo_root), marker=_DEFAULT_PRIMARY_MARKER)
    payload["schema_version"] = args.schema
    json_out, md_out = _write(payload, Path(args.output_dir))
    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    return 1 if payload["nonconformant"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
