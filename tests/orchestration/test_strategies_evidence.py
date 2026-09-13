"""Tests for evidence capture at promotion gates (WP-1005, FR-004).

Tests cover PromotionGate class, capture_evidence, validate_promotion,
and verify_evidence_hash methods.
"""

import hashlib
import json as std_json
from pathlib import Path
from unittest.mock import MagicMock

import orjson as json
import pytest

from thegent.orchestration.strategies.evidence import PromotionGate


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    """Create a temporary session directory."""
    return tmp_path / "session"


@pytest.fixture
def gate(session_dir: Path) -> PromotionGate:
    """Create a PromotionGate instance for testing."""
    return PromotionGate(session_dir)


@pytest.fixture
def mock_csm() -> MagicMock:
    """Create a mock CSM object."""
    csm = MagicMock()
    csm.to_dict.return_value = {"state": "test", "data": [1, 2, 3]}
    csm.phase = MagicMock()
    csm.phase.value = "draft"
    csm.confidence_level = 0.9
    csm.blockers = []
    return csm


@pytest.fixture
def mock_policy() -> MagicMock:
    """Create a mock FallbackPolicy object."""
    policy = MagicMock()
    policy.min_confidence_threshold = 0.7
    return policy


class TestPromotionGateInit:
    """Tests for PromotionGate initialization."""

    def test_sets_session_dir(self, session_dir: Path) -> None:
        """Verify session_dir is set correctly."""
        gate = PromotionGate(session_dir)

        assert gate.session_dir == session_dir

    def test_sets_evidence_dir(self, session_dir: Path) -> None:
        """Verify evidence_dir is derived from session_dir."""
        gate = PromotionGate(session_dir)

        assert gate.evidence_dir == session_dir / "evidence"

    def test_sets_audit_path(self, session_dir: Path) -> None:
        """Verify audit_path is derived from session_dir."""
        gate = PromotionGate(session_dir)

        assert gate.audit_path == session_dir / "evidence_audit.jsonl"

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        """Verify string path is converted to Path."""
        gate = PromotionGate(str(tmp_path / "session"))

        assert isinstance(gate.session_dir, Path)


class TestPromotionGateCaptureEvidence:
    """Tests for capture_evidence method."""

    def test_creates_evidence_dir(self, gate: PromotionGate, mock_csm: MagicMock) -> None:
        """Verify evidence directory is created."""
        gate.capture_evidence("run-001", mock_csm)

        assert gate.evidence_dir.exists()
        assert gate.evidence_dir.is_dir()

    def test_writes_evidence_file(self, gate: PromotionGate, mock_csm: MagicMock, session_dir: Path) -> None:
        """Verify evidence file is written correctly."""
        gate.capture_evidence("run-001", mock_csm)

        evidence_path = session_dir / "evidence" / "run-001_draft.json"
        assert evidence_path.exists()

        content = evidence_path.read_text()
        assert json.loads(content) == {"state": "test", "data": [1, 2, 3]}

    def test_returns_correct_hash(self, gate: PromotionGate, mock_csm: MagicMock) -> None:
        """Verify correct SHA-256 hash is returned."""
        expected_data = std_json.dumps(mock_csm.to_dict(), sort_keys=True)
        expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()

        result = gate.capture_evidence("run-001", mock_csm)

        assert result == expected_hash

    def test_appends_to_audit_trail(self, gate: PromotionGate, mock_csm: MagicMock) -> None:
        """Verify audit trail is updated."""
        gate.capture_evidence("run-001", mock_csm)

        assert gate.audit_path.exists()

        with gate.audit_path.open("r") as f:
            line = f.readline()
            entry = json.loads(line)

        assert entry["run_id"] == "run-001"
        assert entry["phase"] == "draft"
        assert "evidence_hash" in entry
        assert "ts" in entry
        assert "evidence_path" in entry

    def test_handles_phase_without_value(self, gate: PromotionGate, session_dir: Path) -> None:
        """Verify phase without .value uses str()."""
        mock_csm = MagicMock()
        mock_csm.to_dict.return_value = {"test": "data"}
        mock_csm.phase = "simple_phase"  # No .value attribute

        gate.capture_evidence("run-002", mock_csm)

        evidence_path = session_dir / "evidence" / "run-002_simple_phase.json"
        assert evidence_path.exists()

    def test_multiple_captures_append_audit(self, gate: PromotionGate, mock_csm: MagicMock) -> None:
        """Verify multiple captures append to audit trail."""
        gate.capture_evidence("run-001", mock_csm)
        gate.capture_evidence("run-002", mock_csm)
        gate.capture_evidence("run-003", mock_csm)

        with gate.audit_path.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 3
        entries = [json.loads(line) for line in lines]
        assert entries[0]["run_id"] == "run-001"
        assert entries[1]["run_id"] == "run-002"
        assert entries[2]["run_id"] == "run-003"


