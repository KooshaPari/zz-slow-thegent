"""Governance checks for split e2e CLI modules."""

from __future__ import annotations

import ast
import shlex
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPLIT_E2E_FILES = [
    REPO_ROOT / "tests" / "test_e2e_cli_core_a.py",
    REPO_ROOT / "tests" / "test_e2e_cli_core_b.py",
    REPO_ROOT / "tests" / "test_e2e_cli_aliases.py",
    REPO_ROOT / "tests" / "test_e2e_cli_overlays.py",
]
HARD_LINE_CAP = 2500
REQUIRED_E2E_GOVERNANCE_FILES = [
    REPO_ROOT / "tests" / "e2e" / "cli_runner_compat.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_alias_rewrite_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_alias_rewrite_real_app.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_alias_unsupported_rationale.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_runner_compat.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_runner_extracts.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_runner_import_governance.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_runner_rewrite_guards.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_runner_skip_message_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_runner_skip_prefix_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_cli_runner_unicode_tokens.py",
    REPO_ROOT / "tests" / "e2e" / "test_command_surface.py",
    REPO_ROOT / "tests" / "e2e" / "test_e2e_module_pairing.py",
    REPO_ROOT / "tests" / "e2e" / "test_governance_artifact_schema_policy.py",
    REPO_ROOT / "tests" / "e2e" / "test_governance_delta_report.py",
    REPO_ROOT / "tests" / "e2e" / "test_governance_health_artifact.py",
    REPO_ROOT / "tests" / "e2e" / "test_governance_inventory_artifact.py",
    REPO_ROOT / "tests" / "e2e" / "test_governance_registry_order.py",
    REPO_ROOT / "tests" / "e2e" / "test_governance_set_equality.py",
    REPO_ROOT / "tests" / "e2e" / "test_governance_sync_contracts.py",
    REPO_ROOT / "tests" / "e2e" / "test_helper_governance_loophole_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_bundle_order_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_collect_only_commands.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_command_normalized_duplicates.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_command_uniqueness.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_direct_command_token_sanitizer.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_e2e_commands.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_row_file_bijection.py",
    REPO_ROOT / "tests" / "e2e" / "test_readme_row_order_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_real_app_command_families.py",
    REPO_ROOT / "tests" / "e2e" / "test_real_app_help_anchor_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_smoke_runner_governance.py",
    REPO_ROOT / "tests" / "e2e" / "test_split_hygiene.py",
    REPO_ROOT / "tests" / "e2e" / "test_split_marker_governance.py",
    REPO_ROOT / "tests" / "e2e" / "test_split_marker_placement_consistency.py",
    REPO_ROOT / "tests" / "e2e" / "test_top_level_command_snapshot_contract.py",
    REPO_ROOT / "tests" / "e2e" / "test_unsupported_alias_real_app_evidence.py",
]
ALIAS_REWRITE_CONTRACT_TEST = REPO_ROOT / "tests" / "e2e" / "test_cli_alias_rewrite_contract.py"
E2E_README = REPO_ROOT / "tests" / "e2e" / "README.md"
REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND = (
    "pytest -q "
    "tests/e2e/test_cli_alias_rewrite_contract.py "
    "tests/e2e/test_cli_alias_rewrite_real_app.py "
    "tests/e2e/test_cli_alias_unsupported_rationale.py "
    "tests/e2e/test_cli_runner_compat.py "
    "tests/e2e/test_cli_runner_extracts.py "
    "tests/e2e/test_cli_runner_import_governance.py "
    "tests/e2e/test_cli_runner_rewrite_guards.py "
    "tests/e2e/test_cli_runner_skip_message_contract.py "
    "tests/e2e/test_cli_runner_skip_prefix_contract.py "
    "tests/e2e/test_cli_runner_unicode_tokens.py "
    "tests/e2e/test_command_surface.py "
    "tests/e2e/test_e2e_module_pairing.py "
    "tests/e2e/test_governance_artifact_schema_policy.py "
    "tests/e2e/test_governance_delta_report.py "
    "tests/e2e/test_governance_health_artifact.py "
    "tests/e2e/test_governance_inventory_artifact.py "
    "tests/e2e/test_governance_registry_order.py "
    "tests/e2e/test_governance_set_equality.py "
    "tests/e2e/test_governance_sync_contracts.py "
    "tests/e2e/test_helper_governance_loophole_contract.py "
    "tests/e2e/test_readme_bundle_order_contract.py "
    "tests/e2e/test_readme_collect_only_commands.py "
    "tests/e2e/test_readme_command_normalized_duplicates.py "
    "tests/e2e/test_readme_command_uniqueness.py "
    "tests/e2e/test_readme_direct_command_token_sanitizer.py "
    "tests/e2e/test_readme_e2e_commands.py "
    "tests/e2e/test_readme_row_file_bijection.py "
    "tests/e2e/test_readme_row_order_contract.py "
    "tests/e2e/test_real_app_command_families.py "
    "tests/e2e/test_real_app_help_anchor_contract.py "
    "tests/e2e/test_smoke_runner_governance.py "
    "tests/e2e/test_split_hygiene.py "
    "tests/e2e/test_split_marker_governance.py "
    "tests/e2e/test_split_marker_placement_consistency.py "
    "tests/e2e/test_top_level_command_snapshot_contract.py "
    "tests/e2e/test_unsupported_alias_real_app_evidence.py"
)


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_split_e2e_files_exist() -> None:
    for path in SPLIT_E2E_FILES:
        assert path.exists(), f"missing split e2e file: {path}"


