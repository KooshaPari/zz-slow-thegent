"""Comprehensive tests for thegent.security.rbac module."""

from __future__ import annotations


class TestRoleEnum:
    """Tests for Role enum."""

    def test_role_values(self) -> None:
        """Role enum has expected values."""
        from thegent.security.rbac import Role

        assert Role.ADMIN.value == "admin"
        assert Role.OPERATOR.value == "operator"
        assert Role.AUDITOR.value == "auditor"

    def test_role_is_enum(self) -> None:
        """Role is a proper enum."""
        from thegent.security.rbac import Role

        assert hasattr(Role, "_value2member_map_")


class TestPermissionEnum:
    """Tests for Permission enum."""

    def test_permission_values(self) -> None:
        """Permission enum has expected values."""
        from thegent.security.rbac import Permission

        assert Permission.RUN_AGENT.value == "run_agent"
        assert Permission.PURGE_DATA.value == "purge_data"
        assert Permission.VIEW_LOGS.value == "view_logs"


class TestRBACManagerInit:
    """Tests for RBACManager initialization."""

    def test_init_creates_manager(self) -> None:
        """Manager initializes without error."""
        from thegent.security.rbac import RBACManager

        manager = RBACManager()
        assert manager is not None


class TestRBACManagerHasPermission:
    """Tests for RBACManager.has_permission method."""

    def test_admin_has_all_permissions(self) -> None:
        """Admin role has all permissions."""
        from thegent.security.rbac import Permission, RBACManager, Role

        manager = RBACManager()
        assert manager.has_permission(Role.ADMIN, Permission.RUN_AGENT) is True
        assert manager.has_permission(Role.ADMIN, Permission.PURGE_DATA) is True
        assert manager.has_permission(Role.ADMIN, Permission.VIEW_LOGS) is True

    def test_operator_has_limited_permissions(self) -> None:
        """Operator has limited permissions."""
        from thegent.security.rbac import Permission, RBACManager, Role

        manager = RBACManager()
        assert manager.has_permission(Role.OPERATOR, Permission.RUN_AGENT) is True
        assert manager.has_permission(Role.OPERATOR, Permission.PURGE_DATA) is False

    def test_auditor_read_only(self) -> None:
        """Auditor has read-only permissions."""
        from thegent.security.rbac import Permission, RBACManager, Role

        manager = RBACManager()
        assert manager.has_permission(Role.AUDITOR, Permission.VIEW_LOGS) is True
        assert manager.has_permission(Role.AUDITOR, Permission.RUN_AGENT) is False

    def test_incident_commander_has_emergency(self) -> None:
        """Incident commander has emergency override."""
        from thegent.security.rbac import Permission, RBACManager, Role

        manager = RBACManager()
        assert manager.has_permission(Role.INCIDENT_COMMANDER, Permission.EMERGENCY_OVERRIDE) is True

    def test_invalid_role_returns_false(self) -> None:
        """Invalid role returns False."""
        from thegent.security.rbac import Permission, RBACManager

        manager = RBACManager()
        assert manager.has_permission("not_a_role", Permission.RUN_AGENT) is False

    def test_invalid_permission_returns_false(self) -> None:
        """Invalid permission returns False."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        assert manager.has_permission(Role.ADMIN, "not_a_permission") is False


class TestRBACManagerCheckAccess:
    """Tests for RBACManager.check_access method."""

    def test_operator_standard_lane_allowed(self) -> None:
        """Operator can run in standard lane."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        result = manager.check_access(Role.OPERATOR, "run test", lane="standard")
        assert result["allowed"] is True

    def test_operator_critical_lane_denied(self) -> None:
        """Operator cannot run in critical lane."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        result = manager.check_access(Role.OPERATOR, "run test", lane="critical")
        assert result["allowed"] is False
        assert "critical lane" in result["reason"]

    def test_incident_commander_critical_lane_allowed(self) -> None:
        """Incident commander can run in critical lane."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        result = manager.check_access(Role.INCIDENT_COMMANDER, "run test", lane="critical")
        assert result["allowed"] is True

    def test_unknown_operation_denied(self) -> None:
        """Unknown operation returns not allowed."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        result = manager.check_access(Role.ADMIN, "completely_unknown_operation_xyz")
        assert result["allowed"] is False

    def test_invalid_role_denied(self) -> None:
        """Invalid role returns not allowed."""
        from thegent.security.rbac import RBACManager

        manager = RBACManager()
        result = manager.check_access("invalid_role", "run test")
        assert result["allowed"] is False


class TestRBACManagerMapOperation:
    """Tests for RBACManager._map_operation_to_permission method."""

    def test_orchestrate_run_maps_to_run_agent(self) -> None:
        """orchestrate run maps to RUN_AGENT."""
        from thegent.security.rbac import Permission, RBACManager

        manager = RBACManager()
        assert manager._map_operation_to_permission("orchestrate run") == Permission.RUN_AGENT

    def test_govern_purge_maps_to_purge_data(self) -> None:
        """govern purge maps to PURGE_DATA."""
        from thegent.security.rbac import Permission, RBACManager

        manager = RBACManager()
        assert manager._map_operation_to_permission("govern purge") == Permission.PURGE_DATA

    def test_logs_maps_to_view_logs(self) -> None:
        """logs maps to VIEW_LOGS."""
        from thegent.security.rbac import Permission, RBACManager

        manager = RBACManager()
        assert manager._map_operation_to_permission("logs") == Permission.VIEW_LOGS

    def test_unknown_operation_returns_none(self) -> None:
        """Unknown operation returns None."""
        from thegent.security.rbac import RBACManager

        manager = RBACManager()
        assert manager._map_operation_to_permission("completely_unknown") is None


class TestRBACManagerHelpers:
    """Tests for RBACManager helper methods."""

    def test_get_role_permissions(self) -> None:
        """get_role_permissions returns permissions for role."""
        from thegent.security.rbac import Permission, RBACManager, Role

        manager = RBACManager()
        perms = manager.get_role_permissions(Role.ADMIN)
        assert Permission.RUN_AGENT in perms

    def test_get_lane_access(self) -> None:
        """get_lane_access returns roles for lane."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        roles = manager.get_lane_access("critical")
        assert Role.ADMIN in roles
        assert Role.INCIDENT_COMMANDER in roles
        assert Role.OPERATOR not in roles


