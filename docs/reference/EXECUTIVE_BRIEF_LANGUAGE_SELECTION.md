---
title: Executive Brief - Storage Layer Language Selection
date: 2026-02-23
status: DECISION_READY
owner: architecture
tags: [executive-summary, language-selection, decision]
---

# Executive Brief: Storage Layer Language Selection (14.5K LOC)

**Decision:** Rust (primary) or Go (secondary). Mojo not ready. Carbon eliminated.

---

## The Ask

Replace 14.5K LOC of Python storage layer (PostgreSQL + Redis + Neo4j queries, HTTP handlers) with a compiled language. Which one?

---

## Bottom Line Recommendation

### PRIMARY: Rust + Axum/SQLx

- **Timeline:** 6-10 weeks
- **Safety:** Memory-safe by default (compile-time)
- **Performance:** C++ tier, no garbage collection pauses
- **Cost:** 3-6 weeks team training (offset by faster refactoring later)
- **Risk:** Low

### SECONDARY: Go + GORM/sqlc

- **Timeline:** 4-6 weeks (fastest option)
- **Safety:** GC pauses (1-10ms), no compile-time memory safety
- **Performance:** 2-3x slower than Rust (still fast for DB workloads)
- **Cost:** 1-2 weeks team training (simplest learning curve)
- **Risk:** Low

**Choose Rust if:** Long-term maintainability, performance predictability, safety matter more than time-to-market.

**Choose Go if:** Time-to-market < 6 weeks and GC overhead acceptable for your workload.

---

## Languages NOT Ready

### Mojo (Pre-1.0, Late 2026)

- **Problem:** 1.0 not until H1 2026; zero native database drivers; must use Python FFI for all DB operations
- **Performance Cost:** 2-4x slower than Rust/Go due to FFI overhead
- **Verdict:** Wait until 1.0 + ecosystem stabilization (late 2026)

### Carbon (Pre-MVP, 2028+)

- **Problem:** MVP 0.1 not until Dec 2026 at earliest; 1.0 not until after 2028; zero ecosystem
- **Verdict:** Eliminated. Not viable for any 2026 timeline.

### Zig (1.0 in 2026, Ecosystem Emerging)

- **Status:** 1.0 landing sometime in 2026; real production backend built in Feb 2026
- **Problem:** Ecosystem less mature than Rust/Go; fewer proven DB libraries
- **Verdict:** Viable but risky. Wait for 1.0 release + ecosystem stabilization, or commit to writing some custom drivers.

---

## Quick Comparison (Storage Layer Workload)

| Factor                |     Rust     |       Go       |      Mojo      |   Carbon    |     Zig      |
| --------------------- | :----------: | :------------: | :------------: | :---------: | :----------: |
| **Production Ready**  |      ✅      |       ✅       |       ❌       |     ❌      |      ⚠️      |
| **PostgreSQL Driver** |    🥇 pgx    |  🥈 pgx/sqlc   |     ❌ FFI     |   ❌ None   |  ⚠️ pg.zig   |
| **Redis Support**     | ✅ Excellent |  ✅ Excellent  |     ❌ FFI     |   ❌ None   |  ⚠️ Limited  |
| **Neo4j Support**     |   ✅ Good    |  ✅ Excellent  |     ❌ FFI     |   ❌ None   |   ❌ None    |
| **Performance**       | 🥇 C++ tier  | 🥈 2-3x slower |  ❌ FFI slow   | ❌ Unknown  | 🥇 C++ tier  |
| **Dev Velocity**      | ⚠️ 2-3 weeks |  ✅ 1-2 weeks  |   ✅ Python    |   ❌ N/A    | ⚠️ 2-3 weeks |
| **Maturity**          | ✅ Excellent |  ✅ Excellent  |   ❌ Minimal   |   ❌ None   |  ⚠️ Growing  |
| **Learning Curve**    |   ❌ Steep   |   ✅ Gentle    | ✅ Python-like |   ❌ N/A    | ⚠️ Moderate  |
| **Long-term Risk**    |    🟢 Low    |     🟢 Low     |    🔴 High     | 🔴 Critical |  🟡 Medium   |

---

## Decision Criteria

