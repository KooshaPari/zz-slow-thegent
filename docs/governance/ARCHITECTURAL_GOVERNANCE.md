# Architectural Governance: Variation, Redundancy & Legacy Management

**Date:** February 19, 2026
**Status:** Active Policy
**Authority:** Primary decision framework for codebase evolution

---

## 🎯 Core Principle: Zero User Debt = Zero Backwards Compatibility

**Fundamental Rule:** Since we have **no external users** (no user debt), we maintain **zero backwards compatibility**. All changes are breaking changes by design.

**Critical Safety Rule:** **ALWAYS verify parity/migrations BEFORE removals** - This acts as a regression guard.

**AI Agent Pattern:** AI coding agents (Claude, Codex, ChatGPT) **systematically add fallbacks and legacy compatibility** even when explicitly told not to. This is a systemic issue requiring explicit guardrails and verification.

**Implication:**
- ✅ **FIRST:** Verify feature parity and complete migration
- ✅ **THEN:** Remove deprecated code immediately
- ✅ No fallback shims or compatibility layers
- ✅ No "transition periods" or gradual migrations
- ✅ Update all callers simultaneously
- ✅ Delete old implementations entirely
- ✅ **REGRESSION GUARD:** Parity verification prevents breaking changes
- ✅ **AI GUARD:** Explicit rules in AGENTS.md/CLAUDE.md, referenced in prompts
- ✅ **FAIL FAST:** Code should fail and stop, no silent fallbacks

---

## 📊 Part 1: Current State Audit

### 1.1 Backwards Compatibility Patterns Found

#### ✅ **Already Removed (Good)**
- Environment variable fallbacks: `os.environ.get()` → `ThegentSettings` (40+ files migrated)
- Legacy dependency replacements: md5→sha2, lazy_static→OnceLock (complete)

#### ⚠️ **Remaining Patterns (To Remove)**

**Pattern 1: Legacy CLI Directory**
- **Location:** `src/thegent/cli/legacy/`
- **Status:** Still exists, but migrated to use `ThegentSettings`
- **Action:** **DELETE** - No backwards compat needed
- **Rationale:** No external users depend on legacy CLI

**Pattern 2: Deprecated Tool Stubs (atoms-mcp-prod)**
- **Files:** `tools/compliance_verification.py`, `tools/duplicate_detection.py`, `tools/entity_resolver.py`
- **Status:** Backward-compat stubs with warnings
- **Action:** **DELETE** - Update all callers, remove stubs
- **Rationale:** Functionality integrated into canonical implementations

**Pattern 3: Import Fallbacks**
- **Pattern:** `try: from X import Y; except ImportError: from Z import Y`
- **Example:** `compliance_verification.py` lines 13-29
- **Action:** **REMOVE** - Use single canonical import path
- **Rationale:** No need for fallbacks if dependencies are managed

**Pattern 4: Runtime Fallbacks**
- **Pattern:** `try: fast_path(); except: slow_path()`
- **Status:** May exist in performance-critical paths
- **Action:** **EVALUATE** - Keep only if performance-critical AND documented
- **Rationale:** Performance fallbacks are acceptable, compatibility fallbacks are not

### 1.2 Overlapping Implementations Audit

#### **High-Priority Duplications**

**1. CLI Implementations**
- `cli/legacy/` vs `cli/apps/` vs `cli/commands/`
- **Status:** Multiple CLI entry points
- **Action:** **CONSOLIDATE** - Single canonical CLI (`cli/apps/`)
- **Timeline:** Immediate

**2. Configuration Management**
- `config.py` vs `config_provider.py` vs `governance/config_provider_cp.py`
- **Status:** Multiple config systems
- **Action:** **CONSOLIDATE** - Single `ThegentSettings` (already in progress)
- **Timeline:** Complete migration

**3. Discovery Systems**
- `discovery.py` vs `native/discovery_native.py`
- **Status:** Native vs Python implementations
- **Action:** **EVALUATE** - Keep both if performance-critical, document clearly
- **Rationale:** Performance optimization is acceptable duplication

