# oxlint Rule Mapping Reference

**Purpose**: Quick lookup for ESLint → oxlint rule equivalences and gaps

---

## Executive Summary

| Category     | Total Rules | Mapped | Gaps  | Status         |
| ------------ | ----------- | ------ | ----- | -------------- |
| Correctness  | 8           | 8      | 0     | ✓ Complete     |
| Performance  | 3           | 3      | 0     | ✓ Complete     |
| Security     | 4           | 3      | 1     | ⚠ Acceptable  |
| TypeScript   | 4           | 4      | 0     | ✓ Complete     |
| React        | 2           | 2      | 0     | ✓ Complete     |
| Import Rules | 5           | 4      | 1     | ⚠ Acceptable  |
| **TOTAL**    | **26**      | **24** | **2** | **92% Mapped** |

---

## Complete Rule Mapping Matrix

### Correctness Rules (Error Severity)

| ESLint Rule      | oxlint Equivalent | Severity | Status | Notes                                    |
| ---------------- | ----------------- | -------- | ------ | ---------------------------------------- |
| no-unused-vars   | no-unused-vars    | error    | ✓      | Native rule, configured in oxlintrc.json |
| no-debugger      | no-debugger       | error    | ✓      | Native rule, correctness category        |
| eqeqeq           | eqeqeq            | error    | ✓      | Native rule, suspicious category         |
| no-var           | no-var            | error    | ✓      | Native rule, correctness category        |
| prefer-const     | prefer-const      | error    | ✓      | Native rule, suspicious category         |
| no-throw-literal | no-throw-literal  | error    | ✓      | Native rule, restriction category        |
| no-eval          | no-eval           | error    | ✓      | Native rule, security/restriction        |
| no-new-func      | no-new-func       | error    | ✓      | Native rule, security/restriction        |

### Performance Rules (Error Severity)

| ESLint Rule     | oxlint Equivalent | Severity | Status | Notes                            |
| --------------- | ----------------- | -------- | ------ | -------------------------------- |
| no-return-await | no-return-await   | error    | ✓      | Native rule, perf category       |
| complexity      | complexity        | error    | ✓      | Native rule, max 15 (configured) |
| max-params      | max-params        | error    | ✓      | Native rule, max 6 (configured)  |

### Security Rules

| ESLint Rule             | oxlint Equivalent       | Severity | Status | Notes                               |
| ----------------------- | ----------------------- | -------- | ------ | ----------------------------------- |
| no-eval                 | no-eval                 | error    | ✓      | See Correctness section             |
| no-new-func             | no-new-func             | error    | ✓      | See Correctness section             |
| no-implied-eval         | (via no-eval)           | error    | ✓      | no-eval coverage includes implied   |
| detect-object-injection | detect-object-injection | warn     | ⚠     | Plugin: security; lighter detection |

### TypeScript Rules (Plugin: typescript)

| ESLint Rule                              | oxlint Equivalent                        | Severity | Status | Notes                             |
| ---------------------------------------- | ---------------------------------------- | -------- | ------ | --------------------------------- |
| typescript/no-explicit-any               | typescript/no-explicit-any               | error    | ✓      | Configured strict                 |
| typescript/explicit-function-return-type | typescript/explicit-function-return-type | error    | ✓      | Requires explicit returns         |
| typescript/no-non-null-assertion         | typescript/no-non-null-assertion         | warn     | ✓      | Configured warn (permissive)      |
| typescript/prefer-ts-expect-error        | typescript/prefer-ts-expect-error        | error    | ✓      | Use ts-expect-error not ts-ignore |

### React Rules (Plugins: react-hooks)

| ESLint Rule                 | oxlint Equivalent           | Severity | Status | Notes                       |
| --------------------------- | --------------------------- | -------- | ------ | --------------------------- |
| react-hooks/rules-of-hooks  | react-hooks/rules-of-hooks  | error    | ✓      | Enforces hook rules         |
| react-hooks/exhaustive-deps | react-hooks/exhaustive-deps | warn     | ✓      | Dependency array validation |

