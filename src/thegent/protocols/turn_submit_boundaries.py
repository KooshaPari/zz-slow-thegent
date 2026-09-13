"""Turn/Submit phase boundaries protocol.

This module defines the phase boundaries for turn/submit protocol,
managing the lifecycle of agent interactions including parsing,
committing, side effects, and response phases.
"""

from __future__ import annotations

from typing import Any


def build_parse_phase(
    session_id: str,
    user_input: str,
    *,
    request_id: str | None = None,
    request_has_id: bool = False,
) -> dict[str, Any]:
    """Build a parse phase payload.

    Args:
        session_id: The session identifier.
        user_input: The user's input text.
        request_id: Optional request identifier.
        request_has_id: Whether the request has an ID.

    Returns:
        Parse phase payload dictionary.
    """
    return {
        "session_id": session_id,
        "user_input": user_input,
        "request_id": request_id or "",
        "request_has_id": request_has_id,
    }


def resolve_parse_target(phase: dict[str, Any]) -> tuple[str, str, str, bool]:
    """Resolve the parse phase target.

    Args:
        phase: Parse phase payload.

    Returns:
        Tuple of (session_id, user_input, request_id, request_has_id).

    Raises:
        ValueError: If target cannot be resolved.
    """
    session_id = phase.get("session_id", "")
    user_input = phase.get("user_input", "")
    request_id = phase.get("request_id", "")
    request_has_id = phase.get("request_has_id", False)

    if not session_id:
        raise ValueError("parse target unresolved: missing session_id")

    return (session_id, user_input, request_id, request_has_id)


def build_commit_phase(
    session_id: str,
    session: dict[str, Any],
    turn_id: str,
    turn: dict[str, Any],
) -> dict[str, Any]:
    """Build a commit phase payload.

    Args:
        session_id: The session identifier.
        session: The session object.
        turn_id: The turn identifier.
        turn: The turn object.

    Returns:
        Commit phase payload dictionary.
    """
    return {
        "session_id": session_id,
        "session": session,
        "turn_id": turn_id,
        "turn": turn,
    }


def resolve_commit_target(
    phase: dict[str, Any],
) -> tuple[str, dict, str, dict]:
    """Resolve the commit phase target.

    Args:
        phase: Commit phase payload.

    Returns:
        Tuple of (session_id, session, turn_id, turn).

    Raises:
        ValueError: If target cannot be resolved.
    """
    session_id = phase.get("session_id", "")
    session = phase.get("session")
    turn_id = phase.get("turn_id", "")
    turn = phase.get("turn")

    if not session_id or session is None or turn is None:
        raise ValueError("commit target unresolved: missing required fields")

    return (session_id, session, turn_id, turn)


def build_side_effects_phase(
    session_id: str,
    turn_id: str,
    turn: dict[str, Any],
    response: str,
    requires_approval: bool,
    approval_diff: str | None,
) -> dict[str, Any]:
    """Build a side effects phase payload.

    Args:
        session_id: The session identifier.
        turn_id: The turn identifier.
        turn: The turn object.
        response: The agent response.
        requires_approval: Whether approval is required.
        approval_diff: Optional diff for approval.

    Returns:
        Side effects phase payload dictionary.
    """
    return {
        "session_id": session_id,
        "turn_id": turn_id,
        "turn": turn,
        "response": response,
        "requires_approval": requires_approval,
        "approval_diff": approval_diff,
    }


def resolve_side_effects_target(
    phase: dict[str, Any],
) -> tuple[str, str, dict, str, bool, str | None]:
    """Resolve the side effects phase target.

    Args:
        phase: Side effects phase payload.

    Returns:
        Tuple of all phase fields.
    """
    return (
        phase.get("session_id", ""),
        phase.get("turn_id", ""),
        phase.get("turn", {}),
        phase.get("response", ""),
        phase.get("requires_approval", False),
        phase.get("approval_diff"),
    )


