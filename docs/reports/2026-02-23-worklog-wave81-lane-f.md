# Worklog Wave 81 - Lane F

## Summary

This lane reviewed connector queue and throttle hardening for retry/resume behavior.

## Main takeaways

- Dead-letter capture and replay are already present.
- Retry backoff logic is already present.
- The missing piece is lifecycle wiring and traceable metrics.

## Next steps

1. Connect dead-letter replay to a scheduled or CLI-triggered path.
2. Surface queue depth and retry age in telemetry.
3. Expose throttle audit details in the autosync metrics exporter.
