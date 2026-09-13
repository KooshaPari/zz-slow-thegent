"""Tests for GW-23: Semantic cache (embedding-similarity-based LLM response cache).

All tests tagged with @pytest.mark.requirement("FR-CACHE-023").

Uses MockEmbeddingProvider to avoid requiring sentence_transformers in CI.
"""

from __future__ import annotations

import time

import pytest

from thegent.utils.routing_impl.semantic_cache import (
    NumpyEmbeddingProvider,
    SemanticCache,
    SemanticCacheConfig,
    cosine_similarity,
    extract_prompt_text,
    get_semantic_cache,
    reset_semantic_cache,
    semantic_cache_get,
    semantic_cache_set,
)

# ---------------------------------------------------------------------------
# Mock embedding provider
# ---------------------------------------------------------------------------


class MockEmbeddingProvider:
    """Deterministic embedding provider for tests.

    Returns the same embedding vector for every call. Use different instances
    with different vectors to simulate similar vs. dissimilar texts.
    """

    def __init__(self, embedding: list[float]) -> None:
        self._embedding = embedding

    def embed(self, text: str) -> list[float]:  # noqa: ARG002
        return self._embedding

    def is_available(self) -> bool:
        return True


class UnavailableProvider:
    """Always reports itself as unavailable."""

    def embed(self, _text: str) -> list[float]:
        raise RuntimeError("Provider is unavailable")

    def is_available(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UNIT_A = [1.0, 0.0, 0.0]
_UNIT_B = [0.0, 1.0, 0.0]  # orthogonal to A


def _cache(
    threshold: float = 0.95,
    max_entries: int = 500,
    ttl: float = 3600.0,
    provider: object | None = None,
) -> SemanticCache:
    """Build a SemanticCache with a MockEmbeddingProvider by default."""
    config = SemanticCacheConfig(
        similarity_threshold=threshold,
        max_entries=max_entries,
        ttl=ttl,
    )
    if provider is None:
        provider = MockEmbeddingProvider(_UNIT_A)
    return SemanticCache(config=config, provider=provider)


# ---------------------------------------------------------------------------
# cosine_similarity tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_cosine_similarity_identical_vectors() -> None:
    """Identical non-zero vectors must yield similarity 1.0."""
    score = cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert abs(score - 1.0) < 1e-9


@pytest.mark.requirement("FR-CACHE-023")
def test_cosine_similarity_orthogonal_vectors() -> None:
    """Orthogonal vectors must yield similarity 0.0."""
    score = cosine_similarity([1.0, 0.0], [0.0, 1.0])
    assert abs(score) < 1e-9


@pytest.mark.requirement("FR-CACHE-023")
def test_cosine_similarity_zero_vector() -> None:
    """Zero-norm vector must return 0.0 safely (no ZeroDivisionError)."""
    assert cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]) == 0.0
    assert cosine_similarity([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]) == 0.0
    assert cosine_similarity([0.0], [0.0]) == 0.0


# ---------------------------------------------------------------------------
# extract_prompt_text tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_extract_prompt_text_string_content() -> None:
    """String content fields should be concatenated."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "World"},
    ]
    result = extract_prompt_text(messages)
    assert result == "Hello World"


@pytest.mark.requirement("FR-CACHE-023")
def test_extract_prompt_text_content_array() -> None:
    """Content as a list of text blocks should be concatenated."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Part one"},
                {"type": "text", "text": "Part two"},
            ],
        }
    ]
    result = extract_prompt_text(messages)
    assert result == "Part one Part two"


@pytest.mark.requirement("FR-CACHE-023")
def test_extract_prompt_text_mixed() -> None:
    """Mix of string and list content should all be included."""
    messages = [
        {"role": "system", "content": "System prompt"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "User question"},
                {"type": "image_url", "url": "http://example.com/img.png"},
            ],
        },
    ]
    result = extract_prompt_text(messages)
    assert "System prompt" in result
    assert "User question" in result


# ---------------------------------------------------------------------------
# SemanticCache: basic miss
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_miss_returns_none() -> None:
    """Empty cache must return None for any query."""
    sc = _cache()
    result = sc.get("anything", namespace="ns1")
    assert result is None


# ---------------------------------------------------------------------------
# SemanticCache: set / get identical text
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_set_and_get_identical_text() -> None:
    """Setting then getting with the identical text (same embedding) must hit."""
    response = {"choices": [{"text": "Answer"}]}
    sc = _cache(threshold=0.95, provider=MockEmbeddingProvider(_UNIT_A))
    sc.set("What is 2+2?", response, namespace="math")
    result = sc.get("What is 2+2?", namespace="math")
    assert result == response


# ---------------------------------------------------------------------------
# SemanticCache: miss below threshold
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_miss_below_threshold() -> None:
    """When the best similarity is below threshold, None must be returned."""
    # Provider for stored entry uses UNIT_A; provider for query uses UNIT_B (orthogonal)
    response = {"choices": [{"text": "Answer"}]}

    # Store with UNIT_A
    store_provider = MockEmbeddingProvider(_UNIT_A)
    sc = SemanticCache(
        config=SemanticCacheConfig(similarity_threshold=0.95),
        provider=store_provider,
    )
    sc.set("question A", response, namespace="test")

    # Now switch provider to return orthogonal vector for the query
    sc._provider = MockEmbeddingProvider(_UNIT_B)
    result = sc.get("question B", namespace="test")
    assert result is None


