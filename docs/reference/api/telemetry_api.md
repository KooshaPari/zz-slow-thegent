# telemetry API Reference

> **Source**: `src/thegent/telemetry/__init__.py`

OTel GenAI instrumentation and run correlation (WP-Y6, NFR-013).

Provides OpenTelemetry spans with GenAI semantic conventions and run_id correlation
across orchestration, agent calls, and status. Re-exports from observability for
unified access.

Usage:
from thegent.telemetry import instrument_genai_call, instrument_run_bg_status

    with instrument_genai_call(agent_name="claude", model="claude-3-5-sonnet", run_id=run_id):
        ...

---
