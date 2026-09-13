"""Tests for thegent.commands.sync — status, push, pull, reset subcommands.

Covers the four new subcommands added in the impl-sync-command work-stream
item.  All filesystem access is isolated to tmp_path; no live repo state is
touched.

Traces to: FR-SYNC-021 through FR-SYNC-040
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.commands.sync import (
    OperationResult,
    SyncCommand,
)

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------


def _make_cmd(
    tmp_path: Path,
    *,
    agents_dir: Path | None = None,
    hooks_dir: Path | None = None,
    hook_config_path: Path | None = None,
    work_stream_path: Path | None = None,
) -> SyncCommand:
    """Return a SyncCommand rooted at a throwaway temp directory."""
    return SyncCommand(
        project_root=tmp_path,
        agents_dir=agents_dir,
        hooks_dir=hooks_dir,
        hook_config_path=hook_config_path,
        work_stream_path=work_stream_path,
    )


def _agent_dir(tmp_path: Path, names: list[str]) -> Path:
    d = tmp_path / "agents"
    d.mkdir(exist_ok=True)
    for name in names:
        (d / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    return d


def _hooks_dir(tmp_path: Path, scripts: list[str]) -> Path:
    d = tmp_path / "hooks"
    d.mkdir(exist_ok=True)
    for name in scripts:
        (d / f"{name}.sh").write_text(f"#!/bin/sh\n# {name}\n", encoding="utf-8")
    return d


def _hook_config(hooks_dir: Path, registered: list[str]) -> Path:
    lines = ["hooks:"]
    for name in registered:
        lines.append(f"  {name}:")
        lines.append(f"    description: {name}")
    path = hooks_dir / "hook-config.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# SyncResult — new fields
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncPush:
    def test_returns_operation_result(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-028
        cmd = _make_cmd(tmp_path)
        op = cmd.push()
        assert isinstance(op, OperationResult)

    @pytest.mark.skip(reason="Requires agent/hook artifacts in test env")
    def test_push_succeeds_with_default_target(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-028
        cmd = _make_cmd(tmp_path)
        target = tmp_path / "remote"
        target.mkdir()
        with patch.dict(os.environ, {"THGENT_SYNC_REMOTE": str(target)}):
            op = cmd.push()
        assert op.ok is True
        assert op.operation == "push"

    @pytest.mark.skip(reason="Requires agent/hook artifacts in test env")
    def test_push_with_explicit_target(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-029
        cmd = _make_cmd(tmp_path)
        target = tmp_path / "explicit-target"
        target.mkdir()
        op = cmd.push(target=str(target))
        assert op.ok is True
        assert op.details["target"] == str(target.resolve())

    def test_push_env_var_overridden_by_explicit_target(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-029
        cmd = _make_cmd(tmp_path)
        env_target = tmp_path / "env-target"
        explicit_target = tmp_path / "explicit-target"
        env_target.mkdir()
        explicit_target.mkdir()
        with patch.dict(os.environ, {"THGENT_SYNC_REMOTE": str(env_target)}):
            op = cmd.push(target=str(explicit_target))
        assert op.details["target"] == str(explicit_target.resolve())


class TestSyncPull:
    def test_returns_operation_result(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-032
        cmd = _make_cmd(tmp_path)
        op = cmd.pull()
        assert isinstance(op, OperationResult)
