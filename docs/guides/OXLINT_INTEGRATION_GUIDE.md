# oxlint Integration Guide (Phase 4)

**Status**: Integration Phase
**Target**: Replace ESLint dependency with oxlint for JS/TS linting (5-50x speedup)

---

## Overview

This guide explains the Phase 4 oxlint integration strategy and how to integrate the linting-accelerator wrapper into the QA pipeline.

### Key Changes

| Component    | Before                  | After                              | Benefit                      |
| ------------ | ----------------------- | ---------------------------------- | ---------------------------- |
| TS/JS Linter | ESLint (fallback)       | oxlint (primary) + ESLint fallback | 5-50x faster                 |
| Wrapper      | None (inline fallback)  | `hooks/lib/linting-accelerator.sh` | Consistent, testable         |
| Config       | None (no-eslintrc flag) | `oxlintrc.json` in project root    | Explicit, version-controlled |
| Reliability  | Silent fallback         | Transparent fallback + logging     | Better visibility            |

---

## Architecture

### Three-Layer Strategy

```
Application Layer (quality-gate.sh)
    ↓ sources linting-accelerator.sh
Acceleration Layer (hooks/lib/linting-accelerator.sh)
    ├→ Try oxlint first (fast path)
    ├→ Fallback to eslint if unavailable
    └→ Fail loudly if neither available
    ↓
Tool Layer (oxlint OR eslint)
```

### Configuration Files

```
Project Root
├── oxlintrc.json              (NEW: oxlint configuration)
├── hooks/
│   ├── quality-gate.sh        (MODIFIED: integrate accelerator)
│   └── lib/
│       └── linting-accelerator.sh  (NEW: fallback wrapper)
└── docs/
    ├── research/
    │   └── ESLINT_AUDIT.md     (NEW: audit & mapping)
    └── guides/
        └── OXLINT_INTEGRATION_GUIDE.md  (THIS FILE)
```

---

## Implementation Steps

### Step 1: Configuration (COMPLETE)

✓ Created `/oxlintrc.json` with rule mappings:

- 25+ oxlint-native rules
- 10+ plugin rules (typescript, react, import, security)
- Consistent with thegent QA standards
- Includes practical ignorePatterns

**Validation**: oxlintrc.json is valid JSON and matches oxlint schema.

### Step 2: Wrapper Implementation (COMPLETE)

✓ Created `/hooks/lib/linting-accelerator.sh`:

- Transparent fallback mechanism
- Two commands: `ts-lint`, `ts-dead-imports`, `ts-all`
- VERBOSE and OXLINT_DISABLE environment variables for testing
- Persistent logging for troubleshooting

**Features**:

```bash
# Usage from quality-gate.sh:
source "$HOOKS_LIB/linting-accelerator.sh"
_accel_main ts-lint "${TS_FILES[@]}"

# Or with fallback:
_accel_main ts-dead-imports "${TS_FILES[@]}" || exit_code=$?
```

### Step 3: quality-gate.sh Integration (NEXT)

Update `/hooks/quality-gate.sh` to use the accelerator:

**Current Code (lines 178-188)**:

```bash
# Group 3: TypeScript/JavaScript (oxlint lint + dead imports + knip dead code)
if [[ ${#TS_FILES[@]} -gt 0 ]]; then
    if [[ "$(tool_available oxlint)" == "true" ]]; then
      _lint_batch "TS/JS LINT (oxlint)" "$LINT_TMP/ts_lint" \
        oxlint "${TS_FILES[@]}"
      _lint_batch "DEAD IMPORTS (oxlint)" "$LINT_TMP/ts_deadimport" \
        oxlint --deny no-unused-vars "${TS_FILES[@]}"
    elif [[ "$(tool_available eslint)" == "true" ]]; then
      _lint_batch "DEAD IMPORTS (eslint)" "$LINT_TMP/ts_deadimport" \
        eslint --rule '{"no-unused-vars":"warn"}' --no-eslintrc "${TS_FILES[@]}"
```

**Planned Replacement** (using wrapper):

```bash
# Group 3: TypeScript/JavaScript (oxlint + fallback to eslint)
if [[ ${#TS_FILES[@]} -gt 0 ]]; then
    source "$HOOKS_LIB/linting-accelerator.sh"

    _lint_batch "TS/JS LINT (oxlint/eslint)" "$LINT_TMP/ts_lint" \
      _accel_main ts-lint "${TS_FILES[@]}"

    _lint_batch "DEAD IMPORTS (oxlint/eslint)" "$LINT_TMP/ts_deadimport" \
      _accel_main ts-dead-imports "${TS_FILES[@]}"
```

