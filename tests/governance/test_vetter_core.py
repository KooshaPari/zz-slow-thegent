"""Tests for VetterPolicy, VetterCheck, VetterResult core types.

@trace FR-VET-090
"""

from __future__ import annotations

import abc
from typing import Any

import pytest

from thegent.governance.vetter import (
    VetterCheck,
    VetterOutcome,
    VetterPolicy,
    VetterResult,
    VetterSeverity,
)

# ---------------------------------------------------------------------------
# Concrete check fixture — used across TestVetterCheck tests
# ---------------------------------------------------------------------------


class _AlwaysApprove(VetterCheck):
    """Minimal concrete check that always approves. @trace FR-VET-090"""

    @property
    def name(self) -> str:
        return "always_approve"

    @property
    def policy(self) -> VetterPolicy:
        return VetterPolicy(name="test_policy")

    def run(self, payload: dict[str, Any]) -> VetterResult:
        return VetterResult.approved(
            check_name=self.name,
            policy_name=self.policy.name,
            reason="auto-approved",
        )


class _AlwaysReject(VetterCheck):
    """Minimal concrete check that always rejects. @trace FR-VET-090"""

    @property
    def name(self) -> str:
        return "always_reject"

    @property
    def policy(self) -> VetterPolicy:
        return VetterPolicy(name="reject_policy")

    def run(self, payload: dict[str, Any]) -> VetterResult:
        return VetterResult.rejected(
            check_name=self.name,
            policy_name=self.policy.name,
            reason="always rejected",
        )


class _AlwaysRevise(VetterCheck):
    """Minimal concrete check that always requests revision. @trace FR-VET-090"""

    @property
    def name(self) -> str:
        return "always_revise"

    @property
    def policy(self) -> VetterPolicy:
        return VetterPolicy(name="revise_policy")

    def run(self, payload: dict[str, Any]) -> VetterResult:
        return VetterResult.revision_requested(
            check_name=self.name,
            policy_name=self.policy.name,
            reason="needs revision",
        )


