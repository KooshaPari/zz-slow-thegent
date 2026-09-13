"""Eval integration module."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


class ContainsEvaluator:
    """Evaluator for contains assertions."""

    def __init__(self, threshold: float = 0.8, case_sensitive: bool = False) -> None:
        self.threshold = threshold
        self.case_sensitive = case_sensitive

    def evaluate(self, actual: str, expected: str, case: Any) -> dict[str, Any]:
        """Evaluate if actual contains expected."""
        if not self.case_sensitive:
            actual = actual.lower()
            expected = expected.lower()
        score = 1.0 if expected in actual else 0.0
        return {
            "score": score,
            "passed": score >= self.threshold,
        }


@dataclass
class EvalCase:
    """An evaluation test case."""

    id: str = ""
    name: str = ""
    prompt: str = ""
    expected: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    """Result of an evaluation."""

    case_id: str
    score: float
    passed: bool
    model: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExactMatchResult(EvalResult):
    """Exact match evaluation result."""

    actual: str = ""


class ExactMatchEvaluator:
    """Evaluator for exact string matching."""

    def __init__(self, threshold: float = 1.0) -> None:
        self.threshold = threshold

    def evaluate(self, actual: str, expected: str, case: EvalCase) -> ExactMatchResult:
        """Evaluate exact match."""
        # Strip whitespace for comparison
        actual_stripped = actual.strip()
        expected_stripped = expected.strip()
        score = 1.0 if actual_stripped == expected_stripped else 0.0
        return ExactMatchResult(
            case_id=case.id or case.name,
            score=score,
            passed=score >= self.threshold,
            actual=actual_stripped,
        )


@dataclass
class RegexResult(EvalResult):
    """Regex evaluation result."""

    pattern: str = ""


class RegexEvaluator:
    """Evaluator using regex pattern matching."""

    def __init__(self, pattern: str, flags: int = re.IGNORECASE) -> None:
        self.pattern = re.compile(pattern, flags)

    def evaluate(self, actual: str, expected: str, case: EvalCase) -> RegexResult:
        """Evaluate regex match."""
        match = self.pattern.search(actual)
        score = 1.0 if match else 0.0
        return RegexResult(
            case_id=case.id or case.name,
            score=score,
            passed=score >= 0.5,
            pattern=self.pattern.pattern,
            details={"compiled_pattern": self.pattern},
        )


@dataclass
class KeywordCoverageResult(EvalResult):
    """Keyword coverage evaluation result."""

    keywords: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)


class KeywordCoverageEvaluator:
    """Evaluator for keyword coverage."""

    def __init__(self, keywords: list[str], threshold: float = 0.5) -> None:
        self.keywords = [k.lower() for k in keywords]
        self.threshold = threshold

    def evaluate(
        self, actual: str, expected: str, case: EvalCase
    ) -> KeywordCoverageResult:
        """Evaluate keyword coverage."""
        actual_lower = actual.lower()
        found = [k for k in self.keywords if k in actual_lower]
        score = len(found) / len(self.keywords) if self.keywords else 0.0
        return KeywordCoverageResult(
            case_id=case.id or case.name,
            score=score,
            passed=score >= self.threshold,
            keywords=self.keywords,
            found=found,
        )


class EvalSuite:
    """Suite of evaluation cases."""

    def __init__(self, name: str, evaluator: Any) -> None:
        self.name = name
        self.evaluator = evaluator
        self.cases: list[EvalCase] = []
        self._results: list[EvalResult] = []

    def add_case(self, case: EvalCase) -> None:
        """Add a test case."""
        self.cases.append(case)

    def run(self, model: str, outputs: dict[str, str]) -> list[EvalResult]:
        """Run evaluation."""
        self._results = []
        for case in self.cases:
            actual = outputs.get(case.id, "")
            result = self.evaluator.evaluate(actual, case.expected, case)
            result.model = model
            self._results.append(result)
        return self._results

    def results(self) -> list[EvalResult]:
        """Get results from last run."""
        return self._results

    def summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        if not self._results:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "avg_score": 0.0,
            }
        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        avg_score = sum(r.score for r in self._results) / total if total else 0.0
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total else 0.0,
            "avg_score": avg_score,
        }


__all__ = [
    "ContainsEvaluator",
    "EvalCase",
    "EvalResult",
    "EvalSuite",
    "ExactMatchEvaluator",
    "ExactMatchResult",
    "KeywordCoverageEvaluator",
    "KeywordCoverageResult",
    "RegexEvaluator",
    "RegexResult",
]
