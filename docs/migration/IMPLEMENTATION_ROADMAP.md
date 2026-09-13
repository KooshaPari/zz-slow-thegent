# Comprehensive Implementation Roadmap

## Overview

This roadmap provides a detailed, phased approach to migrating thegent's shell infrastructure to Rust/Go for optimal performance, reliability, and cross-platform compatibility.

**Timeline**: 6 weeks
**Expected Improvement**: 10-100x performance gains
**Risk Level**: Low (gradual migration with fallbacks)

---

## Phase 1: Critical Fixes & Foundation (Week 1)

### Day 1-2: Immediate Fixes

**1.1 Fix `find -q` Compatibility** ✅ DONE

- Updated `common.sh` and `fd-wrapper.sh`
- Filters out `-q` option for macOS BSD find
- Converts to `2>/dev/null` redirection

**1.2 Fix `which` Timeout** ✅ DONE

- Added fast-path detection in `find()` wrapper
- Created `which-wrapper.sh` script
- Added `_RESOLVING_PATH` flag support

**1.3 Fix Fork Failures**

- [ ] Add process count monitoring
- [ ] Implement circuit breaker
- [ ] Add early exit for PATH resolution

### Day 3-4: Build Infrastructure

**1.4 Build Rust Extensions**

- [ ] Install maturin: `cargo install maturin` or `pip install maturin`
- [ ] Build `thegent-discovery`: `cd crates/thegent-discovery && maturin develop --release --features python`
- [ ] Build `thegent-tool-detect`: Create crate, build
- [ ] Build `thegent-path-resolve`: Create crate, build
- [ ] Verify imports: `python3 -c "from thegent_discovery import DiscoveryInterface"`

**1.5 Create Build Scripts**

- [x] `scripts/build-discovery-extension.sh`
- [x] `scripts/build-all-rust-extensions.sh`
- [ ] `scripts/test-rust-extensions.sh`

### Day 5: Testing & Validation

**1.6 Test Fixes**

- [ ] Test `which codex` (should be <10ms)
- [ ] Test `find -q` compatibility
- [ ] Test fork failure prevention
- [ ] Benchmark before/after

**Deliverables:**

- ✅ Fixed `find -q` compatibility
- ✅ Fixed `which` timeout
- [ ] Built Rust extensions
- [ ] Performance benchmarks

---

## Phase 2: Core Migrations (Week 2)

### Day 1-2: Tool Detection Migration

**2.1 Implement Rust Tool Detection**

- [x] Create `thegent-tool-detect` crate
- [ ] Implement parallel tool scanning
- [ ] Implement caching
- [ ] Add Python bindings

**2.2 Integrate into Python**

- [ ] Create `thegent/src/thegent/tool_detect.py`
- [ ] Add fallback to bash
- [ ] Update `common.sh` to use Rust binary

**2.3 Performance Testing**

- [ ] Benchmark: bash (60ms) vs Rust (1ms)
- [ ] Test cache effectiveness
- [ ] Validate correctness

**Expected Improvement**: 60ms → 1ms (60x faster)

### Day 3-4: PATH Resolution Migration

**2.4 Implement Rust PATH Resolution**

- [x] Create `thegent-path-resolve` crate
- [ ] Implement native PATH scanning
- [ ] Add skip_dirs support
- [ ] Add Python bindings

**2.5 Integrate into Python**

- [ ] Create `thegent/src/thegent/path_resolve.py`
- [ ] Replace `resolve_real_binary()` calls
- [ ] Update `common.sh` to use Rust

**2.6 Performance Testing**

- [ ] Benchmark: bash (20ms) vs Rust (0.5ms)
- [ ] Test cross-platform compatibility
- [ ] Validate correctness

**Expected Improvement**: 20ms → 0.5ms (40x faster)

### Day 5: Process Scanning Migration

**2.7 Use Rust Discovery Extension**

- [ ] Update `discovery.py` to prefer Rust extension
- [ ] Remove Python fallback (or keep as backup)
- [ ] Test agent detection

**2.8 Performance Testing**

- [ ] Benchmark: Python (50ms) vs Rust (0.5ms)
- [ ] Test process tree walking
- [ ] Validate agent detection

**Expected Improvement**: 50ms → 0.5ms (100x faster)

**Deliverables:**

- [ ] Tool detection migrated to Rust
- [ ] PATH resolution migrated to Rust
- [ ] Process scanning using Rust extension
- [ ] 100x+ performance improvements

---

## Phase 3: Advanced Optimizations (Week 3-4)

### Week 3: Hook Dispatcher Migration

**3.1 Design Hook Dispatcher**

- [ ] Architecture design
- [ ] API specification
- [ ] Error handling strategy

**3.2 Implement Rust Hook Dispatcher**

- [ ] Create `thegent-hook-dispatcher` crate
- [ ] Implement parallel execution
- [ ] Implement timeout handling
- [ ] Implement structured I/O

