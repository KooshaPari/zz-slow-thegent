# OAuth-Only Authentication Policy

## Policy Statement

**If a provider offers OAuth, the API key-based solution is removed entirely.**

- **OAuth providers:** claude, codex, gemini, copilot, antigravity, iflow, kiro, kilo, roo, qwen, kimi
- **API keys:** NOT used for OAuth-capable providers
- **Authentication method:** OAuth only via `thegent cliproxy login <provider>`

## Implementation

### Doctor Command

The `thegent doctor` command now:

1. **Checks OAuth credentials** for all OAuth-capable providers
2. **Requires at least one OAuth provider** to be configured
3. **Does NOT check for API keys** (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
4. **Fails if no OAuth providers are configured** (required feature)

### Configuration Checks

- ✅ **OAuth credentials found:** Provider is configured and ready
- ❌ **OAuth credentials missing:** Run `thegent cliproxy login <provider>`
- ❌ **No providers configured:** At least one OAuth provider must be configured

### Headless Runs

Headless runs (Claude, Codex) require OAuth credentials:

- ✅ **OAuth credentials exist:** Headless runs will be tested
- ❌ **OAuth credentials missing:** Headless runs will fail with clear fix hint

## Migration from API Keys

If you were previously using API keys:

1. **Remove API keys** from environment variables and `.env` files
2. **Run OAuth login** for each provider:
   ```bash
   thegent cliproxy login claude
   thegent cliproxy login codex
   thegent cliproxy login gemini
   ```
3. **Verify** with `thegent doctor`

## Provider Status

| Provider    | OAuth Support | API Key Support |
| ----------- | ------------- | --------------- |
| claude      | ✅ Required   | ❌ Removed      |
| codex       | ✅ Required   | ❌ Removed      |
| gemini      | ✅ Required   | ❌ Removed      |
| copilot     | ✅ Required   | ❌ Removed      |
| antigravity | ✅ Required   | ❌ Removed      |
| iflow       | ✅ Required   | ❌ Removed      |
| kiro        | ✅ Required   | ❌ Removed      |
| kilo        | ✅ Required   | ❌ Removed      |
| roo         | ✅ Required   | ❌ Removed      |
| qwen        | ✅ Required   | ❌ Removed      |
| kimi        | ✅ Required   | ❌ Removed      |

## Rationale

1. **Security:** OAuth is more secure than API keys
2. **User experience:** OAuth login is simpler (browser-based)
3. **Consistency:** Single authentication method per provider
4. **Maintenance:** Less code to maintain (no API key fallback logic)

## Enforcement

- **Doctor command:** Fails if no OAuth providers configured
- **Headless runs:** Fail if OAuth credentials missing
- **Provider validation:** Requires OAuth credentials to pass

All features are **required** - nothing is optional.

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
