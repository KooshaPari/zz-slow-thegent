### [WL-7040]

**Title:** Surface configured-provider discovery failures instead of silently returning partial sets
**Source:** [thegent/src/thegent/doctor.py:530]
**Acceptance checklist:**

- [ ] Replace blanket provider-discovery suppression with typed config-read and parse error branches.
- [ ] Preserve successful provider enumeration behavior for valid config states.
- [ ] Add tests for readable configs, malformed payloads, and missing credential files.
      **Notes:** Silent fallback to partial provider sets can mask configuration regressions.

### [WL-7041]

**Title:** Classify provider model-selection fallback errors before defaulting to provider-name probes
**Source:** [thegent/src/thegent/doctor.py:610]
**Acceptance checklist:**

- [ ] Replace broad model-selection exception handling with explicit missing-model and decode-failure branches.
- [ ] Keep current probe behavior when model metadata is genuinely unavailable.
- [ ] Add tests for successful model selection, malformed metadata, and absent model lists.
      **Notes:** Untyped fallback paths can hide why provider validation degraded.

### [WL-7042]

**Title:** Preserve chat-completion error payload decode failures with bounded diagnostics
**Source:** [thegent/src/thegent/doctor.py:636]
**Acceptance checklist:**

- [ ] Refactor error-body extraction to distinguish invalid JSON from missing error fields.
- [ ] Retain concise response-text fallback for non-JSON provider errors.
- [ ] Add tests for valid JSON errors, malformed payloads, and plain-text failures.
      **Notes:** Collapsing parse failures into generic text reduces troubleshooting precision.

### [WL-7043]

**Title:** Report restricted net-connection inspection during long-running process health checks
**Source:** [thegent/src/thegent/doctor.py:770]
**Acceptance checklist:**

- [ ] Emit bounded diagnostics when access-denied or missing-process errors block connection checks.
- [ ] Preserve lenient long-running-session handling for healthy processes.
- [ ] Add tests for permitted connection checks and denied-access environments.
      **Notes:** Silent permission failures obscure why process activity signals are incomplete.

### [WL-7044]

**Title:** Distinguish CPU sampling access failures from low-utilization process states
**Source:** [thegent/src/thegent/doctor.py:781]
**Acceptance checklist:**

- [ ] Record classified diagnostics for CPU sampling access and lifecycle errors.
- [ ] Preserve normal low-CPU evaluation when sampling succeeds.
- [ ] Add tests for successful sampling, access-denied cases, and disappearing processes.
      **Notes:** Treating sampling failures as inactivity can misclassify active sessions.

### [WL-7045]

**Title:** Preserve I/O counter probe limitations instead of silently skipping activity signals
**Source:** [thegent/src/thegent/doctor.py:794]
**Acceptance checklist:**

- [ ] Add typed handling for unsupported I/O counters versus transient process-access failures.
- [ ] Keep existing activity thresholds for environments that provide counters.
- [ ] Add tests covering supported, unsupported, and denied-access I/O paths.
      **Notes:** Hidden probe limitations can underreport active process behavior.

### [WL-7046]

**Title:** Expose net-connection lookup failures in short-run activity classification
**Source:** [thegent/src/thegent/doctor.py:802]
**Acceptance checklist:**

- [ ] Replace silent network-inspection suppression with bounded failure annotations.
- [ ] Preserve successful connection-based activity detection semantics.
- [ ] Add tests for successful lookups and denied-access/no-such-process conditions.
      **Notes:** Suppressed lookup failures can skew stuck-process determinations.

### [WL-7047]

**Title:** Track file-descriptor inspection gaps when leak scans cannot read process handles
**Source:** [thegent/src/thegent/doctor.py:1098]
**Acceptance checklist:**

- [ ] Record classified reasons when FD counts cannot be collected.
- [ ] Preserve high-FD detection logic for readable processes.
- [ ] Add tests for successful FD collection and access-denied/unsupported APIs.
      **Notes:** Silent FD-scan gaps can conceal resource leak indicators.

### [WL-7048]

**Title:** Preserve orphan-detection blind spots when parent-process inspection is blocked
**Source:** [thegent/src/thegent/doctor.py:1111]
**Acceptance checklist:**

- [ ] Emit bounded diagnostics for NoSuchProcess and AccessDenied during parent inspection.
- [ ] Keep orphan classification unchanged when parent metadata is available.
- [ ] Add tests for valid parent resolution and blocked parent lookups.
      **Notes:** Hidden parent-inspection failures can undercount orphaned runtime processes.

### [WL-7049]

**Title:** Differentiate MCP health endpoint transport failures from non-healthy status responses
**Source:** [thegent/src/thegent/doctor.py:1501]
**Acceptance checklist:**

- [ ] Replace broad health-check exception handling with typed transport and timeout branches.
- [ ] Preserve warning semantics for explicit non-200 MCP health responses.
- [ ] Add tests for healthy responses, HTTP failures, and connection timeouts.
      **Notes:** Conflating transport failures with generic unreachability slows MCP incident triage.
