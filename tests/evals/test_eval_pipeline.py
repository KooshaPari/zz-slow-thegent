"""Tests for GW-74: LLM evals integration.

# @trace FR-EVAL-074
"""

from __future__ import annotations

import re

import pytest

from thegent.evals.integration import (
    ContainsEvaluator,
    EvalCase,
    EvalResult,
    EvalSuite,
    ExactMatchEvaluator,
    KeywordCoverageEvaluator,
    RegexEvaluator,
)

pytestmark = pytest.mark.requirement("FR-EVAL-074")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_case(case_id: str = "c1", prompt: str = "q", expected: str = "expected") -> EvalCase:
    return EvalCase(id=case_id, prompt=prompt, expected=expected)


# ---------------------------------------------------------------------------
# ExactMatchEvaluator
# ---------------------------------------------------------------------------


def test_exact_match_pass():
    """Identical strings score 1.0 and pass."""
    ev = ExactMatchEvaluator()
    case = make_case(expected="hello world")
    result = ev.evaluate("hello world", "hello world", case)
    assert result.score == pytest.approx(1.0)
    assert result.passed is True


def test_exact_match_fail():
    """Different strings score 0.0 and do not pass."""
    ev = ExactMatchEvaluator()
    case = make_case(expected="hello world")
    result = ev.evaluate("goodbye world", "hello world", case)
    assert result.score == pytest.approx(0.0)
    assert result.passed is False


def test_exact_match_strips_whitespace():
    """Leading/trailing whitespace is ignored before comparing."""
    ev = ExactMatchEvaluator()
    case = make_case(expected="hello")
    result = ev.evaluate("  hello  ", "hello", case)
    assert result.score == pytest.approx(1.0)
    assert result.passed is True


# ---------------------------------------------------------------------------
# ContainsEvaluator
# ---------------------------------------------------------------------------


def test_contains_found():
    """Expected substring present in output scores 1.0."""
    ev = ContainsEvaluator()
    case = make_case(expected="Python")
    result = ev.evaluate("I love Python programming", "Python", case)
    assert result.score == pytest.approx(1.0)
    assert result.passed is True


def test_contains_not_found():
    """Missing expected substring scores 0.0."""
    ev = ContainsEvaluator()
    case = make_case(expected="Rust")
    result = ev.evaluate("I love Python programming", "Rust", case)
    assert result.score == pytest.approx(0.0)
    assert result.passed is False


def test_contains_case_insensitive():
    """Default ContainsEvaluator is case-insensitive."""
    ev = ContainsEvaluator()
    case = make_case(expected="python")
    result = ev.evaluate("I love PYTHON programming", "python", case)
    assert result.score == pytest.approx(1.0)
    assert result.passed is True


def test_contains_case_sensitive_miss():
    """case_sensitive=True ContainsEvaluator does not match on case difference."""
    ev = ContainsEvaluator(case_sensitive=True)
    case = make_case(expected="python")
    result = ev.evaluate("I love PYTHON programming", "python", case)
    assert result.score == pytest.approx(0.0)
    assert result.passed is False


# ---------------------------------------------------------------------------
# RegexEvaluator
# ---------------------------------------------------------------------------


def test_regex_match():
    """Pattern found in output scores 1.0."""
    ev = RegexEvaluator(r"\d{3}-\d{4}")
    case = make_case()
    result = ev.evaluate("Call 555-1234 now", "", case)
    assert result.score == pytest.approx(1.0)
    assert result.passed is True


def test_regex_no_match():
    """Pattern absent in output scores 0.0."""
    ev = RegexEvaluator(r"\d{3}-\d{4}")
    case = make_case()
    result = ev.evaluate("No phone number here", "", case)
    assert result.score == pytest.approx(0.0)
    assert result.passed is False


def test_eval_result_details():
    """RegexEvaluator puts compiled_pattern in EvalResult.details."""
    ev = RegexEvaluator(r"hello")
    case = make_case()
    result = ev.evaluate("hello world", "", case)
    assert "compiled_pattern" in result.details
    assert isinstance(result.details["compiled_pattern"], type(re.compile("")))


def test_regex_case_insensitive_default():
    """Default flags include re.IGNORECASE for RegexEvaluator."""
    ev = RegexEvaluator(r"hello")
    case = make_case()
    result = ev.evaluate("HELLO WORLD", "", case)
    assert result.score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# KeywordCoverageEvaluator
# ---------------------------------------------------------------------------


def test_keyword_coverage_all_found():
    """All keywords found yields score 1.0."""
    ev = KeywordCoverageEvaluator(keywords=["apple", "banana", "cherry"])
    case = make_case()
    result = ev.evaluate("I have apple, banana, and cherry", "", case)
    assert result.score == pytest.approx(1.0)
    assert result.passed is True


