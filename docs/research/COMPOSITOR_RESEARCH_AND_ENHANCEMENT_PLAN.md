<DONE>
# TUI Compositor Research and Enhancement Plan

> **Status**: Research Complete | **Priority**: P1 | **Date**: 2026-02-19
> **Task**: research-tui-compositor | **Reference**: TUI_COMPOSITOR_IMPLEMENTATION.md

---

## Executive Summary

The thegent TUI Compositor implementation spans **three distinct packages**:

1. **`src/thegent/ux/compositor.py`** (MVP - Rich-based, tmux-linked)
2. **`src/thegent/ui/compositor/`** (Textual-based app, emerging)
3. **`src/thegent/tui/compositor.py`** (Legacy Textual variant)
4. **`src/thegent/compositor/`** (Alternative modular structure)

The codebase has **basic implementations but significant gaps** in:
- Panel lifecycle management (mount/unmount hooks)
- Composition caching to avoid re-renders
- Error boundaries and recovery for panel crashes
- Performance profiling (render time per frame)
- Comprehensive unit/integration test coverage
- Integration with CLI progress bars (plan_loop_cmd)

This document provides:
1. Current state analysis
2. Gap identification
3. Enhancement recommendations
4. Implementation roadmap

---

## Current State Analysis

### Package Structure

#### 1. `src/thegent/ux/compositor.py` (MVP)

**Type**: Rich-based, minimal MVP
**Purpose**: Display tmux panes in a Rich layout
**Status**: Functional baseline

**What Works**:
- Pane collection from tmux (`collect_panes()`)
- Layout rendering (`render()`)
- Config loading (YAML)
- Live refresh with `Rich.Live`

**Gaps**:
- No panel lifecycle hooks (mount/unmount)
- No composition caching
- No error handling for pane crashes
- No performance profiling
- No async support
- Very basic, terminal-only

**Size**: ~120 lines (tiny)
**Dependencies**: Rich, tmux integration

---

#### 2. `src/thegent/ui/compositor/` (Textual-based)

**Type**: Textual app (async-native)
**Purpose**: Full TUI with pane management, session state
**Status**: Partially implemented

**Modules**:
- `app.py` - CompositApp (main Textual app)
- `pane_manager.py` - PaneManager (tree structure)
- `session_state.py` - SessionState (persistence)
- `terminal_pane.py` - TerminalPane (PTY widget)

**What Works**:
- App initialization with BINDINGS and CSS
- PaneManager with tree data structure
- split_pane (vertical/horizontal)
- close_pane (with minimum-1 guard)
- focus_next (rotation through panes)
- Session persistence (save/load YAML)
- TerminalPane placeholder rendering
- Layout serialization/deserialization

**Gaps**:
- **No panel lifecycle hooks** - on_mount/on_unmount not implemented
- **No composition caching** - renders on every call
- **No error boundaries** - crashes in pane kill the whole app
- **No performance profiling** - no frame time tracking
- **Incomplete PTY integration** - TerminalPane doesn't actually run a shell in most cases
- **No progress bar integration** - can't display CLI progress
- **Textual widgets not mounted** - compose() yields placeholders, no actual terminal widgets
- **Multiple duplicate TODOs** - "# TODO: Actually create Textual terminal widget"

**Size**: ~800 lines (modular, decent)
**Dependencies**: Textual, YAML

---

#### 3. `src/thegent/tui/compositor.py` (Textual variant)

**Type**: Textual app variant
**Purpose**: Alternative Textual implementation
**Status**: Partial (different design)

**What Works**:
- Basic Textual app structure
- Layout composition
- Action bindings (focus, sidebar toggle, maximize)
- Output/status pane management

**Gaps**:
- No pane tree structure
- No split/close operations
- No session persistence
- Seems to be an alternative, not primary

**Size**: ~330 lines
**Dependencies**: Textual

---

#### 4. `src/thegent/compositor/` (Alternative modular)

**Type**: Non-Textual modular structure
**Status**: Partial

**Files**: app.py, pane_manager.py, session_state.py, terminal_pane.py
**Note**: Similar structure to `ui/compositor/` but separate