### If you prioritize: **Safety + Long-term Maintainability**

→ **Choose Rust**

- Compile-time memory safety
- Predictable performance (no GC pauses)
- Better refactoring confidence on large codebases
- Industry momentum (Stripe, Discord, AWS, Google)

### If you prioritize: **Time-to-Market + Simplicity**

→ **Choose Go**

- 4-6 week timeline (vs 6-10 for Rust)
- Gentler learning curve (1-2 weeks)
- Proven at massive scale (Google, Uber, Kubernetes)
- GC overhead acceptable for most web workloads

### If you prioritize: **Performance at Any Cost + Memory Efficiency**

→ **Choose Rust** (Zig in 2027+ after 1.0 ecosystem stabilizes)

- Zero GC pauses
- C++ tier performance
- Fine-grained memory control
- Risk: Zig ecosystem still emerging in 2026

---

## Risk Summary

### Rust Risks

- **Steep learning curve** — 3-6 weeks for team proficiency (medium risk, manageable)
- **Slower initial dev** — Week 1-3 slower; offsets in weeks 4-10 (low risk, expected)
- **Compile times** — Longer than Go but not prohibitive (low risk)

### Go Risks

- **GC pauses** — 1-10ms pauses under load (low risk for most workloads, acceptable tradeoff)
- **No memory safety** — Code review rigor required (manageable with discipline)

### Mojo Risks (Why Not)

- **Pre-1.0 instability** — Breaking changes expected (high risk)
- **FFI overhead** — 2-4x slower for all DB operations (critical issue for your workload)
- **Ecosystem gap** — No native drivers, must use Python (negates performance benefits)

### Carbon Risks (Why Eliminated)

- **Years from production** — MVP 0.1 in Dec 2026, 1.0 after 2028 (critical blocker)
- **Zero ecosystem** — No frameworks, drivers, or libraries (critical blocker)

### Zig Risks (Why Conditional)

- **1.0 timing uncertain** — "Sometime in 2026" is vague (medium risk)
- **Smaller ecosystem** — Fewer battle-tested libraries than Rust/Go (medium risk)
- **Async model unproven** — Different from traditional async/await (medium risk)
- **Mitigation:** Wait for 1.0 + 2-3 months post-release stabilization (late 2026)

---

## Performance Reality (14.5K LOC Storage Layer)

**Critical insight:** Your bottleneck is **database network I/O (5-50ms)**, not CPU:

```
PostgreSQL query latency:      5-20ms  (network/DB dominant)
JSON parsing overhead:          0.5-1ms  (negligible, even with Mojo)
Redis cache hit:               1-5ms   (network dominant)
Neo4j traversal:               5-20ms  (network dominant)
HTTP round-trip:               50-200ms (cumulative of above)

Result:
  Rust vs Go difference:    ~0.5-2ms (5-10% impact, unmeasurable)
  Rust vs Mojo difference: ~2-8ms   (but Mojo not production-ready)
  Rust vs Zig difference:  ~0ms     (parity on DB workloads)

BOTTOM LINE: All three (Rust/Go/Zig) are fast enough.
             Choose based on MATURITY + RISK, not raw speed.
```

**MLIR/SIMD Not a Factor:** Mojo's MLIR advantages apply to numeric/algorithmic workloads (JSON parsing: 52% faster). For DB layers, you're I/O-bound; MLIR helps nothing. FFI overhead negates any parsing gains.

---

## Timeline & Effort

### Rust + Axum/SQLx (Recommended)

```
Week 1-2:  Team Rust fundamentals (async/ownership/borrowing)
Week 3-4:  PostgreSQL ORM layer (SQLx + connection pooling)
Week 5-6:  Redis + Neo4j integration
Week 7-8:  HTTP handlers (Axum framework)
Week 9-10: Perf testing + production hardening
Total: 6-10 weeks, 40-60 person-days
```

### Go + GORM/sqlc (Faster)

```
Week 1:    Setup + sqlc code generation
Week 2-3:  PostgreSQL ORM (GORM models + migrations)
Week 4:    Redis + Neo4j integration
Week 5:    HTTP handlers (Gin or Chi)
Week 6:    Testing + production hardening
Total: 4-6 weeks, 20-30 person-days
```

