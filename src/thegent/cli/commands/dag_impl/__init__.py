"""DAG implementation module (AUDIT-N+11: refactored from impl.py).

This module owns the canonical :class:`DagDocument` dataclass and the
DAG parsing/validation/helpers extracted from ``cli.commands.impl``.
The :mod:`thegent.cli.services.run_dag_helpers` module re-exports the
public symbols; ``cli.commands.impl`` delegates to those wrappers so
the WL-125 monkeypatch sites resolve.

AUDIT-N+19 (Phase 4 wiring): this module now owns the full DAG helper
surface (cycle detection, atomic write, evidence/contract-version
header insertion, agent-aware validation, ``_dag_path`` resolution,
``dag_list_impl`` / ``dag_raw_impl``, ``_resolve_prompt``). The legacy
stubs in :mod:`thegent.cli.commands.impl` delegate here.
"""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# AUDIT-N+19 Phase 4: re-export ThegentSettings at module level so
# `@patch("thegent.cli.commands.dag_impl.ThegentSettings")` resolves.
# This is a lazy proxy: we re-export the actual class from thegent.config.
try:  # pragma: no cover - import guard for partial installs
    from thegent.config import ThegentSettings as _ThegentSettings
except Exception:  # pragma: no cover - keep optional
    _ThegentSettings = None  # type: ignore[assignment]


# Alias so tests can patch either name. `_parse_dag_full` is defined later
# in this module; the name binding is finalized at function-definition time.
ThegentSettings = _ThegentSettings


@dataclass
class DagDocument:
    """Parsed DAG session document.

    Attributes:
        frontmatter: YAML frontmatter key/value pairs (raw, pre-parse).
        tasks: Parsed task rows (one per table row, dict).
        before_table: Markdown body before the tasks table.
        after_table: Markdown body after the tasks table.
        table_headers: Column headers from the first table row.
    """

    frontmatter: dict[str, Any] = field(default_factory=dict)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    before_table: str = ""
    after_table: str = ""
    table_headers: list[str] = field(default_factory=list)


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    """Parse YAML-style ``---\\nkey: value\\n---\\n`` frontmatter from ``raw``.

    Returns ``(frontmatter, remainder)`` where ``remainder`` is the body
    after the closing ``---``. Falls back to ``({},"<raw>")`` when no
    frontmatter block is found.
    """
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    block = match.group(1)
    frontmatter: dict[str, Any] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()
    return frontmatter, raw[match.end() :]


def _parse_dag_full(path: Path) -> DagDocument:
    """Parse a DAG session markdown file at ``path`` into a :class:`DagDocument`.

    The file is expected to have an optional YAML-style frontmatter block
    followed by a markdown body that contains a single tasks table::

        ---
        version: 1
        ---
        # DAG Session

        ## Tasks

        | id | agent | prompt | depends_on | status |
        | --- | --- | --- | --- | --- |
        | T1 | codex | Do work | — | pending |
    """
    raw = Path(path).read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(raw)

    if "|" in body:
        before_table = body[: body.find("|")]
        table_block = body[body.find("|") :]
    else:
        before_table = body
        table_block = ""

    after_table = ""
    tasks: list[dict[str, Any]] = []
    headers: list[str] = []
    rows = [row for row in table_block.splitlines() if row.strip().startswith("|")]
    if rows:
        headers = [cell.strip().lower() for cell in rows[0].strip().strip("|").split("|")]
        data_rows = [r for r in rows[1:] if not re.match(r"^\|\s*-+", r.strip())]
        for row in data_rows:
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) != len(headers):
                continue
            tasks.append({headers[i]: cells[i] for i in range(len(headers))})

    return DagDocument(
        frontmatter=frontmatter,
        tasks=tasks,
        before_table=before_table,
        after_table=after_table,
        table_headers=headers,
    )


def _serialize_dag(doc: DagDocument) -> str:
    """Render a :class:`DagDocument` back into markdown."""
    lines: list[str] = []
    if doc.frontmatter:
        lines.append("---")
        for key, value in doc.frontmatter.items():
            lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")
    if doc.before_table:
        lines.append(doc.before_table.rstrip("\n"))
        lines.append("")
    if doc.table_headers:
        lines.append("| " + " | ".join(doc.table_headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(doc.table_headers)) + " |")
        for task in doc.tasks:
            cells = [_escape_cell(str(task.get(h, ""))) for h in doc.table_headers]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    if doc.after_table:
        lines.append(doc.after_table)
    return "\n".join(lines).rstrip("\n") + "\n"


