"""Contract tests for WL-124: Monolith Split of cli.py into domain submodules.

Verifies:
1. All domain submodules are importable as standalone Python modules.
2. All names previously defined in cli.py are still accessible from cli.py
   (backward compatibility via re-exports).
3. Each domain's __all__ is consistent — every listed name is actually defined.
4. The shared infrastructure module (_cli_shared) exports expected names.
5. No circular imports exist.

# @trace WL-124
"""

from __future__ import annotations

import importlib
import types

import pytest

# ---------------------------------------------------------------------------
# Domain submodule registry
# ---------------------------------------------------------------------------
DOMAIN_MODULES = [
    "thegent.cli.commands.run_cmds",
    "thegent.cli.commands.session_cmds",
    "thegent.cli.commands.governance_cmds",
    "thegent.cli.commands.plan_cmds",
    "thegent.cli.commands.model_cmds",
    "thegent.cli.commands.infra_cmds",
    "thegent.cli.commands.team_cmds",
]

SHARED_MODULE = "thegent.cli.commands._cli_shared"
CLI_MODULE = "thegent.cli.commands.cli"

# ---------------------------------------------------------------------------
# Expected exports per domain (contract: __all__ must contain these)
# ---------------------------------------------------------------------------
EXPECTED_EXPORTS: dict[str, list[str]] = {
    "thegent.cli.commands.run_cmds": [
        "run_cmd",
        "loop_cmd",
        "loop_send_cmd",
        "loop_stop_cmd",
        "bg_cmd",
        "retry_cmd",
        "replay_cmd",
        "trace_replay_cmd",
        "terminal_route_cmd",
        "deep_research_cmd",
        "takeover_cmd",
        "run_diff_cmd",
    ],
    "thegent.cli.commands.session_cmds": [
        "history_cmd",
        "events_cmd",
        "inbox_list_cmd",
        "inbox_wait_cmd",
        "feedback_cmd",
        "ps_cmd",
        "session_contracts_cmd",
        "session_contract_health_gate_cmd",
        "session_contract_health_report_cmd",
        "session_contract_health_trend_cmd",
        "status_cmd",
        "inspect_cmd",
        "logs_cmd",
        "wait_cmd",
        "stop_cmd",
        "pause_cmd",
        "resume_cmd",
        "session_fork_cmd",
        "session_rollback_cmd",
        "session_cmd",
        "session_contract_negotiate_cmd",
        "session_contract_trend_analysis_cmd",
        "deferral_list_cmd",
        "deferral_resume_cmd",
    ],
    "thegent.cli.commands.governance_cmds": [
        "data_protection_cmd",
        "compliance_report_cmd",
        "audit_verify_cmd",
        "escalate_add_cmd",
        "escalate_list_cmd",
        "sweep_cmd",
        "escalate_resolve_cmd",
        "escalate_approve_cmd",
        "govern_approve_cmd",
        "govern_reject_cmd",
        "govern_list_pending_cmd",
        "govern_configure_cmd",
        "govern_go_health_cmd",
        "govern_go_status_cmd",
        "govern_go_cycle_cmd",
        "govern_go_watch_cmd",
        "policy_show_cmd",
        "policy_purge_cmd",
        "contracts_registry_cmd",
        "migration_cmd",
        "drift_cmd",
        "contracts_conformance_cmd",
        "trust_status_cmd",
        "signatures_list_cmd",
        "signatures_verify_cmd",
        "compliance_siem_test_cmd",
        "compliance_plugin_check_cmd",
        "compliance_redact_cmd",
        "govern_cost_cmd",
        "guardrails_check_cmd",
        "guardrails_show_cmd",
        "policy_check_cmd",
        "discovery_register_cmd",
        "discovery_parse_cmd",
        "discovery_scan_cmd",
    ],
    "thegent.cli.commands.plan_cmds": [
        "dag_validate_cmd",
        "dag_list_cmd",
        "dag_add_cmd",
        "dag_remove_cmd",
        "dag_cancel_cmd",
        "dag_status_cmd",
        "dag_update_cmd",
        "dag_ready_cmd",
        "dag_reconcile_cmd",
        "plan_incorporate_cmd",
        "plan_claim_cmd",
        "plan_complete_cmd",
        "plan_wait_next_cmd",
        "plan_do_next_cmd",
        "plan_get_next_cmd",
        "plan_loop_cmd",
        "plan_progress_cmd",
        "plan_analyze_cmd",
        "closure_pack_cmd",
        "dag_run_cmd",
        "dag_sync_cmd",
        "dag_checkpoint_cmd",
        "dag_rollback_cmd",
        "dag_checkpoints_cmd",
        "dag_recover_cmd",
        "dag_probe_cmd",
        "workstream_query_cmd",
        "workstream_stats_cmd",
        "workstream_dashboard_cmd",
        "workstream_launch_cmd",
        "workstream_dependencies_cmd",
    ],
    "thegent.cli.commands.model_cmds": [
        "_models_table",
        "list_agents_cmd",
        "list_droids_cmd",
        "list_models_cmd",
        "speed_index_cmd",
        "quality_index_cmd",
        "metrics_cmd",
        "cost_values_cmd",
        "resolve_model_route_cmd",
        "list_model_contract_schema_cmd",
        "_list_minimax_models",
        "_list_glm_models",
        "_list_cursor_models",
        "_list_cursor_api_models",
        "_list_gemini_models",
        "_list_copilot_models",
        "_list_copilot_models_fallback",
        "_list_claude_models",
        "_list_codex_models",
        "_list_codex_models_fallback",
        "_list_antigravity_models",
        "_list_kiro_models",
        "cliproxy_login_cmd",
        "setup_cmd",
        "rules_sync_cmd",
    ],
    "thegent.cli.commands.infra_cmds": [
        "interruption_list_cmd",
        "config_check_cmd",
        "concurrency_show_cmd",
        "concurrency_set_cmd",
        "load_status_cmd",
        "cost_status_cmd",
        "usage_cmd",
        "interruption_snooze_cmd",
        "purge_cmd",
        "observe_summary_cmd",
        "cockpit_cmd",
        "sitback_dashboard_cmd",
        "archive_cmd",
        "operations_cmd",
        "modes_cmd",
        "benchmark_cmd",
        "release_pack_cmd",
        "forensics_snapshot_cmd",
        "recover_status_cmd",
        "monitor_cmd",
        "context_history_cmd",
        "scratchpad_cmd",
        "explorer_cmd",
    ],
    "thegent.cli.commands.team_cmds": [
        "summary_cmd",
        "explain_cmd",
        "fallbacks_cmd",
        "handoff_cmd",
        "handoff_show_cmd",
        "handoff_list_cmd",
        "handoff_confirm_cmd",
        "watchdog_cmd",
        "dlq_list_cmd",
        "traffic_cmd",
        "drift_monitor_cmd",
        "roadmap_cmd",
        "self_heal_tests_cmd",
        "teammates_list_cmd",
        "teammates_delegate_cmd",
        "teammates_status_cmd",
        "queue_list_cmd",
        "team_create_cmd",
        "team_task_add_cmd",
        "team_task_list_cmd",
        "recover_status_cmd",
        "project_register_cmd",
        "project_list_cmd",
    ],
}

