from __future__ import annotations

from pathlib import Path

import orjson as json
import yaml

from conftest import _load_script_module

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "check_thegent_core_boundary.py"
)
MODULE = _load_script_module("check_thegent_core_boundary", SCRIPT_PATH)
ROOT = Path(__file__).resolve().parents[1]


def _write_boundary_config(path: Path) -> None:
    path.write_text(
        """
[core_boundary]

[core_boundary.allow]
imports = ["thegent.core", "thegent.queue", "thegent.config"]

[core_boundary.block]
imports = ["thegent"]
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_run_check_passes_for_allowed_imports(tmp_path: Path) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)

    (core_dir / "ok.py").write_text(
        "import thegent.core.worker_pool\nfrom thegent.queue import enqueue\n",
        encoding="utf-8",
    )

    is_ok, violations = MODULE.run_check(core_dir=core_dir, config_path=config_path)

    assert is_ok is True
    assert violations == []


def test_run_check_flags_blocked_and_disallowed_imports(tmp_path: Path) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)

    (core_dir / "bad.py").write_text(
        "import thegent\nfrom thegent.mcp import server\n",
        encoding="utf-8",
    )

    is_ok, violations = MODULE.run_check(core_dir=core_dir, config_path=config_path)

    assert is_ok is False
    assert any("blocked import 'thegent'" in msg for msg in violations)
    assert any("blocked import 'thegent.mcp'" in msg for msg in violations)


def test_extract_imports_ignores_relative_imports(tmp_path: Path) -> None:
    py_path = tmp_path / "sample.py"
    py_path.write_text(
        "from .local import helper\nfrom thegent.core import rules_sync\n",
        encoding="utf-8",
    )

    imports = MODULE._extract_imports(py_path)

    assert imports == ["thegent.core"]


def test_main_advisory_mode_returns_zero_on_violations(tmp_path: Path) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)
    (core_dir / "bad.py").write_text("import thegent\n", encoding="utf-8")

    exit_code = MODULE.main(["--core-dir", str(core_dir), "--config", str(config_path)])

    assert exit_code == 0


def test_main_strict_mode_returns_nonzero_on_violations(tmp_path: Path) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)
    (core_dir / "bad.py").write_text("import thegent\n", encoding="utf-8")

    exit_code = MODULE.main(
        ["--core-dir", str(core_dir), "--config", str(config_path), "--strict"]
    )

    assert exit_code == 1


def test_main_json_format_emits_machine_readable_payload(
    tmp_path: Path, capsys
) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)
    (core_dir / "bad.py").write_text("import thegent\n", encoding="utf-8")

    exit_code = MODULE.main(
        ["--core-dir", str(core_dir), "--config", str(config_path), "--format", "json"]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["mode"] == "advisory"
    assert payload["violation_count"] == 1
    assert payload["file_count"] == 1
    assert payload["import_count"] == 1


def test_build_report_contains_policy_and_scan_counts(tmp_path: Path) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)
    (core_dir / "ok.py").write_text(
        "from thegent.core import worker_pool\n", encoding="utf-8"
    )

    report = MODULE.build_report(core_dir=core_dir, config_path=config_path)

    assert report["ok"] is True
    assert report["allowed_prefixes"] == [
        "thegent.core",
        "thegent.queue",
        "thegent.config",
    ]
    assert report["blocked_prefixes"] == ["thegent"]
    assert report["file_count"] == 1
    assert report["import_count"] == 1


def test_main_summary_json_format_emits_compact_counts(tmp_path: Path, capsys) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)
    (core_dir / "bad.py").write_text("import thegent\n", encoding="utf-8")

    exit_code = MODULE.main(
        [
            "--core-dir",
            str(core_dir),
            "--config",
            str(config_path),
            "--format",
            "summary-json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "blocked_count": 1,
        "clean_file_count": 0,
        "disallowed_count": 0,
        "file_count": 1,
        "import_count": 1,
        "mode": "advisory",
        "ok": False,
        "violation_count": 1,
        "violation_file_count": 1,
    }


def test_build_summary_payload_includes_expected_keys() -> None:
    report = {
        "ok": False,
        "violation_count": 2,
        "file_count": 3,
        "import_count": 7,
        "violations": [
            "src/thegent/core/a.py: blocked import 'thegent.mcp'",
            "src/thegent/core/b.py: disallowed import 'thegent.tools'",
        ],
    }

    payload = MODULE.build_summary_payload(report, "strict")

    assert payload == {
        "blocked_count": 1,
        "clean_file_count": 1,
        "disallowed_count": 1,
        "ok": False,
        "mode": "strict",
        "violation_count": 2,
        "violation_file_count": 2,
        "file_count": 3,
        "import_count": 7,
    }


def test_build_violation_kind_counts_splits_blocked_and_disallowed() -> None:
    report = {
        "violations": [
            "src/thegent/core/a.py: blocked import 'thegent.mcp'",
            "src/thegent/core/b.py: disallowed import 'thegent.tools'",
            "src/thegent/core/c.py: blocked import 'thegent'",
        ]
    }

    blocked_count, disallowed_count = MODULE.build_violation_kind_counts(report)

    assert blocked_count == 2
    assert disallowed_count == 1


def test_build_violation_file_count_deduplicates_file_paths() -> None:
    report = {
        "violations": [
            "src/thegent/core/a.py: blocked import 'thegent.mcp'",
            "src/thegent/core/a.py: blocked import 'thegent'",
            "src/thegent/core/b.py: disallowed import 'thegent.tools'",
        ]
    }

    count = MODULE.build_violation_file_count(report)

    assert count == 2


def test_build_clean_file_count_subtracts_violation_files_from_total() -> None:
    report = {
        "file_count": 5,
        "violations": [
            "src/thegent/core/a.py: blocked import 'thegent.mcp'",
            "src/thegent/core/b.py: disallowed import 'thegent.tools'",
        ],
    }

    count = MODULE.build_clean_file_count(report)

    assert count == 3


def test_build_json_payload_adds_mode_to_report() -> None:
    report = {"ok": True, "violation_count": 0}

    payload = MODULE.build_json_payload(report, "advisory")

    assert payload == {"ok": True, "violation_count": 0, "mode": "advisory"}


def test_build_violation_entries_returns_ordered_jsonl_payload() -> None:
    report = {"violations": ["src/thegent/core/a.py: blocked import 'thegent.mcp'"]}

    entries = MODULE.build_violation_entries(report)

    assert entries == [
        {
            "kind": "violation",
            "message": "src/thegent/core/a.py: blocked import 'thegent.mcp'",
        }
    ]


def test_main_violations_jsonl_format_emits_line_delimited_entries(
    tmp_path: Path, capsys
) -> None:
    core_dir = tmp_path / "src" / "thegent" / "core"
    core_dir.mkdir(parents=True)
    config_path = tmp_path / "boundary.toml"
    _write_boundary_config(config_path)
    (core_dir / "bad.py").write_text("import thegent\n", encoding="utf-8")

    exit_code = MODULE.main(
        [
            "--core-dir",
            str(core_dir),
            "--config",
            str(config_path),
            "--format",
            "violations-jsonl",
        ]
    )

    assert exit_code == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    assert lines == [{"kind": "violation", "message": lines[0]["message"]}]
    assert lines[0]["message"].endswith(
        "src/thegent/core/bad.py: blocked import 'thegent'"
    )


def test_wl121_ci_uses_strict_mode_and_local_task_stays_advisory() -> None:
    qa_guide = (ROOT / "docs/guides/QUALITY_ASSURANCE.md").read_text(encoding="utf-8")
    taskfile = yaml.safe_load((ROOT / "Taskfile.yml").read_text(encoding="utf-8"))

    assert "task quality:core-boundary:strict" in qa_guide
    assert "check_thegent_core_boundary.py --format violations-jsonl" in qa_guide
    assert (
        "{ok, mode, violation_count, violation_file_count, clean_file_count, blocked_count, "
        "disallowed_count, file_count, import_count}"
    ) in qa_guide
    assert (
        "| allow | `thegent.core` | `from thegent.core import prompt_queue` | Allowed |"
        in qa_guide
    )
    assert (
        "| block | `thegent` | `from thegent.mcp import server` | Blocked unless also allowlisted |"
        in qa_guide
    )
    assert taskfile["tasks"]["quality:core-boundary"]["cmds"] == [
        "uv run python scripts/check_thegent_core_boundary.py"
    ]
