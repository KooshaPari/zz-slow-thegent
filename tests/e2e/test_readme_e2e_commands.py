"""Sanity checks for e2e README command guidance."""

# noqa: PT018
from __future__ import annotations

import re
import shlex
from collections import Counter
from pathlib import Path

README_PATH = Path(__file__).with_name("README.md")
REPO_ROOT = README_PATH.parents[2]


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _readme_test_paths_from_command_snippets(text: str) -> list[str]:
    command_snippets = [
        snippet for snippet in re.findall(r"`([^`]+)`", text) if "pytest" in snippet
    ]
    return sorted(
        {
            path
            for snippet in command_snippets
            for path in re.findall(r"(tests/[^\s`]+\.py)", snippet)
        }
    )


def _command_table_rows(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    in_table = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if in_table:
                break
            continue
        if not stripped.startswith("|"):
            if in_table:
                break
            continue

        parts = [part.strip() for part in stripped.split("|")[1:-1]]
        if len(parts) != 2:
            continue

        goal, command_cell = parts
        if goal in {"Goal", "---"}:
            in_table = True
            continue

        in_table = True
        rows.append((goal, command_cell))

    return rows


def test_readme_includes_fast_governance_command_pattern() -> None:
    text = _readme_text()

    assert "pytest -q" in text
    assert "tests/e2e/test_split_hygiene.py" in text
    assert "tests/e2e/test_readme_e2e_commands.py" in text
    assert "tests/e2e/test_cli_alias_rewrite_contract.py" in text


def test_readme_includes_full_governance_unit_bundle_row() -> None:
    text = _readme_text()

    assert "Full e2e governance unit bundle (direct)" in text
    assert "pytest -q" in text
    assert "tests/e2e/test_split_hygiene.py" in text
    assert "tests/e2e/test_readme_e2e_commands.py" in text
    assert "tests/e2e/test_readme_row_order_contract.py" in text
    assert "tests/e2e/test_readme_command_uniqueness.py" in text
    assert "tests/e2e/test_readme_command_normalized_duplicates.py" in text
    assert "tests/e2e/test_readme_bundle_order_contract.py" in text
    assert "tests/e2e/test_readme_collect_only_commands.py" in text
    assert "tests/e2e/test_governance_sync_contracts.py" in text
    assert "tests/e2e/test_governance_health_artifact.py" in text
    assert "tests/e2e/test_governance_inventory_artifact.py" in text
    assert "tests/e2e/test_governance_set_equality.py" in text
    assert "tests/e2e/test_cli_alias_rewrite_contract.py" in text
    assert "tests/e2e/test_cli_alias_rewrite_real_app.py" in text
    assert "tests/e2e/test_cli_alias_unsupported_rationale.py" in text
    assert "tests/e2e/test_real_app_command_families.py" in text
    assert "tests/e2e/test_real_app_help_anchor_contract.py" in text
    assert "tests/e2e/test_cli_runner_compat.py" in text
    assert "tests/e2e/test_cli_runner_extracts.py" in text
    assert "tests/e2e/test_cli_runner_rewrite_guards.py" in text
    assert "tests/e2e/test_cli_runner_skip_message_contract.py" in text
    assert "tests/e2e/test_cli_runner_skip_prefix_contract.py" in text
    assert "tests/e2e/test_cli_runner_unicode_tokens.py" in text
    assert "tests/e2e/test_cli_runner_import_governance.py" in text
    assert "tests/e2e/test_command_surface.py" in text
    assert "tests/e2e/test_e2e_module_pairing.py" in text
    assert "tests/e2e/test_smoke_runner_governance.py" in text
    assert "tests/e2e/test_split_marker_governance.py" in text


def test_readme_includes_split_e2e_suite_command_pattern() -> None:
    text = _readme_text()

    assert "pytest -q" in text
    assert "tests/test_e2e_cli_core_a.py" in text
    assert "tests/test_e2e_cli_core_b.py" in text
    assert "tests/test_e2e_cli_aliases.py" in text
    assert "tests/test_e2e_cli_overlays.py" in text
    assert "-m e2e" in text


def test_readme_includes_quality_run_command_pattern() -> None:
    text = _readme_text()

    assert "task quality" in text


def test_readme_includes_compat_cli_runner_rewrite_policy() -> None:
    text = _readme_text()

    assert "CompatCliRunner Rewrite Policy" in text
    assert "Exact alias path only" in text
    assert "Argumentful or optionful invocations are not rewritten." in text
    assert "tests skip." in text


def test_readme_includes_compat_cli_runner_troubleshooting_semantics() -> None:
    text = _readme_text()

    assert "CompatCliRunner Troubleshooting" in text
    assert "No such command" in text
    assert "No such option" in text
    assert "real failure" in text


def test_readme_includes_alias_rewrite_governance_invariants() -> None:
    text = _readme_text()

    assert "Alias Rewrite Governance Invariants" in text
    assert "Exact-path rewrite" in text
    assert "No duplicate old prefixes" in text
    assert "List/tuple-of-strings requirement" in text


def test_readme_includes_alias_rewrite_governance_command_example() -> None:
    text = _readme_text()

    assert "Alias rewrite governance tests" in text
    assert "pytest -q tests/test_e2e_cli_aliases.py -k rewrite" in text


def test_readme_includes_compat_cli_runner_command_example() -> None:
    text = _readme_text()

    assert "Compat unit suite (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_compat.py" in text


def test_readme_includes_direct_alias_rewrite_contract_command_example() -> None:
    text = _readme_text()

    assert "Alias rewrite contract unit (direct)" in text
    assert "pytest -q tests/e2e/test_cli_alias_rewrite_contract.py" in text


def test_readme_includes_direct_command_surface_command_example() -> None:
    text = _readme_text()

    assert "Command-surface unit (direct)" in text
    assert "pytest -q tests/e2e/test_command_surface.py" in text


def test_readme_includes_compat_helper_extract_rewrite_guard_suite_command_example() -> (
    None
):
    text = _readme_text()

    assert "Compat helper extract/rewrite guard suite (direct)" in text
    assert (
        "pytest -q tests/e2e/test_cli_runner_extracts.py tests/e2e/test_cli_runner_rewrite_guards.py"
        in text
    )


def test_readme_includes_utility_module_pairing_governance_command_example() -> None:
    text = _readme_text()

    assert "Utility module pairing governance (direct)" in text
    assert "pytest -q tests/e2e/test_e2e_module_pairing.py" in text


def test_readme_includes_alias_rewrite_real_app_contract_command_example() -> None:
    text = _readme_text()

    assert "Alias rewrite real-app contract unit (direct)" in text
    assert "pytest -q tests/e2e/test_cli_alias_rewrite_real_app.py" in text


def test_readme_includes_compat_skip_message_contract_command_example() -> None:
    text = _readme_text()

    assert "Compat skip-message contract suite (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_skip_message_contract.py" in text


def test_readme_includes_split_marker_governance_command_example() -> None:
    text = _readme_text()

    assert "Split marker governance (direct)" in text
    assert "pytest -q tests/e2e/test_split_marker_governance.py" in text


def test_readme_includes_collect_only_governance_command_example() -> None:
    text = _readme_text()

    assert "README direct e2e collect-only governance (direct)" in text
    assert "pytest -q tests/e2e/test_readme_collect_only_commands.py" in text


def test_readme_includes_readme_command_uniqueness_command_example() -> None:
    text = _readme_text()

    assert "README command uniqueness (direct)" in text
    assert "pytest -q tests/e2e/test_readme_command_uniqueness.py" in text


def test_readme_includes_readme_bundle_order_contract_command_example() -> None:
    text = _readme_text()

    assert "README bundle order contract (direct)" in text
    assert "pytest -q tests/e2e/test_readme_bundle_order_contract.py" in text


def test_readme_includes_readme_row_order_contract_command_example() -> None:
    text = _readme_text()

    assert "README row order contract (direct)" in text
    assert "pytest -q tests/e2e/test_readme_row_order_contract.py" in text


def test_readme_includes_governance_sync_contracts_command_example() -> None:
    text = _readme_text()

    assert "Governance sync contracts (direct)" in text
    assert "pytest -q tests/e2e/test_governance_sync_contracts.py" in text


def test_readme_includes_governance_health_artifact_command_example() -> None:
    text = _readme_text()

    assert "Governance health artifact (direct)" in text
    assert "pytest -q tests/e2e/test_governance_health_artifact.py" in text


def test_readme_includes_real_app_command_families_command_example() -> None:
    text = _readme_text()

    assert "Real-app command families contract (direct)" in text
    assert "pytest -q tests/e2e/test_real_app_command_families.py" in text


def test_readme_includes_compat_edge_token_suite_command_example() -> None:
    text = _readme_text()

    assert "Compat edge-token suite (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_unicode_tokens.py" in text


def test_readme_includes_compat_import_governance_command_example() -> None:
    text = _readme_text()

    assert "Compat import governance (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_import_governance.py" in text


def test_readme_includes_compat_skip_prefix_command_example() -> None:
    text = _readme_text()

    assert "Compat skip-prefix contract suite (direct)" in text
    assert "pytest -q tests/e2e/test_cli_runner_skip_prefix_contract.py" in text


def test_readme_includes_alias_unsupported_rationale_command_example() -> None:
    text = _readme_text()

    assert "Alias unsupported rationale contract (direct)" in text
    assert "pytest -q tests/e2e/test_cli_alias_unsupported_rationale.py" in text


def test_readme_includes_real_app_help_anchor_command_example() -> None:
    text = _readme_text()

    assert "Real-app help anchor contract (direct)" in text
    assert "pytest -q tests/e2e/test_real_app_help_anchor_contract.py" in text


def test_command_table_rows_use_backticked_pytest_or_task_commands() -> None:
    rows = _command_table_rows(_readme_text())
    assert rows, "README command matrix should include at least one command row"

    for goal, command_cell in rows:
        assert command_cell.startswith("`") and command_cell.endswith("`"), (
            f"README command table row '{goal}' must use a backticked command cell: {command_cell!r}"
        )

        command = command_cell[1:-1].strip()
        tokens = shlex.split(command)
        assert tokens, f"README command table row '{goal}' has an empty command"
        assert tokens[0] in {"pytest", "task"}, (
            f"README command table row '{goal}' must start with pytest/task, found: {tokens[0]!r}"
        )


def test_command_table_body_rows_have_exactly_two_columns() -> None:
    text = _readme_text()
    in_table = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if in_table:
                break
            continue
        if not stripped.startswith("|"):
            if in_table:
                break
            continue

        parts = [part.strip() for part in stripped.split("|")[1:-1]]
        if parts in (["Goal", "Command"], ["---", "---"]):
            in_table = True
            continue

        in_table = True
        assert len(parts) == 2, (
            f"README command table body rows must contain exactly 2 columns: {stripped!r}"
        )


def test_command_table_direct_goal_labels_are_unique() -> None:
    rows = _command_table_rows(_readme_text())
    direct_goals = [goal for goal, _command_cell in rows if goal.endswith("(direct)")]
    duplicates = sorted({goal for goal in direct_goals if direct_goals.count(goal) > 1})
    assert not duplicates, (
        "README command table direct goal labels must be unique; duplicates found: "
        + ", ".join(duplicates)
    )


def test_full_bundle_covers_all_direct_readme_e2e_pytest_paths() -> None:
    rows = _command_table_rows(_readme_text())
    full_bundle_goal = "Full e2e governance unit bundle (direct)"
    full_bundle_row = [
        command_cell for goal, command_cell in rows if goal == full_bundle_goal
    ]
    assert full_bundle_row, (
        f"README command table must include '{full_bundle_goal}' row"
    )

    full_bundle_tokens = shlex.split(full_bundle_row[0][1:-1].strip())
    bundle_paths = {
        token
        for token in full_bundle_tokens
        if token.startswith("tests/e2e/") and token.endswith(".py")
    }
    assert bundle_paths, "Full governance bundle must include tests/e2e paths"

    direct_row_paths: set[str] = set()
    for goal, command_cell in rows:
        if goal == full_bundle_goal:
            continue
        if not goal.endswith("(direct)"):
            continue
        if not (command_cell.startswith("`") and command_cell.endswith("`")):
            continue

        tokens = shlex.split(command_cell[1:-1].strip())
        if tokens[:2] != ["pytest", "-q"]:
            continue

        path_tokens = [
            token
            for token in tokens[2:]
            if token.startswith("tests/e2e/") and token.endswith(".py")
        ]
        if len(path_tokens) != len(tokens[2:]):
            continue
        direct_row_paths.update(path_tokens)

    assert direct_row_paths, (
        "README should include direct pytest rows with tests/e2e paths"
    )

    missing_paths = sorted(
        path for path in direct_row_paths if path not in bundle_paths
    )
    assert not missing_paths, (
        "Full governance bundle should include every tests/e2e path referenced by direct README pytest rows: "
        + ", ".join(missing_paths)
    )


def test_fast_governance_row_includes_split_hygiene_path() -> None:
    rows = _command_table_rows(_readme_text())
    fast_row = [
        command_cell for goal, command_cell in rows if goal == "Fast governance checks"
    ]
    assert fast_row, "README command table must include 'Fast governance checks' row"

    tokens = shlex.split(fast_row[0][1:-1].strip())
    path_tokens = [
        token
        for token in tokens
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert "tests/e2e/test_split_hygiene.py" in path_tokens, (
        "Fast governance checks row must include tests/e2e/test_split_hygiene.py"
    )


def test_fast_governance_row_tests_e2e_paths_have_no_duplicates() -> None:
    rows = _command_table_rows(_readme_text())
    fast_row = [
        command_cell for goal, command_cell in rows if goal == "Fast governance checks"
    ]
    assert fast_row, "README command table must include 'Fast governance checks' row"

    tokens = shlex.split(fast_row[0][1:-1].strip())
    path_tokens = [
        token
        for token in tokens
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_tokens, "Fast governance checks row must include tests/e2e paths"

    duplicates = sorted({path for path in path_tokens if path_tokens.count(path) > 1})
    assert not duplicates, (
        "Fast governance checks row must not repeat tests/e2e paths; duplicates found: "
        + ", ".join(duplicates)
    )


def test_fast_governance_row_path_sequence_matches_canonical_mini_sequence() -> None:
    rows = _command_table_rows(_readme_text())
    fast_row = [
        command_cell for goal, command_cell in rows if goal == "Fast governance checks"
    ]
    assert fast_row, "README command table must include 'Fast governance checks' row"

    tokens = shlex.split(fast_row[0][1:-1].strip())
    path_tokens = [
        token
        for token in tokens
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert path_tokens, "Fast governance checks row must include tests/e2e paths"

    assert path_tokens == [
        "tests/e2e/test_split_hygiene.py",
        "tests/e2e/test_readme_e2e_commands.py",
        "tests/e2e/test_cli_alias_rewrite_contract.py",
    ], (
        "Fast governance checks row tests/e2e path sequence must match canonical mini-sequence: "
        "tests/e2e/test_split_hygiene.py, tests/e2e/test_readme_e2e_commands.py, "
        "tests/e2e/test_cli_alias_rewrite_contract.py"
    )


def test_fast_governance_row_starts_pytest_q_and_has_exactly_three_e2e_test_paths() -> (
    None
):
    rows = _command_table_rows(_readme_text())
    fast_row = [
        command_cell for goal, command_cell in rows if goal == "Fast governance checks"
    ]
    assert fast_row, "README command table must include 'Fast governance checks' row"

    tokens = shlex.split(fast_row[0][1:-1].strip())
    assert tokens[:2] == ["pytest", "-q"], (
        "Fast governance checks row must start with 'pytest -q'"
    )

    pattern = re.compile(r"^tests/e2e/test_[^\s`]+\.py$")
    path_tokens = [token for token in tokens[2:] if pattern.match(token)]
    assert len(path_tokens) == 3, (
        "Fast governance checks row must include exactly 3 tests/e2e/test_*.py paths"
    )


def test_fast_governance_paths_are_ordered_strict_prefix_of_full_bundle_paths() -> None:
    rows = _command_table_rows(_readme_text())
    fast_goal = "Fast governance checks"
    full_bundle_goal = "Full e2e governance unit bundle (direct)"

    fast_row = [command_cell for goal, command_cell in rows if goal == fast_goal]
    assert fast_row, f"README command table must include '{fast_goal}' row"
    full_bundle_row = [
        command_cell for goal, command_cell in rows if goal == full_bundle_goal
    ]
    assert full_bundle_row, (
        f"README command table must include '{full_bundle_goal}' row"
    )

    pattern = re.compile(r"^tests/e2e/test_[^\s`]+\.py$")
    fast_paths = [
        token
        for token in shlex.split(fast_row[0][1:-1].strip())
        if pattern.match(token)
    ]
    full_bundle_paths = [
        token
        for token in shlex.split(full_bundle_row[0][1:-1].strip())
        if pattern.match(token)
    ]

    assert fast_paths, (
        "Fast governance checks row must include tests/e2e/test_*.py paths"
    )
    assert full_bundle_paths, (
        "Full governance bundle row must include tests/e2e/test_*.py paths"
    )
    assert len(set(fast_paths)) == len(fast_paths), (
        "Fast governance checks row path list must not include duplicate tests/e2e/test_*.py paths"
    )
    assert len(fast_paths) < len(full_bundle_paths), (
        "Fast governance checks row path list must be a strict subset (shorter than full bundle path list)"
    )
    assert all(path in set(full_bundle_paths) for path in fast_paths), (
        "Fast governance checks row path list must be a subset of full bundle path list"
    )


def test_governance_command_table_rows_have_valid_markdown_two_cell_shape() -> None:
    text = _readme_text()
    lines = text.splitlines()

    table_start = next(
        (idx for idx, line in enumerate(lines) if line.strip() == "| Goal | Command |"),
        None,
    )
    assert table_start is not None, (
        "README governance command table header row must exist"
    )

    table_lines: list[str] = []
    for line in lines[table_start:]:
        stripped = line.strip()
        if not stripped:
            if table_lines:
                break
            continue
        if not stripped.startswith("|"):
            if table_lines:
                break
            continue
        table_lines.append(stripped)

    assert table_lines, "README governance command table must include markdown rows"

    separator_pattern = re.compile(r"^\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|$")
    for row in table_lines:
        assert row.startswith("|") and row.endswith("|"), (
            f"Each governance command table row must start and end with '|': {row!r}"
        )
        parts = [part.strip() for part in row.split("|")[1:-1]]
        assert len(parts) == 2, (
            f"Each governance command table row must have exactly two cells: {row!r}"
        )
        if row == "| Goal | Command |":
            continue
        if separator_pattern.match(row):
            continue
        assert all(part for part in parts), (
            f"Each governance command table body row must have non-empty goal and command cells: {row!r}"
        )


def test_non_direct_rows_do_not_repeat_tests_e2e_test_paths_within_same_row() -> None:
    rows = _command_table_rows(_readme_text())
    pattern = re.compile(r"^tests/e2e/test_[^\s`]+\.py$")

    for goal, command_cell in rows:
        if goal.endswith("(direct)"):
            continue
        if not (command_cell.startswith("`") and command_cell.endswith("`")):
            continue

        tokens = shlex.split(command_cell[1:-1].strip())
        path_tokens = [token for token in tokens if pattern.match(token)]
        if not path_tokens:
            continue

        duplicates = sorted(
            {path for path in path_tokens if path_tokens.count(path) > 1}
        )
        assert not duplicates, (
            f"Non-direct row '{goal}' must not repeat tests/e2e/test_*.py paths; duplicates found: "
            + ", ".join(duplicates)
        )


def test_non_direct_rows_with_tests_e2e_paths_have_governance_or_suite_goal_labels() -> (
    None
):
    rows = _command_table_rows(_readme_text())

    for goal, command_cell in rows:
        if goal.endswith("(direct)"):
            continue
        if not (command_cell.startswith("`") and command_cell.endswith("`")):
            continue

        tokens = shlex.split(command_cell[1:-1].strip())
        path_tokens = [
            token
            for token in tokens
            if token.startswith("tests/e2e/") and token.endswith(".py")
        ]
        if not path_tokens:
            continue

        goal_label = goal.lower()
        assert "governance" in goal_label or "suite" in goal_label, (
            f"Non-direct row '{goal}' includes tests/e2e paths and must contain "
            "'governance' or 'suite' in the goal label"
        )


def test_full_bundle_row_includes_readme_e2e_commands_path() -> None:
    rows = _command_table_rows(_readme_text())
    full_bundle_goal = "Full e2e governance unit bundle (direct)"
    full_bundle_row = [
        command_cell for goal, command_cell in rows if goal == full_bundle_goal
    ]
    assert full_bundle_row, (
        f"README command table must include '{full_bundle_goal}' row"
    )

    tokens = shlex.split(full_bundle_row[0][1:-1].strip())
    path_tokens = [
        token
        for token in tokens
        if token.startswith("tests/e2e/") and token.endswith(".py")
    ]
    assert "tests/e2e/test_readme_e2e_commands.py" in path_tokens, (
        "Full governance bundle row must include tests/e2e/test_readme_e2e_commands.py"
    )


def test_readme_includes_smoke_runner_governance_command_example() -> None:
    text = _readme_text()

    assert "Smoke runner governance (direct)" in text
    assert "pytest -q tests/e2e/test_smoke_runner_governance.py" in text


def test_readme_includes_governance_inventory_command_example() -> None:
    text = _readme_text()

    assert "Governance inventory artifact (direct)" in text
    assert "pytest -q tests/e2e/test_governance_inventory_artifact.py" in text


def test_readme_includes_governance_set_equality_command_example() -> None:
    text = _readme_text()

    assert "Governance set equality (direct)" in text
    assert "pytest -q tests/e2e/test_governance_set_equality.py" in text


def test_readme_includes_normalized_duplicate_command_example() -> None:
    text = _readme_text()

    assert "README command normalized-duplicates (direct)" in text
    assert "pytest -q tests/e2e/test_readme_command_normalized_duplicates.py" in text


def test_governance_goal_labels_appear_exactly_once_in_command_matrix() -> None:
    rows = _command_table_rows(_readme_text())
    governance_goals = [
        goal for goal, _command_cell in rows if "governance" in goal.lower()
    ]
    assert governance_goals, (
        "README command table should include governance goal labels"
    )

    duplicates = sorted(
        {goal for goal in governance_goals if governance_goals.count(goal) > 1}
    )
    assert not duplicates, (
        "README command table governance goal labels must appear exactly once; duplicates found: "
        + ", ".join(duplicates)
    )


def test_readme_command_snippet_test_paths_exist() -> None:
    text = _readme_text()
    readme_test_paths = _readme_test_paths_from_command_snippets(text)

    assert readme_test_paths, (
        "README command snippets should include at least one tests/...py path"
    )

    missing_paths = [
        path for path in readme_test_paths if not (REPO_ROOT / path).exists()
    ]
    assert not missing_paths, (
        "README command snippets reference missing test files: "
        + ", ".join(missing_paths)
    )


def test_governance_related_goal_labels_are_printable_ascii() -> None:
    for goal, _command_cell in _command_table_rows(_readme_text()):
        if "governance" not in goal.lower() and "(direct)" not in goal:
            continue
        assert goal.isascii() and goal.isprintable(), (
            f"Governance-related goal labels must be printable ASCII: {goal!r}"
        )


def test_governance_related_goal_labels_have_no_surrounding_whitespace() -> None:
    for goal, _command_cell in _command_table_rows(_readme_text()):
        if "governance" not in goal.lower() and "(direct)" not in goal:
            continue
        assert goal == goal.strip(), (
            f"Governance-related goal labels must not include outer whitespace: {goal!r}"
        )


def test_governance_related_rows_include_tests_e2e_paths() -> None:
    for goal, command_cell in _command_table_rows(_readme_text()):
        if "(direct)" not in goal:
            continue
        if not (command_cell.startswith("`") and command_cell.endswith("`")):
            continue
        tokens = shlex.split(command_cell[1:-1].strip())
        path_tokens = [
            token
            for token in tokens
            if token.startswith("tests/e2e/") and token.endswith(".py")
        ]
        assert path_tokens, (
            f"Governance-related row '{goal}' must include tests/e2e/*.py path tokens"
        )


def test_fast_governance_non_path_tokens_are_not_duplicated_after_prefix() -> None:
    rows = _command_table_rows(_readme_text())
    fast_row = [
        command_cell for goal, command_cell in rows if goal == "Fast governance checks"
    ]
    assert fast_row, "README command table must include 'Fast governance checks' row"

    tokens = shlex.split(fast_row[0][1:-1].strip())
    assert tokens[:2] == ["pytest", "-q"], (
        "Fast governance checks row must start with `pytest -q`"
    )
    non_path_tokens = [
        token
        for token in tokens[2:]
        if not (token.startswith("tests/e2e/") and token.endswith(".py"))
    ]
    duplicates = [
        token for token, count in Counter(non_path_tokens).items() if count > 1
    ]
    assert not duplicates, (
        "Fast governance checks row must not repeat non-path tokens after `pytest -q`: "
        + ", ".join(duplicates)
    )


def test_full_bundle_has_more_test_paths_than_fast_governance_row() -> None:
    rows = _command_table_rows(_readme_text())
    fast_row = [
        command_cell for goal, command_cell in rows if goal == "Fast governance checks"
    ]
    full_row = [
        command_cell
        for goal, command_cell in rows
        if goal == "Full e2e governance unit bundle (direct)"
    ]
    assert fast_row and full_row, (
        "README command table must include both fast and full governance rows"
    )

    fast_paths = [
        token
        for token in shlex.split(fast_row[0][1:-1].strip())
        if token.startswith("tests/e2e/test_") and token.endswith(".py")
    ]
    full_paths = [
        token
        for token in shlex.split(full_row[0][1:-1].strip())
        if token.startswith("tests/e2e/test_") and token.endswith(".py")
    ]
    assert len(full_paths) > len(fast_paths), (
        "Full governance bundle row must contain more tests/e2e/test_*.py paths than fast governance row"
    )


def test_governance_goal_labels_follow_stable_capitalization_policy() -> None:
    rows = _command_table_rows(_readme_text())
    governance_goals = [
        goal for goal, _command_cell in rows if "governance" in goal.lower()
    ]
    assert governance_goals, (
        "README command table should include governance-related goal labels"
    )

    allowed_lowercase_tokens = {
        "and",
        "artifact",
        "bundle",
        "checks",
        "collect-only",
        "contracts",
        "direct",
        "e2e",
        "equality",
        "governance",
        "health",
        "import",
        "inventory",
        "marker",
        "module",
        "pairing",
        "rewrite",
        "runner",
        "set",
        "smoke",
        "split",
        "sync",
        "tests",
        "unit",
    }

    for goal in governance_goals:
        for raw_token in goal.replace("(", " ").replace(")", " ").split():
            token = raw_token.strip(",.:;").lower()
            if not token or token.isdigit():
                continue
            if raw_token.isupper():
                continue
            if token in allowed_lowercase_tokens:
                continue
            assert raw_token[0].isupper(), (
                "Governance goal labels must use stable capitalization: significant words should be "
                f"capitalized unless explicitly allowed lowercase; offending token {raw_token!r} in {goal!r}"
            )


def test_command_table_parser_ignores_escaped_pipe_backtick_edge_rows_and_keeps_core_rows() -> (
    None
):
    markdown = """
| Goal | Command |
| --- | --- |
| Fast governance checks | `pytest -q tests/e2e/test_split_hygiene.py` |
| Escaped \\| pipe edge row | `pytest -q tests/e2e/test_readme_e2e_commands.py` |
| Escaped backtick edge row | `pytest -q tests/e2e/test_cli_alias_rewrite_contract.py \\`
| Governance sync contracts (direct) | `pytest -q tests/e2e/test_governance_sync_contracts.py` |
"""
    rows = _command_table_rows(markdown)

    goals = [goal for goal, _command_cell in rows]
    assert "Fast governance checks" in goals
    assert "Governance sync contracts (direct)" in goals
    assert "Escaped \\| pipe edge row" not in goals
    assert "Escaped backtick edge row" not in goals


# noqa: PT018
