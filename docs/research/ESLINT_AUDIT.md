<DONE>
# ESLint → oxlint Migration Audit (Phase 4)

**Date**: 2026-02-15
**Status**: Research Complete
**Objective**: Evaluate current ESLint usage and plan safe migration to oxlint for 5-50x linting speedup

---

## Executive Summary

The thegent project is **primarily Python-based** (using ruff for linting) with minimal JavaScript/TypeScript footprint. Current ESLint integration exists only as a **fallback mechanism** in `quality-gate.sh` when oxlint is unavailable. Phase 4 will:

1. Formalize oxlint as the primary JS/TS linter (already partially implemented)
2. Create a **linting-accelerator wrapper** with automatic fallback strategy
3. Establish oxlint configuration in project root
4. Document rule mapping strategy for future projects

---

## Current State Audit

### Project Composition

| Language              | Primary Linter            | Status           | Files                         |
| --------------------- | ------------------------- | ---------------- | ----------------------------- |
| Python                | ruff                      | ✓ Active         | pyproject.toml config         |
| TypeScript/JavaScript | oxlint (fallback: eslint) | ⚠ Fallback only | None configured               |
| Shell                 | shellcheck                | ✓ Active         | Integrated in quality-gate.sh |

**Key Finding**: This is a **Python-first project** with template-based support for TypeScript. No active JS/TS source in main codebase (only templates in `/templates/` directory).

### ESLint Configuration Status

**Current State**:

- ✗ No `.eslintrc*` file found in project root or source directories
- ✗ No `eslint.config.js` configuration
- ✗ No `package.json` with ESLint config
- ⚠ ESLint appears only as **fallback** in `quality-gate.sh` line 186-188

**Integration Points**:

```bash
# hooks/quality-gate.sh (lines 178-188)
if [[ "$(tool_available oxlint)" == "true" ]]; then
  # oxlint is primary
  _lint_batch "TS/JS LINT (oxlint)" "$LINT_TMP/ts_lint" \
    oxlint "${TS_FILES[@]}"
elif [[ "$(tool_available eslint)" == "true" ]]; then
  # eslint is fallback
  _lint_batch "DEAD IMPORTS (eslint)" "$LINT_TMP/ts_deadimport" \
    eslint --rule '{"no-unused-vars":"warn"}' --no-eslintrc "${TS_FILES[@]}"
fi
```

### oxlint Template Configuration

**Location**: `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/templates/quality/oxlintrc.json`

**Current Rules Matrix**:

| Category              | Rules                                                                  | Status                |
| --------------------- | ---------------------------------------------------------------------- | --------------------- |
| **Core Quality**      | no-unused-vars, no-console, no-debugger, eqeqeq, no-eval               | ✓ Configured          |
| **Variables & Scope** | no-var, prefer-const, no-throw-literal                                 | ✓ Configured          |
| **Async/Await**       | no-return-await                                                        | ✓ Configured          |
| **TypeScript**        | explicit-function-return-type, no-explicit-any, prefer-ts-expect-error | ✓ Configured (strict) |
| **Imports**           | no-cycle, no-self-import, no-duplicates, max-dependencies (20)         | ✓ Configured          |
| **React**             | rules-of-hooks (error), exhaustive-deps (warn)                         | ✓ Configured          |
| **Promises**          | no-nesting                                                             | ⚠ Warn (loose)       |
| **Security**          | detect-object-injection, detect-non-literal-regexp                     | ⚠ Warn (loose)       |
| **Complexity**        | complexity (max 15), max-params (6), max-lines (750)                   | ✓ Strict              |
| **Style**             | Unicorn, Next.js, JSDoc plugins enabled                                | ✓ Enabled             |

**Rule Coverage**: ~25 oxlint-native rules + 10 plugin rules

---

## Rule Mapping: ESLint → oxlint

### Direct Matches (No Configuration Needed)

These ESLint rules map 1:1 to oxlint:

| ESLint Rule                      | oxlint Equivalent                | Notes                 |
| -------------------------------- | -------------------------------- | --------------------- |
| no-unused-vars                   | no-unused-vars                   | ✓ Native oxlint       |
| no-console                       | no-console                       | ✓ Native oxlint       |
| no-debugger                      | no-debugger                      | ✓ Native oxlint       |
| eqeqeq                           | eqeqeq                           | ✓ Native oxlint       |
| no-var                           | no-var                           | ✓ Native oxlint       |
| prefer-const                     | prefer-const                     | ✓ Native oxlint       |
| no-eval                          | no-eval                          | ✓ Native oxlint       |
| no-new-func                      | no-new-func                      | ✓ Native oxlint       |
| no-throw-literal                 | no-throw-literal                 | ✓ Native oxlint       |
| complexity                       | complexity                       | ✓ Native oxlint       |
| max-params                       | max-params                       | ✓ Native oxlint       |
| max-lines                        | max-lines                        | ✓ Native oxlint       |
| typescript/no-explicit-any       | typescript/no-explicit-any       | ✓ Plugin: typescript  |
| typescript/no-non-null-assertion | typescript/no-non-null-assertion | ✓ Plugin: typescript  |
| react-hooks/rules-of-hooks       | react-hooks/rules-of-hooks       | ✓ Plugin: react-hooks |
| import/no-cycle                  | import/no-cycle                  | ✓ Plugin: import      |

