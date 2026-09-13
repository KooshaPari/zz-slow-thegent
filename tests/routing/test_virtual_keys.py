"""Tests for GW-28: Virtual key system.

All tests tagged with @pytest.mark.requirement("FR-KEYS-028").

# @trace FR-KEYS-028
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.virtual_keys import (
    VirtualKeyConfig,
    VirtualKeyStore,
    VirtualKeyValidator,
    extract_virtual_key_id,
    get_key_store,
    reset_key_store,
)

# ---------------------------------------------------------------------------
# extract_virtual_key_id
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-KEYS-028")
def test_extract_virtual_key_id_valid() -> None:
    """Bearer sk-tg-abc123 should return the token sk-tg-abc123."""
    result = extract_virtual_key_id("Bearer sk-tg-abc123")
    assert result == "sk-tg-abc123"


@pytest.mark.requirement("FR-KEYS-028")
def test_extract_virtual_key_id_not_virtual() -> None:
    """Bearer sk-openai-abc does not start with sk-tg- so should return None."""
    result = extract_virtual_key_id("Bearer sk-openai-abc")
    assert result is None


@pytest.mark.requirement("FR-KEYS-028")
def test_extract_virtual_key_id_no_bearer() -> None:
    """A token without 'Bearer ' prefix should return None."""
    result = extract_virtual_key_id("sk-tg-abc123")
    assert result is None


@pytest.mark.requirement("FR-KEYS-028")
def test_extract_virtual_key_id_none() -> None:
    """None authorization header should return None."""
    result = extract_virtual_key_id(None)
    assert result is None


@pytest.mark.requirement("FR-KEYS-028")
def test_extract_virtual_key_id_empty_string() -> None:
    """Empty string authorization header should return None."""
    result = extract_virtual_key_id("")
    assert result is None


# ---------------------------------------------------------------------------
# VirtualKeyStore
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-KEYS-028")
def test_virtual_key_store_register_and_get() -> None:
    """A registered key must be retrievable by its key_id."""
    store = VirtualKeyStore()
    cfg = VirtualKeyConfig(key_id="sk-tg-test1", name="Test Key")
    store.register(cfg)
    retrieved = store.get("sk-tg-test1")
    assert retrieved is cfg


@pytest.mark.requirement("FR-KEYS-028")
def test_virtual_key_store_delete() -> None:
    """Deleting an existing key returns True; the key is then gone."""
    store = VirtualKeyStore()
    cfg = VirtualKeyConfig(key_id="sk-tg-del1")
    store.register(cfg)
    assert store.delete("sk-tg-del1") is True
    assert store.get("sk-tg-del1") is None


@pytest.mark.requirement("FR-KEYS-028")
def test_virtual_key_store_delete_missing_returns_false() -> None:
    """Deleting a non-existent key returns False."""
    store = VirtualKeyStore()
    assert store.delete("sk-tg-missing") is False


@pytest.mark.requirement("FR-KEYS-028")
def test_virtual_key_store_list_all() -> None:
    """list_keys with no owner filter returns all registered keys."""
    store = VirtualKeyStore()
    cfg_a = VirtualKeyConfig(key_id="sk-tg-a", owner_id="user-1")
    cfg_b = VirtualKeyConfig(key_id="sk-tg-b", owner_id="user-2")
    store.register(cfg_a)
    store.register(cfg_b)
    all_keys = store.list_keys()
    assert len(all_keys) == 2
    ids = {k.key_id for k in all_keys}
    assert ids == {"sk-tg-a", "sk-tg-b"}


@pytest.mark.requirement("FR-KEYS-028")
def test_virtual_key_store_list_by_owner() -> None:
    """list_keys(owner_id=...) returns only keys belonging to that owner."""
    store = VirtualKeyStore()
    cfg_a = VirtualKeyConfig(key_id="sk-tg-a", owner_id="user-1")
    cfg_b = VirtualKeyConfig(key_id="sk-tg-b", owner_id="user-2")
    cfg_c = VirtualKeyConfig(key_id="sk-tg-c", owner_id="user-1")
    store.register(cfg_a)
    store.register(cfg_b)
    store.register(cfg_c)
    user1_keys = store.list_keys(owner_id="user-1")
    assert len(user1_keys) == 2
    ids = {k.key_id for k in user1_keys}
    assert ids == {"sk-tg-a", "sk-tg-c"}


@pytest.mark.requirement("FR-KEYS-028")
def test_virtual_key_store_get_missing() -> None:
    """Getting a non-existent key returns None."""
    store = VirtualKeyStore()
    result = store.get("sk-tg-does-not-exist")
    assert result is None


# ---------------------------------------------------------------------------
# VirtualKeyValidator
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-KEYS-028")
def test_validate_key_ok() -> None:
    """A valid key with no model restrictions should return allowed=True, reason='ok'."""
    store = VirtualKeyStore()
    cfg = VirtualKeyConfig(key_id="sk-tg-ok1", allowed_models=[])
    store.register(cfg)
    validator = VirtualKeyValidator()
    result = validator.validate_key("sk-tg-ok1", "gpt-4o", store=store)
    assert result.allowed is True
    assert result.reason == "ok"
    assert result.key_config is cfg


@pytest.mark.requirement("FR-KEYS-028")
def test_validate_key_not_found() -> None:
    """An unknown key_id should return allowed=False, reason='key_not_found'."""
    store = VirtualKeyStore()
    validator = VirtualKeyValidator()
    result = validator.validate_key("sk-tg-unknown", "gpt-4o", store=store)
    assert result.allowed is False
    assert result.reason == "key_not_found"
    assert result.key_config is None


@pytest.mark.requirement("FR-KEYS-028")
def test_validate_key_model_not_allowed() -> None:
    """A key with an allowed_models list should block models not in the list."""
    store = VirtualKeyStore()
    cfg = VirtualKeyConfig(key_id="sk-tg-restricted", allowed_models=["claude-3-5-sonnet"])
    store.register(cfg)
    validator = VirtualKeyValidator()
    result = validator.validate_key("sk-tg-restricted", "gpt-4o", store=store)
    assert result.allowed is False
    assert result.reason == "model_not_allowed"
    assert result.key_config is cfg


@pytest.mark.requirement("FR-KEYS-028")
def test_validate_key_model_allowed_in_list() -> None:
    """A key with an allowed_models list should allow a model that is in the list."""
    store = VirtualKeyStore()
    cfg = VirtualKeyConfig(key_id="sk-tg-claude", allowed_models=["claude-3-5-sonnet", "claude-3-haiku"])
    store.register(cfg)
    validator = VirtualKeyValidator()
    result = validator.validate_key("sk-tg-claude", "claude-3-5-sonnet", store=store)
    assert result.allowed is True
    assert result.reason == "ok"


@pytest.mark.requirement("FR-KEYS-028")
def test_validate_key_no_model_restriction() -> None:
    """An empty allowed_models list means all models are allowed."""
    store = VirtualKeyStore()
    cfg = VirtualKeyConfig(key_id="sk-tg-open", allowed_models=[])
    store.register(cfg)
    validator = VirtualKeyValidator()
    # Should allow any model when list is empty
    for model in ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro", "anything"]:
        result = validator.validate_key("sk-tg-open", model, store=store)
        assert result.allowed is True, f"Expected allowed for model={model}"


# ---------------------------------------------------------------------------
# Singleton behaviour
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-KEYS-028")
def test_singleton_same_instance() -> None:
    """get_key_store() must return the same instance on every call."""
    reset_key_store()
    store_a = get_key_store()
    store_b = get_key_store()
    assert store_a is store_b


@pytest.mark.requirement("FR-KEYS-028")
def test_reset_key_store() -> None:
    """reset_key_store() causes get_key_store() to return a fresh instance."""
    reset_key_store()
    store_before = get_key_store()
    reset_key_store()
    store_after = get_key_store()
    assert store_before is not store_after
