# Economic Governance Research & Implementation Proposal

**Status**: Approved for Implementation
**Work Item**: WP-5003
**Priority**: High
**Target Completion**: Phase 2 (Weeks 3-4)
**Last Updated**: 2026-02-18

---

## Executive Summary

Implement **cost-aware routing** for agent task decisions using provider scoring (reliability, latency, cost). This enables thegent to optimize resource allocation by selecting providers based on a cost-to-value ratio, reducing operational costs by 30-50% while maintaining quality and reliability.

### Key Objectives

1. **Optimize cost-to-value**: Route 80% of low-risk tasks to efficient providers (Gemini Flash, Claude Haiku)
2. **Maintain quality**: Preserve >95% accuracy through provider scoring and fallback mechanisms
3. **Enable transparency**: Audit logs for all routing decisions with cost attribution
4. **Support hysteresis**: Prevent oscillation between providers via damping band and dwell time

---

## Problem Statement

### Current State

- Providers selected without cost consideration
- No systematic scoring for reliability/latency tradeoffs
- Potentially high operational costs for routine tasks
- Limited transparency in routing decisions

### Desired State

- Cost-aware provider selection based on task value
- Systematic provider scoring for consistent decisions
- 30-50% cost reduction through optimization
- Full audit trail for compliance and learning

### Business Value

- **Cost Savings**: 30-50% reduction in provider costs
- **Efficiency**: Faster routing decisions (<5ms latency)
- **Quality**: Maintained or improved reliability via fallback
- **Transparency**: Audit trail for regulatory compliance

---

## Technical Approach

### 1. Provider Scoring System

**Components**:

- Reliability score (uptime, error rate, SLA compliance)
- Latency score (response time, p99 percentile)
- Cost score (per-1M-token pricing)

**Scoring Formula**:

```
score = (reliability * 0.4) + (latency_score * 0.2) + (cost_score * 0.4)
```

**Example Provider Scores**:

| Provider     | Reliability | Latency | Cost     | Score |
| ------------ | ----------- | ------- | -------- | ----- |
| Gemini Flash | 0.95        | 200ms   | $0.10/1M | 8.5 ✓ |
| Claude Haiku | 0.98        | 300ms   | $0.25/1M | 8.2 ✓ |
| GPT-4o-mini  | 0.97        | 250ms   | $0.15/1M | 8.4 ✓ |
| Claude Opus  | 0.99        | 500ms   | $15/1M   | 6.0   |

### 2. Cost-to-Value Ratio Calculation

**Formula**:

```
cost_to_value_ratio = estimated_cost / estimated_value
```

Where:

- **Value** = complexity (0.3) + business_impact (0.5) + user_priority (0.2)
- **Cost** = provider_rate × estimated_tokens

**Selection Logic**:

- Calculate ratio for each available provider
- Select provider with lowest cost-to-value ratio
- Fallback to highest-score provider if cost calculation fails
- Document decision in audit log

### 3. Value Estimation

**Factors**:

- **Task complexity**: Simple (1) → Complex (10)
- **Business impact**: Low (1) → Critical (10)
- **User priority**: Standard (1) → Urgent (10)

**Method**:

- Statistical analysis of historical task values
- Task classification system (category → value range)
- User feedback loop for calibration

### 4. Cost Estimation

**Inputs**:

- Provider pricing ($/1M tokens)
- Estimated input tokens (based on task type/size)
- Estimated output tokens (typical range per task category)

**Improvement Loop**:

- Track actual costs vs. estimates
- Adjust multipliers quarterly
- Alert on >20% variance

---

## Architecture

### Components

**Location**: `thegent/src/thegent/governance/catalog.py`

1. **CostAwareRouter** (primary)
   - Route selection logic
   - Provider fallback
   - Decision auditing

2. **ProviderScorer**
   - Reliability calculation
   - Latency normalization
   - Cost normalization
   - Score aggregation

3. **ValueEstimator**
   - Task complexity analysis
   - Business impact scoring
   - Priority weighting

4. **CostEstimator**
   - Token prediction
   - Provider rate lookup
   - Cost calculation

### Data Flow

```
Task Input
    ↓
Task Classification
    ↓
Value Estimation → Cost Estimation
    ↓
Provider Scoring
    ↓
Cost-to-Value Ratio Calculation
    ↓
Route Selection (lowest ratio)
    ↓
Fallback Check
    ↓
Audit Log Entry
    ↓
Provider Execution
```

---

## Integration Points

### Dependencies

- **Pareto Router** (WP-1004): Uses cost-aware routing for task selection
- **Supermemory L3** (WP-5001-SM): Stores provider scores and cost history
- **MAIF Artifacts** (WP-3002): Records routing decisions