class TestPromotionGateValidatePromotion:
    """Tests for validate_promotion method."""

    def test_no_issues_when_confident_and_no_blockers(
        self, gate: PromotionGate, mock_csm: MagicMock, mock_policy: MagicMock
    ) -> None:
        """Verify no issues when confident and no blockers."""
        issues = gate.validate_promotion(mock_csm, mock_policy)

        assert issues == []

    def test_issue_when_low_confidence(self, gate: PromotionGate, mock_csm: MagicMock, mock_policy: MagicMock) -> None:
        """Verify issue when confidence is below threshold."""
        mock_csm.confidence_level = 0.5  # Below 0.7 threshold

        issues = gate.validate_promotion(mock_csm, mock_policy)

        assert len(issues) == 1
        assert "Confidence 0.5 below threshold 0.7" in issues[0]

    def test_issue_when_blockers_present(
        self, gate: PromotionGate, mock_csm: MagicMock, mock_policy: MagicMock
    ) -> None:
        """Verify issue when blockers are present."""
        mock_csm.blockers = ["missing_dep", "timeout"]

        issues = gate.validate_promotion(mock_csm, mock_policy)

        assert len(issues) == 1
        assert "Active blockers present" in issues[0]
        assert "missing_dep" in issues[0]

    def test_multiple_issues(self, gate: PromotionGate, mock_csm: MagicMock, mock_policy: MagicMock) -> None:
        """Verify multiple issues are reported."""
        mock_csm.confidence_level = 0.5
        mock_csm.blockers = ["error"]

        issues = gate.validate_promotion(mock_csm, mock_policy)

        assert len(issues) == 2


class TestPromotionGateVerifyEvidenceHash:
    """Tests for verify_evidence_hash method."""

    def test_returns_true_for_valid_hash(self, gate: PromotionGate, mock_csm: MagicMock) -> None:
        """Verify True for valid hash."""
        evidence_hash = gate.capture_evidence("run-001", mock_csm)

        result = gate.verify_evidence_hash("run-001", "draft", evidence_hash)

        assert result is True

    def test_returns_false_for_invalid_hash(self, gate: PromotionGate, mock_csm: MagicMock) -> None:
        """Verify False for invalid hash."""
        gate.capture_evidence("run-001", mock_csm)

        result = gate.verify_evidence_hash("run-001", "draft", "invalid_hash")

        assert result is False

    def test_returns_false_for_missing_evidence(self, gate: PromotionGate) -> None:
        """Verify False when evidence file doesn't exist."""
        result = gate.verify_evidence_hash("nonexistent", "draft", "some_hash")

        assert result is False

    def test_verifies_correct_phase(self, gate: PromotionGate, mock_csm: MagicMock) -> None:
        """Verify correct phase is checked."""
        evidence_hash = gate.capture_evidence("run-001", mock_csm)

        # Wrong phase should return False
        result = gate.verify_evidence_hash("run-001", "wrong_phase", evidence_hash)
        assert result is False

        # Correct phase should return True
        result = gate.verify_evidence_hash("run-001", "draft", evidence_hash)
        assert result is True

    def test_detects_tampering(self, gate: PromotionGate, mock_csm: MagicMock, session_dir: Path) -> None:
        """Verify tampering is detected."""
        evidence_hash = gate.capture_evidence("run-001", mock_csm)

        # Tamper with the evidence file
        evidence_path = session_dir / "evidence" / "run-001_draft.json"
        original_content = evidence_path.read_text()
        tampered_content = original_content.replace("test", "TAMPERED")
        evidence_path.write_text(tampered_content)

        result = gate.verify_evidence_hash("run-001", "draft", evidence_hash)

        assert result is False