# ---------------------------------------------------------------------------
# TestVetterResult
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-VET-090")
class TestVetterResult:
    def test_vetter_result_approved(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.approved(
            check_name="mycheck",
            policy_name="mypolicy",
            reason="looks good",
        )
        assert result.outcome == VetterOutcome.APPROVED
        assert result.check_name == "mycheck"
        assert result.policy_name == "mypolicy"
        assert result.reason == "looks good"

    def test_vetter_result_rejected(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.rejected(
            check_name="mycheck",
            policy_name="mypolicy",
            reason="bad output",
        )
        assert result.outcome == VetterOutcome.REJECTED
        assert result.reason == "bad output"

    def test_vetter_result_revision_requested(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.revision_requested(
            check_name="mycheck",
            policy_name="mypolicy",
            reason="please fix imports",
        )
        assert result.outcome == VetterOutcome.REVISION_REQUESTED
        assert result.reason == "please fix imports"

    def test_vetter_result_has_reason(self) -> None:
        # @trace FR-VET-090
        result = VetterResult(
            outcome=VetterOutcome.REJECTED,
            reason="explicit reason",
            check_name="c",
            policy_name="p",
        )
        assert result.reason == "explicit reason"

    def test_vetter_result_approved_is_pass(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.approved(check_name="c", policy_name="p")
        assert result.is_pass is True
        assert result.is_fail is False

    def test_vetter_result_rejected_is_fail(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.rejected(check_name="c", policy_name="p", reason="x")
        assert result.is_fail is True
        assert result.is_pass is False

    def test_vetter_result_revision_is_fail(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.revision_requested(check_name="c", policy_name="p", reason="y")
        assert result.is_fail is True
        assert result.is_pass is False

    def test_vetter_result_metadata_optional(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.approved(check_name="c", policy_name="p")
        assert result.metadata == {}

    def test_vetter_result_metadata_populated_via_kwargs(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.approved(
            check_name="c",
            policy_name="p",
            reason="ok",
            score=0.99,
            lines=42,
        )
        assert result.metadata["score"] == 0.99
        assert result.metadata["lines"] == 42

    def test_vetter_result_serializable_to_dict(self) -> None:
        # @trace FR-VET-090
        result = VetterResult.approved(check_name="c", policy_name="p", reason="ok")
        d = result.model_dump()
        assert d["outcome"] == "approved"
        assert d["check_name"] == "c"
        assert d["policy_name"] == "p"
        assert "metadata" in d


# ---------------------------------------------------------------------------
# TestVetterPolicy
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-VET-090")
class TestVetterPolicy:
    def test_vetter_policy_name_required(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="my_policy")
        assert policy.name == "my_policy"

    def test_vetter_policy_enabled_default_true(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="p")
        assert policy.enabled is True

    def test_vetter_policy_disable(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="p")
        policy.disable()
        assert policy.enabled is False

    def test_vetter_policy_enable_after_disable(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="p")
        policy.disable()
        policy.enable()
        assert policy.enabled is True

    def test_vetter_policy_severity_levels(self) -> None:
        # @trace FR-VET-090
        for sev in VetterSeverity:
            policy = VetterPolicy(name="p", severity=sev)
            assert policy.severity == sev

    def test_vetter_policy_severity_default_error(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="p")
        assert policy.severity == VetterSeverity.ERROR

    def test_vetter_policy_description_default_empty(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="p")
        assert policy.description == ""

    def test_vetter_policy_to_dict(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="p", severity=VetterSeverity.WARNING, description="desc")
        d = policy.to_dict()
        assert d["name"] == "p"
        assert d["severity"] == "warning"
        assert d["description"] == "desc"
        assert d["enabled"] is True

    def test_vetter_policy_to_dict_after_disable(self) -> None:
        # @trace FR-VET-090
        policy = VetterPolicy(name="p")
        policy.disable()
        d = policy.to_dict()
        assert d["enabled"] is False


# ---------------------------------------------------------------------------
# TestVetterCheck
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-VET-090")
class TestVetterCheck:
    def test_vetter_check_is_abstract(self) -> None:
        # @trace FR-VET-090
        assert issubclass(VetterCheck, abc.ABC)

    def test_vetter_check_requires_name(self) -> None:
        # @trace FR-VET-090 — cannot instantiate without implementing name
        class _MissingName(VetterCheck):
            @property
            def policy(self) -> VetterPolicy:
                return VetterPolicy(name="p")

            def run(self, payload: dict[str, Any]) -> VetterResult:
                return VetterResult.approved(check_name="x", policy_name="p")

        with pytest.raises(TypeError):
            _MissingName()  # type: ignore[abstract]

    def test_vetter_check_requires_run_method(self) -> None:
        # @trace FR-VET-090 — cannot instantiate without implementing run
        class _MissingRun(VetterCheck):
            @property
            def name(self) -> str:
                return "x"

            @property
            def policy(self) -> VetterPolicy:
                return VetterPolicy(name="p")

        with pytest.raises(TypeError):
            _MissingRun()  # type: ignore[abstract]

    def test_concrete_vetter_check_can_approve(self) -> None:
        # @trace FR-VET-090
        check = _AlwaysApprove()
        result = check.run({})
        assert result.outcome == VetterOutcome.APPROVED
        assert result.is_pass is True

    def test_concrete_vetter_check_can_reject(self) -> None:
        # @trace FR-VET-090
        check = _AlwaysReject()
        result = check.run({"data": "anything"})
        assert result.outcome == VetterOutcome.REJECTED
        assert result.is_fail is True

    def test_concrete_vetter_check_can_request_revision(self) -> None:
        # @trace FR-VET-090
        check = _AlwaysRevise()
        result = check.run({})
        assert result.outcome == VetterOutcome.REVISION_REQUESTED
        assert result.is_fail is True

    def test_vetter_check_policy_attribute(self) -> None:
        # @trace FR-VET-090
        check = _AlwaysApprove()
        assert isinstance(check.policy, VetterPolicy)
        assert check.policy.name == "test_policy"

    def test_vetter_check_accepts_payload_dict(self) -> None:
        # @trace FR-VET-090
        check = _AlwaysApprove()
        result = check.run({"key": "value", "nested": {"a": 1}})
        assert result.is_pass is True

    def test_vetter_check_is_enabled_delegates_to_policy(self) -> None:
        # @trace FR-VET-090 — uses a stable policy instance to verify delegation
        shared_policy = VetterPolicy(name="shared")

        class _StablePolicyCheck(VetterCheck):
            @property
            def name(self) -> str:
                return "stable"

            @property
            def policy(self) -> VetterPolicy:
                return shared_policy

            def run(self, payload: dict[str, Any]) -> VetterResult:
                return VetterResult.approved(check_name=self.name, policy_name=self.policy.name)

        check = _StablePolicyCheck()
        assert check.is_enabled is True
        shared_policy.disable()
        assert check.is_enabled is False

    def test_vetter_check_is_enabled_false_when_policy_disabled(self) -> None:
        # @trace FR-VET-090

        class _DisabledPolicyCheck(VetterCheck):
            _policy = VetterPolicy(name="disabled", enabled=False)

            @property
            def name(self) -> str:
                return "disabled_check"

            @property
            def policy(self) -> VetterPolicy:
                return self._policy

            def run(self, payload: dict[str, Any]) -> VetterResult:
                return VetterResult.approved(check_name=self.name, policy_name=self.policy.name)

        check = _DisabledPolicyCheck()
        assert check.is_enabled is False
