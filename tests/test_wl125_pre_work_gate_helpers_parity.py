from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from thegent.cli.commands import impl, work_stream_impl

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_instruction_architecture.py"


def _load_architecture_module():
    spec = importlib.util.spec_from_file_location("instruction_architecture_check", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_wl125_impl_pre_work_gate_wrappers_delegate(monkeypatch) -> None:
    called: dict[str, object] = {}

    def _fake_defaults():
        called["defaults"] = True
        return {"require_e2e_first": True}

    def _fake_thresholds(project_dir: Path):
        called["thresholds_project_dir"] = project_dir
        return {"max_test_evidence_age_minutes": 15}, "config.yaml"

    def _fake_age(path: Path):
        called["age_path"] = path
        return 5

    def _fake_payload(*, project_dir: Path, thresholds, violations, config_source: str):
        called["payload"] = {
            "project_dir": project_dir,
            "thresholds": thresholds,
            "violations": violations,
            "config_source": config_source,
        }
        return {"governance_blocked": True}

    def _fake_enforce(project_dir: Path):
        called["enforce_project_dir"] = project_dir
        return {"governance_blocked": True}

    monkeypatch.setattr("thegent.cli.commands.impl.pre_work_gate_helpers.pre_work_gate_defaults", _fake_defaults)
    monkeypatch.setattr("thegent.cli.commands.impl.pre_work_gate_helpers.pre_work_gate_thresholds", _fake_thresholds)
    monkeypatch.setattr("thegent.cli.commands.impl.pre_work_gate_helpers.evidence_age_minutes", _fake_age)
    monkeypatch.setattr(
        "thegent.cli.commands.impl.pre_work_gate_helpers.pre_work_governance_block_payload",
        _fake_payload,
    )
    monkeypatch.setattr("thegent.cli.commands.impl.pre_work_gate_helpers.enforce_pre_work_hard_gate", _fake_enforce)

    assert impl._pre_work_gate_defaults() == {"require_e2e_first": True}
    assert impl._pre_work_gate_thresholds(Path("/tmp/project")) == (
        {"max_test_evidence_age_minutes": 15},
        "config.yaml",
    )
    assert impl._evidence_age_minutes(Path("/tmp/evidence.json")) == 5
    assert impl._pre_work_governance_block_payload(
        project_dir=Path("/tmp/project"),
        thresholds={"max_test_evidence_age_minutes": 15},
        violations=[{"evidence_type": "test"}],
        config_source="config.yaml",
    ) == {"governance_blocked": True}
    assert impl._enforce_pre_work_hard_gate(Path("/tmp/project")) == {"governance_blocked": True}

    assert called["defaults"] is True
    assert called["thresholds_project_dir"] == Path("/tmp/project")
    assert called["age_path"] == Path("/tmp/evidence.json")
    assert called["payload"] == {
        "project_dir": Path("/tmp/project"),
        "thresholds": {"max_test_evidence_age_minutes": 15},
        "violations": [{"evidence_type": "test"}],
        "config_source": "config.yaml",
    }
    assert called["enforce_project_dir"] == Path("/tmp/project")


def test_wl125_work_stream_pre_work_gate_wrappers_delegate(monkeypatch) -> None:
    called: dict[str, object] = {}

    def _fake_defaults():
        called["defaults"] = True
        return {"require_e2e_first": False}

    def _fake_thresholds(project_dir: Path):
        called["thresholds_project_dir"] = project_dir
        return {"max_build_evidence_age_minutes": 30}, "defaults"

    def _fake_age(path: Path):
        called["age_path"] = path
        return 9

    def _fake_payload(*, project_dir: Path, thresholds, violations, config_source: str):
        called["payload"] = {
            "project_dir": project_dir,
            "thresholds": thresholds,
            "violations": violations,
            "config_source": config_source,
        }
        return {"governance_blocked": True}

    def _fake_enforce(project_dir: Path):
        called["enforce_project_dir"] = project_dir

    monkeypatch.setattr(
        "thegent.cli.commands.work_stream_impl.pre_work_gate_helpers.pre_work_gate_defaults",
        _fake_defaults,
    )
    monkeypatch.setattr(
        "thegent.cli.commands.work_stream_impl.pre_work_gate_helpers.pre_work_gate_thresholds",
        _fake_thresholds,
    )
    monkeypatch.setattr(
        "thegent.cli.commands.work_stream_impl.pre_work_gate_helpers.evidence_age_minutes",
        _fake_age,
    )
    monkeypatch.setattr(
        "thegent.cli.commands.work_stream_impl.pre_work_gate_helpers.pre_work_governance_block_payload",
        _fake_payload,
    )
    monkeypatch.setattr(
        "thegent.cli.commands.work_stream_impl.pre_work_gate_helpers.enforce_pre_work_hard_gate",
        _fake_enforce,
    )

    assert work_stream_impl._pre_work_gate_defaults() == {"require_e2e_first": False}
    assert work_stream_impl._pre_work_gate_thresholds(Path("/tmp/project")) == (
        {"max_build_evidence_age_minutes": 30},
        "defaults",
    )
    assert work_stream_impl._evidence_age_minutes(Path("/tmp/evidence.json")) == 9
    assert work_stream_impl._pre_work_governance_block_payload(
        project_dir=Path("/tmp/project"),
        thresholds={"max_build_evidence_age_minutes": 30},
        violations=[{"evidence_type": "build"}],
        config_source="defaults",
    ) == {"governance_blocked": True}
    assert work_stream_impl._enforce_pre_work_hard_gate(Path("/tmp/project")) is None

    assert called["defaults"] is True
    assert called["thresholds_project_dir"] == Path("/tmp/project")
    assert called["age_path"] == Path("/tmp/evidence.json")
    assert called["payload"] == {
        "project_dir": Path("/tmp/project"),
        "thresholds": {"max_build_evidence_age_minutes": 30},
        "violations": [{"evidence_type": "build"}],
        "config_source": "defaults",
    }
    assert called["enforce_project_dir"] == Path("/tmp/project")


def test_wl125_orchestration_wrapper_contract_parity() -> None:
    mod = _load_architecture_module()
    expected = {
        "do_next_impl",
        "wait_next_impl",
        "spawn_next_impl",
        "work_stream_claim_impl",
        "work_stream_complete_impl",
        "incorporate_impl",
        "_validate_task_and_record_errors",
        "continuity_snapshot_impl",
    }
    assert set(mod.ORCHESTRATION_WRAPPER_CONTRACTS) == expected
    assert set(mod.ORCHESTRATION_WRAPPER_CONTRACTS.values()) == expected


def test_wl125_command_modules_expose_orchestration_wrapper_names() -> None:
    mod = _load_architecture_module()
    for wrapper_name in mod.ORCHESTRATION_WRAPPER_CONTRACTS:
        assert hasattr(impl, wrapper_name)
        assert hasattr(work_stream_impl, wrapper_name)
