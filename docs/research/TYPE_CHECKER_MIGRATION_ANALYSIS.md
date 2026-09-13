<DONE>
# Type Checker Migration Analysis: ty/zuban/basedpyright vs Pyright/Pylance

## Current State

### IDE (Real-time IntelliSense)

- **Pylance** (VS Code/Cursor extension)
- **Pyright** (language server backend)
- Configuration: `pyrightconfig.json` + `.vscode/settings.json`

### CI/Linting (Batch Checking)

- **Fast**: `ty` + `zuban` (`task lint:type`)
- **Strict**: `basedpyright` + `mypy` (`task lint:strict`)
- Pre-commit: `ty` + `basedpyright`

## Tool Comparison

### ty

- **Purpose**: Fast type checker (Rust-based)
- **Use Case**: Quick feedback during development
- **Speed**: Very fast (10-50x faster than Pyright)
- **Coverage**: Basic type checking, focused on common errors
- **LSP Support**: ❌ No language server (CLI only)
- **IDE Integration**: ❌ Not supported by Pylance

### zuban

- **Purpose**: Fast type checker (complementary to ty)
- **Use Case**: Additional checks alongside ty
- **Speed**: Fast
- **Coverage**: Different error codes than ty
- **LSP Support**: ❌ No language server (CLI only)
- **IDE Integration**: ❌ Not supported by Pylance

### basedpyright

- **Purpose**: Fork/variant of Pyright with additional features
- **Use Case**: Strict type checking (CI/commit)
- **Speed**: Similar to Pyright (slower than ty/zuban)
- **Coverage**: Full Pyright compatibility + extensions
- **LSP Support**: ✅ Compatible with Pyright LSP protocol
- **IDE Integration**: ✅ Can replace Pyright in Pylance

### Pyright (Current)

- **Purpose**: Microsoft's official Python type checker
- **Use Case**: IDE IntelliSense + batch checking
- **Speed**: Moderate (slower than ty/zuban)
- **Coverage**: Comprehensive type checking
- **LSP Support**: ✅ Full LSP support
- **IDE Integration**: ✅ Native Pylance support

## Migration Options

### Option 1: Keep Dual Approach (Recommended)

**Status**: Current approach

**IDE**: Pyright/Pylance (for real-time IntelliSense)
**CI/Linting**: ty + zuban (fast) + basedpyright + mypy (strict)

**Pros**:

- ✅ Best of both worlds: fast IDE feedback + fast CI checks
- ✅ No IDE disruption (Pylance works perfectly)
- ✅ Fast CI feedback (ty/zuban are 10-50x faster)
- ✅ Strict checking when needed (basedpyright + mypy)

**Cons**:

- ⚠️ Two different type checkers (potential inconsistency)
- ⚠️ Need to maintain both configs

**Recommendation**: ✅ **Keep this approach**

### Option 2: Migrate IDE to basedpyright

**Status**: Possible but not recommended

**IDE**: basedpyright (replace Pyright)
**CI/Linting**: ty + zuban (fast) + basedpyright + mypy (strict)

**Pros**:

- ✅ Single type checker for IDE and strict checking
- ✅ Consistent behavior between IDE and CI

**Cons**:

- ❌ basedpyright may not be fully compatible with Pylance
- ❌ Risk of breaking IDE IntelliSense
- ❌ No clear benefit (Pyright works fine for IDE)
- ❌ ty/zuban still needed for fast CI checks

**Recommendation**: ❌ **Not recommended** (high risk, low benefit)

### Option 3: Migrate IDE to ty/zuban

**Status**: Not possible

**IDE**: ty/zuban
**CI/Linting**: ty + zuban

**Pros**:

- ✅ Single fast type checker everywhere

**Cons**:

- ❌ ty/zuban don't have LSP support
- ❌ No IDE integration possible
- ❌ Lose real-time IntelliSense
- ❌ Much less comprehensive than Pyright

**Recommendation**: ❌ **Not possible** (no LSP support)

## Recommendation: Keep Dual Approach

### Rationale

1. **IDE Performance**: Pyright/Pylance is already optimized with our `pyrightconfig.json` exclusions
2. **CI Performance**: ty/zuban provide 10-50x faster feedback than Pyright
3. **Best Tool for Each Job**:
   - IDE: Pyright (comprehensive, real-time, LSP support)
   - Fast CI: ty/zuban (speed)
   - Strict CI: basedpyright + mypy (strictness)

### Current Workflow (Optimal)

```
Development:
  IDE → Pylance (Pyright) → Real-time IntelliSense
  Pre-commit → ty + basedpyright → Fast + strict checks

CI:
  Fast path → ty + zuban → Quick feedback
  Strict path → basedpyright + mypy → Comprehensive checks
```

## Configuration Alignment

### Current Configs

- `pyrightconfig.json` - IDE (Pyright/Pylance)
- `pyproject.toml` - `[tool.ty]`, `[tool.basedpyright]` - CI/Linting

### Recommendation: Keep Separate

- IDE config (`pyrightconfig.json`) optimized for IntelliSense performance
- CI config (`pyproject.toml`) optimized for batch checking speed/strictness

## Future Considerations

### If basedpyright adds significant features

- Could migrate IDE to basedpyright if it becomes a strict superset of Pyright
- Would need to verify Pylance compatibility first

### If ty/zuban add LSP support

- Could consider migrating IDE to ty/zuban for speed
- Would need to verify IntelliSense quality

### Current State is Optimal

- No migration needed
- Each tool serves its purpose well
- Performance is already optimized

## Conclusion

**Recommendation**: ✅ **Keep current dual approach**

- IDE: Pyright/Pylance (optimized with exclusions)
- CI Fast: ty + zuban
- CI Strict: basedpyright + mypy

**No migration needed** - current setup is optimal for both IDE performance and CI speed.
