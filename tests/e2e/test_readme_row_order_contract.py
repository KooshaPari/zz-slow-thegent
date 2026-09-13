"""Contract checks for strict README governance row ordering."""

from __future__ import annotations

import re
from pathlib import Path

README_PATH = Path(__file__).with_name("README.md")

EXPECTED_GOVERNANCE_ROW_ORDER = (
    "Fast governance checks",
    "Alias rewrite contract unit (direct)",
    "Alias rewrite real-app contract unit (direct)",
    "Alias unsupported rationale contract (direct)",
    "Compat unit suite (direct)",
    "Compat helper extract/rewrite guard suite (direct)",
    "Compat import governance (direct)",
    "Compat skip-message contract suite (direct)",
    "Compat skip-prefix contract suite (direct)",
    "Compat edge-token suite (direct)",
    "Command-surface unit (direct)",
    "Utility module pairing governance (direct)",
    "Governance health artifact (direct)",
    "Governance inventory artifact (direct)",
    "Governance set equality (direct)",
    "Governance sync contracts (direct)",
    "README bundle order contract (direct)",
    "README direct e2e collect-only governance (direct)",
    "README command normalized-duplicates (direct)",
    "README command uniqueness (direct)",
    "README row order contract (direct)",
    "Real-app command families contract (direct)",
    "Real-app help anchor contract (direct)",
    "Smoke runner governance (direct)",
    "Split marker governance (direct)",
    "Full e2e governance unit bundle (direct)",
)


def _readme_lines() -> list[str]:
    return README_PATH.read_text(encoding="utf-8").splitlines()


def _command_table_goal_rows() -> list[str]:
    goals: list[str] = []
    in_table = False

    for line in _readme_lines():
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
        if len(parts) < 2:
            continue
        goal = parts[0]
        if goal in {"Goal", "---"}:
            in_table = True
            continue
        in_table = True
        goals.append(goal)

    return goals


def _command_table_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    in_table = False

    for line in _readme_lines():
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
        if len(parts) < 2:
            continue
        goal, command = parts[0], parts[1]
        if goal in {"Goal", "---"}:
            in_table = True
            continue
        in_table = True
        rows.append((goal, command))

    return rows


def _actual_governance_goal_order() -> list[str]:
    expected_goals = set(EXPECTED_GOVERNANCE_ROW_ORDER)
    return [goal for goal in _command_table_goal_rows() if goal in expected_goals]


def _referenced_e2e_test_filenames(command_cell: str) -> list[str]:
    snippet = command_cell.strip()
    if snippet.startswith("`") and snippet.endswith("`"):
        snippet = snippet[1:-1].strip()
    return re.findall(r"tests/e2e/([^\s`]+\.py)", snippet)


def _referenced_e2e_test_paths(command_cell: str) -> list[str]:
    snippet = command_cell.strip()
    if snippet.startswith("`") and snippet.endswith("`"):
        snippet = snippet[1:-1].strip()
    return re.findall(r"(tests/e2e/[^\s`]+\.py)", snippet)


def _normalized_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def _first_mismatch_message(expected: tuple[str, ...], actual: list[str]) -> str | None:
    for index, expected_goal in enumerate(expected, start=1):
        actual_goal = actual[index - 1] if index - 1 < len(actual) else "<missing>"
        if actual_goal != expected_goal:
            return (
                f"README governance row order mismatch at position {index}: "
                f"expected '{expected_goal}' but found '{actual_goal}'."
            )
    if len(actual) > len(expected):
        overflow_goal = actual[len(expected)]
        return (
            f"README governance row order mismatch at position {len(expected) + 1}: "
            f"expected '<end>' but found '{overflow_goal}'."
        )
    return None


def test_governance_rows_follow_strict_expected_order() -> None:
    actual = _actual_governance_goal_order()
    mismatch = _first_mismatch_message(EXPECTED_GOVERNANCE_ROW_ORDER, actual)
    assert mismatch is None, mismatch


def test_governance_block_row_count_matches_expected_order_length() -> None:
    actual = _actual_governance_goal_order()
    assert len(actual) == len(EXPECTED_GOVERNANCE_ROW_ORDER), (
        "README governance block row count must equal EXPECTED_GOVERNANCE_ROW_ORDER length: "
        f"actual={len(actual)} expected={len(EXPECTED_GOVERNANCE_ROW_ORDER)}"
    )