---

### Test Coverage

**Current Tests** (in `tests/ui/compositor/`):
- `test_app.py` - CompositApp initialization, actions (basic)
- `test_basic.py` - Component initialization (smoke tests)
- `test_integration.py` - Session persistence, focus rotation (in-progress)
- `test_pane_manager.py` - PaneManager split/close/focus
- `test_session_state.py` - SessionState save/load
- `test_terminal_pane.py` - TerminalPane initialization

**Coverage**: ~40% (basic smoke tests, missing:)
- Panel lifecycle events (mount/unmount)
- Error recovery scenarios
- Performance profiling
- Progress bar integration
- Composition caching
- Complex multi-pane workflows

**Old Test** (in `tests/test_unit_tui_compositor.py`):
- Tests for `ux/compositor.py` (MVP)
- Basic layout rendering

---

### CLI Integration (plan_loop_cmd)

**Current State**:
- `plan_loop_cmd()` in `src/thegent/cli.py` is a loop that:
  1. Calls `do_next_impl()` to get next work item
  2. Prints item to console (Rich)
  3. Calls `bg_cmd()` to run agent in background
  4. Sleeps, repeats
- Uses Rich `console.print()` for progress

**Integration Gap**:
- No connection to CompositorApp
- No progress bar display in TUI
- No pane switching based on status
- Status updates not reflected in sidebar

**Needed**:
- CompositorApp integration hook
- Progress bar widget in TUI
- Real-time status updates
- Output redirection to pane

---

## Identified Gaps and Missing Features

### Gap 1: Panel Lifecycle Hooks

**Issue**: No on_mount/on_unmount lifecycle for panels
**Impact**: Cannot initialize pane resources, cleanup on close
**Severity**: High

**Missing**:
```python
# Needed in TerminalPane or panel interface
def on_mount(self) -> None:
    """Called when panel is mounted."""
    # Initialize PTY, start shell, setup event handlers
    pass


def on_unmount(self) -> None:
    """Called when panel is unmounted."""
    # Cleanup PTY, terminate shell, save state
    pass
```

**Location**: `src/thegent/ui/compositor/terminal_pane.py`

---

### Gap 2: Composition Caching

**Issue**: Every render call re-fetches, re-renders everything
**Impact**: Performance degradation with many panes
**Severity**: Medium

**Missing**:
```python
# Composition cache to avoid re-renders
class CompositionCache:
    def __init__(self, ttl: float = 0.5):
        self.cache: dict[str, tuple[float, object]] = {}
        self.ttl = ttl

    def get(self, key: str) -> object | None:
        """Get cached composition."""
        if key in self.cache:
            timestamp, value = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None

    def set(self, key: str, value: object) -> None:
        """Cache composition."""
        self.cache[key] = (time.time(), value)
```

**Benefits**:
- Avoid re-rendering unchanged panes
- Reduce CPU usage
- Smoother 60 FPS rendering

**Location**: New in `src/thegent/ui/compositor/` or extend `app.py`

---

### Gap 3: Error Boundaries

**Issue**: Crash in one pane kills entire app
**Impact**: Reliability issue
**Severity**: Medium

**Missing**:
```python
# Error boundary wrapper
class PanelErrorBoundary:
    def __init__(self, pane: Static):
        self.pane = pane
        self.error_count = 0
        self.last_error: Exception | None = None

    def render(self) -> str | RenderableType:
        """Render with error handling."""
        try:
            return self.pane.render()
        except Exception as e:
            self.error_count += 1
            self.last_error = e
            logger.error(f"Pane render error: {e}", exc_info=True)
            return Panel(
                f"[red]Panel Error[/red]\n{str(e)[:100]}",
                title=f"Error (attempt {self.error_count})",
                border_style="red",
            )
```

**Location**: New in `src/thegent/ui/compositor/`

---

### Gap 4: Performance Profiling

**Issue**: No visibility into render times
**Impact**: Cannot identify perf bottlenecks
**Severity**: Low (but needed for production)

