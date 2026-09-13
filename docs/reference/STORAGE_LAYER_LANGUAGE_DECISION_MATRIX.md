---
title: Storage Layer Language Decision Matrix
date: 2026-02-23
status: DECISION_READY
owner: architecture
tags: [quick-reference, language-selection, storage-migration]
---

# Storage Layer Language Decision Matrix (Quick Reference)

**Context:** Replace 14.5K LOC Python storage layer (PostgreSQL + Redis + Neo4j) with compiled language

## Quick Decision Tree

```
Start: Need storage layer replacement in 2026

├─ Safety > Speed?
│  └─ YES → RUST (Axum/SQLx)
│     ✅ Compile-time guarantees, zero-cost abstractions
│     ✅ Best DB driver ecosystem
│     ⚠️  Team training 3-6 weeks
│     ⏱️  Timeline: 6-10 weeks
│
└─ Speed > Safety?
   └─ YES → GO (GORM/sqlc)
      ✅ Rapid development (4-6 weeks)
      ✅ Proven at scale (2+ years production)
      ❌ GC pauses, no memory safety
      ⏱️  Timeline: 4-6 weeks
```

## Language Scorecard (2026)

| Language   |   Production Ready   | Native DB Drivers |   Performance   |    Dev Velocity    |  Ecosystem   |    Risk     | Recommendation |
| ---------- | :------------------: | :---------------: | :-------------: | :----------------: | :----------: | :---------: | :------------: |
| **Rust**   |   ✅ Yes (stable)    |   ✅ pgx (best)   |      🥇 #1      | ⚠️ 2-3 weeks setup | ✅ Excellent |   🟢 Low    |  **PRIMARY**   |
| **Go**     |   ✅ Yes (stable)    |    ✅ pgx/sqlc    |      🥈 #2      | ✅ 1-2 weeks setup | ✅ Excellent |   🟢 Low    | **SECONDARY**  |
| **Zig**    |    ⚠️ 1.0 Q2 2026    |     ⚠️ pg.zig     |  🥇 #1 (tied)   |    ⚠️ Emerging     |  ⚠️ Growing  |  🟡 Medium  | _Wait for 1.0_ |
| **Mojo**   | ❌ Pre-1.0 (H1 2026) |    ❌ FFI only    | ⚠️ FFI overhead |   ✅ Python-like   |  ❌ Minimal  |   🔴 High   | **NOT READY**  |
| **Carbon** |  ❌ MVP 0.1 Q4 2026  |      ❌ None      |   🟢 Unknown    |       ❌ N/A       |   ❌ None    | 🔴 Critical | **ELIMINATED** |

## Comparison Matrix (Storage Layer Use Case)

### PostgreSQL ORM

| Language | Driver         | Async | Type-Safe | Compile-Check |   Maturity   |
| -------- | -------------- | :---: | :-------: | :-----------: | :----------: |
| Rust     | sqlx/Diesel    |  ✅   |    ✅     |      ✅       | ✅ Excellent |
| Go       | sqlc/GORM      |  ✅   |    ⚠️     | ⚠️ GORM only  | ✅ Excellent |
| Zig      | pg.zig         |  ⚠️   |    ⚠️     |      ❌       | ⚠️ Community |
| Mojo     | psycopg3 (FFI) |  ❌   |    ❌     |      ❌       |    ❌ N/A    |
| Carbon   | None           |  ❌   |    ❌     |      ❌       |   ❌ None    |

### Redis Cache Layer

| Language | Driver         | Performance |  API Quality   |   Maturity   |
| -------- | -------------- | :---------: | :------------: | :----------: |
| Rust     | redis-rs       |   🥇 Best   |  ✅ Excellent  | ✅ Excellent |
| Go       | redis          |   🥈 Good   |  ✅ Excellent  | ✅ Excellent |
| Zig      | Community      | ⚠️ Limited  |  ⚠️ Emerging   | ⚠️ Emerging  |
| Mojo     | redis-py (FFI) |   ❌ Slow   | ✅ Python-like | ❌ FFI cost  |
| Carbon   | None           |   ❌ N/A    |     ❌ N/A     |   ❌ None    |

### Neo4j Graph Queries