def test_every_governance_row_command_starts_with_pytest_q() -> None:
    command_by_goal = dict(_command_table_rows())

    for goal in EXPECTED_GOVERNANCE_ROW_ORDER:
        assert goal in command_by_goal, f"README governance row is missing from command table: '{goal}'"
        snippet = command_by_goal[goal].strip().strip("`").strip()
        assert snippet.startswith("pytest -q"), (
            f"README governance row '{goal}' command must start with `pytest -q`: {snippet}"
        )


def test_governance_rows_have_strictly_increasing_table_indices() -> None:
    all_goals = _command_table_goal_rows()
    governance_positions = [index for index, goal in enumerate(all_goals) if goal in EXPECTED_GOVERNANCE_ROW_ORDER]
    assert governance_positions == sorted(governance_positions), (
        f"README governance rows must preserve table order with strictly increasing indices: {governance_positions}"
    )
    assert len(governance_positions) == len(set(governance_positions)), (
        f"README governance rows must not share table positions: {governance_positions}"
    )


def test_each_expected_governance_goal_maps_to_exactly_one_command_cell_occurrence() -> None:
    rows = _command_table_rows()
    occurrences_by_goal = {
        goal: sum(1 for row_goal, _ in rows if row_goal == goal) for goal in EXPECTED_GOVERNANCE_ROW_ORDER
    }
    mismatches = {goal: count for goal, count in occurrences_by_goal.items() if count != 1}
    assert not mismatches, (
        f"Each expected governance goal must map to exactly one command cell occurrence in README table: {mismatches}"
    )


def test_full_bundle_row_is_last_direct_governance_row_in_table_order() -> None:
    goals = _command_table_goal_rows()
    direct_governance_goals = [goal for goal in goals if goal in EXPECTED_GOVERNANCE_ROW_ORDER and "(direct)" in goal]
    assert direct_governance_goals, "README command table must include direct governance rows."
    assert direct_governance_goals[-1] == "Full e2e governance unit bundle (direct)", (
        "Full bundle governance row must remain the last direct governance row in table order: "
        f"{direct_governance_goals}"
    )


def test_governance_rows_form_one_contiguous_block_in_table() -> None:
    all_goals = _command_table_goal_rows()
    positions: list[int] = []

    for goal in EXPECTED_GOVERNANCE_ROW_ORDER:
        assert goal in all_goals, f"README governance row is missing from command table: '{goal}'"
        positions.append(all_goals.index(goal))

    start = positions[0]
    expected_positions = list(range(start, start + len(EXPECTED_GOVERNANCE_ROW_ORDER)))
    assert positions == expected_positions, (
        "README governance rows must remain a contiguous block with no interleaving rows "
        f"between '{EXPECTED_GOVERNANCE_ROW_ORDER[0]}' and '{EXPECTED_GOVERNANCE_ROW_ORDER[-1]}'."
    )


def test_governance_block_is_bounded_by_expected_first_and_last_rows() -> None:
    goals = _command_table_goal_rows()
    governance_positions = [index for index, goal in enumerate(goals) if goal in EXPECTED_GOVERNANCE_ROW_ORDER]
    assert governance_positions, "README command table must include governance rows."

    first_governance_goal = goals[governance_positions[0]]
    last_governance_goal = goals[governance_positions[-1]]
    assert first_governance_goal == EXPECTED_GOVERNANCE_ROW_ORDER[0], (
        "README governance block must start with "
        f"'{EXPECTED_GOVERNANCE_ROW_ORDER[0]}', found '{first_governance_goal}'."
    )
    assert last_governance_goal == EXPECTED_GOVERNANCE_ROW_ORDER[-1], (
        f"README governance block must end with '{EXPECTED_GOVERNANCE_ROW_ORDER[-1]}', found '{last_governance_goal}'."
    )


def test_governance_rows_use_direct_backticked_pytest_commands() -> None:
    command_by_goal = dict(_command_table_rows())

    for goal in EXPECTED_GOVERNANCE_ROW_ORDER:
        assert goal in command_by_goal, f"README governance row is missing from command table: '{goal}'"
        command_cell = command_by_goal[goal]

        assert command_cell.startswith("`"), (
            f"README governance row '{goal}' command must be a single backticked snippet: {command_cell}"
        )
        assert command_cell.endswith("`"), (
            f"README governance row '{goal}' command must be a single backticked snippet: {command_cell}"
        )

        snippet = command_cell[1:-1].strip()
        assert "\n" not in snippet, f"README governance row '{goal}' command must be single-line: {snippet!r}"
        assert "\r" not in snippet, f"README governance row '{goal}' command must be single-line: {snippet!r}"
        assert snippet.startswith("pytest -q "), (
            f"README governance row '{goal}' must present a direct `pytest -q` command: {snippet}"
        )
        assert "tests/e2e/" in snippet, f"README governance row '{goal}' must target tests/e2e paths: {snippet}"


