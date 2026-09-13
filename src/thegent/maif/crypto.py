"""STUB MODULE - thegent.maif.crypto

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

import hashlib


class SigningKey:
    """Stub signing key class."""

    def __init__(self, key_id: str = "") -> None:
        self.key_id = key_id

    def sign(self, data: bytes) -> bytes:
        """Sign data (stub)."""
        return data

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify signature (stub)."""
        return True


class VerifyingKey:
    """Stub verifying key class."""

    def __init__(self, key_id: str = "") -> None:
        self.key_id = key_id

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify signature (stub)."""
        return True


def hash_data(data: bytes) -> str:
    """Hash data using SHA-256."""
    return hashlib.sha256(data).hexdigest()


__all__ = ["SigningKey", "VerifyingKey", "hash_data"]
