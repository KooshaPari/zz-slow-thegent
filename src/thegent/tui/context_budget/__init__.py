"""Stub module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ContextBudget:
    """Budget for context usage."""

    max_tokens: int = 100000
    used_tokens: int = 0

    def remaining(self) -> int:
        """Get remaining budget."""
        return self.max_tokens - self.used_tokens


__all__ = ["ContextBudget", "context_budget_from_result", "context_budget_indicator"]


def context_budget_from_result(result: dict[str, Any]) -> ContextBudget:
    """Create a context budget from a result dictionary."""
    max_tokens = result.get("max_tokens", 100000)
    used_tokens = result.get("used_tokens", 0)
    return ContextBudget(max_tokens=max_tokens, used_tokens=used_tokens)


def context_budget_indicator(budget: ContextBudget) -> str:
    """Generate a visual indicator for context budget usage."""
    percentage = (budget.used_tokens / budget.max_tokens) * 100 if budget.max_tokens > 0 else 0
    bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
    return f"[{bar}] {percentage:.1f}%"