def test_split_e2e_files_import_shared_cli_assertions_helpers() -> None:
    for path in SPLIT_E2E_FILES:
        module = _parse_module(path)
        has_shared_cli_assertions_import = any(
            isinstance(node, ast.ImportFrom) and node.module == "tests.e2e.cli_assertions" for node in module.body
        )
        assert has_shared_cli_assertions_import, (
            f"{path} must import shared cli_assertions helpers from tests.e2e.cli_assertions"
        )


def test_split_e2e_files_do_not_redefine_shared_helpers() -> None:
    forbidden_defs = {
        "load_cli_json",
        "expected_trend_health_signature",
    }
    for path in SPLIT_E2E_FILES:
        module = _parse_module(path)
        local_defs = {
            node.name for node in ast.walk(module) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        overlap = sorted(forbidden_defs & local_defs)
        assert not overlap, f"{path} redefines shared helper(s): {', '.join(overlap)}"


def test_split_e2e_files_use_compat_cli_runner_only() -> None:
    forbidden_cli_runner_modules = {"click.testing", "typer.testing"}

    for path in SPLIT_E2E_FILES:
        module = _parse_module(path)
        imports_compat_cli_runner = False
        has_bare_cli_runner_import = False
        has_bare_cli_runner_instantiation = False

        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom):
                if node.module == "tests.e2e.cli_runner_compat" and any(
                    alias.name == "CompatCliRunner" for alias in node.names
                ):
                    imports_compat_cli_runner = True

                if node.module in forbidden_cli_runner_modules and any(
                    alias.name == "CliRunner" for alias in node.names
                ):
                    has_bare_cli_runner_import = True

            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "CompatCliRunner":
                    imports_compat_cli_runner = True
                if node.func.id == "CliRunner":
                    has_bare_cli_runner_instantiation = True

        assert imports_compat_cli_runner, f"{path} must import and/or instantiate CompatCliRunner for CLI e2e tests"
        assert not has_bare_cli_runner_import, (
            f"{path} imports bare CliRunner; use CompatCliRunner from tests.e2e.cli_runner_compat"
        )
        assert not has_bare_cli_runner_instantiation, f"{path} instantiates bare CliRunner(); use CompatCliRunner()"


def test_split_e2e_files_within_hard_line_cap() -> None:
    for path in SPLIT_E2E_FILES:
        line_count = sum(1 for _ in path.open(encoding="utf-8"))
        assert line_count <= HARD_LINE_CAP, f"{path} has {line_count} lines (> {HARD_LINE_CAP})"


def test_required_e2e_governance_files_exist() -> None:
    for path in REQUIRED_E2E_GOVERNANCE_FILES:
        assert path.exists(), f"missing e2e governance file: {path}"


def test_required_e2e_governance_files_have_no_duplicates() -> None:
    seen: set[Path] = set()
    duplicates: list[Path] = []

    for path in REQUIRED_E2E_GOVERNANCE_FILES:
        if path in seen and path not in duplicates:
            duplicates.append(path)
        seen.add(path)

    assert not duplicates, "duplicate entries in REQUIRED_E2E_GOVERNANCE_FILES: " + ", ".join(
        str(path) for path in duplicates
    )


def test_alias_rewrite_contract_is_mandatory_governance_file() -> None:
    assert ALIAS_REWRITE_CONTRACT_TEST in REQUIRED_E2E_GOVERNANCE_FILES


def test_readme_mentions_alias_rewrite_governance_and_troubleshooting_semantics() -> None:
    text = E2E_README.read_text(encoding="utf-8")

    assert "pytest -q tests/test_e2e_cli_aliases.py -k rewrite" in text
    assert "No such command" in text
    assert "No such option" in text


