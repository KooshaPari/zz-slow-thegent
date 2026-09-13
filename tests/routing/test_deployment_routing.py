"""Tests for GW-17 (provider budget routing), GW-18 (deployment pools), and GW-21 (session stickiness).

@trace FR-ROUTE-017
@trace FR-ROUTE-021
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.cost_aware_router import (
    DeploymentConfig,
    DeploymentPool,
    DeploymentPoolManager,
    ProviderBudgetConfig,
    ProviderBudgetRouter,
    SessionStickyRouter,
    get_session_sticky_extra,
)

# ---------------------------------------------------------------------------
# GW-17: Provider budget routing
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-017")
def test_provider_budget_blocks_over_limit() -> None:
    """After spending over daily limit, the over-budget provider is filtered out."""
    configs = [
        ProviderBudgetConfig(provider="openai", daily_limit_usd=5.0),
        ProviderBudgetConfig(provider="anthropic", daily_limit_usd=10.0),
    ]
    router = ProviderBudgetRouter(configs)

    model_list = [
        {"model_name": "gpt-4o", "litellm_params": {"model": "openai/gpt-4o"}},
        {"model_name": "claude-opus-4.6", "litellm_params": {"model": "anthropic/claude-opus-4.6"}},
    ]

    # Before any spend: both providers available
    filtered = router.filter_model_list(model_list)
    assert len(filtered) == 2

    # Exceed openai daily limit
    router.record_spend("openai", 6.0)
    assert router.is_provider_over_budget("openai") is True
    assert router.is_provider_over_budget("anthropic") is False

    filtered = router.filter_model_list(model_list)
    assert len(filtered) == 1
    assert filtered[0]["model_name"] == "claude-opus-4.6"


@pytest.mark.requirement("FR-ROUTE-017")
def test_provider_budget_falls_back_when_all_over() -> None:
    """If all providers are over budget, filter_model_list returns the full list."""
    configs = [
        ProviderBudgetConfig(provider="openai", daily_limit_usd=1.0),
        ProviderBudgetConfig(provider="anthropic", daily_limit_usd=1.0),
    ]
    router = ProviderBudgetRouter(configs)

    model_list = [
        {"model_name": "gpt-4o", "litellm_params": {"model": "openai/gpt-4o"}},
        {"model_name": "claude-opus-4.6", "litellm_params": {"model": "anthropic/claude-opus-4.6"}},
    ]

    router.record_spend("openai", 2.0)
    router.record_spend("anthropic", 2.0)

    # Both over budget -> must return full list (fail-open)
    filtered = router.filter_model_list(model_list)
    assert len(filtered) == 2


@pytest.mark.requirement("FR-ROUTE-017")
def test_provider_budget_reset_daily() -> None:
    """reset_daily clears all daily spend counters."""
    configs = [ProviderBudgetConfig(provider="openai", daily_limit_usd=5.0)]
    router = ProviderBudgetRouter(configs)

    router.record_spend("openai", 6.0)
    assert router.is_provider_over_budget("openai") is True

    router.reset_daily()
    assert router.is_provider_over_budget("openai") is False


@pytest.mark.requirement("FR-ROUTE-017")
def test_provider_budget_spend_summary() -> None:
    """get_spend_summary returns correct spent/limit/remaining values."""
    configs = [
        ProviderBudgetConfig(provider="openai", daily_limit_usd=10.0),
        ProviderBudgetConfig(provider="anthropic", daily_limit_usd=20.0),
    ]
    router = ProviderBudgetRouter(configs)
    router.record_spend("openai", 3.5)
    router.record_spend("anthropic", 0.0)

    summary = router.get_spend_summary()

    assert "openai" in summary
    assert summary["openai"]["spent"] == pytest.approx(3.5)
    assert summary["openai"]["limit"] == pytest.approx(10.0)
    assert summary["openai"]["remaining"] == pytest.approx(6.5)

    assert "anthropic" in summary
    assert summary["anthropic"]["spent"] == pytest.approx(0.0)
    assert summary["anthropic"]["limit"] == pytest.approx(20.0)
    assert summary["anthropic"]["remaining"] == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# GW-18: Deployment pool concept
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-017")
def test_deployment_pool_to_litellm_format() -> None:
    """DeploymentPoolManager.to_litellm_model_list produces correct LiteLLM entries."""
    pool = DeploymentPool(
        name="gpt-4o",
        deployments=[
            DeploymentConfig(provider="openai", model="gpt-4o", weight=1.0, api_base="https://api.openai.com/v1"),
            DeploymentConfig(provider="openai", model="gpt-4o", weight=2.0, api_base="https://api2.openai.com/v1"),
        ],
    )
    manager = DeploymentPoolManager([pool])
    entries = manager.to_litellm_model_list()

    assert len(entries) == 2
    for entry in entries:
        assert entry["model_name"] == "gpt-4o"
        assert entry["litellm_params"]["model"] == "openai/gpt-4o"
        assert "api_base" in entry["litellm_params"]

    weights = {entry["litellm_params"]["weight"] for entry in entries}
    assert weights == {1.0, 2.0}


@pytest.mark.requirement("FR-ROUTE-017")
def test_deployment_pool_weighted() -> None:
    """All deployments in the pool share the same logical model_name."""
    deployments = [
        DeploymentConfig(provider="openai", model="gpt-4o", weight=1.0),
        DeploymentConfig(provider="openai", model="gpt-4o", weight=3.0),
        DeploymentConfig(provider="openai", model="gpt-4o", weight=5.0),
    ]
    pool = DeploymentPool(name="gpt-4o", deployments=deployments, strategy="weighted")
    manager = DeploymentPoolManager([pool])
    entries = manager.to_litellm_model_list()

    assert len(entries) == 3
    model_names = {e["model_name"] for e in entries}
    assert model_names == {"gpt-4o"}


@pytest.mark.requirement("FR-ROUTE-017")
def test_deployment_pool_add_and_get() -> None:
    """add_pool replaces existing pool; get_pool retrieves it."""
    manager = DeploymentPoolManager([])

    pool_v1 = DeploymentPool(
        name="my-model",
        deployments=[DeploymentConfig(provider="openai", model="gpt-4o")],
    )
    manager.add_pool(pool_v1)
    assert manager.get_pool("my-model") is pool_v1

    pool_v2 = DeploymentPool(
        name="my-model",
        deployments=[
            DeploymentConfig(provider="openai", model="gpt-4o"),
            DeploymentConfig(provider="openai", model="gpt-4o"),
        ],
    )
    manager.add_pool(pool_v2)
    retrieved = manager.get_pool("my-model")
    assert retrieved is pool_v2
    assert len(retrieved.deployments) == 2


# ---------------------------------------------------------------------------
# GW-21: Session stickiness
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-021")
def test_session_sticky_consistent() -> None:
    """Same session_id always maps to the same deployment."""
    pool = DeploymentPool(
        name="gpt-4o",
        deployments=[
            DeploymentConfig(provider="openai", model="gpt-4o", api_base="https://ep1.openai.com/v1"),
            DeploymentConfig(provider="openai", model="gpt-4o", api_base="https://ep2.openai.com/v1"),
            DeploymentConfig(provider="openai", model="gpt-4o", api_base="https://ep3.openai.com/v1"),
        ],
    )
    manager = DeploymentPoolManager([pool])
    sticky = SessionStickyRouter(manager)

    session_id = "session-abc-123"
    first = sticky.get_deployment_for_session("gpt-4o", session_id)
    assert first is not None

    # Multiple calls must return the identical deployment object
    for _ in range(10):
        result = sticky.get_deployment_for_session("gpt-4o", session_id)
        assert result is first


@pytest.mark.requirement("FR-ROUTE-021")
def test_session_sticky_different_sessions() -> None:
    """Different session_ids can map to different deployments."""
    deployments = [
        DeploymentConfig(provider="openai", model="gpt-4o", api_base=f"https://ep{i}.openai.com/v1") for i in range(5)
    ]
    pool = DeploymentPool(name="gpt-4o", deployments=deployments)
    manager = DeploymentPoolManager([pool])
    sticky = SessionStickyRouter(manager)

    session_ids = [f"session-{i}" for i in range(20)]
    endpoints = {sticky.get_deployment_for_session("gpt-4o", sid).api_base for sid in session_ids}  # type: ignore[union-attr]

    # With 20 sessions and 5 endpoints, at least 2 distinct endpoints should be chosen
    assert len(endpoints) >= 2


@pytest.mark.requirement("FR-ROUTE-021")
def test_session_sticky_returns_none_for_unknown_model() -> None:
    """get_deployment_for_session returns None when no pool exists for the model."""
    manager = DeploymentPoolManager([])
    sticky = SessionStickyRouter(manager)

    result = sticky.get_deployment_for_session("unknown-model", "session-xyz")
    assert result is None


@pytest.mark.requirement("FR-ROUTE-021")
def test_get_session_sticky_extra_returns_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_session_sticky_extra returns dict with api_base and api_key when available."""
    monkeypatch.setenv("MY_OPENAI_KEY", "sk-test-123")

    pool = DeploymentPool(
        name="gpt-4o",
        deployments=[
            DeploymentConfig(
                provider="openai",
                model="gpt-4o",
                api_base="https://ep1.openai.com/v1",
                api_key_env="MY_OPENAI_KEY",
            ),
        ],
    )
    manager = DeploymentPoolManager([pool])

    extra = get_session_sticky_extra("gpt-4o", "session-abc", pool_manager=manager)

    assert extra.get("api_base") == "https://ep1.openai.com/v1"
    assert extra.get("api_key") == "sk-test-123"


@pytest.mark.requirement("FR-ROUTE-021")
def test_get_session_sticky_extra_no_session() -> None:
    """get_session_sticky_extra returns empty dict when session_id is None."""
    pool = DeploymentPool(
        name="gpt-4o",
        deployments=[DeploymentConfig(provider="openai", model="gpt-4o")],
    )
    manager = DeploymentPoolManager([pool])

    extra = get_session_sticky_extra("gpt-4o", None, pool_manager=manager)
    assert extra == {}


@pytest.mark.requirement("FR-ROUTE-021")
def test_get_session_sticky_extra_no_pool_manager() -> None:
    """get_session_sticky_extra returns empty dict when pool_manager is None."""
    extra = get_session_sticky_extra("gpt-4o", "session-xyz", pool_manager=None)
    assert extra == {}


@pytest.mark.requirement("FR-ROUTE-021")
def test_get_session_sticky_extra_unknown_model() -> None:
    """get_session_sticky_extra returns empty dict when model has no pool."""
    manager = DeploymentPoolManager([])
    extra = get_session_sticky_extra("no-such-model", "session-xyz", pool_manager=manager)
    assert extra == {}
