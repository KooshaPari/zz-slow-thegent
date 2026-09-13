"""Governance contracts for README direct-row label-to-file bijection."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from tests.e2e.test_readme_row_order_contract import EXPECTED_GOVERNANCE_ROW_ORDER

README_PATH = Path(__file__).with_name("README.md")
_DIRECT_LABEL_PATTERN = re.compile(r"\(direct\)", re.IGNORECASE)
_TEST_PATH_PATTERN = re.compile(r"^tests/e2e/test_[a-z0-9_]+\.py$")
_LABEL_STOPWORDS = {
    "command",
    "commands",
    "contract",
    "contracts",
    "direct",
    "e2e",
    "governance",
    "suite",
    "test",
    "tests",
    "unit",
}


def _readme_lines() -> list[str]:
    return README_PATH.read_text(encoding="utf-8").splitlines()


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
        if len(parts) != 2:
            continue
        label, command = parts
        if label in {"Goal", "---"}:
            in_table = True
            continue
        in_table = True
        if command.startswith("`") and command.endswith("`"):
            command = command[1:-1].strip()
        rows.append((label, command))

    return rows


def _direct_governance_rows() -> list[tuple[str, str]]:
    return [(label, command) for label, command in _command_table_rows() if _DIRECT_LABEL_PATTERN.search(label)]


def _direct_single_file_rows() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for label, command in _direct_governance_rows():
        paths = _test_paths_in_snippet(command)
        if len(paths) == 1:
            rows.append((label, command, paths[0]))
    return rows


def _test_paths_in_snippet(snippet: str) -> list[str]:
    return [token for token in shlex.split(snippet) if _TEST_PATH_PATTERN.fullmatch(token)]


def _label_key_tokens(label: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", label.lower()) if len(token) >= 3 and token not in _LABEL_STOPWORDS
    ]


def _token_matches_slug(token: str, file_slug: str) -> bool:
    singular = token[:-1] if token.endswith("s") and len(token) > 3 else token
    return token in file_slug or singular in file_slug


def _normalized_slug_tokens(path: str) -> set[str]:
    stem = Path(path).stem
    return {token for token in re.findall(r"[a-z0-9]+", stem.lower()) if len(token) >= 3}


def _label_file_overlap_tokens(label: str, path: str) -> set[str]:
    slug = "-".join(sorted(_normalized_slug_tokens(path)))
    return {token for token in _label_key_tokens(label) if _token_matches_slug(token, slug)}


def test_direct_single_file_row_label_token_overlap_set_is_non_empty() -> None:
    rows = _direct_single_file_rows()
    assert rows, "README should include direct rows with exactly one tests/e2e file path"

    for label, _, path in rows:
        overlap = _label_file_overlap_tokens(label, path)
        assert overlap, f"README row '{label}' must have non-empty label/file token overlap with '{path}'"


def test_direct_single_file_row_overlap_set_is_deterministic_under_normalization() -> None:
    rows = _direct_single_file_rows()
    assert rows, "README should include direct rows with exactly one tests/e2e file path"

    for label, _, path in rows:
        baseline = _label_file_overlap_tokens(label, path)
        normalized_label = " ".join(re.findall(r"[a-z0-9]+", label.lower()))
        normalized_path = str(Path(path).with_suffix(".PY")).upper()
        normalized = _label_file_overlap_tokens(normalized_label, normalized_path)
        assert baseline == normalized, (
            f"README row '{label}' overlap set must be deterministic under normalization; "
            f"baseline={sorted(baseline)} normalized={sorted(normalized)}"
        )


def test_direct_single_file_row_paths_are_unique() -> None:
    rows = _direct_single_file_rows()
    assert rows, "README should include direct rows with exactly one tests/e2e file path"

    paths = [path for _, _, path in rows]
    assert len(paths) == len(set(paths)), "README direct single-file rows must not reuse test paths"


def test_direct_single_file_row_path_basenames_are_unique() -> None:
    rows = _direct_single_file_rows()
    assert rows, "README should include direct rows with exactly one tests/e2e file path"

    basenames = [Path(path).name for _, _, path in rows]
    assert len(basenames) == len(set(basenames)), "README direct single-file rows must not reuse path basenames"


def test_direct_single_file_row_commands_start_with_pytest_q() -> None:
    rows = _direct_single_file_rows()
    assert rows, "README should include direct rows with exactly one tests/e2e file path"

    for label, command, _ in rows:
        assert command.startswith("pytest -q "), f"README row '{label}' command must start with 'pytest -q ': {command}"


def test_direct_single_file_rows_align_with_row_order_expected_direct_goals() -> None:
    rows = _direct_single_file_rows()
    assert rows, "README should include direct rows with exactly one tests/e2e file path"

    expected_direct_goals = {goal for goal in EXPECTED_GOVERNANCE_ROW_ORDER if "(direct)" in goal}
    unexpected_labels = sorted(label for label, _command, _path in rows if label not in expected_direct_goals)
    assert not unexpected_labels, (
        "README direct single-file rows must align with expected governance direct-goal subset: "
        + ", ".join(unexpected_labels)
    )


def test_alias_trio_labels_match_alias_path_family_tokens() -> None:
    rows = _direct_single_file_rows()
    alias_rows = [(label, path) for label, _command, path in rows if label.lower().startswith("alias ")]
    assert len(alias_rows) == 3, "README must expose exactly three alias direct single-file rows"

    required_tokens_by_label = {
        "Alias rewrite contract unit (direct)": {"alias", "rewrite", "contract"},
        "Alias rewrite real-app contract unit (direct)": {"alias", "rewrite", "real", "app"},
        "Alias unsupported rationale contract (direct)": {"alias", "unsupported", "rationale"},
    }

    for label, path in alias_rows:
        assert label in required_tokens_by_label, f"Unexpected alias direct row label: {label}"
        slug_tokens = _normalized_slug_tokens(path)
        missing = sorted(token for token in required_tokens_by_label[label] if token not in slug_tokens)
        assert not missing, (
            f"Alias row '{label}' path '{path}' missing required alias-family tokens: {', '.join(missing)}"
        )