**4. State Management**
- `native/state_shm.py` vs `orchestration/state/shm.py` vs `orchestration/state/shadow.py`
- **Status:** Multiple SHM implementations
- **Action:** **CONSOLIDATE** - Single canonical SHM system
- **Timeline:** Phase 2

**5. Routing Systems**
- `routing/litellm_router.py` vs `routing/auto_router.py` vs `routing/pareto_router.py` vs `agents/crew/router.py`
- **Status:** Multiple routing strategies
- **Action:** **EVALUATE** - Keep if distinct strategies, consolidate if overlapping
- **Rationale:** Strategy pattern is acceptable, duplicate logic is not

### 1.3 Concept Explosion Audit

#### **Variations Found**

**1. Agent Implementations**
- `agents/codex_proxy.py`, `agents/droid.py`, `agents/direct_agents.py`, `agents/smolgents/`, `agents/crew/`
- **Status:** Multiple agent types
- **Action:** **EVALUATE** - Keep if distinct capabilities, consolidate if overlapping
- **Decision Framework:** See Section 2.2

**2. Execution Systems**
- `execution.py`, `orchestration/execution/`, `agents/crew/executor.py`
- **Status:** Multiple execution paths
- **Action:** **CONSOLIDATE** - Single execution engine with strategy pattern
- **Timeline:** Phase 3

**3. IPC Mechanisms**
- `infra/ipc.py`, `infra/shm_manager.py`, `native/state_shm.py`
- **Status:** Multiple IPC systems
- **Action:** **CONSOLIDATE** - Single IPC abstraction (Rust-based)
- **Timeline:** Phase 2

### 1.4 Archive/Backup Patterns

#### **Current State**

**Archives:**
- `trace/ARCHIVE/` - Historical code/config
- `archive/` directories in various projects
- **Status:** Historical reference
- **Action:** **KEEP** - But move to separate repo or `.git/archive/`
- **Rationale:** Historical context valuable, but shouldn't clutter main codebase

**Backups:**
- `*.backup` files scattered throughout
- `.env-backup-*` directories
- `*.backup.*` timestamped files
- **Status:** Temporary files
- **Action:** **DELETE** - Use git history instead
- **Rationale:** Git provides version history, backups are redundant

**Deprecated Code:**
- Files marked `DEPRECATED` but still present
- **Status:** Should be removed
- **Action:** **DELETE** - No deprecation period needed
- **Rationale:** Zero user debt = immediate removal

---

## 🏛️ Part 2: Decision Methodology

### 2.1 When to Keep vs Remove

#### **Keep Multiple Implementations IF:**

1. **Performance Optimization**
   - ✅ Native (Rust/Zig) vs Python implementations
   - ✅ Fast path vs slow path (documented performance fallback)
   - ✅ Different runtime targets (PyPy vs CPython)

2. **Strategy Pattern**
   - ✅ Multiple algorithms for same problem (e.g., routing strategies)
   - ✅ Pluggable implementations (e.g., different agent types)
   - ✅ A/B testing or experimentation

3. **Domain Separation**
   - ✅ Different domains (e.g., CLI vs API vs MCP)
   - ✅ Different contexts (e.g., local vs remote execution)
   - ✅ Clear boundaries and no overlap

#### **Remove Multiple Implementations IF:**

1. **Exact Duplication**
   - ❌ Same logic in multiple files
   - ❌ Copy-paste code
   - ❌ No meaningful differences

2. **Backwards Compatibility**
   - ❌ Legacy code kept "just in case"
   - ❌ Deprecated APIs with fallbacks
   - ❌ Transition shims

3. **Unclear Purpose**
   - ❌ Can't explain why two implementations exist
   - ❌ No documented differences
   - ❌ Both solve same problem identically

### 2.2 Concept Explosion Prevention

#### **Decision Framework: New Concept vs Variation**

**Question 1: Does it solve a NEW problem?**
- ✅ **YES** → New concept, create new module
- ❌ **NO** → Variation, extend existing concept

**Question 2: Is it a different STRATEGY for same problem?**
- ✅ **YES** → Strategy pattern, add to existing module
- ❌ **NO** → Duplication, consolidate

