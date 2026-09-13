"""Tests for thegent.integrations.signed_audit_chain — Signed audit artifact chain.

@trace WL-232
"""

from __future__ import annotations

import hashlib

import orjson as json
import pytest

from thegent.integrations.signed_audit_chain import (
    AuditEntry,
    SignedAuditArtifactChain,
)


class TestAuditEntry:
    """Test AuditEntry dataclass. @trace WL-232"""

    @pytest.mark.requirement("WL-232")
    def test_create_entry(self) -> None:
        """Can create an AuditEntry with all fields."""
        entry = AuditEntry(
            entry_id="entry_001",
            data={"action": "update", "resource": "config"},
            signature="abc123",
            prev_signature="def456",
        )

        assert entry.entry_id == "entry_001"
        assert entry.data == {"action": "update", "resource": "config"}
        assert entry.signature == "abc123"
        assert entry.prev_signature == "def456"

    @pytest.mark.requirement("WL-232")
    def test_create_entry_default_prev_signature(self) -> None:
        """Can create an AuditEntry with default prev_signature."""
        entry = AuditEntry(entry_id="entry_001", data={"action": "create"}, signature="abc123")

        assert entry.entry_id == "entry_001"
        assert entry.prev_signature == ""


class TestSignedAuditArtifactChain:
    """Test SignedAuditArtifactChain operations. @trace WL-232"""

    @pytest.fixture
    def chain(self) -> SignedAuditArtifactChain:
        """Provide a fresh chain."""
        return SignedAuditArtifactChain()

    @pytest.mark.requirement("WL-232")
    def test_append_entry(self, chain: SignedAuditArtifactChain) -> None:
        """Can append an entry to the chain."""
        result = chain.append("entry_001", {"action": "create"})

        assert result.entry_id == "entry_001"
        assert result.data == {"action": "create"}
        assert result.signature != ""
        assert result.prev_signature == ""

    @pytest.mark.requirement("WL-232")
    def test_signature_computation(self, chain: SignedAuditArtifactChain) -> None:
        """Signature is computed correctly for first entry."""
        entry = chain.append("entry_001", {"action": "create"})

        # For first entry, prev_signature is empty
        expected_input = f":{entry.entry_id}:{json.dumps(entry.data, sort_keys=True).decode()}"
        expected_signature = hashlib.sha256(expected_input.encode()).hexdigest()

        assert entry.signature == expected_signature

    @pytest.mark.requirement("WL-232")
    def test_chained_signature(self, chain: SignedAuditArtifactChain) -> None:
        """Subsequent entries include previous signature in computation."""
        entry1 = chain.append("entry_001", {"action": "create"})
        entry2 = chain.append("entry_002", {"action": "update"})

        # entry2 should include entry1's signature
        assert entry2.prev_signature == entry1.signature
        assert entry2.signature != entry1.signature

    @pytest.mark.requirement("WL-232")
    def test_verify_chain_empty(self, chain: SignedAuditArtifactChain) -> None:
        """verify_chain returns True for empty chain."""
        assert chain.verify_chain() is True

    @pytest.mark.requirement("WL-232")
    def test_verify_chain_single_entry(self, chain: SignedAuditArtifactChain) -> None:
        """verify_chain returns True for valid single-entry chain."""
        chain.append("entry_001", {"action": "create"})
        assert chain.verify_chain() is True

    @pytest.mark.requirement("WL-232")
    def test_verify_chain_multiple_entries(self, chain: SignedAuditArtifactChain) -> None:
        """verify_chain returns True for valid multi-entry chain."""
        chain.append("entry_001", {"action": "create"})
        chain.append("entry_002", {"action": "update"})
        chain.append("entry_003", {"action": "delete"})

        assert chain.verify_chain() is True

    @pytest.mark.requirement("WL-232")
    def test_verify_chain_tampered_data(self, chain: SignedAuditArtifactChain) -> None:
        """verify_chain detects tampered entry data."""
        chain.append("entry_001", {"action": "create"})
        chain.append("entry_002", {"action": "update"})

        # Tamper with the data of the first entry
        entries = chain.entries()
        entries[0].data = {"action": "deleted"}  # type: ignore

        assert chain.verify_chain() is False

    @pytest.mark.requirement("WL-232")
    def test_verify_chain_tampered_signature(self, chain: SignedAuditArtifactChain) -> None:
        """verify_chain detects tampered entry signature."""
        chain.append("entry_001", {"action": "create"})

        # Tamper with the signature
        entries = chain.entries()
        entries[0].signature = "deadbeef"  # type: ignore

        assert chain.verify_chain() is False

    @pytest.mark.requirement("WL-232")
    def test_verify_chain_broken_link(self, chain: SignedAuditArtifactChain) -> None:
        """verify_chain detects broken chain links."""
        chain.append("entry_001", {"action": "create"})
        chain.append("entry_002", {"action": "update"})

        # Break the chain link
        entries = chain.entries()
        entries[1].prev_signature = "broken"  # type: ignore

        assert chain.verify_chain() is False

    @pytest.mark.requirement("WL-232")
    def test_entries_empty_chain(self, chain: SignedAuditArtifactChain) -> None:
        """entries returns empty list for empty chain."""
        assert chain.entries() == []

    @pytest.mark.requirement("WL-232")
    def test_entries_returns_copy(self, chain: SignedAuditArtifactChain) -> None:
        """entries returns a copy, not the internal list."""
        chain.append("entry_001", {"action": "create"})

        entries = chain.entries()
        entries.pop()  # type: ignore

        # Original should still have the entry
        assert len(chain.entries()) == 1

    @pytest.mark.requirement("WL-232")
    def test_multiple_appends_preserve_order(self, chain: SignedAuditArtifactChain) -> None:
        """Multiple appends preserve entry order."""
        chain.append("entry_001", {"seq": 1})
        chain.append("entry_002", {"seq": 2})
        chain.append("entry_003", {"seq": 3})

        entries = chain.entries()
        assert [e.entry_id for e in entries] == ["entry_001", "entry_002", "entry_003"]

    @pytest.mark.requirement("WL-232")
    def test_complex_data_structures(self, chain: SignedAuditArtifactChain) -> None:
        """Chain handles complex nested data structures."""
        data = {
            "nested": {"deep": {"values": [1, 2, 3]}},
            "list": [{"a": 1}, {"b": 2}],
            "string": "test",
        }
        entry = chain.append("entry_001", data)

        assert entry.data == data
        assert chain.verify_chain() is True

    @pytest.mark.requirement("WL-232")
    def test_signature_deterministic(self, chain: SignedAuditArtifactChain) -> None:
        """Same data produces same signature (deterministic)."""
        entry1 = chain.append("entry_001", {"action": "create"})

        # Create a new chain with same data
        chain2 = SignedAuditArtifactChain()
        entry2 = chain2.append("entry_001", {"action": "create"})

        assert entry1.signature == entry2.signature
