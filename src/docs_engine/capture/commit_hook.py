"""Commit hook - STUB."""

from __future__ import annotations

from typing import Any


class CommitHook:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        return {"status": "ok"}


def write_worklog_entry(message: str, metadata: dict[str, Any] | None = None) -> bool:
    """Write a worklog entry for a commit."""
    return True


__all__ = ["CommitHook", "write_worklog_entry"]
