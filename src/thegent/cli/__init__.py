"""thegent CLI module.

This module provides the command-line interface for thegent.

AUDIT-N+19 Phase 4: re-export the canonical ``dag_run_cmd``,
``dag_recover_cmd``, ``dag_sync_cmd``, ``dag_reconcile_cmd``,
``dag_checkpoint_cmd``, ``dag_rollback_cmd``, ``dag_probe_cmd``,
``cockpit_cmd``, ``feedback_cmd``, ``session_contract_health_*_impl``,
and the ``_serialize_health_*`` serializer family. The canonical homes
live in dedicated modules so monkeypatch sites resolve cleanly.

AUDIT-LANE-CLI-COMMANDS-WL124-001 Phase 1: re-export the patchable
surface (``console``, ``_default_owner_tag``, ``_normalize_output_format``,
``resolve_agent``, ``AGENT_LABELS``, ``time``, and
``_write_health_trend_export``) so the post-WL-124 tests in
``tests/test_unit_cli_commands_a.py`` and ``tests/test_unit_cli_commands_b.py``
that mock at ``thegent.cli.<symbol>`` resolve cleanly. The canonical
homes remain in dedicated modules so this layer is a pure re-export
surface.

AUDIT-LANE-CLI-COMMANDS-WL124-002 Phase 2: extend the re-export surface
to cover the remaining ``*_cmd`` wrappers (escalate/sweep/purge/archive/
benchmark/observe/closure_pack/migration/drift/plan_analyze/dag_checkpoints/
events/history/inspect/list_droids/list_models/logs/pause/policy_show/ps/
resume/session_contract_health_gate/session_contract_health_trend/
session_contracts/status/stop/wait), helpers (``_resolve_cwd``,
``_scope_key``, ``_compose_owner_tag``, ``_list_*_models``,
``_write_health_gate_export``, ``_write_report_export``), the
``RunRegistry`` class, ``get_registry``, ``list_agent_names``, ``Columns``
and the ``subprocess`` re-export so the remaining WL-124-era test
patch sites resolve cleanly.
"""

from __future__ import annotations

import subprocess  # noqa: F401
import time

from thegent.agents.registry import (  # noqa: F401
    AGENT_LABELS,
    list_agent_names,
    resolve_agent,
)
from thegent.cli import bg_cmd, run_cmd
from thegent.cli.commands import impl
from thegent.cli.commands._cli_shared import (  # noqa: F401
    RunRegistry,
    _compose_owner_tag,
    _normalize_output_format,
    _scope_key,
    _write_health_trend_export,
    console,
)
from thegent.cli.commands.cli_dag import dag_checkpoints_cmd  # noqa: F401
from thegent.cli.commands.dag_recover_cmd_impl import dag_recover_cmd  # noqa: F401
from thegent.cli.commands.dag_run_cmd_impl import (  # noqa: F401
    _resolve_cwd,
    dag_run_cmd,
)
from thegent.cli.commands.infra_cmds import (  # noqa: F401
    archive_cmd,
    benchmark_cmd,
    cockpit_cmd,
    observe_summary_cmd,
    purge_cmd,
)
from thegent.cli.commands.model_cmds import (  # noqa: F401
    _list_antigravity_models,
    _list_claude_models,
    _list_codex_models_fallback,
    _list_copilot_models_fallback,
    _list_gemini_models,
    _list_glm_models,
    _list_minimax_models,
    list_agents_cmd,
    list_droids_cmd,
    list_models_cmd,
)
from thegent.cli.commands.plan_cmds import (  # noqa: F401
    _default_owner_tag,
    closure_pack_cmd,
    dag_checkpoint_cmd,
    dag_list_cmd,
    dag_probe_cmd,
    dag_ready_cmd,
    dag_reconcile_cmd,
    dag_rollback_cmd,
    dag_status_cmd,
    dag_sync_cmd,
    dag_update_cmd,
    dag_validate_cmd,
    plan_analyze_cmd,
)
from thegent.cli.commands.session_cmds import (  # noqa: F401
    events_cmd,
    feedback_cmd,
    history_cmd,
    inspect_cmd,
    logs_cmd,
    pause_cmd,
    ps_cmd,
    resume_cmd,
    session_contract_health_gate_cmd,
    session_contract_health_trend_cmd,
    session_contracts_cmd,
    status_cmd,
    stop_cmd,
    wait_cmd,
)
from thegent.cli.commands.session_health_report_impl import (  # noqa: F401
    _serialize_health_report_csv,
    _serialize_health_report_jsonl,
    _serialize_health_report_md,
    session_contract_health_report_impl,
)
from thegent.cli.commands.session_health_trend_impl import (  # noqa: F401
    _serialize_health_trend_csv,
    _serialize_health_trend_jsonl,
    _serialize_health_trend_md,
    session_contract_health_trend_impl,
)
from thegent.cli.governance.governance_escalation_hitl_cmds import (  # noqa: F401
    escalate_add_cmd,
    escalate_list_cmd,
    escalate_resolve_cmd,
    sweep_cmd,
)
from thegent.cli.governance.governance_impl import escalate_resolve_impl  # noqa: F401
from thegent.cli.governance.governance_policy_contracts_cmds import (  # noqa: F401
    drift_cmd,
    migration_cmd,
    policy_show_cmd,
)
from thegent.config import ThegentSettings  # noqa: F401

