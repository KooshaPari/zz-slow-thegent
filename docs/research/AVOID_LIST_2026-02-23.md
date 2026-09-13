<DONE>
# Avoid List - Repos to Avoid

Date: February 23, 2026

## Overview

This document tracks repositories that should be avoided for integration due to specific risk factors.

## Avoid Criteria

- Archived/inactive
- High-privilege security concerns
- Weak governance posture
- Unclear licensing
- Supply chain risks

## Avoid List

### Critical Avoid (Do Not Use)

| Repo                                              | Reason for Avoidance | Severity | Notes                                                |
| ------------------------------------------------- | -------------------- | -------- | ---------------------------------------------------- |
| `textcortex/claude-code-sandbox`                  | ARCHIVED             | Critical | Repository is archived, no longer maintained         |
| `mediar-ai/MCP-server-client-computer-use-ai-sdk` | HIGH PRIVILEGE       | Critical | High-privilege control with unclear security posture |

### High Risk Avoid

| Repo                          | Reason for Avoidance | Severity | Notes                                                                |
| ----------------------------- | -------------------- | -------- | -------------------------------------------------------------------- |
| Various ruvnet social signals | ANECDOTAL ONLY       | High     | Public posts (Reddit, LinkedIn) not reliable for technical decisions |

## Rationale

### textcortex/claude-code-sandbox

- **Status**: Archived as of 2026-02-22
- **Action**: Remove from consideration, no future evaluation needed

### mediar-ai/MCP-server-client-computer-use-ai-sdk

- **Status**: High-privilege control requirements
- **Concern**: Unclear security posture
- **Action**: Avoid unless security posture significantly improves

### Social Signals (ruvnet)

- **Issue**: Reddit posts and LinkedIn updates are marketing/signaling
- **Action**: Use only for awareness, not technical evaluation

## Re-evaluation Criteria

These repos may be re-evaluated if:

1. Significant security improvements
2. Active maintenance resumes
3. Clear governance established
4. Community validation

## Related

- See `docs/research/WATCH_LIST_2026-02-23.md` for repos under observation
- See `docs/research/PHASE_2_FINAL_COMPLETION_SUMMARY_2026-02-23.md` for adopt/pilot decisions
