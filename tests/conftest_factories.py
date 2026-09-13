"""Test factories for thegent data types.

Provides factory functions that create instances with sensible defaults,
allowing tests to override only the fields they care about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def make_run_result(
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    timed_out: bool = False,
) -> Any:
    """Create a RunResult with defaults."""
    from thegent.agents.base import RunResult

    return RunResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
    )


def make_run_meta(
    agent: str = "test-agent",
    prompt: str = "test prompt",
    cwd: str = "/tmp/test",
    owner: str = "test-owner",
    **overrides: Any,
) -> Any:
    """Create a RunMeta with defaults."""
    from thegent.execution import RunMeta

    return RunMeta(agent=agent, prompt=prompt, cwd=cwd, owner=owner, **overrides)


def make_csm(
    task_id: str = "test-task",
    run_id: str = "test-run",
    status: str = "PENDING",
    phase: str = "UNKNOWN",
    progress: float = 0.0,
    **overrides: Any,
) -> Any:
    """Create a CanonicalStructuredMessage with defaults."""
    from thegent.contracts.csm.v1 import CanonicalStructuredMessage, CSMPhase, CSMStatus

    status_enum = CSMStatus[status] if isinstance(status, str) else status
    phase_enum = CSMPhase[phase] if isinstance(phase, str) else phase
    return CanonicalStructuredMessage(
        task_id=task_id,
        run_id=run_id,
        status=status_enum,
        phase=phase_enum,
        progress=progress,
        **overrides,
    )


def make_adapter_result(
    csm: Any | None = None,
    confidence: float = 1.0,
    parse_errors: list[str] | None = None,
    source_provider: str = "test-provider",
) -> Any:
    """Create an AdapterResult with defaults."""
    from thegent.contracts.adapters import AdapterResult

    resolved_csm = csm if csm is not None else make_csm()
    return AdapterResult(
        csm=resolved_csm,
        confidence=confidence,
        parse_errors=parse_errors or [],
        source_provider=source_provider,
    )


def make_fallback_policy(
    allow_plain_fallback: bool = True,
    min_confidence_threshold: float = 0.4,
    max_fallback_rate: float = 0.3,
    strict_providers: list[str] | None = None,
) -> Any:
    """Create a FallbackPolicy with defaults."""
    from thegent.contracts.policy import FallbackPolicy

    return FallbackPolicy(
        allow_plain_fallback=allow_plain_fallback,
        min_confidence_threshold=min_confidence_threshold,
        max_fallback_rate=max_fallback_rate,
        strict_providers=strict_providers or [],
    )


def make_route(
    provider: str = "claude",
    backend_type: str = "direct",  # type: ignore[assignment] -- Literal["direct","proxy"] in Route
    model_alias: str = "claude-sonnet-4-5-20250929",
    priority: int = 0,
    cost_weight: float = 1.0,
) -> Any:
    """Create a Route with defaults."""
    from thegent.models.catalog import Route

    return Route(
        provider=provider,
        backend_type=backend_type,
        model_alias=model_alias,
        priority=priority,
        cost_weight=cost_weight,
    )


def make_checkpoint_meta(
    reason: str = "test checkpoint",
    dag_content: str = "node1 -> node2",
    session_dir: str = "/tmp/test-session",
    owner: str = "test-owner",
) -> Any:
    """Create a CheckpointMeta with defaults."""
    from thegent.execution import CheckpointMeta

    return CheckpointMeta(
        reason=reason,
        dag_content=dag_content,
        session_dir=session_dir,
        owner=owner,
    )


@dataclass
class MockRunner:
    """Mock agent runner for testing."""

    results: list[Any] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)
    _call_index: int = 0

    def add_result(self, result: Any) -> None:
        self.results.append(result)

    async def run(
        self,
        prompt: str,
        cwd: Any = None,
        mode: str = "write",
        timeout: int = 90,
        **kwargs: Any,
    ) -> Any:
        self.calls.append({"prompt": prompt, "cwd": cwd, "mode": mode, "timeout": timeout, **kwargs})
        if self._call_index < len(self.results):
            result = self.results[self._call_index]
            self._call_index += 1
            return result
        return make_run_result()

    def run_sync(
        self,
        prompt: str,
        cwd: Any = None,
        mode: str = "write",
        timeout: int = 90,
        **kwargs: Any,
    ) -> Any:
        self.calls.append({"prompt": prompt, "cwd": cwd, "mode": mode, "timeout": timeout, **kwargs})
        if self._call_index < len(self.results):
            result = self.results[self._call_index]
            self._call_index += 1
            return result
        return make_run_result()
