# MCP, A2A, and Control-Plane Boundary

## Purpose

Define clear ownership boundaries for governance-related protocol surfaces.

## MCP Boundary

1. MCP is the model/tool boundary.
2. MCP tools expose governance reads/writes for:
   - policy status
   - worktree policy reports
   - delegation recommendations
3. MCP should not own inter-agent orchestration state machines.

## A2A Boundary

1. A2A is the agent-to-agent handoff and task-lifecycle boundary.
2. A2A messages carry:
   - task descriptor
   - classifier outputs
   - routing hints (`L2/L3/Ln`)
   - execution status and completion payloads
3. A2A should not encode tool execution internals.

## Internal Control Plane Boundary

1. Scheduler, placement, and queueing are internal control-plane concerns.
2. Control plane owns:
   - worktree placement
   - overlap-risk scoring
   - conflict escalation
   - merge-train gating
3. Control plane emits artifacts for MCP and A2A, but remains source-of-truth.

## Contract Outputs

1. `task classifier schema` -> placement and delegation.
2. `worktree inventory artifact` -> conformance.
3. `governance metrics jsonl` -> policy SLOs.
