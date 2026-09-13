# thegent-cli
# CLI entry point sub-project
# Extracted from main repo - Phase 2 P2.1

__version__ = "0.1.0"

from .commands import list_commands, main, run
from .parser import parse_args

__all__ = ["list_commands", "main", "parse_args", "run"]
