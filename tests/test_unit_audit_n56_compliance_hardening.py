"""AUDIT-N+56: governance/compliance hardening spec (SOTA pass-37).

15 invariants FR-GOV-CP-001..015 covering ComplianceAuditTrail init,
EvidenceStore init, RetentionEnforcer init, ComplianceExporter init,
path absolute guards, JSONL corruption resilience, parent-directory
creation, and canonical ``__all__``.

Source: src/thegent/governance/compliance.py

@trace AUDIT-N+56  FR-GOV-CP-001..015
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thegent.governance import compliance as _mod
from thegent.governance.compliance import (
    ComplianceAuditTrail,
    ComplianceEvidence,
    ComplianceExporter,
    ComplianceProfile,
    ComplianceProfileType,
    EvidenceStore,
    RetentionEnforcer,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-CP-001 -- ComplianceAuditTrail is constructible with absolute storage_path
# ---------------------------------------------------------------------------


class TestCATInit:
    """FR-GOV-CP-001: ``ComplianceAuditTrail(storage_path)`` stores paths."""

    def test_init_sets_storage_path(self, tmp_path: Path) -> None:
        cat = ComplianceAuditTrail(tmp_path)
        assert cat.storage_path == tmp_path

    def test_init_creates_storage_dir(self, tmp_path: Path) -> None:
        sub = tmp_path / "audit"
        ComplianceAuditTrail(sub)
        assert sub.is_dir()


# ---------------------------------------------------------------------------
# FR-GOV-CP-002 -- ComplianceAuditTrail rejects relative storage_path
# ---------------------------------------------------------------------------


class TestCATPathGuard:
    """FR-GOV-CP-002: ``storage_path`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            ComplianceAuditTrail(Path("relative/path"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        cat = ComplianceAuditTrail(tmp_path)
        assert cat.storage_path.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-CP-003 -- EvidenceStore is constructible with absolute store_path
# ---------------------------------------------------------------------------


class TestESInit:
    """FR-GOV-CP-003: ``EvidenceStore(store_path)`` stores paths."""

    def test_init_sets_store_path(self, tmp_path: Path) -> None:
        es = EvidenceStore(tmp_path / "ev.jsonl")
        assert es.store_path == tmp_path / "ev.jsonl"

    def test_init_hash_is_empty(self, tmp_path: Path) -> None:
        es = EvidenceStore(tmp_path / "ev.jsonl")
        assert es._last_hash == ""


# ---------------------------------------------------------------------------
# FR-GOV-CP-004 -- EvidenceStore rejects relative store_path
# ---------------------------------------------------------------------------


class TestESPathGuard:
    """FR-GOV-CP-004: ``store_path`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            EvidenceStore(Path("relative/ev.jsonl"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        es = EvidenceStore(tmp_path / "ev.jsonl")
        assert es.store_path.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-CP-005 -- RetentionEnforcer is constructible with absolute base_dir
# ---------------------------------------------------------------------------


class TestREInit:
    """FR-GOV-CP-005: ``RetentionEnforcer(base_dir)`` stores paths."""

    def test_init_sets_base_dir(self, tmp_path: Path) -> None:
        re = RetentionEnforcer(tmp_path)
        assert re.base_dir == tmp_path

    def test_init_sets_sub_paths(self, tmp_path: Path) -> None:
        re = RetentionEnforcer(tmp_path)
        assert re._policies_path == tmp_path / "policies.jsonl"
        assert re._consent_path == tmp_path / "consent.jsonl"
        assert re._purge_log_path == tmp_path / "purge_log.jsonl"


# ---------------------------------------------------------------------------
# FR-GOV-CP-006 -- RetentionEnforcer rejects relative base_dir
# ---------------------------------------------------------------------------


class TestREPathGuard:
    """FR-GOV-CP-006: ``base_dir`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            RetentionEnforcer(Path("relative/dir"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        re = RetentionEnforcer(tmp_path)
        assert re.base_dir.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-CP-007 -- ComplianceExporter is constructible with absolute session_dir
# ---------------------------------------------------------------------------


class TestCEInit:
    """FR-GOV-CP-007: ``ComplianceExporter(session_dir)`` stores paths."""

    def test_init_sets_session_dir(self, tmp_path: Path) -> None:
        ce = ComplianceExporter(tmp_path)
        assert ce.session_dir == tmp_path


# ---------------------------------------------------------------------------
# FR-GOV-CP-008 -- ComplianceExporter rejects relative session_dir
# ---------------------------------------------------------------------------


class TestCEPathGuard:
    """FR-GOV-CP-008: ``session_dir`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            ComplianceExporter(Path("relative/session"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        ce = ComplianceExporter(tmp_path)
        assert ce.session_dir.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-CP-009 -- EvidenceStore.list_all() returns [] when path missing
# ---------------------------------------------------------------------------


class TestESListAllMissing:
    """FR-GOV-CP-009: ``list_all()`` returns ``[]`` when store_path does not exist."""

    def test_returns_empty_list(self, tmp_path: Path) -> None:
        es = EvidenceStore(tmp_path / "nonexistent.jsonl")
        assert es.list_all() == []


# ---------------------------------------------------------------------------
# FR-GOV-CP-010 -- EvidenceStore.list_all() skips corrupt JSONL lines
# ---------------------------------------------------------------------------


class TestESCorruptResilience:
    """FR-GOV-CP-010: corrupt JSONL lines in ``list_all()`` are skipped."""

    def test_skips_corrupt_line(self, tmp_path: Path) -> None:
        store = tmp_path / "ev.jsonl"
        good = ComplianceEvidence(
            evidence_id="e1",
            kind="agent_decision",
            actor="test",
            timestamp_utc="2026-01-01T00:00:00+00:00",
        )
        store.write_text(f"{{bad-json\n{good.model_dump_json()}\n", encoding="utf-8")
        es = EvidenceStore(store)
        records = es.list_all()
        assert len(records) == 1
        assert records[0].evidence_id == "e1"

    def test_all_corrupt_returns_empty(self, tmp_path: Path) -> None:
        store = tmp_path / "ev.jsonl"
        store.write_text("{not-valid\nalso-not\n", encoding="utf-8")
        es = EvidenceStore(store)
        assert es.list_all() == []


# ---------------------------------------------------------------------------
# FR-GOV-CP-011 -- EvidenceStore.append() creates parent directories
# ---------------------------------------------------------------------------


class TestESAppendParents:
    """FR-GOV-CP-011: ``append()`` creates parent directories."""

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        deep = tmp_path / "a" / "b" / "c" / "ev.jsonl"
        es = EvidenceStore(deep)
        es.append(kind="agent_decision", actor="tester")
        assert deep.parent.is_dir()
        assert deep.exists()


# ---------------------------------------------------------------------------
# FR-GOV-CP-012 -- RetentionEnforcer._read_jsonl() skips corrupt lines
# ---------------------------------------------------------------------------


class TestRECorruptResilience:
    """FR-GOV-CP-012: corrupt lines in ``_read_jsonl()`` are skipped."""

    def test_skips_corrupt_line(self, tmp_path: Path) -> None:
        re = RetentionEnforcer(tmp_path)
        pol_file = tmp_path / "policies.jsonl"
        good = {"policy_id": "p1", "tenant_id": "t1"}
        pol_file.write_text(f"{{bad\n{json.dumps(good)}\n", encoding="utf-8")
        results = re._read_jsonl(pol_file)
        assert len(results) == 1
        assert results[0]["policy_id"] == "p1"

    def test_all_corrupt_returns_empty(self, tmp_path: Path) -> None:
        re = RetentionEnforcer(tmp_path)
        pol_file = tmp_path / "policies.jsonl"
        pol_file.write_text("not-json\nalso-not\n", encoding="utf-8")
        results = re._read_jsonl(pol_file)
        assert results == []


# ---------------------------------------------------------------------------
# FR-GOV-CP-013 -- ComplianceAuditTrail.record_action() creates parent dirs
# ---------------------------------------------------------------------------


class TestCATRecordActionParents:
    """FR-GOV-CP-013: ``record_action()`` creates parent directories."""

    def test_creates_parents_on_record(self, tmp_path: Path) -> None:
        deep = tmp_path / "x" / "y" / "z"
        cat = ComplianceAuditTrail(deep)
        profile = ComplianceProfile(
            profile=ComplianceProfileType.GDPR,
            jurisdiction="EU",
            controls=[],
        )
        cat.record_action("test_action", {}, profile)
        assert deep.is_dir()
        assert cat.ledger_file.exists()


# ---------------------------------------------------------------------------
# FR-GOV-CP-014 -- __all__ exports ComplianceProfileType
# ---------------------------------------------------------------------------


class TestAllExportsProfileType:
    """FR-GOV-CP-014: ``__all__`` exports ``ComplianceProfileType``."""

    def test_all_exports_compliance_profile_type(self) -> None:
        assert "ComplianceProfileType" in _mod.__all__

    def test_module_exports_compliance_profile_type(self) -> None:
        assert _mod.ComplianceProfileType is ComplianceProfileType


# ---------------------------------------------------------------------------
# FR-GOV-CP-015 -- __all__ exports EvidenceStore
# ---------------------------------------------------------------------------


class TestAllExportsEvidenceStore:
    """FR-GOV-CP-015: ``__all__`` exports ``EvidenceStore``."""

    def test_all_exports_evidence_store(self) -> None:
        assert "EvidenceStore" in _mod.__all__

    def test_module_exports_evidence_store(self) -> None:
        assert _mod.EvidenceStore is EvidenceStore
