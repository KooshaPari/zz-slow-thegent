from __future__ import annotations

import pytest

from thegent.cli.commands import cli, plan_cmds


def test_workstream_query_cmd_is_bound_to_extracted_plan_module() -> None:
    assert cli.workstream_query_cmd is plan_cmds.workstream_query_cmd


@pytest.mark.skip(reason="workstream_stats_cmd not implemented")
def test_workstream_stats_cmd_is_bound_to_extracted_plan_module() -> None:
    assert cli.workstream_stats_cmd is plan_cmds.workstream_stats_cmd


@pytest.mark.skip(reason="workstream_dashboard_cmd not implemented")
def test_workstream_dashboard_cmd_is_bound_to_extracted_plan_module() -> None:
    assert cli.workstream_dashboard_cmd is plan_cmds.workstream_dashboard_cmd


@pytest.mark.skip(reason="workstream_launch_cmd not implemented")
def test_workstream_launch_cmd_is_bound_to_extracted_plan_module() -> None:
    assert cli.workstream_launch_cmd is plan_cmds.workstream_launch_cmd


@pytest.mark.skip(reason="workstream_dependencies_cmd not implemented")
def test_workstream_dependencies_cmd_is_bound_to_extracted_plan_module() -> None:
    assert cli.workstream_dependencies_cmd is plan_cmds.workstream_dependencies_cmd


def test_plan_lint_workstream_cmd_is_bound_to_extracted_plan_module() -> None:
    assert cli.plan_lint_workstream_cmd is plan_cmds.plan_lint_workstream_cmd


def test_plan_normalize_workstream_cmd_is_bound_to_extracted_plan_module() -> None:
    assert cli.plan_normalize_workstream_cmd is plan_cmds.plan_normalize_workstream_cmd
