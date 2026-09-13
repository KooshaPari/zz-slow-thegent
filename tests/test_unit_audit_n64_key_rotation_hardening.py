# @trace AUDIT-N+64
"""AUDIT-N+64 hardening tests for governance/key_rotation.py (SOTA pass-48).

Asserts the contract surface FR-GOV-KR-001..015.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from thegent.governance.key_rotation import (
    ApiKeyRecord,
    KeyRegistry,
    KeyRotationMonitor,
    KeyRotationWebhook,
    __all__,
    make_expiry_utc,
)


def _make_record(
    key_id: str = "test-key",
    provider: str = "openai",
    expires_at: str | None = None,
) -> ApiKeyRecord:
    """Helper to build a valid ApiKeyRecord."""
    return ApiKeyRecord(
        key_id=key_id,
        provider=provider,
        expires_at=expires_at or make_expiry_utc(30),
        last_rotated=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# FR-GOV-KR-001: ApiKeyRecord rejects empty key_id (min_length=1)
# ---------------------------------------------------------------------------
def test_kr_001_rejects_empty_key_id() -> None:
    with pytest.raises(Exception):
        ApiKeyRecord(
            key_id="",
            provider="openai",
            expires_at=make_expiry_utc(30),
            last_rotated=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# FR-GOV-KR-002: ApiKeyRecord rejects empty provider (min_length=1)
# ---------------------------------------------------------------------------
def test_kr_002_rejects_empty_provider() -> None:
    with pytest.raises(Exception):
        ApiKeyRecord(
            key_id="key-1",
            provider="",
            expires_at=make_expiry_utc(30),
            last_rotated=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# FR-GOV-KR-003: ApiKeyRecord.is_expired() returns True when expires_at is in the past
# ---------------------------------------------------------------------------
def test_kr_003_is_expired_true_for_past() -> None:
    past = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    record = _make_record(expires_at=past)
    assert record.is_expired() is True


# ---------------------------------------------------------------------------
# FR-GOV-KR-004: ApiKeyRecord.is_expired() returns False when expires_at is in the future
# ---------------------------------------------------------------------------
def test_kr_004_is_expired_false_for_future() -> None:
    record = _make_record(expires_at=make_expiry_utc(30))
    assert record.is_expired() is False


# ---------------------------------------------------------------------------
# FR-GOV-KR-005: ApiKeyRecord.is_expiring_soon() returns True within warn_days window
# ---------------------------------------------------------------------------
def test_kr_005_is_expiring_soon_within_window() -> None:
    soon = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    record = _make_record(expires_at=soon)
    assert record.is_expiring_soon(warn_days=7) is True


# ---------------------------------------------------------------------------
# FR-GOV-KR-006: ApiKeyRecord.days_until_expiry() returns negative for expired keys
# ---------------------------------------------------------------------------
def test_kr_006_days_until_expiry_negative_for_expired() -> None:
    past = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    record = _make_record(expires_at=past)
    assert record.days_until_expiry() < 0


# ---------------------------------------------------------------------------
# FR-GOV-KR-007: KeyRegistry.__init__ expands user path (~)
# ---------------------------------------------------------------------------
def test_kr_007_key_registry_expands_user_path(tmp_path: Path) -> None:
    registry = KeyRegistry("~/.thegent/keys/registry.jsonl")
    # expanduser() should resolve ~ to an absolute path
    assert registry.registry_path.is_absolute()
    assert "~" not in str(registry.registry_path)


# ---------------------------------------------------------------------------
# FR-GOV-KR-008: KeyRegistry.add() rejects duplicate key_id with ValueError
# ---------------------------------------------------------------------------
def test_kr_008_add_rejects_duplicate(tmp_path: Path) -> None:
    reg = KeyRegistry(tmp_path / "reg.jsonl")
    record = _make_record(key_id="dup-1")
    reg.add(record)
    with pytest.raises(ValueError, match="already registered"):
        reg.add(_make_record(key_id="dup-1"))


# ---------------------------------------------------------------------------
# FR-GOV-KR-009: KeyRegistry.list_all() returns empty list for nonexistent file
# ---------------------------------------------------------------------------
def test_kr_009_list_all_empty_for_nonexistent(tmp_path: Path) -> None:
    reg = KeyRegistry(tmp_path / "nonexistent.jsonl")
    assert reg.list_all() == []


# ---------------------------------------------------------------------------
# FR-GOV-KR-010: KeyRegistry.get() raises KeyError for unknown key_id
# ---------------------------------------------------------------------------
def test_kr_010_get_raises_key_error(tmp_path: Path) -> None:
    reg = KeyRegistry(tmp_path / "reg.jsonl")
    with pytest.raises(KeyError):
        reg.get("unknown-key-id")


# ---------------------------------------------------------------------------
# FR-GOV-KR-011: KeyRegistry.update() raises KeyError for unknown key_id
# ---------------------------------------------------------------------------
def test_kr_011_update_raises_key_error(tmp_path: Path) -> None:
    reg = KeyRegistry(tmp_path / "reg.jsonl")
    record = _make_record(key_id="ghost")
    with pytest.raises(KeyError):
        reg.update(record)


# ---------------------------------------------------------------------------
# FR-GOV-KR-012: KeyRotationMonitor.check_all() returns warnings for expiring keys
# ---------------------------------------------------------------------------
def test_kr_012_check_all_returns_warnings(tmp_path: Path) -> None:
    reg = KeyRegistry(tmp_path / "reg.jsonl")
    soon = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    reg.add(_make_record(key_id="exp-1", expires_at=soon))
    monitor = KeyRotationMonitor(reg, warn_days=7)
    warnings = monitor.check_all()
    assert len(warnings) == 1
    assert warnings[0].record.key_id == "exp-1"


# ---------------------------------------------------------------------------
# FR-GOV-KR-013: KeyRotationMonitor.check_provider() filters by provider name
# ---------------------------------------------------------------------------
def test_kr_013_check_provider_filters(tmp_path: Path) -> None:
    reg = KeyRegistry(tmp_path / "reg.jsonl")
    soon = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    reg.add(_make_record(key_id="a-1", provider="openai", expires_at=soon))
    reg.add(_make_record(key_id="b-1", provider="anthropic", expires_at=soon))
    monitor = KeyRotationMonitor(reg, warn_days=7)
    openai_warnings = monitor.check_provider("openai")
    assert len(openai_warnings) == 1
    assert openai_warnings[0].record.provider == "openai"


# ---------------------------------------------------------------------------
# FR-GOV-KR-014: KeyRotationWebhook.__init__ rejects empty webhook_url
# ---------------------------------------------------------------------------
def test_kr_014_webhook_rejects_empty_url(tmp_path: Path) -> None:
    reg = KeyRegistry(tmp_path / "reg.jsonl")
    with pytest.raises(ValueError, match="must not be empty"):
        KeyRotationWebhook(webhook_url="", registry=reg)


# ---------------------------------------------------------------------------
# FR-GOV-KR-015: __all__ exports exactly the expected names
# ---------------------------------------------------------------------------
def test_kr_015_all_exports() -> None:
    expected = [
        "ApiKeyRecord",
        "KeyRegistry",
        "KeyRotationMonitor",
        "KeyRotationWebhook",
        "KeyRotationWarning",
        "make_expiry_utc",
    ]
    assert sorted(__all__) == sorted(expected)
    assert len(__all__) == len(expected)
