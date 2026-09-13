from __future__ import annotations

from typer.testing import CliRunner

from thegent.mesh.main import app

runner = CliRunner()


class _DummyMesh:
    def __init__(self, root) -> None:
        self.root = root
        self.registered: list[tuple[str, dict]] = []
        self.pattern_calls: list[list[str]] = []

    def discover_agents(self, patterns: list[str]):
        self.pattern_calls.append(patterns)
        return [{"pid": 222, "name": "codex"}]

    def register_agent(self, agent_id: str, metadata: dict) -> None:
        self.registered.append((agent_id, metadata))


def test_mesh_discover_auto_detect_registers_and_reports(monkeypatch, tmp_path) -> None:
    mesh = _DummyMesh(tmp_path)
    monkeypatch.setattr("thegent.mesh.main.MeshManager", lambda root: mesh)
    monkeypatch.setattr(
        "thegent.mesh.main.run_detection",
        lambda: [{"pid": 101, "agent": "claude"}, {"pid": 202, "agent": "cursor"}],
    )

    result = runner.invoke(app, ["discover", "--mesh-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Discovered 2 agents." in result.output
    assert "- claude-101" in result.output
    assert "- cursor-202" in result.output
    assert [agent_id for agent_id, _ in mesh.registered] == ["claude-101", "cursor-202"]


def test_mesh_discover_pattern_filter_registers_and_reports(monkeypatch, tmp_path) -> None:
    mesh = _DummyMesh(tmp_path)
    monkeypatch.setattr("thegent.mesh.main.MeshManager", lambda root: mesh)

    result = runner.invoke(app, ["discover", "--patterns", "codex,claude", "--mesh-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Discovered 1 agents." in result.output
    assert "- codex-222" in result.output
    assert mesh.pattern_calls == [["codex", "claude"]]
    assert mesh.registered[0][0] == "codex-222"


def test_mesh_agents_without_agents(tmp_path) -> None:
    result = runner.invoke(app, ["agents", "--mesh-root", str(tmp_path)])
    assert result.exit_code == 0
    assert "No registered agents." in result.output


def test_mesh_agents_lists_registered_agents(tmp_path) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "codex-101.yaml").write_text(
        "pid: 101\ntype: codex\nsource: auto\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["agents", "--mesh-root", str(tmp_path)])
    assert result.exit_code == 0
    assert "Registered agents: 1" in result.output
    assert "codex-101: pid=101 type=codex source=auto" in result.output