class TestRolePermissionsMapping:
    """Tests for role-permission mapping completeness."""

    def test_all_roles_have_permissions(self) -> None:
        """All roles have at least one permission."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        for role in Role:
            perms = manager.get_role_permissions(role)
            assert len(perms) > 0, f"Role {role} has no permissions"

    def test_admin_has_all_permissions(self) -> None:
        """Admin has all defined permissions."""
        from thegent.security.rbac import Permission, RBACManager, Role

        manager = RBACManager()
        admin_perms = manager.get_role_permissions(Role.ADMIN)
        for perm in Permission:
            assert perm in admin_perms, f"Admin missing {perm}"


class TestLaneAccessMapping:
    """Tests for lane access mapping."""

    def test_all_lanes_have_access(self) -> None:
        """All lanes have at least one role with access."""
        from thegent.security.rbac import RBACManager

        manager = RBACManager()
        for lane in ["standard", "critical", "restricted", "emergency"]:
            roles = manager.get_lane_access(lane)
            assert len(roles) > 0, f"Lane {lane} has no roles with access"

    def test_restricted_lane_admin_only(self) -> None:
        """Restricted lane is admin only."""
        from thegent.security.rbac import RBACManager, Role

        manager = RBACManager()
        roles = manager.get_lane_access("restricted")
        assert Role.ADMIN in roles
        assert len(roles) == 1