**Question 3: Does it have distinct CAPABILITIES?**
- ✅ **YES** → New concept, create new module
- ❌ **NO** → Variation, extend existing

**Question 4: Is it a PERFORMANCE optimization?**
- ✅ **YES** → Implementation detail, same module
- ❌ **NO** → Evaluate as new concept

#### **Naming Convention**

**New Concept:**
- New module: `agents/new_agent_type/`
- Clear name indicating distinct capability

**Variation:**
- Extend existing: `agents/existing_agent/variation.py`
- Or: `agents/existing_agent/strategies/variation.py`

**Strategy:**
- Same module: `routing/strategies/strategy_name.py`
- Pluggable via configuration

### 2.3 Redundancy Detection

#### **Automated Detection**

**Code Similarity:**
- Use `jscpd` or similar for duplicate detection
- Threshold: >80% similarity = candidate for consolidation
- Action: Review manually, consolidate if exact duplication

**Import Analysis:**
- Track which modules import which
- Identify unused imports (dead code)
- Action: Remove unused code

**Function Signature Matching:**
- Same function name in multiple files
- Same parameters, different implementations
- Action: Consolidate or rename for clarity

#### **Manual Review Triggers**

**When to Review:**
- Before adding new module: Check for existing similar functionality
- During refactoring: Identify consolidation opportunities
- Quarterly audit: Comprehensive redundancy review

**Review Checklist:**
- [ ] Does this solve a problem already solved?
- [ ] Can existing code be extended instead?
- [ ] Is the difference meaningful or accidental?
- [ ] Would consolidation improve maintainability?

### 2.4 Legacy/Fallback Handling

#### **AI Agent Considerations**

**Systemic Issue:** AI coding agents have a **latent urge to "make it work"** leading to:
- Silent fallbacks that hide failures
- Legacy compatibility shims
- Over-engineering (migration systems for simple changes)
- "Hiding bugs" instead of fixing them

**Prevention Strategy:**
1. **Explicit Instructions:** Rules in `AGENTS.md`/`CLAUDE.md` must be explicit and referenced
2. **"Aim Towards" Framing:** Frame removals positively, explain goals and why
3. **Fail Fast Philosophy:** Code should fail and stop, no silent fallbacks
4. **Parity Verification:** Verify before removal (regression guard)
5. **CI Checks:** Automated detection of fallback patterns

**Example Framing:**
```
BAD: "Don't add fallbacks"
GOOD: "Now that we have fully transitioned to a new system and it has been
confirmed to work as intended, let's clean out all backwards compatibility
and fallbacks so we have a DRY, modular system with clear and clean separation
of responsibilities. Once finished, we have a fresh system with no technical debt."
```

#### **Removal Process (With Parity Verification)**

**Step 1: Identify Legacy Code**
- Search for: `deprecated`, `legacy`, `backward`, `compat`, `fallback`
- Review: `cli/legacy/`, `*_legacy.py`, `*_deprecated.py`

**Step 2: Verify Parity (REGRESSION GUARD)**
- ✅ **REQUIRED:** Identify canonical replacement
- ✅ **REQUIRED:** Verify feature parity (all features supported)
- ✅ **REQUIRED:** Verify migration completeness (all callers migrated)
- ✅ **REQUIRED:** Run tests comparing old vs new behavior
- ✅ **REQUIRED:** Document parity verification results
- ⚠️ **DO NOT PROCEED** if parity not verified

**Step 3: Find All Callers**
- Use `grep` to find imports/usages
- List all files that depend on legacy code
- Verify all callers use canonical implementation

**Step 4: Update Callers**
- Update all callers to use canonical implementation
- No gradual migration - update all at once
- Ensure all functionality preserved

**Step 5: Verify Migration**
- Run full test suite
- Compare behavior: old vs new
- Verify no functionality lost
- Check for broken imports

**Step 6: Delete Legacy Code**
- Remove legacy files entirely
- Remove from imports
- Update documentation
- Remove deprecation warnings

**Step 7: Final Verification**
- Run tests again
- Check for broken imports
- Confirm no references remain
- Verify no regressions introduced

#### **Fallback Removal**

### 2.5 Polyglot Governance Orchestrator (Rule of Thumb)

