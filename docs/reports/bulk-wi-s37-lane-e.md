### [WL-7410]

**Title:** Preserve GPU device-read failure classification in inventory collection paths
**Source:** [thegent/src/thegent/resources/gpu.py:98]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in GPU inventory probing with typed subprocess, parse, and timeout handling.
- [ ] Preserve non-fatal fallback behavior when GPU metadata is unavailable.
- [ ] Add tests for successful GPU enumeration, probe failures, and malformed payload handling.
      **Notes:** The current catch-all path can collapse distinct probe failures into opaque fallback outcomes.

### [WL-7411]

**Title:** Differentiate GPU capability-query errors from unsupported-runtime outcomes
**Source:** [thegent/src/thegent/resources/gpu.py:126]
**Acceptance checklist:**

- [ ] Replace blanket exception handling in capability detection with explicit unsupported-runtime and execution-failure branches.
- [ ] Preserve current empty-result contract for unrecoverable probe states.
- [ ] Add tests for supported runtimes, missing tooling, and command execution faults.
      **Notes:** Treating all failures the same can hide install and runtime regressions during diagnostics.

### [WL-7412]

**Title:** Surface distributed resource probe failures instead of silently returning empty topology
**Source:** [thegent/src/thegent/resources/distributed.py:41]
**Acceptance checklist:**

- [ ] Replace generic suppression in distributed discovery with typed network, parse, and permission failure handling.
- [ ] Preserve resilient behavior when only partial distributed metadata is available.
- [ ] Add tests for healthy discovery, unreachable peers, and malformed responses.
      **Notes:** Silent empty results can mislead operators into reading probe failures as true no-node states.

### [WL-7413]

**Title:** Make TUI config load failures observable without breaking startup flow
**Source:** [thegent/src/thegent/tui/config.py:144]
**Acceptance checklist:**

- [ ] Replace broad config-load suppression with typed file-not-found, decode, and schema validation branches.
- [ ] Preserve default-config fallback semantics for invalid or unreadable user config.
- [ ] Add tests for valid config, malformed content, and permission-denied files.
      **Notes:** Current catch-all handling can hide configuration drift and parser breakage in interactive sessions.

### [WL-7414]

**Title:** Preserve task migration WORK_STREAM read failure context during bootstrap
**Source:** [thegent/src/thegent/task/migrate.py:64]
**Acceptance checklist:**

- [ ] Replace blanket optional-read suppression with explicit path-missing, permission, and decode error handling.
- [ ] Preserve migration continuity when enrichment content cannot be loaded.
- [ ] Add tests for present enrichment data, unreadable files, and invalid markdown payloads.
      **Notes:** Suppressing all read failures can silently drop migration context and complicate operator triage.

### [WL-7415]

**Title:** Narrow task format JSON detection exception handling to decode-specific failures
**Source:** [thegent/src/thegent/task/parser.py:67]
**Acceptance checklist:**

- [ ] Replace generic JSON detection exception handling with typed decode and validation branches.
- [ ] Preserve format-detection precedence across JSON, YAML frontmatter, and legacy task text.
- [ ] Add tests for valid JSON headers, malformed JSON, and non-JSON task content.
      **Notes:** Broad suppression can route malformed inputs through incorrect parser paths with little visibility.

### [WL-7416]

**Title:** Preserve task parser error taxonomy when mapping parse failures to user-facing errors
**Source:** [thegent/src/thegent/task/parser.py:114]
**Acceptance checklist:**

- [ ] Replace broad parse wrapper handling with explicit propagation for known parse and decode exceptions.
- [ ] Preserve existing `TaskParseError` contract for CLI and API callers.
- [ ] Add tests for YAML parse faults, JSON decode errors, and unknown format failures.
      **Notes:** Flattening parser failures into generic errors weakens remediation precision for task authors.

### [WL-7417]

**Title:** Classify task validation runtime failures separately from schema violations
**Source:** [thegent/src/thegent/task/validator.py:130]
**Acceptance checklist:**

- [ ] Replace generic validator exception handling with distinct branches for schema, coercion, and runtime failures.
- [ ] Preserve `ValidationResult` structure for successful and failed validations.
- [ ] Add tests for valid tasks, schema-invalid tasks, and unexpected validator runtime exceptions.
      **Notes:** Combined failure handling can obscure whether an issue is user-authored data or internal validator behavior.

### [WL-7418]

**Title:** Surface plugin loader errors in TUI plugin registration without aborting startup
**Source:** [thegent/src/thegent/tui/plugins.py:109]
**Acceptance checklist:**

- [ ] Replace blanket plugin load suppression with bounded diagnostics including plugin identifier and failure type.
- [ ] Preserve continued startup when one or more optional plugins fail to initialize.
- [ ] Add tests for successful plugin load, import failure, and invalid plugin interface.
      **Notes:** Silent plugin failures reduce confidence in feature availability and complicate debugging of optional extensions.

### [WL-7419]

**Title:** Preserve session registry render failures as bounded diagnostics in routing dashboard
**Source:** [thegent/src/thegent/tui/routing_dashboard.py:111]
**Acceptance checklist:**

- [ ] Replace broad render exception handling with typed UI-state and data-shape failure branches.
- [ ] Preserve dashboard responsiveness when a row or panel fails to render.
- [ ] Add tests for normal render, malformed row data, and transient widget lookup failures.
      **Notes:** Generic suppression can hide regression signals while dashboards appear superficially healthy.
