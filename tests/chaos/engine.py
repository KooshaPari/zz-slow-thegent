"""WP-Y3: Chaos engineering framework for resilience testing."""

import random
import time
from collections.abc import Callable
from typing import Any


class ChaosEngine:
    """Injects faults into the system for resilience testing."""

    def __init__(self, failure_rate: float = 0.0, latency_range: tuple[float, float] = (0.0, 0.0)) -> None:
        self.failure_rate = failure_rate
        self.latency_range = latency_range
        self.active = True

    def inject(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Wrap a function call with potential failure or latency."""
        if not self.active:
            return func(*args, **kwargs)

        # 1. Latency injection
        if self.latency_range[1] > 0:
            delay = random.uniform(self.latency_range[0], self.latency_range[1])
            time.sleep(delay)

        # 2. Failure injection
        if random.random() < self.failure_rate:
            raise RuntimeError("Chaos Engine injected failure")

        return func(*args, **kwargs)


def chaos_wrap_agent(agent_func: Callable[..., Any], engine: ChaosEngine) -> Callable[..., Any]:
    """Decorator to inject chaos into an agent runner."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return engine.inject(agent_func, *args, **kwargs)

    return wrapper