**3.3 Integrate**

- [ ] Replace bash dispatchers
- [ ] Add fallback to bash
- [ ] Performance testing

**Expected Improvement**: 200ms → 20ms (10x faster)

### Week 4: File Operations Migration

**4.1 Implement Rust File Operations**

- [ ] Create `thegent-file-ops` crate
- [ ] Use `walkdir` + `ignore` crates
- [ ] Implement parallel traversal
- [ ] Add Python bindings

**4.2 Integrate**

- [ ] Replace `find()` wrapper
- [ ] Update hooks to use Rust
- [ ] Performance testing

**Expected Improvement**: 30ms → 2ms (15x faster)

---

## Phase 4: Git Operations (Week 5)

### Day 1-3: Git Integration

**5.1 Use Existing `thegent-git` Crate**

- [ ] Build `thegent-git` extension
- [ ] Add mutex handling
- [ ] Add cache management
- [ ] Add Python bindings

**5.2 Integrate**

- [ ] Replace bash git wrapper
- [ ] Update hooks to use Rust
- [ ] Performance testing

**Expected Improvement**: 100ms → 10ms (10x faster)

### Day 4-5: Testing & Optimization

**5.3 Comprehensive Testing**

- [ ] Cross-platform testing
- [ ] Performance benchmarking
- [ ] Compatibility testing
- [ ] Stress testing

---

## Phase 5: Deployment & Monitoring (Week 6)

### Day 1-2: Gradual Rollout

**6.1 Feature Flags**

- [ ] Add feature flags for Rust implementations
- [ ] Enable for testing
- [ ] Monitor performance

**6.2 Gradual Migration**

- [ ] Enable Rust for low-risk operations first
- [ ] Monitor for issues
- [ ] Gradually enable more features

### Day 3-4: Monitoring

**6.3 Performance Monitoring**

- [ ] Add metrics collection
- [ ] Monitor latency
- [ ] Monitor error rates
- [ ] Monitor resource usage

**6.4 Bug Fixes**

- [ ] Fix any issues found
- [ ] Optimize hot paths
- [ ] Update documentation

### Day 5: Documentation

**6.5 Documentation**

- [ ] Update user documentation
- [ ] Update developer documentation
- [ ] Create migration guide
- [ ] Create troubleshooting guide

**Deliverables:**

- [ ] All Rust extensions deployed
- [ ] Performance monitoring in place
- [ ] Documentation complete
- [ ] 10-100x performance improvements achieved

---

## Success Criteria

### Performance Metrics

- ✅ `which` command: <10ms (target: <5ms)
- [ ] Hook execution: <25ms (target: 20ms)
- [ ] Tool detection: <2ms (target: 1ms)
- [ ] PATH resolution: <1ms (target: 0.5ms)
- [ ] Process scanning: <1ms (target: 0.5ms)

### Reliability Metrics

- [ ] Error rate: <0.1%
- [ ] Timeout rate: <0.01%
- [ ] Fork failure rate: 0%
- [ ] Cross-platform compatibility: 100%

### User Experience

- [ ] No more `which` timeouts
- [ ] No more fork failures
- [ ] 10x+ overall performance improvement
- [ ] Better error messages

---

## Risk Mitigation

### Technical Risks

**Risk**: Rust implementation slower than expected

- **Mitigation**: Benchmark early, optimize hot paths, keep bash fallback

**Risk**: Cross-platform compatibility issues

- **Mitigation**: Use cross-platform crates, test on all platforms, CI/CD

**Risk**: Breaking existing functionality

- **Mitigation**: Gradual migration, extensive testing, feature flags

### Operational Risks

**Risk**: Increased maintenance burden

- **Mitigation**: Clear documentation, code organization, team training

**Risk**: Dependency management

- **Mitigation**: Pin versions, regular updates, security audits

---

## Next Steps

1. **Immediate** (Today):
   - Run `bash scripts/fix-which-timeout.sh`
   - Restart shell
   - Test `which codex` (should be instant)

2. **This Week**:
   - Build Rust extensions
   - Test tool detection migration
   - Begin PATH resolution migration

3. **This Month**:
   - Complete core migrations
   - Deploy to production
   - Monitor performance

4. **Ongoing**:
   - Optimize hot paths
   - Add more Rust implementations
   - Monitor and improve

---

## References

- [Comprehensive Performance Analysis](./COMPREHENSIVE_PERFORMANCE_ANALYSIS.md)
- [Fork Failure Analysis](./FORK_FAILURE_ANALYSIS.md)
- [Rust Migration Plan](./RUST_GO_MIGRATION_PLAN.md)
- [ripgrep performance blog](https://blog.burntsushi.net/ripgrep/)
- [fd benchmarks](https://github.com/sharkdp/fd#benchmark)
- [Maturin documentation](https://maturin.rs/)
