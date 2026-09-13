"""Tests for scripts/bootstrap_sync_workflow_project.py.

These tests assert idempotent behavior when resources already exist and when
only missing resources must be created.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "bootstrap_sync_workflow_project.py"


@pytest.fixture
def module() -> object:
    spec = importlib.util.spec_from_file_location("bootstrap_sync_workflow_project", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["bootstrap_sync_workflow_project"] = module
    spec.loader.exec_module(module)
    return module


def test_bootstrap_main_idempotent_skips_existing_resources(module: object) -> None:
    labels = ["sync-system", "agent-workflow"]
    issue_urls = [
        "https://github.com/example/repo/issues/1",
        "https://github.com/example/repo/issues/2",
        "https://github.com/example/repo/issues/3",
        "https://github.com/example/repo/issues/4",
        "https://github.com/example/repo/issues/5",
        "https://github.com/example/repo/issues/6",
        "https://github.com/example/repo/issues/7",
        "https://github.com/example/repo/issues/8",
        "https://github.com/example/repo/issues/9",
        "https://github.com/example/repo/issues/10",
    ]
    issue_specs = module.ISSUES  # type: ignore[attr-defined]
    calls: list[list[str]] = []

    def fake_run_json(cmd: list[str], dry_run: bool) -> list[dict[str, object]]:
        if cmd[:3] == ["gh", "label", "list"]:
            return [{"name": name} for name in labels]
        if cmd[:3] == ["gh", "project", "list"]:
            return [{"title": "thegent Sync System Deep Integration", "number": 5}]
        if cmd[:3] == ["gh", "issue", "list"]:
            return [{"title": spec.title, "url": issue_urls[idx]} for idx, spec in enumerate(issue_specs)]
        if cmd[:3] == ["gh", "project", "item-list"]:
            return [{"content": {"url": url}} for url in issue_urls]
        return []

    def fake_run(cmd: list[str], dry_run: bool) -> str:
        calls.append(cmd)
        return ""

    module._run_json = fake_run_json  # type: ignore[assignment]
    module._run = fake_run  # type: ignore[assignment]

    summary = module.bootstrap_sync_workflow_project(
        owner="example",
        repo="example/repo",
        project_title="thegent Sync System Deep Integration",
        dry_run=False,
    )

    assert summary == {
        "prepared_count": 10,
        "project_number": 5,
        "issue_urls": [
            "https://github.com/example/repo/issues/1",
            "https://github.com/example/repo/issues/2",
            "https://github.com/example/repo/issues/3",
            "https://github.com/example/repo/issues/4",
            "https://github.com/example/repo/issues/5",
            "https://github.com/example/repo/issues/6",
            "https://github.com/example/repo/issues/7",
            "https://github.com/example/repo/issues/8",
            "https://github.com/example/repo/issues/9",
            "https://github.com/example/repo/issues/10",
        ],
    }
    assert not any(cmd[:3] == ["gh", "issue", "create"] for cmd in calls)
    assert not any(cmd[:3] == ["gh", "project", "item-add"] for cmd in calls)


def test_bootstrap_main_dry_run_executes_printing_commands(module: object) -> None:
    calls: list[list[str]] = []
    titles = [spec.title for spec in module.ISSUES]  # type: ignore[attr-defined]
    dry_run_issue_rows = [
        {"title": title, "url": f"https://github.com/example/repo/issues/{idx + 1}"} for idx, title in enumerate(titles)
    ]

    def fake_run_json(cmd: list[str], dry_run: bool) -> list[dict[str, object]]:
        if cmd[:3] == ["gh", "label", "list"]:
            return []
        if cmd[:3] == ["gh", "project", "list"]:
            return []
        if cmd[:3] == ["gh", "issue", "list"]:
            return dry_run_issue_rows
        if cmd[:3] == ["gh", "project", "item-list"]:
            return []
        return []

    def fake_run(cmd: list[str], dry_run: bool) -> str:
        calls.append(cmd)
        if cmd[:3] == ["gh", "project", "create"]:
            return '{"number": 42, "title": "thegent Sync System Deep Integration"}'
        return ""

    module._run_json = fake_run_json  # type: ignore[assignment]
    module._run = fake_run  # type: ignore[assignment]

    summary = module.bootstrap_sync_workflow_project(
        owner="example",
        repo="example/repo",
        project_title="thegent Sync System Deep Integration",
        dry_run=True,
    )

    assert summary["prepared_count"] == 10
    assert summary["project_number"] == 0
    assert len(calls) >= 3
    assert calls and calls[0][0] == "gh"


# noqa: PT018
