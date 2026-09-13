#!/usr/bin/env python3
"""DAG-based quality runner with configurable fail mode.

Uses config/quality-dag.yaml to run steps in dependency order. Parallel within each
tier. In soft mode, if a step fails, dependents are skipped but other branches
continue. In hard mode, execution stops after the first failing tier and remaining
steps are marked blocked.

Writes .quality/logs/<step>.log, .quality/logs/<step>.exit,
.quality/last-run.json, .quality/summary.md.

Run from project root. Uses cwd as ROOT. Requires PyYAML.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import orjson as json

# Resolved at runtime (see _resolve_paths)
ROOT: Path = Path.cwd()
LOG_DIR: Path = Path(".quality") / "logs"
LAST_RUN_JSON: Path = Path(".quality") / "last-run.json"
PROGRESS_JSON: Path = Path(".quality") / "progress.json"
DAG_CONFIG: Path = Path("config") / "quality-dag.yaml"
SUMMARY_MD: Path = Path(".quality") / "summary.md"
LANGUAGE_PROFILE_CONFIG: Path = Path("config") / "quality-language-profiles.yaml"


def _resolve_paths(root: Path | None = None, config: Path | None = None) -> None:
    """Set ROOT and derived paths from args/env."""
    global ROOT, LOG_DIR, LAST_RUN_JSON, PROGRESS_JSON, DAG_CONFIG, SUMMARY_MD
    r = os.environ.get("QUALITY_ROOT")
    if r:
        ROOT = Path(r).resolve()
    elif root:
        ROOT = Path(root).resolve()
    else:
        ROOT = Path.cwd().resolve()
    cfg = os.environ.get("QUALITY_CONFIG") or (str(config) if config else None)
    DAG_CONFIG = Path(cfg).resolve() if cfg else ROOT / "config" / "quality-dag.yaml"
    LOG_DIR = ROOT / ".quality" / "logs"
    LAST_RUN_JSON = ROOT / ".quality" / "last-run.json"
    PROGRESS_JSON = ROOT / ".quality" / "progress.json"
    SUMMARY_MD = ROOT / ".quality" / "summary.md"


def _detect_py(root: Path) -> bool:
    return (
        (root / "pyproject.toml").exists()
        or (root / "setup.py").exists()
        or (root / "backend" / "pyproject.toml").exists()
    )


def _py_steps(root: Path) -> dict[str, dict]:
    py_prefix = "backend:" if (root / "backend" / "pyproject.toml").exists() else "py:"
    return {
        "py-lint": {"deps": [], "command": f"task {py_prefix}lint", "display": "Python lint"},
        "py-type": {"deps": [], "command": f"task {py_prefix}typecheck", "display": "Python type"},
        "py-test": {"deps": ["py-lint", "py-type"], "command": f"task {py_prefix}test", "display": "Python test"},
    }


def _detect_ts(root: Path) -> bool:
    package_json = root / "package.json"
    if not package_json.exists():
        return False
    indicators = ["tsconfig.json", "extensions/vscode/package.json"]
    if any((root / p).exists() for p in indicators):
        return True
    extension_dir = root / "extensions" / "vscode"
    return bool(extension_dir.is_dir() and any(extension_dir.glob("*.ts")))


def _ts_steps(_: Path) -> dict[str, dict]:
    return {
        "ts-lint": {"deps": [], "command": "task typescript:lint", "display": "Frontend lint"},
        "ts-type": {"deps": [], "command": "task typescript:typecheck", "display": "Frontend type"},
        "ts-build": {"deps": ["ts-lint", "ts-type"], "command": "task typescript:build", "display": "Frontend build"},
        "ts-test": {"deps": ["ts-build"], "command": "task typescript:test", "display": "Frontend test"},
    }


def _detect_go(root: Path) -> bool:
    return (root / "go.mod").exists() or (root / "go.work").exists()


def _go_steps(_: Path) -> dict[str, dict]:
    return {
        "go-lint": {"deps": [], "command": "task go:lint", "display": "Go lint"},
        "go-build": {"deps": ["go-lint"], "command": "task go:build", "display": "Go build"},
        "go-test": {"deps": ["go-build"], "command": "task go:test", "display": "Go test"},
    }


def _detect_bash(root: Path) -> bool:
    return (root / "scripts").is_dir() or (root / "hooks").is_dir() or (root / ".github").is_dir()


def _bash_steps(_: Path) -> dict[str, dict]:
    return {"bash-lint": {"deps": [], "command": "task bash:lint", "display": "Bash lint"}}


def _detect_rust(root: Path) -> bool:
    return (root / "Cargo.toml").exists() or (root / "crates" / "Cargo.toml").exists()


def _rust_steps(_: Path) -> dict[str, dict]:
    return {
        "rust-fmt-check": {"deps": [], "command": "task rust:fmt:check", "display": "Rust format check"},
        "rust-check": {"deps": ["rust-fmt-check"], "command": "task rust:check", "display": "Rust check"},
        "rust-clippy": {"deps": ["rust-check"], "command": "task rust:lint", "display": "Rust clippy"},
        "rust-test": {"deps": ["rust-clippy"], "command": "task rust:test", "display": "Rust test"},
        "rust-security": {"deps": ["rust-test"], "command": "task rust:security", "display": "Rust security"},
    }


def _detect_zig(root: Path) -> bool:
    return (root / "build.zig").exists() or any(root.glob("*.zig"))


def _zig_steps(_: Path) -> dict[str, dict]:
    return {
        "zig-fmt-check": {"deps": [], "command": "task zig:fmt:check", "display": "Zig format check"},
        "zig-build": {"deps": ["zig-fmt-check"], "command": "task zig:build", "display": "Zig build"},
        "zig-test": {"deps": ["zig-build"], "command": "task zig:test", "display": "Zig test"},
    }


def _detect_mojo(root: Path) -> bool:
    return bool(list(root.glob("*.mojo")) or list((root / "src").glob("**/*.mojo")))


def _mojo_steps(_: Path) -> dict[str, dict]:
    return {
        "mojo-contracts": {
            "deps": [],
            "command": "task quality:runtime-contracts:mojo-kernel",
            "display": "Mojo runtime contract checks",
        }
    }


DEFAULT_LANGUAGE_PROFILES = {
    "py": {"detect": _detect_py, "steps_fn": _py_steps},
    "ts": {"detect": _detect_ts, "steps_fn": _ts_steps},
    "go": {"detect": _detect_go, "steps_fn": _go_steps},
    "bash": {"detect": _detect_bash, "steps_fn": _bash_steps},
    "rust": {"detect": _detect_rust, "steps_fn": _rust_steps},
    "zig": {"detect": _detect_zig, "steps_fn": _zig_steps},
    "mojo": {"detect": _detect_mojo, "steps_fn": _mojo_steps},
}


def _normalize_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return []


def _build_custom_detector(spec: dict):
    globs = _normalize_list(spec.get("match_globs") or spec.get("match") or spec.get("patterns"))
    files = _normalize_list(spec.get("match_files") or spec.get("files"))
    dirs = _normalize_list(spec.get("match_dirs") or spec.get("dirs"))
    if not (globs or files or dirs):
        return None

    def detect(root: Path) -> bool:
        for path in files:
            if (root / path).exists():
                return True
        for path in dirs:
            if (root / path).is_dir():
                return True
        return any(any(root.glob(pattern)) for pattern in globs)

    return detect


def _load_custom_language_profiles(root: Path) -> dict[str, dict]:
    if not LANGUAGE_PROFILE_CONFIG.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}

    try:
        data = yaml.safe_load(LANGUAGE_PROFILE_CONFIG.read_text())
    except Exception as exc:
        print(f"Ignoring {LANGUAGE_PROFILE_CONFIG}: {exc}", file=sys.stderr)
        return {}

    languages = data.get("languages") or {}
    custom_profiles: dict[str, dict] = {}
    for name, spec in languages.items():
        if not isinstance(spec, dict):
            continue
        detect = _build_custom_detector(spec)
        steps_cfg = spec.get("steps")
        if not detect or not isinstance(steps_cfg, dict):
            continue

        def steps_fn(_: Path, steps=steps_cfg) -> dict:
            return {step: dict(cfg) for step, cfg in steps.items()}

        custom_profiles[name] = {"detect": detect, "steps_fn": steps_fn}
    return custom_profiles


def _detect_stacks(root: Path) -> dict[str, dict]:
    profiles = dict(DEFAULT_LANGUAGE_PROFILES)
    profiles.update(_load_custom_language_profiles(root))

    matched: dict[str, dict] = {}
    for name, profile in profiles.items():
        detect = profile.get("detect")
        if not callable(detect):
            continue
        try:
            if detect(root):
                matched[name] = profile
        except Exception as exc:
            print(f"Error detecting '{name}': {exc}", file=sys.stderr)
    return matched


def _generate_dag_config(root: Path) -> dict:
    """Generate quality-dag steps from detected project structure."""
    stacks = _detect_stacks(root)
    steps: dict[str, dict] = {}
    for profile in stacks.values():
        steps.update(profile["steps_fn"](root))

    if not steps:
        steps["lint"] = {"deps": [], "command": "task lint", "display": "Lint"}
        steps["test"] = {"deps": ["lint"], "command": "task test", "display": "Test"}

    return steps


def _ensure_dag_config(root: Path, config_path: Path) -> None:
    """Create config/quality-dag.yaml if missing (auto-generated from project structure)."""
    import yaml

    if config_path.exists():
        return
    # Only auto-generate when using default path
    default_config = root / "config" / "quality-dag.yaml"
    if config_path != default_config:
        print(f"DAG config not found: {config_path}", file=sys.stderr)
        print(f"Create it or run without --config to use default {default_config}", file=sys.stderr)
        print("Alternative: task quality:gate (full quality gate)", file=sys.stderr)
        raise SystemExit(1)
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)
    steps = _generate_dag_config(root)
    data = {"version": 1, "steps": steps}
    config_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True))
    print(f"Generated {config_path} from project structure", file=sys.stderr)


def _filter_steps(
    steps: dict[str, dict],
    only: str | None = None,
    skip: str | None = None,
) -> dict[str, dict]:
    """Filter steps by --only or --skip."""
    if not only and not skip:
        return steps

    names = set(steps)

    if only:
        want = {s.strip() for s in only.split(",") if s.strip()}
        invalid = want - names
        if invalid:
            print(f"Unknown steps in --only: {', '.join(sorted(invalid))}", file=sys.stderr)
            raise SystemExit(1)
        # Include want + all transitive deps
        included = set(want)
        changed = True
        while changed:
            changed = False
            for name in list(included):
                for dep in steps[name].get("deps", []):
                    if dep in names and dep not in included:
                        included.add(dep)
                        changed = True
        steps = {k: v for k, v in steps.items() if k in included}

    if skip:
        skip_set = {s.strip() for s in skip.split(",") if s.strip()}
        invalid = skip_set - names
        if invalid:
            print(f"Unknown steps in --skip: {', '.join(sorted(invalid))}", file=sys.stderr)
            raise SystemExit(1)
        # Exclude skip_set + all steps that depend on them (transitive)
        excluded = set(skip_set)
        changed = True
        while changed:
            changed = False
            for name, cfg in steps.items():
                if name in excluded:
                    continue
                if any(d in excluded for d in cfg.get("deps", [])):
                    excluded.add(name)
                    changed = True
        steps = {k: v for k, v in steps.items() if k not in excluded}

    return steps


def load_dag() -> dict:
    """Load step DAG from YAML. Auto-generates config if missing."""
    import yaml

    _ensure_dag_config(ROOT, DAG_CONFIG)
    try:
        data = yaml.safe_load(DAG_CONFIG.read_text())
    except yaml.YAMLError as e:
        print(f"Invalid YAML in {DAG_CONFIG}: {e}", file=sys.stderr)
        print("Fix the config or delete it to auto-generate from project structure.", file=sys.stderr)
        raise SystemExit(1) from e
    if not data or not isinstance(data.get("steps"), dict):
        print(f"Invalid config: {DAG_CONFIG} must have a 'steps' dict.", file=sys.stderr)
        raise SystemExit(1)
    steps = data.get("steps", {})
    _validate_dag(steps)
    return steps


def _validate_dag(steps: dict[str, dict]) -> None:
    """Validate DAG: undefined deps, cycles, missing command."""
    if not steps:
        return
    # Check undefined deps and missing command
    for name, cfg in steps.items():
        cmd = cfg.get("command")
        if not cmd or not str(cmd).strip():
            print(f"Step '{name}' has no command.", file=sys.stderr)
            raise SystemExit(1)
        for dep in cfg.get("deps", []):
            if dep not in steps:
                print(f"Step '{name}' depends on undefined step '{dep}'.", file=sys.stderr)
                raise SystemExit(1)
    # Check cycles: Kahn's algorithm leaves remaining iff cycle exists
    in_degree = dict.fromkeys(steps, 0)
    for name, cfg in steps.items():
        for dep in cfg.get("deps", []):
            if dep in steps:
                in_degree[name] += 1
    remaining = set(steps)
    while True:
        ready = [s for s in remaining if in_degree[s] == 0]
        if not ready:
            break
        for s in ready:
            remaining.discard(s)
            for name, cfg in steps.items():
                if name in remaining and s in cfg.get("deps", []):
                    in_degree[name] -= 1
    if remaining:
        print(f"Cycle detected in DAG: {', '.join(sorted(remaining))}", file=sys.stderr)
        raise SystemExit(1)


def topological_tiers(steps: dict[str, dict]) -> list[list[str]]:
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
            break
        tiers.append(ready)
        for s in ready:
            remaining.discard(s)
            for name, cfg in steps.items():
                if name in remaining and s in cfg.get("deps", []):
                    in_degree[name] -= 1

    if remaining:
        tiers.append(list(remaining))  # cycles: run last
    return tiers


def _log(verbose: bool, msg: str) -> None:
    """Print timestamped message when verbose."""
    if verbose:
        ts = time.strftime("%H:%M:%S", time.localtime())
        print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def run_step(
    step_name: str,
    command: str,
    cwd: Path,
    verbose: bool = False,
) -> tuple[str, int, float]:
    """Run one step, return (step_name, exit_code, duration_sec)."""
    log_path = LOG_DIR / f"{step_name}.log"
    exit_path = LOG_DIR / f"{step_name}.exit"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    _log(verbose, f"Starting {step_name}")
    start = time.perf_counter()
    step_timeout = int(os.environ.get("QUALITY_STEP_TIMEOUT_SEC", "600"))
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=step_timeout,
        )
        out = proc.stdout + proc.stderr
        code = proc.returncode
    except subprocess.TimeoutExpired:
        out = f"timeout after {step_timeout}s"
        code = 124
    except Exception as e:
        out = str(e)
        code = 1

    duration = time.perf_counter() - start
    log_path.write_text(out, encoding="utf-8", errors="replace")
    exit_path.write_text(str(code))
    _log(verbose, f"Finished {step_name} (exit {code}, {duration:.1f}s)")

    return step_name, code, duration


def _write_progress(
    results: dict[str, int | str],
    running: list[str],
    durations: dict[str, float] | None = None,
) -> None:
    """Write progress.json for TUI consumption."""
    PROGRESS_JSON.parent.mkdir(parents=True, exist_ok=True)
    durations = durations or {}
    completed = {}
    for k, v in results.items():
        if isinstance(v, int):
            completed[k] = {"code": v, "duration": durations.get(k, 0)}
        elif v == "skipped":
            completed[k] = {"code": -1, "duration": 0}
    data = {
        "running": running,
        "completed": completed,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    PROGRESS_JSON.write_text(json.dumps(data, indent=2).decode())


def run_dag(
    steps: dict,
    results: dict[str, int | str],
    durations: dict[str, float],
    cwd: Path,
    fail_mode: str = "soft",
    progress: bool = False,
    verbose: bool = False,
) -> None:
    """Execute DAG with soft/hard fail behavior."""
    if fail_mode not in {"soft", "hard"}:
        raise ValueError(f"Invalid fail_mode '{fail_mode}', expected 'soft' or 'hard'")

    blocked_mode = False
    tiers = topological_tiers(steps)

    for tier in tiers:
        if blocked_mode:
            for name in tier:
                results[name] = "blocked"
            if progress:
                _write_progress(results, [], durations)
            continue

        # Filter: only run if all deps passed (0)
        to_run = []
        for name in tier:
            deps = steps[name].get("deps", [])
            if all(results.get(d) == 0 for d in deps):
                to_run.append(name)
            else:
                results[name] = "skipped"

        if progress:
            _write_progress(results, to_run, durations)

        if not to_run:
            continue

        max_workers_cfg = int(os.environ.get("QUALITY_MAX_WORKERS", "4"))
        max_workers = max(1, min(len(to_run), max_workers_cfg))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {
                ex.submit(run_step, n, steps[n]["command"], cwd, verbose): n
                for n in to_run
            }
            for fut in as_completed(futures):
                name, code, duration = fut.result()
                results[name] = code
                durations[name] = duration
                if progress:
                    still_running = [s for s in to_run if s not in results]
                    _write_progress(results, still_running, durations)

        if progress:
            _write_progress(results, [], durations)

        if fail_mode == "hard" and any(results.get(n) not in (0, "skipped") for n in to_run):
            blocked_mode = True


def _write_junit(
    results: dict[str, int | str],
    durations: dict[str, float],
    steps: dict,
    junit_path: Path,
) -> None:
    """Write JUnit XML report."""
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    total = len(results)
    failures = sum(1 for v in results.values() if v != 0 and v != "skipped")
    skipped = sum(1 for v in results.values() if v == "skipped")
    total_time = sum(durations.get(k, 0) for k in results)

    testsuite = ET.Element(
        "testsuite",
        name="quality",
        tests=str(total),
        failures=str(failures),
        skipped=str(skipped),
        errors="0",
        time=f"{total_time:.3f}",
    )

    for name, code in results.items():
        display = steps.get(name, {}).get("display", name)
        duration = durations.get(name, 0)
        testcase = ET.SubElement(
            testsuite,
            "testcase",
            name=display,
            classname="quality",
            time=f"{duration:.3f}",
        )
        if code != 0 and code != "skipped":
            log_path = LOG_DIR / f"{name}.log"
            msg = f"Exit {code}"
            detail = log_path.read_text(encoding="utf-8", errors="replace")[:2000] if log_path.exists() else msg
            failure = ET.SubElement(testcase, "failure", message=msg)
            failure.text = detail

    tree = ET.ElementTree(ET.Element("testsuites"))
    tree.getroot().append(testsuite)
    xml_str = minidom.parseString(ET.tostring(tree.getroot(), encoding="unicode")).toprettyxml(indent="  ")
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    junit_path.write_text(xml_str, encoding="utf-8")


def write_last_run(
    results: dict,
    failed: list[str],
    durations: dict[str, float] | None = None,
) -> None:
    """Write last-run.json for quality-report compatibility."""
    LAST_RUN_JSON.parent.mkdir(parents=True, exist_ok=True)
    durations = durations or {}
    status_codes = {
        "skipped": -1,
        "blocked": -2,
    }
    exit_codes = {k: (v if isinstance(v, int) else status_codes.get(str(v), -3)) for k, v in results.items()}
    step_details = {
        k: {"code": exit_codes[k], "duration": durations.get(k, 0)}
        for k in exit_codes
    }
    data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "steps": exit_codes,
        "step_details": step_details,
        "failed_steps": failed,
        "ok": len(failed) == 0,
    }
    LAST_RUN_JSON.write_text(json.dumps(data, indent=2).decode())


def _status_counts(results: dict[str, int | str]) -> tuple[int, int, int, int]:
    """Return (passed, failed, skipped, blocked)."""
    passed = sum(1 for v in results.values() if v == 0)
    failed = sum(1 for v in results.values() if isinstance(v, int) and v != 0)
    skipped = sum(1 for v in results.values() if v == "skipped")
    blocked = sum(1 for v in results.values() if v == "blocked")
    return passed, failed, skipped, blocked


def write_summary_report(
    steps: dict[str, dict],
    results: dict[str, int | str],
    durations: dict[str, float],
    fail_mode: str,
) -> None:
    """Write a markdown summary artifact for the latest run."""
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    passed, failed, skipped, blocked = _status_counts(results)
    total_time = sum(durations.get(k, 0) for k in results)

    lines = [
        "# Quality Run Summary",
        "",
        f"- Timestamp: {started_at}",
        f"- Fail mode: {fail_mode}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        f"- Skipped: {skipped}",
        f"- Blocked: {blocked}",
        f"- Total step runtime (sum): {total_time:.2f}s",
        "",
        "## Step Results",
        "",
        "| Step | Display | Status | Duration (s) |",
        "| --- | --- | --- | ---: |",
    ]

    for name in sorted(results):
        display = steps.get(name, {}).get("display", name)
        value = results[name]
        if value == "skipped":
            status = "skipped"
            duration = "0.00"
        elif value == "blocked":
            status = "blocked"
            duration = "0.00"
        else:
            code = int(value)
            status = "passed" if code == 0 else f"failed({code})"
            duration = f"{durations.get(name, 0):.2f}"
        lines.append(f"| {name} | {display} | {status} | {duration} |")

    lines.append("")
    lines.append("## Logs")
    lines.append("")
    lines.append("- Step logs: `.quality/logs/<step>.log`")
    lines.append("- Last run JSON: `.quality/last-run.json`")
    lines.append("")

    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """Run quality DAG."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DAG-based quality runner with soft/hard fail modes. Auto-generates config if missing."
    )
    parser.add_argument("--tui", action="store_true", help="Write progress.json for TUI")
    parser.add_argument("--dry-run", action="store_true", help="Print tiers and commands, do not run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Timestamped step logs to stderr")
    parser.add_argument("--only", type=str, metavar="STEPS", help="Comma-separated steps to run (and their deps)")
    parser.add_argument("--skip", type=str, metavar="STEPS", help="Comma-separated steps to skip")
    parser.add_argument("--root", type=Path, metavar="DIR", help="Project root (default: cwd)")
    parser.add_argument("--config", type=Path, metavar="FILE", help="Path to quality-dag.yaml")
    parser.add_argument("--ci", action="store_true", help="CI mode: compact one-line summary, no verbose output")
    parser.add_argument("--junit", type=Path, metavar="FILE", help="Write JUnit XML report to file")
    parser.add_argument(
        "--fail-mode",
        choices=["soft", "hard"],
        default="soft",
        help="Failure behavior: soft continues unrelated branches, hard stops after first failing tier",
    )
    args = parser.parse_args()

    _resolve_paths(root=args.root, config=args.config)

    steps = load_dag()
    steps = _filter_steps(steps, only=args.only, skip=args.skip)
    if not steps:
        print("No steps to run after filtering.", file=sys.stderr)
        return 0
    tiers = topological_tiers(steps)

    if args.dry_run:
        for i, tier in enumerate(tiers):
            print(f"Tier {i + 1}: {', '.join(tier)}")
            for name in tier:
                cmd = steps[name].get("command", "?")
                display = steps[name].get("display", name)
                print(f"  {display}: {cmd}")
        return 0

    results: dict[str, int | str] = {}
    durations: dict[str, float] = {}
    run_dag(
        steps,
        results,
        durations,
        ROOT,
        fail_mode=args.fail_mode,
        progress=args.tui,
        verbose=args.verbose,
    )

    failed = [k for k, v in results.items() if isinstance(v, int) and v != 0]
    write_last_run(results, failed, durations)
    write_summary_report(steps, results, durations, args.fail_mode)

    # JUnit XML output
    if args.junit:
        _write_junit(results, durations, steps, args.junit)

    # CI mode: compact one-line summary only
    if args.ci:
        passed = sum(1 for v in results.values() if v == 0)
        if failed:
            print(f"quality: FAIL ({passed} passed, {len(failed)} failed: {', '.join(failed)})", flush=True)
        else:
            print(f"quality: PASS ({passed} steps)", flush=True)
        return 0 if not failed else 1

    # Print failed logs for piping to agent (quality-a, quality-a-r-h)
    if failed and not args.ci:
        for step in failed:
            log_path = LOG_DIR / f"{step}.log"
            display = steps.get(step, {}).get("display", step)
            if log_path.exists():
                print(f"\n--- {display} ---\n", flush=True)
                print(log_path.read_text(encoding="utf-8", errors="replace"), flush=True)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