def test_readme_mentions_direct_alias_rewrite_and_command_surface_unit_commands() -> None:
    text = E2E_README.read_text(encoding="utf-8")

    assert "Alias rewrite contract unit (direct)" in text
    assert "pytest -q tests/e2e/test_cli_alias_rewrite_contract.py" in text
    assert "Alias rewrite real-app contract unit (direct)" in text
    assert "pytest -q tests/e2e/test_cli_alias_rewrite_real_app.py" in text
    assert "Alias unsupported rationale contract (direct)" in text
    assert "pytest -q tests/e2e/test_cli_alias_unsupported_rationale.py" in text
    assert "Real-app command families contract (direct)" in text
    assert "pytest -q tests/e2e/test_real_app_command_families.py" in text
    assert "Real-app help anchor contract (direct)" in text
    assert "pytest -q tests/e2e/test_real_app_help_anchor_contract.py" in text
    assert "Command-surface unit (direct)" in text
    assert "pytest -q tests/e2e/test_command_surface.py" in text
    assert "Compat helper extract/rewrite guard suite (direct)" in text
    assert ("pytest -q tests/e2e/test_cli_runner_extracts.py tests/e2e/test_cli_runner_rewrite_guards.py") in text
    assert "Compat skip-message contract suite (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_skip_message_contract.py" in text
    assert "Compat skip-prefix contract suite (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_skip_prefix_contract.py" in text
    assert "Compat edge-token suite (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_unicode_tokens.py" in text
    assert "Compat import governance (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_import_governance.py" in text
    assert "Utility module pairing governance (direct)" in text
    assert "pytest -q tests/e2e/test_e2e_module_pairing.py" in text
    assert "Smoke runner governance (direct)" in text
    assert "pytest -q tests/e2e/test_smoke_runner_governance.py" in text
    assert "Split marker governance (direct)" in text
    assert "pytest -q tests/e2e/test_split_marker_governance.py" in text
    assert "Governance sync contracts (direct)" in text
    assert "pytest -q tests/e2e/test_governance_sync_contracts.py" in text
    assert "Governance health artifact (direct)" in text
    assert "pytest -q tests/e2e/test_governance_health_artifact.py" in text
    assert "Governance inventory artifact (direct)" in text
    assert "pytest -q tests/e2e/test_governance_inventory_artifact.py" in text
    assert "Governance set equality (direct)" in text
    assert "pytest -q tests/e2e/test_governance_set_equality.py" in text
    assert "README bundle order contract (direct)" in text
    assert "pytest -q tests/e2e/test_readme_bundle_order_contract.py" in text
    assert "README row order contract (direct)" in text
    assert "pytest -q tests/e2e/test_readme_row_order_contract.py" in text
    assert "README command uniqueness (direct)" in text
    assert "pytest -q tests/e2e/test_readme_command_uniqueness.py" in text
    assert "README command normalized-duplicates (direct)" in text
    assert "pytest -q tests/e2e/test_readme_command_normalized_duplicates.py" in text
    assert "README direct e2e collect-only governance (direct)" in text
    assert "pytest -q tests/e2e/test_readme_collect_only_commands.py" in text


def test_readme_mentions_full_governance_unit_bundle_command() -> None:
    text = E2E_README.read_text(encoding="utf-8")

    assert "Full e2e governance unit bundle (direct)" in text
    assert REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND in text


def test_e2e_readme_exists_and_is_non_empty() -> None:
    assert E2E_README.exists(), f"missing e2e README: {E2E_README}"
    assert E2E_README.stat().st_size > 0, f"e2e README is empty: {E2E_README}"


def test_required_e2e_governance_paths_use_tests_e2e_python_files() -> None:
    relative_paths = [path.relative_to(REPO_ROOT).as_posix() for path in REQUIRED_E2E_GOVERNANCE_FILES]
    assert relative_paths, "REQUIRED_E2E_GOVERNANCE_FILES must not be empty"
    assert all(path.startswith("tests/e2e/") and path.endswith(".py") for path in relative_paths), (
        "all REQUIRED_E2E_GOVERNANCE_FILES entries must be Python files under tests/e2e/"
    )


def test_governance_bundle_command_paths_are_mandatory_governance_tests() -> None:
    bundle_paths = {
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    }
    expected_governance_test_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in REQUIRED_E2E_GOVERNANCE_FILES
        if path.name.startswith("test_")
    }
    assert bundle_paths, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    assert bundle_paths <= expected_governance_test_paths, (
        "bundle command includes paths not present in REQUIRED_E2E_GOVERNANCE_FILES"
    )


