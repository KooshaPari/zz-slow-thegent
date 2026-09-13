# Decision Methodology: Keep vs Remove

**Quick Reference Guide** for architectural decisions

---

## 🎯 Core Principle

**Zero User Debt = Zero Backwards Compatibility**

If we have no external users, we maintain no backwards compatibility. All changes are breaking changes by design.

**🛡️ Critical Safety Rule: Always verify parity/migrations BEFORE removals**

This acts as a regression guard to prevent breaking changes.

**🤖 AI Agent Pattern: Agents systematically add fallbacks**

AI coding agents (Claude, Codex, ChatGPT) have a systemic tendency to add fallbacks and legacy compatibility even when explicitly told not to. This requires:

- Explicit rules in AGENTS.md/CLAUDE.md
- "Aim towards" framing (positive direction, not just "don't do X")
- Fail fast philosophy (code should fail and stop)
- CI checks for fallback patterns

---

## 🤔 Decision Trees

### Decision 1: Is This Backwards Compatibility?

```
Is this code kept for backwards compatibility?
│
├─ YES → REMOVE
│   └─ No user debt = no backwards compat needed
│
└─ NO → Continue to Decision 2
```

**Examples:**

- ❌ Legacy CLI directory → **REMOVE**
- ❌ Deprecated tool stubs → **REMOVE**
- ❌ Backward compat re-exports → **REMOVE**

---

### Decision 2: Is This a Fallback?

```
Is this a fallback pattern?
│
├─ Performance Fallback → KEEP (if documented)
│   └─ Example: try: fast_path(); except: slow_path()
│
├─ Compatibility Fallback → REMOVE
│   └─ Example: try: new(); except: old()
│
└─ Dependency Fallback → REMOVE
    └─ Example: try: from X import Y; except: from Z import Y
```

**Examples:**

- ✅ Performance: Fast JSON parser with slow fallback → **KEEP**
- ❌ Compatibility: New API with old API fallback → **REMOVE**
- ❌ Dependency: Import fallback → **REMOVE** (fix imports instead)

---

### Decision 3: Is This Duplication?

```
Are there multiple implementations of the same thing?
│
├─ Exact Duplication → CONSOLIDATE
│   └─ Same logic, different files
│
├─ Performance Optimization → KEEP BOTH (if documented)
│   └─ Native vs Python, fast vs slow path
│
├─ Strategy Pattern → KEEP BOTH (if distinct)
│   └─ Different algorithms for same problem
│
└─ Unclear Purpose → EVALUATE
    └─ Can't explain why two exist
```

**Examples:**

- ❌ Same parsing logic in 2 files → **CONSOLIDATE**
- ✅ Native Rust vs Python implementation → **KEEP BOTH**
- ✅ Multiple routing strategies → **KEEP BOTH** (strategy pattern)
- ❌ Two config systems doing same thing → **CONSOLIDATE**

---

### Decision 4: Is This a New Concept or Variation?

```
Is this a new concept or variation of existing?
│
├─ New Problem → NEW CONCEPT
│   └─ Create new module
│
├─ Different Strategy → VARIATION
│   └─ Add to existing module (strategy pattern)
│
├─ Performance Optimization → IMPLEMENTATION DETAIL
│   └─ Same module, different implementation
│
└─ Unclear → EVALUATE
    └─ Review with team
```

**Examples:**

- ✅ New agent type solving new problem → **NEW CONCEPT**
- ✅ Different routing algorithm → **VARIATION** (strategy)
- ✅ Fast vs slow implementation → **IMPLEMENTATION DETAIL**
- ❌ Can't explain difference → **EVALUATE**

---

### Decision 5: Is This Archive/Backup?

```
Is this an archive or backup?
│
├─ Historical Reference → ARCHIVE (move to separate repo)
│   └─ Valuable context, but clutters main codebase
│
├─ Backup File → DELETE
│   └─ Use git history instead
│
├─ Deprecated Code → DELETE
│   └─ No need to archive deprecated code
│
└─ Temporary File → DELETE
    └─ Should be cleaned up automatically
```

**Examples:**

- ✅ Historical architecture docs → **ARCHIVE** (move to separate repo)
- ❌ `*.backup` files → **DELETE** (use git)
- ❌ Deprecated code → **DELETE** (no archive needed)
- ❌ Temporary test files → **DELETE**

---

## 📋 Quick Checklist

**Before removing code, ALWAYS verify:**

