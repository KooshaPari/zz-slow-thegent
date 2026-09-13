"""Unit tests for governance/verification_gate.py hardening (AUDIT-N+65).

Contract surface: FR-GOV-VG-001..015
"""

from unittest.mock import MagicMock

from thegent.governance.verification_gate import (
    DEFAULT_MAX_REROLLS,
    HealthComputerProtocol,
    ScannerProtocol,
    ScanResultProtocol,
    TaskVerification,
    VerificationGate,
    VerificationVerdict,
)


# ---------------------------------------------------------------------------
# FR-GOV-VG-001: VerificationVerdict has exactly 4 members
# ---------------------------------------------------------------------------
class TestFRGOOVG001:
    def test_verdict_has_exactly_four_members(self):
        members = list(VerificationVerdict)
        assert len(members) == 4

    def test_verdict_members_are_pass_fail_neutral_regression(self):
        names = {m.name for m in VerificationVerdict}
        assert names == {"PASS", "FAIL", "NEUTRAL", "REGRESSION"}


# ---------------------------------------------------------------------------
# FR-GOV-VG-002: VerificationVerdict.PASS value is 'pass'
# ---------------------------------------------------------------------------
class TestFRGOOVG002:
    def test_pass_value(self):
        assert VerificationVerdict.PASS == "pass"


# ---------------------------------------------------------------------------
# FR-GOV-VG-003: TaskVerification stores all fields correctly
# ---------------------------------------------------------------------------
class TestFRGOOVG003:
    def test_task_verification_stores_all_fields(self):
        tv = TaskVerification(
            task_id="t1",
            verdict=VerificationVerdict.PASS,
            metrics_before={"score": 0.5},
            metrics_after={"score": 0.8},
            deltas={"score": 0.3},
            regressions=[],
            evidence_id="verify_t1_r1",
        )
        assert tv.task_id == "t1"
        assert tv.verdict == VerificationVerdict.PASS
        assert tv.metrics_before == {"score": 0.5}
        assert tv.metrics_after == {"score": 0.8}
        assert tv.deltas == {"score": 0.3}
        assert tv.regressions == []
        assert tv.evidence_id == "verify_t1_r1"


# ---------------------------------------------------------------------------
# FR-GOV-VG-004: TaskVerification.evidence_id format is 'verify_{task_id}_{run_id}'
# ---------------------------------------------------------------------------
class TestFRGOOVG004:
    def test_evidence_id_format(self):
        task_id = "task-abc"
        run_id = "run-42"
        evidence_id = f"verify_{task_id}_{run_id}"
        assert evidence_id == "verify_task-abc_run-42"

    def test_evidence_id_from_verify_task(self):
        """Verify the evidence_id construction logic matches the gate."""
        mock_scanner = MagicMock(spec=ScannerProtocol)
        mock_health = MagicMock(spec=HealthComputerProtocol)
        gate = VerificationGate(mock_scanner, mock_health)

        mock_task = MagicMock(spec=["task_id", "dimension", "agent_tier"])
        mock_task.task_id = "my-task"
        mock_task.dimension = "security"
        mock_task.agent_tier = "writer_standard"

        mock_execution = MagicMock(spec=["task_id", "exit_code", "run_id"])
        mock_execution.task_id = "my-task"
        mock_execution.exit_code = 0
        mock_execution.run_id = "run-99"

        pre_dim = MagicMock()
        pre_dim.score = 0.5
        pre_dim.raw_metrics = {}

        pre_scan = MagicMock(spec=ScanResultProtocol)
        pre_scan.get_dimension.return_value = pre_dim

        post_dim = MagicMock()
        post_dim.score = 0.6
        post_dim.raw_metrics = {}
        mock_scanner.scan_dimension.return_value = post_dim

        verification = gate.verify_task(mock_task, mock_execution, pre_scan)
        assert verification.evidence_id == "verify_my-task_run-99"


# ---------------------------------------------------------------------------
# FR-GOV-VG-005: VerificationGate.__init__ stores scanner, health_computer, max_rerolls
# ---------------------------------------------------------------------------
class TestFRGOOVG005:
    def test_init_stores_attributes(self):
        mock_scanner = MagicMock(spec=ScannerProtocol)
        mock_health = MagicMock(spec=HealthComputerProtocol)
        gate = VerificationGate(mock_scanner, mock_health, max_rerolls=5)

        assert gate.scanner is mock_scanner
        assert gate.health_computer is mock_health
        assert gate.max_rerolls == 5

    def test_init_default_rerolls(self):
        mock_scanner = MagicMock(spec=ScannerProtocol)
        mock_health = MagicMock(spec=HealthComputerProtocol)
        gate = VerificationGate(mock_scanner, mock_health)

        assert gate.max_rerolls == DEFAULT_MAX_REROLLS