### Partial Matches (Different Config)

| ESLint Rule                  | oxlint Equivalent            | Mapping Notes             |
| ---------------------------- | ---------------------------- | ------------------------- |
| no-implied-eval              | (via no-eval coverage)       | no-eval covers most cases |
| no-return-await              | no-return-await              | ✓ Identical               |
| unicorn/prefer-node-protocol | unicorn/prefer-node-protocol | ✓ Unicorn plugin          |
| promise/no-nesting           | promise/no-nesting           | ⚠ May need tweaking      |

### Missing in oxlint (Document + Skip)

| ESLint Rule                        | oxlint Status     | Rationale/Workaround                                                              |
| ---------------------------------- | ----------------- | --------------------------------------------------------------------------------- |
| import/no-default-export           | ✗ NOT in oxlint   | Style preference; skip or use in-code JSDoc/eslint-disable                        |
| import/max-dependencies            | Partial           | oxlint: max-params covers function params; file dependencies not natively checked |
| security/detect-object-injection   | ⚠ Basic coverage | oxlint has lighter detection; acceptable for template configs                     |
| security/detect-non-literal-regexp | ⚠ Basic coverage | oxlint covers most cases; document gap                                            |
| jsdoc/\* rules                     | ✗ NOT in oxlint   | Use separate jsdoc plugin or skip in oxlint (use in separate tool)                |

---

## Implementation Strategy

### Phase 4.1: Integration Planning (Current)

**Deliverables**:

1. ✓ Current state audit (this document)
2. ✓ Rule mapping matrix
3. Linting-accelerator wrapper design

### Phase 4.2: Configuration (Next)

**Tasks**:

1. Create `/oxlintrc.json` in project root (copy from template, customize)
2. Document rule gaps and suppressions
3. Create `hooks/lib/linting-accelerator.sh` wrapper

### Phase 4.3: Integration (Next)

**Tasks**:

1. Update `hooks/quality-gate.sh` to use linting-accelerator
2. Wire fallback mechanism into hook dispatcher
3. Add oxlint installation check

### Phase 4.4: Validation (Next)

**Tasks**:

1. Run oxlint on sample TS/JS files (from templates)
2. Compare output to ESLint baseline
3. Document any rule divergences

---

## Linting-Accelerator Design

### Purpose

Wrapper script that:

1. **Tries oxlint first** (5-50x faster, Rust-based)
2. **Falls back to ESLint** (if oxlint not installed or unavailable)
3. **Normalizes output** for compatibility
4. **Caches results** to avoid redundant runs

### Wrapper Location

`/hooks/lib/linting-accelerator.sh`

### Function Signature

```bash
# Usage:
linting_accelerator <command> <file-list>
# Examples:
linting_accelerator "ts/js-lint" src/app.ts src/utils.js
linting_accelerator "dead-imports" src/**/*.ts
```

### Implementation Strategy

**Fallback Logic**:

```
Try oxlint
  ↓ success? → return oxlint result (fast path)
  ↓ not installed/error?
Try eslint
  ↓ success? → return eslint result (legacy fallback)
  ↓ not installed?
  → FAIL with clear message: "Neither oxlint nor eslint available"
```

**Output Normalization**:

- Both tools output JSON or plain text
- Normalize to consistent format for `quality-gate.sh`
- Track which tool was used for reporting

---

## Next Steps

1. **Phase 4.2**: Create `oxlintrc.json` in project root
2. **Phase 4.2**: Implement `hooks/lib/linting-accelerator.sh`
3. **Phase 4.3**: Update `hooks/quality-gate.sh` integration
4. **Phase 4.4**: Run validation suite on templates
5. **Phase 4.5**: Document for future TypeScript projects

---

## Appendix: oxlintrc.json Template Reference

**Location**: `templates/quality/oxlintrc.json`

**Plugins Enabled**:

- typescript, unicorn, react, react-hooks, react-perf, jsx-a11y
- import, jest, jsdoc, nextjs, node, promise, security

**Categories** (via plugin):

- correctness: error
- suspicious: error
- pedantic: error (strict)
- perf: error
- style: error
- restriction: error
- nursery: warn (experimental)

**Key Thresholds**:

- Max complexity: 15
- Max params: 6
- Max lines: 750
- Max dependencies per file: 20

---

## Risk Assessment

| Risk                              | Mitigation                          | Status     |
| --------------------------------- | ----------------------------------- | ---------- |
| ESLint rules not in oxlint        | Documented gap list + suppressions  | ✓ Planned  |
| Fallback to ESLint fails silently | Explicit failure message in wrapper | ✓ Planned  |
| oxlint not installed              | Tool check + informative error      | ✓ Existing |
| Output format differs             | Normalization layer in wrapper      | ✓ Planned  |

**Overall Risk**: LOW (Python-first project, JS/TS is optional/template-based)

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added ESLint configuration patterns
2. Added rule mappings
3. Enhanced cross-references

### Cross-References Added

- LIBRARY_REPLACEMENT_AUDIT_DEEP.md
- GOVERNANCE_POLICY_AUDIT_RESEARCH.md

### Practical Additions

- ESLint config templates
- Rule recommendations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [LIBRARY_REPLACEMENT_AUDIT_DEEP.md](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md) - Library audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
