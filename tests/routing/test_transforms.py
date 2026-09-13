"""Tests for GW-41: middle-out context compression and request transforms.

# @trace FR-REQEXT-041
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.transforms import (
    apply_middle_out,
    apply_transforms,
    extract_transforms,
)


@pytest.mark.requirement("FR-REQEXT-041")
def test_extract_transforms_present() -> None:
    body = {"transforms": ["middle-out"]}
    assert extract_transforms(body) == ["middle-out"]


@pytest.mark.requirement("FR-REQEXT-041")
def test_extract_transforms_missing() -> None:
    body = {"model": "gpt-4o"}
    assert extract_transforms(body) == []


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_middle_out_short_messages_unchanged() -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(5)]
    result = apply_middle_out(messages, max_messages=20)
    assert result == messages


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_middle_out_long_messages_compressed() -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
    result = apply_middle_out(messages, max_messages=10)
    assert len(result) < len(messages)


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_middle_out_preserves_system_messages() -> None:
    messages = [{"role": "system", "content": "You are helpful."}] + [
        {"role": "user", "content": f"msg {i}"} for i in range(25)
    ]
    result = apply_middle_out(messages, max_messages=10)
    system_msgs = [m for m in result if m.get("role") == "system"]
    assert len(system_msgs) == 1
    assert system_msgs[0]["content"] == "You are helpful."


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_middle_out_preserves_first_user() -> None:
    first_user = {"role": "user", "content": "first user message"}
    messages = (
        [{"role": "system", "content": "sys"}]
        + [first_user]
        + [{"role": "user", "content": f"middle {i}"} for i in range(20)]
    )
    result = apply_middle_out(messages, max_messages=10)
    # The first user message should appear in the result
    assert first_user in result


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_middle_out_preserves_recent_messages() -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
    max_messages = 10
    result = apply_middle_out(messages, max_messages=max_messages)
    tail_count = max_messages // 2
    expected_recent = messages[-tail_count:]
    for msg in expected_recent:
        assert msg in result


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_middle_out_inserts_omission_message() -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
    result = apply_middle_out(messages, max_messages=10)
    omission_msgs = [m for m in result if "omitted for context window" in m.get("content", "")]
    assert len(omission_msgs) == 1
    assert omission_msgs[0]["role"] == "assistant"


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_middle_out_does_not_mutate() -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
    original = [dict(m) for m in messages]
    apply_middle_out(messages, max_messages=10)
    assert messages == original


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_transforms_middle_out() -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
    body = {"messages": messages, "transforms": ["middle-out"]}
    result = apply_transforms(body, max_messages=10)
    assert len(result["messages"]) < len(messages)


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_transforms_unknown_ignored() -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(5)]
    body = {"messages": messages, "transforms": ["unknown-transform"]}
    result = apply_transforms(body)
    # Unknown transforms silently ignored; messages unchanged
    assert result["messages"] == messages


@pytest.mark.requirement("FR-REQEXT-041")
def test_apply_transforms_empty_list() -> None:
    messages = [{"role": "user", "content": "hello"}]
    body = {"messages": messages, "transforms": []}
    result = apply_transforms(body)
    assert result["messages"] == messages
