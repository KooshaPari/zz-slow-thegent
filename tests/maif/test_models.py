"""Unit tests for MAIF data models.

Tests the ActionType enum and MAIFArtifact dataclass with validators.
"""

import hashlib
import uuid
from datetime import datetime

import orjson as json
import pytest

from thegent.maif.models import ActionType, MAIFArtifact


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_type_values(self):
        """Verify all ActionType enum values."""
        assert ActionType.WRITE.value == "write"
        assert ActionType.EDIT.value == "edit"
        assert ActionType.DELETE.value == "delete"
        assert ActionType.BASH.value == "bash"
        assert ActionType.CODE_CHANGE.value == "code_change"
        assert ActionType.DECISION.value == "decision"
        assert ActionType.TOOL_USE.value == "tool_use"
        assert ActionType.QUERY.value == "query"
        assert ActionType.OTHER.value == "other"

    def test_action_type_from_value(self):
        """Test creating ActionType from string value."""
        assert ActionType("write") == ActionType.WRITE
        assert ActionType("edit") == ActionType.EDIT


class TestMAIFArtifactCreation:
    """Tests for MAIFArtifact creation and basic validation."""

    def test_create_minimal_artifact(self):
        """Test creating a minimal valid artifact."""
        artifact_id = uuid.uuid4().hex
        timestamp = int(datetime.now().timestamp())
        input_hash = hashlib.sha256(b"input").hexdigest()
        output_hash = hashlib.sha256(b"output").hexdigest()

        artifact = MAIFArtifact(
            id=artifact_id,
            timestamp=timestamp,
            action_type=ActionType.WRITE,
            agent_id="test-agent",
            session_id="session-123",
            input_hash=input_hash,
            output_hash=output_hash,
        )

        assert artifact.id == artifact_id
        assert artifact.timestamp == timestamp
        assert artifact.action_type == ActionType.WRITE
        assert artifact.agent_id == "test-agent"
        assert artifact.session_id == "session-123"
        assert artifact.input_hash == input_hash
        assert artifact.output_hash == output_hash
        assert artifact.previous_hash == ""
        assert artifact.signature == ""
        assert artifact.metadata == {}

    def test_create_artifact_with_metadata(self):
        """Test creating artifact with metadata."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=int(datetime.now().timestamp()),
            action_type=ActionType.EDIT,
            agent_id="agent-1",
            session_id="session-1",
            input_hash=hashlib.sha256(b"before").hexdigest(),
            output_hash=hashlib.sha256(b"after").hexdigest(),
            metadata={"file": "src/main.py", "lines": 42},
        )

        assert artifact.metadata["file"] == "src/main.py"
        assert artifact.metadata["lines"] == 42


class TestMAIFArtifactValidation:
    """Tests for MAIFArtifact field validation."""

    def test_invalid_id_format(self):
        """Test that invalid ID format is rejected."""
        with pytest.raises(ValueError, match="Invalid artifact ID format"):
            MAIFArtifact(
                id="not-a-hex-string",
                timestamp=int(datetime.now().timestamp()),
                action_type=ActionType.WRITE,
                agent_id="agent",
                session_id="session",
                input_hash=hashlib.sha256(b"x").hexdigest(),
                output_hash=hashlib.sha256(b"y").hexdigest(),
            )

    def test_invalid_id_length(self):
        """Test that ID with wrong length is rejected."""
        with pytest.raises(ValueError, match="32-character hex string"):
            MAIFArtifact(
                id="abc123",  # Too short
                timestamp=int(datetime.now().timestamp()),
                action_type=ActionType.WRITE,
                agent_id="agent",
                session_id="session",
                input_hash=hashlib.sha256(b"x").hexdigest(),
                output_hash=hashlib.sha256(b"y").hexdigest(),
            )

    def test_invalid_timestamp(self):
        """Test that non-positive timestamp is rejected."""
        with pytest.raises(ValueError, match="Timestamp must be positive"):
            MAIFArtifact(
                id=uuid.uuid4().hex,
                timestamp=0,
                action_type=ActionType.WRITE,
                agent_id="agent",
                session_id="session",
                input_hash=hashlib.sha256(b"x").hexdigest(),
                output_hash=hashlib.sha256(b"y").hexdigest(),
            )

    def test_invalid_input_hash_format(self):
        """Test that invalid hash format is rejected."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            MAIFArtifact(
                id=uuid.uuid4().hex,
                timestamp=int(datetime.now().timestamp()),
                action_type=ActionType.WRITE,
                agent_id="agent",
                session_id="session",
                input_hash="not-a-hash",
                output_hash=hashlib.sha256(b"y").hexdigest(),
            )

    def test_invalid_hash_length(self):
        """Test that hash with wrong length is rejected."""
        with pytest.raises(ValueError, match="64-character hex string"):
            MAIFArtifact(
                id=uuid.uuid4().hex,
                timestamp=int(datetime.now().timestamp()),
                action_type=ActionType.WRITE,
                agent_id="agent",
                session_id="session",
                input_hash="abc123",  # Too short
                output_hash=hashlib.sha256(b"y").hexdigest(),
            )

    def test_invalid_signature_format(self):
        """Test that invalid signature is rejected."""
        with pytest.raises(ValueError, match="Invalid signature format"):
            MAIFArtifact(
                id=uuid.uuid4().hex,
                timestamp=int(datetime.now().timestamp()),
                action_type=ActionType.WRITE,
                agent_id="agent",
                session_id="session",
                input_hash=hashlib.sha256(b"x").hexdigest(),
                output_hash=hashlib.sha256(b"y").hexdigest(),
                signature="not-a-signature",
            )

    def test_empty_previous_hash_valid(self):
        """Test that empty previous_hash is valid (for first artifact)."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=int(datetime.now().timestamp()),
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            output_hash=hashlib.sha256(b"y").hexdigest(),
            previous_hash="",
        )
        assert artifact.previous_hash == ""

    def test_empty_signature_valid(self):
        """Test that empty signature is valid (before signing)."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=int(datetime.now().timestamp()),
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            output_hash=hashlib.sha256(b"y").hexdigest(),
            signature="",
        )
        assert artifact.signature == ""


