"""Focused coverage for TGNT-P11.1 and TGNT-P14.1 implementations."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from thegent.context.context_injection import ContextInjector
from thegent.infra.ipc import IPCMesh


def test_tgnt_p11_1_ipc_mesh_creates_tmpfs_like_dirs_with_sticky_bit(
    tmp_path: Path,
) -> None:
    mesh_root = tmp_path / "agent-mesh"
    IPCMesh(mesh_root=mesh_root)

    assert mesh_root.is_dir()
    assert (mesh_root / "locks").is_dir()

    mesh_mode = stat.S_IMODE(mesh_root.stat().st_mode)
    locks_mode = stat.S_IMODE((mesh_root / "locks").stat().st_mode)
    assert mesh_mode == 0o1777
    assert locks_mode == 0o1777


def test_tgnt_p14_1_render_agent_template_includes_expected_sections(
    tmp_path: Path,
) -> None:
    injector = ContextInjector(project_root=tmp_path)
    rendered = injector.render_agent_md(
        {"id": "agent-1", "type": "codex"},
        {
            "status": "healthy",
            "agents": ["a", "b"],
            "resources": ["queue", "cache"],
            "port_range": "4500-4600",
        },
    )

    assert "# AGENT IDENTITY" in rendered
    assert "ID: agent-1" in rendered
    assert "Type: codex" in rendered
    assert "Status: healthy" in rendered
    assert "Active Agents: 2" in rendered
    assert "Shared Resources: queue, cache" in rendered
    assert "Use shared port range: 4500-4600" in rendered


def test_tgnt_p14_1_setup_tool_context_replaces_stale_target_with_symlink(
    tmp_path: Path,
) -> None:
    injector = ContextInjector(project_root=tmp_path)
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "AGENT.md").write_text("context", encoding="utf-8")
    stale = agent_dir / "CLAUDE.md"
    stale.write_text("stale", encoding="utf-8")

    injector.setup_tool_context(agent_dir, "claude")

    assert stale.is_symlink()
    assert stale.readlink() == Path("AGENT.md")


def test_tgnt_p14_1_setup_tool_context_fails_without_source(tmp_path: Path) -> None:
    injector = ContextInjector(project_root=tmp_path)
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="Missing required context source file"):
        injector.setup_tool_context(agent_dir, "claude")
