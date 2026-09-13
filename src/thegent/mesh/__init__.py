"""thegent-mesh: Coordination mesh for multi-agent orchestration."""

__version__ = "0.1.0"

from .cache import MeshCache
from .coordination import (
    ConflictPrediction,
    EditIntent,
    FileClaimsRegistry,
    HLCTimestamp,
    IntentRegistry,
    OptimisticConcurrencyControl,
    predict_merge_conflicts,
)
from .mesh import MeshManager
from .smart_merge import MergeResult, SmartMergeConfig, SmartMerger, make_smart_merger
from .task_queue import MaildirQueue

__all__ = [
    "HLCTimestamp",
    "OptimisticConcurrencyControl",
    "FileClaimsRegistry",
    "EditIntent",
    "ConflictPrediction",
    "IntentRegistry",
    "predict_merge_conflicts",
    "MeshCache",
    "MaildirQueue",
    "SmartMerger",
    "SmartMergeConfig",
    "MergeResult",
    "make_smart_merger",
    "MeshManager",
]
