#!/usr/bin/env python3
"""Generate WL-120/WL-136 LOC trend artifacts from git day-end snapshots."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import tomllib
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--boundary-config", type=Path, default=Path("config/thegent_core_boundary.toml"))
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--end-date", type=str, default=dt.datetime.now(dt.UTC).date().isoformat())
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    return parser.parse_args()


def _run_git(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _count_python_code_lines(text: str) -> int:
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def _module_prefixes_from_boundary_config(config_path: Path) -> list[str]:
    with config_path.open("rb") as fh:
        config = tomllib.load(fh)
    zones = config.get("core_boundary", {}).get("zones", {})
    prefixes = [str(value) for value in zones.values()]
    if not prefixes:
        raise RuntimeError(f"No core boundary zones configured in {config_path}")
    return prefixes


def _module_prefix_to_dir(prefix: str) -> str:
    if not prefix.startswith("thegent."):
        raise RuntimeError(f"Unsupported core boundary module prefix: {prefix}")
    suffix = prefix.removeprefix("thegent.").replace(".", "/")
    return f"src/thegent/{suffix}"


def _file_list_for_commit(repo_root: Path, commit: str, base_dir: str) -> list[str]:
    output = _run_git(repo_root, ["ls-tree", "-r", "--name-only", commit, "--", base_dir])
    return [line.strip() for line in output.splitlines() if line.strip().endswith(".py")]


def _compute_snapshot_metrics(repo_root: Path, commit: str, core_dirs: set[str]) -> tuple[int, int]:
    src_files = _file_list_for_commit(repo_root, commit, "src/thegent")
    total_loc = 0
    core_loc = 0
    for path in src_files:
        blob = _run_git(repo_root, ["show", f"{commit}:{path}"])
        lines = _count_python_code_lines(blob)
        total_loc += lines
        if any(path == core_dir or path.startswith(f"{core_dir}/") for core_dir in core_dirs):
            core_loc += lines
    return total_loc, core_loc


def _commit_for_date(repo_root: Path, day: dt.date) -> str:
    before = f"{day.isoformat()} 23:59:59"
    commit = _run_git(repo_root, ["rev-list", "-1", f"--before={before}", "HEAD"]).strip()
    if not commit:
        raise RuntimeError(f"No commit found on or before {day.isoformat()}")
    return commit


def _strict_three_day_decline(values: list[int]) -> bool:
    if len(values) < 3:
        return False
    a, b, c = values[-3], values[-2], values[-1]
    return a > b > c


def _validate_snapshot_dates(snapshots: list[dict[str, object]]) -> None:
    parsed_dates = [dt.date.fromisoformat(str(snapshot["date"])) for snapshot in snapshots]
    if len(parsed_dates) != len(set(parsed_dates)):
        raise RuntimeError("Snapshot dates must be unique.")
    if parsed_dates != sorted(parsed_dates):
        raise RuntimeError("Snapshot dates must be in ascending order.")


def _build_payload(*, generated_at: str, dates: list[dt.date], snapshots: list[dict[str, object]]) -> dict[str, object]:
    total_values = [int(snapshot["total_loc"]) for snapshot in snapshots]
    core_values = [int(snapshot["core_boundary_loc"]) for snapshot in snapshots]
    return {
        "generated_at": generated_at,
        "scope": {
            "wl120": "src/thegent total python LOC (git day-end snapshots)",
            "wl136": "core-boundary zones from config/thegent_core_boundary.toml (git day-end snapshots)",
        },
        "method": {
            "loc_definition": "non-blank, non-comment lines from .py files",
            "daily_sources": [f"git commit snapshot for {day.isoformat()}" for day in dates],
            "note": "Snapshots use git history only to avoid contamination from unrelated uncommitted worktree edits.",
        },
        "snapshots": snapshots,
        "trend": {
            "total_loc_values": total_values,
            "core_boundary_loc_values": core_values,
            "wl120_three_day_decline_met": _strict_three_day_decline(total_values),
            "wl136_core_decline_met": _strict_three_day_decline(core_values),
        },
    }


def _render_md(
    report_date: str, artifact_json_path: str, snapshots: list[dict[str, object]], trend: dict[str, object]
) -> str:
    lines = [
        f"# WL-120/WL-136 LOC Trend Evidence ({report_date})",
        "",
        f"- Artifact JSON: `{artifact_json_path}`",
        "- LOC definition: non-blank, non-comment Python lines.",
        "- Snapshot method: git day-end commits only (worktree excluded).",
        "",
        "| Date | Source | Total LOC (`src/thegent`) | Core-Boundary LOC (`core/queue/agents/config`) |",
        "|---|---|---:|---:|",
    ]
    for snapshot in snapshots:
        short_commit = str(snapshot["commit"])[:12]
        lines.append(
            f"| {snapshot['date']} | git:{short_commit} | {snapshot['total_loc']} | {snapshot['core_boundary_loc']} |"
        )

    lines.extend(
        [
            "",
            f"- WL-120 acceptance (3-day total LOC decline): **{'PASS' if trend['wl120_three_day_decline_met'] else 'FAIL'}**",
            f"- WL-136 exit criterion (3-day core LOC decline): **{'PASS' if trend['wl136_core_decline_met'] else 'FAIL'}**",
            "",
            "Observed deltas:",
            "- Total LOC: " + " -> ".join(str(v) for v in trend["total_loc_values"]),
            "- Core-boundary LOC: " + " -> ".join(str(v) for v in trend["core_boundary_loc_values"]),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    if args.days < 3:
        raise RuntimeError("--days must be >= 3 for WL-120/WL-136 trend checks")

    repo_root = args.repo_root.resolve()
    boundary_config = args.boundary_config if args.boundary_config.is_absolute() else repo_root / args.boundary_config
    report_end_date = dt.date.fromisoformat(args.end_date)

    module_prefixes = _module_prefixes_from_boundary_config(boundary_config)
    core_dirs = {_module_prefix_to_dir(prefix) for prefix in module_prefixes}

    dates = [report_end_date - dt.timedelta(days=offset) for offset in range(args.days - 1, -1, -1)]

    snapshots: list[dict[str, object]] = []
    for day in dates:
        commit = _commit_for_date(repo_root, day)
        total_loc, core_loc = _compute_snapshot_metrics(repo_root, commit, core_dirs)
        snapshots.append(
            {
                "date": day.isoformat(),
                "source": "git_commit",
                "commit": commit,
                "total_loc": total_loc,
                "core_boundary_loc": core_loc,
            }
        )

    _validate_snapshot_dates(snapshots)
    payload = _build_payload(
        generated_at=dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        dates=dates,
        snapshots=snapshots,
    )

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    md = _render_md(
        report_date=report_end_date.isoformat(),
        artifact_json_path=str(args.json_out).replace(str(repo_root) + "/", ""),
        snapshots=snapshots,
        trend=payload["trend"],
    )
    args.md_out.write_text(md, encoding="utf-8")

    print(f"Wrote JSON artifact: {args.json_out}")
    print(f"Wrote Markdown artifact: {args.md_out}")
    print("Total LOC trend:", " -> ".join(str(v) for v in payload["trend"]["total_loc_values"]))
    print("Core boundary trend:", " -> ".join(str(v) for v in payload["trend"]["core_boundary_loc_values"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
