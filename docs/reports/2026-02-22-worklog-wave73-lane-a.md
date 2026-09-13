# Worklog Wave 73 Lane A

Date: 2026-02-22

## Items

1. **WL-9270 — Preserve agent governance by separating parse and execution phases**

- **Source:** [thegent/src/thegent/automation/workflow.go:570]
- **Recommendation:** adopt
- **Action:** Keep the parsing and execution steps in separate paths and add regression coverage for both success and failure boundaries.

2. **WL-9271 — Preserve hook execution by separating sync and async control paths**

- **Source:** [thegent/src/thegent/policy/engine.go:573]
- **Recommendation:** adopt
- **Action:** Implement explicit separation between sync and async control flow with no behavior change on legacy pathways.

3. **WL-9272 — Preserve quality gates by separating signal collection and threshold enforcement**

- **Source:** [thegent/src/thegent/automation/workflow.go:576]
- **Recommendation:** adopt
- **Action:** Move signal capture into an isolated stage and enforce thresholds only after collection to preserve failure semantics and observability.

4. **WL-9273 — Preserve observability by separating metric emission and business logic**

- **Source:** [thegent/src/thegent/policy/engine.go:579]
- **Recommendation:** adopt
- **Action:** Decouple metric emission from core business decisions and add focused tests for metric emission and decision correctness.

5. **WL-9274 — Preserve session state by separating claim and completion transitions**

- **Source:** [thegent/src/thegent/automation/workflow.go:582]
- **Recommendation:** adopt
- **Action:** Split claim state updates from completion transitions, then validate no transition is skipped on error paths.
