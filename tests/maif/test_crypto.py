"""Unit tests for MAIF cryptographic functions.

Tests RSA-2048 signing and verification.
"""

import pytest

from thegent.maif.crypto import SigningKey, VerifyingKey, hash_data


class TestSigningKeyGeneration:
    """Tests for signing key generation."""

    def test_generate_signing_key(self):
        """Test generating a new signing key."""
        signing_key = SigningKey.generate()
        assert signing_key is not None
        assert signing_key.private_key is not None
        assert signing_key.public_key is not None

    def test_signing_key_has_public_key(self):
        """Test that signing key can generate public key."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()
        assert verifying_key is not None
        assert isinstance(verifying_key, VerifyingKey)

    def test_generate_different_keys(self):
        """Test that different invocations generate different keys."""
        key1 = SigningKey.generate()
        key2 = SigningKey.generate()
        # Keys should be different (PEM representation should differ)
        assert key1.to_pem() != key2.to_pem()


class TestSigningKeyPEM:
    """Tests for PEM serialization and deserialization."""

    def test_to_pem(self):
        """Test exporting signing key to PEM."""
        signing_key = SigningKey.generate()
        pem = signing_key.to_pem()
        assert isinstance(pem, bytes)
        assert b"-----BEGIN PRIVATE KEY-----" in pem
        assert b"-----END PRIVATE KEY-----" in pem

    def test_from_pem_roundtrip(self):
        """Test PEM export and reimport roundtrip."""
        signing_key1 = SigningKey.generate()
        pem = signing_key1.to_pem()

        signing_key2 = SigningKey.from_pem(pem)
        data = b"test data"

        # Both keys should produce valid signatures (PSS is non-deterministic, so we verify)
        sig1 = signing_key1.sign(data)
        sig2 = signing_key2.sign(data)

        verifying_key1 = signing_key1.get_public_key()
        verifying_key2 = signing_key2.get_public_key()

        assert verifying_key1.verify(data, sig1)
        assert verifying_key1.verify(data, sig2)
        assert verifying_key2.verify(data, sig1)
        assert verifying_key2.verify(data, sig2)

    def test_from_pem_invalid(self):
        """Test that invalid PEM raises ValueError."""
        with pytest.raises(ValueError, match="Failed to load signing key"):
            SigningKey.from_pem(b"not a valid pem")


class TestSigning:
    """Tests for signing data."""

    def test_sign_data(self):
        """Test signing data."""
        signing_key = SigningKey.generate()
        data = b"test data to sign"
        signature = signing_key.sign(data)

        assert isinstance(signature, bytes)
        assert len(signature) == 256  # RSA-2048 produces 256-byte signature

    def test_sign_empty_data(self):
        """Test signing empty data."""
        signing_key = SigningKey.generate()
        signature = signing_key.sign(b"")
        assert isinstance(signature, bytes)
        assert len(signature) == 256

    def test_sign_large_data(self):
        """Test signing large data."""
        signing_key = SigningKey.generate()
        large_data = b"x" * 100000  # 100KB
        signature = signing_key.sign(large_data)
        assert isinstance(signature, bytes)
        assert len(signature) == 256

    def test_sign_deterministic_for_verification(self):
        """Test that signatures are verifiable (though PSS is non-deterministic)."""
        signing_key = SigningKey.generate()
        data = b"test data"
        verifying_key = signing_key.get_public_key()

        # Multiple signatures should all verify correctly
        for _ in range(5):
            signature = signing_key.sign(data)
            assert verifying_key.verify(data, signature)


class TestVerifyingKeyPEM:
    """Tests for verifying key PEM operations."""

    def test_public_key_to_pem(self):
        """Test exporting public key to PEM."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()
        pem = verifying_key.to_pem()

        assert isinstance(pem, bytes)
        assert b"-----BEGIN PUBLIC KEY-----" in pem
        assert b"-----END PUBLIC KEY-----" in pem

    def test_public_key_from_pem_roundtrip(self):
        """Test public key PEM roundtrip."""
        signing_key = SigningKey.generate()
        verifying_key1 = signing_key.get_public_key()
        pem = verifying_key1.to_pem()

        verifying_key2 = VerifyingKey.from_pem(pem)

        # Both should verify the same signatures
        data = b"test data"
        signature = signing_key.sign(data)

        assert verifying_key1.verify(data, signature)
        assert verifying_key2.verify(data, signature)

    def test_public_key_from_pem_invalid(self):
        """Test that invalid PEM raises ValueError."""
        with pytest.raises(ValueError, match="Failed to load verifying key"):
            VerifyingKey.from_pem(b"not a valid pem")


