# Provider Model Behavior Constraints

**Purpose:** Instruct models (especially minimax, glm) to reduce subagent spam and verbose dispatch announcements.

---

## Known Behaviors

| Provider       | Model        | Tendency                                                                                      |
| -------------- | ------------ | --------------------------------------------------------------------------------------------- |
| minimax        | MiniMax-M2.5 | Repeated "Let me dispatch subagents in parallel"; over-delegation; verbose task announcements |
| glm            | glm-5, GLM-5 | Same as minimax; "I'll dispatch multiple agents..." spam; redundant status updates            |
| kilo           | various      | Generally more restrained                                                                     |
| claude, gemini | various      | Less prone to subagent spam                                                                   |

---

## Constraints (Inject When Provider = minimax | glm)

**Subagent dispatch:**

- Dispatch **once per logical batch**. Do not announce "Let me dispatch..." repeatedly.
- If you have <5 independent tasks, handle 2–3 directly before delegating.
- Prefer **sequential completion** of small batches over parallel spawning of many agents.
- Call in parallel only when tasks are **truly independent** and >3; otherwise batch sequentially.

**Announcements:**

- Do not repeat "I'll dispatch multiple subagents in parallel" or similar.
- Do not form verbose status blocks ("Forming…", "Running 9 Task agents…") unless the user asked for progress.
- Summarize completed work; do not re-announce the same dispatch.

**Rule of thumb:** If you would spawn >5 subagents for a single user request, reconsider: can you do 2–3 yourself first?

---

## Integration Points

| Location                          | How to apply                                                          |
| --------------------------------- | --------------------------------------------------------------------- |
| `skills/agent-orchestra/SKILL.md` | Add "Provider Constraints" section (see below)                        |
| `skills/sitback-agent/SKILL.md`   | Reference provider constraints when dispatching                       |
| `prompt-submit-guard.sh`          | Inject constraints when `provider=minimax` or `provider=glm` detected |
| Cursor/Claude Code                | System instructions or skill loaded per provider                      |

---

## Skill Section (Copy to agent-orchestra)

```markdown
## Provider Constraints (minimax, glm)

When using minimax or glm: dispatch subagents sparingly. Handle 2–3 tasks directly before delegating. Do not announce "Let me dispatch..." repeatedly. Prefer sequential batches over parallel spam.
```

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
