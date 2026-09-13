from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_instruction_architecture.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("instruction_architecture_check", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _top_level_function_defs(path: Path) -> set[str]:
    module_ast = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in module_ast.body if isinstance(node, ast.FunctionDef)}


def test_instruction_doc_map_contains_links() -> None:
    mod = _load_module()
    links = mod.extract_instruction_doc_map_links((ROOT / "CLAUDE.md").read_text(encoding="utf-8"))
    assert links


def test_instruction_architecture_contracts_are_clean() -> None:
    mod = _load_module()
    findings = []
    findings.extend(mod.validate_doc_map_links(ROOT / "CLAUDE.md"))
    findings.extend(mod.validate_required_sections())
    findings.extend(mod.validate_pre_work_gate_governance())
    findings.extend(mod.validate_orchestration_wrapper_governance())
    findings.extend(mod.validate_mcp_server_boundary())
    findings.extend(mod.validate_wl125_impl_boundary())
    assert findings == []
    summary = mod.build_summary(findings)
    assert summary["ok"] is True
    assert summary["finding_count"] == 0
    checked = summary["checked"]
    assert "pre_work_gate_command_modules" in checked
    assert "orchestration_wrapper_command_modules" in checked
    assert "mcp_server_boundary_target" in checked
    assert "wl125_impl_boundary_target" in checked
    assert "wl125_trend_metadata_source" in checked
    assert checked["wl125_trend_warning_metadata_key"] == "trend_snapshot_health"


