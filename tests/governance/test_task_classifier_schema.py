from pathlib import Path

import pytest

from thegent.governance.task_classifier_schema import load_task_classifier_schema


def test_load_task_classifier_schema_default() -> None:
    schema = load_task_classifier_schema()
    assert schema["version"] == 1
    assert "domain" in schema["fields"]
    assert "worktree_mode" in schema["outputs"]


def test_load_task_classifier_schema_invalid_version(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("version: 0\nfields: {}\noutputs: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="version must be >= 1"):
        load_task_classifier_schema(schema_path)


def test_load_task_classifier_schema_missing_keys(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("version: 1\nfields: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing keys"):
        load_task_classifier_schema(schema_path)


def test_load_task_classifier_schema_rejects_non_dict_payload(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text("- just: a\n- list", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid classifier schema payload type"):
        load_task_classifier_schema(schema_path)


def test_load_task_classifier_schema_rejects_bad_schema_contract(
    tmp_path: Path,
) -> None:
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text(
        """
        version: 0
        fields:
          task_id:
            type: unsupported
            required: true
        outputs:
          worktree_mode:
            type: enum
            values: [L1_direct, L2_managed, L3_specialist, Ln_worker]
            required: true
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="version must be >= 1"):
        load_task_classifier_schema(schema_path)


def test_load_task_classifier_schema_rejects_missing_output_type_flag(
    tmp_path: Path,
) -> None:
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text(
        """
        version: 1
        fields:
          task_id:
            type: string
            required: true
        outputs:
          worktree_mode:
            values: [L1_direct, L2_managed, L3_specialist, Ln_worker]
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="outputs\\.worktree_mode missing required keys: type"):
        load_task_classifier_schema(schema_path)


def test_load_task_classifier_schema_rejects_policy_defaults_with_unknown_scale(
    tmp_path: Path,
) -> None:
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text(
        """
        version: 1
        fields:
          task_id:
            type: string
            required: true
        outputs:
          worktree_mode:
            type: enum
            values: [L1_direct, L2_managed, L3_specialist, Ln_worker]
            required: true
        policy_defaults:
          XS:
            worktree_mode: shared_lane
            commit_mode: single
          S:
            worktree_mode: shared_lane
            commit_mode: micro
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="policy_defaults missing required key 'M'"):
        load_task_classifier_schema(schema_path)
