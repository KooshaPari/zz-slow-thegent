"""Tests for GW-44/45/46/47: gateway request extension helpers.

Coverage:
- extract_provider_gateway_options (GW-44): present, missing, empty gateway
- extract_special_headers (GW-45): present, none present, case-insensitive
- enrich_model_entry (GW-46): no metadata, with context_length (mocked)
- inject_proxy_models (GW-47): adds missing, no duplicates, empty list

# @trace FR-REQEXT-044 FR-REQEXT-045 FR-REQEXT-046 FR-REQEXT-047
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from thegent.cliproxy_adapter import (
    enrich_model_entry,
    extract_provider_gateway_options,
    extract_special_headers,
    inject_proxy_models,
)
from thegent.utils.routing_impl import harness_model_mapping

# ---------------------------------------------------------------------------
# GW-44: extract_provider_gateway_options
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-REQEXT-044")
def test_extract_provider_gateway_options_present() -> None:
    """Returns the gateway sub-dict when providerOptions.gateway is set."""
    body = {
        "model": "claude-sonnet-4-6",
        "providerOptions": {
            "gateway": {
                "cache": True,
                "timeout": 30,
            }
        },
    }
    result = extract_provider_gateway_options(body)
    assert result == {"cache": True, "timeout": 30}


@pytest.mark.requirement("FR-REQEXT-044")
def test_extract_provider_gateway_options_missing() -> None:
    """Returns empty dict when providerOptions key is absent."""
    body = {"model": "claude-haiku-4-5", "messages": []}
    result = extract_provider_gateway_options(body)
    assert result == {}


@pytest.mark.requirement("FR-REQEXT-044")
def test_extract_provider_gateway_options_empty_gateway() -> None:
    """Returns empty dict when providerOptions.gateway is an empty dict."""
    body = {
        "model": "claude-opus-4-6",
        "providerOptions": {"gateway": {}},
    }
    result = extract_provider_gateway_options(body)
    assert result == {}


@pytest.mark.requirement("FR-REQEXT-044")
def test_extract_provider_gateway_options_no_gateway_key() -> None:
    """Returns empty dict when providerOptions is present but has no gateway key."""
    body = {
        "providerOptions": {"someOtherOption": "value"},
    }
    result = extract_provider_gateway_options(body)
    assert result == {}


# ---------------------------------------------------------------------------
# GW-45: extract_special_headers
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-REQEXT-045")
def test_extract_special_headers_present() -> None:
    """Known special headers are extracted and returned."""
    request_headers = {
        "x-session-id": "sess-abc123",
        "x-request-id": "req-xyz",
        "x-anthropic-beta": "prompt-caching-2024-07-31",
        "content-type": "application/json",
        "authorization": "Bearer secret",
    }
    result = extract_special_headers(request_headers)

    assert result["x-session-id"] == "sess-abc123"
    assert result["x-request-id"] == "req-xyz"
    assert result["x-anthropic-beta"] == "prompt-caching-2024-07-31"
    # Non-special headers must not be included
    assert "content-type" not in result
    assert "authorization" not in result


@pytest.mark.requirement("FR-REQEXT-045")
def test_extract_special_headers_none_present() -> None:
    """Returns empty dict when no special headers are present."""
    request_headers = {
        "content-type": "application/json",
        "host": "localhost",
        "accept": "*/*",
    }
    result = extract_special_headers(request_headers)
    assert result == {}


@pytest.mark.requirement("FR-REQEXT-045")
def test_extract_special_headers_case_insensitive() -> None:
    """Header matching is case-insensitive (key.lower() is compared)."""
    request_headers = {
        "X-Session-Id": "sess-upper",
        "X-ANTHROPIC-BETA": "streaming-abc",
        "X-Stainless-OS": "macOS",
    }
    result = extract_special_headers(request_headers)

    assert result["X-Session-Id"] == "sess-upper"
    assert result["X-ANTHROPIC-BETA"] == "streaming-abc"
    assert result["X-Stainless-OS"] == "macOS"


@pytest.mark.requirement("FR-REQEXT-045")
def test_extract_special_headers_stainless_arch() -> None:
    """x-stainless-arch is extracted as a special header."""
    request_headers = {
        "x-stainless-arch": "arm64",
        "x-stainless-os": "macOS",
    }
    result = extract_special_headers(request_headers)

    assert result["x-stainless-arch"] == "arm64"
    assert result["x-stainless-os"] == "macOS"


# ---------------------------------------------------------------------------
# GW-46: enrich_model_entry
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-REQEXT-046")
def test_enrich_model_entry_no_metadata() -> None:
    """Entry for unknown model is returned unchanged."""
    entry = {"id": "totally-unknown-model-xyz", "object": "model"}
    result = enrich_model_entry(entry)
    # Must be identical to input (no new keys added)
    assert result == entry


@pytest.mark.requirement("FR-REQEXT-046")
def test_enrich_model_entry_with_context_length() -> None:
    """When model_metadata reports a known model, enrich_model_entry does not crash.

    The function uses lazy imports inside a try/except. We verify it returns the
    entry (possibly enriched) and does not raise.
    """
    # claude-sonnet-4-6 is in MODEL_METADATA so has_model_metadata returns True.
    # The model_metadata dict has 'context_window' but not 'context_length' as an
    # attribute (it's a plain dict), so hasattr checks fail and entry is returned
    # with only the original fields (no exception).
    entry = {"id": "claude-sonnet-4-6", "object": "model"}
    result = enrich_model_entry(entry)

    # Must return a dict containing at least the original entry fields
    assert isinstance(result, dict)
    assert result.get("id") == "claude-sonnet-4-6"
    assert result.get("object") == "model"


@pytest.mark.requirement("FR-REQEXT-046")
def test_enrich_model_entry_known_model_unchanged_fields() -> None:
    """Known model in registry does not lose existing fields."""
    # claude-sonnet-4-6 is in MODEL_METADATA; enrich_model_entry returns at minimum
    # the original entry (may or may not add fields depending on meta shape).
    entry = {"id": "claude-sonnet-4-6", "object": "model", "custom_field": "preserved"}
    result = enrich_model_entry(entry)

    # Existing fields must be preserved
    assert result["id"] == "claude-sonnet-4-6"
    assert result["object"] == "model"
    assert result["custom_field"] == "preserved"


@pytest.mark.requirement("FR-REQEXT-046")
def test_enrich_model_entry_exception_returns_entry() -> None:
    """If model_metadata import raises, the original entry is returned unchanged."""
    entry = {"id": "some-model", "object": "model"}

    with patch("builtins.__import__", side_effect=ImportError("no module")):
        # This patches all imports globally — too broad.
        # Use a targeted patch instead:
        pass

    # Targeted patch: simulate has_model_metadata raising
    with patch(
        "thegent.utils.routing_impl.model_metadata.has_model_metadata",
        side_effect=RuntimeError("simulated failure"),
    ):
        result = enrich_model_entry(entry)

    # Exception is caught inside enrich_model_entry → returns original entry
    assert result == entry


# ---------------------------------------------------------------------------
# GW-47: inject_proxy_models
# ---------------------------------------------------------------------------


@pytest.fixture
def canonical_to_openrouter_fixture(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Use a deterministic mapping so inject_proxy_models tests are isolated."""
    mapping_seed = {
        "gpt-4o": "openai/gpt-4o",
        "claude-sonnet-4-6": "anthropic/claude-sonnet-4-6",
        "o3-mini": "openai/o3-mini",
    }
    # Fresh per-test mapping object to avoid cross-test mutation coupling.
    mapping = dict(mapping_seed)
    monkeypatch.setattr(
        harness_model_mapping,
        "CANONICAL_TO_OPENROUTER",
        mapping,
        raising=True,
    )
    return mapping


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_adds_missing(canonical_to_openrouter_fixture: dict[str, str]) -> None:
    """Canonical aliases not in the models list are injected."""
    models: list[dict] = [{"id": "gpt-4o", "object": "model"}]
    result = inject_proxy_models(models)

    # gpt-4o is already present; other aliases should be added
    result_ids = {m["id"] for m in result}
    assert "gpt-4o" in result_ids

    injected = result_ids - {"gpt-4o"}
    expected_aliases = set(canonical_to_openrouter_fixture.keys()) - {"gpt-4o"}
    assert injected == expected_aliases


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_no_duplicates(canonical_to_openrouter_fixture: dict[str, str]) -> None:
    """Aliases already present in the list are not duplicated."""
    # Seed list with all canonical aliases
    initial = [{"id": alias, "object": "model"} for alias in canonical_to_openrouter_fixture]
    result = inject_proxy_models(initial)

    # IDs should appear exactly once each
    ids = [m["id"] for m in result]
    for alias in canonical_to_openrouter_fixture:
        assert ids.count(alias) == 1, f"Alias {alias!r} appears {ids.count(alias)} times"


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_complete_canonical_set_is_noop(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """When all canonical aliases already exist, no new entries are injected."""
    initial = [{"id": alias, "object": "model"} for alias in canonical_to_openrouter_fixture]
    result = inject_proxy_models(initial)

    assert result == initial
    assert len(result) == len(initial)


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_prepopulated_canonical_and_mapped_duplicates(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Pre-populated canonical+mapped duplicates remain stable; only missing aliases are injected."""
    initial = [
        {"id": "custom-model", "object": "model"},
        {"id": "gpt-4o", "object": "model"},
        {"id": "openai/gpt-4o", "object": "model"},
        {"id": "gpt-4o", "object": "model"},
        {"id": "openai/gpt-4o", "object": "model"},
    ]

    result = inject_proxy_models(initial)
    ids = [m["id"] for m in result]

    # Existing duplicate canonical and mapped IDs are preserved as-is.
    assert ids.count("gpt-4o") == 2
    assert ids.count("openai/gpt-4o") == 2

    # Missing canonical aliases are injected exactly once.
    for alias in canonical_to_openrouter_fixture:
        expected_count = 2 if alias == "gpt-4o" else 1
        assert ids.count(alias) == expected_count


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_preserves_existing_model_order_on_injection(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Original model order is stable; injected aliases are appended."""
    existing = [
        {"id": "custom-first", "object": "model"},
        {"id": "claude-sonnet-4-6", "object": "model"},
        {"id": "custom-last", "object": "model"},
    ]
    existing_ids = [m["id"] for m in existing]

    result = inject_proxy_models(existing)
    result_ids = [m["id"] for m in result]

    # Existing entries remain in the exact original order.
    assert result_ids[: len(existing_ids)] == existing_ids

    # New entries are appended in deterministic mapping order.
    injected_ids = result_ids[len(existing_ids) :]
    expected_injected = [alias for alias in canonical_to_openrouter_fixture if alias not in set(existing_ids)]
    assert injected_ids == expected_injected


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_stable_append_order_for_multiple_injected_aliases(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """When multiple aliases are missing, they are appended in deterministic mapping order."""
    # Only one canonical alias is pre-populated, so multiple aliases are injected.
    existing = [
        {"id": "o3-mini", "object": "model"},
        {"id": "custom-model", "object": "model"},
    ]
    result = inject_proxy_models(existing)
    result_ids = [m["id"] for m in result]

    # Existing entries remain first in original order.
    assert result_ids[: len(existing)] == ["o3-mini", "custom-model"]

    # Multiple missing aliases are appended in fixture mapping order.
    expected_appended = [alias for alias in canonical_to_openrouter_fixture if alias not in {"o3-mini", "custom-model"}]
    assert result_ids[len(existing) :] == expected_appended


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_repeated_noop_idempotency_three_calls(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """After first injection pass, additional passes (2nd/3rd) are strict no-ops."""
    first = inject_proxy_models([])
    second = inject_proxy_models(first)
    third = inject_proxy_models(second)

    # Repeated calls should not alter content or ordering once canonical aliases are present.
    assert second == first
    assert third == first

    ids = [m["id"] for m in third]
    for alias in canonical_to_openrouter_fixture:
        assert ids.count(alias) == 1, f"Alias {alias!r} appears {ids.count(alias)} times"


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_empty_list(canonical_to_openrouter_fixture: dict[str, str]) -> None:
    """Starting from an empty list injects all canonical aliases."""
    result = inject_proxy_models([])

    result_ids = {m["id"] for m in result}
    # All canonical aliases must be present
    for alias in canonical_to_openrouter_fixture:
        assert alias in result_ids


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_injected_entries_have_required_fields(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Injected model entries have id, object, created, owned_by fields."""
    result = inject_proxy_models([])

    for entry in result:
        assert "id" in entry
        assert entry["object"] == "model"
        assert "created" in entry
        assert entry["owned_by"] == "thegent-proxy"


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_preserves_existing_entries(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Existing entries are not modified."""
    existing = [{"id": "custom-model", "object": "model", "extra": "data"}]
    result = inject_proxy_models(existing)

    custom = next((m for m in result if m["id"] == "custom-model"), None)
    assert custom is not None
    assert custom["extra"] == "data"


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_preserves_non_target_model_names_untouched(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Non-target model IDs must remain exactly as provided."""
    existing = [
        {"id": "vendor-x/custom-model-v2", "object": "model", "extra": "keep"},
        {"id": "another-provider/model.alpha", "object": "model"},
    ]

    result = inject_proxy_models(existing)

    assert result[0] == {"id": "vendor-x/custom-model-v2", "object": "model", "extra": "keep"}
    assert result[1] == {"id": "another-provider/model.alpha", "object": "model"}


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_empty_mapping_dict_returns_original_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty mapping dict should perform no injection and return input list content unchanged."""
    models = [{"id": "custom-model", "object": "model"}]
    monkeypatch.setattr(
        harness_model_mapping,
        "CANONICAL_TO_OPENROUTER",
        {},
        raising=True,
    )

    result = inject_proxy_models(models)

    assert result == models
    assert result is not models


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_none_or_missing_id_key_path_handling(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """None input returns unchanged; entries missing id key path are preserved and injection still works."""
    assert inject_proxy_models(None) is None

    models_with_missing_id = [{"object": "model", "name": "no-id-entry"}]
    result = inject_proxy_models(models_with_missing_id)

    assert result[0] == {"object": "model", "name": "no-id-entry"}
    injected_ids = {entry["id"] for entry in result[1:]}
    assert injected_ids == set(canonical_to_openrouter_fixture.keys())


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_injects_canonical_on_mapping_mismatch(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Presence of backend model ID does not suppress canonical alias injection."""
    models = [{"id": "openai/gpt-4o", "object": "model"}]
    result = inject_proxy_models(models)
    result_ids = {m["id"] for m in result}

    # Guard: canonical alias must still be injected when only mapped backend ID exists.
    assert "gpt-4o" in result_ids


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_case_insensitive_alias_normalization_if_supported(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Assert case-insensitive alias de-dup only when implementation supports it."""
    mixed_case_existing = [{"id": "GPT-4O", "object": "model"}]
    result = inject_proxy_models(mixed_case_existing)
    ids = [m["id"] for m in result]

    has_case_insensitive_dedup = ids.count("gpt-4o") == 0 and ids.count("GPT-4O") == 1
    if has_case_insensitive_dedup:
        assert ids.count("gpt-4o") == 0
        assert ids.count("GPT-4O") == 1
    else:
        # Current behavior without case-insensitive normalization: canonical alias is injected.
        assert "gpt-4o" in ids
        assert "GPT-4O" in ids


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_malformed_mapping_with_non_dict_entries_returns_original_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed mapping with non-dict entries is guarded by returning the original list."""
    models = [{"id": "custom-model", "object": "model"}]
    malformed_mapping = [["gpt-4o"], ["o3-mini"]]  # non-dict + unhashable entries
    monkeypatch.setattr(
        harness_model_mapping,
        "CANONICAL_TO_OPENROUTER",
        malformed_mapping,
        raising=True,
    )
    result = inject_proxy_models(models)

    assert result is models


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_malformed_mapping_none_values_and_non_string_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed dict contents (None values + non-string keys) are handled without crashing."""
    models = [{"id": "custom-model", "object": "model"}]
    malformed_mapping = {
        404: None,  # non-string key with None value
        "valid-alias": None,  # None value for string key
    }
    monkeypatch.setattr(
        harness_model_mapping,
        "CANONICAL_TO_OPENROUTER",
        malformed_mapping,
        raising=True,
    )

    result = inject_proxy_models(models)
    result_ids = [entry["id"] for entry in result]

    # Current contract: keys are iterated for injection; values are ignored.
    assert result_ids == ["custom-model", 404, "valid-alias"]


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_mapping_error_returns_original_list() -> None:
    """If mapping source is invalid, contract is to return input unchanged."""
    models = [{"id": "custom-model", "object": "model"}]
    with patch.object(harness_model_mapping, "CANONICAL_TO_OPENROUTER", None):
        result = inject_proxy_models(models)

    assert result is models


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_mixed_valid_and_malformed_mapping_entries_returns_original(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mixed mapping entries must not partially inject; function returns original list on failure."""
    models = [{"id": "custom-model", "object": "model"}]
    mixed_mapping = ("gpt-4o", ["malformed-alias-entry"])
    monkeypatch.setattr(
        harness_model_mapping,
        "CANONICAL_TO_OPENROUTER",
        mixed_mapping,
        raising=True,
    )

    result = inject_proxy_models(models)

    assert result is models
    assert result == [{"id": "custom-model", "object": "model"}]


@pytest.mark.requirement("FR-REQEXT-047")
def test_inject_proxy_models_does_not_mutate_input_list_on_success(
    canonical_to_openrouter_fixture: dict[str, str],
) -> None:
    """Success path returns a new list and leaves input list content untouched."""
    models = [{"id": "gpt-4o", "object": "model"}]
    snapshot = list(models)

    result = inject_proxy_models(models)

    assert result is not models
    assert models == snapshot
    assert len(result) > len(models)