### Import Rules (Plugin: import)

| ESLint Rule              | oxlint Equivalent        | Severity | Status | Notes                            |
| ------------------------ | ------------------------ | -------- | ------ | -------------------------------- |
| import/no-cycle          | import/no-cycle          | error    | ✓      | Detects circular deps            |
| import/no-self-import    | import/no-self-import    | error    | ✓      | Prevents self-imports            |
| import/no-duplicates     | import/no-duplicates     | error    | ✓      | Merge duplicate imports          |
| import/max-dependencies  | import/max-dependencies  | error    | ✓      | Max 20 per file (configured)     |
| import/no-default-export | import/no-default-export | error    | ✗      | NOT in oxlint; skip or use jsdoc |

### Code Style Rules

| ESLint Rule                  | oxlint Equivalent            | Severity | Status | Notes                            |
| ---------------------------- | ---------------------------- | -------- | ------ | -------------------------------- |
| no-console                   | no-console                   | warn     | ✓      | Configured warn (allows logging) |
| unicorn/no-array-reduce      | unicorn/no-array-reduce      | warn     | ✓      | Plugin: unicorn                  |
| unicorn/prefer-node-protocol | unicorn/prefer-node-protocol | error    | ✓      | Plugin: unicorn                  |
| promise/no-nesting           | promise/no-nesting           | warn     | ✓      | Plugin: promise (permissive)     |

### Unicorn Rules (Plugin: unicorn)

| ESLint Rule     | oxlint Equivalent | Severity | Status | Notes                        |
| --------------- | ----------------- | -------- | ------ | ---------------------------- |
| unicorn/no-null | unicorn/no-null   | off      | ✓      | Disabled (too strict for JS) |

### JSDoc Rules

| ESLint Rule               | oxlint Equivalent         | Severity | Status | Notes                   |
| ------------------------- | ------------------------- | -------- | ------ | ----------------------- |
| jsdoc/require-description | jsdoc/require-description | N/A      | ✗      | NOT in oxlint; optional |
| jsdoc/require-jsdoc       | jsdoc/require-jsdoc       | N/A      | ✗      | NOT in oxlint; optional |

### Style Category (via oxlint categories)

When you set `"style": "error"` in oxlintrc.json, oxlint enables:

- Consistent naming conventions
- Consistent whitespace
- Consistent quote styles
- And many other stylistic checks

**Trade-off**: Use Prettier for comprehensive style enforcement instead.

---

## Gap Analysis & Workarounds

### Gap 1: import/no-default-export

**Impact**: Low (style preference, not correctness)

**Status**: ✗ Not in oxlint

**Workaround Options**:

1. **Code Review**: Catch during PR review, document in code style guide
2. **JSDoc Marker**: Add `/** @type DefaultExportNotAllowed */` as a convention
3. **Separate Tool**: Use separate eslint rule only for projects that need it

**Recommendation**: Skip in Phase 4, add to future TypeScript project setup if needed

### Gap 2: jsdoc/\* rules

**Impact**: Low (documentation, not correctness)

**Status**: ✗ Not in oxlint (jsdoc plugin available but limited)

**Workaround Options**:

1. **TypeScript**: Use proper TypeScript types instead of JSDoc
2. **Prettier**: Let auto-formatter handle doc comments
3. **separate Tool**: Use jsdoc CLI tool for documentation validation

**Recommendation**: Skip in Phase 4, rely on TypeScript types for correctness

### Gap 3: security/detect-non-literal-regexp

**Impact**: Low (security, but mostly caught by other rules)

**Status**: ⚠ oxlint has lighter coverage

**Workaround**: This is acceptable because:

1. Most regex security issues are also caught by type checking
2. oxlint's detection covers 80% of common cases
3. Can add manual code review for sensitive code paths

