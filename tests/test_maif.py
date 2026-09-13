"""Tests for MAIF action artifacts."""

import tempfile
from pathlib import Path

from thegent.maif.artifacts import (
    MAIFArtifact,
    generate_key_pair,
    sign_artifact,
    verify_artifact,
)
from thegent.maif.manager import MAIFManager
from thegent.maif.store import MAIFArtifactStore


def test_artifact_signing_and_verification():
    private_key, _public_key = generate_key_pair()

    artifact = MAIFArtifact(
        action_type="tool_use",
        payload={"tool": "ls", "args": ["."]},
        agent_id="test-agent",
        session_id="test-session",
    )

    # Initial artifact has no signature
    assert artifact.signature is None
    assert verify_artifact(artifact, private_key) is False

    # Sign it
    signature = sign_artifact(artifact, private_key)
    assert artifact.signature == signature
    assert len(signature) > 0

    # Verify it
    assert verify_artifact(artifact, private_key) is True

    # Tamper with payload
    artifact.payload["tool"] = "rm"
    assert verify_artifact(artifact, private_key) is False


def test_artifact_store():
    with tempfile.NamedTemporaryFile() as tmp:
        db_path = Path(tmp.name)
        store = MAIFArtifactStore(db_path)

        artifact = MAIFArtifact(
            action_type="mcp_call",
            payload={"server": "test-server", "tool": "test-tool"},
            agent_id="test-agent",
            session_id="session-123",
        )

        store.store(artifact)

        # Retrieve by ID
        retrieved = store.get(artifact.artifact_id)
        assert retrieved is not None
        assert retrieved.artifact_id == artifact.artifact_id
        assert retrieved.payload == artifact.payload
        assert retrieved.session_id == "session-123"

        # List by session
        session_artifacts = store.list_by_session("session-123")
        assert len(session_artifacts) == 1
        assert session_artifacts[0].artifact_id == artifact.artifact_id

        # List for unknown session
        assert len(store.list_by_session("unknown")) == 0


def test_maif_manager():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "maif.db"
        manager = MAIFManager(db_path)

        # Create artifact (auto-loads/generates keys)
        artifact = manager.create_artifact(
            action_type="decision",
            payload={"choice": "A", "reason": "better performance"},
            agent_id="test-agent",
            session_id="session-456",
        )

        assert artifact.signature is not None
        assert artifact.artifact_id is not None

        # Verify
        assert manager.verify(artifact.artifact_id) is True

        # Session history
        history = manager.get_session_history("session-456")
        assert len(history) == 1
        assert history[0].artifact_id == artifact.artifact_id
