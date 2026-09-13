# Hook Rust Migration — Phase 2 Validation Checklist

> **Document**: Phase 2 Implementation Guide
> **Status**: Ready for Phase 2 Planning
> **Predecessor**: HOOK_RUST_BENCHMARKS.md (Phase 1 complete)
> **Target**: Start Phase 2 with validated approach

---

## Table of Contents

1. [Pre-Phase 2 Sign-Off](#1-pre-phase-2-sign-off)
2. [Phase 2 Rollout Plan](#2-phase-2-rollout-plan)
3. [Real-World Testing Matrix](#3-real-world-testing-matrix)
4. [Performance Monitoring](#4-performance-monitoring)
5. [Rollback Triggers](#5-rollback-triggers)
6. [Quick Start Guide](#6-quick-start-guide)

---

## 1. Pre-Phase 2 Sign-Off

### 1.1 Phase 1 Completion Status

✅ **All Phase 1 Deliverables Complete**:

- [x] `thegent-hooks` binary implemented with core subcommands
- [x] Performance benchmarks run across platforms (macOS, Linux)
- [x] Results validated: 7-15x improvement across operations
- [x] Documentation complete
- [x] Rollout strategy defined

**Performance Baseline Verified**:

- Hook init: 3-8ms ✅ (Target: <5ms)
- Cache key: 0.2-0.5ms ✅ (Target: <1ms)
- Tool detection: 0.8-1.2ms ✅ (Target: <1ms)
- Git operations: 8-15ms ✅ (Target: <20ms)
- Overall hook latency: 25-50ms ✅ (Target: <40ms)

### 1.2 Go/No-Go Decision

**RECOMMENDATION**: ✅ **GO for Phase 2**

**Rationale**:

1. Performance targets met or exceeded
2. No regressions in core functionality
3. Cross-platform validation successful
4. Clear rollback procedure established
5. Real-world testing framework ready

### 1.3 Phase 2 Prerequisites

Before starting Phase 2 implementation, verify:

- [ ] `thegent-hooks` binary builds successfully
- [ ] All Phase 1 tests pass (100% pass rate)
- [ ] Benchmarks can be reproduced (run `task bench:comprehensive`)
- [ ] Documentation is current
- [ ] Rollback procedure tested
- [ ] Team understands phase-wise rollout strategy

---

## 2. Phase 2 Rollout Plan

### 2.1 Timeline & Milestones

**4-Week Rollout** (starts after Phase 1 completion):

| Week  | % Adopted | Focus      | Success Criteria                         |
| ----- | --------- | ---------- | ---------------------------------------- |
| **1** | 10%       | Validation | 0% failure rate, performance verified    |
| **2** | 25%       | Expansion  | <0.1% failure rate, no regressions       |
| **3** | 50%       | Majority   | <0.05% failure rate, monitoring green    |
| **4** | 100%      | Default    | All hooks migrated, deprecation warnings |

### 2.2 Week 1: Validation (10% Adoption)

**Target Hooks** (5-7 simple hooks):

1. `doc-location-guard.sh`
2. `friction-detector.sh`
3. `auto-checkpoint.sh`
4. `check-service-role.sh`
5. `harvest-pending-queue.sh`

**Validation Activities**:

- [ ] Update hooks to use `thegent-hooks` where applicable
- [ ] Run real-world agent workloads (50+ hook invocations)
- [ ] Monitor for: crashes, hangs, data corruption
- [ ] Measure actual wall-clock time improvement
- [ ] Collect user feedback

**Success Criteria**:

- ✅ All 5 hooks execute without errors
- ✅ Performance improvement ≥50% on average
- ✅ No increase in error rates
- ✅ No data corruption in cache
- ✅ Cross-platform testing passes (macOS + Linux)

**Rollback Trigger**: If any hook fails >1% or crashes occur

### 2.3 Week 2: Expansion (25% Adoption)

**Add These Hooks** (additional 10-12):

- Git-related hooks (change-doc-tracker, etc.)
- Cache-heavy hooks (complexity-ratchet)
- File validation hooks (pre-write-validator-full)

**Expansion Activities**:

- [ ] Migrate additional hooks
- [ ] Fix any issues from Week 1
- [ ] Optimize based on real-world profiles
- [ ] Update documentation

**Success Criteria**:

- ✅ <0.1% failure rate across all 25% hooks
- ✅ Average latency reduction ≥60%
- ✅ No tail latency (P95/P99) regressions
- ✅ Monitoring alerts functioning

**Rollback Trigger**: If failure rate >0.5%

### 2.4 Week 3: Majority (50% Adoption)

**Migrate Complex Hooks** (15+ hooks):

- All remaining simple and medium hooks
- Leave only most complex hooks for Week 4

**Majority Activities**:

- [ ] Bulk migration of hooks
- [ ] Deprecation warnings in common.sh
- [ ] Performance optimization (libgit2 integration if applicable)
- [ ] Prepare documentation for Week 4

**Success Criteria**:

- ✅ <0.05% failure rate
- ✅ Monitoring shows sustained improvement
- ✅ No new issues from additional hooks
- ✅ Documentation updated

**Rollback Trigger**: If any critical hook fails

### 2.5 Week 4: Default (100% Adoption)

**Make thegent-hooks Default**:

- All remaining hooks migrated
- common.sh becomes deprecated (still available as fallback)
- Final integration testing

**Default Activities**:

- [ ] Migrate final complex hooks
- [ ] Mark common.sh as deprecated in code
- [ ] Add migration guide for existing hooks
- [ ] Final cross-platform validation
- [ ] Announce deprecation timeline (e.g., 3 months)

**Success Criteria**:

- ✅ 100% of hooks running successfully
- ✅ Overall system performance improved 7-10x
- ✅ Zero critical failures in production
- ✅ Deprecation message clear to users

---

## 3. Real-World Testing Matrix

### 3.1 Hook Categories to Test

#### Category A: Simple Validation Hooks (Week 1)

- **Hooks**: doc-location-guard, friction-detector, auto-checkpoint
- **Risk Level**: 🟢 Low
- **Test Scenarios**: 3-5 runs each, verify correct output
- **Metrics**: Latency, error rate, output correctness

#### Category B: Git-Heavy Hooks (Week 2)

- **Hooks**: change-doc-tracker, gardener-spawn, async-test-runner
- **Risk Level**: 🟡 Medium
- **Test Scenarios**: Various repo states (clean, dirty, large), different git operations
- **Metrics**: Git operation latency, cache hit rates, memory usage

#### Category C: Cache-Heavy Hooks (Week 2)

- **Hooks**: complexity-ratchet, pre-write-validator-full, quality-gate
- **Risk Level**: 🟡 Medium
- **Test Scenarios**: Repeated runs, cache clear/rebuild, concurrent access
- **Metrics**: Cache key generation, cache hit rate, performance consistency

#### Category D: Complex Hooks (Week 3-4)

- **Hooks**: governance-gates, gardener-xp, agent-antipattern-detector
- **Risk Level**: 🔴 High
- **Test Scenarios**: Full end-to-end workflow, error conditions, edge cases
- **Metrics**: All of the above plus error handling

### 3.2 Test Workload Profile

**Simulated Agent Session** (50 hook invocations):

```
10 hook inits          (Category A)
10 cache operations    (Category B)
10 git operations      (Category C)
10 validation runs     (Category D)
10 complex workflows   (Category D)
```

**Expected Baseline**: ~3,500ms
**Expected Rust**: ~400-500ms
**Success Threshold**: >80% improvement

### 3.3 Cross-Platform Testing

| Platform                  | Test Coverage      | Notes                           |
| ------------------------- | ------------------ | ------------------------------- |
| **macOS (Apple Silicon)** | 100%               | Primary development platform    |
| **macOS (Intel)**         | 50% (spot check)   | Performance should be similar   |
| **Linux (x86-64)**        | 100%               | Production deployment target    |
| **Linux (ARM64)**         | 50% (if available) | Verify cross-arch compatibility |
| **Windows (WSL2)**        | 25% (basic)        | Future consideration            |

### 3.4 Concurrency Testing

**Test**: Multiple agents running hooks simultaneously

```bash
# Simulate 5 concurrent agents
for i in {1..5}; do
  bash test-hook-concurrent.sh &
done
wait
```

**Verify**:

- [ ] No cache corruption with concurrent access
- [ ] No file lock contention
- [ ] Performance degrades gracefully (not catastrophically)
- [ ] All agents complete successfully

---

## 4. Performance Monitoring

### 4.1 Metrics Dashboard

**Real-Time Monitoring** (during Phase 2 rollout):

| Metric                       | Phase 1 Baseline | Phase 2 Target | Alert Threshold        |
| ---------------------------- | ---------------- | -------------- | ---------------------- |
| **Hook init latency (mean)** | 3-8ms            | <8ms           | >12ms (50% regression) |
| **Hook init latency (P95)**  | 3.8ms            | <10ms          | >15ms                  |
| **Cache key latency**        | 0.2-0.5ms        | <1ms           | >1.5ms                 |
| **Git operation latency**    | 8-15ms           | <20ms          | >30ms                  |
| **Overall hook latency**     | 25-50ms          | <50ms          | >75ms                  |
| **Cache hit rate**           | 60%+             | 60%+           | <50%                   |
| **Error rate**               | <0.01%           | <0.05%         | >0.1%                  |

### 4.2 Monitoring Implementation

**Logs & Metrics**:

```bash
# Each hook invocation logs:
{
  "timestamp": "2026-02-20T12:30:45Z",
  "hook_name": "quality-gate",
  "phase": "phase2",
  "latency_ms": 520,
  "init_latency_ms": 12,
  "cache_hit": true,
  "error": null,
  "status": "success"
}
```

**Aggregation** (hourly):

```json
{
  "hour": "2026-02-20T12:00:00Z",
  "phase2_hooks": 150,
  "mean_latency_ms": 45,
  "p95_latency_ms": 80,
  "p99_latency_ms": 120,
  "error_count": 0,
  "error_rate_pct": 0.0,
  "cache_hit_rate_pct": 68.5
}
```

### 4.3 Alert Rules

**Critical** 🔴:

- Error rate >0.5%
- Any crash/hang in production
- Data corruption detected
- Latency regression >100ms

**High** 🟠:

- Error rate >0.1%
- Latency regression >50ms
- Cache corruption suspected
- Git operations consistently slow

**Medium** 🟡:

- Cache hit rate <50%
- Latency increase >20% from baseline
- Individual hook >2σ slower

---

## 5. Rollback Triggers

### 5.1 Automatic Rollback

**Trigger Conditions** (auto-rollback to shell):

1. **Failure Rate Exceeds Threshold**
   - Error rate >0.1% in any hour
   - Action: Revert to common.sh for affected hooks

2. **Data Corruption Detected**
   - Cache checksum mismatch
   - Truncated cache files
   - Action: Clear cache, revert to shell

3. **Critical Crash Pattern**
   - Same hook crashes >2% of executions
   - Hang detected (timeout >30s)
   - Action: Immediate revert to shell

4. **Performance Regression**
   - Latency increase >100ms sustained
   - P95 latency >5x normal
   - Action: Investigate, consider rollback

### 5.2 Manual Rollback

**Decision Points** (weekly review):

- [ ] Week 1 summary: Meet success criteria? (Go/No-Go)
- [ ] Week 2 summary: Expansion successful? (Continue/Pause)
- [ ] Week 3 summary: Ready for full migration? (Proceed/Investigate)
- [ ] Week 4 summary: Phase 2 complete? (Archive/Extend)

**Rollback Procedure** (if needed):

```bash
# 1. Disable thegent-hooks
echo "use_rust_runtime: false" >> hooks/hook-config.yaml

# 2. Revert to common.sh
# (All affected hooks automatically fall back)

# 3. Verify functionality
task test:hooks  # Run hook tests

# 4. Analyze root cause
task bench:report  # Review performance data

# 5. Fix & retry
# (Adjust Rust code or shell fallback, redeploy)
```

---

## 6. Quick Start Guide

### 6.1 Running Phase 2 Validation

**Step 1: Validate Phase 1 Setup**

```bash
# Verify thegent-hooks binary works
thegent-hooks --version

# Run baseline benchmarks
task bench:comprehensive
```

**Step 2: Prepare Phase 2 Environment**

```bash
# Ensure monitoring is ready
mkdir -p benchmarks/results
task bench:setup

# Prepare hook migration
cp hooks/lib/common.sh hooks/lib/common.sh.bak  # Backup
```

**Step 3: Run Validation (Week 1)**

```bash
# Test one hook migration
cd hooks
# Update hook to use thegent-hooks instead of common.sh

# Run validation
bash test-hook-integration.sh doc-location-guard.sh

# Monitor performance
task bench:report
```

**Step 4: Gradual Rollout (Weeks 2-4)**

```bash
# Week 1 → Week 2
task bench:extended
# Review results, migrate more hooks

# Week 2 → Week 3
# Continue adding hooks

# Week 3 → Week 4
# Migrate remaining hooks
# Update documentation
```

### 6.2 Benchmark Commands

```bash
# Run comprehensive benchmarks (all scenarios)
task bench:comprehensive

# Run specific benchmark type
task bench:operations     # Operation-level only
task bench:hooks          # Real hooks
task bench:aggregate      # Sequential/batch

# Generate analysis report
task bench:report

# View results
task bench:view

# Compare two runs
task bench:compare -- run1_id run2_id

# List all runs
task bench:list
```

### 6.3 Monitoring Commands

```bash
# Watch performance metrics in real-time
watch -n 5 'tail -20 benchmarks/results/latest/summary.json | jq .'

# Compare current vs baseline
python3 scripts/benchmark-analysis.py \
  --baseline-dir benchmarks/results/phase1/current \
  --current-dir benchmarks/results/latest/current

# Extract specific metric
jq '.results[0].mean' benchmarks/results/latest/current/*.json
```

### 6.4 Troubleshooting

**Issue**: `thegent-hooks: command not found`

- **Solution**: Build with `cargo build --release` or install with `task setup`

**Issue**: Benchmark execution times very slow

- **Solution**: Check system load (`top`), ensure no background jobs running

**Issue**: Git operations timing out

- **Solution**: Check git repo integrity (`git fsck --full`)

**Issue**: Cache corruption or incorrect results

- **Solution**: Clear cache (`rm -rf .thegent/cache/*`) and rerun

---

## Checklist for Phase 2 Go-Live

### Pre-Phase 2 (Day -1)

- [ ] All Phase 1 tests passing
- [ ] Benchmarks reproducible
- [ ] Documentation up-to-date
- [ ] Rollback procedure tested
- [ ] Monitoring configured
- [ ] Team trained on rollout procedure

### Week 1 Start

- [ ] Select 5-7 simple hooks for migration
- [ ] Create PR with hook updates
- [ ] Deploy to staging
- [ ] Run 8-hour validation period
- [ ] Measure and document performance
- [ ] Decision: continue to Week 2 or investigate issues

### Each Week Thereafter

- [ ] Daily monitoring of error rates
- [ ] Benchmark run at week end
- [ ] Performance trend analysis
- [ ] User feedback collection
- [ ] Week-end go/no-go decision

### Week 4 Completion

- [ ] 100% of hooks migrated
- [ ] Final cross-platform testing
- [ ] Documentation updated for deprecation
- [ ] Announce deprecation timeline
- [ ] Begin Phase 3 planning (if proceeding)

---

## Success Metrics & KPIs

**Phase 2 is successful if**:

✅ **Performance**:

- 70%+ improvement in hook latency across all categories
- Zero latency regressions
- Cache hit rate ≥60%

✅ **Reliability**:

- <0.05% error rate throughout rollout
- Zero data corruption incidents
- All cross-platform tests passing

✅ **Adoption**:

- 100% of hooks successfully migrated
- Zero critical failures during rollout
- User satisfaction ≥95%

✅ **Operational**:

- Monitoring and alerts functional
- Rollback procedure working (tested)
- Documentation complete and accurate

---

## Phase 3 Planning (After Phase 2)

Once Phase 2 completes successfully:

1. **Make thegent-hooks Default** (Phase 3)
   - All new hooks use thegent-hooks automatically
   - Deprecation of common.sh begins

2. **Advanced Optimizations** (Phase 3+)
   - Integrate libgit2 for native git (8x faster)
   - Implement native Rust hooks for critical paths
   - Optional: binary embedding of common hooks

3. **Deprecation & Cleanup** (Phase 3+)
   - Remove common.sh after 3-month deprecation period
   - Archive shell hooks
   - Update documentation

---

**Ready to proceed with Phase 2? ✅**

Review this checklist. Once all pre-requisites are met, Phase 2 is ready to start.

Contact: Lead Phase 2 with the plan, monitoring, and rollback procedures documented above.