class TestMAIFArtifactSerialization:
    """Tests for artifact serialization."""

    def test_serialize_for_signing(self):
        """Test deterministic serialization for signing."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_hash=hashlib.sha256(b"input").hexdigest(),
            output_hash=hashlib.sha256(b"output").hexdigest(),
        )

        serialized = artifact.serialize_for_signing()
        assert isinstance(serialized, bytes)

        # Should be valid JSON
        data = json.loads(serialized)
        assert data["agent_id"] == "agent-1"
        assert data["action_type"] == "write"  # Enum value, not object
        assert "signature" not in data  # Signature excluded

    def test_serialize_for_signing_deterministic(self):
        """Test that serialization is deterministic."""
        artifact1 = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.EDIT,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"a").hexdigest(),
            output_hash=hashlib.sha256(b"b").hexdigest(),
        )

        # Create identical artifact
        artifact2 = MAIFArtifact(
            id=artifact1.id,
            timestamp=artifact1.timestamp,
            action_type=ActionType.EDIT,
            agent_id="agent",
            session_id="session",
            input_hash=artifact1.input_hash,
            output_hash=artifact1.output_hash,
        )

        assert artifact1.serialize_for_signing() == artifact2.serialize_for_signing()

    def test_serialize_excludes_signature(self):
        """Test that signature is excluded from serialization."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            output_hash=hashlib.sha256(b"y").hexdigest(),
            signature="a" * 512,  # Dummy signature
        )

        serialized = artifact.serialize_for_signing()
        data = json.loads(serialized)
        assert "signature" not in data


class TestMAIFArtifactHashing:
    """Tests for artifact hashing."""

    def test_get_hash(self):
        """Test computing artifact hash."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"input").hexdigest(),
            output_hash=hashlib.sha256(b"output").hexdigest(),
        )

        artifact_hash = artifact.get_hash()
        assert isinstance(artifact_hash, str)
        assert len(artifact_hash) == 64  # SHA-256 hex string
        assert all(c in "0123456789abcdef" for c in artifact_hash)

    def test_get_hash_deterministic(self):
        """Test that hashing is deterministic."""
        artifact1 = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"input").hexdigest(),
            output_hash=hashlib.sha256(b"output").hexdigest(),
        )

        hash1 = artifact1.get_hash()
        hash2 = artifact1.get_hash()
        assert hash1 == hash2

    def test_hash_changes_with_artifact_content(self):
        """Test that hash changes when artifact content changes."""
        artifact1 = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"input").hexdigest(),
            output_hash=hashlib.sha256(b"output").hexdigest(),
        )

        artifact2 = MAIFArtifact(
            id=uuid.uuid4().hex,  # Different ID
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=artifact1.input_hash,
            output_hash=artifact1.output_hash,
        )

        assert artifact1.get_hash() != artifact2.get_hash()


class TestMAIFArtifactHashChain:
    """Tests for hash chain verification."""

    def test_verify_hash_chain_first_artifact(self):
        """Test that first artifact has no previous hash."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            output_hash=hashlib.sha256(b"y").hexdigest(),
            previous_hash="",
        )

        assert artifact.verify_hash_chain(None) is True

    def test_verify_hash_chain_linked_artifacts(self):
        """Test that linked artifacts verify correctly."""
        artifact1 = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            output_hash=hashlib.sha256(b"y").hexdigest(),
            previous_hash="",
        )

        hash1 = artifact1.get_hash()

        artifact2 = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000001,
            action_type=ActionType.EDIT,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"y").hexdigest(),
            output_hash=hashlib.sha256(b"z").hexdigest(),
            previous_hash=hash1,
        )

        assert artifact2.verify_hash_chain(artifact1) is True

    def test_verify_hash_chain_broken(self):
        """Test that broken chain fails verification."""
        artifact1 = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            output_hash=hashlib.sha256(b"y").hexdigest(),
            previous_hash="",
        )

        artifact2 = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000001,
            action_type=ActionType.EDIT,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"y").hexdigest(),
            output_hash=hashlib.sha256(b"z").hexdigest(),
            previous_hash="incorrect_hash",
        )

        assert artifact2.verify_hash_chain(artifact1) is False

    def test_verify_hash_chain_first_artifact_with_previous_hash(self):
        """Test that first artifact with previous_hash fails verification."""
        artifact = MAIFArtifact(
            id=uuid.uuid4().hex,
            timestamp=1000000,
            action_type=ActionType.WRITE,
            agent_id="agent",
            session_id="session",
            input_hash=hashlib.sha256(b"x").hexdigest(),
            output_hash=hashlib.sha256(b"y").hexdigest(),
            previous_hash=hashlib.sha256(b"dummy").hexdigest(),
        )

        assert artifact.verify_hash_chain(None) is False
