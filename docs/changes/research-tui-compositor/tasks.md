---
task_id: research-tui-compositor
status: in_progress
---

# TUI Compositor — Implementation Tasks

**Date**: 2026-02-18
**Status**: Task Breakdown
**Version**: 1.0

---

## Phase 1: Foundation (Week 1)

### Goal
Basic Textual app with menubar, statusbar, and single terminal pane.

### Tasks

#### P1.1: Project Setup & Dependencies
**Depends on**: None
**Effort**: 1-2 hours

- [ ] Create new module: `thegent/src/thegent/ui/compositor/`
- [ ] Create `__init__.py`, `app.py`, `pane_manager.py`, `session_state.py`
- [ ] Add Textual to `pyproject.toml` dependencies
- [ ] Create test directory: `tests/ui/compositor/`
- [ ] Set up pytest fixtures for testing

**Acceptance Criteria**:
- All files created and importable
- `pytest` finds test directory
- No import errors

**Checklist**:
- [ ] `pyproject.toml` updated
- [ ] Module structure created
- [ ] Tests discoverable
- [ ] Linters pass (ruff, type checking)

---

#### P1.2: CompositApp Skeleton
**Depends on**: P1.1
**Effort**: 2-3 hours

- [ ] Implement `CompositApp` class (Textual.App)
- [ ] Add `Header`, `Footer` widgets
- [ ] Implement basic key bindings
- [ ] Add logging and debug output

**Code**:
```python
# thegent/src/thegent/ui/compositor/app.py
class CompositApp(App):
    TITLE = "Thegent Compositor"
    BINDINGS = [
        ("ctrl+n", "new_pane", "New Pane"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(id="main-pane-container")
        yield Footer()
```

**Acceptance Criteria**:
- App starts without errors
- Header/Footer render correctly
- Quit binding works (Ctrl+Q)

**Checklist**:
- [ ] CompositApp renders
- [ ] Header displays "Thegent Compositor"
- [ ] Ctrl+Q quits cleanly
- [ ] Unit tests written

---

#### P1.3: TerminalPane Widget
**Depends on**: P1.1
**Effort**: 3-4 hours

- [ ] Implement `TerminalPane` class
- [ ] Add PTY allocation and shell spawning
- [ ] Implement input/output handling
- [ ] Add cleanup on pane close

**Code**:
```python
# thegent/src/thegent/ui/compositor/terminal_pane.py
class TerminalPane(Static):
    def __init__(self, pane_id: str, working_dir: str = "."):
        super().__init__()
        self.pane_id = pane_id
        self.working_dir = working_dir

    def spawn_shell(self, shell: str = "/bin/bash") -> None:
        # Allocate PTY, fork shell
        pass
```

**Acceptance Criteria**:
- PTY allocation succeeds
- Shell spawns and renders in pane
- Input echoes to terminal
- Pane closes cleanly

**Checklist**:
- [ ] PTY allocated
- [ ] Shell runs in pane
- [ ] Input/output working
- [ ] Cleanup implemented
- [ ] Unit tests written

---

#### P1.4: Basic Integration & Single-Pane Demo
**Depends on**: P1.2, P1.3
**Effort**: 2-3 hours

- [ ] Connect `CompositApp` to `TerminalPane`
- [ ] Implement `action_new_pane()` to create and display pane
- [ ] Test startup with single pane
- [ ] Add logging and debug output

**Acceptance Criteria**:
- App starts with one terminal pane
- Pane is interactive (can type, execute commands)
- Pane renders output correctly

**Checklist**:
- [ ] CompositApp displays TerminalPane
- [ ] Terminal is interactive
- [ ] Commands execute in pane
- [ ] App is stable (no crashes)

---

### Phase 1 Testing

**Test Coverage Target**: 80%

- [ ] Unit tests for `TerminalPane` (PTY operations)
- [ ] Unit tests for `CompositApp` (app initialization)
- [ ] Integration test (app start + interactive pane)
- [ ] Run `pytest` with coverage report

---

### Phase 1 Deliverables

1. **Working single-pane app**
   - App starts in <500ms
   - Terminal pane is interactive
   - Ctrl+Q quits cleanly
   - All tests passing

2. **Documentation**
   - `design.md` (completed)
   - `README.md` for compositor module
   - Developer setup guide

3. **Code Quality**
   - No lint errors (ruff pass)
   - Type annotations complete
   - Test coverage ≥80%

---

## Phase 2: Compositor Integration (Week 2)

### Goal
Implement pane splitting, merging, layout management, and session persistence.

### Tasks

#### P2.1: PaneManager Foundation
**Depends on**: P1.4
**Effort**: 3-4 hours

- [ ] Implement `PaneNode` data structure
- [ ] Implement `PaneManager` tree operations
- [ ] Add split/merge logic for horizontal and vertical splits
- [ ] Implement pane focus tracking

