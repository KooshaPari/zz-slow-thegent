# Parity Verification Template

**Use this template before removing any legacy/deprecated code.**

---

## Parity Verification: [Old Implementation] → [New Implementation]

**Date:** YYYY-MM-DD
**Verifier:** [Name]
**Status:** ⏳ In Progress / ✅ Complete / ❌ Failed

---

## 1. Feature Comparison

| Feature   | Old Implementation | New Implementation | Status       | Notes                |
| --------- | ------------------ | ------------------ | ------------ | -------------------- |
| Feature 1 | ✅ Location/API    | ✅ Location/API    | ✅ Parity    | -                    |
| Feature 2 | ✅ Location/API    | ✅ Location/API    | ✅ Parity    | -                    |
| Feature 3 | ✅ Location/API    | ⚠️ Different API   | ⚠️ Review    | [Explain difference] |
| Feature 4 | ✅ Location/API    | ❌ Missing         | ❌ **BLOCK** | [Action required]    |

**Summary:**

- ✅ Features with parity: X
- ⚠️ Features with differences: Y (acceptable)
- ❌ Missing features: Z (**BLOCK REMOVAL**)

---

## 2. Migration Completeness

### Callers Identified

| Caller Location | Old Import          | New Import          | Status       |
| --------------- | ------------------- | ------------------- | ------------ |
| `file1.py`      | `from old import X` | `from new import X` | ✅ Migrated  |
| `file2.py`      | `from old import Y` | `from new import Y` | ✅ Migrated  |
| `file3.py`      | `from old import Z` | ❌ Not migrated     | ❌ **BLOCK** |

**Summary:**

- Total callers: X
- Migrated: Y
- Remaining: Z (**BLOCK REMOVAL** if > 0)

### Migration Commands

```bash
# Find all callers
grep -r "old_module\|old.import" src/ tests/

# Verify migration
grep -r "old_module\|old.import" src/ tests/ | wc -l  # Should be 0
```

---

## 3. Behavioral Parity Testing

### Test Results

| Test Case                   | Old Implementation | New Implementation | Status    |
| --------------------------- | ------------------ | ------------------ | --------- |
| Test 1: Basic functionality | ✅ Pass            | ✅ Pass            | ✅ Parity |
| Test 2: Edge case handling  | ✅ Pass            | ✅ Pass            | ✅ Parity |
| Test 3: Error handling      | ✅ Pass            | ⚠️ Different       | ⚠️ Review |
| Test 4: Performance         | ✅ 100ms           | ✅ 50ms            | ✅ Better |

**Summary:**

- Tests passing: X/Y
- Behavioral differences: Z (acceptable/unacceptable)
- Performance: Better/Same/Worse

### Test Code

```python
# tests/parity/test_old_vs_new.py
def test_parity_old_vs_new():
    """Verify new implementation has parity with old."""
    # Test all features
    # Compare outputs
    # Verify no functionality lost
    pass
```

---

## 4. Documentation

- [ ] Parity verification documented
- [ ] Differences documented (if any)
- [ ] Migration guide updated
- [ ] API changes documented

---

## 5. Approval

**Parity Verification:**

- [ ] ✅ Feature parity verified
- [ ] ✅ Migration complete
- [ ] ✅ Tests pass
- [ ] ✅ Documentation updated

**Ready for Removal:**

- [ ] ✅ All checks pass
- [ ] ✅ Approval obtained
- [ ] ✅ Removal plan documented

**If any check fails:**

- ❌ **DO NOT PROCEED** with removal
- ⚠️ Fix issues first
- 🔄 Re-verify after fixes

---

## 6. Post-Removal Verification

**After removal, verify:**

- [ ] All tests pass
- [ ] No broken imports
- [ ] No regressions
- [ ] Performance acceptable

---

## Notes

[Additional notes, concerns, or observations]

---

**Template Version:** 1.0
**Last Updated:** 2026-02-19