---

## Team Implications

### Rust Route

- **Training cost:** $50K-100K (team ramp-up, mentoring)
- **Hiring impact:** Easier future recruiting in Rust market
- **Productivity:** Slower weeks 1-4, faster weeks 5+
- **Confidence:** Higher long-term (memory safety at compile-time)

### Go Route

- **Training cost:** $10K-20K (simpler language)
- **Hiring impact:** Neutral (Go widely known)
- **Productivity:** Steady fast throughout
- **Confidence:** Moderate (GC pauses, human discipline required)

---

## Recommendation Decision Tree

```
Need result in < 5 weeks?
  YES → Go only choice
  NO  → Continue below

Can invest 3-6 weeks in team training?
  NO  → Go (faster ramp-up)
  YES → Continue below

Safety/predictability > time-to-market?
  YES → Rust (recommended)
  NO  → Go (acceptable)

Want finest performance control?
  YES → Rust or Zig (wait for 1.0)
  NO  → Go (good enough)
```

---

## Final Call

### **PRIMARY RECOMMENDATION: Rust + Axum/SQLx**

- Safest long-term choice
- Best database driver ecosystem
- Zero GC pauses (predictable latency)
- Compile-time memory safety (fewer bugs)
- Team investment pays dividends on future refactoring

### **ACCEPTABLE ALTERNATIVE: Go + GORM/sqlc**

- Fastest time-to-market
- Proven at Google/Uber/Kubernetes scale
- Simpler learning curve
- GC pauses acceptable for most web workloads
- Choose if timeline pressure > 5 weeks

### **NOT READY: Mojo**

- Pre-1.0 instability
- FFI overhead defeats performance benefits
- No native drivers (Python interop costs)
- Re-evaluate late 2026 + 6 months ecosystem maturation

### **ELIMINATED: Carbon**

- MVP 0.1 not until Dec 2026
- 1.0 not until 2028+
- Zero ecosystem
- Not viable for any 2026 timeline

### **CONDITIONAL: Zig (Post-1.0 Late 2026)**

- 1.0 expected 2026 (timing uncertain)
- Viable but emerging ecosystem
- Consider if Rust learning curve blocking factor
- Risk: Commit to writing some custom DB drivers

---

## Implementation Checklist

- [ ] **Architecture Review:** Present Rust vs Go tradeoff to stakeholders
- [ ] **Team Decision:** Safety vs Speed — which matters more?
- [ ] **POC/Spike:** 3-5 day Rust spike (basic DB query + Redis)
- [ ] **Cost Estimate:** Rust 40-60 person-days, Go 20-30 person-days
- [ ] **Training Plan:** Rust ramp-up curriculum (3-6 weeks), Go simpler
- [ ] **Go/No-Go Decision:** Proceed with chosen language
- [ ] **Project Kickoff:** Initiate 6-10 week (Rust) or 4-6 week (Go) sprint

---

## Sources & References

- [Mojo Roadmap](https://docs.modular.com/mojo/roadmap/) — 1.0 H1 2026
- [Carbon Roadmap](https://github.com/carbon-language/carbon-lang/blob/trunk/docs/project/roadmap.md) — 0.1 Q4 2026
- [Zig Web Backend (Feb 2026)](https://lalinsky.com/2026/02/19/six-months-of-yak-shaving-a-zig-web-backend-stack.html) — Production backend
- [Rust Web Frameworks (2026)](https://aarambhdevhub.medium.com/rust-web-frameworks-in-2026-axum-vs-actix-web-rocket-vs-warp-vs-salvo-which-one-should-you-2db3792c79a2) — Axum ecosystem
- [Go ORM Comparison (2026)](https://encore.cloud/resources/go-orms) — pgx/sqlc/GORM comparison
- [Go Production Case Study (Feb 2026)](https://medium.com/@the_atomic_architect/we-ran-go-rust-postgresql-and-kubernetes-in-production-for-two-years-heres-what-actually-78d99b2b9020) — 2-year production report

---

**Prepared by:** Architecture Research
**Date:** February 23, 2026
**Status:** Decision Ready
**Next Step:** Stakeholder review + team decision (Rust or Go)
