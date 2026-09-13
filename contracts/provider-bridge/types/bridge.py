from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol, TypedDict

Capability = Literal["chat_completion", "embeddings", "rerank", "tool_execution"]
LaneID = Literal["litellm_donut", "bifrost", "native"]
EventType = Literal["chunk", "tool_call", "tool_result", "route_change", "error", "done"]


class Intent(TypedDict):
    capability: Capability
    task_type: str
    latency_tier: Literal["interactive", "batch"]
    quality_tier: Literal["low", "medium", "high"]


class ProviderIntent(TypedDict):
    class_order: list[str]
    allow_models: list[str]
    deny_models: list[str]


class GovernancePolicy(TypedDict, total=False):
    budget_usd_max: float
    max_fallbacks: int
    retry_policy: Literal["none", "standard", "aggressive"]
    rate_policy_id: str


class Message(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ToolDef(TypedDict):
    name: str
    description: str
    schema: dict[str, Any]


class ExecutionInputs(TypedDict):
    messages: list[Message]
    tools: list[ToolDef]
    tool_choice: Literal["none", "auto", "required"]


class MetaproviderMeta(TypedDict):
    inheritance_level: Literal["base", "metaprovider", "lane", "provider"]
    parent_request_id: str


class ExecutionRequest(TypedDict, total=False):
    bridge_schema_version: str
    request_id: str
    run_id: str
    session_id: str
    harness_profile: Literal["codex", "claude", "droid", "antigma", "codex_alt"]
    metaprovider_id: Literal["agentapi", "cliproxy"]
    lane_id: LaneID
    actor: dict[str, Any]
    intent: Intent
    provider_intent: ProviderIntent
    governance: GovernancePolicy
    inputs: ExecutionInputs
    context: dict[str, Any]
    stream: bool
    metaprovider_meta: MetaproviderMeta
    extra: dict[str, Any]


class SelectedRoute(TypedDict):
    provider_id: str
    subprovider_id: str
    model: str


class Usage(TypedDict):
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class GovernanceOutcome(TypedDict, total=False):
    budget_check: Literal["pass", "fail"]
    rate_limit_check: Literal["pass", "fail"]
    fallback_used: bool
    fallback_depth: int


class ResponseError(TypedDict):
    code: str
    message: str
    class_: str


class ExecutionResponse(TypedDict, total=False):
    bridge_schema_version: str
    request_id: str
    run_id: str
    status: Literal["ok", "error"]
    selected_route: SelectedRoute
    attempts: int
    usage: Usage
    output: dict[str, Any]
    error: dict[str, Any]
    governance_outcome: GovernanceOutcome


class ExecutionEvent(TypedDict, total=False):
    event_type: EventType
    request_id: str
    run_id: str
    attempt_id: str
    route_id: str
    tool_call_id: str
    ts: str
    payload: dict[str, Any]


class RouteConstraints(TypedDict, total=False):
    requires_region: str
    max_cost_per_1k_tokens: float
    supports_tools: bool
    supports_stream: bool


class RouteCandidate(TypedDict):
    route_id: str
    provider_id: str
    subprovider_id: str
    provider_class: Literal["local_inference", "cloud_direct", "cloud_aggregator", "account_api", "internal_custom"]
    model: str
    priority: int
    constraints: RouteConstraints


class HarnessDefaults(TypedDict):
    intent_capability: Capability
    latency_tier: Literal["interactive", "batch"]
    quality_tier: Literal["low", "medium", "high"]


class HarnessPolicyOverrides(TypedDict):
    max_fallbacks: int
    budget_usd_max: float


class HarnessToolPolicy(TypedDict):
    allowed_tool_sets: list[str]
    requires_confirmation_for: list[str]


class HarnessProfile(TypedDict):
    harness_profile: Literal["codex", "claude", "droid", "antigma", "codex_alt"]
    defaults: HarnessDefaults
    policy_overrides: HarnessPolicyOverrides
    tool_policy: HarnessToolPolicy


class ProviderAdapter(Protocol):
    def execute(self, req: ExecutionRequest) -> ExecutionResponse: ...

    def stream(self, req: ExecutionRequest) -> Iterable[ExecutionEvent]: ...

    def capabilities(self) -> dict[str, Any]: ...


class MetaproviderAdapter(ProviderAdapter, Protocol):
    def resolve_subproviders(self, req: ExecutionRequest) -> list[RouteCandidate]: ...


class Middleware(Protocol):
    def name(self) -> str: ...

    def handle(self, req: ExecutionRequest, next_handler: Handler) -> ExecutionResponse: ...


class Handler(Protocol):
    def handle(self, req: ExecutionRequest) -> ExecutionResponse: ...


class Runtime(Protocol):
    def register(self, provider_id: str, adapter: MetaproviderAdapter) -> None: ...

    def execute(self, req: ExecutionRequest) -> ExecutionResponse: ...

    def stream(self, req: ExecutionRequest) -> Iterable[ExecutionEvent]: ...


@dataclass(frozen=True)
class EventEnvelope:
    event_type: EventType
    request_id: str
    run_id: str
    attempt_id: str
    payload: dict[str, Any]
    ts: datetime
    route_id: str | None = None
    tool_call_id: str | None = None
