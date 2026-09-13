# Hook Point Latency Benchmark (2026-02-18)

- Scope: targeted latency checks for hook-stop profiles and roid harness dispatch.
- Host: local macOS workstation.
- Method: `hyperfine` with warmup and repeated runs; values in seconds.

| Scenario                                     | Runs |   Mean |    P50 |    P95 |    P99 |    Min |    Max |
| -------------------------------------------- | ---: | -----: | -----: | -----: | -----: | -----: | -----: |
| Stop hook point (ultrafast profile)          |    9 |  0.694 |  0.674 |  1.011 |  1.011 |  0.536 |  1.011 |
| Stop hook point (fast profile)               |    5 | 16.258 | 15.665 | 19.207 | 19.207 | 15.301 | 19.207 |
| CLI dispatch startup (`thegent roid --help`) |   15 |  4.074 |  3.352 |  6.299 |  7.246 |  2.415 |  7.246 |

## Notes

- `ultrafast` profile stayed sub-second in this run.
- `fast` profile was dominated by `quality-gate.sh` timeout envelope and returned non-zero; benchmark used ignore-failure mode to capture wall time.
- `thegent roid --help` reflects full CLI startup cost in current workspace state.
