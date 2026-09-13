"""Domain value objects - immutable objects defined by their attributes.

Value Object Principles:
- Immutable (no setters, create new instances)
- No identity (two VOs with same values are equal)
- Self-validating
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class CommandHash:
    """Immutable command hash for deduplication."""

    value: str
    algorithm: str = "sha256"

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)


@dataclass(frozen=True)
class TaskMetadata:
    """Immutable task metadata."""

    command: str
    cwd: str
    env: tuple[tuple[str, str], ...]
    timeout_seconds: int = 3600

    def with_timeout(self, seconds: int) -> "TaskMetadata":
        """Create new TaskMetadata with different timeout."""
        return TaskMetadata(
            command=self.command,
            cwd=self.cwd,
            env=self.env,
            timeout_seconds=seconds,
        )


@dataclass(frozen=True)
class MergeConflict:
    """Immutable merge conflict information."""

    file_path: str
    line_start: int
    line_end: int
    ours_content: str
    theirs_content: str

    @property
    def conflict_range(self) -> str:
        return f"{self.line_start}-{self.line_end}"


@dataclass(frozen=True)
class LockStatus:
    """Immutable lock status for command deduplication."""

    locked: bool
    pid: int | None = None
    acquired_at: datetime | None = None
    expires_at: datetime | None = None

    @classmethod
    def acquired(cls, pid: int, ttl_seconds: int = 3600) -> "LockStatus":
        """Create acquired lock status."""
        now = datetime.now()
        return cls(
            locked=True,
            pid=pid,
            acquired_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )

    @classmethod
    def released(cls) -> "LockStatus":
        """Create released lock status."""
        return cls(locked=False)

    def is_expired(self) -> bool:
        """Check if lock has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if lock is valid (acquired and not expired)."""
        return self.locked and not self.is_expired()


@dataclass(frozen=True)
class QueuePriority:
    """Immutable queue priority levels."""

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    value: str

    def __post_init__(self) -> None:
        if self.value not in (self.HIGH, self.NORMAL, self.LOW):
            raise ValueError(f"Invalid priority: {self.value}")

    @classmethod
    def high(cls) -> "QueuePriority":
        return cls(value=cls.HIGH)

    @classmethod
    def normal(cls) -> "QueuePriority":
        return cls(value=cls.NORMAL)

    @classmethod
    def low(cls) -> "QueuePriority":
        return cls(value=cls.LOW)


@dataclass(frozen=True)
class MergeStrategy:
    """Immutable merge strategy types."""

    AUTO = "auto"
    OURS = "ours"
    THEIRS = "theirs"
    MANUAL = "manual"
    value: str

    def __post_init__(self) -> None:
        if self.value not in (self.AUTO, self.OURS, self.THEIRS, self.MANUAL):
            raise ValueError(f"Invalid strategy: {self.value}")

    @classmethod
    def auto(cls) -> "MergeStrategy":
        return cls(value=cls.AUTO)

    @classmethod
    def ours(cls) -> "MergeStrategy":
        return cls(value=cls.OURS)

    @classmethod
    def theirs(cls) -> "MergeStrategy":
        return cls(value=cls.THEIRS)

    @classmethod
    def manual(cls) -> "MergeStrategy":
        return cls(value=cls.MANUAL)


@dataclass(frozen=True)
class HealthScore:
    """Health score for system monitoring."""

    overall: float
    components: tuple[tuple[str, float], ...]

    @classmethod
    def from_components(cls, **kwargs: float) -> "HealthScore":
        """Create health score from components."""
        components = tuple(kwargs.items())
        if not components:
            return cls(overall=1.0, components=())
        overall = sum(v for _, v in components) / len(components)
        return cls(overall=overall, components=components)

    def is_healthy(self) -> bool:
        return self.overall >= 0.8

    def is_degraded(self) -> bool:
        return 0.5 <= self.overall < 0.8

    def is_unhealthy(self) -> bool:
        return self.overall < 0.5
