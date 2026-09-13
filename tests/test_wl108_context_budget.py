"""Tests for WL-108 ContextBudget indicator module.

# @trace WL-108
"""

from __future__ import annotations

import pytest

from thegent.agents.base import RunResult
from thegent.tui.context_budget import (
    ContextBudget,
    context_budget_from_result,
    context_budget_indicator,
)

# ---------------------------------------------------------------------------
# ContextBudget.ratio
# ---------------------------------------------------------------------------


def test_ratio_is_fraction_of_used_over_max() -> None:
    """# @trace WL-108 — ratio = used / max."""
    budget = ContextBudget(used=400, max=1000)
    assert budget.ratio == pytest.approx(0.4)


def test_ratio_at_full_capacity() -> None:
    """# @trace WL-108 — ratio == 1.0 when used == max."""
    budget = ContextBudget(used=1000, max=1000)
    assert budget.ratio == pytest.approx(1.0)


def test_ratio_raises_when_max_is_zero() -> None:
    """# @trace WL-108 — max=0 is an invalid state; must raise ValueError."""
    budget = ContextBudget(used=10, max=0)
    with pytest.raises(ValueError, match="context max must be > 0"):
        _ = budget.ratio


# ---------------------------------------------------------------------------
# ContextBudget.color
# ---------------------------------------------------------------------------


def test_color_green_below_60_percent() -> None:
    """# @trace WL-108 — ratio < 0.60 → green."""
    budget = ContextBudget(used=500, max=1000)  # 50%
    assert budget.color == "green"


def test_color_yellow_at_60_percent() -> None:
    """# @trace WL-108 — ratio == 0.60 → yellow (boundary)."""
    budget = ContextBudget(used=600, max=1000)  # exactly 60%
    assert budget.color == "yellow"


def test_color_yellow_between_60_and_80() -> None:
    """# @trace WL-108 — 0.60 <= ratio < 0.80 → yellow."""
    budget = ContextBudget(used=700, max=1000)  # 70%
    assert budget.color == "yellow"


def test_color_red_at_80_percent() -> None:
    """# @trace WL-108 — ratio == 0.80 → red (boundary)."""
    budget = ContextBudget(used=800, max=1000)  # exactly 80%
    assert budget.color == "red"


def test_color_red_above_80_percent() -> None:
    """# @trace WL-108 — ratio > 0.80 → red."""
    budget = ContextBudget(used=950, max=1000)  # 95%
    assert budget.color == "red"


# ---------------------------------------------------------------------------
# ContextBudget.format_bar
# ---------------------------------------------------------------------------


def test_format_bar_plain_contains_ctx_prefix() -> None:
    """# @trace WL-108 — plain format_bar wraps output in [CTX: ...] brackets."""
    budget = ContextBudget(used=12_000, max=128_000)
    bar = budget.format_bar(ansi=False)
    assert bar == "[CTX: 12k/128k]"


def test_format_bar_ansi_contains_escape_codes() -> None:
    """# @trace WL-108 — ANSI format_bar wraps text in color escapes + reset."""
    budget = ContextBudget(used=500, max=1000)  # 50% → green
    bar = budget.format_bar(ansi=True)
    assert "\033[32m" in bar  # green open
    assert "\033[0m" in bar  # reset close
    assert "[CTX: " in bar


def test_format_bar_ansi_yellow() -> None:
    """# @trace WL-108 — 70% usage produces yellow ANSI code."""
    budget = ContextBudget(used=700, max=1000)
    bar = budget.format_bar(ansi=True)
    assert "\033[33m" in bar  # yellow


def test_format_bar_ansi_red() -> None:
    """# @trace WL-108 — 85% usage produces red ANSI code."""
    budget = ContextBudget(used=850, max=1000)
    bar = budget.format_bar(ansi=True)
    assert "\033[31m" in bar  # red


def test_format_bar_small_values_no_k_suffix() -> None:
    """# @trace WL-108 — values below 1000 render without 'k' suffix."""
    budget = ContextBudget(used=50, max=100)
    bar = budget.format_bar(ansi=False)
    assert bar == "[CTX: 50/100]"


# ---------------------------------------------------------------------------
# context_budget_from_result
# ---------------------------------------------------------------------------


def test_from_result_returns_budget_when_fields_present() -> None:
    """# @trace WL-108 — builds ContextBudget from RunResult with token data."""
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=12_000,
        context_window_max=128_000,
    )
    budget = context_budget_from_result(result)
    assert budget is not None
    assert budget.used == 12_000
    assert budget.max == 128_000


def test_from_result_returns_none_when_used_is_none() -> None:
    """# @trace WL-108 — missing context_tokens_used → None."""
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=None,
        context_window_max=128_000,
    )
    assert context_budget_from_result(result) is None


def test_from_result_returns_none_when_used_is_negative() -> None:
    """# @trace WL-108 — negative context_tokens_used is invalid → None."""
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=-1,
        context_window_max=128_000,
    )
    assert context_budget_from_result(result) is None


def test_from_result_returns_none_when_max_is_none() -> None:
    """# @trace WL-108 — missing context_window_max → None."""
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=1000,
        context_window_max=None,
    )
    assert context_budget_from_result(result) is None


def test_from_result_returns_none_when_max_is_zero() -> None:
    """# @trace WL-108 — context_window_max=0 is invalid → None."""
    result = RunResult(
        exit_code=0,
        stdout="ok",
        stderr="",
        context_tokens_used=100,
        context_window_max=0,
    )
    assert context_budget_from_result(result) is None


# ---------------------------------------------------------------------------
# context_budget_indicator
# ---------------------------------------------------------------------------


def test_indicator_returns_none_when_no_token_data() -> None:
    """# @trace WL-108 — no context data → indicator returns None."""
    result = RunResult(exit_code=0, stdout="", stderr="")
    assert context_budget_indicator(result) is None


def test_indicator_returns_ansi_string_when_data_present() -> None:
    """# @trace WL-108 — with token data, indicator returns colored [CTX: ...] string."""
    result = RunResult(
        exit_code=0,
        stdout="",
        stderr="",
        context_tokens_used=64_000,
        context_window_max=128_000,
    )
    bar = context_budget_indicator(result, ansi=True)
    assert bar is not None
    assert "[CTX: " in bar
    assert "\033[" in bar  # some ANSI code present


def test_indicator_plain_text_no_ansi() -> None:
    """# @trace WL-108 — ansi=False returns bracket string with no escape codes."""
    result = RunResult(
        exit_code=0,
        stdout="",
        stderr="",
        context_tokens_used=64_000,
        context_window_max=128_000,
    )
    bar = context_budget_indicator(result, ansi=False)
    assert bar is not None
    assert "\033[" not in bar
    assert bar == "[CTX: 64k/128k]"