class TestSignatureVerification:
    """Tests for signature verification."""

    def test_verify_valid_signature(self):
        """Test verifying a valid signature."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()

        data = b"test message"
        signature = signing_key.sign(data)

        assert verifying_key.verify(data, signature) is True

    def test_verify_invalid_signature(self):
        """Test that invalid signature fails verification."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()

        data = b"test message"
        # Create a wrong signature (all zeros)
        invalid_signature = b"\x00" * 256

        assert verifying_key.verify(data, invalid_signature) is False

    def test_verify_wrong_data(self):
        """Test that signature doesn't verify with different data."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()

        data1 = b"original message"
        data2 = b"different message"
        signature = signing_key.sign(data1)

        assert verifying_key.verify(data1, signature) is True
        assert verifying_key.verify(data2, signature) is False

    def test_verify_corrupted_signature(self):
        """Test that corrupted signature fails verification."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()

        data = b"test message"
        signature = signing_key.sign(data)

        # Corrupt the signature by flipping a bit
        corrupted = bytearray(signature)
        corrupted[0] ^= 1
        corrupted_signature = bytes(corrupted)

        assert verifying_key.verify(data, corrupted_signature) is False

    def test_verify_wrong_key(self):
        """Test that signature from one key doesn't verify with another."""
        key1 = SigningKey.generate()
        key2 = SigningKey.generate()

        data = b"test message"
        signature = key1.sign(data)
        verifying_key2 = key2.get_public_key()

        assert verifying_key2.verify(data, signature) is False

    def test_verify_empty_signature(self):
        """Test verification with empty signature fails."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()

        data = b"test message"
        assert verifying_key.verify(data, b"") is False


class TestHashFunction:
    """Tests for SHA-256 hashing."""

    def test_hash_data(self):
        """Test hashing data."""
        data = b"test data"
        result = hash_data(data)

        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex is 64 chars
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_deterministic(self):
        """Test that hashing is deterministic."""
        data = b"same data"
        hash1 = hash_data(data)
        hash2 = hash_data(data)
        assert hash1 == hash2

    def test_hash_different_data_different_hash(self):
        """Test that different data produces different hashes."""
        hash1 = hash_data(b"data1")
        hash2 = hash_data(b"data2")
        assert hash1 != hash2

    def test_hash_empty_data(self):
        """Test hashing empty data."""
        result = hash_data(b"")
        assert len(result) == 64
        # SHA-256 of empty string is a known value
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_hash_large_data(self):
        """Test hashing large data."""
        large_data = b"x" * 1000000  # 1MB
        result = hash_data(large_data)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


class TestSignAndVerifyRoundTrip:
    """Integration tests for complete sign and verify flow."""

    def test_sign_and_verify_simple_message(self):
        """Test complete sign and verify flow for a simple message."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()

        message = b"important message"
        signature = signing_key.sign(message)

        assert verifying_key.verify(message, signature) is True

    def test_sign_and_verify_with_pem_keys(self):
        """Test sign and verify using PEM-serialized keys."""
        # Generate and serialize
        signing_key1 = SigningKey.generate()
        signing_pem = signing_key1.to_pem()
        verifying_key1 = signing_key1.get_public_key()
        verifying_pem = verifying_key1.to_pem()

        # Deserialize
        signing_key2 = SigningKey.from_pem(signing_pem)
        verifying_key2 = VerifyingKey.from_pem(verifying_pem)

        # Sign and verify
        message = b"test message"
        signature = signing_key2.sign(message)
        assert verifying_key2.verify(message, signature) is True
        assert verifying_key1.verify(message, signature) is True

    def test_multiple_messages(self):
        """Test signing and verifying multiple different messages."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()

        messages = [
            b"message 1",
            b"message 2",
            b"message 3",
            b"",
            b"very long message " * 1000,
        ]

        for message in messages:
            signature = signing_key.sign(message)
            assert verifying_key.verify(message, signature) is True
