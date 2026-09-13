"""Stub module."""

from dataclasses import dataclass


@dataclass
class AclCheckResult:
    """Result of an ACL check."""

    allowed: bool
    reason: str = ""


@dataclass
class AclRule:
    """An ACL rule."""

    id: str
    action: str  # allow or deny
    resource: str
    subject: str = "*"


class McpAcl:
    """MCP ACL manager."""

    def __init__(self) -> None:
        self._rules: list[AclRule] = []

    def check(self, resource: str, subject: str) -> AclCheckResult:
        """Check if access is allowed."""
        return AclCheckResult(allowed=True, reason="allowed")

    def add_rule(self, rule: AclRule) -> None:
        """Add an ACL rule."""
        self._rules.append(rule)


__all__ = ["AclCheckResult", "AclRule", "McpAcl", "check_mcp_acl"]


def check_mcp_acl(resource: str, subject: str) -> AclCheckResult:
    """Check MCP ACL for resource access."""
    return AclCheckResult(allowed=True, reason="allowed")