def test_keyword_coverage_partial():
    """Partial keyword coverage yields a fractional score."""
    ev = KeywordCoverageEvaluator(keywords=["apple", "banana", "cherry"], threshold=0.5)
    case = make_case()
    result = ev.evaluate("I have apple and banana", "", case)
    assert result.score == pytest.approx(2 / 3)
    assert result.passed is True


def test_keyword_coverage_threshold():
    """Score below threshold causes passed=False."""
    # Use unambiguous multi-character keywords to avoid substring collisions.
    # 'alpha' and 'beta' are present; 'gamma' and 'delta' are absent -> 2/4 = 0.5
    ev = KeywordCoverageEvaluator(keywords=["alpha", "beta", "gamma", "delta"], threshold=0.9)
    case = make_case()
    result = ev.evaluate("alpha beta", "", case)
    assert result.score == pytest.approx(0.5)
    assert result.passed is False


# ---------------------------------------------------------------------------
# EvalSuite
# ---------------------------------------------------------------------------


def test_eval_suite_run():
    """EvalSuite.run() produces one EvalResult per case."""
    suite = EvalSuite("my_suite", ExactMatchEvaluator())
    suite.add_case(EvalCase(id="c1", prompt="p1", expected="yes"))
    suite.add_case(EvalCase(id="c2", prompt="p2", expected="no"))
    outputs = {"c1": "yes", "c2": "maybe"}
    results = suite.run("gpt-4", outputs)
    assert len(results) == 2
    assert all(isinstance(r, EvalResult) for r in results)
    assert results[0].case_id == "c1"
    assert results[0].score == pytest.approx(1.0)
    assert results[1].case_id == "c2"
    assert results[1].score == pytest.approx(0.0)


def test_eval_suite_summary_pass_rate():
    """EvalSuite.summary() computes the correct pass_rate."""
    suite = EvalSuite("suite", ExactMatchEvaluator())
    suite.add_case(EvalCase(id="c1", prompt="", expected="yes"))
    suite.add_case(EvalCase(id="c2", prompt="", expected="no"))
    suite.add_case(EvalCase(id="c3", prompt="", expected="maybe"))
    outputs = {"c1": "yes", "c2": "no", "c3": "nope"}
    suite.run("test-model", outputs)
    summary = suite.summary()
    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["pass_rate"] == pytest.approx(2 / 3)


def test_eval_suite_summary_avg_score():
    """EvalSuite.summary() computes the correct avg_score."""
    # Use unambiguous multi-char keywords to avoid substring collisions.
    # c1: both 'fox' and 'cat' present -> score=1.0
    # c2: 'fox' present, 'cat' absent -> score=0.5
    # avg = (1.0 + 0.5) / 2 = 0.75
    ev = KeywordCoverageEvaluator(keywords=["fox", "cat"], threshold=0.5)
    suite = EvalSuite("kw_suite", ev)
    suite.add_case(EvalCase(id="c1", prompt="", expected=""))
    suite.add_case(EvalCase(id="c2", prompt="", expected=""))
    outputs = {"c1": "the fox and the cat", "c2": "the fox runs"}
    suite.run("model", outputs)
    summary = suite.summary()
    # c1 score = 1.0, c2 score = 0.5
    assert summary["avg_score"] == pytest.approx(0.75)


def test_eval_case_metadata():
    """metadata dict is preserved intact on EvalCase."""
    meta = {"domain": "medical", "difficulty": "hard", "version": 2}
    case = EvalCase(id="c99", prompt="q", expected="a", metadata=meta)
    assert case.metadata["domain"] == "medical"
    assert case.metadata["difficulty"] == "hard"
    assert case.metadata["version"] == 2


def test_eval_suite_model_stamped_on_results():
    """run() stamps the model name onto each EvalResult."""
    suite = EvalSuite("suite", ExactMatchEvaluator())
    suite.add_case(EvalCase(id="c1", prompt="", expected="ok"))
    results = suite.run("claude-3", {"c1": "ok"})
    assert results[0].model == "claude-3"


def test_eval_suite_results_method():
    """results() returns the list of EvalResults from the last run."""
    suite = EvalSuite("suite", ExactMatchEvaluator())
    suite.add_case(EvalCase(id="c1", prompt="", expected="ok"))
    suite.run("model", {"c1": "ok"})
    assert len(suite.results()) == 1
    assert suite.results()[0].case_id == "c1"


def test_eval_suite_empty_summary_before_run():
    """summary() before any run returns zero-valued dict."""
    suite = EvalSuite("empty", ExactMatchEvaluator())
    s = suite.summary()
    assert s["total"] == 0
    assert s["pass_rate"] == pytest.approx(0.0)
