"""Unit tests for governance/providers.py hardening (AUDIT-N+68).

Contract surface: FR-GOV-PR-001..024
"""

import pytest

from thegent.governance.providers import (
    _BUILTIN_PROVIDERS,
    ProviderConfig,
    ProviderRegistry,
    ProviderType,
    _initialize_registry,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure a clean registry for every test to avoid ClassVar pollution."""
    ProviderRegistry.clear()
    ProviderRegistry._initialized = False
    _initialize_registry()
    yield
    ProviderRegistry.clear()
    ProviderRegistry._initialized = False


# ---------------------------------------------------------------------------
# FR-GOV-PR-001: ProviderType has exactly 2 members
# ---------------------------------------------------------------------------
class TestFRGOVPR001:
    def test_provider_type_has_exactly_two_members(self):
        members = list(ProviderType)
        assert len(members) == 2


# ---------------------------------------------------------------------------
# FR-GOV-PR-002: ProviderType.DIRECT.value == 'direct'
# ---------------------------------------------------------------------------
class TestFRGOVPR002:
    def test_direct_value(self):
        assert ProviderType.DIRECT.value == "direct"


# ---------------------------------------------------------------------------
# FR-GOV-PR-003: ProviderType.PROXY.value == 'proxy'
# ---------------------------------------------------------------------------
class TestFRGOVPR003:
    def test_proxy_value(self):
        assert ProviderType.PROXY.value == "proxy"


# ---------------------------------------------------------------------------
# FR-GOV-PR-004: ProviderConfig stores all fields
# ---------------------------------------------------------------------------
class TestFRGOVPR004:
    def test_config_stores_all_fields(self):
        cfg = ProviderConfig(
            provider_id="test-p",
            name="Test Provider",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://api.test.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.50,
            max_rpm=100,
            max_tpm=50000,
            fallback_order=["other-p"],
        )
        assert cfg.provider_id == "test-p"
        assert cfg.name == "Test Provider"
        assert cfg.provider_type == ProviderType.DIRECT
        assert cfg.api_endpoint == "https://api.test.com"
        assert cfg.auth_method == "api_key"
        assert cfg.cost_per_1m_tokens == 0.50
        assert cfg.max_rpm == 100
        assert cfg.max_tpm == 50000
        assert cfg.fallback_order == ["other-p"]


# ---------------------------------------------------------------------------
# FR-GOV-PR-005: ProviderConfig.fallback_order default is empty list
# ---------------------------------------------------------------------------
class TestFRGOVPR005:
    def test_fallback_order_default_empty(self):
        cfg = ProviderConfig(
            provider_id="no-fb",
            name="No Fallback",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://none.test",
            auth_method="api_key",
            cost_per_1m_tokens=0.01,
            max_rpm=1,
            max_tpm=1,
        )
        assert cfg.fallback_order == []


# ---------------------------------------------------------------------------
# FR-GOV-PR-006: ProviderRegistry.get returns None for unknown
# ---------------------------------------------------------------------------
class TestFRGOVPR006:
    def test_get_returns_none_for_unknown(self):
        result = ProviderRegistry.get("nonexistent-provider-id")
        assert result is None


# ---------------------------------------------------------------------------
# FR-GOV-PR-007: ProviderRegistry.register and get round-trip
# ---------------------------------------------------------------------------
class TestFRGOVPR007:
    def test_register_and_get_round_trip(self):
        cfg = ProviderConfig(
            provider_id="roundtrip-p",
            name="Roundtrip",
            provider_type=ProviderType.PROXY,
            api_endpoint="https://rt.test",
            auth_method="oauth",
            cost_per_1m_tokens=1.0,
            max_rpm=200,
            max_tpm=10000,
        )
        ProviderRegistry.register(cfg)
        got = ProviderRegistry.get("roundtrip-p")
        assert got is cfg


# ---------------------------------------------------------------------------
# FR-GOV-PR-008: ProviderRegistry.list_providers returns all
# ---------------------------------------------------------------------------
class TestFRGOVPR008:
    def test_list_providers_returns_all(self):
        ProviderRegistry.clear()
        for i in range(3):
            ProviderRegistry.register(
                ProviderConfig(
                    provider_id=f"lp-{i}",
                    name=f"LP {i}",
                    provider_type=ProviderType.DIRECT,
                    api_endpoint=f"https://{i}.test",
                    auth_method="api_key",
                    cost_per_1m_tokens=0.0,
                    max_rpm=1,
                    max_tpm=1,
                )
            )
        providers = ProviderRegistry.list_providers()
        assert len(providers) == 3
        ids = {p.provider_id for p in providers}
        assert ids == {"lp-0", "lp-1", "lp-2"}


# ---------------------------------------------------------------------------
# FR-GOV-PR-009: ProviderRegistry.get_fallback_order returns list
# ---------------------------------------------------------------------------
class TestFRGOVPR009:
    def test_get_fallback_order_returns_list(self):
        cfg = ProviderConfig(
            provider_id="fb-test",
            name="FB Test",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://fb.test",
            auth_method="api_key",
            cost_per_1m_tokens=0.1,
            max_rpm=10,
            max_tpm=1000,
            fallback_order=["a", "b", "c"],
        )
        ProviderRegistry.register(cfg)
        order = ProviderRegistry.get_fallback_order("fb-test")
        assert order == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# FR-GOV-PR-010: ProviderRegistry.get_fallback_order returns [] for unknown
# ---------------------------------------------------------------------------
class TestFRGOVPR010:
    def test_get_fallback_order_returns_empty_for_unknown(self):
        order = ProviderRegistry.get_fallback_order("unknown-id")
        assert order == []


# ---------------------------------------------------------------------------
# FR-GOV-PR-011: ProviderRegistry.unregister removes provider
# ---------------------------------------------------------------------------
class TestFRGOVPR011:
    def test_unregister_removes_provider(self):
        cfg = ProviderConfig(
            provider_id="unreg-p",
            name="Unreg",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://unreg.test",
            auth_method="api_key",
            cost_per_1m_tokens=0.01,
            max_rpm=1,
            max_tpm=1,
        )
        ProviderRegistry.register(cfg)
        assert ProviderRegistry.get("unreg-p") is not None
        ProviderRegistry.unregister("unreg-p")
        assert ProviderRegistry.get("unreg-p") is None


# ---------------------------------------------------------------------------
# FR-GOV-PR-012: ProviderRegistry.clear empties registry
# ---------------------------------------------------------------------------
class TestFRGOVPR012:
    def test_clear_empties_registry(self):
        ProviderRegistry.register(
            ProviderConfig(
                provider_id="clear-p",
                name="Clear",
                provider_type=ProviderType.DIRECT,
                api_endpoint="https://clear.test",
                auth_method="api_key",
                cost_per_1m_tokens=0.0,
                max_rpm=1,
                max_tpm=1,
            )
        )
        assert ProviderRegistry.count() >= 1
        ProviderRegistry.clear()
        assert ProviderRegistry.count() == 0


# ---------------------------------------------------------------------------
# FR-GOV-PR-013: ProviderRegistry.count returns correct count
# ---------------------------------------------------------------------------
class TestFRGOVPR013:
    def test_count_returns_correct_count(self):
        ProviderRegistry.clear()
        assert ProviderRegistry.count() == 0
        ProviderRegistry.register(
            ProviderConfig(
                provider_id="cnt-a",
                name="A",
                provider_type=ProviderType.DIRECT,
                api_endpoint="https://a.test",
                auth_method="api_key",
                cost_per_1m_tokens=0.0,
                max_rpm=1,
                max_tpm=1,
            )
        )
        assert ProviderRegistry.count() == 1
        ProviderRegistry.register(
            ProviderConfig(
                provider_id="cnt-b",
                name="B",
                provider_type=ProviderType.PROXY,
                api_endpoint="https://b.test",
                auth_method="api_key",
                cost_per_1m_tokens=0.0,
                max_rpm=1,
                max_tpm=1,
            )
        )
        assert ProviderRegistry.count() == 2


# ---------------------------------------------------------------------------
# FR-GOV-PR-014: Built-in providers: 5 total
# ---------------------------------------------------------------------------
class TestFRGOVPR014:
    def test_builtin_providers_count(self):
        assert len(_BUILTIN_PROVIDERS) == 5


# ---------------------------------------------------------------------------
# FR-GOV-PR-015: Built-in gemini-3-flash exists
# ---------------------------------------------------------------------------
class TestFRGOVPR015:
    def test_gemini_3_flash_exists(self):
        cfg = ProviderRegistry.get("gemini-3-flash")
        assert cfg is not None
        assert cfg.name == "Google Gemini 3 Flash"


# ---------------------------------------------------------------------------
# FR-GOV-PR-016: Built-in claude-haiku-4.5 exists
# ---------------------------------------------------------------------------
class TestFRGOVPR016:
    def test_claude_haiku_45_exists(self):
        cfg = ProviderRegistry.get("claude-haiku-4.5")
        assert cfg is not None
        assert cfg.name == "Anthropic Claude Haiku 4.5"


# ---------------------------------------------------------------------------
# FR-GOV-PR-017: Built-in gpt-4o-mini exists
# ---------------------------------------------------------------------------
class TestFRGOVPR017:
    def test_gpt_4o_mini_exists(self):
        cfg = ProviderRegistry.get("gpt-4o-mini")
        assert cfg is not None
        assert cfg.name == "OpenAI GPT-4o Mini"


# ---------------------------------------------------------------------------
# FR-GOV-PR-018: Built-in providers have fallback chains
# ---------------------------------------------------------------------------
class TestFRGOVPR018:
    def test_all_builtin_providers_have_fallback_chains(self):
        for cfg in _BUILTIN_PROVIDERS:
            assert isinstance(cfg.fallback_order, list), (
                f"{cfg.provider_id} fallback_order is not a list"
            )
            assert len(cfg.fallback_order) > 0, (
                f"{cfg.provider_id} has empty fallback_order"
            )


# ---------------------------------------------------------------------------
# FR-GOV-PR-019: _initialize_registry is idempotent
# ---------------------------------------------------------------------------
class TestFRGOVPR019:
    def test_initialize_registry_idempotent(self):
        ProviderRegistry.clear()
        ProviderRegistry._initialized = False
        _initialize_registry()
        count_after_first = ProviderRegistry.count()
        _initialize_registry()
        count_after_second = ProviderRegistry.count()
        assert count_after_first == count_after_second
        assert count_after_first == len(_BUILTIN_PROVIDERS)


# ---------------------------------------------------------------------------
# FR-GOV-PR-020: ProviderConfig.cost_per_1m_tokens is float
# ---------------------------------------------------------------------------
class TestFRGOVPR020:
    def test_cost_per_1m_tokens_is_float(self):
        for cfg in _BUILTIN_PROVIDERS:
            assert isinstance(cfg.cost_per_1m_tokens, float), (
                f"{cfg.provider_id} cost_per_1m_tokens is not float"
            )


# ---------------------------------------------------------------------------
# FR-GOV-PR-021: ProviderConfig.max_rpm is int
# ---------------------------------------------------------------------------
class TestFRGOVPR021:
    def test_max_rpm_is_int(self):
        for cfg in _BUILTIN_PROVIDERS:
            assert isinstance(cfg.max_rpm, int), f"{cfg.provider_id} max_rpm is not int"


# ---------------------------------------------------------------------------
# FR-GOV-PR-022: ProviderConfig.max_tpm is int
# ---------------------------------------------------------------------------
class TestFRGOVPR022:
    def test_max_tpm_is_int(self):
        for cfg in _BUILTIN_PROVIDERS:
            assert isinstance(cfg.max_tpm, int), f"{cfg.provider_id} max_tpm is not int"


# ---------------------------------------------------------------------------
# FR-GOV-PR-023: All built-in providers have non-empty api_endpoint
# ---------------------------------------------------------------------------
class TestFRGOVPR023:
    def test_all_builtin_providers_have_nonempty_api_endpoint(self):
        for cfg in _BUILTIN_PROVIDERS:
            assert cfg.api_endpoint, f"{cfg.provider_id} has empty api_endpoint"
            assert isinstance(cfg.api_endpoint, str)
            assert len(cfg.api_endpoint) > 0


# ---------------------------------------------------------------------------
# FR-GOV-PR-024: All built-in providers have auth_method='api_key'
# ---------------------------------------------------------------------------
class TestFRGOVPR024:
    def test_all_builtin_providers_auth_method_api_key(self):
        for cfg in _BUILTIN_PROVIDERS:
            assert cfg.auth_method == "api_key", (
                f"{cfg.provider_id} auth_method is '{cfg.auth_method}', expected 'api_key'"
            )
