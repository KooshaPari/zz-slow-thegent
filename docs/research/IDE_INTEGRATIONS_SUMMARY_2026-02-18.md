<DONE>
# IDE Integrations Summary

**Date**: 2026-02-18
**Status**: Research Complete, Implementation Ready

---

## Key Findings

### 1. Serena (oraios/serena) ✅ Already Integrated

**Status**: Integrated via MCP mount
**JetBrains Plugin**: Available but not yet integrated
**Opportunity**: Add JetBrains plugin support as alternative backend

### 2. Serenade (serenadeai/serenade) ❌ Not Integrated

**Status**: Voice coding tool, different from Serena
**JetBrains Plugin**: Available
**Priority**: Low (niche use case)

### 3. Ghostty ⚠️ Terminal, Not IDE Integration

**Status**: Terminal emulator with shell integration
**IDE Integration**: Not applicable (terminal tool)
**Opportunity**: Use for agent terminal workflows

---

## Integration Plan

### Phase 1: Serena JetBrains Plugin (Week 1)

- Auto-detect JetBrains plugin
- Prefer plugin over LSP backend
- Unified configuration

### Phase 2: Ghostty Terminal (Week 2)

- Terminal session management
- Shell integration setup
- Agent terminal workflows

### Phase 3: Unified IDE Layer (Week 3-4)

- IDE abstraction
- Multiple IDE support
- MCP exposure

---

## Quick Start

### Enable Serena JetBrains Plugin

1. Install plugin: https://plugins.jetbrains.com/plugin/28946-serena
2. Configure in thegent:

   ```bash
   # Auto-detect (default)
   THGENT_SERENA_BACKEND=auto thegent serve

   # Force JetBrains plugin
   THGENT_SERENA_BACKEND=jetbrains thegent serve
   ```

### Check Ghostty Integration

```bash
# Check Ghostty installation
thegent terminal ghostty-check

# Verify shell integration
echo $GHOSTTY_RESOURCES_DIR
```

---

## Files Created

- `docs/research/IDE_INTEGRATIONS_AUDIT_AND_PLAN_2026-02-18.md` - Full audit & plan
- `docs/research/IDE_INTEGRATIONS_SUMMARY_2026-02-18.md` - This summary

---

## Next Steps

1. Implement Phase 1 (Serena JetBrains plugin support)
2. Test with JetBrains IDE Ultimate
3. Document integration guide
4. Move to Phase 2 (Ghostty terminal)