# ---------------------------------------------------------------------------
# SemanticCache: similar text → hit (same mock embedding)
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_set_and_get_similar_text() -> None:
    """Two texts that produce the same embedding must both hit after one set."""
    response = {"answer": "42"}
    # Both texts produce identical embedding → similarity = 1.0 → above any threshold
    sc = _cache(threshold=0.95, provider=MockEmbeddingProvider(_UNIT_A))
    sc.set("What is the answer to life?", response, namespace="ns")
    # "different phrasing" also returns UNIT_A → hit
    result = sc.get("What is the answer to everything?", namespace="ns")
    assert result == response


# ---------------------------------------------------------------------------
# SemanticCache: expired entry not returned
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_expired_entry_not_returned() -> None:
    """Entries with TTL=0 should be immediately expired and not returned."""
    response = {"data": "ephemeral"}
    sc = SemanticCache(
        config=SemanticCacheConfig(ttl=0.0, similarity_threshold=0.5),
        provider=MockEmbeddingProvider(_UNIT_A),
    )
    sc.set("transient question", response, namespace="ns")
    # Allow the entry's created_at to age past TTL=0
    time.sleep(0.01)
    result = sc.get("transient question", namespace="ns")
    assert result is None


# ---------------------------------------------------------------------------
# SemanticCache: clear namespace
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_clear_namespace() -> None:
    """clear(namespace) must remove all entries in that namespace."""
    response = {"x": 1}
    sc = _cache()
    sc.set("q1", response, namespace="alpha")
    sc.set("q2", response, namespace="alpha")
    sc.set("q3", response, namespace="beta")

    removed = sc.clear(namespace="alpha")
    assert removed == 2
    # alpha is gone
    assert sc.get("q1", namespace="alpha") is None
    # beta is untouched
    assert sc.get("q3", namespace="beta") == response


# ---------------------------------------------------------------------------
# SemanticCache: max_entries eviction
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_max_entries_eviction() -> None:
    """After max_entries, the oldest entry must be evicted."""
    max_entries = 3
    sc = SemanticCache(
        config=SemanticCacheConfig(max_entries=max_entries, similarity_threshold=0.0),
        provider=MockEmbeddingProvider(_UNIT_A),
    )
    responses = [{"id": i} for i in range(max_entries + 1)]
    texts = [f"question {i}" for i in range(max_entries + 1)]

    for _, (text, resp) in enumerate(zip(texts, responses, strict=False)):
        sc.set(text, resp, namespace="ns")

    with sc._lock:
        entries = sc._store.get("ns", [])
    assert len(entries) == max_entries


# ---------------------------------------------------------------------------
# SemanticCache: unavailable provider
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_unavailable_provider_get_returns_none() -> None:
    """When the provider is unavailable, get() must return None without error."""
    sc = SemanticCache(
        config=SemanticCacheConfig(),
        provider=UnavailableProvider(),
    )
    result = sc.get("anything")
    assert result is None


@pytest.mark.requirement("FR-CACHE-023")
def test_semantic_cache_unavailable_provider_set_noop() -> None:
    """When the provider is unavailable, set() must be a silent no-op (no exception)."""
    sc = SemanticCache(
        config=SemanticCacheConfig(),
        provider=UnavailableProvider(),
    )
    sc.set("question", {"answer": "x"})  # must not raise
    with sc._lock:
        assert sc._store == {}


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_singleton_returns_same_instance() -> None:
    """get_semantic_cache() must return the same object on repeated calls."""
    reset_semantic_cache()
    a = get_semantic_cache()
    b = get_semantic_cache()
    assert a is b


@pytest.mark.requirement("FR-CACHE-023")
def test_reset_semantic_cache() -> None:
    """reset_semantic_cache() must cause get_semantic_cache() to return a new instance."""
    reset_semantic_cache()
    first = get_semantic_cache()
    reset_semantic_cache()
    second = get_semantic_cache()
    assert first is not second


# ---------------------------------------------------------------------------
# Convenience functions (smoke tests via singleton)
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_convenience_functions_roundtrip() -> None:
    """semantic_cache_set / semantic_cache_get must work end-to-end via singleton."""
    reset_semantic_cache()
    # Inject a mock provider into the freshly created singleton
    cache = get_semantic_cache()
    cache._provider = MockEmbeddingProvider(_UNIT_A)
    cache._config.similarity_threshold = 0.95

    response = {"result": "ok"}
    semantic_cache_set("test prompt", response, namespace="smoke")
    result = semantic_cache_get("test prompt", namespace="smoke")
    assert result == response

    # Cleanup
    reset_semantic_cache()


# ---------------------------------------------------------------------------
# NumpyEmbeddingProvider smoke test
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-023")
def test_numpy_provider_deterministic() -> None:
    """NumpyEmbeddingProvider must return the same vector for the same text."""
    provider = NumpyEmbeddingProvider(dim=64)
    if not provider.is_available():
        pytest.skip("numpy not installed")
    v1 = provider.embed("hello world")
    v2 = provider.embed("hello world")
    assert v1 == v2


@pytest.mark.requirement("FR-CACHE-023")
def test_numpy_provider_unit_vector() -> None:
    """NumpyEmbeddingProvider must return a unit vector (norm ≈ 1.0)."""
    provider = NumpyEmbeddingProvider(dim=128)
    if not provider.is_available():
        pytest.skip("numpy not installed")
    import math

    vec = provider.embed("unit test")
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-6


@pytest.mark.requirement("FR-CACHE-023")
def test_numpy_provider_different_texts_differ() -> None:
    """NumpyEmbeddingProvider should produce different vectors for different texts."""
    provider = NumpyEmbeddingProvider(dim=128)
    if not provider.is_available():
        pytest.skip("numpy not installed")
    v1 = provider.embed("apple")
    v2 = provider.embed("completely unrelated")
    # Very unlikely to collide by chance
    assert v1 != v2
