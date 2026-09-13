"""Dynamic tools module for MCP server."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DynamicToolSpec:
    """Specification for a dynamic tool."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class DynamicToolCall:
    """Represents a dynamic tool call."""

    call_id: str
    session_id: str
    name: str
    arguments: dict[str, Any]
    timeout_seconds: float = 30.0
    requested_at: str = ""
    expires_at: str = ""


@dataclass
class PendingDynamicToolCall:
    """Represents a pending dynamic tool call."""

    call_id: str
    session_id: str
    name: str
    arguments: dict[str, Any]
    created_at: str = ""
    status: str = "pending"


@dataclass
class DynamicToolCallResult:
    """Result of a dynamic tool call."""

    call_id: str
    success: bool
    output: Any = None
    error: str = ""


class DynamicToolRegistry:
    """Registry for dynamic tools."""

    def __init__(self, default_timeout_seconds: float = 30.0) -> None:
        self.default_timeout_seconds = default_timeout_seconds
        self.tools: dict[
            str, dict[str, DynamicToolSpec]
        ] = {}  # session -> tool_name -> spec
        self.pending_calls: dict[str, DynamicToolCall] = {}
        self._call_counter = 0

    def register_dynamic_tool(
        self, session_id: str, tool_spec: DynamicToolSpec
    ) -> DynamicToolSpec:
        """Register a dynamic tool for a session."""
        if not session_id or not session_id.strip():
            raise ValueError("session_id must be non-empty")

        normalized_session = session_id.strip()
        normalized_name = tool_spec.name.strip()

        if not normalized_name:
            raise ValueError("tool name must be non-empty")

        if not tool_spec.description or not tool_spec.description.strip():
            raise ValueError("tool_spec.description must be non-empty")

        if not isinstance(tool_spec.input_schema, dict):
            raise ValueError("input_schema must be a dict")

        session_tools = self.tools.setdefault(normalized_session, {})
        if normalized_name in session_tools:
            raise ValueError(
                f"Tool '{normalized_name}' already registered for session '{normalized_session}'"
            )

        session_tools[normalized_name] = tool_spec
        return tool_spec

    def list_dynamic_tools(self, session_id: str) -> list[DynamicToolSpec]:
        """List dynamic tools for a session."""
        if not session_id:
            raise ValueError("session_id must be non-empty")
        return list(self.tools.get(session_id.strip(), {}).values())

    def create_tool_call(
        self,
        session_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        timeout_seconds: float = 30.0,
    ) -> PendingDynamicToolCall:
        """Create a tool call."""
        if not session_id or not session_id.strip():
            raise ValueError("session_id must be non-empty")

        normalized_session = session_id.strip()
        normalized_name = tool_name.strip()

        if not self.tools.get(normalized_session):
            raise KeyError(f"Tool '{normalized_name}' not registered")
        if normalized_name not in self.tools[normalized_session]:
            raise KeyError(f"Tool '{normalized_name}' not registered")

        self._call_counter += 1
        call_id = f"call-{self._call_counter}"
        now = time.time()

        # Store as DynamicToolCall for internal use
        call = DynamicToolCall(
            call_id=call_id,
            session_id=normalized_session,
            name=normalized_name,
            arguments=arguments,
            timeout_seconds=timeout_seconds,
            requested_at=str(now),
            expires_at=str(now + timeout_seconds),
        )
        self.pending_calls[call_id] = call

        # Return PendingDynamicToolCall
        return PendingDynamicToolCall(
            call_id=call_id,
            session_id=normalized_session,
            name=normalized_name,
            arguments=arguments,
            created_at=str(now),
            status="pending",
        )

    @staticmethod
    def tool_call_requested_event(
        call: PendingDynamicToolCall | DynamicToolCall,
    ) -> dict[str, Any]:
        """Get event for tool call request."""
        return {
            "event": "tool_call_requested",
            "callId": call.call_id,
            "sessionId": call.session_id,
            "name": call.name,
            "arguments": call.arguments,
        }

    def get_pending_call(self, call_id: str) -> DynamicToolCall:
        """Get a pending call by ID."""
        if call_id not in self.pending_calls:
            raise KeyError(f"unknown dynamic call id: {call_id}")
        return self.pending_calls[call_id]

    def resolve_tool_call(
        self, call_id: str, output: Any = None, success: bool = True, error: str = ""
    ) -> DynamicToolCallResult:
        """Resolve a tool call."""
        if call_id not in self.pending_calls:
            raise KeyError(f"unknown dynamic call id: {call_id}")

        call = self.pending_calls.pop(call_id)
        return DynamicToolCallResult(
            call_id=call.call_id,
            success=success,
            output=output,
            error=error,
        )

    @staticmethod
    def tool_call_completed_event(result: DynamicToolCallResult) -> dict[str, Any]:
        """Get event for tool call completion."""
        event = {
            "event": "tool_call_completed",
            "callId": result.call_id,
            "output": result.output,
            "success": result.success,
        }
        if result.error:
            event["error"] = result.error
        return event

    def pending_calls_for_session(self, session_id: str) -> list[DynamicToolCall]:
        """Get pending calls for a session."""
        if not session_id:
            raise ValueError("session_id must be non-empty")
        return [c for c in self.pending_calls.values() if c.session_id == session_id]

    def resolve_tool_call_for_session(
        self, session_id: str, call_id: str, output: Any = None, success: bool = True
    ) -> DynamicToolCallResult:
        """Resolve a tool call, enforcing session ownership."""
        call = self.pending_calls.get(call_id)
        if call is None:
            raise KeyError(f"unknown dynamic call id: {call_id}")
        if call.session_id != session_id.strip():
            raise KeyError(f"call {call_id} does not belong to session {session_id}")

        return self.resolve_tool_call(call_id, output=output, success=success)

    def clear_session(self, session_id: str) -> None:
        """Clear all tools and calls for a session."""
        if not session_id or not session_id.strip():
            raise ValueError("session_id must be non-empty")

        normalized = session_id.strip()
        if normalized in self.tools:
            del self.tools[normalized]

        # Remove pending calls for this session
        self.pending_calls = {
            k: v for k, v in self.pending_calls.items() if v.session_id != normalized
        }


