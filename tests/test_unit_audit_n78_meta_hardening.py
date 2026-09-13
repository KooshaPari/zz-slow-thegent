"""AUDIT-N+78: governance/meta hardening spec (SOTA pass-62).

15 invariants FR-GOV-MT-001..015 covering MetaGovernance init,
constitution loading, validate_action keyword guards, save_constitution
mkdir, get_constitution_summary, default rules, inactive rule skip,
__all__ export, and path fallback.

Source: src/thegent/governance/meta.py

@trace AUDIT-N+78 FR-GOV-MT-001..015
"""

from __future__ import annotations

import json
from pathlib import Path

from thegent.governance.meta import MetaGovernance


class TestMetaGovernanceInit:
    def test_returns_meta_governance(self, tmp_path):
        mg = MetaGovernance(constitution_path=tmp_path / "constitution.json")
        assert isinstance(mg, MetaGovernance)

    def test_default_path_fallback(self):
        mg = MetaGovernance()
        assert mg.path is not None
        assert isinstance(mg.path, Path)

    def test_has_rules_list(self, tmp_path):
        mg = MetaGovernance(constitution_path=tmp_path / "constitution.json")
        assert hasattr(mg, "rules")
        assert isinstance(mg.rules, list)


class TestConstitutionLoading:
    def test_creates_default_constitution(self, tmp_path):
        path = tmp_path / "constitution.json"
        mg = MetaGovernance(constitution_path=path)
        assert path.exists()
        assert len(mg.rules) >= 1

    def test_loads_existing_constitution(self, tmp_path):
        path = tmp_path / "constitution.json"
        mg1 = MetaGovernance(constitution_path=path)
        count = len(mg1.rules)
        mg2 = MetaGovernance(constitution_path=path)
        assert len(mg2.rules) == count


class TestValidateAction:
    def test_blocks_delete_action(self, tmp_path):
        mg = MetaGovernance(constitution_path=tmp_path / "constitution.json")
        ok, reason = mg.validate_action("delete all files", set())
        assert ok is False
        assert reason is not None

    def test_allows_safe_action(self, tmp_path):
        mg = MetaGovernance(constitution_path=tmp_path / "constitution.json")
        ok, reason = mg.validate_action("read status", set())
        assert ok is True
        assert reason is None

    def test_blocks_secret_tag(self, tmp_path):
        mg = MetaGovernance(constitution_path=tmp_path / "constitution.json")
        ok, _reason = mg.validate_action("upload data", {"secret"})
        assert ok is False

    def test_inactive_rules_skipped(self, tmp_path):
        mg = MetaGovernance(constitution_path=tmp_path / "constitution.json")
        for rule in mg.rules:
            rule.is_active = False
        ok, _reason = mg.validate_action("delete everything", set())
        assert ok is True


class TestSaveConstitution:
    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "a" / "b" / "constitution.json"
        MetaGovernance(constitution_path=path)
        assert path.exists()

    def test_persists_rules(self, tmp_path):
        path = tmp_path / "constitution.json"
        mg = MetaGovernance(constitution_path=path)
        mg.save_constitution()
        data = json.loads(path.read_text())
        assert isinstance(data, list)
        assert len(data) >= 1


class TestConstitutionSummary:
    def test_returns_string(self, tmp_path):
        mg = MetaGovernance(constitution_path=tmp_path / "constitution.json")
        summary = mg.get_constitution_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.meta import __all__ as exported

        assert "MetaGovernance" in exported
        assert "Rule" in exported
