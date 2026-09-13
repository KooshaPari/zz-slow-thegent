# Worklog Wave 81 - Lane A

## Summary

This lane analyzed CLIProxyAPI bug items that affect thegent indirectly or directly through request-shape and streaming contracts.

## Main takeaways

- Tool-name parity needs fail-fast validation before proxy dispatch.
- Streaming completion behavior needs regression coverage.
- Provider-switch state/signature handling should be explicit in tests.

## Next steps

1. Add a focused parity test for `tool_choice.name` vs `tools[].name`.
2. Add a streaming regression test for completion markers.
3. Add request-shape guards for known `INVALID_ARGUMENT` patterns.