Treat thegent governance as a **superset orchestrator** over native language tools, not a replacement for them.

#### **Architecture Boundary**

- Native tools own language semantics (lint, format, type, test, vuln where applicable).
- thegent owns policy, orchestration, caching, normalized output, governance decisions, and cross-language gates.

#### **Decision Rules**

1. Optimize for leverage first: compose native tools before building custom replacements.
2. Build custom checks only for measured gaps: missing capability, unacceptable latency, unstable output, weak maintenance, or compliance constraints.
3. Require evidence before rewrite: baseline runtime, false-positive rate, CI cost, flake rate, and DX friction.
4. Adapter first, rewriter last: wrappers/post-processors before re-implementing a checker.
5. Enforce compatibility contracts: stable input/output schema, deterministic exit codes, and versioned plugin API.
6. Keep custom logic incremental-aware: changed-files mode locally; full-tree mode in CI/nightly.
7. Roll out enforcement in tiers: advisory -> soft fail -> hard fail with explicit owner/date.
8. Keep policy centralized: one canonical policy spec; avoid scattered hidden rules.
9. Prefer safe auto-fix: formatting/import/order fixes in `fix` mode; unsafe transforms explicitly opt-in.
10. Treat security/compliance as first-class: secrets, supply chain, SBOM, attestations, vulnerability and license policy.
11. Allow exceptions only with governance: owner, reason, expiry, and removal date.
12. Instrument every gate: timing, pass/fail trend, flake rate, and cost telemetry.
13. Keep runner portability: POSIX-first core with language-specific plugins and pinned toolchains.
14. Design for replacement: each custom extension has owner, tests, docs, and deprecation/exit plan.
15. Preserve native-tool parity: upgrade custom behavior when upstream tools catch up.

**Pattern: `try: new(); except: old()`**
- **Action:** Remove `except` clause entirely
- **Rationale:** If new code fails, fix it, don't fallback

**Pattern: `if legacy_flag: old(); else: new()`**
- **Action:** Remove flag and old code
- **Rationale:** No need for feature flags if no users

**Pattern: Import fallbacks**
- **Action:** Fix imports, remove fallbacks
- **Rationale:** Dependencies should be managed, not worked around

### 2.5 Archive/Backup Management

#### **Archive Policy**

**What to Archive:**
- ✅ Historical reference (moved implementations)
- ✅ Research documents (completed research)
- ✅ Design decisions (ADRs, architecture docs)

**What NOT to Archive:**
- ❌ Deprecated code (delete instead)
- ❌ Backup files (use git)
- ❌ Temporary files (delete)

**Archive Location:**
- Separate git repo: `thegent-archive/`
- Or: `.git/archive/` directory (not tracked)
- Or: External documentation site

**Archive Structure:**
```
archive/
  YYYY-MM-DD-description/
    - original_code/
    - migration_notes.md
    - decision_record.md
```

#### **Backup Policy**

**No Backup Files:**
- ❌ No `*.backup` files in repo
- ❌ No `.env-backup-*` directories
- ❌ No timestamped backup files

**Use Git Instead:**
- ✅ Git history for version tracking
- ✅ Git tags for releases
- ✅ Git branches for experiments

**Exception:**
- ✅ Build artifacts (`.build/`, `target/`) - in `.gitignore`
- ✅ Temporary test files - cleaned up automatically

---

## 🛡️ Part 2.6: Parity Verification Process (Regression Guard)

### **Critical Requirement: Verify Before Remove**

**Rule:** **NEVER remove code without first verifying parity and migration completeness.**

### **Parity Verification Checklist**

**Before Removal:**
- [ ] **Identify Canonical Replacement**
  - What is the new implementation?
  - Where is it located?
  - What is its API?

- [ ] **Feature Parity Audit**
  - List all features of old implementation
  - Verify each feature exists in new implementation
  - Document any differences (if acceptable)
  - **DO NOT PROCEED** if features missing

- [ ] **Migration Completeness**
  - Find all callers of old implementation
  - Verify all callers migrated to new implementation
  - Update any remaining callers
  - **DO NOT PROCEED** if callers not migrated