# Global registry for tools sessions
class _ToolsSessions:
    """Manages tools sessions."""

    def __init__(self) -> None:
        self._dynamic_registry = DynamicToolRegistry()

    def reset_dynamic_registry_for_tests(self) -> None:
        """Reset the registry for testing."""
        self._dynamic_registry = DynamicToolRegistry()

    def session_send_impl(
        self,
        session_id: str,
        message: str,
        msg_type: str,
        send_impl: Any = None,
    ) -> str:
        """Handle session messages for dynamic tools."""
        import json as json_lib

        data = json_lib.loads(message)
        reg = self._dynamic_registry

        if msg_type == "dynamic_tool_register":
            spec = DynamicToolSpec(
                name=data["name"],
                description=data["description"],
                input_schema=data.get("input_schema", {}),
            )
            reg.register_dynamic_tool(session_id, spec)
            return json_lib.dumps({"success": True, "registered": {"name": spec.name}})

        elif msg_type == "dynamic_tool_list":
            tools = reg.list_dynamic_tools(session_id)
            return json_lib.dumps(
                {
                    "success": True,
                    "session_id": session_id,
                    "tools": [
                        {"name": t.name, "description": t.description} for t in tools
                    ],
                }
            )

        elif msg_type == "dynamic_tool_invoke":
            call = reg.create_tool_call(
                session_id, data["name"], data.get("arguments", {})
            )
            event = reg.tool_call_requested_event(call)
            return json_lib.dumps({"success": True, "event": event})

        elif msg_type == "dynamic_tool_complete":
            if not data.get("callId"):
                raise ValueError("callId must be non-empty")
            if (
                data.get("success") is False
                and not data.get("output")
                and not data.get("error")
            ):
                raise ValueError("Must provide output or error when success is False")
            result = reg.resolve_tool_call(
                data["callId"],
                output=data.get("output"),
                success=data.get("success", True),
                error=data.get("error", ""),
            )
            event = reg.tool_call_completed_event(result)
            return json_lib.dumps({"success": True, "event": event})

        return json_lib.dumps({"success": False, "error": "Unknown msg_type"})


# Global instance
_tools_sessions = _ToolsSessions()


async def thegent_register_tool(
    session_id: str,
    name: str,
    description: str,
    input_schema: dict[str, Any],
) -> str:
    """MCP tool: register a dynamic tool."""
    import json as json_lib

    spec = DynamicToolSpec(
        name=name, description=description, input_schema=input_schema
    )
    _tools_sessions._dynamic_registry.register_dynamic_tool(session_id, spec)
    return json_lib.dumps({"success": True, "registered": {"name": name}})


async def thegent_list_dynamic_tools(session_id: str) -> str:
    """MCP tool: list dynamic tools for a session."""
    import json as json_lib

    tools = _tools_sessions._dynamic_registry.list_dynamic_tools(session_id)
    return json_lib.dumps(
        {
            "success": True,
            "session_id": session_id,
            "tools": [{"name": t.name, "description": t.description} for t in tools],
        }
    )


async def thegent_complete_tool_call(
    session_id: str,
    call_id: str,
    output: Any = None,
    success: bool = True,
) -> str:
    """MCP tool: complete a dynamic tool call."""
    import json as json_lib

    result = _tools_sessions._dynamic_registry.resolve_tool_call(
        call_id, output=output, success=success
    )
    event = _tools_sessions._dynamic_registry.tool_call_completed_event(result)
    return json_lib.dumps({"success": True, "event": event})


__all__ = [
    "DynamicToolRegistry",
    "DynamicToolCall",
    "DynamicToolCallResult",
    "DynamicToolSpec",
    "PendingDynamicToolCall",
]
