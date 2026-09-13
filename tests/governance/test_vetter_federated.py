from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orjson as json
import pytest

from thegent.govern.vetter.checks import (
    DiffSizeCheck,
    DiffSizeVetterCheck,
    LLMJudgeCheck,
    QualityScoreVetterCheck,
    RuffCheck,
    RuffVetterCheck,
    SafetyCheck,
    SafetyVetterCheck,
    SchemaCheck,
    SchemaVetterCheck,
    TestPassCheck,
    TestPassVetterCheck,
)
from thegent.govern.vetter.models import VetterCheckResult, VetterPolicy, VetterVerdict
from thegent.govern.vetter.orchestrator import VetterOrchestrator


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _check_name_catalog() -> set[str]:
    return {
        SchemaCheck.name,
        DiffSizeCheck.name,
        SafetyCheck.name,
        LLMJudgeCheck.name,
        QualityScoreVetterCheck.name,
        TestPassCheck.name,
        RuffCheck.name,
        SchemaVetterCheck.name,
        DiffSizeVetterCheck.name,
        SafetyVetterCheck.name,
        TestPassVetterCheck.name,
        RuffVetterCheck.name,
    }


def _read_contract(contract_name: str) -> dict[str, Any]:
    path = _repo_root() / "contracts" / "vetter" / contract_name
    return json.loads(path.read_text(encoding="utf-8"))


def _failing_check(name: str) -> Any:
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=False, message="failed"))
    return check


def _passing_check(name: str) -> Any:
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=True))
    return check


def test_contracts_default_and_production_strict_parse_and_use_known_check_names() -> None:
    allowed_names = _check_name_catalog()
    default_contract = _read_contract("default.json")
    strict_contract = _read_contract("production-strict.json")

    default_policy = VetterPolicy.model_validate(default_contract)
    strict_policy = VetterPolicy.model_validate(strict_contract)

    assert default_policy.on_fail == "reject"
    assert strict_policy.on_fail == "escalate"
    assert set(default_policy.checks).issubset(allowed_names)
    assert set(strict_policy.checks).issubset(allowed_names)


class _FakeFederatedPolicyManager:
    def __init__(self, resolved_policy: dict[str, Any]) -> None:
        self.resolved_policy = resolved_policy
        self.calls: list[tuple[Any, str]] = []

    def resolve_policy(self, ns: Any, policy_id: str) -> dict[str, Any]:
        self.calls.append((ns, policy_id))
        return self.resolved_policy


@pytest.mark.asyncio
async def test_orchestrator_uses_federated_manager_resolve_policy_when_namespace_context_present(
    tmp_path: Path,
) -> None:
    fed_manager = _FakeFederatedPolicyManager(resolved_policy={"checks": ["fed_only"]})
    base_policy = VetterPolicy(checks=["base_only"])

    orch = VetterOrchestrator(
        session_dir=tmp_path,
        federated_policy=fed_manager,
        check_registry={
            "base_only": _failing_check("base_only"),
            "fed_only": _passing_check("fed_only"),
        },
    )

    result = await orch.evaluate(
        result=MagicMock(output=""),
        policy=base_policy,
        run_context={
            "run_id": "run-fed-001",
            "org": "acme",
            "project": "agent",
            "environment": "production",
            "policy_id": "default",
        },
    )

    assert result.verdict == VetterVerdict.APPROVED
    assert len(fed_manager.calls) == 1
    namespace, called_policy_id = fed_manager.calls[0]
    assert called_policy_id == "default"
    assert namespace.org == "acme"
    assert namespace.project == "agent"
    assert namespace.env == "production"


@pytest.mark.asyncio
async def test_eu_ai_act_overlay_forces_escalation_for_critical_failures(tmp_path: Path) -> None:
    hitl = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        hitl_workflow=hitl,
        check_registry={"safety": _failing_check("safety")},
    )

    result = await orch.evaluate(
        result=MagicMock(output="diff --git a/a.py b/a.py\n+unsafe"),
        policy=VetterPolicy(checks=["safety"], on_fail="reject"),
        run_context={"run_id": "run-eu-001", "jurisdiction_profile": "EU-AI-ACT"},
    )

    assert result.verdict == VetterVerdict.ESCALATED
    hitl.await_approval.assert_called_once()
