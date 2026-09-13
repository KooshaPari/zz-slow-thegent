#!/usr/bin/env python3
"""Run fix agents for failed quality steps.

Spawns fix agents per checker in topological order (respects deps).
Writes status to .quality/fix-agents.json.
Requires config/quality-fix-dag.yaml.
"""

from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import orjson as json

ROOT = Path.cwd()
LOG_DIR = ROOT / ".quality" / "logs"
FIX_AGENTS_JSON = ROOT / ".quality" / "fix-agents.json"
FIX_DAG_CONFIG = ROOT / "config" / "quality-fix-dag.yaml"

# Add shared scripts to path for quality_fix_planner import
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))


def load_fix_dag() -> dict:
    """Load fix job config from YAML."""
    import yaml

    if not FIX_DAG_CONFIG.exists():
        return {}
    data = yaml.safe_load(FIX_DAG_CONFIG.read_text())
    return data.get("fix_jobs", {})


def _topological_tiers(steps: dict[str, dict]) -> list[list[str]]:
    """Return steps in tiers (each tier can run in parallel)."""
    in_degree = dict.fromkeys(steps, 0)
    for name, cfg in steps.items():
        for dep in cfg.get("deps", []):
            if dep in steps:
                in_degree[name] += 1

    tiers: list[list[str]] = []
    remaining = set(steps)

    while remaining:
        ready = [s for s in remaining if in_degree[s] == 0]
        if not ready:
            tiers.append(list(remaining))  # cycles: run last
            break
        tiers.append(ready)
        for s in ready:
            remaining.discard(s)
            for name, cfg in steps.items():
                if name in remaining and s in cfg.get("deps", []):
                    in_degree[name] -= 1

    return tiers


def run_fix_agents() -> int:
    """Run fix agents for failed steps in topological order."""
    from quality_fix_planner import get_fix_jobs

    jobs = get_fix_jobs()
    if not jobs:
        return 0

    fix_config = load_fix_dag()
    # Build subgraph: only jobs that have fix config
    job_names = {step_name for step_name, _ in jobs}
    subgraph = {
        name: cfg
        for name, cfg in fix_config.items()
        if name in job_names and cfg.get("command")
    }
    if not subgraph:
        return 0

    # Run in topological order (parallel within each tier)
    tiers = _topological_tiers(subgraph)
    agents: list[dict] = []

    def _run_one(step_name: str) -> dict:
        cfg = subgraph.get(step_name, {})
        cmd = cfg.get("command", "")
        if not cmd:
            return {"name": step_name, "status": "skipped", "pid": None}
        try:
            proc = subprocess.run(
                cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=300
            )
            return {
                "name": step_name,
                "status": "passed" if proc.returncode == 0 else "failed",
                "pid": proc.pid,
            }
        except Exception as e:
            return {"name": step_name, "status": f"error: {e}", "pid": None}

    for tier in tiers:
        with ThreadPoolExecutor(max_workers=len(tier)) as ex:
            futures = [ex.submit(_run_one, name) for name in tier]
            for fut in as_completed(futures):
                agents.append(fut.result())

    FIX_AGENTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    FIX_AGENTS_JSON.write_text(json.dumps({"agents": agents}, indent=2).decode())

    return 0 if all(a.get("status") == "passed" for a in agents) else 1


def main() -> int:
    return run_fix_agents()


if __name__ == "__main__":
    sys.exit(main())