def test_pre_work_gate_command_module_flags_literal_duplication(tmp_path: Path) -> None:
    mod = _load_module()
    module_path = tmp_path / "bad_module.py"
    module_path.write_text(
        "\n".join(
            [
                "from thegent.cli.services import pre_work_gate_helpers",
                "",
                "def _enforce_pre_work_hard_gate(project_dir):",
                "    return pre_work_gate_helpers.enforce_pre_work_hard_gate(project_dir)",
                "",
                "def note():",
                "    return 'WP-HG-05.pre_work_hard_gate'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    findings = mod.validate_pre_work_gate_command_module(
        module_path=module_path,
        wrapper_contracts={"_enforce_pre_work_hard_gate": "enforce_pre_work_hard_gate"},
    )
    assert any(item.kind == "pre_work_gate_literal_duplicate" for item in findings)


def test_pre_work_gate_command_module_flags_wrapper_logic_leak(tmp_path: Path) -> None:
    mod = _load_module()
    module_path = tmp_path / "bad_wrapper.py"
    module_path.write_text(
        "\n".join(
            [
                "from thegent.cli.services import pre_work_gate_helpers",
                "",
                "def _enforce_pre_work_hard_gate(project_dir):",
                "    gate = pre_work_gate_helpers.enforce_pre_work_hard_gate(project_dir)",
                "    return gate",
                "",
            ]
        ),
        encoding="utf-8",
    )

    findings = mod.validate_pre_work_gate_command_module(
        module_path=module_path,
        wrapper_contracts={"_enforce_pre_work_hard_gate": "enforce_pre_work_hard_gate"},
    )
    assert any(item.kind == "pre_work_gate_wrapper_logic_leak" for item in findings)


def test_orchestration_wrapper_command_module_requires_direct_delegation(tmp_path: Path) -> None:
    mod = _load_module()
    module_path = tmp_path / "orchestration_wrappers.py"
    module_path.write_text(
        "\n".join(
            [
                "from thegent.cli.services import work_stream_orchestration",
                "",
                "def do_next_impl(cd=None, limit=5):",
                "    return work_stream_orchestration.do_next_impl(cd=cd, limit=limit)",
                "",
                "def wait_next_impl(cd=None, poll_interval=2.0, timeout=0.0, sources=('do_next',)):",
                "    return work_stream_orchestration.wait_next_impl(",
                "        cd=cd,",
                "        poll_interval=poll_interval,",
                "        timeout=timeout,",
                "        sources=sources,",
                "    )",
                "",
                "def spawn_next_impl(",
                "    cd=None, limit=10, agent='free', timeout=None, lane='critical',",
                "    override_reason='manual-next-step', claim=True,",
                "):",
                "    return work_stream_orchestration.spawn_next_impl(",
                "        cd=cd,",
                "        limit=limit,",
                "        agent=agent,",
                "        timeout=timeout,",
                "        lane=lane,",
                "        override_reason=override_reason,",
                "        claim=claim,",
                "    )",
                "",
                "def work_stream_claim_impl(item_id, agent_id, cd=None):",
                "    return work_stream_orchestration.work_stream_claim_impl(item_id=item_id, agent_id=agent_id, cd=cd)",
                "",
                "def work_stream_complete_impl(item_id, agent_id, cd=None):",
                "    return work_stream_orchestration.work_stream_complete_impl(",
                "        item_id=item_id,",
                "        agent_id=agent_id,",
                "        cd=cd,",
                "    )",
                "",
                "def incorporate_impl(cd=None, dry_run=False):",
                "    return work_stream_orchestration.incorporate_impl(cd=cd, dry_run=dry_run)",
                "",
                "def _validate_task_and_record_errors(tf, validation_errors):",
                "    return work_stream_orchestration._validate_task_and_record_errors(",
                "        tf=tf,",
                "        validation_errors=validation_errors,",
                "    )",
                "",
                "def continuity_snapshot_impl(owner, run_ids, state_summary=None, next_steps=None):",
                "    return work_stream_orchestration.continuity_snapshot_impl(",
                "        owner=owner,",
                "        run_ids=run_ids,",
                "        state_summary=state_summary,",
                "        next_steps=next_steps,",
                "    )",
                "",
            ]
        ),
        encoding="utf-8",
    )

    findings = mod.validate_orchestration_wrapper_command_module(module_path=module_path)
    assert findings == []


def test_orchestration_wrapper_command_module_flags_business_logic_leak(tmp_path: Path) -> None:
    mod = _load_module()
    module_path = tmp_path / "bad_orchestration_wrappers.py"
    module_path.write_text(
        "\n".join(
            [
                "from thegent.cli.services import work_stream_orchestration",
                "",
                "def continuity_snapshot_impl(owner, run_ids, state_summary=None, next_steps=None):",
                "    result = work_stream_orchestration.continuity_snapshot_impl(",
                "        owner=owner,",
                "        run_ids=run_ids,",
                "        state_summary=state_summary,",
                "        next_steps=next_steps,",
                "    )",
                "    result['owner'] = owner",
                "    return result",
                "",
                "def _validate_task_and_record_errors(tf, validation_errors):",
                "    work_stream_orchestration._validate_task_and_record_errors(",
                "        tf=tf,",
                "        validation_errors=validation_errors,",
                "    )",
                "    validation_errors.append({'file': tf.name, 'error': 'extra logic'})",
                "",
            ]
        ),
        encoding="utf-8",
    )

    findings = mod.validate_orchestration_wrapper_command_module(
        module_path=module_path,
        wrapper_contracts={
            "continuity_snapshot_impl": "continuity_snapshot_impl",
            "_validate_task_and_record_errors": "_validate_task_and_record_errors",
        },
    )
    assert any(item.kind == "orchestration_wrapper_logic_leak" for item in findings)


def test_mcp_server_boundary_flags_line_ceiling(tmp_path: Path) -> None:
    mod = _load_module()
    server_path = tmp_path / "server.py"
    server_path.write_text("\n".join(["x = 1"] * 12), encoding="utf-8")

    findings = mod.validate_mcp_server_boundary(
        server_path=server_path,
        max_lines=10,
        required_wiring_strings=(),
        max_top_level_functions=100,
        max_mcp_tool_decorators=100,
    )
    assert any(item.kind == "mcp_server_line_ceiling" for item in findings)


def test_mcp_server_boundary_flags_missing_wiring(tmp_path: Path) -> None:
    mod = _load_module()
    server_path = tmp_path / "server.py"
    server_path.write_text("from fastmcp import FastMCP\nmcp = FastMCP('x')\n", encoding="utf-8")

    findings = mod.validate_mcp_server_boundary(
        server_path=server_path,
        max_lines=100,
        required_wiring_strings=("_server_execution_tools.register_execution_tools(",),
        max_top_level_functions=100,
        max_mcp_tool_decorators=100,
    )
    assert any(item.kind == "mcp_server_wiring_missing" for item in findings)


def test_wl125_impl_boundary_flags_line_ceiling(tmp_path: Path) -> None:
    mod = _load_module()
    impl_path = tmp_path / "impl.py"
    impl_path.write_text("\n".join(["x = 1"] * 12), encoding="utf-8")

    findings = mod.validate_wl125_impl_boundary(
        impl_path=impl_path,
        max_lines=10,
        required_trend_metadata_key="trend_snapshot_health",
    )
    assert any(item.kind == "wl125_impl_line_ceiling" for item in findings)


def test_wl125_impl_boundary_flags_missing_trend_warning_metadata_key(tmp_path: Path) -> None:
    mod = _load_module()
    impl_path = tmp_path / "impl.py"
    impl_path.write_text("def noop():\n    return 'ok'\n", encoding="utf-8")
    trend_metadata_source = tmp_path / "run_observe_helpers.py"
    trend_metadata_source.write_text("def metadata():\n    return {'x': 1}\n", encoding="utf-8")

    findings = mod.validate_wl125_impl_boundary(
        impl_path=impl_path,
        max_lines=100,
        trend_metadata_source_path=trend_metadata_source,
        required_trend_metadata_key="trend_snapshot_health",
    )
    assert any(item.kind == "wl125_trend_metadata_key_missing" for item in findings)


def test_wl125_impl_defines_required_governance_wrapper_function_defs() -> None:
    mod = _load_module()
    impl_path = ROOT / "src" / "thegent" / "cli" / "commands" / "impl.py"

    defined_functions = _top_level_function_defs(impl_path)
    required_wrappers = set(mod.PRE_WORK_GATE_WRAPPER_CONTRACTS) | set(mod.ORCHESTRATION_WRAPPER_CONTRACTS)
    missing = sorted(required_wrappers - defined_functions)
    assert missing == []


def test_wl125_architecture_check_still_expects_impl_wrapper_contracts() -> None:
    mod = _load_module()
    impl_path = ROOT / "src" / "thegent" / "cli" / "commands" / "impl.py"

    assert impl_path in mod.PRE_WORK_GATE_COMMAND_MODULES
    assert impl_path in mod.ORCHESTRATION_WRAPPER_COMMAND_MODULES
    assert set(mod.PRE_WORK_GATE_WRAPPER_CONTRACTS) == {
        "_pre_work_gate_defaults",
        "_pre_work_gate_thresholds",
        "_evidence_age_minutes",
        "_pre_work_governance_block_payload",
        "_enforce_pre_work_hard_gate",
    }
    assert set(mod.ORCHESTRATION_WRAPPER_CONTRACTS) == {
        "do_next_impl",
        "wait_next_impl",
        "spawn_next_impl",
        "work_stream_claim_impl",
        "work_stream_complete_impl",
        "incorporate_impl",
        "_validate_task_and_record_errors",
        "continuity_snapshot_impl",
    }
