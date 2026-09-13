### [WL-8180]

**Title:** Preserve health endpoint metrics while splitting validation and emit stages
**Source:** [thegent/src/thegent/health/endpoint.py:156]
**Acceptance checklist:**

- [ ] Distinguish invalid request validation from metrics emit failures.
- [ ] Keep response contract unchanged for valid requests.
- [ ] Add tests for invalid payload and emit exceptions.
      **Notes:** Improves observability in degraded environments.

### [WL-8181]

**Title:** Separate conversation export parse errors from storage failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:348]
**Acceptance checklist:**

- [ ] Handle malformed conversation JSON separately from write failures.
- [ ] Preserve export command structure for storage failures.
- [ ] Add tests for malformed export input and read-only storage.
      **Notes:** Helps isolate root cause when dump failures occur.

### [WL-8182]

**Title:** Preserve borrow tool call behavior while separating command parse and broker errors
**Source:** [thegent/src/thegent/tools/borrow.py:466]
**Acceptance checklist:**

- [ ] Split command payload parse errors from broker dispatch errors.
- [ ] Preserve return contract and error messages.
- [ ] Add tests for payload parse and dispatch failure branches.
      **Notes:** Improves traceability of borrow runtime issues.

### [WL-8183]

**Title:** Preserve cache rebuild contract while separating lock handling from rebuild execution
**Source:** [thegent/src/thegent/cache/rebuilder.py:134]
**Acceptance checklist:**

- [ ] Handle lock acquisition failures separately from rebuild processing errors.
- [ ] Keep existing retry or fallback behavior for lock contention.
- [ ] Add tests for lock contention and rebuild exceptions.
      **Notes:** Improves recovery during concurrent rebuild attempts.

### [WL-8184]

**Title:** Separate control-plane manifest parse and dispatch route errors
**Source:** [thegent/src/thegent/control_plane/server.py:340]
**Acceptance checklist:**

- [ ] Validate manifest fields before dispatching routes.
- [ ] Preserve existing fallback for unknown route handling.
- [ ] Add tests for malformed manifest and route errors.
      **Notes:** Reduces hidden control-plane runtime failures.

### [WL-8185]

**Title:** Preserve clipboard sync behavior while separating path validation and write failures
**Source:** [thegent/src/thegent/clipboard/history.py:246]
**Acceptance checklist:**

- [ ] Add explicit branch for invalid history paths vs write exceptions.
- [ ] Keep sync behavior for valid paths while surfacing write errors.
- [ ] Add tests for invalid path and read-only path cases.
      **Notes:** Improves reliability for cross-process history sync.

### [WL-8186]

**Title:** Separate artifact metadata decode failures from artifact fetch failures
**Source:** [thegent/src/thegent/artifacts/uploader.py:329]
**Acceptance checklist:**

- [ ] Handle metadata decode failures before upload call.
- [ ] Preserve upload retry semantics for network failures.
- [ ] Add tests for malformed metadata and network exceptions.
      **Notes:** Prevents avoidable retries and preserves debugability.

### [WL-8187]

**Title:** Preserve shell completion cache while separating JSON corruption and stale cache states
**Source:** [thegent/src/thegent/shell_cli.py:603]
**Acceptance checklist:**

- [ ] Handle corrupted completion cache JSON separately from stale cache indicators.
- [ ] Preserve completion generation on corrupt cache.
- [ ] Add tests for corrupt JSON and stale cache refresh.
      **Notes:** Keeps UX responsive under local cache damage.

### [WL-8188]

**Title:** Preserve plugin loader resilience while separating manifest read failures
**Source:** [thegent/src/thegent/ui/plugin_loader.py:343]
**Acceptance checklist:**

- [ ] Separate manifest file I/O failures from parser exceptions.
- [ ] Keep plugin loader fallback path for unreadable manifests.
- [ ] Add tests for missing manifest and malformed manifest content.
      **Notes:** Better startup reliability with clearer failure boundaries.

### [WL-8189]

**Title:** Separate queue scaler parse failures from scaling action failures
**Source:** [thegent/src/thegent/queue/scaler.py:142]
**Acceptance checklist:**

- [ ] Split malformed scaler config parse from process scaling failures.
- [ ] Preserve scaling policy fallback on parse failures.
- [ ] Add tests for malformed config and failed scaling operations.
      **Notes:** Improves scalability stability under config drift.
