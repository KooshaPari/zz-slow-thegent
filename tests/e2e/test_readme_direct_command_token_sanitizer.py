"""Token sanitizer contracts for README direct pytest rows."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

README_PATH = Path(__file__).with_name("README.md")


def _direct_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    in_table = False

    for line in README_PATH.read_text(encoding="utf-8").splitlines():
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
        if goal.endswith("(direct)"):
            rows.append((goal, command_cell))

    return rows


def _table_command_snippets() -> list[str]:
    snippets: list[str] = []
    in_table = False

    for line in README_PATH.read_text(encoding="utf-8").splitlines():
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
        snippets.extend(re.findall(r"`([^`]+)`", command_cell))

    return snippets


def _commands() -> list[list[str]]:
    text = README_PATH.read_text(encoding="utf-8")
    commands: list[list[str]] = []
    for snippet in re.findall(r"`([^`]+)`", text):
        tokens = shlex.split(snippet)
        if tokens[:2] == ["pytest", "-q"] and any(t.startswith("tests/e2e/") and t.endswith(".py") for t in tokens):
            commands.append(tokens)
    return commands


def test_table_command_snippets_never_include_shell_redirection_tokens() -> None:
    snippets = _table_command_snippets()
    assert snippets

    for snippet in snippets:
        tokens = shlex.split(snippet)
        assert not any(token in {">", ">>", "<"} for token in tokens), (
            f"README command snippets must not include shell redirection tokens ('>', '>>', '<'): {snippet!r}"
        )


def test_table_command_snippets_are_shlex_tokenizable() -> None:
    snippets = _table_command_snippets()
    assert snippets

    for snippet in snippets:
        try:
            shlex.split(snippet)
        except ValueError as exc:
            pytest.fail(
                "README table command snippet must be shlex-tokenizable "
                f"(likely unbalanced quotes): {snippet!r} ({exc})"
            )


def test_direct_single_file_rows_contain_exactly_one_e2e_file_token() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        if any(keyword in goal.lower() for keyword in ("suite", "bundle")):
            continue

        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )

        e2e_tokens = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/") and token.endswith(".py")
        ]
        assert len(e2e_tokens) == 1, (
            f"README direct single-file row '{goal}' must contain exactly one tests/e2e/*.py token: {snippets[0]!r}"
        )


def test_direct_rows_have_exactly_one_backticked_command_snippet() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        if "bundle" in goal.lower():
            continue

        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )


def test_direct_row_command_snippet_is_single_line_without_shell_separators() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )

        snippet = snippets[0]
        assert "\n" not in snippet, f"README direct row '{goal}' command snippet must be single-line: {snippet!r}"
        assert "\r" not in snippet, f"README direct row '{goal}' command snippet must be single-line: {snippet!r}"
        assert not re.search(r";|&&|\|\||\|", snippet), (
            f"README direct row '{goal}' command snippet must not contain shell separators (; && || |): {snippet!r}"
        )


def test_direct_pytest_rows_only_use_allowed_tokens() -> None:
    commands = _commands()
    assert commands

    for tokens in commands:
        for token in tokens[2:]:
            assert token.startswith("tests/e2e/"), (
                f"Direct README governance pytest rows must contain only tests/e2e paths after `pytest -q`: {tokens!r}"
            )
            assert token.endswith(".py"), (
                f"Direct README governance pytest rows must contain only tests/e2e paths after `pytest -q`: {tokens!r}"
            )


def test_direct_row_command_snippet_starts_with_pytest_q_prefix() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )

        snippet = snippets[0]
        assert snippet.startswith("pytest -q "), (
            f"README direct row '{goal}' command snippet must start with 'pytest -q ': {snippet!r}"
        )


def test_direct_row_referenced_e2e_paths_exist_on_disk() -> None:
    rows = _direct_rows()
    assert rows
    repo_root = Path(__file__).resolve().parents[2]

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )

        for token in shlex.split(snippets[0]):
            if token.startswith("tests/e2e/") and token.endswith(".py"):
                target = repo_root / token
                assert target.exists(), f"README direct row '{goal}' references missing tests/e2e path: {token!r}"


def test_direct_rows_do_not_reference_command_surface_helper_path() -> None:
    rows = _direct_rows()
    assert rows

    forbidden_path = "tests/e2e/command_surface.py"
    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        assert forbidden_path not in shlex.split(snippets[0]), (
            f"README direct row '{goal}' must not reference helper path {forbidden_path!r}: {snippets[0]!r}"
        )


def test_direct_row_command_cell_has_one_backticked_snippet_and_no_extra_backticks() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        assert command_cell.count("`") == 2, (
            f"README direct row '{goal}' command cell must contain no extra backticks: {command_cell!r}"
        )


def test_direct_row_python_path_tokens_start_with_tests_e2e_prefix() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )

        tokens = shlex.split(snippets[0])
        path_tokens = [token for token in tokens if token.endswith(".py")]
        assert path_tokens, f"README direct row '{goal}' must include at least one .py path token: {snippets[0]!r}"

        for token in path_tokens:
            assert token.startswith("tests/e2e/"), (
                f"README direct row '{goal}' .py path token must start with 'tests/e2e/': {token!r}"
            )


def test_non_bundle_direct_rows_do_not_duplicate_identical_command_snippets() -> None:
    rows = _direct_rows()
    assert rows

    snippet_to_goal: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []

    for goal, command_cell in rows:
        if "bundle" in goal.lower():
            continue

        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        snippet = snippets[0]

        prior_goal = snippet_to_goal.get(snippet)
        if prior_goal is None:
            snippet_to_goal[snippet] = goal
            continue
        duplicates.append((snippet, prior_goal, goal))

    assert not duplicates, f"README non-bundle direct rows must not duplicate identical command snippets: {duplicates}"


def test_each_direct_test_path_maps_to_single_goal_label() -> None:
    rows = _direct_rows()
    assert rows

    path_to_goal: dict[str, str] = {}
    collisions: list[tuple[str, str, str]] = []

    for goal, command_cell in rows:
        if "bundle" in goal.lower():
            continue

        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        paths = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/test_") and token.endswith(".py")
        ]
        for path in paths:
            prior_goal = path_to_goal.get(path)
            if prior_goal is None:
                path_to_goal[path] = goal
                continue
            if prior_goal != goal:
                collisions.append((path, prior_goal, goal))

    assert not collisions, (
        f"Each direct-row tests/e2e/test_*.py path must map to exactly one direct goal label: {collisions}"
    )


def test_direct_single_file_rows_have_unique_path_basenames() -> None:
    rows = _direct_rows()
    assert rows

    basename_to_path: dict[str, str] = {}
    collisions: list[tuple[str, str, str]] = []

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        e2e_paths = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/") and token.endswith(".py")
        ]
        if len(e2e_paths) != 1:
            continue

        path = e2e_paths[0]
        basename = Path(path).name
        prior_path = basename_to_path.get(basename)
        if prior_path is None:
            basename_to_path[basename] = path
            continue
        if prior_path != path:
            collisions.append((basename, prior_path, path))

    assert not collisions, f"README direct single-file rows must use unique tests/e2e/*.py basenames: {collisions}"


def test_each_direct_row_command_has_no_duplicate_whitespace_normalized_tokens() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        normalized_tokens = [re.sub(r"\s+", " ", token).strip() for token in shlex.split(snippets[0])]
        duplicates = sorted({token for token in normalized_tokens if normalized_tokens.count(token) > 1})
        assert not duplicates, (
            "README direct-row command must not contain duplicate whitespace-normalized tokens: "
            f"goal={goal!r} duplicates={duplicates!r} command={snippets[0]!r}"
        )


def test_non_suite_non_bundle_direct_rows_are_goal_to_single_test_file_bijection() -> None:
    rows = _direct_rows()
    assert rows

    goal_to_path: dict[str, str] = {}
    path_to_goal: dict[str, str] = {}
    collisions: list[tuple[str, str, str]] = []

    for goal, command_cell in rows:
        lower_goal = goal.lower()
        if "suite" in lower_goal or "bundle" in lower_goal:
            continue

        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        test_paths = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/test_") and token.endswith(".py")
        ]
        assert len(test_paths) == 1, (
            f"README non-suite/non-bundle direct row '{goal}' must map to exactly one tests/e2e/test_*.py path: "
            f"{snippets[0]!r}"
        )

        path = test_paths[0]
        goal_to_path[goal] = path
        prior_goal = path_to_goal.get(path)
        if prior_goal is None:
            path_to_goal[path] = goal
            continue
        if prior_goal != goal:
            collisions.append((path, prior_goal, goal))

    assert goal_to_path, "Expected at least one non-suite/non-bundle direct row in README table."
    assert not collisions, (
        f"README non-suite/non-bundle direct rows must be a 1:1 goal->single-file mapping: {collisions}"
    )


def test_only_suite_or_bundle_direct_rows_may_reference_multiple_test_files() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        test_paths = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/test_") and token.endswith(".py")
        ]
        if len(test_paths) <= 1:
            continue
        assert any(keyword in goal.lower() for keyword in ("suite", "bundle")), (
            "README direct rows may include multiple tests/e2e/test_*.py paths only when the goal label "
            f"contains 'suite' or 'bundle': goal={goal!r} command={snippets[0]!r}"
        )


def test_suite_direct_rows_do_not_duplicate_path_basenames_across_tokens() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        if "suite" not in goal.lower():
            continue

        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README suite direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        path_tokens = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/") and token.endswith(".py")
        ]
        basenames = [Path(token).name for token in path_tokens]
        duplicates = sorted({name for name in basenames if basenames.count(name) > 1})
        assert not duplicates, (
            "README suite direct row must not duplicate tests/e2e/*.py basenames across path tokens: "
            f"goal={goal!r} duplicates={duplicates!r} command={snippets[0]!r}"
        )


def test_alias_trio_direct_rows_each_have_exactly_one_test_path_token() -> None:
    rows = _direct_rows()
    assert rows

    alias_trio_goals = {
        "Alias rewrite contract unit (direct)",
        "Alias rewrite real-app contract unit (direct)",
        "Alias unsupported rationale contract (direct)",
    }

    direct_map = dict(rows)
    assert alias_trio_goals <= set(direct_map), (
        "README direct table must include all alias trio direct rows: "
        f"missing={sorted(alias_trio_goals - set(direct_map))!r}"
    )

    for goal in sorted(alias_trio_goals):
        command_cell = direct_map[goal]
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README alias direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        test_paths = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/test_") and token.endswith(".py")
        ]
        assert len(test_paths) == 1, (
            "README alias trio direct-row command cell must contain exactly one tests/e2e/test_*.py token: "
            f"goal={goal!r} command={snippets[0]!r}"
        )


def test_direct_rows_have_no_empty_command_snippets() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        assert snippets[0].strip(), (
            f"README direct row '{goal}' command snippet must not be empty or whitespace-only: {command_cell!r}"
        )


def test_direct_rows_have_no_duplicate_test_path_tokens_within_row() -> None:
    rows = _direct_rows()
    assert rows

    for goal, command_cell in rows:
        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        test_paths = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/test_") and token.endswith(".py")
        ]
        duplicates = sorted({path for path in test_paths if test_paths.count(path) > 1})
        assert not duplicates, (
            "README direct row command must not repeat tests/e2e/test_*.py path tokens within the same row: "
            f"goal={goal!r} duplicates={duplicates!r} command={snippets[0]!r}"
        )


def test_direct_non_bundle_single_file_rows_have_unique_basename_coverage() -> None:
    rows = _direct_rows()
    assert rows

    basename_to_goal: dict[str, str] = {}
    collisions: list[tuple[str, str, str]] = []

    for goal, command_cell in rows:
        if "bundle" in goal.lower():
            continue

        snippets = re.findall(r"`([^`]+)`", command_cell)
        assert len(snippets) == 1, (
            f"README direct row '{goal}' must have exactly one backticked command snippet: {command_cell!r}"
        )
        test_paths = [
            token for token in shlex.split(snippets[0]) if token.startswith("tests/e2e/test_") and token.endswith(".py")
        ]
        if len(test_paths) != 1:
            continue

        basename = Path(test_paths[0]).name
        prior_goal = basename_to_goal.get(basename)
        if prior_goal is None:
            basename_to_goal[basename] = goal
            continue
        if prior_goal != goal:
            collisions.append((basename, prior_goal, goal))

    assert basename_to_goal, "Expected at least one non-bundle direct single-file tests/e2e/test_*.py row."
    assert not collisions, (
        "README direct non-bundle single-file rows must have unique tests/e2e/test_*.py basename coverage: "
        f"{collisions}"
    )