- [ ] **Behavioral Parity Testing**
  - Create test comparing old vs new behavior
  - Run tests with both implementations
  - Verify outputs match (or acceptable differences documented)
  - **DO NOT PROCEED** if behavior differs unexpectedly

- [ ] **Documentation**
  - Document parity verification results
  - Document any intentional differences
  - Update migration guide if needed

### **Parity Verification Template**

```markdown
## Parity Verification: [Old Implementation] → [New Implementation]

**Date:** YYYY-MM-DD
**Verifier:** [Name]

### Feature Comparison
| Feature | Old Implementation | New Implementation | Status |
|---------|-------------------|-------------------|--------|
| Feature 1 | ✅ | ✅ | ✅ Parity |
| Feature 2 | ✅ | ✅ | ✅ Parity |
| Feature 3 | ✅ | ❌ | ⚠️ Missing - [Action] |

### Migration Status
- [ ] All callers identified
- [ ] All callers migrated
- [ ] Tests updated
- [ ] Documentation updated

### Test Results
- [ ] Behavioral tests pass
- [ ] Performance acceptable
- [ ] No regressions

### Approval
- [ ] Parity verified
- [ ] Migration complete
- [ ] Ready for removal
```

### **Automated Parity Checks**

**CI/CD Integration:**
```bash
# Run parity tests before removal
pytest tests/parity/ --markers parity_check

# Compare old vs new behavior
python scripts/verify_parity.py --old old_module --new new_module
```

**Test Structure:**
```python
# tests/parity/test_cli_legacy_parity.py
def test_cli_legacy_parity():
    """Verify cli/apps has parity with cli/legacy."""
    # Test all features from legacy
    # Compare outputs
    # Verify no functionality lost
```

### **Regression Guard Enforcement**

**Pre-Removal Gate:**
- ✅ Parity verification required
- ✅ Migration completeness required
- ✅ Test results required
- ✅ Documentation required
- ⚠️ **BLOCK** removal if any check fails

**Post-Removal Verification:**
- ✅ Run full test suite
- ✅ Verify no broken imports
- ✅ Check for regressions
- ✅ Monitor for issues

---

## 📋 Part 3: Implementation Plan

### 3.1 Immediate Actions (Week 1)

**Priority 1: Remove Legacy CLI**
- [ ] **PARITY CHECK:** Verify `cli/apps/` has all features from `cli/legacy/`
- [ ] **MIGRATION CHECK:** Verify all callers migrated to `cli/apps/`
- [ ] **TEST CHECK:** Run tests comparing old vs new behavior
- [ ] Audit `cli/legacy/` usage
- [ ] Update all callers to `cli/apps/`
- [ ] **ONLY AFTER PARITY VERIFIED:** Delete `cli/legacy/` directory
- [ ] Update documentation

**Priority 2: Remove Deprecated Stubs**
- [ ] **PARITY CHECK:** Verify canonical implementations have all features
- [ ] **MIGRATION CHECK:** Verify all test files use canonical imports
- [ ] **TEST CHECK:** Run tests with canonical implementations
- [ ] Find all deprecated tool stubs
- [ ] Update callers to canonical implementations
- [ ] **ONLY AFTER PARITY VERIFIED:** Delete stub files
- [ ] Remove deprecation warnings

**Priority 3: Clean Backup Files**
- [ ] Find all `*.backup` files
- [ ] **VERIFY:** No active code depends on backup files
- [ ] Delete backup files
- [ ] Add `*.backup` to `.gitignore`
- [ ] Document git-based backup policy

### 3.2 Short-Term Actions (Weeks 2-4)

**Consolidation Phase 1:**
- [ ] Consolidate config systems → `ThegentSettings`
- [ ] Consolidate SHM implementations → single system
- [ ] Consolidate IPC mechanisms → Rust-based abstraction

**Redundancy Removal:**
- [ ] Run code similarity analysis
- [ ] Identify duplicate functions
- [ ] Consolidate or rename for clarity

**Concept Audit:**
- [ ] Review agent implementations
- [ ] Document distinct capabilities
- [ ] Consolidate overlapping implementations

### 3.3 Medium-Term Actions (Months 2-3)

