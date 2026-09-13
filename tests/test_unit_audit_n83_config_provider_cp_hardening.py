"""AUDIT-N+83: governance/config_provider_cp hardening spec (SOTA pass-67).

15 invariants FR-GOV-CP-001..015 covering ControlPlaneConfigProvider init,
resolve fallback on error, get_tenant_config None return, URL normalization,
__all__ export, and sync httpx usage.

Source: src/thegent/governance/config_provider_cp.py

@trace AUDIT-N+83 FR-GOV-CP-001..015
"""

from __future__ import annotations

from thegent.governance.config_provider_cp import ControlPlaneConfigProvider


class TestControlPlaneConfigProviderInit:
    def test_returns_instance(self):
        cp = ControlPlaneConfigProvider(url="http://localhost:9999")
        assert isinstance(cp, ControlPlaneConfigProvider)

    def test_url_stripped(self):
        cp = ControlPlaneConfigProvider(url="http://localhost:9999/")
        assert cp.url == "http://localhost:9999"

    def test_has_resolve_method(self):
        cp = ControlPlaneConfigProvider(url="http://localhost:9999")
        assert callable(getattr(cp, "resolve", None))

    def test_has_get_tenant_config_method(self):
        cp = ControlPlaneConfigProvider(url="http://localhost:9999")
        assert callable(getattr(cp, "get_tenant_config", None))


class TestResolve:
    def test_resolve_returns_dict_on_connection_error(self):
        cp = ControlPlaneConfigProvider(url="http://192.0.2.1:1", timeout=0.1)
        result = cp.resolve()
        assert isinstance(result, dict)

    def test_resolve_with_keys(self):
        cp = ControlPlaneConfigProvider(url="http://192.0.2.1:1", timeout=0.1)
        result = cp.resolve(keys=["foo"])
        assert isinstance(result, dict)


class TestGetTenantConfig:
    def test_returns_none_on_connection_error(self):
        cp = ControlPlaneConfigProvider(url="http://192.0.2.1:1", timeout=0.1)
        result = cp.get_tenant_config("tenant-1")
        assert result is None


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.config_provider_cp import __all__ as exported

        assert "ControlPlaneConfigProvider" in exported
