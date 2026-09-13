# trace API Reference

> **Source**: `src/thegent/trace/__init__.py`

Deterministic replay system for agent execution traces.

This package provides:

- TraceRecorder: Record agent execution to JSONL traces
- ReplayEngine: Replay traces with mocked LLM/file I/O
- DiffAnalyzer: Compare original vs. replayed execution
- TraceVariator: Generate parameterized trace variations

---
