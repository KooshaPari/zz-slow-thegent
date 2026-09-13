"""Govern command snippet uniqueness and full-bundle path coverage checks."""

from __future__ import annotations

import hashlib
import re
import shlex
from collections import Counter
from pathlib import Path

from tests.e2e import test_split_hygiene

README_PATH = Path(__file__).with_name("README.md")

FULL_E2E_GOVERNANCE_TEST_PATHS = (
    "tests/e2e/test_split_hygiene.py",
    "tests/e2e/test_readme_e2e_commands.py",
    "tests/e2e/test_readme_row_order_contract.py",
    "tests/e2e/test_readme_row_file_bijection.py",
    "tests/e2e/test_readme_command_uniqueness.py",
    "tests/e2e/test_readme_command_normalized_duplicates.py",
    "tests/e2e/test_readme_bundle_order_contract.py",
    "tests/e2e/test_readme_collect_only_commands.py",
    "tests/e2e/test_readme_direct_command_token_sanitizer.py",
    "tests/e2e/test_governance_sync_contracts.py",
    "tests/e2e/test_governance_registry_order.py",
    "tests/e2e/test_governance_health_artifact.py",
    "tests/e2e/test_governance_artifact_schema_policy.py",
    "tests/e2e/test_governance_inventory_artifact.py",
    "tests/e2e/test_governance_set_equality.py",
    "tests/e2e/test_governance_delta_report.py",
    "tests/e2e/test_cli_alias_rewrite_contract.py",
    "tests/e2e/test_cli_alias_rewrite_real_app.py",
    "tests/e2e/test_cli_alias_unsupported_rationale.py",
    "tests/e2e/test_unsupported_alias_real_app_evidence.py",
    "tests/e2e/test_real_app_command_families.py",
    "tests/e2e/test_real_app_help_anchor_contract.py",
    "tests/e2e/test_top_level_command_snapshot_contract.py",
    "tests/e2e/test_cli_runner_compat.py",
    "tests/e2e/test_cli_runner_extracts.py",
    "tests/e2e/test_cli_runner_rewrite_guards.py",
    "tests/e2e/test_cli_runner_skip_message_contract.py",
    "tests/e2e/test_cli_runner_skip_prefix_contract.py",
    "tests/e2e/test_cli_runner_unicode_tokens.py",
    "tests/e2e/test_cli_runner_import_governance.py",
    "tests/e2e/test_helper_governance_loophole_contract.py",
    "tests/e2e/test_command_surface.py",
    "tests/e2e/test_e2e_module_pairing.py",
    "tests/e2e/test_smoke_runner_governance.py",
    "tests/e2e/test_split_marker_placement_consistency.py",
    "tests/e2e/test_split_marker_governance.py",
)

EXPECTED_FULL_BUNDLE_PATH_SEQUENCE_SHA256 = "c52b1c79bae49e175c08bd8981ceef0159dd60d9ff1b0a7fd0c9b6a1c51cf12e"

ALLOWED_FULL_BUNDLE_PATH_PREFIX_FAMILIES = (
    "test_cli_",
    "test_command_",
    "test_e2e_",
    "test_governance_",
    "test_helper_",
    "test_readme_",
    "test_real_",
    "test_smoke_",
    "test_split_",
    "test_top_",
    "test_unsupported_",
)


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _backticked_pytest_or_task_snippets(text: str) -> list[str]:
    snippets = [snippet.strip() for snippet in re.findall(r"`([^`]+)`", text)]
    command_snippets: list[str] = []
    for snippet in snippets:
        tokens = shlex.split(snippet)
        if not tokens:
            continue
        if tokens[0] in {"pytest", "task"}:
            command_snippets.append(snippet)
    return command_snippets


def _full_bundle_command_snippet(text: str) -> str:
    match = re.search(
        r"\|\s*Full e2e governance unit bundle \(direct\)\s*\|\s*`([^`]+)`\s*\|",
        text,
    )
    assert match, "README must contain the full governance unit bundle row"
    return match.group(1)


def _test_path_tokens(snippet: str) -> list[str]:
    return [token for token in shlex.split(snippet) if token.startswith("tests/") and token.endswith(".py")]


def _command_table_rows(text: str) -> list[tuple[str, str]]:
    return [
        (goal.strip(), snippet.strip()) for goal, snippet in re.findall(r"\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|", text)
    ]


def test_no_duplicate_backticked_pytest_or_task_command_snippets() -> None:
    snippets = _backticked_pytest_or_task_snippets(_readme_text())
    assert snippets, "README should include at least one backticked pytest/task command snippet"

    counts = Counter(snippets)
    duplicates = [snippet for snippet, count in counts.items() if count > 1]
    assert not duplicates, "README should not duplicate exact pytest/task snippets: " + "; ".join(duplicates)


