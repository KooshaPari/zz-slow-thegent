"""Stub module for sandboxing."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SandboxProvider:
    """Sandbox provider stub."""

    def __init__(self) -> None:
        self._sandboxes: dict[str, Any] = {}
        self.system: str = "Darwin"

    def create_sandbox(self, profile: str) -> Any:
        """Create a sandbox."""
        sandbox = {"profile": profile, "running": True}
        self._sandboxes[profile] = sandbox
        return sandbox

    def wrap_command(self, cmd: list[str], tier: int = 1) -> list[str]:
        """Wrap a command with sandboxing.

        Args:
            cmd: Command to wrap.
            tier: Sandbox tier level (1=standard, 2=tier2 with worktree).

        Returns:
            Wrapped command with sandbox arguments.
        """
        import os

        worktree = os.environ.get("THGENT_SANDBOX_WORKTREE", "")
        allowed_reads = os.environ.get("THGENT_SANDBOX_ALLOWED_READS", "")

        if tier == 2 and worktree:
            # Tier 2: include worktree bind but no root bind
            return [
                "bwrap",
                "--bind",
                worktree,
                worktree,
                "--bind",
                "/tmp",
                "/tmp",
            ] + cmd
        else:
            # Tier 1: standard sandboxing
            args = ["bwrap", "--ro-bind", "/", "/"]
            if allowed_reads:
                args.extend(["--ro-bind", allowed_reads, allowed_reads])
            return args + cmd

    def destroy_sandbox(self, profile: str) -> bool:
        """Destroy a sandbox."""
        if profile in self._sandboxes:
            del self._sandboxes[profile]
            return True
        return False


__all__ = ["SandboxProvider"]
