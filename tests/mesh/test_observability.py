from __future__ import annotations

from pathlib import Path

from thegent.mesh.observability import mesh_status_cmd


def test_mesh_status_cmd_prints_no_agents(capsys, tmp_path: Path) -> None:
    mesh_status_cmd(tmp_path)
    captured = capsys.readouterr()
    assert "No registered agents." in captured.out


def test_mesh_status_cmd_prints_agent_rows(capsys, tmp_path: Path) -> None:
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "agent-100.yaml").write_text("pid: 100\ntype: codex\nsource: auto-detect\n", encoding="utf-8")

    mesh_status_cmd(tmp_path)
    captured = capsys.readouterr()
    assert f"Mesh root: {tmp_path}" in captured.out
    assert "Registered agents: 1" in captured.out
    assert "agent-100: pid=100 type=codex source=auto-detect" in captured.out
