from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from thegent.cli.commands import impl
from thegent.cli.commands.dag_impl import DagDocument


def test_wrapper_parse_dag_full_delegates(tmp_path: Path) -> None:
    dag_path = tmp_path / "dag-session.md"
    expected = DagDocument(
        frontmatter={},
        tasks=[],
        before_table="",
        after_table="",
        table_headers=["id", "agent", "prompt", "depends_on", "status"],
    )
    with patch("thegent.cli.services.run_dag_helpers.parse_dag_full", return_value=expected) as mock_fn:
        result = impl._parse_dag_full(dag_path)
    mock_fn.assert_called_once_with(dag_path)
    assert result is expected


def test_wrapper_dag_update_task_delegates_kwargs() -> None:
    doc = DagDocument(
        frontmatter={},
        tasks=[],
        before_table="",
        after_table="",
        table_headers=["id", "agent", "prompt", "depends_on", "status"],
    )
    with patch("thegent.cli.services.run_dag_helpers.dag_update_task", return_value=True) as mock_fn:
        result = impl._dag_update_task(
            doc,
            "T1",
            status="running",
            session_id="sess-1",
            prompt="Do work",
            agent="codex",
            depends_on="T0",
            retry_count=2,
            contract_version="1.0.0",
        )
    mock_fn.assert_called_once_with(
        doc=doc,
        task_id="T1",
        status="running",
        session_id="sess-1",
        prompt="Do work",
        agent="codex",
        depends_on="T0",
        retry_count=2,
        contract_version="1.0.0",
    )
    assert result is True


def test_parse_and_validate_path_functional(tmp_path: Path) -> None:
    dag_path = tmp_path / "dag-session.md"
    dag_path.write_text(
        (
            "---\n"
            "version: 1\n"
            "project: demo\n"
            "owner: test\n"
            "---\n"
            "# DAG Session\n\n"
            "## Tasks\n\n"
            "| id | agent | prompt | depends_on | status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| T1 |  | Do a thing | — | pending |\n"
        ),
        encoding="utf-8",
    )

    doc = impl._parse_dag_full(dag_path)
    errors = impl._validate_dag(doc)

    assert doc.tasks[0]["id"] == "T1"
    assert errors == []