def test_direct_governance_rows_are_lexicographic_by_referenced_test_filename() -> None:
    direct_rows: list[tuple[str, str]] = []

    for goal, command in _command_table_rows():
        if goal in EXPECTED_GOVERNANCE_ROW_ORDER and "(direct)" in goal:
            filenames = _referenced_e2e_test_filenames(command)
            if len(filenames) == 1:
                direct_rows.append((goal, filenames[0]))

    filenames_in_table_order = [filename for _, filename in direct_rows]
    assert filenames_in_table_order == sorted(filenames_in_table_order), (
        "README direct governance rows must be lexicographically ordered by referenced test filename: "
        f"{filenames_in_table_order}"
    )


def test_direct_governance_rows_have_unique_normalized_goal_slugs() -> None:
    direct_goals = [
        goal for goal in _command_table_goal_rows() if goal in EXPECTED_GOVERNANCE_ROW_ORDER and "(direct)" in goal
    ]
    slugs_in_table_order = [_normalized_slug(goal) for goal in direct_goals]
    assert all(slug for slug in slugs_in_table_order), (
        "README direct governance row goals must produce non-empty normalized slugs: "
        f"{list(zip(direct_goals, slugs_in_table_order, strict=False))}"
    )
    duplicates = sorted({slug for slug in slugs_in_table_order if slugs_in_table_order.count(slug) > 1})
    assert not duplicates, "README direct governance row normalized slugs must be unique: " + ", ".join(duplicates)


def test_non_bundle_direct_governance_rows_do_not_duplicate_single_file_paths() -> None:
    first_goal_by_path: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []

    for goal, command in _command_table_rows():
        if goal not in EXPECTED_GOVERNANCE_ROW_ORDER or "(direct)" not in goal:
            continue
        if "bundle" in goal.lower():
            continue

        unique_paths = sorted(set(_referenced_e2e_test_paths(command)))
        if len(unique_paths) != 1:
            continue

        path = unique_paths[0]
        first_goal = first_goal_by_path.get(path)
        if first_goal is None:
            first_goal_by_path[path] = goal
            continue
        duplicates.append((path, first_goal, goal))

    assert not duplicates, (
        f"README non-bundle direct governance rows must not duplicate exact single-file test paths: {duplicates}"
    )


def test_alias_governance_trio_rows_exist_in_stable_relative_order() -> None:
    goals = _command_table_goal_rows()
    direct_goals = [goal for goal in goals if "(direct)" in goal]

    contract_matches = [goal for goal in direct_goals if goal.startswith("Alias rewrite contract ")]
    real_app_matches = [goal for goal in direct_goals if goal.startswith("Alias rewrite real-app ")]
    unsupported_matches = [
        goal
        for goal in direct_goals
        if goal.startswith("Alias unsupported ") and (" evidence " in f" {goal} " or " rationale " in f" {goal} ")
    ]

    assert len(contract_matches) == 1, (
        "README must include exactly one direct alias governance contract row "
        f"(found {len(contract_matches)}): {contract_matches}"
    )
    assert len(real_app_matches) == 1, (
        "README must include exactly one direct alias governance real-app row "
        f"(found {len(real_app_matches)}): {real_app_matches}"
    )
    assert len(unsupported_matches) == 1, (
        "README must include exactly one direct alias governance unsupported evidence/rationale row "
        f"(found {len(unsupported_matches)}): {unsupported_matches}"
    )

    contract_index = direct_goals.index(contract_matches[0])
    real_app_index = direct_goals.index(real_app_matches[0])
    unsupported_index = direct_goals.index(unsupported_matches[0])
    assert contract_index < real_app_index < unsupported_index, (
        "README alias governance trio rows must remain in stable relative order "
        "(contract, real-app, unsupported evidence/rationale)."
    )


