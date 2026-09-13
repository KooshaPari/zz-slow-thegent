# Sitback Plugin API

Plugins extend the Sitback Agent with dashboard widgets and startup steps.

## Discovery

Plugins are loaded from `~/.claude/sitback-plugins/`:

- **JSON plugins** (`*.json`): Static widgets and startup steps
- **Python plugins** (`*.py`): Dynamic registration via `register_sitback(registry)`

## JSON Plugin Format

```json
{
  "startup_steps": ["Check harness status before presenting dashboard."],
  "widgets": {
    "my-widget": {
      "title": "Custom Panel",
      "content": "Static content here",
      "border_style": "cyan"
    }
  }
}
```

- `startup_steps`: Extra lines appended to the startup prompt (when not `--no-dashboard`)
- `widgets`: Dashboard panels shown when `--profile full` (CLI) or `profile=full` (MCP)

## Python Plugin Format

```python
def register_sitback(registry):
    registry.register_startup_step("Run custom pre-check.")
    registry.register_widget(
        "dynamic", lambda: {"title": "Live Data", "content": fetch_live_data(), "border_style": "green"}
    )
    registry.register_harness_status(lambda: get_heliosShield_status())  # override default
```

### Registry Methods

| Method                        | Purpose                                   |
| ----------------------------- | ----------------------------------------- | ------------------------- |
| `register_widget(name, fn)`   | `fn()` → `{title, content, border_style}` |
| `register_startup_step(step)` | Append line to startup prompt             |
| `register_harness_status(fn)` | `fn()` → `dict                            | None` (heliosShield/FUSE) |

## Harness / heliosShield Placeholder

When `THGENT_SITBACK_HARNESS=1`, the built-in harness placeholder shows a "heliosShield/FUSE integration coming when plugin lands" panel in `--profile full`. Plugins can override via `register_harness_status()`.

## Profiles

| Profile  | Dashboard content                            |
| -------- | -------------------------------------------- |
| `light`  | Summary line only                            |
| `medium` | Sessions, circuits, drift, budget, terminals |
| `full`   | Medium + plugin widgets + harness status     |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
