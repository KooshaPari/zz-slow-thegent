# power API Reference

> **Source**: `src/thegent/infra/power.py`

Power management utilities (macOS sleep prevention).

---

## is_mac_sleep_prevention_enabled

Check if macOS sleep prevention is enabled in settings.

---

## wrap_with_caffeinate

```python
wrap_with_caffeinate(cmd: list[str], agent_name: Any)
```

Wrap command with caffeinate on macOS to keep Mac awake during long-running tasks.

**Parameters**:

- `cmd`: Command to wrap
- `agent_name`: Name of the agent (claude, codex, etc.) to check against config.
  If None, it wraps regardless of agent name if mac_keep_awake is True.

---
