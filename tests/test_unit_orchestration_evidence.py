"""Unit tests for orchestration evidence capture (WP-1005, FR-004)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json

from thegent.contracts.csm import CanonicalStructuredMessage, CSMPhase, CSMStatus
from thegent.contracts.policy import FallbackPolicy
from thegent.orchestration.strategies.evidence import PromotionGate

if TYPE_CHECKING:
    from pathlib import Path


class TestPromotionGate:
    """Evidence capture and validation."""

    def test_capture_evidence_stores_and_returns_hash(self, tmp_path: Path) -> None:
        gate = PromotionGate(tmp_path)
        csm = CanonicalStructuredMessage(
            run_id="run_123",
            phase=CSMPhase.OPERATOR,
            status=CSMStatus.COMPLETED,
            confidence_level=0.9,
        )
        h = gate.capture_evidence("run_123", csm)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
        evidence_path = tmp_path / "evidence" / "run_123_operator.json"
        assert evidence_path.exists()
        assert evidence_path.read_text()

    def test_capture_evidence_audit_trail(self, tmp_path: Path) -> None:
        gate = PromotionGate(tmp_path)
        csm = CanonicalStructuredMessage(run_id="run_1", phase=CSMPhase.PLANNER)
        gate.capture_evidence("run_1", csm)
        assert gate.audit_path.exists()
        lines = gate.audit_path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["run_id"] == "run_1"
        assert "evidence_hash" in entry
        assert "ts" in entry

    def test_validate_promotion_confidence_below_threshold(
        self, tmp_path: Path
    ) -> None:
        gate = PromotionGate(tmp_path)
        csm = CanonicalStructuredMessage(confidence_level=0.2)
        policy = FallbackPolicy(min_confidence_threshold=0.5)
        issues = gate.validate_promotion(csm, policy)
        assert len(issues) == 1
        assert "Confidence" in issues[0]

    def test_validate_promotion_blockers_present(self, tmp_path: Path) -> None:
        gate = PromotionGate(tmp_path)
        csm = CanonicalStructuredMessage(confidence_level=0.9, blockers=["need-review"])
        policy = FallbackPolicy()
        issues = gate.validate_promotion(csm, policy)
        assert len(issues) == 1
        assert "blockers" in issues[0]

    def test_validate_promotion_passes(self, tmp_path: Path) -> None:
        gate = PromotionGate(tmp_path)
        csm = CanonicalStructuredMessage(confidence_level=0.9, blockers=[])
        policy = FallbackPolicy(min_confidence_threshold=0.4)
        issues = gate.validate_promotion(csm, policy)
        assert issues == []

    def test_verify_evidence_hash_matches(self, tmp_path: Path) -> None:
        gate = PromotionGate(tmp_path)
        csm = CanonicalStructuredMessage(run_id="r1", phase=CSMPhase.OPERATOR)
        h = gate.capture_evidence("r1", csm)
        assert gate.verify_evidence_hash("r1", "operator", h) is True

    def test_verify_evidence_hash_mismatch(self, tmp_path: Path) -> None:
        gate = PromotionGate(tmp_path)
        csm = CanonicalStructuredMessage(run_id="r1", phase=CSMPhase.OPERATOR)
        gate.capture_evidence("r1", csm)
        assert gate.verify_evidence_hash("r1", "operator", "wrong_hash") is False

    def test_verify_evidence_hash_missing_file(self, tmp_path: Path) -> None:
        gate = PromotionGate(tmp_path)
        assert gate.verify_evidence_hash("nonexistent", "operator", "abc") is False
