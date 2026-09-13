"""Task routing and categorization for thegent.

Implements Pareto frontier routing based on Terminal Bench 2.0 benchmarks.
Routes tasks to optimal models based on complexity, cost constraints, and quality requirements.

Key components:
- TaskRouter: Main routing engine with constraint validation
- TaskClassifier: Categorizes tasks (FAST/NORMAL/COMPLEX/HIGH_COMPLEX)
- ConstraintValidator: Validates hard constraints (quality, cost, speed)
- Pareto router: Hard constraints → Pareto frontier → lexicographic selection
- Auto router: Gemini Flash classifier + Pareto routing for agent/model="auto"
"""

from thegent.utils.routing_impl.cliproxy_client import (
    CLIProxyRoutingClient,
    RoutingResponse,
)
from thegent.utils.routing_impl.models import (
    RoutingConstraint,
    TaskCategory,
    TaskMetadata,
)
from thegent.utils.routing_impl.pareto_router import ParetoRouter, RouteCandidate
from thegent.utils.routing_impl.task_router import (
    ConstraintValidator,
    TaskClassifier,
    TaskRouter,
)

__all__ = [
    "CLIProxyRoutingClient",
    "ConstraintValidator",
    "ParetoRouter",
    "RoutingConstraint",
    "RoutingResponse",
    "RouteCandidate",
    "TaskCategory",
    "TaskClassifier",
    "TaskMetadata",
    "TaskRouter",
]
