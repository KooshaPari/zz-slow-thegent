"""Unit tests for WP-3002: Signed action artifacts."""

from thegent.governance.signatures import (
    ArtifactSigner,
    generate_artifact_hash,
    sign_artifact,
    verify_signature,
)


def test_hash_consistency():
    """Hash should be consistent for the same data regardless of key order."""
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}
    assert generate_artifact_hash(data1) == generate_artifact_hash(data2)


def test_sign_and_verify():
    """Verify that a signature can be verified with the same key."""
    data = {"task": "test", "id": 123}
    key = "secret"
    sig = sign_artifact(data, key)
    assert verify_signature(data, sig, key) is True
    assert verify_signature(data, sig, "wrong-key") is False


def test_artifact_signer_envelope():
    """Test the ArtifactSigner class envelope creation and verification."""
    signer = ArtifactSigner()
    payload = {"run_id": "run-1", "action": "promote"}

    envelope = signer.create_signed_artifact("PROMOTION", payload)

    assert envelope["type"] == "PROMOTION"
    assert envelope["payload"] == payload
    assert "signature" in envelope
    assert "metadata" in envelope
    assert "hash" in envelope["metadata"]

    assert signer.verify_envelope(envelope) is True

    # Tamper with payload
    envelope["payload"]["action"] = "tamper"
    assert signer.verify_envelope(envelope) is False
