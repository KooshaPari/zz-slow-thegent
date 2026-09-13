### [WL-7740]

**Title:** Emit explicit watchdog event callbacks from default file watcher handler instead of no-op pass
**Source:** [thegent/src/thegent/infra/fast_file_watcher.py:80]
**Acceptance checklist:**

- [ ] Replace the no-op `on_any_event` body with structured event forwarding (event type, path, is_directory).
- [ ] Keep current `start()` API backward compatible for callers that pass a custom handler.
- [ ] Add tests that assert default handler emits at least create/modify/delete events.
      **Notes:** The default handler currently drops all filesystem events, making watchdog mode non-observable unless callers provide a custom handler.

### [WL-7741]

**Title:** Distinguish WSL detection read errors from non-WSL environments in platform probe
**Source:** [thegent/src/thegent/infra/wsl_interop.py:35]
**Acceptance checklist:**

- [ ] Catch specific file-read exceptions for `/proc/version` and log probe failure context.
- [ ] Preserve `False` return for confirmed non-WSL hosts while surfacing probe I/O failures.
- [ ] Add tests for valid WSL marker, valid non-WSL Linux content, and `/proc/version` read failure.
      **Notes:** The broad exception path currently makes probe failures indistinguishable from legitimate non-WSL detection.

### [WL-7742]

**Title:** Surface partial directory-size traversal failures instead of silently suppressing walk errors
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:205]
**Acceptance checklist:**

- [ ] Return size results with explicit partial/error metadata when `os.walk` fails on subpaths.
- [ ] Preserve current byte-count behavior for fully readable directories.
- [ ] Add tests for permission-denied subdirectories and disappearing files during traversal.
      **Notes:** Silent suppression can return incomplete totals without signaling that size computation was degraded.

### [WL-7743]

**Title:** Replace empty worktree listing fallback with typed error signaling and diagnostic context
**Source:** [thegent/src/thegent/infra/worktree.py:79]
**Acceptance checklist:**

- [ ] Replace broad exception swallowing in `list_active_worktrees` with explicit subprocess/parse error handling.
- [ ] Return a typed failure object or raise a domain error instead of defaulting to `[]` on errors.
- [ ] Add tests for successful list parsing, git command failure, and malformed porcelain output.
      **Notes:** Returning an empty list on all failures masks broken git state and can trigger unsafe cleanup decisions.

### [WL-7744]

**Title:** Report resource limit introspection failures explicitly instead of defaulting to hardcoded values
**Source:** [thegent/src/thegent/infra/resource_limits.py:58]
**Acceptance checklist:**

- [ ] Narrow exception handling in `get_fd_limit` and attach failure reason to diagnostics output.
- [ ] Keep default fallback values only for unsupported platforms, not generic runtime failures.
- [ ] Add tests for successful limit reads, unsupported-resource paths, and syscall failure propagation.
      **Notes:** Blind fallback to defaults can hide host configuration problems and mislead capacity checks.

### [WL-7745]

**Title:** Preserve markdown config load failures from unified config parser with actionable error metadata
**Source:** [thegent/src/thegent/integration/unified_config.py:104]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression with explicit parse/load error reporting that includes source path.
- [ ] Keep successful frontmatter/table extraction behavior unchanged for valid files.
- [ ] Add tests for unreadable markdown files, malformed frontmatter, and valid config extraction.
      **Notes:** Current behavior silently returns an empty config map, obscuring whether config is absent or unreadable.

### [WL-7746]

**Title:** Count and report malformed queue rows skipped during JSONL entry parsing
**Source:** [thegent/src/thegent/queue/storage.py:29]
**Acceptance checklist:**

- [ ] Track malformed-line count and line numbers in `_parse_entries` instead of silent `continue`.
- [ ] Expose parse-quality diagnostics to queue callers without breaking existing list/claim APIs.
- [ ] Add tests for mixed valid/invalid queue files and fully malformed queue content.
      **Notes:** Silent row drops can hide queue corruption and cause pending counts to drift from operator expectations.

### [WL-7747]

**Title:** Make queue lease timestamp parse failures explicit in filtered list output
**Source:** [thegent/src/thegent/queue/storage.py:85]
**Acceptance checklist:**

- [ ] Replace silent lease parse suppression with explicit invalid-lease status on affected items.
- [ ] Preserve include/exclude expired semantics for valid ISO lease timestamps.
- [ ] Add tests for valid leases, malformed lease strings, and timezone-variant timestamp formats.
      **Notes:** Invalid lease data is currently ignored, which can keep broken claimed entries invisible during filtering.

### [WL-7748]

**Title:** Expose invalid JSON records encountered under queue lock reads instead of dropping them silently
**Source:** [thegent/src/thegent/queue/locking.py:54]
**Acceptance checklist:**

- [ ] Record invalid-line metadata during `read_entries` while preserving lock safety and atomic write semantics.
- [ ] Return structured diagnostics to callers so corruption can be remediated deterministically.
- [ ] Add tests for lock-protected reads with valid rows, invalid JSON rows, and mixed content.
      **Notes:** Silent drops under lock can lead to lossy rewrites that permanently remove malformed but recoverable entries.

### [WL-7749]

**Title:** Emit fragment extraction read errors during sync discovery instead of silent pass on `OSError`
**Source:** [thegent/src/thegent/commands/sync.py:833]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression in `_extract_fragments_from_file` with warning/error metadata that includes path and errno.
- [ ] Continue processing remaining markdown files after a per-file read failure.
- [ ] Add tests for unreadable fragment files, mixed readable/unreadable sets, and normal extraction behavior.
      **Notes:** Hidden read failures make sync output appear complete even when source fragment files were skipped.