- [ ] **PARITY CHECKED:** New implementation has all features?
- [ ] **MIGRATION COMPLETE:** All callers migrated?
- [ ] **TESTS PASS:** Parity tests verify behavior?
- [ ] **DOCUMENTED:** Parity verification documented?

**Before adding code, ask:**

- [ ] **Is this backwards compatibility?** → **REMOVE** (after parity check)
- [ ] **Is this a compatibility fallback?** → **REMOVE** (after parity check)
- [ ] **Is this exact duplication?** → **CONSOLIDATE** (after parity check)
- [ ] **Is this a backup file?** → **DELETE**
- [ ] **Is this deprecated code?** → **DELETE** (after parity check)

**Before keeping code, ask:**

- [ ] **Does it solve a NEW problem?** → New concept
- [ ] **Is it a different STRATEGY?** → Variation (strategy pattern)
- [ ] **Is it a PERFORMANCE optimization?** → Implementation detail
- [ ] **Can I explain why two exist?** → If no, consolidate

---

## 🚫 Anti-Patterns (Never Do)

1. ❌ **Silent fallbacks** (AI agents love these!)
   - Pattern: `try: do_thing(); except: pass` or `try: do_thing(); except: return default`
   - Action: **REMOVE**, code should fail and stop
   - **AI Guard:** Explicit rule in AGENTS.md: "Code must fail loudly, no silent fallbacks"

2. ❌ **Backwards compatibility shims**
   - Pattern: `def old(): warnings.warn(); return new()`
   - Action: **DELETE** old function, update callers

3. ❌ **Legacy compatibility layers**
   - Pattern: `if legacy_flag: old(); else: new()`
   - Action: **REMOVE** flag and old code
   - **AI Guard:** "No legacy compatibility. Zero user debt = zero backwards compatibility"

4. ❌ **Import fallbacks**
   - Pattern: `try: from X import Y; except: from Z import Y`
   - Action: **FIX** imports, remove fallback

5. ❌ **Deprecated code with warnings**
   - Pattern: `warnings.warn("deprecated")` but code still exists
   - Action: **DELETE** code, no warnings needed

6. ❌ **Backup files in repo**
   - Pattern: `*.backup`, `.env-backup-*`
   - Action: **DELETE**, use git history

7. ❌ **Duplicate implementations**
   - Pattern: Same logic in multiple files
   - Action: **CONSOLIDATE** into single implementation

8. ❌ **Error hiding**
   - Pattern: `try: thing(); except: delete_from_db()` (hide bugs)
   - Action: **REMOVE**, fix the bug instead
   - **AI Guard:** "Never hide errors. Fail fast, fail loudly."

---

## ✅ Good Patterns (Do This)

1. ✅ **Performance fallbacks** (documented)

   ```python
   def fast_parse(data):
       try:
           return orjson.loads(data)  # Fast
       except:
           return json.loads(data)  # Slow (performance fallback)
   ```

2. ✅ **Strategy pattern** (distinct strategies)

   ```python
   class Router:
       strategies = {
           "litellm": LiteLLMRouter(),
           "pareto": ParetoRouter(),
       }
   ```

3. ✅ **Native optimizations** (performance-critical)
   ```python
   if IS_NATIVE_AVAILABLE:
       from .native import fast_discovery
   else:
       from .python import slow_discovery
   ```

---

## 🎯 Decision Matrix

| Pattern                | Keep?  | Rationale               |
| ---------------------- | ------ | ----------------------- |
| Backwards compat shim  | ❌ NO  | No user debt            |
| Deprecated code        | ❌ NO  | Delete immediately      |
| Compatibility fallback | ❌ NO  | Fix instead of fallback |
| Performance fallback   | ✅ YES | If documented           |
| Exact duplication      | ❌ NO  | Consolidate             |
| Strategy pattern       | ✅ YES | If distinct strategies  |
| Native optimization    | ✅ YES | Performance-critical    |
| Backup files           | ❌ NO  | Use git                 |
| Archive (historical)   | ✅ YES | Move to separate repo   |

---

## 📚 References

- **Full Governance:** `docs/governance/ARCHITECTURAL_GOVERNANCE.md`
- **Audit Report:** `docs/governance/BACKWARDS_COMPAT_AUDIT_2026-02-19.md`
- **Policy:** Zero user debt = zero backwards compatibility

---

**Last Updated:** 2026-02-19
**Quick Reference:** Use this for daily decisions
