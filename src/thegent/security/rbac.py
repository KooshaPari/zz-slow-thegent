"""Role-Based Access Control (RBAC) for thegent."""

from __future__ import annotations

from enum import Enum
from typing import Any


class Role(Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    INCIDENT_COMMANDER = "incident_commander"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class Permission(Enum):
    """Permissions for RBAC."""

    RUN_AGENT = "run_agent"
    PURGE_DATA = "purge_data"
    VIEW_LOGS = "view_logs"
    MANAGE_USERS = "manage_users"
    VIEW_METRICS = "view_metrics"
    CONFIGURE_SYSTEM = "configure_system"
    EMERGENCY_OVERRIDE = "emergency_override"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        Permission.RUN_AGENT,
        Permission.PURGE_DATA,
        Permission.VIEW_LOGS,
        Permission.MANAGE_USERS,
        Permission.VIEW_METRICS,
        Permission.CONFIGURE_SYSTEM,
        Permission.EMERGENCY_OVERRIDE,
    },
    Role.OPERATOR: {
        Permission.RUN_AGENT,
        Permission.VIEW_LOGS,
        Permission.VIEW_METRICS,
    },
    Role.AUDITOR: {
        Permission.VIEW_LOGS,
        Permission.VIEW_METRICS,
    },
    Role.INCIDENT_COMMANDER: {
        Permission.RUN_AGENT,
        Permission.VIEW_LOGS,
        Permission.EMERGENCY_OVERRIDE,
    },
    Role.DEVELOPER: {
        Permission.RUN_AGENT,
        Permission.VIEW_LOGS,
    },
    Role.VIEWER: {
        Permission.VIEW_LOGS,
    },
}


LANE_ACCESS: dict[str, set[Role]] = {
    "standard": {Role.ADMIN, Role.OPERATOR, Role.DEVELOPER, Role.VIEWER},
    "critical": {Role.ADMIN, Role.INCIDENT_COMMANDER},
    "restricted": {Role.ADMIN},
    "emergency": {Role.ADMIN, Role.INCIDENT_COMMANDER},
}


OPERATION_PERMISSION_MAP: dict[str, Permission] = {
    "orchestrate run": Permission.RUN_AGENT,
    "run": Permission.RUN_AGENT,
    "run test": Permission.RUN_AGENT,
    "govern purge": Permission.PURGE_DATA,
    "purge": Permission.PURGE_DATA,
    "logs": Permission.VIEW_LOGS,
    "logs --session": Permission.VIEW_LOGS,
    "view logs": Permission.VIEW_LOGS,
    "manage users": Permission.MANAGE_USERS,
    "add user": Permission.MANAGE_USERS,
    "remove user": Permission.MANAGE_USERS,
    "metrics": Permission.VIEW_METRICS,
    "view metrics": Permission.VIEW_METRICS,
    "configure": Permission.CONFIGURE_SYSTEM,
    "system configure": Permission.CONFIGURE_SYSTEM,
    "emergency": Permission.EMERGENCY_OVERRIDE,
}


class RBACManager:
    """Role-Based Access Control manager."""

    def __init__(self) -> None:
        """Initialize RBAC manager."""
        self._role_permissions = ROLE_PERMISSIONS.copy()
        self._lane_access = LANE_ACCESS.copy()

    def has_permission(self, role: Role, permission: Permission) -> bool:
        """Check if a role has a specific permission.

        Args:
            role: The role to check.
            permission: The permission to verify.

        Returns:
            True if role has the permission, False otherwise.
        """
        if not isinstance(role, Role):
            return False
        if not isinstance(permission, Permission):
            return False

        role_perms = self._role_permissions.get(role, set())
        return permission in role_perms

    def check_access(
        self,
        role: Role,
        operation: str,
        lane: str | None = None,
    ) -> dict[str, Any]:
        """Check if a role has access to perform an operation.

        Args:
            role: The role attempting the operation.
            operation: The operation being attempted.
            lane: Optional lane for agent operations.

        Returns:
            Dictionary with 'allowed' bool and 'reason' string.
        """
        if not isinstance(role, Role):
            return {
                "allowed": False,
                "reason": "Invalid role provided",
            }

        permission = self._map_operation_to_permission(operation)

        if permission is None:
            return {
                "allowed": False,
                "reason": f"Unknown operation: {operation}",
            }

        if not self.has_permission(role, permission):
            return {
                "allowed": False,
                "reason": f"Role {role.value} lacks required permission: {permission.value}",
            }

        if lane is not None:
            allowed_lanes = self._lane_access.get(lane, set())
            if role not in allowed_lanes:
                return {
                    "allowed": False,
                    "reason": f"Role {role.value} does not have access to {lane} lane",
                }

        return {
            "allowed": True,
            "reason": f"Access granted for {operation}",
        }

    def _map_operation_to_permission(self, operation: str) -> Permission | None:
        """Map an operation string to a Permission.

        Args:
            operation: Operation string to map.

        Returns:
            Corresponding Permission or None if not found.
        """
        op_lower = operation.lower().strip()

        for op_pattern, perm in OPERATION_PERMISSION_MAP.items():
            if op_pattern in op_lower:
                return perm

        return None

    def _role_from_settings(self) -> Role:
        """Get the current role from settings.

        Returns:
            Role from settings, defaults to VIEWER.
        """
        return Role.VIEWER

    def get_role_permissions(self, role: Role) -> set[Permission]:
        """Get all permissions for a role.

        Args:
            role: The role to get permissions for.

        Returns:
            Set of permissions for the role.
        """
        return self._role_permissions.get(role, set()).copy()

    def get_lane_access(self, lane: str) -> set[Role]:
        """Get all roles that can access a lane.

        Args:
            lane: The lane to check.

        Returns:
            Set of roles that can access the lane.
        """
        return self._lane_access.get(lane, set()).copy()


__all__ = [
    "Permission",
    "RBACManager",
    "Role",
]