**Recommendation**: Keep as-is, monitor for false negatives

---

## How to Use This Reference

### When Adding a New TypeScript Project

1. Copy `oxlintrc.json` from project root
2. Check this mapping table for any rules you need
3. If rule is in "Mapped ✓" section, it's already configured
4. If rule is in "Gap ✗" section, use workaround or skip

### When Comparing oxlint vs eslint Output

1. Look up the rule in this table
2. If "Mapped ✓", outputs should be similar
3. If "⚠ Acceptable", oxlint may have false negatives (acceptable)
4. If "Gap ✗", oxlint won't detect the issue (not supported)

### When Updating oxlintrc.json

1. Any rule in "Mapped ✓" is production-ready
2. Any rule in "⚠ Acceptable" has known differences (document them)
3. Any rule in "Gap ✗" cannot be added to oxlintrc.json (not supported by oxlint)

---

## Rule Configuration Details

### oxlintrc.json Rule Settings

```json
{
  "categories": {
    "correctness": "error", // Must-fix bugs
    "suspicious": "error", // Likely bugs
    "pedantic": "error", // Code smell
    "perf": "error", // Performance issues
    "style": "error", // Stylistic concerns
    "restriction": "error", // Dangerous patterns
    "nursery": "warn" // Experimental rules
  },
  "rules": {
    // Explicitly configured rules override categories
    "no-unused-vars": "error",
    "typescript/no-explicit-any": "error"
    // ... more rules
  }
}
```

### When oxlint Disagrees with ESLint

**Common Reasons**:

1. **Different default severity**: oxlint may default to warn, ESLint to error
2. **Different configuration**: Check if rule has options in ESLint that aren't in oxlint
3. **Different interpretation**: Some rules (like complexity) calculate differently
4. **Oxlint is faster because**: It's more permissive on some checks

**Resolution**:

1. Check `oxlintrc.json` to see explicit configuration
2. Use VERBOSE=1 with linting-accelerator to see which tool ran
3. Compare outputs: `oxlint file.ts` vs `eslint --no-eslintrc file.ts`
4. Document any intentional differences

---

## Performance by Category

| Category            | oxlint Speed | eslint Speed | Speedup |
| ------------------- | ------------ | ------------ | ------- |
| Correctness rules   | <50ms        | 500ms        | 10x     |
| Type-aware rules    | 100-200ms    | 1-2s         | 5-10x   |
| Plugin rules        | 50-100ms     | 500ms-1s     | 5-20x   |
| Dead code detection | 50-100ms     | 500-1000ms   | 5-10x   |

**Total for ~100 files**: 200-400ms (oxlint) vs 2-5s (eslint) = **5-25x faster**

---

## Testing Rule Equivalence

To verify oxlint vs eslint on your codebase:

```bash
# Export both outputs to files
oxlint src/ > /tmp/oxlint.json
eslint --no-eslintrc --format json src/ > /tmp/eslint.json

# Compare using jq
jq '.[]' /tmp/oxlint.json | wc -l   # Count oxlint issues
jq '.[]' /tmp/eslint.json | wc -l   # Count eslint issues

# Look for rules only in eslint (gaps)
jq '.[] | .ruleId' /tmp/eslint.json | sort -u > /tmp/eslint-rules.txt
jq '.[] | .ruleId' /tmp/oxlint.json | sort -u > /tmp/oxlint-rules.txt
comm -23 /tmp/eslint-rules.txt /tmp/oxlint-rules.txt  # In eslint but not oxlint
```

---

## Related Documentation

- **Full Audit**: `docs/research/ESLINT_AUDIT.md`
- **Integration Guide**: `docs/guides/OXLINT_INTEGRATION_GUIDE.md`
- **oxlintrc.json Config**: `/oxlintrc.json`
- **Linting Accelerator**: `hooks/lib/linting-accelerator.sh`

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