__all__ = [
    "run_cmd",
    "bg_cmd",
    "impl",
    "dag_run_cmd",
    "dag_recover_cmd",
    "dag_sync_cmd",
    "dag_reconcile_cmd",
    "dag_checkpoint_cmd",
    "dag_rollback_cmd",
    "dag_probe_cmd",
    "dag_checkpoints_cmd",
    "plan_analyze_cmd",
    "closure_pack_cmd",
    "session_contract_health_report_impl",
    "session_contract_health_trend_impl",
    "session_contract_health_gate_cmd",
    "session_contract_health_trend_cmd",
    "session_contracts_cmd",
    "_serialize_health_report_md",
    "_serialize_health_report_csv",
    "_serialize_health_report_jsonl",
    "_serialize_health_trend_md",
    "_serialize_health_trend_csv",
    "_serialize_health_trend_jsonl",
    "_write_health_trend_export",
    "cockpit_cmd",
    "feedback_cmd",
    "history_cmd",
    "events_cmd",
    "inspect_cmd",
    "list_droids_cmd",
    "list_models_cmd",
    "logs_cmd",
    "pause_cmd",
    "policy_show_cmd",
    "ps_cmd",
    "purge_cmd",
    "resume_cmd",
    "status_cmd",
    "stop_cmd",
    "sweep_cmd",
    "wait_cmd",
    "archive_cmd",
    "benchmark_cmd",
    "escalate_add_cmd",
    "escalate_list_cmd",
    "escalate_resolve_cmd",
    "escalate_resolve_impl",
    "migration_cmd",
    "drift_cmd",
    "observe_summary_cmd",
    "dag_list_cmd",
    "dag_status_cmd",
    "dag_ready_cmd",
    "dag_update_cmd",
    "dag_validate_cmd",
    "list_agents_cmd",
    "ThegentSettings",
    "console",
    "_default_owner_tag",
    "_compose_owner_tag",
    "_normalize_output_format",
    "_resolve_cwd",
    "_scope_key",
    "_list_antigravity_models",
    "_list_claude_models",
    "_list_codex_models_fallback",
    "_list_copilot_models_fallback",
    "_list_gemini_models",
    "_list_glm_models",
    "_list_minimax_models",
    "resolve_agent",
    "AGENT_LABELS",
    "list_agent_names",
    "RunRegistry",
    "time",
    "subprocess",
]