**Missing**:
```python
# Frame time profiling
class FrameProfiler:
    def __init__(self):
        self.frame_times: list[float] = []
        self.last_frame_start: float | None = None

    def start_frame(self) -> None:
        """Mark frame start."""
        self.last_frame_start = time.perf_counter()

    def end_frame(self) -> float:
        """Mark frame end, return elapsed time."""
        if self.last_frame_start:
            elapsed = time.perf_counter() - self.last_frame_start
            self.frame_times.append(elapsed)
            # Keep only last 100 frames
            if len(self.frame_times) > 100:
                self.frame_times.pop(0)
            return elapsed
        return 0.0

    def stats(self) -> dict[str, float]:
        """Get frame time statistics."""
        if not self.frame_times:
            return {}
        return {
            "min_ms": min(self.frame_times) * 1000,
            "max_ms": max(self.frame_times) * 1000,
            "avg_ms": sum(self.frame_times) / len(self.frame_times) * 1000,
            "p95_ms": sorted(self.frame_times)[int(len(self.frame_times) * 0.95)] * 1000,
        }
```

**Location**: New in `src/thegent/ui/compositor/`

---

### Gap 5: CLI Progress Bar Integration

**Issue**: plan_loop_cmd uses console.print(), no TUI integration
**Impact**: Progress not visible in compositor sidebar
**Severity**: Medium

**Missing**:
```python
# Hook for progress updates
class LoopProgressWidget(Static):
    """Display progress of plan_loop_cmd."""

    def update_progress(self, item_id: str, status: str, iteration: int, max_iterations: int) -> None:
        """Update progress display."""
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        )
        progress.add_task(
            f"[cyan]{item_id}[/cyan]",
            total=max_iterations if max_iterations else 100,
            completed=iteration,
        )
        self.update(progress)
```

**Location**: New widget or extend existing

---

## Enhancement Recommendations

### Tier 1: Critical (Do First)

1. **Panel Lifecycle Hooks** (4 hours)
   - Add `on_mount()` / `on_unmount()` to TerminalPane
   - Start shell in on_mount
   - Cleanup PTY in on_unmount
   - Write tests for lifecycle events

2. **Error Boundaries** (3 hours)
   - Wrap pane renders with try/catch
   - Display error UI instead of crashing
   - Log errors for debugging
   - Write error recovery tests

3. **Comprehensive Test Suite** (6 hours)
   - Fill gaps in `tests/ui/compositor/`
   - Add lifecycle event tests
   - Add error scenario tests
   - Add integration tests with plan_loop_cmd

### Tier 2: Important (Do Next)

4. **Composition Caching** (3 hours)
   - Implement CompositionCache
   - Invalidate on state changes
   - Measure performance improvement

5. **Performance Profiling** (2 hours)
   - Add FrameProfiler
   - Display in status bar
   - Log to metrics

6. **CLI Integration** (4 hours)
   - Hook plan_loop_cmd to CompositorApp
   - Display progress in sidebar
   - Update pane output in real-time

### Tier 3: Polish (Do Later)

7. **Advanced Features**
   - Pane themes and customization
   - Pane search/filtering
   - Session snapshots
   - Keyboard macros

---

## Implementation Roadmap

### Phase 1: Lifecycle Hooks (P1.1)

**Files to Modify**:
- `src/thegent/ui/compositor/terminal_pane.py`
  - Add event class: `PanelMounted`, `PanelUnmounted`
  - Implement `on_mount()` - start shell
  - Implement `on_unmount()` - cleanup PTY
  - Add `_shell_output` buffer for capture

- `tests/ui/compositor/test_terminal_pane.py`
  - Test on_mount triggers shell spawn
  - Test on_unmount closes PTY
  - Test output capture

**Effort**: 4 hours
**Test Coverage**: 90%+

---

### Phase 2: Error Boundaries (P1.2)

**Files to Modify**:
- `src/thegent/ui/compositor/app.py`
  - Add PanelErrorBoundary wrapper class
  - Wrap all pane render calls

- `src/thegent/ui/compositor/terminal_pane.py`
  - Add error_count, last_error tracking
  - Implement render with error handling

- `tests/ui/compositor/test_terminal_pane.py`
  - Test crash in pane doesn't crash app
  - Test error UI displayed
  - Test recovery after error

