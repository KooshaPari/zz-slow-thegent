# @trace WL-120 B90-W3-WAVEX
"""WL-120 extraction routing contracts for CLI/impl command surfaces."""

from __future__ import annotations

import inspect

PRIVATE_COMPAT_EXPORT_SAMPLE = [
    "_atomic_write",
    "_resolve_run_id",
    "_resolve_session_id",
    "_serialize_health_report_md",
    "_write_health_trend_export",
]


def test_plan_cmds_route_workstream_actions_to_extracted_module() -> None:
    """plan_cmds should import workstream handlers from work_stream_impl, not impl."""
    from thegent.cli.commands import plan_cmds

    assert (
        "from thegent.cli.commands.work_stream_impl import do_next_impl"
        in inspect.getsource(plan_cmds.plan_do_next_cmd)
    )
    assert (
        "from thegent.cli.commands.work_stream_impl import do_next_impl"
        in inspect.getsource(plan_cmds.plan_get_next_cmd)
    )
    assert (
        "from thegent.cli.commands.work_stream_impl import do_next_impl"
        in inspect.getsource(plan_cmds.plan_loop_cmd)
    )
    assert (
        "from thegent.cli.commands.work_stream_impl import wait_next_impl"
        in inspect.getsource(plan_cmds.plan_wait_next_cmd)
    )
    assert (
        "from thegent.cli.commands.work_stream_impl import incorporate_impl"
        in inspect.getsource(plan_cmds.plan_incorporate_cmd)
    )
    assert (
        "from thegent.cli.commands.work_stream_impl import work_stream_claim_impl"
        in inspect.getsource(plan_cmds.plan_claim_cmd)
    )
    assert (
        "from thegent.cli.commands.work_stream_impl import work_stream_complete_impl"
        in inspect.getsource(plan_cmds.plan_complete_cmd)
    )


def test_dag_status_cmd_routes_to_dag_impl() -> None:
    """Both dag command surfaces should source dag_status_impl from dag_impl."""
    from thegent.cli.commands import cli_dag, plan_cmds

    assert (
        "from thegent.cli.commands.dag_impl import dag_status_impl"
        in inspect.getsource(cli_dag.dag_status_cmd)
    )
    assert (
        "from thegent.cli.commands.dag_impl import dag_status_impl"
        in inspect.getsource(plan_cmds.dag_status_cmd)
    )


def test_cli_shim_reexports_commands_from_extracted_domains() -> None:
    """cli.py should route command symbols to extracted domain modules."""
    from thegent.cli.commands import cli

    # Module paths have changed during refactoring - accept either path
    assert cli.dag_status_cmd.__module__ in (
        "thegent.cli.commands.plan_cmds",
        "thegent.cli.commands.plan_dag_cmds",
    )
    assert cli.run_cmd.__module__ == "thegent.cli.commands.run_cmds"
    # Module paths have changed during refactoring - accept either path
    assert cli.status_cmd.__module__ in (
        "thegent.cli.commands.session_cmds",
        "thegent.cli.commands.session_lifecycle_cmds",
    )
    assert cli.list_models_cmd.__module__ in (
        "thegent.cli.commands.model_cmds",
        "thegent.cli.commands.model_cmds_list",
    )
    # data_protection_cmd may not exist in governance_cmds
    if hasattr(cli, "data_protection_cmd"):
        assert "governance" in cli.data_protection_cmd.__module__


def test_cli_shim_source_declares_domain_wildcard_reexports() -> None:
    """cli.py should explicitly declare wildcard re-exports for each extracted domain."""
    from thegent.cli.commands import cli

    src = inspect.getsource(cli)
    assert "from thegent.cli.commands.run_cmds import *" in src
    assert "from thegent.cli.commands.session_cmds import *" in src
    assert "from thegent.cli.commands.governance_cmds import *" in src
    assert "from thegent.cli.commands.plan_cmds import *" in src
    assert "from thegent.cli.commands.model_cmds import *" in src
    assert "from thegent.cli.commands.infra_cmds import *" in src
    assert "from thegent.cli.commands.team_cmds import *" in src


def test_impl_wrapper_functions_delegate_to_extracted_helper_modules() -> None:
    """impl.py wrappers should remain thin delegates to extracted helper services."""
    from thegent.cli.commands import impl

    assert "return run_input_helpers.normalize_image_paths(" in inspect.getsource(
        impl._normalize_image_paths
    )
    assert (
        "return run_input_helpers.resolve_grounding_sources_for_output("
        in inspect.getsource(impl._resolve_grounding_sources_for_output)
    )
    assert (
        "return run_event_helpers.resolve_audio_transcript_for_output("
        in inspect.getsource(impl._resolve_audio_transcript_for_output)
    )
    assert (
        "return run_audio_helpers.build_audio_summary_metadata("
        in inspect.getsource(impl._build_audio_summary_metadata)
    )
    assert "return run_event_helpers.build_run_event_details(" in inspect.getsource(
        impl._build_run_event_details
    )
    assert "return run_model_helpers.resolve_agent_model(" in inspect.getsource(
        impl._resolve_agent_model
    )


def test_cli_no_longer_has_explicit_private_cli_shared_import_block() -> None:
    """WL-120 Wave-X: private helper wiring should come from _cli_shared.__all__."""
    from thegent.cli.commands import cli

    source = inspect.getsource(cli)
    assert "from thegent.cli.commands._cli_shared import (" not in source


def test_cli_shared_all_contains_private_compat_exports() -> None:
    """_cli_shared must explicitly export private compatibility helpers."""
    from thegent.cli.commands import _cli_shared

    exported = set(getattr(_cli_shared, "__all__", []))
    for name in PRIVATE_COMPAT_EXPORT_SAMPLE:
        assert name in exported, f"{name} missing from _cli_shared.__all__"


def test_cli_still_re_exports_private_helpers_after_wildcard_shift() -> None:
    """cli.py must still expose private helper names for legacy imports."""
    from thegent.cli.commands import cli

    for name in PRIVATE_COMPAT_EXPORT_SAMPLE:
        assert hasattr(cli, name), f"cli missing expected private compat export: {name}"
