from __future__ import annotations

from pathlib import Path

from conftest import _load_script_module

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_wl122_max_lines_canonical_path.py"
MODULE = _load_script_module("check_wl122_max_lines_canonical_path", SCRIPT_PATH)


def _ci_with_task_setup(*lines: str) -> str:
    return "steps:\n  - uses: arduino/setup-task@v2\n" + "".join(lines)


def test_build_report_passes_for_canonical_ci_path() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is True
    assert report["errors"] == []
    assert report["warnings"] == []
    assert report["canonical_invocations"] == 1


def test_build_report_fails_on_direct_script_call() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup("  - run: sh scripts/max-lines-gate.sh\n"),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n"
            "  - repo: local\n"
            "    hooks:\n"
            "      - id: max-lines-gate\n"
            "        entry: sh scripts/max-lines-gate.sh\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow does not invoke `task quality:max-lines`." in report["errors"]
    assert "CI workflow must not call scripts/max-lines-gate.sh directly." in report["errors"]
    assert ".pre-commit-config.yaml max-lines hook must invoke `task quality:max-lines`." in report["errors"]
    assert ".pre-commit-config.yaml must not call scripts/max-lines-gate.sh directly." in report["errors"]


def test_build_report_fails_when_canonical_invocation_occurs_more_than_once() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: task quality:max-lines\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow must invoke `task quality:max-lines` exactly once (found 2)." in report["errors"]


def test_build_report_fails_when_ci_contract_checker_step_is_missing() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow must run WL-122 canonical-path checker in strict mode." in report["errors"]


def test_build_report_fails_when_wl117_metadata_checker_is_missing() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow must run WL-117 extension metadata checker in strict mode." in report["errors"]


def test_build_report_fails_when_wl117_checker_runs_after_max_lines() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: task quality:max-lines\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow must run WL-117 metadata checker before WL-122 max-lines gate." in report["errors"]


def test_build_report_fails_when_wl122_checker_runs_after_wl117_checker() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow must run WL-122 checker before WL-117 metadata checker." in report["errors"]


def test_build_report_fails_when_wl117_checker_is_duplicated() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow must run WL-117 extension metadata checker exactly once." in report["errors"]


def test_build_report_fails_when_task_setup_action_is_missing() -> None:
    report = MODULE.build_report(
        ci_text=(
            "steps:\n"
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n  - repo: local\n    hooks:\n      - id: max-lines-gate\n        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert "CI workflow must install Task runner via `arduino/setup-task@v2` before max-lines gate." in report["errors"]


def test_build_report_fails_when_precommit_hook_is_duplicated() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n"
            "  - repo: local\n"
            "    hooks:\n"
            "      - id: max-lines-gate\n"
            "        entry: task quality:max-lines\n"
            "      - id: max-lines-gate\n"
            "        entry: task quality:max-lines\n"
        ),
    )
    assert report["ok"] is False
    assert ".pre-commit-config.yaml must declare `max-lines-gate` hook exactly once." in report["errors"]


def test_build_report_fails_when_precommit_entry_has_extra_arguments() -> None:
    report = MODULE.build_report(
        ci_text=_ci_with_task_setup(
            "  - run: uv run python scripts/check_wl122_max_lines_canonical_path.py --strict\n"
            "  - run: uv run python scripts/check_extension_package_metadata.py --strict\n"
            "  - run: task quality:max-lines\n"
        ),
        taskfile_text="tasks:\n  quality:max-lines:\n    cmds:\n      - sh scripts/max-lines-gate.sh\n",
        precommit_text=(
            "repos:\n"
            "  - repo: local\n"
            "    hooks:\n"
            "      - id: max-lines-gate\n"
            "        entry: task quality:max-lines --verbose\n"
        ),
    )
    assert report["ok"] is False
    assert ".pre-commit-config.yaml max-lines hook must invoke `task quality:max-lines`." in report["errors"]


# noqa: PT018