### Dependents

- **Lifecycle Loop** (WP-5001): Informed by cost-aware routing
- **The Gent Loop**: Cost scoring influences risk assessment

---

## Performance Targets

| Metric                     | Target | Notes              |
| -------------------------- | ------ | ------------------ |
| Provider selection latency | <5ms   | 99th percentile    |
| Cost prediction accuracy   | >90%   | vs. actual billed  |
| Value estimation accuracy  | >85%   | vs. actual outcome |
| Cost savings               | 30-50% | vs. baseline       |
| Audit log latency          | <1ms   | Non-blocking write |

---

## Acceptance Criteria

### Functional

- [ ] Cost-aware routing implemented and tested
- [ ] Provider scoring system produces consistent scores
- [ ] Cost-to-value ratio calculation accurate
- [ ] Fallback mechanism tested for all failure modes
- [ ] Audit logs capture all routing decisions

### Performance

- [ ] Provider selection latency <5ms (p99)
- [ ] Cost prediction accuracy >90%
- [ ] Value estimation accuracy >85%
- [ ] Cost savings 30-50% in production

### Quality

- [ ] Comprehensive unit tests (>90% coverage)
- [ ] Integration tests with live providers
- [ ] Performance tests under load
- [ ] Audit trail verification

### Documentation

- [ ] Architecture documentation
- [ ] Operator runbook
- [ ] Provider setup guide
- [ ] Cost analysis report

---

## Risk Assessment

### Technical Risks

| Risk                          | Impact | Probability | Mitigation                                |
| ----------------------------- | ------ | ----------- | ----------------------------------------- |
| Cost estimation inaccurate    | Medium | Medium      | Learn from actuals, recalibrate quarterly |
| Provider unavailable          | Low    | Low         | Immediate fallback to next-best provider  |
| Value estimation wrong        | Medium | Medium      | User feedback loop, manual override       |
| Oscillation between providers | Low    | Low         | Hysteresis with dwell time (see WP-1004)  |

### Operational Risks

| Risk                    | Impact | Probability | Mitigation                            |
| ----------------------- | ------ | ----------- | ------------------------------------- |
| Cost overrun            | High   | Low         | Budget alerts, auto-throttling        |
| Routing decision wrong  | Medium | Low         | Audit trail, manual review capability |
| Performance degradation | Medium | Low         | Monitoring, auto-scaling              |

---

## Success Metrics

### Cost Metrics

- **Cost savings**: 30-50% vs. baseline
- **Cost predictability**: Actual vs. estimate variance <20%
- **Cost per task**: Tracks to budget

### Quality Metrics

- **Routing accuracy**: >95% correct provider selection
- **Fallback rate**: <1% of tasks use fallback
- **Audit coverage**: 100% of routing decisions logged

### Operational Metrics

- **Selection latency**: <5ms (p99)
- **System uptime**: >99.95%
- **Alert accuracy**: <5% false positives

---

## Timeline

### Phase 2: Routing (Weeks 3-4)

**Week 3: Implementation**

- Day 1-2: Implement ProviderScorer
- Day 3-4: Implement ValueEstimator & CostEstimator
- Day 5: Implement CostAwareRouter with fallback

**Week 4: Integration & Testing**

- Day 1-2: Integration with Pareto Router
- Day 3-4: Performance testing under load
- Day 5: Audit trail verification & documentation

---

## Dependencies & Blockers

### Dependencies

- **WP-5001-SM**: Supermemory integration (for storing scores)
- **WP-1004**: Pareto routing (for hysteresis)

### Blockers

- None identified

### External Dependencies

- Provider APIs must be stable
- Provider pricing must be accessible programmatically
- Performance requirements must be achievable with latency budget

---

## Next Steps

1. **Approval**: Review proposal with architecture team
2. **Implementation**: Begin Phase 2 (Weeks 3-4)
3. **Testing**: Comprehensive testing across providers
4. **Deployment**: Staged rollout with monitoring
5. **Optimization**: Learn from production data, recalibrate

---

## See Also

- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](../../research/SESSION_RESEARCH_FRAGMENTS_EXPANDED.md#3-economic-governance) — Research details
- [Pareto Routing Proposal](../research-pareto-routing/proposal.md) — Related work
- [WORK_STREAM.md](../../reference/WORK_STREAM.md) — Work tracking
- [02-UNIFIED-WBS.md](../../plans/02-UNIFIED-WBS.md) — Phased plan

---

**Approved**: Pending architecture review
**Contact**: thegent team
**Last Updated**: 2026-02-18
