"""Orchestration layer — plans, message bus, dispatch, budget tracking.

Public surface
--------------
- :class:`OrchestrationPlan`, :data:`AGENT_HINT`, :data:`BUDGET_TOKENS`, …
  from :mod:`thegent.orchestration.plan`
- :class:`InterAgentMessage`, :class:`MessageBus`,
  :class:`InterAgentProtocol` from :mod:`thegent.orchestration.inter_agent_protocol`
- :class:`BudgetTracker`, :class:`BudgetExceededError` from
  :mod:`thegent.orchestration.budget_tracker`

Hardening (AUDIT-N+33, AUDIT-N+38)
----------------------------------
The re-export surface in this ``__init__`` is the single canonical import
path for orchestration primitives.  Submodules may carry their own
``__all__`` for direct consumers, but new code MUST import from
``thegent.orchestration`` so we have one place to wire deprecation /
aliasing later.

Consensus submodules are re-exported as package attributes so tests can
patch ``thegent.orchestration.{redlock_atomic, omega_consensus,
redis_concurrency}`` symbols directly (mirror of the
``thegent.orchestration.sub_agent_dispatcher`` re-export pattern).

# @trace AUDIT-N+33
# @trace AUDIT-N+38
"""

from __future__ import annotations

import sys as _sys

from thegent.orchestration.aggregator import ResultAggregator
from thegent.orchestration.budget_tracker import (
    BudgetExceededError,
    BudgetTracker,
)

# Consensus submodules — exposed as ``thegent.orchestration.<name>``
# so tests can patch symbols (e.g. ``_import_redis_sync``) via the
# canonical package path.  Mirrors the sub_agent_dispatcher re-export
# pattern.  AUDIT-N+38.
from thegent.orchestration.consensus.omega_consensus import (  # noqa: E402
    FinalState,
    OmegaConsensus,
)
from thegent.orchestration.consensus.redis_concurrency import (  # noqa: E402
    RedisConcurrencyController,
    RedisConfig,
    _InMemoryStore,
    make_redis_concurrency_controller,
)
from thegent.orchestration.consensus.redlock_atomic import (  # noqa: E402
    RedlockAcquireResult,
    RedlockAtomic,
    RedlockController,
    _import_redis_sync,
    _InMemoryLockState,
    _parse_node_urls_from_env,
    _parse_redis_url,
    make_redlock_controller,
)
from thegent.orchestration.inter_agent_protocol import (
    InterAgentMessage,
    InterAgentProtocol,
    MessageBus,
    MessageType,
)
from thegent.orchestration.plan import (
    AGENT_HINT,
    BUDGET_TIME_S,
    BUDGET_TOKENS,
    MODEL_HINT,
    OUTPUT_SCHEMA,
    PARENT_RUN_ID,
    REQUIRE_HITL,
    SANDBOX,
    OrchestrationPlan,
)
from thegent.orchestration.sub_agent_dispatcher import (
    DispatchResult,
    SubAgentDispatcher,
)

redlock_atomic = _sys.modules["thegent.orchestration.consensus.redlock_atomic"]
omega_consensus = _sys.modules["thegent.orchestration.consensus.omega_consensus"]
redis_concurrency = _sys.modules["thegent.orchestration.consensus.redis_concurrency"]
_sys.modules.setdefault(
    "thegent.orchestration.redlock_atomic",
    redlock_atomic,
)
_sys.modules.setdefault(
    "thegent.orchestration.omega_consensus",
    omega_consensus,
)
_sys.modules.setdefault(
    "thegent.orchestration.redis_concurrency",
    redis_concurrency,
)

__all__ = [
    "AGENT_HINT",
    "BUDGET_TIME_S",
    "BUDGET_TOKENS",
    "BudgetExceededError",
    "BudgetTracker",
    "DispatchResult",
    "InterAgentMessage",
    "InterAgentProtocol",
    "MessageBus",
    "MessageType",
    "MODEL_HINT",
    "OUTPUT_SCHEMA",
    "OrchestrationPlan",
    "PARENT_RUN_ID",
    "REQUIRE_HITL",
    "ResultAggregator",
    "SANDBOX",
    "SubAgentDispatcher",
]
