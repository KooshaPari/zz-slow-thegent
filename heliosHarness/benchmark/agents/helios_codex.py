#!/usr/bin/env python3
"""
Helios Agent Adapter for Harbor
================================

This module provides a Harbor-compatible agent wrapper for our custom codex binary.

Usage:
    harbor run -d terminal-bench-sample@2.0 -a helios-codex --agent-kwarg binary=/path/to/codex
"""

import os
import subprocess


class HeliosCodexAdapter:
    """Adapter for Helios codex binary"""

    def __init__(self, binary_path: str | None = None):
        self.binary = binary_path or os.environ.get("HELIOS_CODEX_BINARY", "codex")

    @property
    def name(self) -> str:
        return "helios-codex"

    @property
    def version(self) -> str:
        try:
            result = subprocess.run([self.binary, "--version"], capture_output=True, timeout=5)
            return result.stdout.decode() or "unknown"
        except:
            return "unknown"

    async def run(self, instruction: str, env, context, **kwargs):
        """Run the codex binary with instruction"""
        cmd = [self.binary, "exec", "--skip-git-repo-check", instruction]

        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.stdout.decode()
