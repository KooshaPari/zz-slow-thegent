"""Cliff - STUB."""


class CliffRunner:
    """CLI runner for cliff changelog generation."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def run(self, *args, **kwargs) -> int:
        """Run the cliff command."""
        return 0


class CliffGenerator:
    def __init__(self, *args, **kwargs):
        pass

    def generate(self, *args, **kwargs) -> str:
        return ""


__all__ = ["CliffGenerator", "CliffRunner"]
