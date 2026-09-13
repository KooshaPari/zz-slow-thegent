# TUI Compositor Implementation

A terminal user interface compositor for the Thegent agent orchestration platform.

**Status**: Phase 1 (Foundation) Complete
**Date**: 2026-02-18

## Overview

The TUI Compositor provides a GUI-like experience in the terminal with:

- Menu bar for navigation
- Status bar for real-time information
- Terminal pane splitting (horizontal/vertical)
- Session persistence
- Keyboard shortcuts for efficient navigation

## Architecture

### Layered Design

```
┌─────────────────────────────────────────┐
│ CompositApp (Textual.App)               │
├─────────────────────────────────────────┤
│ Header | Statusbar | Footer             │
├─────────────────────────────────────────┤
│ Vertical Container (Pane Layout)        │
│  ├─ TerminalPane 1                      │
│  ├─ TerminalPane 2                      │
│  └─ ...                                 │
├─────────────────────────────────────────┤
│ PaneManager (Tree Structure)            │
│  └─ Handles split/merge/focus           │
├─────────────────────────────────────────┤
│ SessionState (Persistence)              │
│  └─ YAML files in ~/.config/thegent/    │
└─────────────────────────────────────────┘
```

### Components

| Component    | Purpose                   | Status  |
| ------------ | ------------------------- | ------- |
| CompositApp  | Main application          | ✅ P1.2 |
| TerminalPane | PTY-based terminal widget | 🔲 P1.3 |
| PaneManager  | Split/merge tree logic    | 🔲 P2.1 |
| SessionState | Persistence layer         | ✅ P1.1 |
| Statusbar    | Real-time status display  | ✅ P1.2 |

## Phase Progress

### Phase 1: Foundation ✅ IN PROGRESS

- [x] P1.1: Project Setup & Dependencies
- [x] P1.2: CompositApp Skeleton
- [ ] P1.3: TerminalPane Widget
- [ ] P1.4: Basic Integration & Single-Pane Demo

### Phase 2: Compositor Integration (Week 2)

- [ ] P2.1: PaneManager Foundation
- [ ] P2.2: UI Integration for Pane Operations
- [ ] P2.3: Layout Serialization
- [ ] P2.4: Session Persistence
- [ ] P2.5: Layout Management UI

### Phase 3: Advanced Features (Week 3)

- [ ] P3.1: Floating Windows & Dialogs
- [ ] P3.2: Theme Support
- [ ] P3.3: Real-Time Process Monitoring (Optional)
- [ ] P3.4: Web Export (Optional)

## Key Bindings

| Binding  | Action           |
| -------- | ---------------- |
| `Ctrl+N` | New Pane         |
| `Ctrl+V` | Split Vertical   |
| `Ctrl+H` | Split Horizontal |
| `Ctrl+X` | Close Pane       |
| `Ctrl+L` | Focus Next Pane  |
| `Ctrl+Q` | Quit             |

## File Structure

```
src/thegent/ui/
├── compositor/
│   ├── __init__.py           # Module exports
│   ├── app.py                # CompositApp class
│   ├── terminal_pane.py      # TerminalPane widget
│   ├── pane_manager.py       # Pane tree management
│   └── session_state.py      # Session persistence

tests/ui/compositor/
├── conftest.py               # Test fixtures
├── test_basic.py             # Basic functionality tests
├── test_app.py               # CompositApp tests
├── test_pane_manager.py      # (existing)
├── test_terminal_pane.py     # (existing)
└── test_session_state.py     # (existing)

docs/changes/research-tui-compositor/
├── proposal.md               # Proposal and requirements
├── design.md                 # Design details (to be completed)
├── tasks.md                  # Task breakdown and acceptance criteria
└── README.md                 # This file
```

## Getting Started

### Installation

```bash
# Install dependencies
uv sync --group dev

# Verify module structure
python -c "from thegent.ui.compositor import CompositApp; print('✓')"
```

### Testing

```bash
# Run basic tests
pytest tests/ui/compositor/test_basic.py -v

# Run all compositor tests
pytest tests/ui/compositor/ -v

# Check coverage
pytest tests/ui/compositor/ --cov=src/thegent/ui/compositor
```

### Running the App (When Ready)

```bash
# P1.4 will implement this
python -m thegent.ui.compositor
```

## Development Roadmap

### Phase 1 Completion Criteria

- [x] Module structure created and importable
- [x] Tests discoverable and basic tests passing
- [x] CompositApp renders with Header/Footer/Statusbar
- [ ] TerminalPane with PTY integration
- [ ] Single pane interactive demo

### P1.3 Tasks (Next)

1. Implement PTY allocation in TerminalPane
2. Shell process spawning
3. Input/output handling
4. Cleanup on pane close
5. Unit tests for PTY operations

### P1.4 Tasks

1. Integrate TerminalPane into CompositApp
2. Implement action_new_pane()
3. Verify interactive shell works
4. Performance benchmarks
5. Integration tests

## Dependencies

- **Textual**: Terminal UI framework
- **PyYAML**: Session state serialization
- **Python 3.12+**: Runtime

## Performance Targets

| Metric        | Target | Status       |
| ------------- | ------ | ------------ |
| App startup   | <500ms | 🔲 To verify |
| Pane creation | <100ms | 🔲 To verify |
| Layout switch | <50ms  | 🔲 To verify |
| Idle memory   | <100MB | 🔲 To verify |
| Idle CPU      | <2%    | 🔲 To verify |

## References

- **Proposal**: [proposal.md](./proposal.md)
- **Design**: [design.md](./design.md)
- **Tasks**: [tasks.md](./tasks.md)
- **Research**: [../../research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md](../../research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md) § 2
- **Textual Docs**: https://textual.textualize.io/

## Contributing

To contribute to the TUI Compositor:

1. Follow the phase progression (P1 → P2 → P3)
2. Implement tests first (TDD pattern)
3. Verify code compiles and imports
4. Update acceptance criteria as you complete tasks
5. Document any design decisions in design.md

## Contact

For questions or issues, refer to the main thegent documentation.
