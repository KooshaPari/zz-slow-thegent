"""Tests for WAI-ARIA-style annotation helpers."""

import pytest

from thegent.i18n.aria import (
    _quote,
    _tokenize,
    _unquote,
    annotate,
    aria_attributes,
    is_valid_role,
    parse_aria,
)


@pytest.mark.parametrize(
    "role",
    [
        "status",
        "log",
        "timer",
        "progressbar",
        "alert",
        "table",
        "row",
        "columnheader",
        "rowheader",
        "group",
        "region",
        "list",
        "listitem",
    ],
)
def test_is_valid_role_accepts_supported_roles(role: str) -> None:
    assert is_valid_role(role)


@pytest.mark.parametrize("role", ["button", "dialog", "STATUS", ""])
def test_is_valid_role_rejects_unsupported_roles(role: str) -> None:
    assert not is_valid_role(role)


def test_aria_attributes_uses_group_defaults() -> None:
    assert aria_attributes() == "[role=group]"


def test_aria_attributes_preserves_valid_role() -> None:
    assert aria_attributes(role="status") == "[role=status]"


def test_aria_attributes_downgrades_invalid_role_to_group() -> None:
    assert aria_attributes(role="not-a-role") == "[role=group]"


@pytest.mark.parametrize("aria_live", ["off", "polite", "assertive"])
def test_aria_attributes_includes_valid_live_value(aria_live: str) -> None:
    assert aria_attributes(aria_live=aria_live) == f"[role=group aria-live={aria_live}]"


def test_aria_attributes_drops_invalid_live_value() -> None:
    assert aria_attributes(aria_live="urgent") == "[role=group]"


def test_aria_attributes_omits_atomic_when_false() -> None:
    assert aria_attributes(aria_atomic=False) == "[role=group]"


def test_aria_attributes_includes_atomic_when_true() -> None:
    assert aria_attributes(aria_atomic=True) == "[role=group aria-atomic=true]"


def test_aria_attributes_quotes_label_with_spaces() -> None:
    assert aria_attributes(aria_label="Build status") == '[role=group aria-label="Build status"]'


def test_aria_attributes_includes_label_references() -> None:
    annotation = aria_attributes(
        role="region",
        aria_labelledby="heading-id",
        aria_describedby="help text",
    )

    assert annotation == '[role=region aria-labelledby=heading-id aria-describedby="help text"]'


def test_aria_attributes_includes_extra_mapping_in_order() -> None:
    annotation = aria_attributes(extra={"aria-busy": "true", "data-state": "in progress"})

    assert annotation == '[role=group aria-busy=true data-state="in progress"]'


def test_quote_leaves_single_token_unchanged() -> None:
    assert _quote("heading-id") == "heading-id"


def test_quote_wraps_value_containing_spaces() -> None:
    assert _quote("Build status") == '"Build status"'


def test_quote_escapes_embedded_double_quotes() -> None:
    assert _quote('Say "ready"') == '"Say \\"ready\\""'


def test_quote_wraps_empty_value() -> None:
    assert _quote("") == '""'


def test_unquote_removes_outer_double_quotes() -> None:
    assert _unquote('"Build status"') == "Build status"


def test_unquote_leaves_unquoted_value_unchanged() -> None:
    assert _unquote("polite") == "polite"


def test_tokenize_respects_quoted_values() -> None:
    text = 'role=status aria-label="Build status" aria-live=polite'

    assert list(_tokenize(text)) == [
        "role=status",
        'aria-label="Build status"',
        "aria-live=polite",
    ]


def test_tokenize_handles_mixed_whitespace() -> None:
    assert list(_tokenize("role=status\taria-live=polite\naria-atomic=true")) == [
        "role=status",
        "aria-live=polite",
        "aria-atomic=true",
    ]


def test_tokenize_empty_text_yields_no_tokens() -> None:
    assert list(_tokenize("")) == []


def test_parse_aria_parses_bracketed_annotation() -> None:
    annotation = '[role=status aria-live=polite aria-label="Build status"]'

    assert parse_aria(annotation) == {
        "role": "status",
        "aria-live": "polite",
        "aria-label": "Build status",
    }


def test_parse_aria_accepts_annotation_without_brackets() -> None:
    assert parse_aria("role=alert aria-live=assertive") == {
        "role": "alert",
        "aria-live": "assertive",
    }


def test_parse_aria_ignores_tokens_without_equals_sign() -> None:
    assert parse_aria("[role=status malformed aria-live=polite]") == {
        "role": "status",
        "aria-live": "polite",
    }


def test_parse_aria_round_trip_preserves_attributes() -> None:
    annotation = aria_attributes(
        role="status",
        aria_live="polite",
        aria_atomic=True,
        aria_label="Build status",
        aria_labelledby="build-heading",
        aria_describedby="build details",
        extra={"aria-busy": "true"},
    )

    assert parse_aria(annotation) == {
        "role": "status",
        "aria-live": "polite",
        "aria-atomic": "true",
        "aria-label": "Build status",
        "aria-labelledby": "build-heading",
        "aria-describedby": "build details",
        "aria-busy": "true",
    }


def test_annotate_appends_attribute_trailer() -> None:
    assert annotate("Live runs", role="status", aria_live="polite", aria_atomic=True) == (
        "Live runs [role=status aria-live=polite aria-atomic=true]"
    )


def test_annotate_uses_default_arguments() -> None:
    assert annotate("Overview") == "Overview [role=group]"


def test_annotate_passes_label_and_extra_mapping() -> None:
    result = annotate(
        "Queue",
        role="region",
        aria_label="Pending work",
        extra={"aria-busy": "true"},
    )

    assert result == 'Queue [role=region aria-label="Pending work" aria-busy=true]'