def test_full_bundle_row_contains_each_governance_test_exactly_once() -> None:
    snippet = _full_bundle_command_snippet(_readme_text())
    path_tokens = _test_path_tokens(snippet)
    counts = Counter(path_tokens)

    duplicate_paths = [path for path, count in counts.items() if count > 1]
    assert not duplicate_paths, "Full bundle command should not repeat test paths: " + ", ".join(duplicate_paths)

    missing_paths = [path for path in FULL_E2E_GOVERNANCE_TEST_PATHS if counts[path] != 1]
    assert not missing_paths, "Full bundle command must include each governance test exactly once: " + ", ".join(
        missing_paths
    )

    unexpected_paths = [path for path in path_tokens if path not in FULL_E2E_GOVERNANCE_TEST_PATHS]
    assert not unexpected_paths, "Full bundle command contains unexpected test paths: " + ", ".join(unexpected_paths)


def test_full_bundle_readme_and_split_hygiene_path_sequences_match_exactly() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    split_hygiene_paths = _test_path_tokens(test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
    assert readme_paths == split_hygiene_paths, (
        "README full bundle path sequence must match test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND exactly"
    )


def test_full_bundle_first_and_last_path_sentinels_are_stable() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    assert readme_paths, "README full bundle command must include at least one path token"
    assert readme_paths[0] == "tests/e2e/test_cli_alias_rewrite_contract.py", (
        "README full bundle command must start with test_cli_alias_rewrite_contract.py"
    )
    assert readme_paths[-1] == "tests/e2e/test_unsupported_alias_real_app_evidence.py", (
        "README full bundle command must end with test_unsupported_alias_real_app_evidence.py"
    )


def test_full_bundle_path_count_matches_required_governance_test_entries() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    required_test_entry_count = sum(
        1 for path in test_split_hygiene.REQUIRED_E2E_GOVERNANCE_FILES if path.name.startswith("test_")
    )
    assert len(readme_paths) == required_test_entry_count, (
        "README full bundle path count must match the number of test_* entries in "
        "test_split_hygiene.REQUIRED_E2E_GOVERNANCE_FILES"
    )


def test_full_bundle_readme_path_sequence_is_lexicographically_sorted() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    assert readme_paths == sorted(readme_paths), "README full bundle path sequence must be lexicographically sorted"


def test_full_bundle_path_list_matches_full_governance_tuple_membership_exactly() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    assert set(readme_paths) == set(FULL_E2E_GOVERNANCE_TEST_PATHS), (
        "README full bundle path set must exactly match FULL_E2E_GOVERNANCE_TEST_PATHS membership"
    )


def test_full_bundle_includes_alias_trio_in_canonical_adjacent_order() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    alias_trio = (
        "tests/e2e/test_cli_alias_rewrite_contract.py",
        "tests/e2e/test_cli_alias_rewrite_real_app.py",
        "tests/e2e/test_cli_alias_unsupported_rationale.py",
    )
    counts = Counter(readme_paths)
    missing_or_duplicate = [path for path in alias_trio if counts[path] != 1]
    assert not missing_or_duplicate, "README full bundle must include each alias trio path exactly once: " + ", ".join(
        missing_or_duplicate
    )

    start_idx = readme_paths.index(alias_trio[0])
    assert tuple(readme_paths[start_idx : start_idx + len(alias_trio)]) == alias_trio, (
        "README full bundle must include alias trio paths in canonical adjacent order"
    )


def test_full_bundle_row_has_no_duplicate_non_path_tokens_excluding_initial_pytest_q() -> None:
    tokens = shlex.split(_full_bundle_command_snippet(_readme_text()))
    assert tokens[:2] == ["pytest", "-q"], "README full bundle command must begin with `pytest -q`"

    non_path_tokens = [token for token in tokens if not (token.startswith("tests/") and token.endswith(".py"))]
    duplicate_non_path_tokens = [token for token, count in Counter(non_path_tokens[2:]).items() if count > 1]
    assert not duplicate_non_path_tokens, (
        "README full bundle command must not repeat non-path tokens after `pytest -q`: "
        + ", ".join(duplicate_non_path_tokens)
    )


def test_full_bundle_row_has_no_trailing_non_path_tokens_after_first_path() -> None:
    tokens = shlex.split(_full_bundle_command_snippet(_readme_text()))
    first_path_index = next(
        (idx for idx, token in enumerate(tokens) if token.startswith("tests/") and token.endswith(".py")),
        None,
    )
    assert first_path_index is not None, "README full bundle command must include at least one test path token"

    trailing_non_path_tokens = [
        token for token in tokens[first_path_index + 1 :] if not (token.startswith("tests/") and token.endswith(".py"))
    ]
    assert not trailing_non_path_tokens, (
        "README full bundle command must not include non-path tokens after the first test path token: "
        + ", ".join(trailing_non_path_tokens)
    )


def test_full_bundle_path_list_equals_sorted_unique_list_and_expected_count() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    sorted_unique_paths = sorted(set(readme_paths))
    assert readme_paths == sorted_unique_paths, (
        "README full bundle path list must equal its lexicographically sorted unique path list"
    )
    assert len(readme_paths) == len(FULL_E2E_GOVERNANCE_TEST_PATHS), (
        "README full bundle path list length must match FULL_E2E_GOVERNANCE_TEST_PATHS expected count"
    )


def test_readme_full_bundle_includes_single_file_direct_rows_exactly_once() -> None:
    text = _readme_text()
    bundle_counts = Counter(_test_path_tokens(_full_bundle_command_snippet(text)))

    direct_single_file_paths: list[str] = []
    for goal, command in _command_table_rows(text):
        if not goal.endswith("(direct)") or "bundle" in goal.lower():
            continue
        tokens = shlex.split(command)
        if tokens[:2] != ["pytest", "-q"]:
            continue
        path_tokens = _test_path_tokens(command)
        if len(path_tokens) == 1:
            direct_single_file_paths.append(path_tokens[0])

    assert direct_single_file_paths, "README should contain direct single-file governance rows"

    missing_or_duplicate = [path for path in direct_single_file_paths if bundle_counts[path] != 1]
    assert not missing_or_duplicate, (
        "README full bundle path list must include each direct single-file row path exactly once: "
        + ", ".join(missing_or_duplicate)
    )


def test_full_bundle_command_has_no_duplicated_path_basenames() -> None:
    path_tokens = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    basename_counts = Counter(Path(path).name for path in path_tokens)
    duplicate_basenames = [name for name, count in basename_counts.items() if count > 1]
    assert not duplicate_basenames, "README full bundle command must not duplicate test path basenames: " + ", ".join(
        sorted(duplicate_basenames)
    )


def test_full_bundle_row_and_split_constant_share_path_count_and_basename_multiset() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    split_paths = _test_path_tokens(test_split_hygiene.REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND)
    assert len(readme_paths) == len(split_paths), (
        "README full bundle row and split hygiene constant must have identical path counts"
    )
    assert Counter(Path(path).name for path in readme_paths) == Counter(Path(path).name for path in split_paths), (
        "README full bundle row and split hygiene constant must share identical path basename multisets"
    )


def test_full_bundle_path_basenames_are_globally_unique() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    readme_basenames = [Path(path).name for path in readme_paths]
    duplicate_basenames = sorted(basename for basename, count in Counter(readme_basenames).items() if count > 1)
    assert len(readme_basenames) == len(set(readme_basenames)), (
        "README full bundle path basenames must be globally unique; duplicates: " + ", ".join(duplicate_basenames)
    )


def test_full_bundle_contains_no_paths_outside_full_governance_tuple() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    unexpected_paths = sorted(set(readme_paths) - set(FULL_E2E_GOVERNANCE_TEST_PATHS))
    assert not unexpected_paths, (
        "README full bundle command must not include paths outside FULL_E2E_GOVERNANCE_TEST_PATHS: "
        + ", ".join(unexpected_paths)
    )


def test_full_bundle_alias_trio_appears_once_each_in_increasing_index_order() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    alias_trio = (
        "tests/e2e/test_cli_alias_rewrite_contract.py",
        "tests/e2e/test_cli_alias_rewrite_real_app.py",
        "tests/e2e/test_cli_alias_unsupported_rationale.py",
    )
    counts = Counter(readme_paths)
    missing_or_duplicate = [path for path in alias_trio if counts[path] != 1]
    assert not missing_or_duplicate, "README full bundle must include each alias trio path exactly once: " + ", ".join(
        missing_or_duplicate
    )

    alias_indices = [readme_paths.index(path) for path in alias_trio]
    assert alias_indices == sorted(alias_indices), (
        "README full bundle must list alias trio paths in increasing index order"
    )


def test_full_bundle_path_sequence_sha256_snapshot_is_stable() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    sequence_hash = hashlib.sha256("\n".join(readme_paths).encode("utf-8")).hexdigest()
    assert sequence_hash == EXPECTED_FULL_BUNDLE_PATH_SEQUENCE_SHA256, (
        "README full bundle path sequence hash changed.\n"
        f"Expected: {EXPECTED_FULL_BUNDLE_PATH_SEQUENCE_SHA256}\n"
        f"Actual:   {sequence_hash}\n"
        "Update guidance: if this order change is intentional, verify the full path sequence and then update "
        "`EXPECTED_FULL_BUNDLE_PATH_SEQUENCE_SHA256` in tests/e2e/test_readme_command_uniqueness.py."
    )


def test_full_bundle_paths_use_only_allowlisted_prefix_families() -> None:
    readme_paths = _test_path_tokens(_full_bundle_command_snippet(_readme_text()))
    invalid_paths = [
        path
        for path in readme_paths
        if not any(Path(path).name.startswith(prefix) for prefix in ALLOWED_FULL_BUNDLE_PATH_PREFIX_FAMILIES)
    ]
    assert not invalid_paths, (
        "README full bundle contains paths outside the allowlisted filename prefix families. "
        f"Allowed prefixes: {', '.join(ALLOWED_FULL_BUNDLE_PATH_PREFIX_FAMILIES)}. "
        f"Invalid paths: {', '.join(invalid_paths)}"
    )
