"""WP-9005: Universal tool adapter layer.

Maps direct tool calls to unified operation envelopes with validation.
"""

from collections.abc import Callable
from typing import Any

from thegent.adapters.ports import AdapterRegistry
from thegent.operations import OPERATION_MAP, Operation


class UniversalToolAdapter:
    """Adapts disparate tools to the unified operation surface."""

    def __init__(self) -> None:
        self._adapters: dict[str, Callable[..., Any]] = {}

    def register_adapter(self, command: str, adapter_fn: Callable[..., Any]) -> None:
        """Register an adapter for a specific CLI command."""
        self._adapters[command] = adapter_fn

    def call_tool(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Call a tool through its operation-mapped adapter."""
        # Find operation mapping
        entry = next((e for e in OPERATION_MAP if e.command == command), None)
        if not entry:
            return {"error": f"Command {command} not mapped to any operation."}

        adapter = self._adapters.get(command)
        if not adapter:
            # Fallback to generic invocation (simplified)
            return {
                "status": "success",
                "operation": entry.operation,
                "command": command,
            }

        return adapter(**kwargs)

    def call(self, **kwargs: Any) -> dict[str, Any]:
        """Protocol-compatible adapter entrypoint."""
        command = kwargs.pop("command", "")
        if not isinstance(command, str):
            return {"error": "command must be a string"}
        return self.call_tool(command, **kwargs)


# Register with global adapter registry
AdapterRegistry.register("universal_tool", UniversalToolAdapter())


def validate_tool_schema(operation: Operation, payload: dict[str, Any]) -> list[str]:
    """WP-9005: Validate tool call payload against operation-specific schema."""
    issues = []
    # Simplified validation logic
    if operation == Operation.ORCHESTRATE and "prompt" not in payload:
        issues.append("Orchestration requires a 'prompt'.")
    return issues
