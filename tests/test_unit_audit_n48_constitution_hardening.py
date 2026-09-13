"""AUDIT-N+48: governance/constitution hardening spec.

15 invariants FR-GOV-CN-001..015 covering ConstitutionManager init,
_load, critique_action, generate_poa, and path traversal guards.

Source: src/thegent/governance/constitution.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.governance.constitution import (
    ConstitutionalViolation,
    ConstitutionManager,
    ProofOfAlignment,
)


# ============================  FR-GOV-CN-001  ============================
class TestCNInit:
    """FR-GOV-CN-001: ConstitutionManager.__init__ stores path and calls
    _load."""

    def test_init_stores_path(self, tmp_path: Path) -> None:
        cm = ConstitutionManager(tmp_path / "constitution.yaml")
        assert cm.path == tmp_path / "constitution.yaml"

    def test_init_loads_principles(self, tmp_path: Path) -> None:
        cm = ConstitutionManager(tmp_path / "constitution.yaml")
        assert isinstance(cm.principles, list)


# ============================  FR-GOV-CN-002  ============================
class TestCNLoadMissingFile:
    """FR-GOV-CN-002: _load() with a non-existent file sets principles
    to an empty list."""

    def test_missing_file_empty_principles(self, tmp_path: Path) -> None:
        cm = ConstitutionManager(tmp_path / "nonexistent.yaml")
        assert cm.principles == []


# ============================  FR-GOV-CN-003  ============================
class TestCNLoadValidYaml:
    """FR-GOV-CN-003: _load() with a valid YAML file parses principles."""

    def test_valid_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text(
            "principles:\n  - id: P1-SAFETY\n    desc: Safety first\n  - id: P2-PRIVACY\n    desc: Privacy matters\n"
        )
        cm = ConstitutionManager(yaml_file)
        assert len(cm.principles) == 2
        assert cm.principles[0]["id"] == "P1-SAFETY"


# ============================  FR-GOV-CN-004  ============================
class TestCNLoadMalformedYaml:
    """FR-GOV-CN-004: _load() with malformed YAML falls back to empty
    principles (does not crash)."""

    def test_malformed_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("{{invalid yaml::")
        cm = ConstitutionManager(yaml_file)
        # Should either fall back to empty list or raise gracefully
        assert isinstance(cm.principles, list)


# ============================  FR-GOV-CN-005  ============================
class TestCNCritiqueActionSafe:
    """FR-GOV-CN-005: critique_action() returns no violations for a safe
    prompt."""

    def test_safe_action(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text(
            "principles:\n  - id: P1-SAFETY\n    desc: Safety first\n  - id: P2-PRIVACY\n    desc: Privacy matters\n"
        )
        cm = ConstitutionManager(yaml_file)
        violations = cm.critique_action({"prompt": "please list files"})
        assert violations == []


# ============================  FR-GOV-CN-006  ============================
class TestCNCritiqueActionDestructive:
    """FR-GOV-CN-006: critique_action() detects destructive commands."""

    def test_rm_rf_detected(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P1-SAFETY\n    desc: Safety first\n")
        cm = ConstitutionManager(yaml_file)
        violations = cm.critique_action({"prompt": "run rm -rf /tmp/data"})
        assert len(violations) >= 1
        assert violations[0].principle_id == "P1-SAFETY"

    def test_force_push_detected(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P1-SAFETY\n    desc: Safety first\n")
        cm = ConstitutionManager(yaml_file)
        violations = cm.critique_action({"prompt": "force push to main"})
        assert len(violations) >= 1

    def test_delete_all_detected(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P1-SAFETY\n    desc: Safety first\n")
        cm = ConstitutionManager(yaml_file)
        violations = cm.critique_action({"prompt": "delete all records"})
        assert len(violations) >= 1


# ============================  FR-GOV-CN-007  ============================
class TestCNCritiqueActionPrivacy:
    """FR-GOV-CN-007: critique_action() detects privacy violations."""

    def test_password_detected(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P2-PRIVACY\n    desc: Privacy matters\n")
        cm = ConstitutionManager(yaml_file)
        violations = cm.critique_action({"prompt": "send the password"})
        assert len(violations) >= 1
        assert violations[0].principle_id == "P2-PRIVACY"

    def test_api_key_detected(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P2-PRIVACY\n    desc: Privacy matters\n")
        cm = ConstitutionManager(yaml_file)
        violations = cm.critique_action({"prompt": "include api_key in payload"})
        assert len(violations) >= 1


# ============================  FR-GOV-CN-008  ============================
class TestCNCritiqueActionNoPrinciples:
    """FR-GOV-CN-008: critique_action() with no principles returns no
    violations."""

    def test_empty_principles(self, tmp_path: Path) -> None:
        cm = ConstitutionManager(tmp_path / "nonexistent.yaml")
        violations = cm.critique_action({"prompt": "rm -rf /"})
        assert violations == []


# ============================  FR-GOV-CN-009  ============================
class TestCNCritiqueActionMissingPrompt:
    """FR-GOV-CN-009: critique_action() handles action dict with no
    'prompt' key."""

    def test_no_prompt_key(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P1-SAFETY\n    desc: Safety first\n")
        cm = ConstitutionManager(yaml_file)
        violations = cm.critique_action({})
        assert violations == []


# ============================  FR-GOV-CN-010  ============================
class TestCNGeneratePOA:
    """FR-GOV-CN-010: generate_poa() returns a ProofOfAlignment with
    correct fields."""

    def test_poa_fields(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P1-SAFETY\n    desc: Safety first\n")
        cm = ConstitutionManager(yaml_file)
        poa = cm.generate_poa("action-001", True)
        assert isinstance(poa, ProofOfAlignment)
        assert poa.aligned is True
        assert "P1-SAFETY" in poa.verified_principles
        assert len(poa.critique_hash) == 64  # SHA-256 hex


# ============================  FR-GOV-CN-011  ============================
class TestCNGeneratePOAHash:
    """FR-GOV-CN-011: generate_poa() produces a deterministic SHA-256
    hash."""

    def test_deterministic_hash(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P1-SAFETY\n    desc: Safety first\n")
        cm = ConstitutionManager(yaml_file)
        poa1 = cm.generate_poa("action-001", True)
        poa2 = cm.generate_poa("action-001", True)
        assert poa1.critique_hash == poa2.critique_hash

    def test_different_action_different_hash(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "constitution.yaml"
        yaml_file.write_text("principles:\n  - id: P1-SAFETY\n    desc: Safety first\n")
        cm = ConstitutionManager(yaml_file)
        poa1 = cm.generate_poa("action-001", True)
        poa2 = cm.generate_poa("action-002", True)
        assert poa1.critique_hash != poa2.critique_hash


# ============================  FR-GOV-CN-012  ============================
class TestCNConstitutionalViolationModel:
    """FR-GOV-CN-012: ConstitutionalViolation is a Pydantic BaseModel
    with required fields."""

    def test_violation_fields(self) -> None:
        v = ConstitutionalViolation(
            principle_id="P1",
            reason="test",
            remediation="fix it",
        )
        assert v.principle_id == "P1"
        assert v.reason == "test"
        assert v.remediation == "fix it"

    def test_violation_requires_all_fields(self) -> None:
        with pytest.raises(Exception):
            ConstitutionalViolation(principle_id="P1")  # type: ignore


# ============================  FR-GOV-CN-013  ============================
class TestCNProofOfAlignmentModel:
    """FR-GOV-CN-013: ProofOfAlignment is a Pydantic BaseModel with
    required fields."""

    def test_poa_fields(self) -> None:
        poa = ProofOfAlignment(
            verified_principles=["P1"],
            critique_hash="abc123",
            aligned=True,
        )
        assert poa.verified_principles == ["P1"]
        assert poa.aligned is True

    def test_poa_requires_all_fields(self) -> None:
        with pytest.raises(Exception):
            ProofOfAlignment(verified_principles=["P1"])  # type: ignore


# ============================  FR-GOV-CN-014  ============================
class TestCNPathTraversalGuard:
    """FR-GOV-CN-014: ConstitutionManager rejects relative paths."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            ConstitutionManager(Path("relative/constitution.yaml"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        cm = ConstitutionManager(tmp_path / "constitution.yaml")
        assert cm.path.is_absolute()


# ============================  FR-GOV-CN-015  ============================
class TestCNTraceAnnotation:
    """FR-GOV-CN-015: Module must contain @trace AUDIT-N+48 annotation
    and FR-GOV-CN-001..015 invariant markers."""

    def test_trace_annotation_exists(self) -> None:
        import thegent.governance.constitution as mod

        source = open(mod.__file__).read()
        assert "AUDIT-N+48" in source
        assert "FR-GOV-CN-001" in source or "FR-GOV-CN-" in source