| Language | Driver             | Type Support | Query Builder |   Maturity   |
| -------- | ------------------ | :----------: | :-----------: | :----------: |
| Rust     | neo4rs             |   ⚠️ Basic   |   ⚠️ Manual   |  ⚠️ Growing  |
| Go       | neo4j-driver       |   ✅ Full    |    ✅ Good    | ✅ Excellent |
| Zig      | None               |    ❌ N/A    |    ❌ N/A     |   ❌ None    |
| Mojo     | neo4j-driver (FFI) |  ✅ Via FFI  |  ✅ Via FFI   | ❌ FFI cost  |
| Carbon   | None               |    ❌ N/A    |    ❌ N/A     |   ❌ None    |

### HTTP Request Handlers

| Language | Framework  |   Async    |  Routing   | Middleware |   Maturity   |
| -------- | ---------- | :--------: | :--------: | :--------: | :----------: |
| Rust     | Axum       |     ✅     |     ✅     |     ✅     | ✅ Excellent |
| Go       | Gin/Chi    |     ✅     |     ✅     |     ✅     | ✅ Excellent |
| Zig      | None       |  ⚠️ None   |  ⚠️ None   |  ⚠️ None   |   ❌ None    |
| Mojo     | Python FFI | ❌ Via FFI | ❌ Via FFI | ❌ Via FFI |   ❌ None    |
| Carbon   | None       |   ❌ N/A   |   ❌ N/A   |   ❌ N/A   |   ❌ None    |

## Performance Expectations (Storage Layer Ops)

```
PostgreSQL query (1000 rows, serialize to JSON):
  Rust (pgx) .................. 1.2-1.5ms ✅ Best
  Go (pgx) .................... 1.5-2.0ms ✅ Comparable
  Zig (pg.zig) ................ 1.3-1.8ms ✅ Comparable
  Mojo (psycopg3 FFI) ......... 4-8ms   ❌ 3-5x slower

Redis set/get (100 ops):
  Rust (redis-rs) ............. 0.3ms   ✅ Best
  Go (redis) .................. 0.4ms   ✅ Comparable
  Zig (community) ............. 0.35ms  ✅ Comparable
  Mojo (redis-py FFI) ......... 1-2ms   ❌ 3-5x slower

Neo4j traversal (depth 5):
  Rust (neo4rs) ............... 5-8ms   ✅ Good
  Go (neo4j-driver) ........... 6-9ms   ✅ Good
  Zig (none available) ........ N/A     ❌ N/A
  Mojo (neo4j-driver FFI) ..... 12-20ms ❌ 2-3x slower
```

**GC Pause Risk:**

- Rust: None (no GC)
- Go: 1-10ms pause, ~1-5 per second under load
- Zig: None (no GC)
- Mojo: Variable (Python GC + FFI latency)
- Carbon: Unknown

## Implementation Timeline

### Rust + Axum/SQLx (Recommended)

```
Week 1-2: Team Rust ramp-up
  - Async/await fundamentals
  - Ownership + borrow checker
  - Error handling (Result/Option)
  Milestone: Simple DB query + Redis operation working

Week 3-4: PostgreSQL layer
  - SQLx connection pooling
  - Custom ORM wrapper (or Diesel)
  - Transaction handling
  Milestone: Port 30% of Python ORM code

Week 5-6: Cache + Neo4j
  - Redis operations (set/get/invalidation)
  - Neo4j query builder
  Milestone: Port 60% of Python code

Week 7-8: HTTP integration
  - Axum handlers
  - Error mapping (DB errors → HTTP responses)
  - Middleware integration
  Milestone: Port 85% of Python code

Week 9-10: Perf + Hardening
  - Load testing
  - Latency profiling
  - Canary deployment
  Milestone: Production-ready (100% feature parity)
```

### Go + GORM/sqlc (If Prioritizing Speed)

```
Week 1: Setup + sqlc codegen
  - Basic Go project structure
  - sqlc schema generation
  Milestone: Type-safe SQL queries generated

Week 2-3: PostgreSQL layer
  - GORM model definitions
  - Migrations
  Milestone: Port 50% of Python ORM

Week 4: Redis + Neo4j
  - Redis operations
  - Neo4j queries
  Milestone: Port 80% of Python code

Week 5: HTTP handlers
  - Gin/Chi router
  - Error handling
  Milestone: Port 95% of Python code

Week 6: Testing + Deployment
  - Load testing
  - Canary deployment
  Milestone: Production-ready
```

## Risk Assessment

### Rust Risks

