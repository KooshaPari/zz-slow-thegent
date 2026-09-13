from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

from conftest import _load_script_module

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "collect_wl_monolith_baselines.py"
MODULE = _load_script_module("collect_wl_monolith_baselines", SCRIPT_PATH)


def test_collect_all_has_expected_targets() -> None:
    payload = MODULE.collect_all()

    assert sorted(payload.keys()) == ["WL-124", "WL-125", "WL-126"]


def test_collect_all_reports_nonzero_line_counts() -> None:
    payload = MODULE.collect_all()

    assert payload["WL-124"]["line_count"] > 0
    assert payload["WL-125"]["line_count"] > 0
    assert payload["WL-126"]["line_count"] > 0


def test_collect_metrics_includes_function_samples() -> None:
    payload = MODULE.collect_all()

    assert isinstance(payload["WL-124"]["top_level_function_sample"], list)
    assert isinstance(payload["WL-125"]["top_level_function_sample"], list)
    assert isinstance(payload["WL-126"]["top_level_function_sample"], list)


def test_wl126_catalog_module_has_stable_import_surface() -> None:
    catalog_module = importlib.import_module("thegent.mcp.server_catalog_tools")

    assert hasattr(catalog_module, "thegent_list_operations_impl")


def test_wl124_team_command_group_module_import_surface() -> None:
    module = importlib.import_module("thegent.cli.commands.team_commands")

    assert hasattr(module, "team_create_cmd")
    assert hasattr(module, "team_task_add_cmd")
    assert hasattr(module, "team_task_list_cmd")


def test_wl124_project_command_group_module_import_surface() -> None:
    module = importlib.import_module("thegent.cli.commands.project_commands")

    assert hasattr(module, "project_register_cmd")
    assert hasattr(module, "project_list_cmd")


def test_wl124_queue_command_group_module_import_surface() -> None:
    module = importlib.import_module("thegent.cli.commands.queue_commands")

    assert hasattr(module, "queue_list_cmd")


def test_wl124_recovery_command_group_module_import_surface() -> None:
    module = importlib.import_module("thegent.cli.commands.recovery_commands")

    assert hasattr(module, "recover_status_cmd")
    assert hasattr(module, "forensics_snapshot_cmd")


def test_wl124_operations_command_group_module_import_surface() -> None:
    module = importlib.import_module("thegent.cli.commands.operations_commands")

    assert hasattr(module, "operations_cmd")


def test_wl124_plan_command_group_module_import_surface() -> None:
    module = importlib.import_module("thegent.cli.commands.plan_cmds")

    assert hasattr(module, "workstream_query_cmd")
    assert hasattr(module, "workstream_stats_cmd")


def test_wl124_governance_command_group_module_import_surface() -> None:
    module = importlib.import_module("thegent.cli.commands.governance_cmds")

    assert hasattr(module, "guardrails_check_cmd")
    assert hasattr(module, "guardrails_show_cmd")
    assert hasattr(module, "policy_check_cmd")


def test_wl125_run_input_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.run_input_helpers")

    assert hasattr(module, "normalize_image_paths")
    assert hasattr(module, "append_context_usage")
    assert hasattr(module, "resolve_grounding_sources_for_output")


def test_wl125_run_event_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.run_event_helpers")

    assert hasattr(module, "resolve_audio_transcript_for_output")
    assert hasattr(module, "build_run_event_details")


def test_wl125_run_audio_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.run_audio_helpers")

    assert hasattr(module, "build_audio_summary_metadata")


def test_wl125_session_path_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.session_path_helpers")

    assert hasattr(module, "session_paths")


def test_wl125_run_model_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.run_model_helpers")

    assert hasattr(module, "resolve_agent_model")


def test_wl125_session_id_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.session_id_helpers")

    assert hasattr(module, "new_session_id")


def test_wl125_process_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.process_helpers")

    assert hasattr(module, "is_pid_running")


def test_wl125_retry_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.retry_helpers")

    assert hasattr(module, "backoff_delay")


def test_wl125_prompt_constraint_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.prompt_constraint_helpers")

    assert hasattr(module, "inject_time_constraint")


def test_wl125_spawn_retry_helper_service_import_surface() -> None:
    module = importlib.import_module("thegent.cli.services.spawn_retry_helpers")

    assert hasattr(module, "retry_if_eagain")
    assert hasattr(module, "EAGAIN_ERRNOS")


def test_wl126_mcp_re_exports_server_result_helpers() -> None:
    mcp_module = importlib.import_module("thegent.mcp")

    assert hasattr(mcp_module, "server_stable_json")
    assert hasattr(mcp_module, "server_error_result")
    assert hasattr(mcp_module, "server_elicitation_cache_key")
    assert hasattr(mcp_module, "server_get_cached_elicitation")
    assert hasattr(mcp_module, "server_default_cwd_from_context")
    assert hasattr(mcp_module, "server_default_owner_from_context")
    assert hasattr(mcp_module, "server_resolve_cwd_elicitation")
    assert hasattr(mcp_module, "server_resolve_owner_elicitation")
    assert hasattr(mcp_module, "server_load_module")