**Consolidation Phase 2:**
- [ ] Consolidate execution systems
- [ ] Consolidate routing strategies (if overlapping)
- [ ] Consolidate discovery systems (if overlapping)

**Archive Migration:**
- [ ] Move historical archives to separate repo
- [ ] Document archive policy
- [ ] Set up archive maintenance process

**Governance Automation:**
- [ ] Set up CI checks for deprecated patterns
- [ ] Add linting rules for fallbacks
- [ ] Create audit scripts

### 3.4 Ongoing Governance

**Quarterly Audits:**
- [ ] Redundancy review
- [ ] Concept explosion check
- [ ] Legacy code audit
- [ ] Archive cleanup

**Pre-Commit Checks:**
- [ ] No `*.backup` files
- [ ] No deprecated patterns
- [ ] No backwards compat code

**Documentation:**
- [ ] Keep decision records updated
- [ ] Document consolidation decisions
- [ ] Maintain architecture diagrams

---

## 🔍 Part 4: Detection & Enforcement

### 4.1 Automated Detection

#### **CI/CD Checks**

**Pattern Detection:**
```bash
# Check for deprecated patterns
grep -r "deprecated\|legacy\|backward\|compat" --include="*.py" src/
grep -r "\.backup" --include="*" .
grep -r "try:.*except.*fallback" --include="*.py" src/
```

**Code Similarity:**
```bash
# Install jscpd
npm install -g jscpd

# Run duplicate detection
jscpd src/ --min-lines 10 --min-tokens 50 --threshold 80
```

**Import Analysis:**
```bash
# Find unused imports
ruff check --select F401 src/
```

#### **Linting Rules**

**Ruff Configuration:**
```toml
[tool.ruff.lint]
# Disallow deprecated patterns
select = ["F", "E", "W", "B", "C4"]

[tool.ruff.lint.per-file-ignores]
# Allow in test files only
"**/test_*.py" = ["F401"]  # Unused imports OK in tests
```

**Custom Rules:**
- No `*.backup` files in repo
- No `deprecated` without removal date
- No `backward compat` comments

### 4.2 Manual Review Process

#### **Pre-Commit Checklist**

Before committing:
- [ ] No backwards compatibility code added
- [ ] No fallback patterns introduced
- [ ] No duplicate implementations created
- [ ] No backup files included
- [ ] New concepts vs variations evaluated
- [ ] **PARITY VERIFIED:** If removing code, parity checked first

#### **Code Review Checklist**

Reviewers check:
- [ ] Does this duplicate existing functionality?
- [ ] Is backwards compatibility needed? (Answer: NO)
- [ ] Are fallbacks necessary? (Answer: NO, except performance)
- [ ] Is this a new concept or variation?
- [ ] Are archives/backups handled correctly?
- [ ] **PARITY VERIFIED:** If removing code, was parity verified?
- [ ] **MIGRATION COMPLETE:** Are all callers migrated?
- [ ] **TESTS PASS:** Do tests verify parity?

### 4.3 Enforcement Escalation

#### **Violation Levels**

**Level 1: Warning**
- Minor pattern violation
- Action: Fix in next commit
- Example: Import fallback in non-critical code

**Level 2: Block**
- Significant violation
- Action: Fix before merge
- Example: New backwards compat code

**Level 3: Revert**
- Critical violation
- Action: Revert commit
- Example: Deprecated code reintroduced

#### **Escalation Process**

1. **Automated Detection** → CI fails
2. **Reviewer Feedback** → Request changes
3. **Architecture Review** → If pattern unclear
4. **Policy Update** → If policy needs clarification

---

## 📚 Part 5: Examples & Patterns

### 5.1 Good Patterns ✅

**Performance Fallback (Acceptable):**
```python
# ✅ GOOD: Performance optimization, documented
def fast_json_parse(data: bytes) -> dict:
    """Parse JSON with performance fallback."""
    try:
        return orjson.loads(data)  # Fast path
    except Exception:
        return json.loads(data)  # Slow path (performance fallback)
```

