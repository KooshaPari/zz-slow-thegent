"""Sync contracts for e2e governance file and command declarations."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from tests.e2e import test_split_hygiene

GOVERNANCE_HELPER_NAME_PARTS = (
    "governance",
    "split_hygiene",
    "readme",
    "cli_runner",
    "command_surface",
    "alias_rewrite",
    "alias",
    "module_pairing",
)
FORBIDDEN_DIRECT_HELPER_MODULE_PATHS = {
    "tests/e2e/cli_runner_compat.py",
    "tests/e2e/cli_assertions.py",
    "tests/e2e/command_surface.py",
}
COMMAND_SURFACE_DIRECT_TRIO_PATHS = {
    "tests/e2e/test_command_surface.py",
    "tests/e2e/test_real_app_command_families.py",
    "tests/e2e/test_real_app_help_anchor_contract.py",
}
ALIAS_DIRECT_TRIO_PATHS = {
    "tests/e2e/test_cli_alias_rewrite_contract.py",
    "tests/e2e/test_cli_alias_rewrite_real_app.py",
    "tests/e2e/test_cli_alias_unsupported_rationale.py",
}
ALIAS_DIRECT_TRIO_GOALS = {
    "Alias rewrite contract unit (direct)": "tests/e2e/test_cli_alias_rewrite_contract.py",
    "Alias rewrite real-app contract unit (direct)": "tests/e2e/test_cli_alias_rewrite_real_app.py",
    "Alias unsupported rationale contract (direct)": "tests/e2e/test_cli_alias_unsupported_rationale.py",
}
SPLIT_HYGIENE_README_CORE_PATHS = {
    "tests/e2e/test_split_hygiene.py",
    "tests/e2e/test_readme_e2e_commands.py",
}


def _e2e_governance_helper_tests() -> set[Path]:
    e2e_dir = Path(__file__).resolve().parent
    return {
        path.resolve()
        for path in e2e_dir.iterdir()
        if path.is_file()
        and path.name.startswith("test_")
        and path.suffix == ".py"
        and any(part in path.name for part in GOVERNANCE_HELPER_NAME_PARTS)
    }


def _required_governance_files() -> set[Path]:
    return {path.resolve() for path in test_split_hygiene.REQUIRED_E2E_GOVERNANCE_FILES}


def _relative(path: Path) -> str:
    return str(path.resolve().relative_to(test_split_hygiene.REPO_ROOT))


def _bundle_command_paths() -> set[str]:
    tokens = shlex.split(test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
    return {token for token in tokens if token.startswith("tests/") and token.endswith(".py")}


def _readme_direct_pytest_paths() -> set[str]:
    text = test_split_hygiene.E2E_README.read_text(encoding="utf-8")
    table_row_pattern = re.compile(
        r"^\|\s*[^|]*\(direct\)\s*\|\s*`([^`]+)`\s*\|$",
        flags=re.MULTILINE,
    )
    command_snippets = [match.group(1) for match in table_row_pattern.finditer(text)]
    direct_paths: set[str] = set()

    for snippet in command_snippets:
        paths = [token for token in shlex.split(snippet) if token.startswith("tests/") and token.endswith(".py")]
        if len(paths) == 1:
            direct_paths.add(paths[0])

    return direct_paths


def _readme_direct_row_paths() -> set[str]:
    text = test_split_hygiene.E2E_README.read_text(encoding="utf-8")
    table_row_pattern = re.compile(
        r"^\|\s*[^|]*\(direct\)\s*\|\s*`([^`]+)`\s*\|$",
        flags=re.MULTILINE,
    )
    direct_row_paths: set[str] = set()

    for match in table_row_pattern.finditer(text):
        command = match.group(1)
        direct_row_paths.update(
            token for token in shlex.split(command) if token.startswith("tests/e2e/") and token.endswith(".py")
        )

    return direct_row_paths


def _readme_non_direct_row_paths() -> set[str]:
    text = test_split_hygiene.E2E_README.read_text(encoding="utf-8")
    table_row_pattern = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|$",
        flags=re.MULTILINE,
    )
    non_direct_paths: set[str] = set()

    for goal, command in table_row_pattern.findall(text):
        if "(direct)" in goal:
            continue
        non_direct_paths.update(
            token for token in shlex.split(command) if token.startswith("tests/e2e/") and token.endswith(".py")
        )

    return non_direct_paths


def _readme_direct_non_bundle_row_path_counts() -> dict[str, int]:
    text = test_split_hygiene.E2E_README.read_text(encoding="utf-8")
    table_row_pattern = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|$",
        flags=re.MULTILINE,
    )
    path_counts: dict[str, int] = {}

    for goal, command in table_row_pattern.findall(text):
        if "(direct)" not in goal:
            continue
        if "bundle" in goal.lower():
            continue

        for token in shlex.split(command):
            if token.startswith("tests/e2e/") and token.endswith(".py"):
                path_counts[token] = path_counts.get(token, 0) + 1

    return path_counts


def _readme_table_goal_command_pairs() -> list[tuple[str, str]]:
    text = test_split_hygiene.E2E_README.read_text(encoding="utf-8")
    table_row_pattern = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|$",
        flags=re.MULTILINE,
    )
    return [(goal.strip(), command.strip()) for goal, command in table_row_pattern.findall(text)]


def test_governance_helper_files_are_represented_in_required_list() -> None:
    discovered_files = _e2e_governance_helper_tests()
    required_files = _required_governance_files()

    missing = sorted(discovered_files - required_files)

    assert not missing, "governance helper e2e tests missing from REQUIRED_E2E_GOVERNANCE_FILES: " + ", ".join(
        _relative(path) for path in missing
    )


def test_governance_bundle_command_paths_exist_and_match_required_set() -> None:
    tokens = shlex.split(test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
    path_tokens = [token for token in tokens if token.startswith("tests/") and token.endswith(".py")]
    command_paths = {test_split_hygiene.REPO_ROOT / token for token in path_tokens}

    missing_on_disk = sorted(path for path in command_paths if not path.exists())
    assert not missing_on_disk, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND references missing paths: " + ", ".join(
        _relative(path) for path in missing_on_disk
    )

    allowed_paths = _required_governance_files() | {Path(test_split_hygiene.__file__).resolve()}
    unexpected = sorted(path.resolve() for path in command_paths - allowed_paths)
    assert not unexpected, (
        "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND includes paths outside "
        "REQUIRED_E2E_GOVERNANCE_FILES + tests/e2e/test_split_hygiene.py: "
        + ", ".join(_relative(path) for path in unexpected)
    )


def test_readme_direct_pytest_paths_are_registered_governance_tests() -> None:
    required_tests = {
        str(path.relative_to(test_split_hygiene.REPO_ROOT))
        for path in _required_governance_files()
        if path.name.startswith("test_")
    }
    direct_paths = _readme_direct_pytest_paths()
    unexpected = sorted(direct_paths - required_tests)

    assert not unexpected, (
        "README direct governance rows reference tests not registered in "
        "REQUIRED_E2E_GOVERNANCE_FILES: " + ", ".join(unexpected)
    )


def test_bundle_only_contract_paths_remain_bundle_only() -> None:
    bundle_only_paths = {
        "tests/e2e/test_governance_registry_order.py",
        "tests/e2e/test_governance_artifact_schema_policy.py",
        "tests/e2e/test_governance_delta_report.py",
        "tests/e2e/test_readme_row_file_bijection.py",
        "tests/e2e/test_readme_direct_command_token_sanitizer.py",
        "tests/e2e/test_top_level_command_snapshot_contract.py",
        "tests/e2e/test_split_marker_placement_consistency.py",
    }
    required_tests = {
        str(path.relative_to(test_split_hygiene.REPO_ROOT))
        for path in _required_governance_files()
        if path.name.startswith("test_")
    }
    bundle_paths = _bundle_command_paths()
    direct_paths = _readme_direct_pytest_paths()

    assert bundle_only_paths <= required_tests, (
        "bundle-only contract tests must be tracked in REQUIRED_E2E_GOVERNANCE_FILES: "
        + ", ".join(sorted(bundle_only_paths - required_tests))
    )
    assert bundle_only_paths <= bundle_paths, (
        "bundle-only contract tests must stay in REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND: "
        + ", ".join(sorted(bundle_only_paths - bundle_paths))
    )
    assert bundle_only_paths.isdisjoint(direct_paths), (
        "bundle-only contract tests should not appear as README direct rows: "
        + ", ".join(sorted(bundle_only_paths & direct_paths))
    )


def test_readme_direct_rows_do_not_reference_helper_modules() -> None:
    direct_paths = _readme_direct_pytest_paths()
    forbidden = sorted(direct_paths & FORBIDDEN_DIRECT_HELPER_MODULE_PATHS)
    assert not forbidden, "README direct governance rows must not reference helper modules: " + ", ".join(forbidden)


def test_readme_direct_rows_include_command_surface_contract_trio() -> None:
    direct_paths = _readme_direct_pytest_paths()
    missing = sorted(COMMAND_SURFACE_DIRECT_TRIO_PATHS - direct_paths)
    assert not missing, "README direct governance rows missing command-surface contract trio: " + ", ".join(missing)


def test_fast_governance_readme_paths_are_strict_subset_of_full_bundle() -> None:
    fast_governance_paths = _readme_direct_pytest_paths()
    full_bundle_paths = _bundle_command_paths()
    assert fast_governance_paths < full_bundle_paths, (
        "README fast-governance direct pytest paths must be a strict subset of "
        "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND paths"
    )


def test_full_bundle_references_split_hygiene_once() -> None:
    tokens = shlex.split(test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
    split_hygiene_relpath = "tests/e2e/test_split_hygiene.py"
    assert tokens.count(split_hygiene_relpath) == 1, (
        "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include tests/e2e/test_split_hygiene.py exactly once"
    )


def test_readme_direct_rows_referenced_files_are_subset_of_required_governance_test_modules() -> None:
    required_test_modules = {
        str(path.relative_to(test_split_hygiene.REPO_ROOT))
        for path in _required_governance_files()
        if path.name.startswith("test_")
    }
    direct_row_paths = _readme_direct_row_paths()
    unexpected = sorted(direct_row_paths - required_test_modules)

    assert not unexpected, (
        "README direct rows reference files outside REQUIRED_E2E_GOVERNANCE_FILES test modules: "
        + ", ".join(unexpected)
    )


def test_readme_full_bundle_row_includes_readme_e2e_commands_contract() -> None:
    text = test_split_hygiene.E2E_README.read_text(encoding="utf-8")
    row_pattern = re.compile(
        r"^\|\s*Full e2e governance unit bundle \(direct\)\s*\|\s*`([^`]+)`\s*\|$",
        flags=re.MULTILINE,
    )
    match = row_pattern.search(text)
    assert match is not None, "README missing Full e2e governance unit bundle (direct) row"

    bundle_paths = {
        token for token in shlex.split(match.group(1)) if token.startswith("tests/e2e/") and token.endswith(".py")
    }
    required_path = "tests/e2e/test_readme_e2e_commands.py"
    assert required_path in bundle_paths, (
        "README full e2e governance unit bundle row must include tests/e2e/test_readme_e2e_commands.py"
    )


def test_readme_non_direct_rows_do_not_reference_cli_runner_compat_helper_module() -> None:
    non_direct_paths = _readme_non_direct_row_paths()
    forbidden_path = "tests/e2e/cli_runner_compat.py"
    assert forbidden_path not in non_direct_paths, (
        "README non-direct governance rows must not reference helper module: " + forbidden_path
    )


def test_readme_direct_non_bundle_rows_include_alias_and_command_surface_trios_once_by_path() -> None:
    path_counts = _readme_direct_non_bundle_row_path_counts()
    required_once_paths = ALIAS_DIRECT_TRIO_PATHS | COMMAND_SURFACE_DIRECT_TRIO_PATHS
    missing = sorted(path for path in required_once_paths if path_counts.get(path, 0) == 0)
    duplicated = sorted(path for path in required_once_paths if path_counts.get(path, 0) > 1)

    assert not missing, (
        "README direct non-bundle governance rows missing alias/command-surface trio paths: " + ", ".join(missing)
    )
    assert not duplicated, (
        "README direct non-bundle governance rows must reference alias/command-surface trio "
        "paths exactly once each: " + ", ".join(duplicated)
    )


def test_readme_full_bundle_command_tokens_match_required_bundle_tokens_when_normalized() -> None:
    goal_command_pairs = _readme_table_goal_command_pairs()
    full_bundle_goal = "Full e2e governance unit bundle (direct)"
    readme_full_bundle_command = next(
        (command for goal, command in goal_command_pairs if goal == full_bundle_goal),
        None,
    )
    assert readme_full_bundle_command is not None, "README missing Full e2e governance unit bundle (direct) row"

    normalized_readme_tokens = tuple(shlex.split(readme_full_bundle_command))
    normalized_required_tokens = tuple(shlex.split(test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND))
    assert normalized_readme_tokens == normalized_required_tokens, (
        "README full-bundle command tokens must match REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND after normalization"
    )


def test_alias_direct_trio_goals_are_unique_and_map_to_single_direct_row_path() -> None:
    goal_command_pairs = _readme_table_goal_command_pairs()
    seen_goal_counts: dict[str, int] = {}
    goal_to_paths: dict[str, list[str]] = {}

    for goal, command in goal_command_pairs:
        if goal not in ALIAS_DIRECT_TRIO_GOALS:
            continue
        seen_goal_counts[goal] = seen_goal_counts.get(goal, 0) + 1
        goal_to_paths[goal] = [
            token for token in shlex.split(command) if token.startswith("tests/e2e/") and token.endswith(".py")
        ]

    missing = sorted(goal for goal in ALIAS_DIRECT_TRIO_GOALS if seen_goal_counts.get(goal, 0) == 0)
    duplicated = sorted(goal for goal, count in seen_goal_counts.items() if count > 1)
    assert not missing, "README missing alias direct goals: " + ", ".join(missing)
    assert not duplicated, "README alias direct goals must be unique: " + ", ".join(duplicated)

    wrong_path_counts = sorted(goal for goal, paths in goal_to_paths.items() if len(paths) != 1)
    assert not wrong_path_counts, (
        "README alias direct goals must map to exactly one direct-row test path: " + ", ".join(wrong_path_counts)
    )

    mismatched_paths = sorted(
        goal
        for goal, expected_path in ALIAS_DIRECT_TRIO_GOALS.items()
        if goal_to_paths.get(goal, [None])[0] != expected_path
    )
    assert not mismatched_paths, "README alias direct goal-to-path mapping mismatch for: " + ", ".join(mismatched_paths)


def test_non_direct_goals_do_not_use_direct_suffix() -> None:
    non_direct_goals = [goal for goal, _command in _readme_table_goal_command_pairs() if "(direct)" not in goal]
    assert non_direct_goals, "README command table must include non-direct goals"
    malformed = [goal for goal in non_direct_goals if goal.strip().endswith("(direct)")]
    assert not malformed, "README non-direct goals must not use '(direct)' suffix: " + ", ".join(malformed)


def test_direct_row_commands_are_shlex_roundtrip_token_stable() -> None:
    direct_commands = [command for goal, command in _readme_table_goal_command_pairs() if "(direct)" in goal]
    assert direct_commands, "README command table must include direct rows"

    unstable: list[str] = []
    for command in direct_commands:
        tokens = shlex.split(command)
        normalized = shlex.join(tokens)
        if shlex.split(normalized) != tokens:
            unstable.append(command)

    assert not unstable, "README direct-row commands must be stable under shlex roundtrip normalization: " + "; ".join(
        unstable
    )


def test_non_governance_non_direct_rows_exclude_governance_only_contract_paths() -> None:
    governance_only_paths = (
        ALIAS_DIRECT_TRIO_PATHS | COMMAND_SURFACE_DIRECT_TRIO_PATHS | SPLIT_HYGIENE_README_CORE_PATHS
    )
    goal_command_pairs = _readme_table_goal_command_pairs()
    non_governance_non_direct_rows = [
        (goal, command)
        for goal, command in goal_command_pairs
        if "(direct)" not in goal and "governance" not in goal.lower()
    ]
    assert non_governance_non_direct_rows, "README command table must include non-governance non-direct rows"

    referenced_paths: set[str] = set()
    for _goal, command in non_governance_non_direct_rows:
        referenced_paths.update(
            token for token in shlex.split(command) if token.startswith("tests/e2e/") and token.endswith(".py")
        )

    forbidden = sorted(referenced_paths & governance_only_paths)
    assert not forbidden, (
        "README non-governance non-direct rows must not reference governance-only paths: " + ", ".join(forbidden)
    )


def test_fast_governance_row_is_strict_set_and_cardinality_subset_of_full_bundle_with_unique_basenames() -> None:
    goal_command_pairs = _readme_table_goal_command_pairs()
    fast_goal = "Fast governance checks"
    full_goal = "Full e2e governance unit bundle (direct)"
    fast_command = next((command for goal, command in goal_command_pairs if goal == fast_goal), None)
    full_command = next((command for goal, command in goal_command_pairs if goal == full_goal), None)

    assert fast_command is not None, "README missing Fast governance checks row"
    assert full_command is not None, "README missing Full e2e governance unit bundle (direct) row"

    fast_paths = [
        token for token in shlex.split(fast_command) if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    full_paths = [
        token for token in shlex.split(full_command) if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    fast_set = set(fast_paths)
    full_set = set(full_paths)

    assert fast_set < full_set, (
        "README Fast governance checks row must be a strict path-set subset of "
        "the Full e2e governance unit bundle (direct) row"
    )
    assert len(fast_set) < len(full_set), (
        "README Fast governance checks row must have fewer unique test paths than "
        "the Full e2e governance unit bundle (direct) row"
    )

    fast_basenames = [Path(path).name for path in fast_paths]
    full_basenames = [Path(path).name for path in full_paths]
    assert len(fast_basenames) == len(set(fast_basenames)), (
        "README Fast governance checks row must not repeat test basenames"
    )
    assert len(full_basenames) == len(set(full_basenames)), (
        "README Full e2e governance unit bundle (direct) row must not repeat test basenames"
    )


def test_non_direct_rows_command_text_must_not_contain_direct_marker() -> None:
    goal_command_pairs = _readme_table_goal_command_pairs()
    non_direct_commands = [command for goal, command in goal_command_pairs if "(direct)" not in goal]
    assert non_direct_commands, "README command table must include non-direct rows"

    malformed = [command for command in non_direct_commands if "(direct)" in command]
    assert not malformed, "README non-direct row command text must not contain '(direct)': " + "; ".join(malformed)


def test_readme_and_split_bundle_path_edges_stay_synchronized() -> None:
    goal_command_pairs = _readme_table_goal_command_pairs()
    full_bundle_goal = "Full e2e governance unit bundle (direct)"
    readme_full_bundle_command = next(
        (command for goal, command in goal_command_pairs if goal == full_bundle_goal),
        None,
    )
    assert readme_full_bundle_command is not None, "README missing Full e2e governance unit bundle (direct) row"

    readme_paths = [
        token
        for token in shlex.split(readme_full_bundle_command)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    split_constant_paths = [
        token
        for token in shlex.split(test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert len(readme_paths) >= 10, "README full e2e governance unit bundle row must include at least 10 test paths"
    assert len(split_constant_paths) >= 10, "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND must include at least 10 test paths"

    assert readme_paths[:5] == split_constant_paths[:5], (
        "README and REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND first 5 bundle paths diverged: "
        f"{readme_paths[:5]} != {split_constant_paths[:5]}"
    )
    assert readme_paths[-5:] == split_constant_paths[-5:], (
        "README and REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND last 5 bundle paths diverged: "
        f"{readme_paths[-5:]} != {split_constant_paths[-5:]}"
    )


def test_non_direct_row_paths_are_disjoint_from_forbidden_direct_helper_modules() -> None:
    non_direct_paths = _readme_non_direct_row_paths()
    forbidden = sorted(non_direct_paths & FORBIDDEN_DIRECT_HELPER_MODULE_PATHS)
    assert not forbidden, (
        "README non-direct row path tokens must be disjoint from "
        "FORBIDDEN_DIRECT_HELPER_MODULE_PATHS: " + ", ".join(forbidden)
    )


def test_direct_non_bundle_rows_cover_command_surface_trio_exactly_once_by_path() -> None:
    path_counts = _readme_direct_non_bundle_row_path_counts()
    missing = sorted(path for path in COMMAND_SURFACE_DIRECT_TRIO_PATHS if path_counts.get(path, 0) == 0)
    duplicated = sorted(path for path in COMMAND_SURFACE_DIRECT_TRIO_PATHS if path_counts.get(path, 0) > 1)

    assert not missing, "README direct non-bundle rows missing command-surface trio paths: " + ", ".join(missing)
    assert not duplicated, (
        "README direct non-bundle rows must reference command-surface trio paths exactly once: " + ", ".join(duplicated)
    )


def test_direct_non_bundle_rows_cover_alias_trio_exactly_once_by_path() -> None:
    path_counts = _readme_direct_non_bundle_row_path_counts()
    missing = sorted(path for path in ALIAS_DIRECT_TRIO_PATHS if path_counts.get(path, 0) == 0)
    duplicated = sorted(path for path in ALIAS_DIRECT_TRIO_PATHS if path_counts.get(path, 0) > 1)

    assert not missing, "README direct non-bundle rows missing alias trio paths: " + ", ".join(missing)
    assert not duplicated, "README direct non-bundle rows must reference alias trio paths exactly once: " + ", ".join(
        duplicated
    )


def test_readme_full_bundle_command_text_matches_split_constant_after_whitespace_collapse() -> None:
    full_bundle_goal = "Full e2e governance unit bundle (direct)"
    readme_full_bundle_command = next(
        (command for goal, command in _readme_table_goal_command_pairs() if goal == full_bundle_goal),
        None,
    )
    assert readme_full_bundle_command is not None, "README missing Full e2e governance unit bundle (direct) row"

    def collapse(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    assert collapse(readme_full_bundle_command) == collapse(
        test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND
    ), (
        "README full-bundle command text must stay synchronized with "
        "REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND after whitespace collapse"
    )


def test_readme_governance_rows_do_not_reference_tests_outside_tests_e2e() -> None:
    governance_rows = [
        (goal, command)
        for goal, command in _readme_table_goal_command_pairs()
        if "governance" in goal.lower() and "(direct)" in goal
    ]
    assert governance_rows, "README command table must include governance rows"

    outside_paths: set[str] = set()
    for _goal, command in governance_rows:
        for token in shlex.split(command):
            if token.startswith("tests/") and token.endswith(".py"):
                if not token.startswith("tests/e2e/"):
                    outside_paths.add(token)

    assert not outside_paths, "README governance rows must not reference test paths outside tests/e2e/: " + ", ".join(
        sorted(outside_paths)
    )