def test_governance_bundle_command_contains_each_mandatory_test_once() -> None:
    bundle_test_paths = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    expected_governance_test_paths = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REQUIRED_E2E_GOVERNANCE_FILES
        if path.name.startswith("test_")
    ]
    assert bundle_test_paths, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    assert len(bundle_test_paths) == len(set(bundle_test_paths)), (
        "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must not contain duplicate test paths"
    )
    assert bundle_test_paths == expected_governance_test_paths, (
        "bundle command must contain every REQUIRED_E2E_GOVERNANCE_FILES test_* entry exactly once"
    )


def test_governance_bundle_command_includes_split_hygiene_and_readme_e2e_commands() -> None:
    bundle_test_paths = {
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    }
    assert "tests/e2e/test_split_hygiene.py" in bundle_test_paths
    assert "tests/e2e/test_readme_e2e_commands.py" in bundle_test_paths


def test_governance_bundle_command_path_tokens_are_ascii_only() -> None:
    path_tokens = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_tokens, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    non_ascii = [token for token in path_tokens if not token.isascii()]
    assert not non_ascii, "bundle command path tokens must be ASCII-only: " + ", ".join(non_ascii)


def test_governance_bundle_command_path_tokens_are_relative() -> None:
    path_tokens = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_tokens, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    absolute = [token for token in path_tokens if token.startswith("/")]
    assert not absolute, "bundle command path tokens must be relative (no leading slash): " + ", ".join(absolute)


def test_governance_bundle_command_includes_split_hygiene_exactly_once() -> None:
    path_tokens = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_tokens, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    assert path_tokens.count("tests/e2e/test_split_hygiene.py") == 1, (
        "bundle command must include tests/e2e/test_split_hygiene.py exactly once"
    )


def test_governance_bundle_command_includes_readme_e2e_commands_exactly_once() -> None:
    path_tokens = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_tokens, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    assert path_tokens.count("tests/e2e/test_readme_e2e_commands.py") == 1, (
        "bundle command must include tests/e2e/test_readme_e2e_commands.py exactly once"
    )


def test_governance_bundle_command_path_list_has_no_empty_or_whitespace_surrounded_tokens() -> None:
    raw_tokens = REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND.split(" ")
    path_indices = [
        index for index, token in enumerate(raw_tokens) if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_indices, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    path_token_window = raw_tokens[path_indices[0] : path_indices[-1] + 1]
    empty_tokens = [token for token in path_token_window if token == ""]
    whitespace_surrounded = [token for token in path_token_window if token and token != token.strip()]
    assert not empty_tokens, "bundle path list must not contain empty tokens"
    assert not whitespace_surrounded, "bundle path list must not contain whitespace-surrounded tokens: " + ", ".join(
        whitespace_surrounded
    )


def test_governance_bundle_command_test_paths_are_lexicographically_sorted() -> None:
    bundle_test_paths = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert bundle_test_paths, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    assert bundle_test_paths == sorted(bundle_test_paths), "bundle command test paths must be lexicographically sorted"


def test_governance_bundle_command_includes_only_e2e_test_modules() -> None:
    bundle_test_paths = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert bundle_test_paths, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    assert all(Path(path).name.startswith("test_") for path in bundle_test_paths), (
        "bundle command must include only tests/e2e/test_*.py files"
    )


def test_governance_bundle_command_has_no_helper_module_paths() -> None:
    path_tokens = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_tokens, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    invalid = [token for token in path_tokens if not Path(token).name.startswith("test_")]
    assert not invalid, (
        "bundle command must not include helper-module paths; only tests/e2e/test_*.py is allowed: "
        + ", ".join(invalid)
    )


def test_full_governance_bundle_command_contains_no_paths_outside_tests_e2e_test_pattern() -> None:
    python_path_tokens = [
        token for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND) if token.endswith(".py")
    ]
    assert python_path_tokens, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include Python test path tokens"
    invalid = [
        token
        for token in python_path_tokens
        if not (token.startswith("tests/e2e/test_") and Path(token).name.startswith("test_"))
    ]
    assert not invalid, (
        "full governance bundle command must not include paths outside tests/e2e/test_*.py: " + ", ".join(invalid)
    )


def test_full_governance_bundle_command_matches_required_test_governance_files_exactly() -> None:
    bundle_test_paths = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/test_") and token.endswith(".py")
    ]
    required_test_paths = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REQUIRED_E2E_GOVERNANCE_FILES
        if path.name.startswith("test_")
    ]
    assert bundle_test_paths, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include tests/e2e/test_*.py paths"
    assert len(bundle_test_paths) == len(required_test_paths), (
        "full governance bundle command test_* path count must match required test_* governance file count"
    )
    assert set(bundle_test_paths) == set(required_test_paths), (
        "full governance bundle command must include all required test_* governance files with no extras"
    )