def build_response_phase(
    request_has_id: bool,
    request_id: str | None,
    turn: dict[str, Any],
    approval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a response phase payload.

    Args:
        request_has_id: Whether the request has an ID.
        request_id: The request identifier.
        turn: The turn object.
        approval_payload: Optional approval payload.

    Returns:
        Response phase payload dictionary.
    """
    return {
        "request_has_id": request_has_id,
        "request_id": request_id or "",
        "turn": turn,
        "approval_payload": approval_payload,
    }


def resolve_response_target(
    phase: dict[str, Any],
) -> tuple[bool, str, dict, dict | None]:
    """Resolve the response phase target.

    Args:
        phase: Response phase payload.

    Returns:
        Tuple of (request_has_id, request_id, turn, approval_payload).

    Raises:
        ValueError: If target cannot be resolved.
    """
    request_has_id = phase.get("request_has_id", False)
    request_id = phase.get("request_id", "")
    turn = phase.get("turn", {})
    approval_payload = phase.get("approval_payload")

    if approval_payload is not None and not isinstance(approval_payload, dict):
        raise ValueError("response target unresolved: invalid approval_payload")

    return (request_has_id, request_id, turn, approval_payload)


def build_cli_command_parse_phase(request: dict[str, Any]) -> dict[str, Any]:
    """Build CLI command parse phase payload."""
    return {"type": "cli_command_parse", "request": request}


def build_cli_dispatch_phase(plan: dict[str, Any]) -> dict[str, Any]:
    """Build CLI dispatch phase payload."""
    return {"type": "cli_dispatch", "plan": plan}


def build_observability_event_phase(event: dict[str, Any]) -> dict[str, Any]:
    """Build observability event phase payload."""
    return {"type": "observability_event", "event": event}


def build_hook_registration_phase(hooks: list[dict[str, Any]]) -> dict[str, Any]:
    """Build hook registration phase payload."""
    return {"type": "hook_registration", "hooks": hooks}


def build_hook_invocation_phase(hook_id: str, context: dict[str, Any]) -> dict[str, Any]:
    """Build hook invocation phase payload."""
    return {"type": "hook_invocation", "hook_id": hook_id, "context": context}


def build_policy_match_phase(policy_id: str, context: dict[str, Any]) -> dict[str, Any]:
    """Build policy match phase payload."""
    return {"type": "policy_match", "policy_id": policy_id, "context": context}


def build_provider_selection_phase(provider_id: str, context: dict[str, Any]) -> dict[str, Any]:
    """Build provider selection phase payload."""
    return {
        "type": "provider_selection",
        "provider_id": provider_id,
        "context": context,
    }


def build_provider_rule_evaluation_phase(rule_id: str, context: dict[str, Any]) -> dict[str, Any]:
    """Build provider rule evaluation phase payload."""
    return {"type": "provider_rule_evaluation", "rule_id": rule_id, "context": context}


def build_queue_priority_phase(queue_id: str, priority: int) -> dict[str, Any]:
    """Build queue priority phase payload."""
    return {"type": "queue_priority", "queue_id": queue_id, "priority": priority}


def build_retry_loop_phase(
    attempt: int,
    max_attempts: int,
    error: str | None,
) -> dict[str, Any]:
    """Build retry loop phase payload."""
    return {
        "type": "retry_loop",
        "attempt": attempt,
        "max_attempts": max_attempts,
        "error": error,
    }


def build_queue_scheduling_phase(
    queue_id: str,
    scheduled_at: float | None = None,
    priority: int = 0,
) -> dict[str, Any]:
    """Build queue scheduling phase payload."""
    return {
        "type": "queue_scheduling",
        "queue_id": queue_id,
        "scheduled_at": scheduled_at,
        "priority": priority,
    }


def build_session_state_update_phase(
    session_id: str,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Build session state update phase payload."""
    return {"type": "session_state_update", "session_id": session_id, "state": state}


def build_sync_diff_phase(
    project_id: str,
    diff: str,
    base_commit: str | None = None,
) -> dict[str, Any]:
    """Build sync diff phase payload."""
    return {
        "type": "sync_diff",
        "project_id": project_id,
        "diff": diff,
        "base_commit": base_commit,
    }


def build_workflow_guard_phase(
    workflow_id: str,
    guard_type: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build workflow guard phase payload."""
    return {
        "type": "workflow_guard",
        "workflow_id": workflow_id,
        "guard_type": guard_type,
        "context": context or {},
    }


def build_sync_commit_phase(
    project_id: str,
    commit_message: str,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Build sync commit phase payload."""
    return {
        "type": "sync_commit",
        "project_id": project_id,
        "commit_message": commit_message,
        "files": files or [],
    }


def resolve_cli_handler_selection_target(
    phase: dict[str, Any],
) -> tuple[str, str | None]:
    """Resolve CLI handler selection target.

    Args:
        phase: The phase payload.

    Returns:
        Tuple of (handler_type, handler_id).
    """
    return (
        phase.get("handler_type", ""),
        phase.get("handler_id"),
    )


def resolve_observability_serialization_target(
    phase: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Resolve observability serialization target.

    Args:
        phase: The phase payload.

    Returns:
        Tuple of (format, data).
    """
    return (
        phase.get("format", "json"),
        phase.get("data", {}),
    )


def resolve_hook_invocation_target(
    phase: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Resolve hook invocation target.

    Args:
        phase: The phase payload.

    Returns:
        Tuple of (hook_id, context).
    """
    return (
        phase.get("hook_id", ""),
        phase.get("context", {}),
    )


def resolve_policy_enforcement_plan_target(
    phase: dict[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    """Resolve policy enforcement plan target.

    Args:
        phase: The phase payload.

    Returns:
        Tuple of (policy_id, action, context).
    """
    return (
        phase.get("policy_id", ""),
        phase.get("action", ""),
        phase.get("context", {}),
    )


def resolve_session_persistence_plan_target(
    context: dict[str, Any],
) -> str:
    """Resolve the session persistence plan target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("session_persistence_plan_target", "default")


def resolve_workflow_guard_target(
    context: dict[str, Any],
) -> str:
    """Resolve the workflow guard target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("workflow_guard_target", "default")


def resolve_observability_target(
    context: dict[str, Any],
) -> str:
    """Resolve the observability target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("observability_target", "default")


def resolve_queue_execution_target(
    context: dict[str, Any],
) -> str:
    """Resolve the queue execution target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("queue_execution_target", "default")


def resolve_provider_final_selection_target(
    context: dict[str, Any],
) -> str:
    """Resolve the provider final selection target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("provider_final_selection_target", "default")


def resolve_sync_commit_plan_target(
    context: dict[str, Any],
) -> str:
    """Resolve the sync commit plan target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("sync_commit_plan_target", "default")


def resolve_session_persistence_target(
    context: dict[str, Any],
) -> str:
    """Resolve the session persistence target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("session_persistence_target", "default")


def resolve_terminal_outcome_target(
    context: dict[str, Any],
) -> str:
    """Resolve the terminal outcome target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("terminal_outcome_target", "default")


def resolve_policy_enforcement_target(
    context: dict[str, Any],
) -> str:
    """Resolve the policy enforcement target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("policy_enforcement_target", "default")


def resolve_workflow_execution_target(
    context: dict[str, Any],
) -> str:
    """Resolve the workflow execution target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("workflow_execution_target", "default")


def resolve_retry_outcome_target(
    context: dict[str, Any],
) -> str:
    """Resolve the retry outcome target.

    Args:
        context: The context dictionary.

    Returns:
        The target string.
    """
    return context.get("retry_outcome_target", "default")


__all__ = [
    "build_parse_phase",
    "resolve_parse_target",
    "build_commit_phase",
    "resolve_commit_target",
    "build_side_effects_phase",
    "resolve_side_effects_target",
    "build_response_phase",
    "resolve_response_target",
    "build_cli_command_parse_phase",
    "build_cli_dispatch_phase",
    "build_observability_event_phase",
    "build_hook_registration_phase",
    "build_hook_invocation_phase",
    "build_policy_match_phase",
    "build_provider_selection_phase",
    "build_provider_rule_evaluation_phase",
    "build_queue_priority_phase",
    "build_retry_loop_phase",
    "build_queue_scheduling_phase",
    "build_session_state_update_phase",
    "build_sync_diff_phase",
    "build_workflow_guard_phase",
    "build_sync_commit_phase",
    "resolve_cli_handler_selection_target",
    "resolve_observability_serialization_target",
    "resolve_hook_invocation_target",
    "resolve_policy_enforcement_plan_target",
    "resolve_session_persistence_plan_target",
    "resolve_workflow_guard_target",
    "resolve_observability_target",
    "resolve_queue_execution_target",
    "resolve_provider_final_selection_target",
    "resolve_sync_commit_plan_target",
    "resolve_session_persistence_target",
    "resolve_terminal_outcome_target",
    "resolve_policy_enforcement_target",
    "resolve_workflow_execution_target",
    "resolve_retry_outcome_target",
]
