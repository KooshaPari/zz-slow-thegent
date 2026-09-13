"""Application queries - CQRS query handlers."""

from dataclasses import dataclass


@dataclass
class GetLockQuery:
    """Query to get a specific lock."""
    cmd_hash: str


@dataclass
class ListLocksQuery:
    """Query to list all locks."""
    include_expired: bool = False


@dataclass
class GetQueueDepthQuery:
    """Query to get the queue depth."""
    priority: str | None = None


@dataclass
class GetMergeCandidatesQuery:
    """Query to get merge candidates."""
    base_branch: str | None = None
    min_conflicts: int = 0
