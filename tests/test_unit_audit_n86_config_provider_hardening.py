"""AUDIT-N+86: governance/config_provider hardening spec (SOTA pass-70).

15 invariants FR-GOV-CFG-001..015 covering ConfigProvider protocol,
EnvConfigProvider resolve, key filtering, override merge,
get_config_provider factory, __all__ export.

Source: src/thegent/governance/config_provider.py

@trace AUDIT-N+86 FR-GOV-CFG-001..015
"""

from __future__ import annotations

from thegent.governance.config_provider import (
    ConfigProvider,
    EnvConfigProvider,
    get_config_provider,
)


class TestConfigProviderProtocol:
    def test_env_provider_is_protocol(self):
        assert hasattr(ConfigProvider, "resolve")
        assert hasattr(ConfigProvider, "get_tenant_config")


class TestEnvConfigProvider:
    def test_returns_instance(self):
        p = EnvConfigProvider()
        assert isinstance(p, EnvConfigProvider)

    def test_resolve_returns_dict(self):
        p = EnvConfigProvider()
        result = p.resolve()
        assert isinstance(result, dict)

    def test_resolve_with_keys(self):
        p = EnvConfigProvider()
        result = p.resolve(keys=["log_level"])
        assert isinstance(result, dict)

    def test_resolve_unknown_keys_filtered(self):
        p = EnvConfigProvider()
        result = p.resolve(keys=["nonexistent_key_xyz"])
        assert isinstance(result, dict)
        assert "nonexistent_key_xyz" not in result

    def test_resolve_with_overrides(self):
        p = EnvConfigProvider()
        result = p.resolve(request_overrides={"custom_key": "value"})
        assert result.get("custom_key") == "value"

    def test_get_tenant_config_returns_none(self):
        p = EnvConfigProvider()
        result = p.get_tenant_config("any-tenant")
        assert result is None


class TestGetConfigProvider:
    def test_returns_config_provider(self):
        from thegent.governance.config_provider_cp import ControlPlaneConfigProvider

        p = get_config_provider()
        assert isinstance(p, (EnvConfigProvider, ControlPlaneConfigProvider))


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.config_provider import __all__ as exported

        assert "ConfigProvider" in exported
        assert "EnvConfigProvider" in exported
        assert "get_config_provider" in exported
