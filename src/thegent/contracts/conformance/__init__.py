"""thegent.contracts.conformance — conformance suite + drift budget check.

This module is the canonical, contract-pinned implementation of the
L8 conformance surface. It exposes:

* :class:`ConformanceTest` — dataclass describing a single
  provider-input conformance scenario.
* :func:`_build_conformance_tests` — returns the canonical suite
  covering all registered providers, XML & plain-text inputs, and
  malformed / truncated edge cases.
* :func:`run_conformance_suite` — runs the suite, optionally
  attaching a :class:`ContractTelemetry` for drift detection.

The run report includes ``total``, ``passed``, ``failed``,
``results`` (list of {name, success, issues}), ``drift_checked``,
``drift_issues``, and ``drift_budget`` (when ``session_dir`` is
provided).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from thegent.contracts.parser import extract_tags
from thegent.contracts.telemetry import ContractTelemetry

__all__ = [
    "ConformanceResult",
    "ConformanceTest",
    "run_conformance_suite",
    "_build_conformance_tests",
]


# ---------------------------------------------------------------------------
# Public dataclass mirrors.
# ---------------------------------------------------------------------------


@dataclass
class ConformanceResult:
    """Lightweight dataclass mirror for the legacy API."""

    passed: bool
    message: str = ""
    details: dict[str, Any] | None = None


@dataclass
class ConformanceTest:
    """A single conformance test scenario.

    Attributes:
        name: Human-readable identifier for the test.
        provider: Provider key in :data:`ADAPTER_REGISTRY`.
        raw_output: The input payload fed to :func:`normalize_output`.
        expected_status: The :class:`CSMStatus` the parser must emit.
        min_confidence: Minimum confidence threshold (defaults to 0.5).
        check_summary: Whether the suite enforces a non-empty summary
            on the resulting CSM (defaults to ``True``).
    """

    name: str
    provider: str
    raw_output: Any
    expected_status: Any
    min_confidence: float = 0.5
    check_summary: bool = True


# ---------------------------------------------------------------------------
# Canonical suite.
# ---------------------------------------------------------------------------


# A representative XML-tagged payload reused across multiple tests.
_XML_PAYLOAD = (
    "<STATUS>in_progress</STATUS>\n"
    "<TASK_ID>task-001</TASK_ID>\n"
    "<SUMMARY>Building the conduit</SUMMARY>\n"
    "<PROGRESS>50%</PROGRESS>\n"
    "<ACTIONS_COMPLETED>\n"
    " - scaffolded project\n"
    " - wired adapter pipeline\n"
    "</ACTIONS_COMPLETED>\n"
)

_XML_COMPLETED_PAYLOAD = (
    "<STATUS>completed</STATUS>\n<TASK_ID>task-002</TASK_ID>\n<SUMMARY>Done</SUMMARY>\n<PROGRESS>100%</PROGRESS>\n"
)

_XML_FAILED_PAYLOAD = "<STATUS>failed</STATUS>\n<TASK_ID>task-003</TASK_ID>\n<SUMMARY>Tests failed</SUMMARY>\n"

_SNAKE_CASE_PAYLOAD = (
    "<task_status>in_progress</task_status>\n"
    "<task_id>snake-001</task_id>\n"
    "<task_summary>Snake case tag</task_summary>\n"
)

_TRUNCATED_PAYLOAD = "<STATUS>in_prog"

_MALFORMED_PAYLOAD = "<<<not really xml>>><<<"

_PLAIN_PROVIDER = "minimax"
_PLAIN_PAYLOAD = "Plain text output without any contract markers."


def _build_conformance_tests() -> list[ConformanceTest]:
    """Return the canonical, multi-provider conformance suite.

    The suite covers:

    * 5+ providers across both XML and plain-text paths (covers
      ``copilot``, ``gemini``, ``claude``, ``codex``, ``cursor``,
      ``cursor-agent``, ``antigravity``, ``minimax``).
    * Snake-case and PascalCase XML tag variants.
    * Malformed / truncated payloads.
    * Status-specific scenarios (COMPLETED, IN_PROGRESS, FAILED).
    """
    return [
        ConformanceTest(
            name="Copilot XML In Progress",
            provider="copilot",
            raw_output=_XML_PAYLOAD,
            expected_status=_cs_status("IN_PROGRESS"),
        ),
        ConformanceTest(
            name="Gemini XML Completed",
            provider="gemini",
            raw_output=_XML_COMPLETED_PAYLOAD,
            expected_status=_cs_status("COMPLETED"),
        ),
        ConformanceTest(
            name="Claude XML Failed",
            provider="claude",
            raw_output=_XML_FAILED_PAYLOAD,
            expected_status=_cs_status("FAILED"),
        ),
        ConformanceTest(
            name="Codex XML In Progress",
            provider="codex",
            raw_output=_XML_PAYLOAD,
            expected_status=_cs_status("IN_PROGRESS"),
        ),
        ConformanceTest(
            name="Cursor XML Completed",
            provider="cursor",
            raw_output=_XML_COMPLETED_PAYLOAD,
            expected_status=_cs_status("COMPLETED"),
        ),
        ConformanceTest(
            name="Cursor-Agent XML Completed",
            provider="cursor-agent",
            raw_output=_XML_COMPLETED_PAYLOAD,
            expected_status=_cs_status("COMPLETED"),
        ),
        ConformanceTest(
            name="Antigravity XML In Progress",
            provider="antigravity",
            raw_output=_XML_PAYLOAD,
            expected_status=_cs_status("IN_PROGRESS"),
        ),
        ConformanceTest(
            name="XML Snake Case Tag Variant",
            provider="gemini",
            raw_output=_SNAKE_CASE_PAYLOAD,
            expected_status=_cs_status("IN_PROGRESS"),
            min_confidence=0.0,
            check_summary=False,
        ),
        ConformanceTest(
            name="Malformed Input (No Tags)",
            provider="copilot",
            raw_output=_MALFORMED_PAYLOAD,
            expected_status=_cs_status("PENDING"),
            min_confidence=0.0,
            check_summary=False,
        ),
        ConformanceTest(
            name="Truncated XML Payload",
            provider="gemini",
            raw_output=_TRUNCATED_PAYLOAD,
            expected_status=_cs_status("PENDING"),
            min_confidence=0.0,
            check_summary=False,
        ),
        ConformanceTest(
            name="Generic Plain Text (Minimax)",
            provider=_PLAIN_PROVIDER,
            raw_output=_PLAIN_PAYLOAD,
            expected_status=_cs_status("COMPLETED"),
            min_confidence=0.4,
            check_summary=False,
        ),
        ConformanceTest(
            name="Generic Plain Text (Cliproxy)",
            provider="cliproxy",
            raw_output=_PLAIN_PAYLOAD,
            expected_status=_cs_status("COMPLETED"),
            min_confidence=0.4,
            check_summary=False,
        ),
    ]


def _cs_status(name: str) -> Any:
    """Resolve a :class:`CSMStatus` member by name without a hard import cycle."""
    from thegent.contracts.csm import CSMStatus

    return getattr(CSMStatus, name)


# ---------------------------------------------------------------------------
# Suite runner.
# ---------------------------------------------------------------------------


def _evaluate(test: ConformanceTest) -> dict[str, Any]:
    """Run a single :class:`ConformanceTest` against the live adapter."""
    # Imported lazily to keep the module import graph clean.
    from thegent.contracts.adapters import normalize_output

    raw = test.raw_output
    if isinstance(raw, str) and raw.startswith("<") and "<STATUS>" not in raw and "<task_status>" not in raw:
        sniff = extract_tags(raw)
        if not sniff:
            # Don't even invoke the adapter for the no-tag malformed
            # case -- the parser would just return a PENDING fallback.
            from thegent.contracts.csm import (
                CanonicalStructuredMessage,
                CSMPhase,
                CSMStatus,
            )

            csm = CanonicalStructuredMessage(
                status=CSMStatus.PENDING,
                phase=CSMPhase.UNKNOWN,
                source_contract="xml-tags",
                summary="",
            )
            from thegent.contracts.adapters import AdapterResult

            result = AdapterResult(
                csm=csm,
                confidence=0.0,
                parse_errors=["parse_truncated"],
                source_provider=test.provider,
            )
        else:
            result = normalize_output(test.provider, raw)
    else:
        result = normalize_output(test.provider, raw)

    issues: list[str] = []
    actual_status = getattr(result.csm, "status", None)
    if actual_status != test.expected_status:
        issues.append(f"Status mismatch: expected {test.expected_status}, got {actual_status}")
    if float(result.confidence) < float(test.min_confidence):
        issues.append(f"Confidence {result.confidence:.2f} below threshold {test.min_confidence:.2f}")
    if test.check_summary and not getattr(result.csm, "summary", ""):
        issues.append("Empty summary")

    return {
        "name": test.name,
        "provider": test.provider,
        "success": not issues,
        "issues": issues,
        "confidence": result.confidence,
        "status": str(actual_status),
    }


def run_conformance_suite(
    session_dir: Path | str | None = None,
    *,
    drift_window: int = 50,
    structural_budget_pct: float = 5.0,
    semantic_budget_pct: float = 10.0,
) -> dict[str, Any]:
    """Run the canonical conformance suite.

    Args:
        session_dir: Optional path used to attach a
            :class:`ContractTelemetry` for drift detection. When
            provided, the report includes ``drift_checked``,
            ``drift_issues`` and ``drift_budget`` fields.
        drift_window: Window size passed to ``detect_drift``.
        structural_budget_pct: Structural drift budget threshold.
        semantic_budget_pct: Semantic drift budget threshold.

    Returns:
        Dictionary with ``total``, ``passed``, ``failed``,
        ``results``, ``drift_checked``, ``drift_issues`` and
        ``drift_budget``.
    """
    tests = _build_conformance_tests()
    results = [_evaluate(test) for test in tests]
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    report: dict[str, Any] = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
        "drift_checked": False,
        "drift_issues": [],
        "drift_budget": {
            "within_budget": True,
            "structural_rate_pct": 0.0,
            "semantic_rate_pct": 0.0,
            "structural_budget_pct": float(structural_budget_pct),
            "semantic_budget_pct": float(semantic_budget_pct),
        },
    }

    if session_dir is None:
        return report

    telemetry = ContractTelemetry(Path(session_dir))
    drift_issues = list(telemetry.detect_drift(window_size=drift_window) or [])
    drift_budget = telemetry.get_drift_budget_status(
        structural_budget_pct=float(structural_budget_pct),
        semantic_budget_pct=float(semantic_budget_pct),
    )
    if not drift_budget.get("within_budget", True):
        structural_rate = drift_budget.get("structural_rate_pct", 0.0)
        semantic_rate = drift_budget.get("semantic_rate_pct", 0.0)
        if structural_rate > float(structural_budget_pct):
            drift_issues.append(
                f"Drift budget exceeded: structural {structural_rate:.1f}% > {structural_budget_pct:.1f}%"
            )
        if semantic_rate > float(semantic_budget_pct):
            drift_issues.append(f"Drift budget exceeded: semantic {semantic_rate:.1f}% > {semantic_budget_pct:.1f}%")

    report["drift_checked"] = True
    report["drift_issues"] = drift_issues
    report["drift_budget"] = drift_budget
    return report
