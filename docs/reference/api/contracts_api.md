# contracts API Reference

> **Source**: `src/thegent/contracts/__init__.py`

Contract registry and canonical schema for thegent orchestration.

Provides:

- ContractRegistry: authoritative contract versioning and compatibility
- CanonicalStructuredMessage (CSM): unified schema for agent outputs
- OutputAdapter: protocol for provider-specific output normalization
- ChunkEvent, EvidenceEvent, PolicyEvent: canonical event schemas (WP-0002)

OPT-006: Lazy adapter loading (import on first use) - Reduce startup time ~200ms.

---