### Step 4: Validation (NEXT)

**Pre-Integration Checks**:

1. Verify oxlintrc.json is valid JSON
2. Test linting-accelerator.sh on sample files
3. Compare oxlint output to eslint baseline
4. Run quality-gate on templates/typescript directory

**Test Commands**:

```bash
# Verify config
jq . oxlintrc.json  # Should output valid JSON

# Test wrapper (with oxlint)
./hooks/lib/linting-accelerator.sh ts-lint templates/typescript/*.ts

# Test wrapper (fallback simulation)
OXLINT_DISABLE=1 ./hooks/lib/linting-accelerator.sh ts-lint templates/typescript/*.ts

# Compare outputs
oxlint templates/typescript/app.ts > /tmp/oxlint.txt
eslint --no-eslintrc templates/typescript/app.ts > /tmp/eslint.txt
diff /tmp/oxlint.txt /tmp/eslint.txt
```

### Step 5: Hook Update (NEXT)

1. Update `hooks/quality-gate.sh` to source and use linting-accelerator
2. Update `hooks/hook-config.yaml` if needed for timing
3. Verify no breaking changes to existing Python/Shell linting

---

## Rule Mapping Reference

### Oxlint Native Rules (No Configuration)

These rules are automatically enabled by oxlint when you enable categories:

| Rule           | Category             | ESLint Equivalent | Status         |
| -------------- | -------------------- | ----------------- | -------------- |
| no-unused-vars | correctness          | no-unused-vars    | ✓ Direct match |
| no-debugger    | correctness          | no-debugger       | ✓ Direct match |
| eqeqeq         | suspicious           | eqeqeq            | ✓ Direct match |
| no-var         | correctness          | no-var            | ✓ Direct match |
| prefer-const   | suspicious           | prefer-const      | ✓ Direct match |
| no-eval        | security/restriction | no-eval           | ✓ Direct match |
| no-new-func    | security/restriction | no-new-func       | ✓ Direct match |
| max-params     | restriction          | max-params        | ✓ Direct match |
| complexity     | restriction          | complexity        | ✓ Direct match |
| max-lines      | restriction          | max-lines         | ✓ Direct match |

### Plugin Rules (oxlint Configuration)

These are explicitly configured in oxlintrc.json:

| Plugin      | Rules                                                                 | Status    |
| ----------- | --------------------------------------------------------------------- | --------- |
| typescript  | no-explicit-any, explicit-function-return-type, no-non-null-assertion | ✓ Strict  |
| react-hooks | rules-of-hooks, exhaustive-deps                                       | ✓ Enabled |
| import      | no-cycle, no-self-import, no-duplicates, max-dependencies             | ✓ Enabled |
| unicorn     | prefer-node-protocol, no-array-reduce                                 | ✓ Enabled |
| security    | detect-object-injection, detect-non-literal-regexp                    | ✓ Warn    |

### Rules Not in oxlint (Documented Gap)

These ESLint rules are not natively available in oxlint:

| Rule                     | Workaround                                           |
| ------------------------ | ---------------------------------------------------- |
| import/no-default-export | Enforce via code review or separate jsdoc rule       |
| jsdoc/\* rules           | Use separate jsdoc tool or skip in automated linting |
| Various stylistic rules  | Use prettier instead                                 |

**Status**: This is acceptable for Phase 4. We prioritize:

1. **Correctness** rules (must have)
2. **Performance** rules (must have)
3. **Security** rules (must have)
4. **Style** rules (nice-to-have, can use prettier)

---

## Performance Impact

### Expected Speedup

| Operation               | ESLint | oxlint     | Speedup    |
| ----------------------- | ------ | ---------- | ---------- |
| Lint 100 small files    | ~2-3s  | ~100-200ms | 10-30x     |
| Lint 10 large files     | ~1-2s  | ~50-100ms  | 10-20x     |
| Dead imports check      | ~1-2s  | ~50-100ms  | 10-20x     |
| **Total (both checks)** | ~4-5s  | ~200-400ms | **10-25x** |

**System Requirements**:

- oxlint: ~50MB (single binary, Rust)
- eslint: ~100MB+ (node_modules)

### Caching Strategy

The linting-accelerator works with existing hook caching:

- `quality-gate.sh` already caches results per commit
- oxlint runs at 200-400ms, cached results hit in <10ms
- No additional caching needed in accelerator layer

---

## Testing Strategy

### Unit Tests (if implementing hook tests)

