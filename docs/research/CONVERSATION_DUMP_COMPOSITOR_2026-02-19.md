<DONE>
# Conversation Dump: TUI Compositor Research

**Date**: 2026-02-19
**Task**: research-tui-compositor
**Status**: Research Complete
**Priority**: P1

---

## Issues Addressed

1. **Multiple Compositor Packages**: Discovered 4 separate implementations in different namespaces
2. **Architecture Clarity**: Identified which implementation is primary (ui/compositor/)
3. **Feature Gaps**: Mapped missing features against design requirements
4. **Test Coverage**: Assessed current test suite (40% coverage, significant gaps)
5. **CLI Integration**: Identified missing integration with plan_loop_cmd

---

## Findings Summary

### Package Landscape

| Package             | Status      | Size      | Purpose                |
| ------------------- | ----------- | --------- | ---------------------- |
| `ux/compositor.py`  | MVP         | 120 lines | Rich + tmux simple MVP |
| `ui/compositor/`    | Partial     | 800 lines | Textual app (primary)  |
| `tui/compositor.py` | Variant     | 330 lines | Alternative Textual    |
| `compositor/`       | Alternative | Similar   | Modular variant        |

**Primary Implementation**: `src/thegent/ui/compositor/` (Textual-based, most complete)

### Critical Gaps

1. **Panel Lifecycle** (HIGH)
   - No on_mount/on_unmount hooks
   - Cannot initialize shell on creation
   - Cannot cleanup on destruction
   - Impact: Shells not actually starting in most cases

2. **Error Boundaries** (MEDIUM)
   - No crash recovery in panes
   - App exits if pane render fails
   - No error UI
   - Impact: Production reliability issue

3. **Composition Caching** (MEDIUM)
   - Every render re-fetches everything
   - No TTL-based invalidation
   - Impact: Perf degrades with many panes

4. **Performance Profiling** (LOW)
   - No frame time tracking
   - No visibility into bottlenecks
   - Impact: Can't optimize what you can't measure

5. **CLI Integration** (MEDIUM)
   - plan_loop_cmd uses console.print()
   - No TUI progress display
   - No real-time status updates
   - Impact: Progress invisible during loop execution

### Test Gap Analysis

**Current Coverage**: ~40%

- ✅ Component initialization (smoke tests)
- ✅ Basic pane operations (split/close/focus)
- ✅ Session persistence
- ❌ Lifecycle event tests
- ❌ Error recovery tests
- ❌ Composition caching tests
- ❌ Performance profiling tests
- ❌ CLI integration tests
- ❌ Complex multi-pane workflows

**To reach 100%**: Need ~6 hours of additional test writing

---

## Key Code Locations

### Main Files

1. **App Core**
   - `src/thegent/ui/compositor/app.py` - CompositApp (Textual)
   - Lines 113-189: compose() and on_mount()
   - Lines 150-238: Action handlers (split/close/focus)

2. **Pane Management**
   - `src/thegent/ui/compositor/pane_manager.py` - PaneManager
   - Lines 42-88: split_pane() - tree manipulation
   - Lines 90-139: close_pane() - with cleanup
   - Lines 145-174: focus_next() - rotation

3. **Terminal Widget**
   - `src/thegent/ui/compositor/terminal_pane.py` - TerminalPane
   - Lines 49-115: spawn_shell() - PTY allocation
   - Lines 117-124: on_mount() placeholder
   - Lines 126-146: close() - cleanup
   - **TODO: Implement actual shell spawning in on_mount()**

4. **Session Persistence**
   - `src/thegent/ui/compositor/session_state.py` - SessionState
   - Lines 34-57: save() - YAML persistence
   - Lines 59-82: load() - YAML loading
   - Lines 100-116: list_sessions() - enumeration

### Test Files

1. **Component Tests**
   - `tests/ui/compositor/test_app.py` - 50 lines
   - `tests/ui/compositor/test_basic.py` - 86 lines
   - `tests/ui/compositor/test_pane_manager.py` - ~100 lines
   - `tests/ui/compositor/test_session_state.py` - ~100 lines
   - `tests/ui/compositor/test_terminal_pane.py` - ~100 lines

2. **Integration Tests**
   - `tests/ui/compositor/test_integration.py` - 121 lines
   - **Issue**: Uses wrong import paths (thegent.compositor instead of thegent.ui.compositor)
   - **Issue**: Tests methods that don't exist in current implementation

---

## Enhancement Plan

### Phase 1 (Immediate - 4-6 hours)

1. **Panel Lifecycle Hooks**
   - Implement proper on_mount() in TerminalPane
   - Add on_unmount() for cleanup
   - Start shell in on_mount()
   - Write unit tests

