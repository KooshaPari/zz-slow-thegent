"""Shell-level regression tests for governance policy gate script."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOCS = [
    "docs/governance/WORKTREE_AND_DELEGATION_INDEX.md",
    "docs/governance/WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md",
    "docs/governance/DELEGATION_ARCHITECTURE_LN.md",
    "docs/governance/TASK_CLASSIFIER_SCHEMA.yaml",
    "docs/governance/DOMAIN_PLAYBOOKS.md",
    "docs/governance/GOVERNANCE_ROADMAP_DAG.md",
    "docs/governance/MCP_A2A_CONTROL_PLANE_BOUNDARY.md",
    "docs/governance/ROLLOUT_PHASES_CHECKLIST.md",
]

DOC_CONTENTS = {
    "docs/governance/UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md": (
        "# docs/governance/UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md\n"
        "thegent worktree refresh\n"
        "thegent worktree migrate-legacy\n"
        "thegent_worktree\n"
    ),
    "docs/governance/WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md": (
        "# docs/governance/WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md\n"
        "Long-lived canary or package-tracking worktrees must be refreshed through the structured governance surface "
        "(`thegent worktree refresh` or `./scripts/worktree_governance.sh refresh`) rather than ad hoc local branch edits.\n"
    ),
    "docs/governance/GOVERNANCE_SUMMARY.md": (
        "# docs/governance/GOVERNANCE_SUMMARY.md\n"
        "Long-lived canary and high-extreme package branches must follow the canonical structured refresh policy in "
        "`UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md` before merge; the CI workflow enforces that policy via "
        "`task quality:governance:canary-refresh` and the local pre-push contract uses "
        "`task quality:pre-push:strict-governance`.\n"
        "legacy worktrees are reported separately through `task quality:governance:legacy-remediation-report`\n"
    ),
}


def _write_governance_fixture(repo_root: Path) -> None:
    (repo_root / "docs/governance").mkdir(parents=True, exist_ok=True)
    for doc in REQUIRED_DOCS:
        (repo_root / doc).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / doc).write_text(f"# {doc}\n", encoding="utf-8")
    for doc, content in DOC_CONTENTS.items():
        (repo_root / doc).parent.mkdir(parents=True, exist_ok=True)
        (repo_root / doc).write_text(content, encoding="utf-8")

    (repo_root / "AGENTS.md").write_text(
        "Reference: docs/governance/WORKTREE_AND_DELEGATION_INDEX.md\n",
        encoding="utf-8",
    )

    (repo_root / ".thegent-primary-main").write_text(
        "# thegent primary checkout policy\n"
        "Keep this repository checkout on main.\n"
        "Use dedicated worktrees for branch development.\n",
        encoding="utf-8",
    )
    (repo_root / "Taskfile.yml").write_text(
        "version: '3'\n"
        "tasks:\n"
        "  quality:governance:canary-refresh:\n"
        "    cmds:\n"
        "      - ./scripts/check_canary_refresh_governance.sh\n"
        "  quality:governance:worktree-inventory:\n"
        "    cmds:\n"
        "      - |\n"
        "        if ! uv run python scripts/worktree_governance_inventory.py --repo-root . --output-dir docs/governance; then\n"
        '          echo "[WARN] worktree inventory contains nonconformant entries; inspect docs/governance/worktree-governance-inventory.md"\n'
        "        fi\n"
        "  quality:governance:worktree-inventory:strict:\n"
        "    cmds:\n"
        "      - uv run python scripts/worktree_governance_inventory.py --repo-root . --output-dir docs/governance\n"
        "  quality:governance:legacy-remediation-report:\n"
        "    cmds:\n"
        "      - uv run python scripts/worktree_legacy_remediation_report.py --repo-root . --output-dir docs/governance\n"
        "  quality:pre-push:strict-governance:\n"
        "    cmds:\n"
        "      - task quality:governance:canary-refresh\n",
        encoding="utf-8",
    )


def _init_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "policy-repo"
    scripts_root = repo_root / "scripts"
    scripts_root.mkdir(parents=True)
    (repo_root / "docs" / "governance").mkdir(parents=True)

    shutil.copy2(
        REPO_ROOT / "scripts" / "governance_policy_check.sh",
        scripts_root / "governance_policy_check.sh",
    )
    shutil.copy2(
        REPO_ROOT / "scripts" / "worktree_legacy_remediation_report.py",
        scripts_root / "worktree_legacy_remediation_report.py",
    )
    shutil.copy2(
        REPO_ROOT / "scripts" / "worktree_governance.sh",
        scripts_root / "worktree_governance.sh",
    )
    shutil.copy2(REPO_ROOT / "scripts" / "bootstrap.sh", scripts_root / "bootstrap.sh")
    (scripts_root / "governance_policy_check.sh").chmod(0o755)
    (scripts_root / "worktree_legacy_remediation_report.py").chmod(0o755)
    (scripts_root / "worktree_governance.sh").chmod(0o755)
    (scripts_root / "bootstrap.sh").chmod(0o755)

    _write_governance_fixture(repo_root)

    subprocess.run(
        ["git", "init", "-q", "-b", "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return repo_root


def _run_policy_check(
    repo_root: Path, *, branch: str | None = None
) -> subprocess.CompletedProcess[str]:
    if branch is not None:
        subprocess.run(
            ["git", "checkout", "-q", "-b", branch],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

    return subprocess.run(
        [str(repo_root / "scripts/governance_policy_check.sh")],
        cwd=repo_root,
        env={
            **os.environ,
            "THGENT_GOV_METRICS_FILE": str(repo_root / "var/metrics.jsonl"),
        },
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.unit
def test_governance_policy_check_passes_on_clean_main(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    proc = _run_policy_check(repo_root)
    assert proc.returncode == 0, proc.stderr
    assert "[OK] governance policy checks passed" in proc.stdout


@pytest.mark.unit
def test_governance_policy_check_fails_when_not_on_main(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    proc = _run_policy_check(repo_root, branch="feature/alt")
    assert proc.returncode != 0
    assert "Governance precondition: primary checkout must be on main" in proc.stderr


@pytest.mark.unit
def test_governance_policy_check_fails_when_marker_missing(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    (repo_root / ".thegent-primary-main").unlink()
    proc = _run_policy_check(repo_root)
    assert proc.returncode != 0
    assert "Governance precondition: missing" in proc.stderr
