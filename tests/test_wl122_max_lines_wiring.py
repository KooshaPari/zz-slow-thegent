"""WL-122 wiring assertion: canonical max-lines gate is referenced consistently."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_wl122_max_lines_gate_wiring_is_canonical() -> None:
    taskfile = yaml.safe_load((ROOT / "Taskfile.yml").read_text(encoding="utf-8"))
    pre_commit = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    qa_guide = (ROOT / "docs/guides/QUALITY_ASSURANCE.md").read_text(encoding="utf-8")

    max_lines_cmd = (
        "MAX_LINES=${MAX_LINES:-2500} WARN_LINES=${WARN_LINES:-2000} MAX_LINES_SCOPE=${MAX_LINES_SCOPE:-changed} "
        "MAX_LINES_EXCLUDE_PREFIXES=${MAX_LINES_EXCLUDE_PREFIXES:-.git,node_modules,dist,build,target,.venv,__pycache__,docs/.vitepress/dist,docs-dist,.shadow-,crates/thegent-hooks/src/main.rs,hooks/hook-dispatcher/src/main.rs,hooks/governance-gates.sh,src/thegent/integrations/workstream_autosync.py,src/thegent/execution.py} sh scripts/max-lines-gate.sh"
    )
    task_cmds = taskfile["tasks"]["quality:max-lines"]["cmds"]
    assert max_lines_cmd in task_cmds
    assert {"task": "quality:max-lines"} in taskfile["tasks"]["quality"]["cmds"]

    local_hooks = next(repo for repo in pre_commit["repos"] if repo["repo"] == "local")["hooks"]
    hook = next(h for h in local_hooks if h["id"] == "max-lines-gate")
    assert hook["entry"] == "task quality:max-lines"
    assert "pre-commit" in hook["stages"]
    assert "pre-push" in hook["stages"]
    assert hook["stages"] == ["pre-commit", "pre-push"]
    assert "task quality:max-lines" in qa_guide


def test_ci_quality_job_uses_minimal_harness_contract_gate_wiring() -> None:
    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = ci["jobs"]["quality"]["steps"]

    assert any(step.get("uses") == "arduino/setup-task@v2" for step in steps)
    step_names = [step["name"] for step in steps]
    assert len(step_names) == len(set(step_names))
    assert "Assert canonical max-lines CI path (WL-122)" in step_names
    assert "Check extension package metadata sanity (WL-117)" in step_names
    assert "Run max-lines gate via canonical task path (WL-122)" in step_names

    run_step = next(step for step in steps if "mandatory quality gates" in step["name"].lower())
    run_script = run_step["run"]

    assert run_script.count("task quality:sitback-contracts") == 1
    assert run_script.count("task quality:harness-model-contracts") == 1
    assert "sitback_rc=$?" in run_script
    assert "harness_rc=$?" in run_script
    assert "set +e" in run_script
    assert "set -e" in run_script
    assert run_script.index("set +e") < run_script.index("task quality:sitback-contracts")
    assert run_script.index("task quality:harness-model-contracts") < run_script.index("set -e")
    assert 'if [ "$sitback_rc" -ne 0 ] || [ "$harness_rc" -ne 0 ]' in run_script
    assert "exit 1" in run_script

    assert "Run strict core-boundary check (WL-121)" not in set(step_names)
