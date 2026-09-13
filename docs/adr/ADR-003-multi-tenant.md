# ADR-003: Multi-Tenant Architecture

**Date**: 2026-04-02  
**Status**: Proposed  
**Deciders**: Agent

## Context

thegent needs to support multi-tenant deployments where multiple users/teams share the same infrastructure while maintaining isolation.

## Decision Drivers

- **Isolation**: Strong boundaries between tenants
- **Scalability**: Support 1000+ tenants
- **Efficiency**: Shared resources where safe
- **Security**: No cross-tenant data leakage

## Options Considered

### Isolation Models

| Model         | Isolation | Overhead | Complexity |
| ------------- | --------- | -------- | ---------- |
| **Namespace** | Process   | Low      | Medium     |
| **Container** | Kernel    | Medium   | Medium     |
| **VM**        | Hardware  | High     | High       |

## Decision

**Hybrid: Namespaces for metadata, Containers for execution, VMs for sensitive workloads**

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    thegent Multi-Tenant                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │                Shared Control Plane                   ││
│  │  • API Gateway (auth per tenant)                    ││
│  │  • Metadata Database (tenant_id column)          ││
│  │  • Shared cache (namespaced)                       ││
│  └─────────────────────────────────────────────────────┘│
│                          │                               │
│  ┌───────────────────────▼─────────────────────────────┐│
│  │              Tenant Isolation Layer                 ││
│  │                                                      ││
│  │  Tenant A            Tenant B           Tenant C   ││
│  │  ┌─────────┐         ┌─────────┐        ┌─────────┐ ││
│  │  │ Control │         │ Control │        │ Control │ ││
│  │  │ Plane   │         │ Plane   │        │ Plane   │ ││
│  │  │ (NS)    │         │ (NS)    │        │ (NS)    │ ││
│  │  └────┬────┘         └────┬────┘        └────┬────┘ ││
│  │       │                   │                  │      ││
│  │       ▼                   ▼                  ▼      ││
│  │  ┌─────────┐         ┌─────────┐        ┌─────────┐ ││
│  │  │Sandbox 1│         │Sandbox 1│        │Sandbox 1│ ││
│  │  │ (gVisor)│         │(Firecracker)      │(bubble) │ ││
│  │  └─────────┘         └─────────┘        └─────────┘ ││
│  │                                                      ││
│  │  Execution tier based on tenant trust level         ││
│  │                                                      ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Consequences

### Positive

- **Scalable**: Support many tenants
- **Flexible**: Different isolation per tenant
- **Efficient**: Shared control plane

### Negative

- **Complex**: Multiple isolation mechanisms
- **Security surface**: More to audit

## References

- thegent SOTA Research: `docs/research/AGENT_FRAMEWORKS_SOTA.md`
