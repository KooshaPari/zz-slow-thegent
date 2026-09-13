#!/usr/bin/env python3
"""Validate instruction architecture contracts (WL-139 follow-up phases A-D).

Checks:
1) CLAUDE.md Instruction Doc Map links resolve to existing files.
2) Optional anchors in doc-map links resolve to real markdown sections.
3) Project CLAUDE templates include required overlay sections.

Outputs summary JSON for quality-gate reporting.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_PATH = ROOT / "CLAUDE.md"
OVERLAY_TEMPLATE = ROOT / "templates" / "claude" / "CLAUDE.md.template"
PROJECT_TEMPLATE = (
    ROOT / "templates" / "initialize-project" / "{{ project_name }}" / "CLAUDE.md"
)

SECTION_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
MAP_ENTRY_RE = re.compile(r"`(?P<link>[^`]+\.md(?:#[A-Za-z0-9_-]+)?)`")

REQUIRED_SECTIONS: dict[Path, tuple[str, ...]] = {
    OVERLAY_TEMPLATE: (
        "Questionnaire Snapshot",
        "DX / AX / UX Baseline",
        "Project-Type Focus",
    ),
    PROJECT_TEMPLATE: (
        "Questionnaire Snapshot",
        "Project-Type Operating Model",
        "DX Contract",
        "AX Contract",
        "UX Contract",
    ),
}

PRE_WORK_GATE_COMMAND_MODULES: tuple[Path, ...] = (
    ROOT / "src" / "thegent" / "cli" / "commands" / "impl.py",
    ROOT / "src" / "thegent" / "cli" / "commands" / "work_stream_impl.py",
)

PRE_WORK_GATE_WRAPPER_CONTRACTS: dict[str, str] = {
    "_pre_work_gate_defaults": "pre_work_gate_defaults",
    "_pre_work_gate_thresholds": "pre_work_gate_thresholds",
    "_evidence_age_minutes": "evidence_age_minutes",
    "_pre_work_governance_block_payload": "pre_work_governance_block_payload",
    "_enforce_pre_work_hard_gate": "enforce_pre_work_hard_gate",
}

PRE_WORK_GATE_LITERAL_BLOCKLIST: tuple[str, ...] = (
    "WP-HG-05.pre_work_hard_gate",
    "~/.claude/.async-test-results.json",
    ".claude/verification/qa-state.json",
    ".claude/verification/qa-attestation.json",
    "require_e2e_first",
    "max_test_evidence_age_minutes",
    "max_build_evidence_age_minutes",
    "max_e2e_evidence_age_minutes",
    "Pre-work hard gate blocked new work start: missing or stale verification evidence.",
    "Refresh async test evidence:",
    "Refresh build/env evidence:",
    "Refresh e2e evidence:",
)

ORCHESTRATION_WRAPPER_COMMAND_MODULES: tuple[Path, ...] = PRE_WORK_GATE_COMMAND_MODULES

ORCHESTRATION_WRAPPER_CONTRACTS: dict[str, str] = {
    "do_next_impl": "do_next_impl",
    "wait_next_impl": "wait_next_impl",
    "spawn_next_impl": "spawn_next_impl",
    "work_stream_claim_impl": "work_stream_claim_impl",
    "work_stream_complete_impl": "work_stream_complete_impl",
    "incorporate_impl": "incorporate_impl",
    "_validate_task_and_record_errors": "_validate_task_and_record_errors",
    "continuity_snapshot_impl": "continuity_snapshot_impl",
}

MCP_SERVER_PATH = ROOT / "src" / "thegent" / "mcp" / "server.py"
MCP_SERVER_MAX_LINES = 500
MCP_SERVER_REQUIRED_WIRING_STRINGS: tuple[str, ...] = (
    "_server_execution_tools.register_execution_tools(",
    "_server_control_tools.register_control_tools(",
    "_server_planning_tools.register_planning_tools(",
    "_server_terminal_tools.register_terminal_tools(",
    "_server_research_tools.register_research_tools(",
    "_server_ops_tools.register_ops_tools(",
    "_server_optional_tools.register_optional_tools(",
)
MCP_SERVER_MAX_TOP_LEVEL_FUNCTIONS = 8
MCP_SERVER_MAX_MCP_TOOL_DECORATORS = 2

WL125_IMPL_PATH = ROOT / "src" / "thegent" / "cli" / "commands" / "impl.py"
WL125_IMPL_MAX_LINES = 1300
WL125_TREND_METADATA_SOURCE_PATH = (
    ROOT / "src" / "thegent" / "cli" / "services" / "run_observe_helpers.py"
)
WL125_IMPL_REQUIRED_TREND_METADATA_KEY = "trend_snapshot_health"


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    message: str


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if not body:
        return body
    first = body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return body[1:]
    return body


def _extract_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def _safe_attr_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _safe_attr_name(node.value)
        if base is None:
            return None
        return f"{base}.{node.attr}"
    return None


def _load_ast(path: Path) -> ast.Module | None:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    return ast.parse(content, filename=str(path))


def _validate_wrapper_delegation(
    *,
    module_path: Path,
    wrapper_name: str,
    helper_name: str,
) -> Finding | None:
    module_ast = _load_ast(module_path)
    if module_ast is None:
        return Finding(
            kind="pre_work_gate_module_missing",
            path=_display_path(module_path),
            message="Required command module for pre-work hard gate governance is missing.",
        )

    target: ast.FunctionDef | None = None
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name == wrapper_name:
            target = node
            break
    if target is None:
        return Finding(
            kind="pre_work_gate_wrapper_missing",
            path=_display_path(module_path),
            message=f"Missing required wrapper `{wrapper_name}` for pre-work gate helper delegation.",
        )

    body = _strip_docstring(target.body)
    if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
        return Finding(
            kind="pre_work_gate_wrapper_logic_leak",
            path=_display_path(module_path),
            message=f"Wrapper `{wrapper_name}` must be a single return delegation to pre_work_gate_helpers.",
        )

    call_expr = body[0].value
    if not isinstance(call_expr, ast.Call):
        return Finding(
            kind="pre_work_gate_wrapper_logic_leak",
            path=_display_path(module_path),
            message=f"Wrapper `{wrapper_name}` must return a helper call directly.",
        )
    if not (
        isinstance(call_expr.func, ast.Attribute)
        and isinstance(call_expr.func.value, ast.Name)
        and call_expr.func.value.id == "pre_work_gate_helpers"
        and call_expr.func.attr == helper_name
    ):
        return Finding(
            kind="pre_work_gate_wrapper_logic_leak",
            path=_display_path(module_path),
            message=(
                f"Wrapper `{wrapper_name}` must delegate to "
                f"`pre_work_gate_helpers.{helper_name}`."
            ),
        )

    expected_params = [
        arg.arg
        for arg in target.args.posonlyargs + target.args.args + target.args.kwonlyargs
    ]
    passed_params: list[str] = []
    for arg in call_expr.args:
        arg_name = _extract_name(arg)
        if arg_name is None:
            return Finding(
                kind="pre_work_gate_wrapper_logic_leak",
                path=_display_path(module_path),
                message=f"Wrapper `{wrapper_name}` must pass through parameters without transformation.",
            )
        passed_params.append(arg_name)
    for kw in call_expr.keywords:
        if kw.arg is None:
            return Finding(
                kind="pre_work_gate_wrapper_logic_leak",
                path=_display_path(module_path),
                message=f"Wrapper `{wrapper_name}` must not use **kwargs in helper delegation.",
            )
        kw_value_name = _extract_name(kw.value)
        if kw_value_name is None or kw_value_name != kw.arg:
            return Finding(
                kind="pre_work_gate_wrapper_logic_leak",
                path=_display_path(module_path),
                message=f"Wrapper `{wrapper_name}` must pass `{kw.arg}` through unchanged.",
            )
        passed_params.append(kw.arg)

    if sorted(expected_params) != sorted(passed_params):
        return Finding(
            kind="pre_work_gate_wrapper_logic_leak",
            path=_display_path(module_path),
            message=f"Wrapper `{wrapper_name}` must pass through all original parameters unchanged.",
        )
    return None


def _validate_orchestration_wrapper_delegation(
    *,
    module_path: Path,
    wrapper_name: str,
    helper_name: str,
) -> Finding | None:
    module_ast = _load_ast(module_path)
    if module_ast is None:
        return Finding(
            kind="orchestration_wrapper_module_missing",
            path=_display_path(module_path),
            message="Required command module for orchestration wrapper governance is missing.",
        )

    target: ast.FunctionDef | None = None
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name == wrapper_name:
            target = node
            break
    if target is None:
        return Finding(
            kind="orchestration_wrapper_missing",
            path=_display_path(module_path),
            message=f"Missing required orchestration wrapper `{wrapper_name}` in command module.",
        )

    body = _strip_docstring(target.body)
    if len(body) != 1:
        return Finding(
            kind="orchestration_wrapper_logic_leak",
            path=_display_path(module_path),
            message=(
                f"Orchestration business logic is banned from command modules; "
                f"`{wrapper_name}` must contain only direct delegation."
            ),
        )

    call_expr: ast.Call | None = None
    stmt = body[0]
    if (
        isinstance(stmt, ast.Return)
        and stmt.value is not None
        and isinstance(stmt.value, ast.Call)
    ) or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
        call_expr = stmt.value

    if call_expr is None:
        return Finding(
            kind="orchestration_wrapper_logic_leak",
            path=_display_path(module_path),
            message=f"Wrapper `{wrapper_name}` must delegate with a single direct call.",
        )

    if not (
        isinstance(call_expr.func, ast.Attribute)
        and isinstance(call_expr.func.value, ast.Name)
        and call_expr.func.value.id == "work_stream_orchestration"
        and call_expr.func.attr == helper_name
    ):
        return Finding(
            kind="orchestration_wrapper_logic_leak",
            path=_display_path(module_path),
            message=(
                f"Wrapper `{wrapper_name}` must delegate directly to "
                f"`work_stream_orchestration.{helper_name}`."
            ),
        )

    expected_params = [
        arg.arg
        for arg in target.args.posonlyargs + target.args.args + target.args.kwonlyargs
    ]
    passed_params: list[str] = []
    for arg in call_expr.args:
        arg_name = _extract_name(arg)
        if arg_name is None:
            return Finding(
                kind="orchestration_wrapper_logic_leak",
                path=_display_path(module_path),
                message=f"Wrapper `{wrapper_name}` must pass through parameters without transformation.",
            )
        passed_params.append(arg_name)
    for kw in call_expr.keywords:
        if kw.arg is None:
            return Finding(
                kind="orchestration_wrapper_logic_leak",
                path=_display_path(module_path),
                message=f"Wrapper `{wrapper_name}` must not use **kwargs in orchestration delegation.",
            )
        kw_value_name = _extract_name(kw.value)
        if kw_value_name is None or kw_value_name != kw.arg:
            return Finding(
                kind="orchestration_wrapper_logic_leak",
                path=_display_path(module_path),
                message=f"Wrapper `{wrapper_name}` must pass `{kw.arg}` through unchanged.",
            )
        passed_params.append(kw.arg)

    if sorted(expected_params) != sorted(passed_params):
        return Finding(
            kind="orchestration_wrapper_logic_leak",
            path=_display_path(module_path),
            message=f"Wrapper `{wrapper_name}` must pass through all original parameters unchanged.",
        )
    return None


def validate_pre_work_gate_command_module(
    *,
    module_path: Path,
    wrapper_contracts: dict[str, str] | None = None,
    literal_blocklist: tuple[str, ...] = PRE_WORK_GATE_LITERAL_BLOCKLIST,
) -> list[Finding]:
    contracts = wrapper_contracts or PRE_WORK_GATE_WRAPPER_CONTRACTS
    findings: list[Finding] = []

    if not module_path.exists():
        findings.append(
            Finding(
                kind="pre_work_gate_module_missing",
                path=_display_path(module_path),
                message="Required command module for pre-work hard gate governance is missing.",
            )
        )
        return findings

    content = module_path.read_text(encoding="utf-8")
    for literal in literal_blocklist:
        if literal in content:
            findings.append(
                Finding(
                    kind="pre_work_gate_literal_duplicate",
                    path=_display_path(module_path),
                    message=(
                        "Pre-work hard-gate business literal leaked into command module; "
                        f"keep it in service helper only: {literal}"
                    ),
                )
            )

    for wrapper_name, helper_name in contracts.items():
        finding = _validate_wrapper_delegation(
            module_path=module_path,
            wrapper_name=wrapper_name,
            helper_name=helper_name,
        )
        if finding is not None:
            findings.append(finding)
    return findings


def validate_pre_work_gate_governance(
    command_modules: tuple[Path, ...] = PRE_WORK_GATE_COMMAND_MODULES,
) -> list[Finding]:
    findings: list[Finding] = []
    for module_path in command_modules:
        findings.extend(validate_pre_work_gate_command_module(module_path=module_path))
    return findings


def validate_orchestration_wrapper_command_module(
    *,
    module_path: Path,
    wrapper_contracts: dict[str, str] | None = None,
) -> list[Finding]:
    contracts = wrapper_contracts or ORCHESTRATION_WRAPPER_CONTRACTS
    findings: list[Finding] = []

    if not module_path.exists():
        findings.append(
            Finding(
                kind="orchestration_wrapper_module_missing",
                path=_display_path(module_path),
                message="Required command module for orchestration wrapper governance is missing.",
            )
        )
        return findings

    for wrapper_name, helper_name in contracts.items():
        finding = _validate_orchestration_wrapper_delegation(
            module_path=module_path,
            wrapper_name=wrapper_name,
            helper_name=helper_name,
        )
        if finding is not None:
            findings.append(finding)
    return findings


def validate_orchestration_wrapper_governance(
    command_modules: tuple[Path, ...] = ORCHESTRATION_WRAPPER_COMMAND_MODULES,
) -> list[Finding]:
    findings: list[Finding] = []
    for module_path in command_modules:
        findings.extend(
            validate_orchestration_wrapper_command_module(module_path=module_path)
        )
    return findings


def validate_mcp_server_boundary(
    *,
    server_path: Path = MCP_SERVER_PATH,
    max_lines: int = MCP_SERVER_MAX_LINES,
    required_wiring_strings: tuple[str, ...] = MCP_SERVER_REQUIRED_WIRING_STRINGS,
    max_top_level_functions: int = MCP_SERVER_MAX_TOP_LEVEL_FUNCTIONS,
    max_mcp_tool_decorators: int = MCP_SERVER_MAX_MCP_TOOL_DECORATORS,
) -> list[Finding]:
    findings: list[Finding] = []

    if not server_path.exists():
        findings.append(
            Finding(
                kind="mcp_server_missing",
                path=_display_path(server_path),
                message="MCP server boundary target is missing.",
            )
        )
        return findings

    content = server_path.read_text(encoding="utf-8")
    line_count = len(content.splitlines())
    if line_count > max_lines:
        findings.append(
            Finding(
                kind="mcp_server_line_ceiling",
                path=_display_path(server_path),
                message=f"server.py line count {line_count} exceeds ceiling {max_lines}.",
            )
        )

    for wiring in required_wiring_strings:
        if wiring not in content:
            findings.append(
                Finding(
                    kind="mcp_server_wiring_missing",
                    path=_display_path(server_path),
                    message=f"Missing required MCP extraction wiring: {wiring}",
                )
            )

    module_ast = _load_ast(server_path)
    if module_ast is None:
        return findings

    top_level_functions = [
        node
        for node in module_ast.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if len(top_level_functions) > max_top_level_functions:
        findings.append(
            Finding(
                kind="mcp_server_top_level_functions",
                path=_display_path(server_path),
                message=(
                    f"server.py exposes {len(top_level_functions)} top-level functions; "
                    f"expected <= {max_top_level_functions} in extracted architecture."
                ),
            )
        )

    mcp_tool_decorator_count = 0
    for node in ast.walk(module_ast):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if _safe_attr_name(decorator.func) == "mcp.tool":
                mcp_tool_decorator_count += 1
    if mcp_tool_decorator_count > max_mcp_tool_decorators:
        findings.append(
            Finding(
                kind="mcp_server_tool_decorator_count",
                path=_display_path(server_path),
                message=(
                    f"server.py defines {mcp_tool_decorator_count} @mcp.tool decorators; "
                    f"expected <= {max_mcp_tool_decorators}."
                ),
            )
        )
    return findings


def validate_wl125_impl_boundary(
    *,
    impl_path: Path = WL125_IMPL_PATH,
    max_lines: int = WL125_IMPL_MAX_LINES,
    trend_metadata_source_path: Path = WL125_TREND_METADATA_SOURCE_PATH,
    required_trend_metadata_key: str = WL125_IMPL_REQUIRED_TREND_METADATA_KEY,
) -> list[Finding]:
    findings: list[Finding] = []

    if not impl_path.exists():
        findings.append(
            Finding(
                kind="wl125_impl_missing",
                path=_display_path(impl_path),
                message="WL-125 boundary target is missing.",
            )
        )
        return findings

    content = impl_path.read_text(encoding="utf-8")
    line_count = len(content.splitlines())
    if line_count > max_lines:
        findings.append(
            Finding(
                kind="wl125_impl_line_ceiling",
                path=_display_path(impl_path),
                message=f"impl.py line count {line_count} exceeds WL-125 ceiling {max_lines}.",
            )
        )

    if not trend_metadata_source_path.exists():
        findings.append(
            Finding(
                kind="wl125_trend_metadata_source_missing",
                path=_display_path(trend_metadata_source_path),
                message="WL-125 trend metadata source file is missing.",
            )
        )
        return findings

    trend_metadata_content = trend_metadata_source_path.read_text(encoding="utf-8")
    if required_trend_metadata_key not in trend_metadata_content:
        findings.append(
            Finding(
                kind="wl125_trend_metadata_key_missing",
                path=_display_path(trend_metadata_source_path),
                message=(
                    "WL-125 trend warning metadata key missing from trend metadata source: "
                    f"{required_trend_metadata_key}"
                ),
            )
        )

    return findings


def slugify_heading(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"[^a-z0-9\s-]", "", normalized)
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def extract_heading_slugs(path: Path) -> set[str]:
    content = path.read_text(encoding="utf-8")
    slugs: set[str] = set()
    for line in content.splitlines():
        match = SECTION_RE.match(line)
        if not match:
            continue
        slugs.add(slugify_heading(match.group(1)))
    return slugs


def resolve_local_doc(link: str) -> tuple[Path, str | None]:
    doc_part, _, anchor = link.partition("#")
    target = (ROOT / doc_part).resolve()
    return target, (anchor or None)


def extract_instruction_doc_map_links(claude_content: str) -> list[str]:
    links: list[str] = []
    in_map = False
    for line in claude_content.splitlines():
        if line.strip() == "## Instruction Doc Map":
            in_map = True
            continue
        if in_map and line.startswith("## "):
            break
        if not in_map:
            continue
        match = MAP_ENTRY_RE.search(line)
        if match:
            links.append(match.group("link"))
    return links


def validate_doc_map_links(claude_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    content = claude_path.read_text(encoding="utf-8")
    links = extract_instruction_doc_map_links(content)
    if not links:
        findings.append(
            Finding(
                kind="map_missing",
                path=_display_path(claude_path),
                message="Instruction Doc Map is missing or has no markdown links.",
            )
        )
        return findings

    for link in links:
        target, anchor = resolve_local_doc(link)
        rel = str(Path(link.split("#", 1)[0]))
        if not target.exists():
            findings.append(
                Finding(
                    kind="broken_link",
                    path=_display_path(claude_path),
                    message=f"Doc-map target does not exist: {rel}",
                )
            )
            continue
        if anchor:
            slugs = extract_heading_slugs(target)
            if anchor not in slugs:
                findings.append(
                    Finding(
                        kind="stale_anchor",
                        path=_display_path(target),
                        message=f"Anchor '#{anchor}' not found in heading slugs.",
                    )
                )
    return findings


def validate_required_sections() -> list[Finding]:
    findings: list[Finding] = []
    for template_path, required in REQUIRED_SECTIONS.items():
        if not template_path.exists():
            findings.append(
                Finding(
                    kind="missing_template",
                    path=_display_path(template_path),
                    message="Required template file is missing.",
                )
            )
            continue

        headings = extract_heading_slugs(template_path)
        for section in required:
            slug = slugify_heading(section)
            if slug not in headings:
                findings.append(
                    Finding(
                        kind="missing_section",
                        path=_display_path(template_path),
                        message=f"Missing required section: {section}",
                    )
                )
    return findings


def run_checks() -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(validate_doc_map_links(CLAUDE_PATH))
    findings.extend(validate_required_sections())
    findings.extend(validate_pre_work_gate_governance())
    findings.extend(validate_orchestration_wrapper_governance())
    findings.extend(validate_mcp_server_boundary())
    findings.extend(validate_wl125_impl_boundary())
    return findings


def build_summary(findings: list[Finding]) -> dict[str, object]:
    by_kind: dict[str, int] = {}
    for item in findings:
        by_kind[item.kind] = by_kind.get(item.kind, 0) + 1
    return {
        "ok": not findings,
        "finding_count": len(findings),
        "by_kind": by_kind,
        "checked": {
            "doc_map_source": str(CLAUDE_PATH.relative_to(ROOT)),
            "templates": [str(path.relative_to(ROOT)) for path in REQUIRED_SECTIONS],
            "pre_work_gate_command_modules": [
                str(path.relative_to(ROOT)) for path in PRE_WORK_GATE_COMMAND_MODULES
            ],
            "orchestration_wrapper_command_modules": [
                str(path.relative_to(ROOT))
                for path in ORCHESTRATION_WRAPPER_COMMAND_MODULES
            ],
            "mcp_server_boundary_target": str(MCP_SERVER_PATH.relative_to(ROOT)),
            "wl125_impl_boundary_target": str(WL125_IMPL_PATH.relative_to(ROOT)),
            "wl125_trend_metadata_source": str(
                WL125_TREND_METADATA_SOURCE_PATH.relative_to(ROOT)
            ),
            "wl125_trend_warning_metadata_key": WL125_IMPL_REQUIRED_TREND_METADATA_KEY,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true", help="Exit non-zero when findings exist."
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=ROOT / ".quality" / "instruction-architecture-summary.json",
        help="Write summary JSON artifact.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    findings = run_checks()
    summary = build_summary(findings)

    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    if args.format == "json":
        payload = {
            "summary": summary,
            "findings": [finding.__dict__ for finding in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Instruction architecture check")
        print(f"- findings: {len(findings)}")
        print(f"- summary artifact: {args.summary_json.relative_to(ROOT)}")
        for finding in findings:
            print(f"  - [{finding.kind}] {finding.path}: {finding.message}")

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
