# Provider Bridge Contract Scaffold

This directory defines the unified API/SDK bridge contract for metaprovider execution.

## Layout

- `schema/`: JSON Schema source of truth.
- `types/`: language stubs/interfaces (Go + Python).
- `tests/`: fixture-driven schema/interface tests.

## Contract Goals

1. One request/response shape across all execution lanes.
2. Lane and provider specialization through typed inheritance.
3. Stable IDs for end-to-end observability and fallback lineage.
4. Harness/runtime decoupling from provider-specific internals.

## Core IDs

- `run_id`
- `request_id`
- `attempt_id`
- `route_id`
- `tool_call_id`

## Execution Lanes

- `litellm_donut`
- `bifrost`
- `native`

## Notes

- Schemas intentionally use strict `additionalProperties: false`.
- Version every payload with `bridge_schema_version`.
