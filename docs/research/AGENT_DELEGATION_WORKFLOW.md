<DONE>
# Agent Delegation Workflow

**Date:** 2026-02-17
**Status:** Setup in Progress
**Purpose:** Document the workflow for using thegent CLI agents for parallel task completion

---

## Overview

The thegent CLI provides two main agent types for delegation:

1. **Flash Agents** (`thegent dex flash`) - Fast, cheap model (Gemini 3 Flash) for generating writeups, specs, and research
2. **Free Agents** (`thegent free`) - Free tier agent (gpt-5-mini) for task completion and development from synthesized writeups

---

## Workflow Pattern

### Phase 1: Research & Writeup Generation (Flash Agents)

Use `thegent dex flash` to generate comprehensive research writeups and implementation plans:

```bash
# Generate research writeup
thegent dex flash --print "Generate comprehensive research writeup for: <task-id> - <description>. Include: 1) Current state audit, 2) Implementation plan, 3) Migration steps, 4) Testing strategy. Save to docs/research/<TASK_ID>_PLAN.md"
```

**Use Cases:**

- Research tasks that need deep analysis
- Implementation plans from requirements
- Migration strategies
- Architecture decisions

### Phase 2: Implementation (Free Agents)

Use `thegent free` to implement tasks from generated writeups:

```bash
# Implement from writeup
thegent free "Implement <task-id> based on docs/research/<TASK_ID>_PLAN.md. Follow the implementation plan step by step."

# Or use --do-next for automatic work stream processing
thegent free --do-next --repeat 5
```

**Use Cases:**

- Code implementation from specs
- Migration work
- Feature development
- Bug fixes

---

## Current Status

### Setup Requirements

**Prerequisites:**

1. ✅ Runtime infrastructure initialized (Phase 1-3 complete)
2. ⚠️ CLIProxyAPIPlus service must be running for `thegent dex flash`
3. ✅ `thegent free` should work independently

**Proxy Service:**

- Default port: `8317`
- Start with: `thegent serve` or `thegent mcp up`
- Check status: `thegent doctor`

### Known Issues

1. **Proxy Port Mismatch:**
   - Proxy running on port `8318` (detected: `/Users/kooshapari/.local/bin/cli-proxy-api-plus`)
   - thegent trying to connect to port `8317`
   - **Status:** Proxy is running but on different port
   - **Solution:** Configure thegent to use port 8318 or restart proxy on 8317

2. **Proxy Connection Errors (when using wrong port):**
   - `404 Not Found` for websocket connections
   - `502 Bad Gateway: unknown provider for model`
   - **Workaround:** Use `thegent free` which doesn't require proxy, or fix port configuration

3. **Import Error (Fixed):**
   - `ImportError: cannot import name 'app' from 'thegent.main'`
   - **Status:** Fixed in main.py initialization

---

## Delegation Examples

### Example 1: Library Migration Task

**Step 1: Generate Writeup (Flash)**

```bash
thegent dex flash --print "Generate research writeup for: research-library-retry - Migrate manual retry loops to tenacity (4 files). Include: 1) Audit of current retry implementations, 2) tenacity integration plan, 3) Migration steps for each file, 4) Testing strategy. Save to docs/research/LIBRARY_RETRY_MIGRATION_PLAN.md"
```

**Step 2: Implement (Free)**

```bash
thegent free "Implement research-library-retry migration based on docs/research/LIBRARY_RETRY_MIGRATION_PLAN.md. Migrate all 4 files to use tenacity."
```

### Example 2: Documentation Task

**Step 1: Generate Writeup (Flash)**

```bash
thegent dex flash --print "Generate implementation plan for: vitepress-vhs-setup - Set up VHS for terminal recordings. Include: 1) VHS installation, 2) VitePress integration, 3) Example workflows, 4) Automation scripts. Save to docs/research/VITEPRESS_VHS_SETUP_PLAN.md"
```

**Step 2: Implement (Free)**

```bash
thegent free "Set up VHS for terminal recordings based on docs/research/VITEPRESS_VHS_SETUP_PLAN.md"
```

---

## Parallel Work Strategy

### Batch Processing

Use `--repeat` flag for parallel work:

```bash
# Process 5 work items in sequence
thegent free --do-next --repeat 5
```

### Background Execution

Use `--bg` flag for async execution:

```bash
# Run in background
thegent free --bg "Implement task X"
thegent free --bg "Implement task Y"
thegent free --bg "Implement task Z"
```

---

## Next Steps

1. **Fix Proxy Service:**
   - Ensure CLIProxyAPIPlus is running
   - Verify configuration
   - Test `thegent dex flash` connectivity

2. **Test Delegation:**
   - Generate writeups with flash agents
   - Implement tasks with free agents
   - Verify parallel execution

3. **Scale Up:**
   - Use for all work stream items
   - Automate with `--do-next`
   - Monitor progress

---

## References

- **Work Stream:** [docs/reference/WORK_STREAM.md](../reference/WORK_STREAM.md)
- **Runtime Infrastructure:** [RUNTIME_INFRASTRUCTURE_INTEGRATION_PHASE3_COMPLETE.md](RUNTIME_INFRASTRUCTURE_INTEGRATION_PHASE3_COMPLETE.md)
- **thegent CLI Docs:** Run `thegent --help` for full command reference
