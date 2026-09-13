# Worklog Wave 81 - Lane E

## Summary

This lane reviewed connector reliability work around rollup and telemetry initiatives.

## Main takeaways

- Queue/replay plumbing already exists.
- Throttle/backoff handling already exists.
- The next step is to surface queue depth, age, and throttle state in metrics.

## Next steps

1. Wire the replay engine into a scheduled job or CLI hook.
2. Expose queue depth/age and throttle state in metrics.
3. Validate traceable resume examples in the worklog docs.