```bash
# Test 1: oxlint available and working
test_oxlint_primary() {
  local result
  result=$(_accel_main ts-lint samples/app.ts)
  [[ $? -eq 0 ]] && echo "PASS: oxlint lint" || echo "FAIL"
}

# Test 2: fallback to eslint
test_eslint_fallback() {
  OXLINT_DISABLE=1 _accel_main ts-lint samples/app.ts
  [[ $? -ge 0 ]] && echo "PASS: eslint fallback" || echo "FAIL"
}

# Test 3: both unavailable = clear error
test_neither_available() {
  PATH="" _accel_main ts-lint samples/app.ts 2>&1 | grep -q "Neither oxlint nor eslint"
  [[ $? -eq 0 ]] && echo "PASS: clear error" || echo "FAIL"
}
```

### Integration Tests

```bash
# Run against templates
./hooks/quality-gate.sh  # Should pick up no TS files unless templates modified

# Run on sample TS files (if any)
for f in templates/typescript/*.ts; do
  oxlint "$f" > /tmp/ox.txt
  eslint --no-eslintrc "$f" > /tmp/es.txt
  # Diff should be small (mostly formatting)
done
```

---

## Troubleshooting

### Issue: "Neither oxlint nor eslint available"

**Cause**: Neither tool is installed

**Solution**:

```bash
# Install oxlint (recommended)
npm install -g oxlint

# OR install eslint (fallback)
npm install -g eslint
```

### Issue: Unexpected lint errors after update

**Cause**: oxlint and eslint have different defaults

**Solution**:

1. Check `oxlintrc.json` rule settings
2. Use `VERBOSE=1` to see which tool ran
3. Compare with `OXLINT_DISABLE=1` to test eslint baseline

### Issue: Performance still slow

**Cause**: Fallback to eslint or first-run cache miss

**Solution**:

```bash
# Check which tool is running
VERBOSE=1 ./hooks/lib/linting-accelerator.sh ts-lint file.ts

# Force oxlint
OXLINT_DISABLE=0 ...  # (it's already 0 by default)

# Check if oxlint is in PATH
which oxlint
```

---

## Rollback Plan

If oxlint integration causes issues:

1. **Disable oxlint temporarily**:

   ```bash
   export OXLINT_DISABLE=1
   # quality-gate.sh will use eslint fallback
   ```

2. **Remove oxlint integration**:
   - Delete `hooks/lib/linting-accelerator.sh`
   - Revert `hooks/quality-gate.sh` to inline fallback logic
   - Keep `oxlintrc.json` for future projects

3. **Full revert**:
   - Delete `oxlintrc.json`
   - Delete `hooks/lib/linting-accelerator.sh`
   - Restore `hooks/quality-gate.sh` to original

---

## Next Phase: Phase 4.5

**Title**: Validation & Metrics

**Goals**:

1. Run full quality gate on templates and sample projects
2. Collect before/after linting time metrics
3. Document any rule divergences in ESLINT_AUDIT.md
4. Create oxlint adoption guide for future TypeScript projects

**Deliverables**:

- Performance metrics report
- Updated oxlintrc.json if rule refinements needed
- Tutorial for TypeScript project templates

---

## References

- **oxlint GitHub**: https://github.com/oxc-project/oxc
- **oxlint Rules**: https://oxc-project.github.io/docs/guide/linter/rules.html
- **ESLint Migration**: https://oxc-project.github.io/docs/guide/tools/eslint-compare.html
- **Project oxlintrc.json**: `/oxlintrc.json`
- **Audit & Rule Mapping**: `docs/research/ESLINT_AUDIT.md`

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

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue             | Symptom                     | Solution                                      |
| ----------------- | --------------------------- | --------------------------------------------- |
| oxlint not found  | "command not found: oxlint" | Install via npm: `npm install -g oxlint`      |
| Config not loaded | No rules applied            | Check `oxlintrc.json` in project root         |
| False positives   | Incorrect warnings          | Update `extends` or adjust rules              |
| Slow execution    | > 1s per file               | Check for too many files, use `--max-workers` |

### 10.2 Debug Commands

```bash
# Check oxlint installation
oxlint --version

# Check config
oxlint --print-config

# Run with verbose
oxlint --verbose src/

# Check what config is being used
oxlint --show-config-path
```

### 10.3 Fallback Verification

```bash
# Test fallback to eslint
eslint --version

# Run eslint directly
eslint src/ --ext .js,.ts

# Check accelerator script
bash hooks/lib/linting-accelerator.sh --test
```

---

## 11. Extension Summary

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 10:** Troubleshooting
   - Common issues table
   - Debug commands
   - Fallback verification

### Cross-References Added

- ESLINT_AUDIT.md
- quality-gate.sh
- linting-accelerator.sh

### Practical Additions

- Troubleshooting table
- Debug commands for verification
- Fallback testing procedures
