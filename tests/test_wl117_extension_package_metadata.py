from __future__ import annotations

from pathlib import Path

import orjson as json

from conftest import _load_script_module

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_extension_package_metadata.py"
MODULE = _load_script_module("check_extension_package_metadata", SCRIPT_PATH)


def _write_valid_extension(root: Path, name: str = "vscode") -> Path:
    extension_dir = root / name
    src_dir = extension_dir / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "extension.ts").write_text("export function activate() {}\n", encoding="utf-8")
    package = {
        "name": "thegent-vscode",
        "displayName": "thegent",
        "description": "VS Code client scaffold",
        "version": "0.0.1",
        "engines": {"vscode": "^1.95.0"},
        "activationEvents": ["onCommand:thegent.startSession"],
        "main": "./src/extension.ts",
        "contributes": {
            "commands": [
                {"command": "thegent.startSession", "title": "thegent: Start Session"},
            ]
        },
        "scripts": {
            "lint": "eslint src --ext ts",
            "test": "node ./out/tests.js",
        },
    }
    (extension_dir / "package.json").write_text(json.dumps(package).decode(), encoding="utf-8")
    (extension_dir / "README.md").write_text(
        "## Run Steps\n\n```bash\nnpm run lint\nnpm run test\n```\n",
        encoding="utf-8",
    )
    return extension_dir


def test_validate_extension_package_passes_for_valid_package(tmp_path: Path) -> None:
    extension_dir = _write_valid_extension(tmp_path)
    errors = MODULE.validate_extension_package(extension_dir)
    assert errors == []


def test_validate_extension_package_flags_missing_activation_event(
    tmp_path: Path,
) -> None:
    extension_dir = _write_valid_extension(tmp_path)
    package_path = extension_dir / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["activationEvents"] = []
    package_path.write_text(json.dumps(package).decode(), encoding="utf-8")

    errors = MODULE.validate_extension_package(extension_dir)
    assert any("`activationEvents` must be a non-empty list" in error for error in errors)


def test_build_report_checks_all_extension_directories(tmp_path: Path) -> None:
    _write_valid_extension(tmp_path, "vscode")
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "package.json").write_text("{}", encoding="utf-8")

    report = MODULE.build_report(tmp_path)
    assert report["ok"] is False
    assert sorted(report["checked_extensions"]) == ["broken", "vscode"]
    assert any("`name` must be a non-empty string" in error for error in report["errors"])


def test_validate_extension_package_flags_missing_readme_script_reference(
    tmp_path: Path,
) -> None:
    extension_dir = _write_valid_extension(tmp_path)
    (extension_dir / "README.md").write_text(
        "## Run Steps\n\n```bash\nnpm run lint\nnpm run package\n```\n",
        encoding="utf-8",
    )

    errors = MODULE.validate_extension_package(extension_dir)
    assert any("package.json lacks scripts.package" in error for error in errors)


def test_validate_extension_package_rejects_duplicate_command_ids(
    tmp_path: Path,
) -> None:
    extension_dir = _write_valid_extension(tmp_path)
    package_path = extension_dir / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["contributes"]["commands"].append(
        {"command": "thegent.startSession", "title": "thegent: Duplicate Start Session"}
    )
    package_path.write_text(json.dumps(package).decode(), encoding="utf-8")

    errors = MODULE.validate_extension_package(extension_dir)
    assert any("duplicate contributes.commands command id `thegent.startSession`" in error for error in errors)


def test_validate_extension_package_requires_lint_and_test_run_steps(
    tmp_path: Path,
) -> None:
    extension_dir = _write_valid_extension(tmp_path)
    (extension_dir / "README.md").write_text(
        "## Run Steps\n\n```bash\nnpm run lint\n```\n",
        encoding="utf-8",
    )

    errors = MODULE.validate_extension_package(extension_dir)
    assert any("Run Steps must include `npm run test`" in error for error in errors)


def test_validate_extension_package_requires_lint_before_test_in_run_steps(
    tmp_path: Path,
) -> None:
    extension_dir = _write_valid_extension(tmp_path)
    (extension_dir / "README.md").write_text(
        "## Run Steps\n\n```bash\nnpm run test\nnpm run lint\n```\n",
        encoding="utf-8",
    )

    errors = MODULE.validate_extension_package(extension_dir)
    assert any("Run Steps must list `npm run lint` before `npm run test`" in error for error in errors)


def test_validate_extension_package_rejects_duplicate_run_step_commands(
    tmp_path: Path,
) -> None:
    extension_dir = _write_valid_extension(tmp_path)
    (extension_dir / "README.md").write_text(
        "## Run Steps\n\n```bash\nnpm run lint\nnpm run test\nnpm run lint\n```\n",
        encoding="utf-8",
    )

    errors = MODULE.validate_extension_package(extension_dir)
    assert any("Run Steps must not repeat the same `npm run <script>` command" in error for error in errors)


# noqa: PT018
