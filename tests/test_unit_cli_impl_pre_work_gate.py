"""WP-HG-05 pre-work hard gate tests for do-next and workstream claim."""

from pathlib import Path

import pytest


def _write_json(path: Path, payload: str = "{}") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


@pytest.mark.unit
def test_do_next_impl_blocks_when_evidence_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing evidence returns governance block payload with empty next items."""
    from thegent.cli.commands.impl import do_next_impl

    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))

    project = tmp_path / "project"
    project.mkdir(parents=True, exist_ok=True)

    result = do_next_impl(cd=project, limit=5)

    assert result["governance_blocked"] is True
    assert result["count"] == 0
    assert result["next_items"] == []
    assert "governance_block" in result
    assert result["governance_block"]["gate"] == "WP-HG-05.pre_work_hard_gate"


@pytest.mark.unit
def test_pre_work_gate_returns_none_when_evidence_fresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fresh evidence should not return governance block shape from helper."""
    from thegent.cli.commands.impl import _enforce_pre_work_hard_gate

    home = tmp_path / "home"
    _write_json(home / ".claude" / ".async-test-results.json")
    monkeypatch.setenv("HOME", str(home))

    project = tmp_path / "project"
    _write_json(project / ".claude" / "verification" / "qa-state.json")
    _write_json(project / ".claude" / "verification" / "qa-attestation.json")

    block = _enforce_pre_work_hard_gate(project)
    assert block is None


@pytest.mark.unit
def test_pre_work_gate_reads_hook_yaml_thresholds_from_project_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Project hook-config thresholds must override defaults for e2e requirement."""
    from thegent.cli.commands.impl import _enforce_pre_work_hard_gate

    home = tmp_path / "home"
    _write_json(home / ".claude" / ".async-test-results.json")
    monkeypatch.setenv("HOME", str(home))

    project = tmp_path / "project"
    _write_json(project / ".claude" / "verification" / "qa-state.json")
    (project / "hooks").mkdir(parents=True, exist_ok=True)
    (project / "hooks" / "hook-config.yaml").write_text(
        "\n".join(
            [
                "settings:",
                "  regression_spiral_guard:",
                "    require_e2e_first: false",
                "    max_test_evidence_age_minutes: 30",
                "    max_build_evidence_age_minutes: 30",
                "    max_e2e_evidence_age_minutes: 30",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # No qa-attestation evidence is created; defaults would block here.
    block = _enforce_pre_work_hard_gate(project)
    assert block is None


@pytest.mark.unit
def test_work_stream_claim_impl_blocks_when_evidence_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Claim command returns success=false with governance block when evidence is missing."""
    from thegent.cli.commands.impl import work_stream_claim_impl

    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))

    project = tmp_path / "project"
    project.mkdir(parents=True, exist_ok=True)

    result = work_stream_claim_impl(item_id="WP-1", agent_id="agent-1", cd=project)

    assert result["success"] is False
    assert result["governance_blocked"] is True
    assert result["item_id"] == "WP-1"
    assert result["agent_id"] == "agent-1"
    assert result["governance_block"]["gate"] == "WP-HG-05.pre_work_hard_gate"


@pytest.mark.unit
def test_spawn_next_impl_blocks_when_evidence_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Spawn-next returns governance block payload instead of silently reporting empty."""
    from thegent.cli.commands.impl import spawn_next_impl

    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))

    project = tmp_path / "project"
    project.mkdir(parents=True, exist_ok=True)

    result = spawn_next_impl(cd=project, limit=3)

    assert result["governance_blocked"] is True
    assert result["count"] == 0
    assert result["spawned"] == []
    assert result["errors"] == []
    assert result["governance_block"]["gate"] == "WP-HG-05.pre_work_hard_gate"