**Strategy Pattern (Acceptable):**
```python
# ✅ GOOD: Multiple strategies, pluggable
class Router:
    strategies = {
        "litellm": LiteLLMRouter(),
        "pareto": ParetoRouter(),
        "auto": AutoRouter(),
    }
```

**Native Optimization (Acceptable):**
```python
# ✅ GOOD: Native vs Python, performance-critical
if IS_NATIVE_AVAILABLE:
    from .native import fast_discovery
else:
    from .python import slow_discovery
```

### 5.2 Bad Patterns ❌

**Backwards Compatibility (Remove):**
```python
# ❌ BAD: Backwards compat shim
def old_function():
    warnings.warn("Deprecated, use new_function()")
    return new_function()  # Remove this entirely
```

**Import Fallback (Remove):**
```python
# ❌ BAD: Import fallback
try:
    from .canonical import thing
except ImportError:
    from .legacy import thing  # Fix imports instead
```

**Duplicate Implementation (Remove):**
```python
# ❌ BAD: Same logic, different file
# file1.py
def parse_config():
    # 50 lines of parsing logic

# file2.py
def parse_config():
    # Same 50 lines, slightly different  # Consolidate!
```

**Backup Files (Remove):**
```bash
# ❌ BAD: Backup files in repo
config.py.backup
.env.backup.20260130
# Use git history instead
```

### 5.3 Migration Examples

**Example 1: Removing Legacy CLI**

**Before:**
```
cli/
  legacy/
    cli_legacy.py  # Old implementation
  apps/
    main.py  # New implementation
```

**After:**
```
cli/
  apps/
    main.py  # Single canonical implementation
```

**Migration Steps:**
1. Find all imports of `cli.legacy`
2. Update to `cli.apps`
3. Delete `cli/legacy/` directory
4. Update tests

**Example 2: Consolidating Config**

**Before:**
```python
# config.py
def get_config():
    return os.environ.get("THGENT_X", "default")


# config_provider.py
def get_config():
    return settings.x  # Different implementation
```

**After:**
```python
# config.py (canonical)
from thegent.config import ThegentSettings


def get_config():
    settings = ThegentSettings()
    return settings.x
```

**Migration Steps:**
1. Migrate `config_provider.py` to use `ThegentSettings`
2. Update all callers
3. Delete `config_provider.py`
4. Update imports

---

## 📊 Part 6: Metrics & Tracking

### 6.1 Key Metrics

**Redundancy Metrics:**
- Code similarity percentage (target: <5%)
- Duplicate function count (target: 0)
- Unused import count (target: 0)

**Legacy Metrics:**
- Deprecated code files (target: 0)
- Backwards compat patterns (target: 0)
- Fallback patterns (target: 0, except performance)

**Archive Metrics:**
- Backup files in repo (target: 0)
- Archive size (track growth)
- Archive access frequency

### 6.2 Reporting

**Weekly:**
- New violations detected
- Fixes completed
- Patterns introduced

**Monthly:**
- Redundancy audit results
- Legacy code removal progress
- Archive cleanup status

**Quarterly:**
- Comprehensive audit
- Policy review
- Metrics trend analysis

---

## 🎯 Summary

### Core Principles

1. **Zero User Debt = Zero Backwards Compatibility**
   - Remove deprecated code immediately
   - No fallback shims
   - Update all callers simultaneously

2. **Consolidate Redundancies**
   - Remove duplicate implementations
   - Consolidate overlapping code
   - Use strategy pattern for variations

3. **Prevent Concept Explosion**
   - New concept vs variation decision framework
   - Clear naming conventions
   - Document distinct capabilities

4. **Manage Archives Properly**
   - No backup files in repo
   - Use git for version history
   - Archive historical code separately

5. **Automate Detection**
   - CI/CD checks for violations
   - Linting rules for patterns
   - Regular audits

### Next Steps

1. **Immediate:** Remove legacy CLI, deprecated stubs, backup files
2. **Short-term:** Consolidate config, SHM, IPC systems
3. **Medium-term:** Archive migration, governance automation
4. **Ongoing:** Quarterly audits, pattern enforcement

---

**Last Updated:** 2026-02-19
**Next Review:** 2026-03-19
**Authority:** Architecture team

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->
## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.

