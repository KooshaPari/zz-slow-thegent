"""CLI - STUB."""

from dataclasses import dataclass

# Stub application instance
app = None


@dataclass
class ResearchCLI:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        pass


__all__ = ["app", "ResearchCLI"]