| Risk                 | Probability | Impact | Mitigation                                   |
| -------------------- | :---------: | :----: | -------------------------------------------- |
| Steep learning curve |   Medium    | Medium | 1-week intensive training + pair programming |
| Slower initial dev   |     Low     | Medium | Accept longer week 1-3; faster later         |
| Dependency bloat     |     Low     |  Low   | Use curated ecosystem (tokio.rs recommended) |
| Compile time         |     Low     |  Low   | Incremental builds in watch mode             |

### Go Risks

| Risk                 | Probability | Impact | Mitigation                               |
| -------------------- | :---------: | :----: | ---------------------------------------- |
| GC pauses under load |     Low     | Medium | Monitor P99 latency; tune GOGC if needed |
| No memory safety     |   Medium    |  Low   | Code review rigor + testing              |
| Larger binaries      |     Low     |  Low   | Accept ~10-20MB binary size              |

### Zig Risks (if 1.0 released)

| Risk                 | Probability | Impact | Mitigation                                 |
| -------------------- | :---------: | :----: | ------------------------------------------ |
| Ecosystem immaturity |    High     |  High  | Commit to writing some custom drivers      |
| 1.0 API changes      |   Medium    | Medium | Wait 1-2 months post-1.0 for stabilization |
| Smaller community    |   Medium    |  Low   | Fallback to Rust/Go if blocked             |

### Mojo Risks

| Risk                     | Probability |    Impact    | Mitigation                 |
| ------------------------ | :---------: | :----------: | -------------------------- |
| Pre-1.0 breaking changes |  Critical   |   Critical   | Wait until 1.0 + ecosystem |
| FFI overhead             |  Critical   |     High     | Negates Mojo advantages    |
| No native DB drivers     |  Critical   |     High     | Forced Python interop      |
| **VERDICT**              |  **High**   | **Critical** | **Do not use in 2026**     |

## Decision Checklist

- [ ] **Team Experience Level**
  - [ ] Rust experience? → Rust easier
  - [ ] Go experience? → Go easier
  - [ ] Python background? → Go is shorter learning curve

- [ ] **Performance Requirements**
  - [ ] Need <1ms DB ops? → Rust recommended (pgx best)
  - [ ] <5ms acceptable? → Go acceptable
  - [ ] Predictable latency critical? → Rust (no GC)

- [ ] **Development Timeline**
  - [ ] <5 weeks needed? → Go only option
  - [ ] 6-10 weeks acceptable? → Rust recommended
  - [ ] Can wait for Zig 1.0? → Zig if 1.0 releases Q2 2026

- [ ] **Long-term Maintenance**
  - [ ] Safety > features? → Rust
  - [ ] Simplicity > safety? → Go
  - [ ] Bleeding edge acceptable? → Zig (post-1.0)

- [ ] **Ecosystem Requirements**
  - [ ] Neo4j critical? → Go (best driver)
  - [ ] PostgreSQL critical? → Rust (best driver)
  - [ ] Flexible on both? → Go for velocity

## Final Recommendation

### PRIMARY: Rust + Axum/SQLx

**When to choose:** If safety, performance, and long-term maintainability outweigh time-to-market

- 6-10 week timeline
- Best DB driver ecosystem
- Zero-cost abstractions (no GC pauses)
- Compile-time memory safety
- Team training required (3-6 weeks)

### SECONDARY: Go + GORM/sqlc

**When to choose:** If time-to-market is critical and GC overhead is acceptable

- 4-6 week timeline
- Proven at production scale
- Faster team onboarding
- Goroutines simplicity
- Trade safety for speed

### TERTIARY: Zig (Only if 1.0 lands Q1-Q2 2026)

**When to choose:** If 1.0 releases with stable APIs and you want memory safety without GC

- 8-12 week timeline
- 1.0 ecosystem still emerging
- Community-driven DB drivers
- Low-level control
- Risk: ecosystem immaturity

### NOT RECOMMENDED: Mojo

**Wait until:** 1.0 release + 6-12 month ecosystem stabilization (late 2026 → 2027)

- Pre-1.0 instability
- FFI overhead kills performance advantages
- No native DB drivers
- Ecosystem minimal

### ELIMINATED: Carbon

**Not viable for any 2026 timeline**

- MVP 0.1 end of 2026 at earliest
- 1.0 after 2028
- Zero ecosystem
- Pre-production status

---

**Decision Authority:** Architecture Review Board
**Last Updated:** 2026-02-23
**Review Cycle:** Post-decision (update if new language releases)
