"""Tests for WL-226: Remote Payload Checksums.

Verifies SHA256 checksum computation, storage, and verification for payload integrity.

# @trace WL-226
"""

from __future__ import annotations

import hashlib

import orjson as json
import pytest


@pytest.mark.requirement("WL-226")
class TestRemotePayloadChecksumVerifier:
    """WL-226: Remote payload checksum verification for integrity."""

    def test_checksum_record_dataclass_structure(self):
        """# @trace WL-226 — ChecksumRecord has required fields."""
        from thegent.integrations.payload_checksum import ChecksumRecord

        record = ChecksumRecord(payload_id="test_id", checksum="abc123")
        assert record.payload_id == "test_id"
        assert record.checksum == "abc123"

    def test_compute_returns_checksum_record(self):
        """# @trace WL-226 — compute() returns ChecksumRecord."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {"key": "value"}
        record = verifier.compute("payload_1", data)

        assert record.payload_id == "payload_1"
        assert isinstance(record.checksum, str)
        assert len(record.checksum) == 64  # SHA256 hex is 64 chars

    def test_compute_consistent_hash(self):
        """# @trace WL-226 — compute() produces consistent hash."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {"key": "value"}

        record1 = verifier.compute("payload_1", data)
        record2 = verifier.compute("payload_1", data)

        assert record1.checksum == record2.checksum

    def test_compute_different_data_different_hash(self):
        """# @trace WL-226 — compute() produces different hash for different data."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}

        record1 = verifier.compute("payload_1", data1)
        record2 = verifier.compute("payload_1", data2)

        assert record1.checksum != record2.checksum

    def test_compute_hash_independent_of_key_order(self):
        """# @trace WL-226 — compute() uses sort_keys=True for consistent hashing."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}

        record1 = verifier.compute("payload_1", data1)
        record2 = verifier.compute("payload_1", data2)

        assert record1.checksum == record2.checksum

    def test_compute_sha256_validation(self):
        """# @trace WL-226 — compute() produces valid SHA256 checksum."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {"key": "value"}
        record = verifier.compute("payload_1", data)

        expected_hash = hashlib.sha256(json.dumps(data, sort_keys=True).decode().encode("utf-8")).hexdigest()

        assert record.checksum == expected_hash

    def test_store_saves_record(self):
        """# @trace WL-226 — store() saves a checksum record."""
        from thegent.integrations.payload_checksum import (
            ChecksumRecord,
            RemotePayloadChecksumVerifier,
        )

        verifier = RemotePayloadChecksumVerifier()
        record = ChecksumRecord(payload_id="payload_1", checksum="abc123")
        verifier.store(record)

        retrieved = verifier.get("payload_1")
        assert retrieved.payload_id == "payload_1"
        assert retrieved.checksum == "abc123"

    def test_get_raises_keyerror_for_nonexistent(self):
        """# @trace WL-226 — get() raises KeyError for nonexistent payload."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()

        with pytest.raises(KeyError, match="not found"):
            verifier.get("nonexistent")

    def test_get_returns_stored_record(self):
        """# @trace WL-226 — get() returns the stored record."""
        from thegent.integrations.payload_checksum import (
            ChecksumRecord,
            RemotePayloadChecksumVerifier,
        )

        verifier = RemotePayloadChecksumVerifier()
        original = ChecksumRecord(payload_id="test", checksum="hash123")
        verifier.store(original)

        retrieved = verifier.get("test")
        assert retrieved.payload_id == original.payload_id
        assert retrieved.checksum == original.checksum

    def test_verify_returns_true_for_matching_data(self):
        """# @trace WL-226 — verify() returns True when checksums match."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {"key": "value"}

        record = verifier.compute("payload_1", data)
        verifier.store(record)

        assert verifier.verify("payload_1", data) is True

    def test_verify_returns_false_for_mismatched_data(self):
        """# @trace WL-226 — verify() returns False when data doesn't match."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        original_data = {"key": "value1"}
        modified_data = {"key": "value2"}

        record = verifier.compute("payload_1", original_data)
        verifier.store(record)

        assert verifier.verify("payload_1", modified_data) is False

    def test_verify_returns_false_for_nonexistent_payload(self):
        """# @trace WL-226 — verify() returns False for nonexistent payload."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {"key": "value"}

        assert verifier.verify("nonexistent", data) is False

    def test_verify_empty_dict(self):
        """# @trace WL-226 — verify() works with empty dictionaries."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        empty_data = {}

        record = verifier.compute("payload_1", empty_data)
        verifier.store(record)

        assert verifier.verify("payload_1", empty_data) is True
        assert verifier.verify("payload_1", {"key": "value"}) is False

    def test_verify_complex_nested_data(self):
        """# @trace WL-226 — verify() handles complex nested data."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            "metadata": {"version": "1.0", "timestamp": "2026-02-22"},
        }

        record = verifier.compute("payload_1", data)
        verifier.store(record)

        assert verifier.verify("payload_1", data) is True

    def test_multiple_payloads_independent(self):
        """# @trace WL-226 — multiple payloads are stored independently."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()

        data1 = {"id": 1}
        data2 = {"id": 2}

        record1 = verifier.compute("payload_1", data1)
        record2 = verifier.compute("payload_2", data2)

        verifier.store(record1)
        verifier.store(record2)

        assert verifier.verify("payload_1", data1) is True
        assert verifier.verify("payload_2", data2) is True
        assert verifier.verify("payload_1", data2) is False
        assert verifier.verify("payload_2", data1) is False

    def test_store_overwrites_previous(self):
        """# @trace WL-226 — store() overwrites previous record for same payload."""
        from thegent.integrations.payload_checksum import (
            ChecksumRecord,
            RemotePayloadChecksumVerifier,
        )

        verifier = RemotePayloadChecksumVerifier()

        record1 = ChecksumRecord(payload_id="payload_1", checksum="hash1")
        record2 = ChecksumRecord(payload_id="payload_1", checksum="hash2")

        verifier.store(record1)
        verifier.store(record2)

        retrieved = verifier.get("payload_1")
        assert retrieved.checksum == "hash2"

    def test_compute_with_special_characters(self):
        """# @trace WL-226 — compute() handles special characters in data."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {"text": "Hello 世界 🚀", "emoji": "🎉", "unicode": "café"}

        record = verifier.compute("payload_1", data)
        assert isinstance(record.checksum, str)
        assert len(record.checksum) == 64

    def test_compute_with_numeric_values(self):
        """# @trace WL-226 — compute() handles various numeric types."""
        from thegent.integrations.payload_checksum import RemotePayloadChecksumVerifier

        verifier = RemotePayloadChecksumVerifier()
        data = {"int": 42, "float": 3.14, "negative": -100, "zero": 0}

        record = verifier.compute("payload_1", data)
        verifier.store(record)
        assert verifier.verify("payload_1", data) is True

    def test_checksum_record_immutability(self):
        """# @trace WL-226 — ChecksumRecord can be modified after creation."""
        from thegent.integrations.payload_checksum import ChecksumRecord

        record = ChecksumRecord(payload_id="test", checksum="hash1")
        original_checksum = record.checksum

        record.payload_id = "modified"
        assert record.checksum == original_checksum
