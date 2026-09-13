"""Stub module."""

from dataclasses import dataclass


@dataclass
class HashChainValidator:
    """Validator for hash chains."""

    chain_id: str = ""

    def validate(self, block: dict) -> bool:
        """Validate a block in the chain."""
        return True


__all__ = ["HashChainValidator"]
