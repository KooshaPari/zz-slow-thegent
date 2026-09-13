"""Circuit breaker module for resilience (AUDIT-N+39 hardened).

Each circuit breaker is a small JSON file under
``<root>/.circuits/<circuit_name>.json`` carrying the current
failure count and the ``opened_at`` ISO-8601 timestamp. A circuit is
considered open once its count meets or exceeds the configured
threshold (default 3).

The persistence layer is intentionally simple (no Redis, no locks):
the file is rewritten atomically on every state change so a single
writer is enough for the dormant-cluster contract.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "DEFAULT_THRESHOLD",
    "is_open",
    "record_failure",
    "record_success",
    "should_allow",
]


DEFAULT_THRESHOLD = 3


@dataclass(frozen=True)
class CircuitState:
    """Persisted circuit breaker state.

    @trace FR-RES-001
    """

    circuit_name: str
    count: int
    threshold: int
    opened_at: str  # ISO-8601 UTC

    def to_dict(self) -> dict[str, Any]:
        return {
            "circuit_name": self.circuit_name,
            "count": self.count,
            "threshold": self.threshold,
            "opened_at": self.opened_at,
        }


class CircuitBreaker:
    """Object-style API for the same persistence layer."""

    def __init__(
        self, root: Path, circuit_name: str, threshold: int = DEFAULT_THRESHOLD
    ) -> None:
        self.root = Path(root)
        self.circuit_name = circuit_name
        self.threshold = threshold

    @property
    def _state_file(self) -> Path:
        return self.root / ".circuits" / f"{self.circuit_name}.json"

    def _load(self) -> CircuitState | None:
        if not self._state_file.exists():
            return None
        try:
            data = json.loads(self._state_file.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        return CircuitState(
            circuit_name=data.get("circuit_name", self.circuit_name),
            count=int(data.get("count", 0)),
            threshold=int(data.get("threshold", self.threshold)),
            opened_at=str(data.get("opened_at", "")),
        )

    def _save(self, state: CircuitState) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write: tmp file + rename
        fd, tmp = tempfile.mkstemp(
            dir=self._state_file.parent, prefix=".cb_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(state.to_dict(), f)
            os.replace(tmp, self._state_file)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise

    def is_open(self) -> bool:
        state = self._load()
        return state is not None and state.count >= state.threshold

    def should_allow(self) -> bool:
        return not self.is_open()

    def record_failure(self) -> CircuitState:
        current = self._load()
        count = (current.count if current else 0) + 1
        opened_at = current.opened_at if current and current.opened_at else _now_iso()
        new_state = CircuitState(
            circuit_name=self.circuit_name,
            count=count,
            threshold=self.threshold,
            opened_at=opened_at,
        )
        self._save(new_state)
        return new_state

    def record_success(self) -> CircuitState | None:
        current = self._load()
        if current is None:
            return None
        if current.count == 0 and not current.opened_at:
            return current
        cleared = CircuitState(
            circuit_name=self.circuit_name,
            count=0,
            threshold=self.threshold,
            opened_at="",
        )
        self._save(cleared)
        return cleared


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_state(root: Path, circuit_name: str, threshold: int) -> CircuitState:
    """Read or initialise a CircuitState from disk."""
    cb = CircuitBreaker(root, circuit_name, threshold=threshold)
    state = cb._load()  # noqa: SLF001 -- private but stable
    if state is not None:
        return state
    return CircuitState(
        circuit_name=circuit_name,
        count=0,
        threshold=threshold,
        opened_at="",
    )


def _save_state(root: Path, state: CircuitState) -> None:
    cb = CircuitBreaker(root, state.circuit_name, threshold=state.threshold)
    cb._save(state)  # noqa: SLF001 -- private but stable


def is_open(root: Path, circuit_name: str, threshold: int = DEFAULT_THRESHOLD) -> bool:
    """Return ``True`` if the named circuit is currently open."""
    state = _load_state(root, circuit_name, threshold)
    return state.count >= state.threshold


def should_allow(
    root: Path, circuit_name: str, threshold: int = DEFAULT_THRESHOLD
) -> bool:
    """Return ``True`` if calls through the named circuit should proceed."""
    return not is_open(root, circuit_name, threshold=threshold)


def record_failure(
    root: Path, circuit_name: str, threshold: int = DEFAULT_THRESHOLD
) -> CircuitState:
    """Increment the failure counter for the named circuit and persist it."""
    state = _load_state(root, circuit_name, threshold)
    new_state = CircuitState(
        circuit_name=circuit_name,
        count=state.count + 1,
        threshold=threshold,
        opened_at=state.opened_at or _now_iso(),
    )
    _save_state(root, new_state)
    return new_state


def record_success(
    root: Path, circuit_name: str, threshold: int = DEFAULT_THRESHOLD
) -> CircuitState | None:
    """Reset the failure counter for the named circuit."""
    state = _load_state(root, circuit_name, threshold)
    if state.count == 0 and not state.opened_at:
        return state
    cleared = CircuitState(
        circuit_name=circuit_name,
        count=0,
        threshold=threshold,
        opened_at="",
    )
    _save_state(root, cleared)
    return cleared