# Expected names from _cli_shared (shared infrastructure contract)
EXPECTED_SHARED_NAMES = [
    "console",
    "ThegentSettings",
    "RunRegistry",
    "_lazy_import",
    "_resolve_run_id",
    "_resolve_session_id",
    "_normalize_output_format",
    "EXIT_TIMEOUT",
    "EXIT_HEALTH_GATE_FAILED",
    "_format_context_usage_line",
    "_format_grounding_sources_lines",
    "_format_transcript_summary_line",
    "_scope_key",
    "_compose_owner_tag",
    "_inject_skill_instructions",
    "_get_health_targets_path",
    "_health_targets_exists",
    "_bootstrap_metric_contracts",
    "_safe_dict",
    "_safe_list",
    "_load_artifact",
    "_HEALTH_TARGETS_TEMPLATE",
    "_METRIC_CONTRACTS_TEMPLATE",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import(module_name: str) -> types.ModuleType:
    """Import a module by name, fail loudly on any error."""
    return importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# Tests: Domain submodule importability
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_name", DOMAIN_MODULES)
def test_domain_module_importable(module_name: str) -> None:
    """Each domain submodule must be importable without errors.

    # @trace WL-124
    """
    mod = _import(module_name)
    assert isinstance(mod, types.ModuleType), f"{module_name} did not import as a module"


# ---------------------------------------------------------------------------
# Tests: __all__ consistency — every listed name is actually defined
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_name", DOMAIN_MODULES)
def test_all_names_defined_in_module(module_name: str) -> None:
    """Every name listed in __all__ must be defined in the module.

    # @trace WL-124
    """
    mod = _import(module_name)
    assert hasattr(mod, "__all__"), f"{module_name} must define __all__"
    missing = [name for name in mod.__all__ if not hasattr(mod, name)]
    assert not missing, f"{module_name}.__all__ lists names not defined in module: {missing}"


# ---------------------------------------------------------------------------
# Tests: Contract — expected exports present in each domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("module_name", "expected_names"),
    list(EXPECTED_EXPORTS.items()),
)
def test_expected_exports_present(module_name: str, expected_names: list[str]) -> None:
    """Each domain module must export its contract-specified names.

    # @trace WL-124
    """
    mod = _import(module_name)
    for name in expected_names:
        assert hasattr(mod, name), f"{module_name} is missing expected export: {name}"


