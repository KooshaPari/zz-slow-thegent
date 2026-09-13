<DONE>
# Doctor Command: OAuth-Only Authentication Update

**Date:** 2026-02-17
**Status:** Complete

## Changes Made

### 1. Removed API Key Checks

**Before:**

- Checked for `ANTHROPIC_API_KEY` environment variable
- Failed if API key not set

**After:**

- Removed API key checks entirely
- OAuth-only authentication for all OAuth-capable providers

### 2. OAuth Provider Validation

**New Check:**

- Checks for OAuth credentials for all OAuth-capable providers
- Requires at least ONE OAuth provider to be configured
- Lists configured providers in success message

**OAuth Providers:**

- claude, codex, gemini, copilot, antigravity, iflow, kiro, kilo, roo, qwen, kimi

### 3. Headless Runs

**Before:**

- Checked for `ANTHROPIC_API_KEY` before running headless tests
- Warned if API key missing

**After:**

- Checks for OAuth credentials before running headless tests
- Fails if OAuth credentials missing (required feature)
- Clear fix hints pointing to OAuth login

### 4. Provider Validation

**Before:**

- Warned on provider failures
- Optional feature

**After:**

- Fails on provider failures (required feature)
- Suggests OAuth login on auth errors (401/403)
- All providers must work

### 5. No Optional Features

**Before:**

- Headless runs were warnings
- Nix config was optional
- Some failures didn't count against success

**After:**

- All features are required
- All failures count against success
- Nix config only fails if Nix is installed (otherwise ok)

## Policy Enforcement

**OAuth-Only Policy:**

- If provider offers OAuth → OAuth is REQUIRED
- API keys are NOT checked or used
- At least one OAuth provider must be configured

**Required Features:**

- OAuth provider configuration (at least one)
- Headless runs (Claude, Codex)
- Provider validation (all configured providers must work)
- MCP server connectivity
- CLIProxy connectivity

## Migration Guide

1. **Remove API keys** from environment:

   ```bash
   unset ANTHROPIC_API_KEY
   unset OPENAI_API_KEY
   unset GOOGLE_API_KEY
   ```

2. **Configure OAuth providers:**

   ```bash
   thegent cliproxy login claude
   thegent cliproxy login codex
   thegent cliproxy login gemini
   ```

3. **Verify with doctor:**
   ```bash
   thegent doctor
   ```

## Files Changed

- `src/thegent/doctor.py` - Updated configuration and provider checks
- `docs/guides/OAUTH_ONLY_AUTHENTICATION.md` - Policy documentation
- `docs/guides/DOCTOR_FIXES.md` - Previous fixes (now superseded)

## Rationale

1. **Security:** OAuth is more secure than API keys
2. **Consistency:** Single authentication method per provider
3. **Simplicity:** No API key management needed
4. **Enforcement:** All features required, nothing optional

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
