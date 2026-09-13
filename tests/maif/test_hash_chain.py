"""Unit tests for MAIF hash chain validator.

Tests the HashChainValidator class for chain verification and tamper detection.
"""

import hashlib

from thegent.maif.artifact_generator import MAIFArtifactGenerator
from thegent.maif.crypto import SigningKey
from thegent.maif.hash_chain import HashChainValidator
from thegent.maif.models import ActionType


class TestHashChainValidatorCreation:
    """Tests for hash chain validator creation."""

    def test_create_validator(self):
        """Test creating a hash chain validator."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        assert validator is not None
        assert validator.verifying_key is verifying_key
        assert validator.chain_heads == {}


class TestHashChainVerification:
    """Tests for hash chain verification."""

    def test_verify_empty_chain(self):
        """Test verifying an empty chain."""
        signing_key = SigningKey.generate()
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        is_valid, message = validator.verify_chain([])
        assert is_valid is True
        assert "empty" in message.lower()

    def test_verify_single_artifact_chain(self):
        """Test verifying a chain with a single artifact."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"input",
            output_data=b"output",
        )

        is_valid, message = validator.verify_chain([artifact])
        assert is_valid is True
        assert message == "OK"

    def test_verify_two_artifact_chain(self):
        """Test verifying a chain with two linked artifacts."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact1 = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        artifact2 = generator.create_artifact(
            action_type=ActionType.EDIT,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"y",
            output_data=b"z",
        )

        is_valid, message = validator.verify_chain([artifact1, artifact2])
        assert is_valid is True
        assert message == "OK"

    def test_verify_long_chain(self):
        """Test verifying a longer chain."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifacts = []
        for i in range(10):
            artifact = generator.create_artifact(
                action_type=ActionType.WRITE,
                agent_id="agent-1",
                session_id="session-1",
                input_data=f"input-{i}".encode(),
                output_data=f"output-{i}".encode(),
            )
            artifacts.append(artifact)

        is_valid, message = validator.verify_chain(artifacts)
        assert is_valid is True
        assert message == "OK"


class TestHashChainTampering:
    """Tests for detecting chain tampering."""

    def test_detect_broken_hash_chain(self):
        """Test that broken hash chain is detected."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact1 = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        artifact2 = generator.create_artifact(
            action_type=ActionType.EDIT,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"y",
            output_data=b"z",
        )

        # Tamper with previous_hash
        artifact2.previous_hash = hashlib.sha256(b"fake").hexdigest()

        is_valid, message = validator.verify_chain([artifact1, artifact2])
        assert is_valid is False
        assert "hash chain broken" in message.lower()

    def test_detect_invalid_signature(self):
        """Test that invalid signature is detected."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        # Tamper with signature
        artifact.signature = "a" * 512  # All zeros

        is_valid, message = validator.verify_chain([artifact])
        assert is_valid is False
        assert "signature invalid" in message.lower()

    def test_detect_corrupted_artifact_data(self):
        """Test that corrupted artifact data breaks chain."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        # Tamper with artifact data (but keep signature for now)
        artifact.agent_id = "hacker"
        # Signature is now invalid because artifact was modified

        is_valid, _message = validator.verify_chain([artifact])
        assert is_valid is False

    def test_detect_different_sessions_in_chain(self):
        """Test that artifacts from different sessions are rejected."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact1 = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        artifact2 = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-2",
            input_data=b"a",
            output_data=b"b",
        )

        is_valid, message = validator.verify_chain([artifact1, artifact2])
        assert is_valid is False
        assert "different sessions" in message.lower()


class TestIndividualArtifactVerification:
    """Tests for verifying individual artifacts."""

    def test_verify_valid_artifact(self):
        """Test verifying a valid artifact."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        assert validator.verify_artifact(artifact) is True

    def test_verify_artifact_with_invalid_signature(self):
        """Test that artifact with invalid signature fails verification."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        # Tamper with signature
        artifact.signature = "b" * 512

        assert validator.verify_artifact(artifact) is False

    def test_verify_artifact_with_empty_signature(self):
        """Test that artifact with empty signature fails verification."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        # Clear signature
        artifact.signature = ""

        assert validator.verify_artifact(artifact) is False


class TestChainHeads:
    """Tests for chain head tracking."""

    def test_chain_head_after_verification(self):
        """Test that chain head is updated after verification."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        assert not validator.has_chain_head("session-1")

        validator.verify_chain([artifact])

        assert validator.has_chain_head("session-1")
        assert validator.get_chain_head("session-1") == artifact.get_hash()

    def test_chain_head_updated_with_longer_chain(self):
        """Test that chain head is updated with longer chain."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact1 = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        validator.verify_chain([artifact1])
        head1 = validator.get_chain_head("session-1")

        artifact2 = generator.create_artifact(
            action_type=ActionType.EDIT,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"y",
            output_data=b"z",
        )

        validator.verify_chain([artifact1, artifact2])
        head2 = validator.get_chain_head("session-1")

        assert head1 != head2
        assert head2 == artifact2.get_hash()

    def test_verify_chain_from_head(self):
        """Test verifying chain starting from known head."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact1 = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        validator.verify_chain([artifact1])

        # Create second artifact
        artifact2 = generator.create_artifact(
            action_type=ActionType.EDIT,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"y",
            output_data=b"z",
        )

        # Verify using chain head
        is_valid, _message = validator.verify_chain_from_head("session-1", [artifact2])
        assert is_valid is True

    def test_verify_chain_from_head_broken_link(self):
        """Test that broken link from head is detected."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact1 = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        validator.verify_chain([artifact1])

        # Create artifact that doesn't link to head
        artifact2 = generator.create_artifact(
            action_type=ActionType.EDIT,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"y",
            output_data=b"z",
        )

        # Tamper with previous_hash to break link
        artifact2.previous_hash = hashlib.sha256(b"fake").hexdigest()

        is_valid, message = validator.verify_chain_from_head("session-1", [artifact2])
        assert is_valid is False
        assert "doesn't link to known head" in message.lower()

    def test_reset_session(self):
        """Test resetting session chain head."""
        signing_key = SigningKey.generate()
        generator = MAIFArtifactGenerator(signing_key)
        verifying_key = signing_key.get_public_key()
        validator = HashChainValidator(verifying_key)

        artifact = generator.create_artifact(
            action_type=ActionType.WRITE,
            agent_id="agent-1",
            session_id="session-1",
            input_data=b"x",
            output_data=b"y",
        )

        validator.verify_chain([artifact])
        assert validator.has_chain_head("session-1")

        validator.reset_session("session-1")
        assert not validator.has_chain_head("session-1")
