"""Tests for thegent.integrations.tenant_namespace — Tenancy-safe namespacing.

@trace WL-217
"""

from __future__ import annotations

import pytest

from thegent.integrations.tenant_namespace import (
    TenantNamespace,
    TenantNamespaceResolver,
)


class TestTenantNamespace:
    """Test TenantNamespace dataclass. @trace WL-217"""

    @pytest.mark.requirement("WL-217")
    def test_create_namespace(self) -> None:
        """Can create a TenantNamespace with all fields."""
        ns = TenantNamespace(tenant_id="org-123", prefix="org-123")

        assert ns.tenant_id == "org-123"
        assert ns.prefix == "org-123"

    @pytest.mark.requirement("WL-217")
    def test_namespace_fields_accessible(self) -> None:
        """Fields of TenantNamespace are accessible."""
        ns = TenantNamespace(tenant_id="tenant-A", prefix="tenant-A")

        assert ns.tenant_id == "tenant-A"
        assert ns.prefix == "tenant-A"


class TestTenantNamespaceResolver:
    """Test TenantNamespaceResolver operations. @trace WL-217"""

    @pytest.fixture
    def resolver(self) -> TenantNamespaceResolver:
        """Provide a TenantNamespaceResolver instance."""
        return TenantNamespaceResolver("tenant-123")

    @pytest.mark.requirement("WL-217")
    def test_namespace_single_key(self, resolver: TenantNamespaceResolver) -> None:
        """Can namespace a single key."""
        result = resolver.namespace("api-key")

        assert result == "tenant-123:api-key"

    @pytest.mark.requirement("WL-217")
    def test_namespace_empty_key(self, resolver: TenantNamespaceResolver) -> None:
        """Can namespace an empty key."""
        result = resolver.namespace("")

        assert result == "tenant-123:"

    @pytest.mark.requirement("WL-217")
    def test_strip_namespace_valid_key(self, resolver: TenantNamespaceResolver) -> None:
        """Can strip namespace from a valid namespaced key."""
        namespaced = "tenant-123:api-key"
        result = resolver.strip_namespace(namespaced)

        assert result == "api-key"

    @pytest.mark.requirement("WL-217")
    def test_strip_namespace_wrong_tenant(
        self, resolver: TenantNamespaceResolver
    ) -> None:
        """Raises ValueError when stripping key from wrong tenant."""
        namespaced = "other-tenant:api-key"

        with pytest.raises(ValueError, match="does not belong to tenant"):
            resolver.strip_namespace(namespaced)

    @pytest.mark.requirement("WL-217")
    def test_strip_namespace_no_prefix(self, resolver: TenantNamespaceResolver) -> None:
        """Raises ValueError when key has no namespace prefix."""
        with pytest.raises(ValueError, match="does not belong to tenant"):
            resolver.strip_namespace("api-key")

    @pytest.mark.requirement("WL-217")
    def test_is_owned_true(self, resolver: TenantNamespaceResolver) -> None:
        """is_owned returns True for owned keys."""
        assert resolver.is_owned("tenant-123:api-key") is True

    @pytest.mark.requirement("WL-217")
    def test_is_owned_false_wrong_tenant(
        self, resolver: TenantNamespaceResolver
    ) -> None:
        """is_owned returns False for keys from other tenants."""
        assert resolver.is_owned("other-tenant:api-key") is False

    @pytest.mark.requirement("WL-217")
    def test_is_owned_false_no_prefix(self, resolver: TenantNamespaceResolver) -> None:
        """is_owned returns False for keys without prefix."""
        assert resolver.is_owned("api-key") is False

    @pytest.mark.requirement("WL-217")
    def test_namespace_dict_empty(self, resolver: TenantNamespaceResolver) -> None:
        """namespace_dict handles empty dictionary."""
        result = resolver.namespace_dict({})

        assert result == {}

    @pytest.mark.requirement("WL-217")
    def test_namespace_dict_multiple_keys(
        self, resolver: TenantNamespaceResolver
    ) -> None:
        """namespace_dict namespaces all keys in dictionary."""
        data = {"key1": "value1", "key2": "value2"}
        result = resolver.namespace_dict(data)

        assert result == {"tenant-123:key1": "value1", "tenant-123:key2": "value2"}

    @pytest.mark.requirement("WL-217")
    def test_strip_dict_valid(self, resolver: TenantNamespaceResolver) -> None:
        """strip_dict removes namespace from all keys."""
        data = {"tenant-123:key1": "value1", "tenant-123:key2": "value2"}
        result = resolver.strip_dict(data)

        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.requirement("WL-217")
    def test_strip_dict_mixed_tenants_raises(
        self, resolver: TenantNamespaceResolver
    ) -> None:
        """strip_dict raises ValueError if any key doesn't belong to tenant."""
        data = {"tenant-123:key1": "value1", "other-tenant:key2": "value2"}

        with pytest.raises(ValueError, match="does not belong to tenant"):
            resolver.strip_dict(data)

    @pytest.mark.requirement("WL-217")
    def test_strip_dict_empty(self, resolver: TenantNamespaceResolver) -> None:
        """strip_dict handles empty dictionary."""
        result = resolver.strip_dict({})

        assert result == {}