**Code**:
```python
# thegent/src/thegent/ui/compositor/pane_manager.py
class PaneManager:
    def split_pane(self, direction: str) -> TerminalPane:
        # Split current pane, create new pane
        pass

    def close_pane(self) -> None:
        # Close current pane, rebalance layout
        pass

    def focus_next(self) -> None:
        # Rotate focus to next pane
        pass
```

**Acceptance Criteria**:
- Split operations create correct tree structure
- Close operations remove panes and rebalance
- Focus rotation works correctly

**Checklist**:
- [ ] Tree structure correct
- [ ] Split operations tested
- [ ] Close operations tested
- [ ] Focus rotation tested
- [ ] Unit tests written (80%+ coverage)

---

#### P2.2: UI Integration for Pane Operations
**Depends on**: P2.1, P1.4
**Effort**: 2-3 hours

- [ ] Integrate `PaneManager` into `CompositApp`
- [ ] Implement `action_split_horizontal()`, `action_split_vertical()`
- [ ] Implement `action_close_pane()`, `action_focus_next()`
- [ ] Update statusbar to show pane count

**Acceptance Criteria**:
- All split/merge/close/focus actions work
- Statusbar updates correctly
- Layout renders properly after operations

**Checklist**:
- [ ] Ctrl+H/V split correctly
- [ ] Ctrl+X closes pane
- [ ] Ctrl+L focuses next pane
- [ ] Statusbar reflects pane count
- [ ] Integration tests written

---

#### P2.3: Layout Serialization
**Depends on**: P2.1
**Effort**: 2-3 hours

- [ ] Implement `PaneManager.save_layout()` (tree → dict)
- [ ] Implement `PaneManager.restore_layout()` (dict → tree)
- [ ] Test round-trip serialization
- [ ] Test YAML compatibility

**Code**:
```python
# thegent/src/thegent/ui/compositor/pane_manager.py
def save_layout(self) -> dict:
    return self._serialize_tree(self.root)


def restore_layout(self, layout_data: dict) -> None:
    self.root = self._deserialize_tree(layout_data)
```

**Acceptance Criteria**:
- Tree serialization produces valid dict
- Deserialization reconstructs identical tree
- YAML round-trip preserves structure

**Checklist**:
- [ ] Serialization implemented
- [ ] Deserialization implemented
- [ ] Round-trip tests written
- [ ] YAML tests written

---

#### P2.4: Session Persistence
**Depends on**: P2.3
**Effort**: 2-3 hours

- [ ] Implement `SessionState` class
- [ ] Add `save_session()` to persist state to disk
- [ ] Add `load_session()` to restore from disk
- [ ] Integrate into `CompositApp.on_mount()`

**Acceptance Criteria**:
- Sessions save to YAML successfully
- Sessions load from disk correctly
- App restores previous layout on restart

**Checklist**:
- [ ] SessionState class implemented
- [ ] Session dir created (`~/.config/thegent/sessions/`)
- [ ] Save/load round-trip tested
- [ ] Integration test (restart app)
- [ ] Unit tests written

---

#### P2.5: Layout Management UI
**Depends on**: P2.4
**Effort**: 2-3 hours

- [ ] Add `action_save_layout(name)` to save custom layouts
- [ ] Add `action_restore_layout(name)` to load layouts
- [ ] Implement layout selection menu
- [ ] Add Ctrl+S/Ctrl+R shortcuts

**Acceptance Criteria**:
- Named layouts can be saved and restored
- Layout menu displays available layouts
- Shortcuts work correctly

**Checklist**:
- [ ] Save layout action implemented
- [ ] Restore layout action implemented
- [ ] Layout menu implemented
- [ ] Shortcuts work (Ctrl+S, Ctrl+R)
- [ ] Integration tests written

---

### Phase 2 Testing

**Test Coverage Target**: 80%

- [ ] Unit tests for `PaneManager` (tree operations, serialization)
- [ ] Unit tests for `SessionState` (persistence)
- [ ] Integration tests (UI actions → layout changes)
- [ ] E2E test (session restart + recovery)
- [ ] Run `pytest` with coverage report

---

### Phase 2 Deliverables

1. **Functional multi-pane compositor**
   - Pane splitting works (H/V)
   - Pane merging works
   - Layout switching works
   - Session persistence works

2. **Performance benchmarks**
   - Pane creation: <100ms
   - Layout switch: <50ms
   - Session load: <200ms

3. **Documentation**
   - Layout YAML schema documented
   - Session file format documented
   - User guide for layout management

---

## Phase 3: Advanced Features (Week 3)

### Goal
Add floating windows, plugin system, themes, and optional web export.

### Tasks

#### P3.1: Floating Windows & Dialogs
**Depends on**: P2.5
**Effort**: 3-4 hours