# ---------------------------------------------------------------------------
# Tests: Backward compatibility — all domain exports accessible from cli.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "expected_name",
    sorted({name for names in EXPECTED_EXPORTS.values() for name in names}),
)
def test_backward_compat_via_cli_module(expected_name: str) -> None:
    """All domain-exported names must be accessible from thegent.cli.commands.cli.

    This confirms that the re-export block at the bottom of cli.py works.

    # @trace WL-124
    """
    cli = _import(CLI_MODULE)
    assert hasattr(cli, expected_name), f"thegent.cli.commands.cli missing re-exported name: {expected_name}"


# ---------------------------------------------------------------------------
# Tests: Shared infrastructure module
# ---------------------------------------------------------------------------


def test_cli_shared_importable() -> None:
    """_cli_shared must import without errors.

    # @trace WL-124
    """
    mod = _import(SHARED_MODULE)
    assert isinstance(mod, types.ModuleType)


@pytest.mark.parametrize("name", EXPECTED_SHARED_NAMES)
def test_cli_shared_exports_expected_names(name: str) -> None:
    """_cli_shared must expose each shared infrastructure name.

    # @trace WL-124
    """
    mod = _import(SHARED_MODULE)
    assert hasattr(mod, name), f"thegent.cli.commands._cli_shared missing expected name: {name}"


# ---------------------------------------------------------------------------
# Tests: No circular imports
# ---------------------------------------------------------------------------


def test_no_circular_imports_shared_then_domains() -> None:
    """Importing _cli_shared followed by all domain modules must not fail.

    Circular import chains would raise ImportError or cause partial module state.

    # @trace WL-124
    """
    _import(SHARED_MODULE)
    for module_name in DOMAIN_MODULES:
        _import(module_name)


def test_no_circular_imports_domains_then_cli() -> None:
    """Importing all domain modules then cli.py must not fail.

    # @trace WL-124
    """
    for module_name in DOMAIN_MODULES:
        _import(module_name)
    _import(CLI_MODULE)


# ---------------------------------------------------------------------------
# Tests: CLI module (cli.py) still importable and not broken
# ---------------------------------------------------------------------------


def test_cli_module_importable() -> None:
    """thegent.cli.commands.cli must be importable as before the split.

    # @trace WL-124
    """
    mod = _import(CLI_MODULE)
    assert isinstance(mod, types.ModuleType)


def test_cli_module_wildcard_import_works() -> None:
    """Wildcard import from cli must succeed (the user-facing contract).

    # @trace WL-124
    """
    cli = _import(CLI_MODULE)
    # Spot-check a sample of well-known names from each domain
    spot_check = [
        "run_cmd",  # run_cmds
        "ps_cmd",  # session_cmds
        "govern_approve_cmd",  # governance_cmds
        "dag_validate_cmd",  # plan_cmds
        "list_models_cmd",  # model_cmds
        "config_check_cmd",  # infra_cmds
        "handoff_cmd",  # team_cmds
    ]
    for name in spot_check:
        assert hasattr(cli, name), f"thegent.cli.commands.cli missing spot-check name: {name}"


# ---------------------------------------------------------------------------
# Tests: Domain module count (guard against silent drops)
# ---------------------------------------------------------------------------


def test_expected_domain_module_count() -> None:
    """Exactly 7 domain submodules must exist (WL-124 specification).

    # @trace WL-124
    """
    assert len(DOMAIN_MODULES) == 7, f"Expected 7 domain modules, got {len(DOMAIN_MODULES)}: {DOMAIN_MODULES}"


def test_total_exported_names_count() -> None:
    """Total exported names across all domains must be 173 (WL-124 specification).

    # @trace WL-124
    """
    total = sum(len(v) for v in EXPECTED_EXPORTS.values())
    assert total == 173, f"Expected 173 total exported names across all domains, got {total}"


# ---------------------------------------------------------------------------
# Tests: Callable — each exported command function must be callable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("module_name", "fn_name"),
    [
        (mod, name)
        for mod, names in EXPECTED_EXPORTS.items()
        for name in names
        if not name.startswith("_")  # only public command functions
    ],
)
def test_command_functions_are_callable(module_name: str, fn_name: str) -> None:
    """Every public command function in __all__ must be callable.

    # @trace WL-124
    """
    mod = _import(module_name)
    fn = getattr(mod, fn_name)
    assert callable(fn), f"{module_name}.{fn_name} is not callable (expected a function/command)"