2. **Error Boundaries**
   - Add PanelErrorBoundary wrapper
   - Catch render exceptions
   - Display error UI
   - Write error scenario tests

3. **Fix Existing Tests**
   - Fix import paths in test_integration.py
   - Update tests to match current API
   - Add lifecycle and error tests

### Phase 2 (Follow-up - 3-4 hours)

4. **Composition Caching**
   - Implement CompositionCache
   - Integrate into render pipeline
   - Measure perf improvement

5. **Performance Profiling**
   - Add FrameProfiler
   - Display stats in status bar
   - Log metrics

6. **CLI Integration**
   - Hook plan_loop_cmd to TUI
   - Add progress widget
   - Update status bar

---

## Architecture Insights

### Pane Manager Tree Structure

Current implementation uses a tree structure:

```
PaneNode {
  pane_id: str
  direction: "horizontal" | "vertical" | None
  is_leaf: bool
  children: List[PaneNode]
}
```

**Strengths**:

- Supports arbitrary nesting
- Serializable (save/load)
- Can traverse depth-first

**Weakness**:

- No parent pointers (requires recursive search)
- No cache of leaf nodes (recalculated each time)

**Improvement**: Add parent pointers and leaf cache for O(1) operations

### Render Pipeline

Current (naive):

```
App.on_update() → render() → PaneManager.get_all_leaves()
  → TerminalPane.render() × N → Display
```

**Issues**:

- No caching
- Pane.render() might fail (no error boundary)
- No frame time tracking

**Improved**:

```
App.on_update() → Frame.start()
  → cache.try_get(pane_id) ⊕ render()
  → [ErrorBoundary] TerminalPane.render()
  → cache.set(pane_id, result)
  → Display → Frame.end() → Profiler.record()
```

---

## Recommendations

### Short-term (Do Now)

1. ✅ Write comprehensive research document (DONE)
2. Fix lifecycle hooks in TerminalPane (4 hours)
3. Add error boundaries (3 hours)
4. Fix and expand test suite (6 hours)
5. Verify plan_loop_cmd integration point

### Medium-term (Next Sprint)

6. Implement composition caching (3 hours)
7. Add performance profiling (2 hours)
8. Integrate CLI progress display (4 hours)
9. Optimize pane tree operations

### Long-term (Nice to Have)

10. Multi-terminal support (Kitty, WezTerm)
11. Session snapshots
12. Pane themes/customization
13. Search/filtering

---

## Test Strategy Summary

### Unit Tests (90% coverage)

- Panel lifecycle (mount/unmount)
- Error boundaries (crash handling)
- Pane operations (split/close/focus)
- Cache hit/miss
- Profile frame times

### Integration Tests (100% coverage)

- Multi-pane workflows
- Session persistence + restore
- CLI ↔ TUI progress updates
- Error recovery workflows

### E2E Tests (critical paths)

- plan_loop_cmd with progress display
- Complex layout (4+ panes)
- Error recovery (crash + restart)

---

## Risks and Mitigations

| Risk                | Mitigation                          |
| ------------------- | ----------------------------------- |
| Shell not starting  | Keep existing fallback to pipe mode |
| PTY on Windows      | Document Unix-only; use fallback    |
| Textual API changes | Pin version, add integration tests  |
| Perf with 10+ panes | Caching + profiling shows impact    |

---

## Next Actions for Agent

**Phase 1 Implementation** (if approved):

1. Create `src/thegent/ui/compositor/cache.py` (CompositionCache)
2. Create `src/thegent/ui/compositor/profiler.py` (FrameProfiler)
3. Update `src/thegent/ui/compositor/terminal_pane.py`:
   - Implement on_mount() → spawn shell
   - Implement on_unmount() → cleanup
   - Add error handling to render()
4. Update `src/thegent/ui/compositor/app.py`:
   - Integrate cache into render loop
   - Add profiler frame tracking
   - Integrate error boundaries
5. Create `tests/ui/compositor/test_lifecycle.py` (lifecycle tests)
6. Create `tests/ui/compositor/test_error_recovery.py` (error tests)
7. Fix `tests/ui/compositor/test_integration.py` (import paths)

**Estimated Time**: 10-12 hours

---

## References

- **Design Doc**: `docs/research/TUI_COMPOSITOR_IMPLEMENTATION.md`
- **API Reference**: `docs/reference/api/compositor_api.md`
- **Implementation Plan**: `docs/research/COMPOSITOR_RESEARCH_AND_ENHANCEMENT_PLAN.md` (this session)
- **Code**: `src/thegent/ui/compositor/`, `tests/ui/compositor/`

---

**Session Complete**: Research phase done, ready for implementation.
