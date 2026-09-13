from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "sharecli_boundary_drift_check.py"
)
SPEC = importlib.util.spec_from_file_location(
    "sharecli_boundary_drift_check", SCRIPT_PATH
)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_config(root: Path, body: str) -> Path:
    config_path = root / "config" / "sharecli_boundary_drift_allowlist.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(body.strip() + "\n", encoding="utf-8")
    return config_path


def _write_python(root: Path, relative_path: str, source: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")
    return path


def test_allowlisted_violation_is_warning_and_advisory_exit_zero(
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [sharecli_boundary]
        enforced_lanes = []

        [[sharecli_boundary.allow]]
        path = "src/thegent/governance/policy.py"
        symbol = "thegent.mesh.sandbox"
        lane = "execution-safety"
        sunset_gate = "execution safety adapter lands"
        reason = "fixture"
        """,
    )
    _write_python(
        tmp_path,
        "src/thegent/governance/policy.py",
        "from thegent.mesh.sandbox import Sandboxing\n",
    )

    findings = MODULE.collect_findings(tmp_path, config_path)
    exit_code = MODULE.main(["--root", str(tmp_path), "--config", str(config_path)])

    assert exit_code == 0
    assert len(findings) == 1
    assert findings[0].severity == "warn"
    assert findings[0].allowlisted is True
    assert findings[0].sunset_gate == "execution safety adapter lands"


def test_enforced_lane_unallowlisted_violation_fails_in_strict_mode(
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [sharecli_boundary]
        enforced_lanes = ["queue"]
        """,
    )
    _write_python(
        tmp_path,
        "src/thegent/mesh/mesh.py",
        "from thegent.mesh.task_queue import MaildirQueue\n",
    )

    findings = MODULE.collect_findings(tmp_path, config_path)
    exit_code = MODULE.main(
        ["--root", str(tmp_path), "--config", str(config_path), "--strict"]
    )

    assert exit_code == 1
    assert len(findings) == 1
    assert findings[0].severity == "fail"
    assert findings[0].lane == "queue"
    assert findings[0].allowlisted is False


def test_legacy_cli_share_import_is_rejected(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path, '[sharecli_boundary]\nenforced_lanes = ["queue"]'
    )
    _write_python(tmp_path, "src/thegent/mesh/cli.py", "import thegent_cli_share\n")
    findings = MODULE.collect_findings(tmp_path, config_path)
    assert len(findings) == 1
    assert findings[0].severity == "fail"


def test_json_payload_contains_required_finding_fields(tmp_path: Path, capsys) -> None:
    config_path = _write_config(
        tmp_path,
        """
        [sharecli_boundary]
        enforced_lanes = ["process-health"]
        """,
    )
    _write_python(
        tmp_path,
        "src/thegent/mesh/agent_patterns.py",
        "from thegent.mesh.process_detection import detect_agents\n",
    )

    exit_code = MODULE.main(
        ["--root", str(tmp_path), "--config", str(config_path), "--format", "json"]
    )
    payload = json.loads(capsys.readouterr().out)
    finding = payload["findings"][0]

    assert exit_code == 0
    assert finding == {
        "allowlisted": False,
        "lane": "process-health",
        "line": 1,
        "path": "src/thegent/mesh/agent_patterns.py",
        "pattern": "thegent.mesh.process_detection",
        "severity": "fail",
        "sunset_gate": "",
    }


def test_docs_paths_are_ignored(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path, '[sharecli_boundary]\nenforced_lanes = ["queue"]'
    )
    _write_python(
        tmp_path,
        "docs/example.py",
        "from thegent.mesh.task_queue import MaildirQueue\n",
    )

    findings = MODULE.collect_findings(tmp_path, config_path)

    assert findings == []


def test_native_harness_file_growth_is_classified(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, "[sharecli_boundary]\nenforced_lanes = []")
    native_file = tmp_path / "crates" / "harness-native" / "src" / "dispatcher.rs"
    native_file.parent.mkdir(parents=True)
    native_file.write_text("fn main() {}\n", encoding="utf-8")

    findings = MODULE.collect_findings(tmp_path, config_path)

    assert len(findings) == 1
    assert findings[0].path == "crates/harness-native/src/dispatcher.rs"
    assert findings[0].lane == "native-harness"
    assert findings[0].pattern == "crates/harness-native"
    assert findings[0].severity == "info"
