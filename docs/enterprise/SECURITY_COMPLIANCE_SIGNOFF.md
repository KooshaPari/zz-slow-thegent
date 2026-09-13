# Security and Compliance Signoff Package

**Version:** 1.0
**Status:** PROVISIONAL
**Date:** 2026-02-14

## 1. Executive Summary

Thegent orchestration layer provides a unified control plane for agent execution. This document details the security controls, compliance posture, and risk mitigation strategies implemented in the system.

## 2. Security Architecture

- **Identity & Access Management:**
  - Local execution uses OS-level permissions.
  - Proxy execution uses Fernet-encrypted API keys.
  - MCP server supports tool-approval loops for sensitive operations.
- **Data Protection:**
  - All session logs stored in `~/.factory/sessions` with 0700 permissions.
  - API keys managed via `thegent.config` with sensitive field masking in logs.
  - Evidence set hashes (SHA-256) ensure audit trail integrity.
- **Network Security:**
  - FastMCP server defaults to localhost (127.0.0.1).
  - Outbound agent calls restricted to configured provider endpoints.

## 3. Compliance Framework

| Requirement    | Implementation            | Status      |
| -------------- | ------------------------- | ----------- |
| Audit Trail    | RunRegistry hash-chaining | ✓ Compliant |
| Immutable Logs | WORM-simulated storage    | ✓ Compliant |
| Policy Gating  | PolicyEngine pre-check    | ✓ Compliant |
| Access Control | Env-scoped owner tags     | ✓ Compliant |

## 4. Threat Model & Mitigations

- **Threat:** Agent prompt injection to leak API keys.
  - _Mitigation:_ System prompt constraints + tool-call budget injection.
- **Threat:** Unauthorized access to session logs.
  - _Mitigation:_ OS-level isolation + ownership-tagged scopes.
- **Threat:** Replay attacks on governance artifacts.
  - _Mitigation:_ RUN_ID correlation + timestamped hash chains.

## 5. Signoff

- **Architecture:** ✓ Approved 2026-02-14
- **Security:** [PENDING]
- **Compliance:** [PENDING]

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
