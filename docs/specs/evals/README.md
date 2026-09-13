# Evaluation & Benchmarks Domain Technical Specification

## Overview

Model evaluation, benchmarking, and quality metrics.

## Benchmarks

| Benchmark          | Purpose      | Files                  |
| ------------------ | ------------ | ---------------------- |
| Terminal Bench 2.0 | Coding       | `bench/models.py`      |
| SWE-Bench          | Software eng | External               |
| Custom evals       | Domain       | `evals/integration.py` |

### Metrics

| Metric          | Purpose         |
| --------------- | --------------- |
| Quality score   | Output quality  |
| Speed score     | Latency         |
| Cost score      | Token usage     |
| Pareto frontier | Multi-objective |

## Quality Gates

- Benchmarks pass
- Regression detection
- Cost thresholds
- Latency SLAs