# ---------------------------------------------------------------------------
# FR-GOV-VG-006: _determine_verdict returns REGRESSION when regressions exist
# ---------------------------------------------------------------------------
class TestFRGOOVG006:
    def test_regression_when_regressions_exist(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        verdict = gate._determine_verdict(
            pre_score=0.5, post_score=0.9, regressions=["security"]
        )
        assert verdict == VerificationVerdict.REGRESSION


# ---------------------------------------------------------------------------
# FR-GOV-VG-007: _determine_verdict returns PASS when post > pre and no regressions
# ---------------------------------------------------------------------------
class TestFRGOOVG007:
    def test_pass_when_improved(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        verdict = gate._determine_verdict(pre_score=0.5, post_score=0.8, regressions=[])
        assert verdict == VerificationVerdict.PASS


# ---------------------------------------------------------------------------
# FR-GOV-VG-008: _determine_verdict returns NEUTRAL when scores equal
# ---------------------------------------------------------------------------
class TestFRGOOVG008:
    def test_neutral_when_equal(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        verdict = gate._determine_verdict(pre_score=0.5, post_score=0.5, regressions=[])
        assert verdict == VerificationVerdict.NEUTRAL


# ---------------------------------------------------------------------------
# FR-GOV-VG-009: _determine_verdict returns FAIL when post < pre
# ---------------------------------------------------------------------------
class TestFRGOOVG009:
    def test_fail_when_regressed_score(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        verdict = gate._determine_verdict(pre_score=0.8, post_score=0.3, regressions=[])
        assert verdict == VerificationVerdict.FAIL


# ---------------------------------------------------------------------------
# FR-GOV-VG-010: get_escalated_tier returns next tier
# ---------------------------------------------------------------------------
class TestFRGOOVG010:
    def test_escalation_next_tier(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        assert gate.get_escalated_tier("writer_fast") == "writer_standard"

    def test_escalation_second_to_last(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        assert gate.get_escalated_tier("writer_standard") == "writer_high"


# ---------------------------------------------------------------------------
# FR-GOV-VG-011: get_escalated_tier returns None for highest tier
# ---------------------------------------------------------------------------
class TestFRGOOVG011:
    def test_escalation_highest_tier_returns_none(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        assert gate.get_escalated_tier("writer_high") is None


# ---------------------------------------------------------------------------
# FR-GOV-VG-012: get_escalated_tier returns None for unknown tier
# ---------------------------------------------------------------------------
class TestFRGOOVG012:
    def test_escalation_unknown_tier_returns_none(self):
        gate = VerificationGate(MagicMock(), MagicMock())
        assert gate.get_escalated_tier("nonexistent_tier") is None


# ---------------------------------------------------------------------------
# FR-GOV-VG-013: should_reroll returns True when attempts < max_rerolls
# ---------------------------------------------------------------------------
class TestFRGOOVG013:
    def test_reroll_true_when_under_limit(self):
        gate = VerificationGate(MagicMock(), MagicMock(), max_rerolls=3)
        assert gate.should_reroll(0) is True
        assert gate.should_reroll(1) is True
        assert gate.should_reroll(2) is True


# ---------------------------------------------------------------------------
# FR-GOV-VG-014: should_reroll returns False when attempts >= max_rerolls
# ---------------------------------------------------------------------------
class TestFRGOOVG014:
    def test_reroll_false_at_limit(self):
        gate = VerificationGate(MagicMock(), MagicMock(), max_rerolls=3)
        assert gate.should_reroll(3) is False
        assert gate.should_reroll(4) is False
        assert gate.should_reroll(100) is False


# ---------------------------------------------------------------------------
# FR-GOV-VG-015: __all__ exports exactly the expected names
# ---------------------------------------------------------------------------
class TestFRGOOVG015:
    def test_all_exports(self):
        from thegent.governance import verification_gate as mod

        expected = [
            "AGENT_TIER_ESCALATION",
            "DEFAULT_MAX_REROLLS",
            "HealthComputerProtocol",
            "ScannerProtocol",
            "ScanResultProtocol",
            "TaskExecutionProtocol",
            "TaskVerification",
            "VerificationGate",
            "VerificationVerdict",
        ]
        assert sorted(mod.__all__) == sorted(expected)
        assert len(mod.__all__) == len(expected)

    def test_all_items_are_importable(self):
        import thegent.governance.verification_gate as mod

        for name in mod.__all__:
            assert hasattr(mod, name), (
                f"{name} listed in __all__ but not found in module"
            )