def _parse_dag_session(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return ``(frontmatter, tasks)`` for the DAG at ``path``."""
    doc = _parse_dag_full(path)
    return doc.frontmatter, doc.tasks


def _validate_task_id(task_id: str) -> str | None:
    """Return an error string if ``task_id`` is not a valid DAG task id."""
    if not task_id or not isinstance(task_id, str):
        return "Task id must be a non-empty string"
    if not re.match(r"^[A-Za-z0-9_\-]+$", task_id):
        return f"Task id {task_id!r} contains invalid characters"
    return None


def _validate_agent(agent: str) -> str | None:
    """Return an error string if ``agent`` is not a known backend."""
    if not agent or not isinstance(agent, str):
        return "Agent must be a non-empty string"
    # Lazy import so we don't bind at module import time. Test patches
    # ``thegent.cli.commands.dag_impl.resolve_agent`` / ``list_agent_names``
    # so the resolve call must resolve to *this* module's attributes on
    # every invocation (live-lookup).
    import sys as _sys

    mod = _sys.modules[__name__]
    list_agent_names = getattr(mod, "list_agent_names", None)
    resolve_agent = getattr(mod, "resolve_agent", None)
    if list_agent_names is None or resolve_agent is None:
        # Module-level attributes not yet populated — fall back to
        # registry imports.
        from thegent.agents.registry import list_agent_names as _list
        from thegent.agents.registry import resolve_agent as _resolve

        list_agent_names = _list
        resolve_agent = _resolve
    try:
        names = list_agent_names()
        if names and agent not in names:
            return f"Unknown agent {agent!r}"
    except Exception:  # pragma: no cover - defensive
        return None
    return None


# ---------------------------------------------------------------------------
# Module-level ``list_agent_names`` / ``resolve_agent`` shims so that
# ``@patch("thegent.cli.commands.dag_impl.list_agent_names", ...)`` and
# ``@patch("thegent.cli.commands.dag_impl.resolve_agent", ...)`` mock
# targets resolve to module attributes (rather than failing with
# ``AttributeError``). Default to the registry implementations.
# ---------------------------------------------------------------------------
try:
    from thegent.agents.registry import (
        list_agent_names,  # noqa: F401
        resolve_agent,  # noqa: F401
    )
except Exception:  # pragma: no cover - defensive

    def list_agent_names() -> list[str]:  # type: ignore[no-redef]
        return []

    def resolve_agent(name: str) -> Any:  # type: ignore[no-redef]
        return None


def _parse_depends_on(depends_on: Any) -> list[str]:
    """Normalize a ``depends_on`` field into a list of dependency ids."""
    if depends_on is None:
        return []
    if isinstance(depends_on, str):
        # Strip em/en-dashes and "-" sentinel so legacy "-", "—", "—"
        # all normalize to an empty list.
        cleaned = depends_on.replace("\u2014", "").replace("\u2013", "").replace("—", "").replace("-", "")
        return [d.strip() for d in cleaned.split(",") if d.strip()]
    if isinstance(depends_on, list):
        return [str(d) for d in depends_on if d]
    return []


def _get_ready_task_ids(tasks: list[dict[str, Any]]) -> list[str]:
    """Return ids of tasks whose dependencies are all satisfied.

    A task is "ready" iff:

      * ``status`` is ``"pending"``
      * every dependency listed in ``depends_on`` has ``status == "done"``
    """
    completed = {t.get("id") for t in tasks if t.get("status") == "done"}
    ready: list[str] = []
    for task in tasks:
        if task.get("status") != "pending":
            continue
        deps = _parse_depends_on(task.get("depends_on"))
        if all(dep in completed for dep in deps):
            ready.append(task.get("id", ""))
    return [r for r in ready if r]


def _validate_dag(doc: DagDocument) -> list[str]:
    """Validate a :class:`DagDocument`; return list of error strings.

    Checks:

      * Unknown task dependencies (``depends on unknown task``)
      * Duplicate task ids (``Duplicate task ID``)
      * Unknown agents (``Unknown agent``)
      * ``done`` tasks missing ``evidence`` / ``session_id``
    """
    errors: list[str] = []
    if not doc.tasks:
        return errors
    seen_ids: set[str] = set()
    for task in doc.tasks:
        tid = task.get("id", "")
        if tid in seen_ids:
            errors.append(f"Duplicate task ID {tid!r}")
        seen_ids.add(tid)
    task_ids = {t.get("id") for t in doc.tasks if t.get("id")}
    for task in doc.tasks:
        deps = _parse_depends_on(task.get("depends_on"))
        for dep in deps:
            if dep not in task_ids:
                errors.append(f"Task {task.get('id')!r} depends on unknown task {dep!r}")
        agent = task.get("agent", "")
        agent_err = _validate_agent(agent) if agent else None
        if agent_err:
            errors.append(agent_err)
        status = task.get("status", "")
        if status == "done" and not (task.get("evidence") or task.get("session_id")):
            errors.append(f"Task {task.get('id')!r} has status 'done' but is missing evidence / session_id")
    return errors


def _check_dag_cycles(tasks: list[dict[str, Any]]) -> list[str]:
    """Detect cycles in the dependency graph described by ``tasks``.

    Returns a list of error strings:

      * ``"cycle detected: <id1> -> <id2> -> ... -> <id1>"`` for each
        cycle found.
      * ``"unknown task <id> depends on <dep>"`` for tasks whose
        dependencies reference ids not present in ``tasks``.
    """
    errors: list[str] = []
    task_ids = {t.get("id") for t in tasks if t.get("id")}
    for task in tasks:
        deps = _parse_depends_on(task.get("depends_on"))
        for dep in deps:
            if dep not in task_ids:
                errors.append(f"unknown task {task.get('id')!r} depends on {dep!r}")

    adj: dict[str, list[str]] = {}
    for task in tasks:
        tid = task.get("id")
        if not tid:
            continue
        adj[tid] = _parse_depends_on(task.get("depends_on"))

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = dict.fromkeys(adj, WHITE)
    stack: list[str] = []
    seen_cycles: set[str] = set()

    def dfs(node: str) -> None:
        color[node] = GRAY
        stack.append(node)
        for nxt in adj.get(node, []):
            if nxt not in color:
                continue
            if color[nxt] == GRAY:
                if nxt in stack:
                    idx = stack.index(nxt)
                    cyc = stack[idx:] + [nxt]
                    key = "->".join(cyc)
                    if key not in seen_cycles:
                        seen_cycles.add(key)
                        errors.append(f"cycle detected: {' -> '.join(cyc)}")
            elif color[nxt] == WHITE:
                dfs(nxt)
        stack.pop()
        color[node] = BLACK

    for node in list(color):
        if color[node] == WHITE:
            dfs(node)

    return errors


def _dag_update_task(
    doc: DagDocument,
    task_id: str,
    *,
    status: str | None = None,
    session_id: str | None = None,
    prompt: str | None = None,
    agent: str | None = None,
    depends_on: str | None = None,
    retry_count: int | None = None,
    contract_version: str | None = None,
) -> bool:
    """Apply updates to a task row in ``doc``; return True if found.

    ``session_id`` is mirrored to the ``evidence`` column so downstream
    tooling that consumes the markdown table can recover the session id
    without depending on a hidden column.
    """
    for task in doc.tasks:
        if task.get("id") != task_id:
            continue
        if status is not None:
            task["status"] = status
        if session_id is not None:
            task["session_id"] = session_id
            task["evidence"] = session_id
        if prompt is not None:
            task["prompt"] = prompt
        if agent is not None:
            task["agent"] = agent
        if depends_on is not None:
            task["depends_on"] = depends_on
        if retry_count is not None:
            task["retry_count"] = retry_count
        if contract_version is not None:
            task["contract_version"] = contract_version
        return True
    return False


def _ensure_evidence_header(doc: DagDocument) -> None:
    """Ensure the ``evidence`` column header is present if any task uses it."""
    if any("evidence" in t for t in doc.tasks):
        if "evidence" not in doc.table_headers:
            doc.table_headers.append("evidence")


def _ensure_contract_version_header(doc: DagDocument) -> None:
    """Ensure the ``contract_version`` column header is present if any task uses it."""
    if any("contract_version" in t for t in doc.tasks):
        if "contract_version" not in doc.table_headers:
            doc.table_headers.append("contract_version")


def _escape_cell(value: str) -> str:
    """Escape a table-cell value so it round-trips through markdown.

    Pipes inside a cell must be backslash-escaped, otherwise the
    table breaks when re-serialized.
    """
    if value is None:
        return ""
    text = str(value)
    if "|" in text:
        text = text.replace("|", "\\|")
    text = text.replace("\n", " ").replace("\r", " ")
    return text


def _resolve_prompt(prompt: str | None = None, prompt_file: str | None = None) -> str:
    """Resolve prompt from argument or file."""
    if prompt:
        return prompt
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8")
    return ""


def _atomic_write(path: Path, content: str, *, backup: bool = False) -> None:
    """Atomically write ``content`` to ``path``.

    Writes to a sibling tempfile then ``os.replace`` for atomicity.
    When ``backup=True`` an existing file is copied to ``<path>.bak``
    before the swap.
    """
    target = Path(path)
    if backup and target.exists():
        backup_path = target.with_suffix(target.suffix + ".bak")
        backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".", dir=str(target.parent or "."))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_name, target)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def _ensure_dag_file(path: str | Path) -> DagDocument:
    """Ensure a DAG file exists at ``path`` and return its parsed document.

    If the file does not exist, it is created with an empty markdown
    skeleton (frontmatter + table header) so subsequent writes are
    well-formed. The parsed :class:`DagDocument` is returned either way.
    """
    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        empty = DagDocument(
            frontmatter={},
            tasks=[],
            before_table="## Tasks\n\n",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        _atomic_write(p, _serialize_dag(empty))
        return empty
    return _parse_dag_full(p)


def _dag_path(cwd: Path | None) -> tuple[Path | None, Path | None]:
    """Resolve the canonical DAG document path under ``cwd``.

    Returns ``(cwd, dag_path)``. Both elements are ``None`` when the
    working directory cannot be resolved.
    """
    if cwd is None:
        return None, None
    dag_path = cwd / ".factory" / "dag-session.md"
    return cwd, dag_path


def dag_list_impl(*, cd: Path | None = None) -> dict[str, Any]:
    """Return ``{"tasks": [...], "path": "..."}`` for the DAG at ``cd``.

    Returns ``{"error": "..."}`` when the file does not exist.
    """
    cwd, dag_path = _dag_path(cd)
    if cwd is None or dag_path is None:
        return {"error": "Could not resolve cwd for DAG list"}
    if not dag_path.exists():
        return {"error": f"DAG not found: {dag_path}"}
    doc = _parse_dag_full(dag_path)
    return {"frontmatter": doc.frontmatter, "tasks": doc.tasks, "path": str(dag_path)}


def dag_raw_impl(*, cd: Path | None = None) -> str:
    """Return the raw markdown content of the DAG at ``cd``.

    Returns an ``Error: ...`` string when the file is missing.
    """
    cwd, dag_path = _dag_path(cd)
    if cwd is None or dag_path is None:
        return "Error: could not resolve cwd for DAG raw read"
    if not dag_path.exists():
        return f"Error: DAG not found at {dag_path}"
    return dag_path.read_text(encoding="utf-8")


def dag_ready_impl(cd: Path | None = None) -> dict[str, Any]:
    """List ready task ids in the DAG under ``cd/.factory/dag-session.md``."""
    cwd = cd or Path.cwd()
    dag_path = cwd / ".factory" / "dag-session.md"
    if not dag_path.exists():
        return {"error": f"DAG not found: {dag_path}", "ready": []}
    doc = _parse_dag_full(dag_path)
    return {
        "ready": _get_ready_task_ids(doc.tasks),
        "path": str(dag_path),
    }


def dag_status_impl(cd: Path | None = None) -> dict[str, Any]:
    """Return the status summary for the DAG under ``cd``.

    Returns ``{"tasks": [...], "summary": {...}, "path": "..."}``.
    """
    cwd, dag_path = _dag_path(cd)
    if cwd is None or dag_path is None:
        return {"error": "Could not resolve cwd for DAG status"}
    if not dag_path.exists():
        return {"error": f"DAG not found: {dag_path}"}
    doc = _parse_dag_full(dag_path)
    status_counts: dict[str, int] = {}
    for task in doc.tasks:
        s = task.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    return {
        "tasks": doc.tasks,
        "summary": status_counts,
        "path": str(dag_path),
    }


__all__ = [
    "DagDocument",
    "_parse_dag_full",
    "_serialize_dag",
    "_parse_dag_session",
    "_validate_task_id",
    "_validate_agent",
    "_parse_depends_on",
    "_get_ready_task_ids",
    "_validate_dag",
    "_check_dag_cycles",
    "_dag_update_task",
    "_ensure_evidence_header",
    "_ensure_contract_version_header",
    "_escape_cell",
    "_resolve_prompt",
    "_atomic_write",
    "_ensure_dag_file",
    "_dag_path",
    "dag_list_impl",
    "dag_raw_impl",
    "dag_ready_impl",
    "dag_status_impl",
]
