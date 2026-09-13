from __future__ import annotations

"""Tests for GW-51: PII masking round-trip guardrail.

# @trace FR-GUARD-051
"""

import pytest

from thegent.utils.routing_impl.guardrails.pii import (
    mask_messages,
    mask_pii,
    unmask_content,
    unmask_pii,
)

pytestmark = pytest.mark.requirement("FR-GUARD-051")


def test_mask_email():
    result = mask_pii("Contact us at alice@example.com for help.")
    assert "[EMAIL_1]" in result.masked_text
    assert "alice@example.com" not in result.masked_text
    assert len(result.entities) == 1
    assert result.entities[0].entity_type == "EMAIL"
    assert result.entities[0].original == "alice@example.com"


def test_mask_phone():
    result = mask_pii("Call me at 415-555-1234 anytime.")
    assert "[PHONE_1]" in result.masked_text
    assert "415-555-1234" not in result.masked_text
    assert result.entities[0].entity_type == "PHONE"


def test_mask_ssn():
    result = mask_pii("My SSN is 123-45-6789.")
    assert "[SSN_1]" in result.masked_text
    assert "123-45-6789" not in result.masked_text
    assert result.entities[0].entity_type == "SSN"


def test_mask_credit_card():
    result = mask_pii("Pay with card 4111 1111 1111 1111.")
    assert "[CREDIT_CARD_1]" in result.masked_text
    assert "4111 1111 1111 1111" not in result.masked_text
    assert result.entities[0].entity_type == "CREDIT_CARD"


def test_mask_ip_address():
    result = mask_pii("Server IP is 192.168.1.1 — do not share.")
    assert "[IP_ADDRESS_1]" in result.masked_text
    assert "192.168.1.1" not in result.masked_text
    assert result.entities[0].entity_type == "IP_ADDRESS"


def test_unmask_restores_original():
    original_text = "Email me at user@domain.org please."
    result = mask_pii(original_text)
    restored = unmask_pii(result.masked_text, result.token_map)
    assert restored == original_text


def test_mask_multiple_entities_numbered():
    text = "First: a@test.com, second: b@test.com, third: c@test.com"
    result = mask_pii(text)
    assert "[EMAIL_1]" in result.masked_text
    assert "[EMAIL_2]" in result.masked_text
    assert "[EMAIL_3]" in result.masked_text
    assert len(result.entities) == 3
    for i, entity in enumerate(result.entities, start=1):
        assert entity.token == f"[EMAIL_{i}]"


def test_mask_messages_list():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "My email is user@example.com and my SSN is 111-22-3333.",
        },
    ]
    masked_msgs, token_map = mask_messages(messages)
    user_content = masked_msgs[1]["content"]
    assert "user@example.com" not in user_content
    assert "111-22-3333" not in user_content
    assert "[EMAIL_1]" in user_content
    assert "[SSN_1]" in user_content
    assert "user@example.com" in token_map.values()
    assert "111-22-3333" in token_map.values()
    # System message untouched (no PII)
    assert masked_msgs[0]["content"] == "You are a helpful assistant."


def test_mask_no_pii_unchanged():
    text = "The quick brown fox jumps over the lazy dog."
    result = mask_pii(text)
    assert result.masked_text == text
    assert result.entities == []
    assert result.token_map == {}


def test_entity_type_filter():
    text = "Email: alice@example.com. Phone: 800-555-0100."
    result = mask_pii(text, entity_types=["EMAIL"])
    assert "[EMAIL_1]" in result.masked_text
    # Phone should NOT be masked
    assert "800-555-0100" in result.masked_text
    assert all(e.entity_type == "EMAIL" for e in result.entities)


def test_unmask_content_roundtrip():
    original = "Call bob@corp.io or ring 212-555-9999."
    mask_result = mask_pii(original)
    restored = unmask_content(mask_result.masked_text, mask_result.token_map)
    assert restored == original


def test_mask_pii_result_token_map():
    text = "Reach me at dev@example.net"
    result = mask_pii(text)
    assert len(result.token_map) == 1
    token = next(iter(result.token_map.keys()))
    assert token == "[EMAIL_1]"
    assert result.token_map[token] == "dev@example.net"
