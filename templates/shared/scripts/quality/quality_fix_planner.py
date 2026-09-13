#!/usr/bin/env python3
"""Plan fix jobs from quality run results.

Reads .quality/last-run.json and returns list of (step_name, log_path) for failed steps.
"""

from __future__ import annotations

from pathlib import Path

import orjson as json

ROOT = Path.cwd()
LOG_DIR = ROOT / ".quality" / "logs"
LAST_RUN_JSON = ROOT / ".quality" / "last-run.json"


def get_fix_jobs() -> list[tuple[str, Path]]:
    """Return list of (step_name, log_path) for failed steps that have fix jobs."""
    if not LAST_RUN_JSON.exists():
        return []

    try:
        data = json.loads(LAST_RUN_JSON.read_text())
        failed = data.get("failed_steps", [])
    except (json.JSONDecodeError, OSError):
        return []

    jobs = []
    for step in failed:
        log_path = LOG_DIR / f"{step}.log"
        if log_path.exists() and log_path.stat().st_size > 0:
            jobs.append((step, log_path))
    return jobs
