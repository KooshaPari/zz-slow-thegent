# mcp_tools_modes API Reference

> **Source**: `src/thegent/mcp_tools_modes.py`

MCP tools for Plan, Delegate, Discussion, Research, Validation modes and protocols.

Supports structured agent work: plans, elicitation briefs, research reports,
validation checklists, and mode-aware team orchestration.

---

## register_modes

```python
register_modes(mcp: FastMCP)
```

Register Plan, Delegate, Discussion, Research, Validation, and Protocol tools.

---

## thegent_dag_ready

```python
thegent_dag_ready(cd: Any)
```

List DAG task IDs that are ready (pending with all deps Union[done, cancelled]|skipped).

Use before thegent_dag_run to see what can be spawned.

---

## thegent_dag_recover

```python
thegent_dag_recover(cd: Any, action: str)
```

Perform recovery playbook actions on the DAG.

action: retry-Union[failed, clear]-Union[stuck, reset]-Union[retries, fallback].

---

## thegent_dag_run

```python
thegent_dag_run(cd: Any, dry_run: bool, task: Any, max_parallel: Any, lane: Any)
```

Spawn agents for ready DAG tasks. Use thegent_dag_ready first to see ready tasks.

dry_run: list what would run without spawning. task: run only this task id.
max_parallel: cap concurrent running tasks.

---

## thegent_dag_sync

```python
thegent_dag_sync(cd: Any, auto_run_next: bool)
```

Sync DAG task status from session exit (running -> done/failed).

auto_run_next: spawn next ready tasks after sync (auto-spawn loop).

---

## thegent_discussion_add_question

```python
thegent_discussion_add_question(session_id: str, question: str, answer: Any)
```

Add a question (and optional answer) to a discussion session.

Use after thegent_discussion_start. Call thegent_discussion_finalize to save the brief.

---

## thegent_discussion_finalize

```python
thegent_discussion_finalize(brief_content: str, brief_id: Any, cd: Any)
```

Save elicitation brief to docs/briefs/. Use after discussion/elicitation phase.

---

## thegent_discussion_start

```python
thegent_discussion_start(topic: str, cd: Any)
```

Start a discussion/elicitation session. Returns session_id for thegent_discussion_add_question.

---

## thegent_plan_approve

```python
thegent_plan_approve(plan_id: str, cd: Any)
```

Mark plan as approved. Writes approval marker (e.g. .approved) for downstream automation.

---

## thegent_plan_create

```python
thegent_plan_create(prompt: str, plan_id: Any, brief_path: Any, cd: Any)
```

Create a new plan file from a prompt. Writes a structured template to docs/plans/.

Optionally reference brief_path (e.g. docs/briefs/ELICIT_xxx.md) for context.

---

## thegent_plan_get

```python
thegent_plan_get(plan_id: Any, cd: Any)
```

Get plan content by ID or path. If plan_id is a path, read it. Else find in docs/plans/.

---

## thegent_plan_save

```python
thegent_plan_save(content: str, plan_id: Any, cd: Any)
```

Save plan content to docs/plans/. plan_id becomes filename (e.g. PLAN_oauth2.md).

---

## thegent_plan_status

```python
thegent_plan_status(cd: Any)
```

Get current plan status: plan file path, approval state, last modified.

Use when agent needs to know if a plan exists or where it is.

---

## thegent_protocol_get

```python
thegent_protocol_get(mode: Any, name: Any, cd: Any)
```

Get protocol content by mode (discussion, research, validation) or name.

---

## thegent_protocol_list

```python
thegent_protocol_list(cd: Any)
```

List available protocols from .thegent/protocols/.

Returns protocol names and modes (discussion, research, validation).

---

## thegent_research_finalize

```python
thegent_research_finalize(report_content: str, report_id: Any, cd: Any)
```

Save research report to docs/research/. Use after research phase.

---

## thegent_team_create

```python
thegent_team_create(prompt: str, mode: str, teammates: int, cd: Any)
```

Create a team record for orchestration. mode: normal, discussion, research, plan, delegate, validation.

Returns team_id. Use thegent_team_delegate to assign work to teammates.

---

## thegent_team_delegate

```python
thegent_team_delegate(teammate_id: str, prompt: str, parent_run_id: Any)
```

Delegate a task to a teammate. Uses TeammateManager. teammate_id from agents/\*.md.

---

## thegent_team_list

```python
thegent_team_list(cd: Any)
```

List teams and delegations. Returns active teams and TeammateManager delegations.

---

## thegent_validation_report

```python
thegent_validation_report(cd: Any, protocol: Any)
```

Get validation report if one exists. Use after validation phase.

protocol: optional protocol name to load checklist from.

---