def test_governance_bundle_command_path_tokens_are_contiguous() -> None:
    tokens = shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
    path_indices = [
        index for index, token in enumerate(tokens) if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_indices, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"
    first = path_indices[0]
    last = path_indices[-1]
    interleaved = [token for token in tokens[first : last + 1] if not token.startswith("tests/e2e/")]
    assert not interleaved, (
        "bundle command path tokens must be contiguous with no interleaved non-path args after first test path: "
        + ", ".join(interleaved)
    )


def test_governance_bundle_command_after_first_test_path_contains_only_test_paths() -> None:
    tokens = shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
    first_test_path_index = next(
        (index for index, token in enumerate(tokens) if token.startswith("tests/e2e/test_") and token.endswith(".py")),
        None,
    )
    assert first_test_path_index is not None, (
        "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include tests/e2e/test_*.py paths"
    )

    trailing_tokens = tokens[first_test_path_index:]
    invalid = [
        token for token in trailing_tokens if not (token.startswith("tests/e2e/test_") and token.endswith(".py"))
    ]
    assert not invalid, (
        "after the first tests/e2e/test_*.py token, all remaining tokens must be tests/e2e/test_*.py paths: "
        + ", ".join(invalid)
    )


def test_governance_bundle_command_test_path_count_matches_required_test_file_count() -> None:
    bundle_test_path_count = sum(
        1
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/test_") and token.endswith(".py")
    )
    required_test_file_count = sum(1 for path in REQUIRED_E2E_GOVERNANCE_FILES if path.name.startswith("test_"))
    assert bundle_test_path_count == required_test_file_count, (
        "bundle command tests/e2e/test_*.py path count must match REQUIRED_E2E_GOVERNANCE_FILES test_* entry count"
    )


def test_governance_bundle_command_path_tokens_have_stable_sorted_multiset_diff() -> None:
    bundle_path_tokens = [
        token
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/test_") and token.endswith(".py")
    ]
    required_path_tokens = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REQUIRED_E2E_GOVERNANCE_FILES
        if path.name.startswith("test_")
    ]
    assert bundle_path_tokens, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include test paths"

    sorted_bundle = sorted(bundle_path_tokens)
    sorted_required = sorted(required_path_tokens)
    bundle_only = sorted(set(sorted_bundle) - set(sorted_required))
    required_only = sorted(set(sorted_required) - set(sorted_bundle))

    assert len(sorted_bundle) == len(sorted_required), (
        "bundle vs required path-token counts differ under sorted-token comparison: "
        f"bundle={len(sorted_bundle)} required={len(sorted_required)}"
    )
    assert sorted_bundle == sorted_required, (
        "bundle path-token multiset is unstable under sorted-token diff checks; "
        f"bundle_only={bundle_only}, required_only={required_only}"
    )


def test_full_bundle_path_basenames_match_required_test_basenames_exactly() -> None:
    bundle_test_basenames = sorted(
        Path(token).name
        for token in shlex.split(REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/test_") and token.endswith(".py")
    )
    required_test_basenames = sorted(
        path.name for path in REQUIRED_E2E_GOVERNANCE_FILES if path.name.startswith("test_")
    )
    assert bundle_test_basenames, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include tests/e2e/test_*.py paths"
    assert bundle_test_basenames == required_test_basenames, (
        "full-bundle path basenames must equal required test_* basenames exactly"
    )


def test_required_governance_files_are_lexicographically_sorted() -> None:
    relative_paths = [path.relative_to(REPO_ROOT).as_posix() for path in REQUIRED_E2E_GOVERNANCE_FILES]
    assert relative_paths == sorted(relative_paths), (
        "REQUIRED_E2E_GOVERNANCE_FILES must be lexicographically sorted by relative path"
    )


def test_required_governance_files_follow_allowed_filename_policy() -> None:
    relative_paths = [path.relative_to(REPO_ROOT).as_posix() for path in REQUIRED_E2E_GOVERNANCE_FILES]
    assert relative_paths, "REQUIRED_E2E_GOVERNANCE_FILES must not be empty"

    allowed_helper_files = {"tests/e2e/cli_runner_compat.py"}
    invalid = [
        path for path in relative_paths if path not in allowed_helper_files and not Path(path).name.startswith("test_")
    ]
    assert not invalid, "REQUIRED_E2E_GOVERNANCE_FILES contains unsupported non-test helper entries: " + ", ".join(
        invalid
    )
