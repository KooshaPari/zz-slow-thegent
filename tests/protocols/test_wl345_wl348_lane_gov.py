from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

from thegent.governance.compliance import AuditExporter, EvidenceStore


def test_wl345_reconcile_export_raises_on_count_mismatch(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence.jsonl")
    store.append(kind="agent_decision", actor="agent-a")
    exporter = AuditExporter(store)
    with pytest.raises(RuntimeError, match="Export reconciliation mismatch"):
        exporter.reconcile_export(expected_count=2)


def test_wl346_enforce_integrity_raises_for_tampered_chain(tmp_path: Path) -> None:
    store_path = tmp_path / "evidence.jsonl"
    store = EvidenceStore(store_path)
    store.append(kind="agent_decision", actor="agent-a")
    store.append(kind="human_approval", actor="reviewer-b")

    lines = store_path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["actor"] = "tampered-actor"
    lines[0] = json.dumps(tampered)
    store_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="integrity verification failed"):
        AuditExporter(EvidenceStore(store_path)).enforce_integrity()


def test_wl347_export_rejects_unknown_kind_filter(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence.jsonl")
    store.append(kind="agent_decision", actor="agent-a")
    exporter = AuditExporter(store)
    with pytest.raises(ValueError, match="Unknown evidence kind"):
        exporter.export_json(kind_filter=["unknown_kind"])


def test_wl348_export_checkpoint_writes_digest(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path / "evidence.jsonl")
    store.append(kind="agent_decision", actor="agent-a")
    store.append(kind="policy_evaluation", actor="policy-engine")
    checkpoint_path = tmp_path / "checkpoint.json"

    checkpoint = AuditExporter(store).export_checkpoint(
        checkpoint_id="wl-348-checkpoint", output_path=checkpoint_path
    )

    assert checkpoint["checkpoint_id"] == "wl-348-checkpoint"
    assert checkpoint["record_count"] == 2
    assert len(checkpoint["evidence_digest_sha256"]) == 64
    assert checkpoint_path.exists()
