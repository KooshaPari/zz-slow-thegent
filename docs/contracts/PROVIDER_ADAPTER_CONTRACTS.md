# Provider Adapter Contracts (G-RV-05)

**Purpose:** Document output contracts for copilot, gemini, codex, and claude adapters.
**Date:** 2026-02-14
**Scope:** WBS-X5 Provider Adapter Layer

---

## 1. Overview

Provider adapters normalize raw agent output into `CanonicalStructuredMessage` (CSM). All four primary providers (copilot, gemini, codex, claude) use the same XML-based contract. Adapters are implemented in `src/thegent/contracts/adapters.py`.

| Provider     | Adapter          | Source Contract         | Notes                |
| ------------ | ---------------- | ----------------------- | -------------------- |
| copilot      | XMLOutputAdapter | task-tool-18 / xml-tags | GitHub Copilot CLI   |
| gemini       | XMLOutputAdapter | task-tool-18 / xml-tags | Google Gemini CLI    |
| codex        | XMLOutputAdapter | task-tool-18 / xml-tags | Codex proxy / cursor |
| claude       | XMLOutputAdapter | task-tool-18 / xml-tags | Anthropic Claude CLI |
| cursor-agent | XMLOutputAdapter | task-tool-18 / xml-tags | Cursor agent         |
| antigravity  | XMLOutputAdapter | task-tool-18 / xml-tags | Proxy backend        |

---

## 2. Shared XML Protocol

All providers emit XML tags in stdout. The parser extracts balanced tags `<TAG>content</TAG>` (case-insensitive).

### 2.1 Supported Tags → CSM Mapping

| XML Tag                                        | CSM Field         | Notes                                                                                          |
| ---------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------- |
| STATUS, TASK_STATUS                            | status            | pending, in_progress, completed, failed, blocked, cancelled, done→completed, skipped→cancelled |
| PROGRESS, TASK_PROGRESS, PERCENT_COMPLETE      | progress          | 0–100 or 0.0–1.0; normalized to 0.0–1.0                                                        |
| TASK_ID, TASKID                                | task_id           |                                                                                                |
| OBJECTIVE, TASK_OBJECTIVE                      | objective         |                                                                                                |
| SUMMARY, TASK_SUMMARY, TASK_UPDATE, TASKUPDATE | summary           |                                                                                                |
| ACTIONS_COMPLETED                              | actions_completed | Newline-separated list                                                                         |
| ISSUES, TASK_ISSUES                            | issues            | Newline-separated list                                                                         |
| NEXT_STEPS, TASK_NEXT_STEPS                    | next_steps        | Newline-separated list                                                                         |

### 2.2 Status Normalization

```
pending, in_progress, completed, failed, blocked, cancelled
done → completed
skipped → cancelled
```

---

## 3. Per-Provider Contract Notes

### 3.1 Copilot

- **CLI:** `copilot` (GitHub Copilot CLI)
- **Output:** Stdout with XML tags; same tag set as task-tool-18
- **Fallback:** If no XML tags, `GenericOutputAdapter` or `extract_condensed` yields `source_contract=plain` with confidence 0.7

### 3.2 Gemini

- **CLI:** `gemini` (Google Gemini CLI)
- **Output:** Stdout with XML tags; supports task-tool-18 and zen-rich-v1
- **Fallback:** Same as copilot

### 3.3 Codex

- **CLI:** `cursor agent` or codex proxy
- **Output:** Stdout with XML tags; cursor-agent format compatible with task-tool-18
- **Fallback:** Same as copilot

### 3.4 Claude

- **CLI:** `claude` (Anthropic Claude CLI)
- **Output:** Stdout with XML tags; same tag set as task-tool-18
- **Fallback:** Same as copilot

---

## 4. Adapter Result Contract

Every adapter returns `AdapterResult`:

| Field           | Type                       | Description                                                            |
| --------------- | -------------------------- | ---------------------------------------------------------------------- |
| csm             | CanonicalStructuredMessage | Normalized output                                                      |
| confidence      | float                      | 0.0–1.0; 1.0 = full parse, 0.7 = validation issues, 0.3–0.5 = fallback |
| parse_errors    | list[str]                  | parse_truncated, no_xml_tags_detected, or validation issues            |
| source_provider | str                        | Provider identifier                                                    |

---

## 5. Fallback Behavior

When `normalize_output(..., allow_fallback=True)`:

1. Try registered adapter (XMLOutputAdapter for primary providers)
2. If parse_truncated → return adapter result (do not fall back)
3. If adapter fails or no tags → fallback to `extract_condensed` with `source_contract=fallback-plain`, confidence 0.3–0.5
4. If `allow_fallback=False` → raise `SemanticValidationError`

---

## 6. Implementation Reference

- **Adapters:** `src/thegent/contracts/adapters.py`
- **Registry:** `ADAPTER_REGISTRY`, `get_adapter`, `register_adapter`
- **Normalization:** `normalize_output(provider, raw, context, allow_fallback)`
- **CSM schema:** `src/thegent/contracts/csm.py`
- **Parser:** `src/thegent/contracts/parser.py` (IncrementalXMLParser)

---

## 7. Conformance

- Run `thegent govern conformance` for adapter conformance suite
- Run `thegent govern conformance --check-drift` for drift alarms
- See `docs/contracts/FALLBACK_POLICY.md` for policy and observability

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
- [FALLBACK_POLICY.md](./FALLBACK_POLICY.md) — fallback policy