**Effort**: 3 hours
**Test Coverage**: 85%+

---

### Phase 3: Comprehensive Testing (P1.3)

**Files to Create/Modify**:
- `tests/ui/compositor/test_lifecycle.py` (NEW)
  - Mount/unmount sequences
  - Pane creation/destruction lifecycle

- `tests/ui/compositor/test_error_recovery.py` (NEW)
  - Crash scenarios
  - Recovery scenarios
  - Error UI verification

- `tests/ui/compositor/test_composition_integration.py` (NEW)
  - Multi-pane workflows
  - Complex split/close sequences

- `tests/ui/compositor/test_cli_integration.py` (NEW)
  - plan_loop_cmd integration
  - Progress bar display

**Effort**: 6 hours
**Test Coverage**: 100% (E2E + Integration)

---

### Phase 4: Composition Caching (P2.1)

**Files to Create/Modify**:
- `src/thegent/ui/compositor/cache.py` (NEW)
  - CompositionCache class
  - TTL-based invalidation

- `src/thegent/ui/compositor/app.py`
  - Integrate cache into render pipeline
  - Invalidate on state changes

- `tests/ui/compositor/test_caching.py` (NEW)
  - Cache hit/miss verification
  - Invalidation behavior
  - Performance benchmarks

**Effort**: 3 hours
**Expected Perf Gain**: 2-3x speedup with many panes

---

### Phase 5: Performance Profiling (P2.2)

**Files to Create/Modify**:
- `src/thegent/ui/compositor/profiler.py` (NEW)
  - FrameProfiler class
  - Metrics tracking

- `src/thegent/ui/compositor/app.py`
  - Integrate profiler into render loop
  - Display stats in status bar

- `tests/ui/compositor/test_profiling.py` (NEW)
  - Profiler functionality
  - Stats accuracy

**Effort**: 2 hours
**Output**: Frame time visibility in status bar

---

### Phase 6: CLI Integration (P2.3)

**Files to Create/Modify**:
- `src/thegent/ui/compositor/widgets/progress.py` (NEW)
  - LoopProgressWidget
  - Real-time updates

- `src/thegent/cli.py`
  - Hook plan_loop_cmd to CompositorApp
  - Send progress updates

- `tests/ui/compositor/test_cli_integration.py`
  - plan_loop_cmd in TUI context
  - Progress updates
  - Output capture

**Effort**: 4 hours
**Integration**: CLI ↔ TUI bidirectional

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                  CLI (cli.py)                              │
│  ┌────────────────────────────────────────────────────────┐│
│  │ plan_loop_cmd                                          ││
│  │  ├─ do_next_impl() → next work item                   ││
│  │  ├─ bg_cmd() → background execution                  ││
│  │  └─ [NEW] emit_progress_update() → TUI                ││
│  └────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│              CompositorApp (Textual)                        │
│  ┌────────────────────────────────────────────────────────┐│
│  │ compose() → Header + MainContainer + Statusbar        ││
│  │            + ProgressWidget (NEW)                      ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │ PaneManager                                            ││
│  │  ├─ PaneNode tree (split/merge)                       ││
│  │  ├─ lifecycle hooks (mount/unmount)   [NEW]           ││
│  │  └─ focus rotation                                     ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │ TerminalPane (×N)                                      ││
│  │  ├─ on_mount() → spawn shell        [NEW]             ││
│  │  ├─ on_unmount() → cleanup          [NEW]             ││
│  │  ├─ render() with ErrorBoundary     [NEW]             ││
│  │  └─ output buffer                                      ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │ SessionState                                           ││
│  │  └─ save/load layout + state                          ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │ CompositionCache [NEW]                                 ││
│  │  └─ cache pane renders (TTL 0.5s)                     ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │ FrameProfiler [NEW]                                    ││
│  │  └─ track render times, display stats                 ││
│  └────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### Unit Tests (test_*.py)

