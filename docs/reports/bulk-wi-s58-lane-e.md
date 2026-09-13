### [WL-8460]

**Title:** Preserve orchestration API behavior by separating authorization checks and payload marshaling
**Source:** [thegent/src/thegent/orchestration/api.py:467]
**Acceptance checklist:**

- [ ] Separate authorization failures from payload marshaling failures.
- [ ] Preserve baseline authorization semantics with fallback marshaling.
- [ ] Add tests for auth and marshaling branch behavior.
      **Notes:** Helps prevent API outages from one serialization change.

### [WL-8461]

**Title:** Preserve queue drain by separating backlog analysis and worker dispatch
**Source:** [thegent/src/thegent/queue/drain.py:391]
**Acceptance checklist:**

- [ ] Distinguish backlog analysis failures from worker dispatch failures.
- [ ] Preserve dispatch under analysis fallback.
- [ ] Add tests for backlog and dispatch branches.
      **Notes:** Improves queue reliability under partial observability.

### [WL-8462]

**Title:** Preserve auth token lifecycle by separating issue-time claiming and refresh scheduling
**Source:** [thegent/src/thegent/auth/lifecycle.py:349]
**Acceptance checklist:**

- [ ] Separate token issue-time claim failures from refresh scheduling failures.
- [ ] Preserve refresh schedule defaults when issue-time claims fail.
- [ ] Add tests for claim and scheduling failures.
      **Notes:** Keeps token management stable under mixed token providers.

### [WL-8463]

**Title:** Preserve CLI profile handling by separating profile parse and profile selection
**Source:** [thegent/src/thegent/cli/profile.py:276]
**Acceptance checklist:**

- [ ] Separate profile parse failures from profile selection failures.
- [ ] Preserve active profile on parse branch regressions.
- [ ] Add tests for parse and selection branch behavior.
      **Notes:** Improves CLI ergonomics when profile formats drift.

### [WL-8464]

**Title:** Preserve artifact migration by separating manifest transform and migration execution
**Source:** [thegent/src/thegent/artifacts/migrate.py:512]
**Acceptance checklist:**

- [ ] Separate manifest transform failures from migration execution failures.
- [ ] Preserve migration staging on transform failures.
- [ ] Add tests for transform and execution branches.
      **Notes:** Avoids irreversible migration steps during one-side failures.

### [WL-8465]

**Title:** Preserve event publisher by separating destination resolution and publish attempt
**Source:** [thegent/src/thegent/publisher/dispatcher.py:421]
**Acceptance checklist:**

- [ ] Distinguish destination resolution failures from publish attempt failures.
- [ ] Preserve retry queue when destination cannot be resolved.
- [ ] Add tests for destination and publish branch handling.
      **Notes:** Helps maintain event reliability during routing drift.

### [WL-8466]

**Title:** Preserve prompt compression by separating token count estimation and compression transform
**Source:** [thegent/src/thegent/prompt/compression.py:358]
**Acceptance checklist:**

- [ ] Separate token counting failures from compression transform failures.
- [ ] Keep uncompressed prompts in fallback mode.
- [ ] Add tests for counting and transform branches.
      **Notes:** Preserves prompt flow when compression internals degrade.

### [WL-8467]

**Title:** Preserve command audit trail by separating command capture and audit persistence
**Source:** [thegent/src/thegent/audit/commands.py:333]
**Acceptance checklist:**

- [ ] Separate command capture failures from audit persistence failures.
- [ ] Preserve capture metrics when persistence is unavailable.
- [ ] Add tests for capture and persistence branch cases.
      **Notes:** Keeps audit completeness under partial persistence outages.

### [WL-8468]

**Title:** Preserve UI panel state by separating user preference parse and persistence
**Source:** [thegent/src/thegent/ui/prefs.py:452]
**Acceptance checklist:**

- [ ] Separate user preference parse errors from persistence errors.
- [ ] Preserve panel defaults with parse fallback.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Helps prevent UI state loss during preference format changes.

### [WL-8469]

**Title:** Preserve scheduling telemetry by separating histogram bucketization and stream export
**Source:** [thegent/src/thegent/telemetry/scheduler.py:491]
**Acceptance checklist:**

- [ ] Split histogram bucketization failures from stream export failures.
- [ ] Preserve scheduling samples when export fails.
- [ ] Add tests for bucketization and export branches.
      **Notes:** Improves observability during scheduler data path transitions.
