"""E2E contract checks for CLIProxy provider smoke lifecycle wiring."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKFILE = ROOT / "Taskfile.yml"


def test_taskfile_has_provider_smoke_task() -> None:
    text = TASKFILE.read_text(encoding="utf-8")
    assert "quality:providers:cheapest-smoke:" in text
    assert "uv run python scripts/cliproxy_provider_smoke.py" in text
    assert "quality:providers:required-gate:" in text
    assert "--strict-required-providers" in text


def test_harness_contract_chains_include_provider_smoke() -> None:
    text = TASKFILE.read_text(encoding="utf-8")
    for task_name in (
        "quality:harness-contracts:smoke",
        "quality:harness-contracts:quick",
        "quality:harness-contracts",
    ):
        pattern = rf"(?ms)^  {re.escape(task_name)}:\n(.*?)(?=^  [^ \n].*:\n|\Z)"
        match = re.search(pattern, text)
        assert match is not None, f"Task '{task_name}' must exist in Taskfile.yml"
        block = match.group(1)
        assert "task: quality:providers:cheapest-smoke" in block


def test_strict_harness_contract_chain_uses_required_provider_gate() -> None:
    text = TASKFILE.read_text(encoding="utf-8")
    pattern = r"(?ms)^  quality:harness-contracts:strict:\n(.*?)(?=^  [^ \n].*:\n|\Z)"
    match = re.search(pattern, text)
    assert match is not None, "Task 'quality:harness-contracts:strict' must exist in Taskfile.yml"
    block = match.group(1)
    assert "task: quality:providers:required-gate" in block
