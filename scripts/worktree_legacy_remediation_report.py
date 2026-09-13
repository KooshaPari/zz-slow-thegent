#!/usr/bin/env python
"""Emit a remediation report for legacy worktrees outside the canonical root."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LegacyWorktreeEntry:
    path: str
    branch: str
    dirty_count: int
    ahead: int | None
    behind: int | None
    prunable: bool
    issues: list[str]
    suggested_action: str


def _parse_git_worktree(path: Path) -> list[tuple[str, str, bool]]:
    try:
        text = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=path, text=True).splitlines()
    except Exception as exc:  # pragma: no cover - surfaced by task validation
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


def _git_status_count(path: str) -> int:
    output = subprocess.check_output(["git", "-C", path, "status", "--porcelain"], text=True)
    return len([line for line in output.splitlines() if line.strip()])


def _git_ahead_behind(path: str, branch: str, base_branch: str) -> tuple[int | None, int | None]:
    if branch == "(detached)":
        return None, None

    try:
        ahead = int(
            subprocess.check_output(
                ["git", "-C", path, "rev-list", "--count", f"{base_branch}..{branch}"],
                text=True,
            ).strip()
        )
        behind = int(
            subprocess.check_output(
                ["git", "-C", path, "rev-list", "--count", f"{branch}..{base_branch}"],
                text=True,
            ).strip()
        )
    except Exception:
        return None, None
    return ahead, behind


def _suggest_action(branch: str, dirty_count: int, prunable: bool) -> str:
    if prunable and dirty_count == 0:
        return "prune"
    if branch == "(detached)":
        return "inspect"
    return "migrate"


def generate_report(*, repo_root: Path | None = None, base_branch: str = "main") -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    root = repo_root.resolve()
    required_root = (root / ".worktrees").resolve()
    entries: list[LegacyWorktreeEntry] = []

    for path, branch, prunable in _parse_git_worktree(root):
        resolved = Path(path).resolve()
        if resolved == root:
            continue
        if resolved.is_relative_to(required_root):
            continue

        dirty_count = _git_status_count(path)
        ahead, behind = _git_ahead_behind(path, branch, base_branch)
        issues = ["path outside repository root"]
        if branch == "(detached)":
            issues.append("detached branch")
        if dirty_count > 0:
            issues.append(f"{dirty_count} dirty path(s)")
        if ahead is not None and behind is not None:
            issues.append(f"ahead {ahead}; behind {behind}")

        entries.append(
            LegacyWorktreeEntry(
                path=path,
                branch=branch,
                dirty_count=dirty_count,
                ahead=ahead,
                behind=behind,
                prunable=bool(prunable),
                issues=issues,
                suggested_action=_suggest_action(branch, dirty_count, bool(prunable)),
            )
        )

    payload = {
        "schema_version": "governance.worktree.legacy_remediation.v1",
        "timestamp": datetime.now(UTC).isoformat(),
        "repo_root": str(root),
        "required_root": str(required_root),
        "base_branch": base_branch,
        "total": len(entries),
        "dirty": sum(1 for entry in entries if entry.dirty_count > 0),
        "prunable": sum(1 for entry in entries if entry.prunable),
        "entries": [asdict(entry) for entry in entries],
    }
    return payload


def _write(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "worktree-legacy-remediation.json"
    md_path = out_dir / "worktree-legacy-remediation.md"
    json_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    md_lines = [
        "# Legacy Worktree Remediation Report",
        "",
        f"- total legacy worktrees: `{payload['total']}`",
        f"- dirty legacy worktrees: `{payload['dirty']}`",
        f"- prunable legacy worktrees: `{payload['prunable']}`",
        f"- canonical base branch: `{payload['base_branch']}`",
        "",
    ]
    for entry in payload["entries"]:
        ahead = entry["ahead"] if entry["ahead"] is not None else "-"
        behind = entry["behind"] if entry["behind"] is not None else "-"
        issues = "; ".join(entry["issues"]) or "-"
        md_lines.append(
            f"- {entry['suggested_action'].upper()} {entry['path']} ({entry['branch']}) :: "
            f"dirty={entry['dirty_count']} ahead={ahead} behind={behind} :: {issues}"
        )

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Emit a legacy worktree remediation report")
    parser.add_argument("--output-dir", default="docs/governance")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--schema", default="governance.worktree.legacy_remediation.v1")
    args = parser.parse_args()

    payload = generate_report(repo_root=Path(args.repo_root), base_branch=args.base_branch)
    payload["schema_version"] = args.schema
    json_out, md_out = _write(payload, Path(args.output_dir))
    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