def test_alias_governance_trio_direct_paths_follow_canonical_increasing_order() -> None:
    command_by_goal = dict(_command_table_rows())
    alias_goals = (
        "Alias rewrite contract unit (direct)",
        "Alias rewrite real-app contract unit (direct)",
        "Alias unsupported rationale contract (direct)",
    )
    trio_paths: list[str] = []

    for goal in alias_goals:
        assert goal in command_by_goal, f"README governance row is missing from command table: '{goal}'"
        unique_paths = sorted(set(_referenced_e2e_test_paths(command_by_goal[goal])))
        assert len(unique_paths) == 1, (
            f"README alias governance row '{goal}' must reference exactly one tests/e2e path: {command_by_goal[goal]}"
        )
        trio_paths.append(unique_paths[0])

    assert trio_paths == sorted(trio_paths), (
        f"README alias governance trio direct paths must be in canonical increasing order: {trio_paths}"
    )


def test_alias_governance_trio_goals_are_contiguous_in_table_positions() -> None:
    goals = _command_table_goal_rows()
    alias_goals = (
        "Alias rewrite contract unit (direct)",
        "Alias rewrite real-app contract unit (direct)",
        "Alias unsupported rationale contract (direct)",
    )
    positions: list[int] = []

    for goal in alias_goals:
        assert goal in goals, f"README governance row is missing from command table: '{goal}'"
        positions.append(goals.index(goal))

    contiguous_positions = list(range(min(positions), max(positions) + 1))
    assert positions == contiguous_positions, (
        "README alias governance trio goals must be contiguous in command table position: "
        f"{list(zip(alias_goals, positions, strict=False))}"
    )


def test_governance_block_has_no_duplicate_command_cells() -> None:
    rows = _command_table_rows()
    governance_commands: dict[str, list[str]] = {}

    for goal, command in rows:
        if goal not in EXPECTED_GOVERNANCE_ROW_ORDER:
            continue
        normalized_command = command.strip()
        governance_commands.setdefault(normalized_command, []).append(goal)

    duplicates = sorted((command, goals) for command, goals in governance_commands.items() if len(goals) > 1)
    assert not duplicates, (
        f"README governance block must not contain duplicate command cells across goals: {duplicates}"
    )


def test_expected_governance_row_order_labels_are_unique() -> None:
    duplicates = sorted(
        {goal for goal in EXPECTED_GOVERNANCE_ROW_ORDER if EXPECTED_GOVERNANCE_ROW_ORDER.count(goal) > 1}
    )
    assert not duplicates, "EXPECTED_GOVERNANCE_ROW_ORDER must not contain duplicate goal labels: " + ", ".join(
        duplicates
    )


def test_suite_direct_multi_path_rows_keep_stable_path_ordering_by_basename() -> None:
    rows = _command_table_rows()
    multi_path_direct_rows: list[tuple[str, list[str]]] = []

    for goal, command in rows:
        if goal not in EXPECTED_GOVERNANCE_ROW_ORDER or "(direct)" not in goal:
            continue
        paths = _referenced_e2e_test_paths(command)
        if len(paths) > 1:
            multi_path_direct_rows.append((goal, paths))

    assert multi_path_direct_rows, "README governance command table must include at least one multi-path direct row."

    out_of_order = [
        (goal, paths)
        for goal, paths in multi_path_direct_rows
        if paths != sorted(paths, key=lambda path: (Path(path).name, path))
    ]
    assert not out_of_order, (
        f"README suite direct rows with multiple paths must keep stable basename ordering: {out_of_order}"
    )


def test_governance_goal_labels_are_unique_case_insensitively() -> None:
    lowered_labels = [goal.lower() for goal in EXPECTED_GOVERNANCE_ROW_ORDER]
    duplicates = sorted({label for label in lowered_labels if lowered_labels.count(label) > 1})
    assert not duplicates, (
        "EXPECTED_GOVERNANCE_ROW_ORDER must not contain case-insensitive duplicate goal labels: "
        + ", ".join(duplicates)
    )


def test_no_extra_governance_like_direct_rows_outside_expected_block() -> None:
    governance_keywords = ("governance", "alias", "compat", "real-app", "command-surface", "split marker")
    extras: list[str] = []

    for goal in _command_table_goal_rows():
        if "(direct)" not in goal:
            continue
        lowered = goal.lower()
        if any(keyword in lowered for keyword in governance_keywords) and goal not in EXPECTED_GOVERNANCE_ROW_ORDER:
            extras.append(goal)

    assert not extras, (
        "README contains governance-like direct rows outside EXPECTED_GOVERNANCE_ROW_ORDER: " + ", ".join(extras)
    )