**Lifecycle Tests** (NEW):
```python
def test_terminal_pane_mount_spawns_shell():
    """Verify on_mount() starts shell process."""
    pane = TerminalPane("test-pane", working_dir="/tmp")
    pane.on_mount()
    assert pane.process is not None
    assert pane.pty_master is not None


def test_terminal_pane_unmount_closes_pty():
    """Verify on_unmount() closes PTY."""
    pane = TerminalPane("test-pane", working_dir="/tmp")
    pane.on_mount()
    pane.on_unmount()
    assert pane.process is None or not pane.process.poll()
```

**Error Boundary Tests** (NEW):
```python
def test_pane_render_error_shows_error_ui():
    """Verify crash in pane doesn't crash app."""
    pane = ErrorBoundaryPane(FailingPane())
    output = pane.render()
    assert "[red]Panel Error[/red]" in str(output)


def test_error_boundary_tracks_error_count():
    """Verify error count incremented on crash."""
    boundary = PanelErrorBoundary(FailingPane())
    boundary.render()
    boundary.render()
    assert boundary.error_count == 2
```

**Caching Tests** (NEW):
```python
def test_composition_cache_hit():
    """Verify cache returns same object."""
    cache = CompositionCache()
    render = Panel("test")
    cache.set("pane1", render)
    assert cache.get("pane1") is render


def test_composition_cache_ttl():
    """Verify cache expires after TTL."""
    cache = CompositionCache(ttl=0.1)
    cache.set("pane1", Panel("test"))
    time.sleep(0.2)
    assert cache.get("pane1") is None
```

### Integration Tests (test_integration.py)

**Lifecycle Workflow**:
```python
def test_full_pane_lifecycle():
    """Full lifecycle: create → mount → render → unmount → close."""
    app = CompositApp()
    # Mount app
    # Create pane
    # Verify mounted
    # Render
    # Unmount
    # Verify closed
```

**Multi-Pane Workflow**:
```python
def test_split_merge_workflow():
    """Create → split → split → focus rotate → close → close."""
    pm = PaneManager()
    pm.create_root_pane("p0")
    pm.split_pane("vertical")
    pm.split_pane("horizontal")
    assert pm.get_pane_count() == 3
    pm.focus_next()
    pm.close_pane()
    assert pm.get_pane_count() == 2
```

### E2E Tests (test_cli_integration.py)

**CLI → TUI Progress**:
```python
async def test_plan_loop_with_compositor():
    """Verify plan_loop_cmd updates TUI progress."""
    app = CompositorApp()
    async with app.run_test() as pilot:
        # Simulate plan_loop_cmd
        emit_progress_update("item1", "running", 1, 5)
        await pilot.pause()
        # Verify progress widget updated
        assert "1/5" in str(app.progress_widget)
```

---

## Library Dependencies

**No new dependencies needed**:
- Textual (already used)
- Rich (already used)
- Standard library (time, dataclasses, logging)

---

## Success Criteria

### Phase 1 (Lifecycle + Error Boundaries + Tests)
- ✅ Panel lifecycle hooks functional
- ✅ Error boundaries catch and display errors
- ✅ 90%+ test coverage of lifecycle code
- ✅ plan_loop_cmd progress visible in status bar

### Phase 2 (Caching + Profiling + CLI)
- ✅ Composition caching reduces renders by 80%+
- ✅ Frame time stats displayed in status bar
- ✅ plan_loop_cmd fully integrated with TUI
- ✅ 100% test coverage (E2E + Integration)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| PTY on Windows | High | Medium | Use fallback pipe mode (already in code) |
| Shell integration issues | Medium | Medium | Extensive testing, fallback to bash |
| Performance with 10+ panes | Low | Low | Caching reduces CPU, profiler shows stats |
| Textual API changes | Low | Low | Dependency pinning in pyproject.toml |

---

## References

- [TUI Compositor Implementation Research](./TUI_COMPOSITOR_IMPLEMENTATION.md)
- [Textual Documentation](https://textual.textualize.io)
- [Rich Documentation](https://rich.readthedocs.io)

---

**Next Steps**:
1. Approve enhancement plan
2. Implement Phase 1 (Lifecycle + Error + Tests)
3. Verify plan_loop_cmd integration
4. Implement Phase 2 (Caching + Profiling)
5. Add CLI hooks and progress display