- [ ] Implement `FloatingWindow` widget
- [ ] Add confirmation dialogs (close pane, quit, unsaved)
- [ ] Add input dialogs (new pane working dir, layout name)
- [ ] Add info/error message popups

**Acceptance Criteria**:
- Dialogs render correctly
- Dialog actions work (confirm/cancel)
- Input dialogs capture text

**Checklist**:
- [ ] FloatingWindow implemented
- [ ] Confirmation dialogs working
- [ ] Input dialogs working
- [ ] Message popups working

---

#### P3.2: Theme Support
**Depends on**: P1.2
**Effort**: 2-3 hours

- [ ] Add theme configuration (light/dark)
- [ ] Implement CSS styling for themes
- [ ] Add theme switching via menu
- [ ] Store theme preference in session

**Acceptance Criteria**:
- Light and dark themes display correctly
- Theme switching works
- Theme preference persists

**Checklist**:
- [ ] CSS styles created
- [ ] Light/dark themes working
- [ ] Theme switching implemented
- [ ] Preference persistence working

---

#### P3.3: Real-Time Process Monitoring (Optional)
**Depends on**: P1.3
**Effort**: 2-3 hours

- [ ] Add CPU/memory usage tracking per pane
- [ ] Display process info in statusbar
- [ ] Add process tree view (optional)

**Acceptance Criteria**:
- Process stats display in statusbar
- Stats update in real-time
- No significant performance impact

**Checklist**:
- [ ] Process monitoring implemented
- [ ] Statusbar displays stats
- [ ] Performance acceptable

---

#### P3.4: Web Export (Optional)
**Depends on**: P3.1
**Effort**: 2-3 hours

- [ ] Set up `textual serve` integration
- [ ] Export app to web version
- [ ] Test web version functionality

**Acceptance Criteria**:
- `textual serve` exports app successfully
- Web version is functional

**Checklist**:
- [ ] Web export working
- [ ] Web UI functional

---

### Phase 3 Testing

**Test Coverage Target**: 75%

- [ ] Unit tests for floating windows
- [ ] Integration tests for theme switching
- [ ] E2E tests for dialogs

---

### Phase 3 Deliverables

1. **Feature-complete compositor**
   - All advanced features working
   - Theme support
   - Optional web export

2. **Performance benchmarks**
   - Memory usage: <100MB idle
   - CPU usage: <2% idle

3. **Documentation**
   - User manual
   - Plugin development guide
   - Theme customization guide

---

## Quality Gates

### Code Quality

- [ ] All files pass `ruff check`
- [ ] All files pass type checking (`pyright` or `mypy`)
- [ ] No new lint suppressions without justification
- [ ] Test coverage ≥80% for compositor core

### Testing

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] E2E tests for key workflows
- [ ] Manual testing (interactive pane, splits, persistence)

### Performance

- [ ] App startup: <500ms
- [ ] Pane creation: <100ms
- [ ] Layout switch: <50ms
- [ ] Idle memory: <100MB
- [ ] Idle CPU: <2%

### Documentation

- [ ] `proposal.md` complete
- [ ] `design.md` complete
- [ ] `tasks.md` complete (this file)
- [ ] README for compositor module
- [ ] User guide

---

## Work Stream Integration

### Work Items

Add to `WORK_STREAM.md`:

```
## ACTIVE

### research-tui-compositor
- Status: IN_PROGRESS
- Priority: P1
- Owner: [agent-id]
- Depends on: -
- Blocking: -
- Progress:
  - [x] Proposal written
  - [x] Design written
  - [ ] Phase 1 (foundation) complete
  - [ ] Phase 2 (compositor) complete
  - [ ] Phase 3 (advanced) complete
  - [ ] Quality gates passed
  - [ ] Merged to main
```

### Related Tasks

- **research-tui-compositor**: This implementation
- **research-sitback-ui**: Use compositor for Sitback dashboard
- **research-unified-system-app**: Integrate compositor into unified app

---

## Success Criteria (Final)

1. ✅ App starts in <500ms
2. ✅ Menubar with File/Edit/View/Tools/Help menus functional
3. ✅ Statusbar displays session name, agent status, real-time clock
4. ✅ Can split panes horizontally and vertically; focus switching works
5. ✅ Terminal panes execute shell commands and display output
6. ✅ Keyboard shortcuts work (Ctrl+N, Ctrl+V, Ctrl+X, Ctrl+L)
7. ✅ Layouts can be saved to and restored from YAML
8. ✅ Session state persists across app restart
9. ✅ All linters pass; no new lint suppressions
10. ✅ Test coverage ≥80% for compositor core logic

---

## References

- **Proposal**: [./proposal.md](./proposal.md)
- **Design**: [./design.md](./design.md)
- **Research**: [../../research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md](../../research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md) § 2
- **Textual Docs**: https://textual.textualize.io/
- **Related Plan**: [../../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md](../../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md)
