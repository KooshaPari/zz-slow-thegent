# Advanced Performance Patterns & Best Practices

## Table of Contents

1. [Multi-Level Caching](#multi-level-caching)
2. [Parallel Processing Patterns](#parallel-processing-patterns)
3. [Error Handling & Resilience](#error-handling--resilience)
4. [Benchmarking Infrastructure](#benchmarking-infrastructure)
5. [Monitoring & Observability](#monitoring--observability)
6. [Cross-Platform Optimizations](#cross-platform-optimizations)
7. [Security Considerations](#security-considerations)
8. [Testing Strategies](#testing-strategies)

---

## Multi-Level Caching

### Architecture

```
┌─────────────────────────────────────────┐
│         L1: LRU Cache (Memory)          │
│  - Fastest access (<1μs)                 │
│  - Limited size (100-1000 entries)      │
│  - Hot data only                         │
└──────────────┬──────────────────────────┘
               │ Miss
               ▼
┌─────────────────────────────────────────┐
│    L2: Concurrent HashMap (Memory)      │
│  - Fast access (<10μs)                   │
│  - Larger size (10K-100K entries)        │
│  - TTL-based expiration                  │
└──────────────┬──────────────────────────┘
               │ Miss
               ▼
┌─────────────────────────────────────────┐
│      L3: Disk Cache (Persistent)        │
│  - Slower access (<1ms)                  │
│  - Unlimited size                        │
│  - Survives restarts                     │
└─────────────────────────────────────────┘
```

### Implementation

**Rust Implementation** (`thegent-cache` crate):

- L1: `LruCache` for hot data
- L2: `DashMap` for concurrent access
- L3: JSON files on disk

**Benefits**:

- 99%+ hit rate for frequently accessed data
- Sub-microsecond access for hot data
- Automatic promotion/demotion
- TTL-based expiration

**Usage**:

```rust
let cache = MultiLevelCache::new(1000, Duration::from_secs(3600))
    .with_disk_cache("/tmp/thegent-cache");

cache.insert("tool:jq", "/usr/bin/jq".to_string());
let path = cache.get(&"tool:jq".to_string());
```

---

## Parallel Processing Patterns

### Rayon for CPU-Bound Tasks

**Tool Detection**:

```rust
use rayon::prelude::*;

let tools = vec!["jq", "rg", "fd", "timeout"];
let results: Vec<_> = tools
    .par_iter()
    .map(|tool| (tool, detect_tool(tool)))
    .collect();
```

**File Operations**:

```rust
use walkdir::WalkDir;
use rayon::prelude::*;

WalkDir::new(root)
    .into_iter()
    .par_bridge()
    .filter_map(|entry| {
        // Process in parallel
    })
    .collect()
```

### Tokio for I/O-Bound Tasks

**Async Hook Execution**:

```rust
use tokio::time::{timeout, Duration};

async fn execute_hook(hook: Hook, event: Event) -> Result<HookResult> {
    timeout(Duration::from_secs(5), async {
        // Execute hook
    })
    .await?
}
```

**Concurrent Tool Detection**:

```rust
use tokio::time::Instant;

async fn detect_all_tools() -> HashMap<String, String> {
    let start = Instant::now();
    let futures: Vec<_> = TOOLS.iter()
        .map(|tool| detect_tool_async(tool))
        .collect();

    let results = futures::future::join_all(futures).await;
    let duration = start.elapsed();

    eprintln!("Detected {} tools in {:?}", results.len(), duration);
    results.into_iter().collect()
}
```

---

## Error Handling & Resilience

### Circuit Breaker Pattern

**Implementation**:

```rust
pub struct CircuitBreaker {
    failure_count: usize,
    last_failure: Option<Instant>,
    open: bool,
    threshold: usize,
    reset_timeout: Duration,
}

impl CircuitBreaker {
    pub fn can_proceed(&mut self) -> bool {
        if self.open {
            if let Some(last) = self.last_failure {
                if last.elapsed() > self.reset_timeout {
                    self.open = false;
                    self.failure_count = 0;
                    return true;
                }
            }
            return false;
        }
        true
    }

    pub fn record_success(&mut self) {
        self.failure_count = 0;
    }

    pub fn record_failure(&mut self) {
        self.failure_count += 1;
        self.last_failure = Some(Instant::now());
        if self.failure_count >= self.threshold {
            self.open = true;
        }
    }
}
```

### Retry with Exponential Backoff

```rust
use tokio::time::{sleep, Duration};

async fn retry_with_backoff<F, T, E>(
    mut f: F,
    max_retries: usize,
) -> Result<T, E>
where
    F: FnMut() -> Result<T, E>,
{
    let mut delay = Duration::from_millis(100);

    for attempt in 0..max_retries {
        match f() {
            Ok(result) => return Ok(result),
            Err(e) if attempt < max_retries - 1 => {
                sleep(delay).await;
                delay *= 2; // Exponential backoff
            }
            Err(e) => return Err(e),
        }
    }

    unreachable!()
}
```

### Graceful Degradation

```rust
pub enum FallbackStrategy {
    /// Use cached value if available
    UseCache,
    /// Use slower but reliable method
    UseSlowPath,
    /// Return default value
    UseDefault,
    /// Fail fast
    FailFast,
}

pub fn resolve_tool_with_fallback(
    name: &str,
    strategy: FallbackStrategy,
) -> Option<String> {
    // Try fast path first
    match fast_resolve(name) {
        Ok(path) => return Some(path),
        Err(_) => match strategy {
            FallbackStrategy::UseCache => {
                if let Some(cached) = cache.get(name) {
                    return Some(cached);
                }
            }
            FallbackStrategy::UseSlowPath => {
                return slow_resolve(name).ok();
            }
            FallbackStrategy::UseDefault => {
                return Some(default_path(name));
            }
            FallbackStrategy::FailFast => return None,
        },
    }
    None
}
```

---

## Benchmarking Infrastructure

### Criterion.rs Integration

**Setup** (`Cargo.toml`):

```toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "tool_detection"
harness = false
```

**Benchmark** (`benches/tool_detection.rs`):

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use thegent_tool_detect::ToolDetector;

fn bench_tool_detection(c: &mut Criterion) {
    let detector = ToolDetector::new();

    c.bench_function("detect_all_tools", |b| {
        b.iter(|| {
            black_box(detector.detect_all());
        });
    });

    c.bench_function("detect_cached", |b| {
        detector.detect_all(); // Warm cache
        b.iter(|| {
            black_box(detector.detect_all());
        });
    });
}

criterion_group!(benches, bench_tool_detection);
criterion_main!(benches);
```

### Hyperfine Integration

**Script** (`scripts/benchmark.sh`):

```bash
#!/usr/bin/env bash

hyperfine \
  --warmup 3 \
  --runs 10 \
  --export-json results.json \
  'bash -c "source hooks/lib/common.sh; detect_tools_bash"' \
  'thegent-tool-detect --json'
```

### Performance Regression Detection

```rust
use std::fs;

pub fn check_performance_regression(
    current: Duration,
    baseline: Duration,
    threshold: f64,
) -> bool {
    let ratio = current.as_secs_f64() / baseline.as_secs_f64();
    if ratio > (1.0 + threshold) {
        eprintln!(
            "Performance regression detected: {:.2}x slower than baseline",
            ratio
        );
        return true;
    }
    false
}
```

---

## Monitoring & Observability

### Metrics Collection

```rust
use std::sync::atomic::{AtomicU64, Ordering};

pub struct Metrics {
    tool_detection_count: AtomicU64,
    tool_detection_duration: AtomicU64,
    cache_hits: AtomicU64,
    cache_misses: AtomicU64,
    errors: AtomicU64,
}

impl Metrics {
    pub fn record_tool_detection(&self, duration: Duration) {
        self.tool_detection_count.fetch_add(1, Ordering::Relaxed);
        self.tool_detection_duration
            .fetch_add(duration.as_micros() as u64, Ordering::Relaxed);
    }

    pub fn record_cache_hit(&self) {
        self.cache_hits.fetch_add(1, Ordering::Relaxed);
    }

    pub fn record_cache_miss(&self) {
        self.cache_misses.fetch_add(1, Ordering::Relaxed);
    }

    pub fn get_stats(&self) -> Stats {
        let hits = self.cache_hits.load(Ordering::Relaxed);
        let misses = self.cache_misses.load(Ordering::Relaxed);
        let total = hits + misses;
        let hit_rate = if total > 0 {
            hits as f64 / total as f64
        } else {
            0.0
        };

        Stats {
            tool_detection_count: self.tool_detection_count.load(Ordering::Relaxed),
            avg_tool_detection_duration: Duration::from_micros(
                self.tool_detection_duration.load(Ordering::Relaxed)
                    / self.tool_detection_count.load(Ordering::Relaxed).max(1),
            ),
            cache_hit_rate: hit_rate,
            errors: self.errors.load(Ordering::Relaxed),
        }
    }
}
```

### Structured Logging

```rust
use tracing::{info, warn, error, instrument};

#[instrument(skip(self))]
pub fn detect_tools(&self) -> HashMap<String, String> {
    let start = Instant::now();
    info!("Starting tool detection");

    match self.scan_tools() {
        Ok(tools) => {
            let duration = start.elapsed();
            info!(
                tools_count = tools.len(),
                duration_ms = duration.as_millis(),
                "Tool detection completed"
            );
            tools
        }
        Err(e) => {
            error!(error = %e, "Tool detection failed");
            HashMap::new()
        }
    }
}
```

### Health Checks

```rust
pub struct HealthChecker {
    cache: Arc<MultiLevelCache<String, String>>,
    metrics: Arc<Metrics>,
}

impl HealthChecker {
    pub fn check(&self) -> HealthStatus {
        let mut status = HealthStatus::Healthy;
        let mut issues = Vec::new();

        // Check cache health
        let cache_stats = self.cache.get_stats();
        if cache_stats.hit_rate < 0.8 {
            status = HealthStatus::Degraded;
            issues.push("Cache hit rate below 80%".to_string());
        }

        // Check error rate
        let error_rate = self.metrics.get_error_rate();
        if error_rate > 0.01 {
            status = HealthStatus::Unhealthy;
            issues.push(format!("Error rate: {:.2}%", error_rate * 100.0));
        }

        HealthStatus {
            status,
            issues,
            timestamp: SystemTime::now(),
        }
    }
}
```

---

## Cross-Platform Optimizations

### Platform-Specific Implementations

```rust
#[cfg(target_os = "macos")]
mod macos {
    pub fn resolve_binary(name: &str) -> Option<String> {
        // macOS-specific PATH resolution
        // Use /usr/bin/which or system_profiler
    }
}

#[cfg(target_os = "linux")]
mod linux {
    pub fn resolve_binary(name: &str) -> Option<String> {
        // Linux-specific PATH resolution
        // Use /usr/bin/which or readlink -f
    }
}

#[cfg(target_os = "windows")]
mod windows {
    pub fn resolve_binary(name: &str) -> Option<String> {
        // Windows-specific PATH resolution
        // Use where.exe or GetCommandLine
    }
}
```

### Conditional Compilation

```rust
#[cfg(feature = "jemalloc")]
use jemallocator::Jemalloc;

#[cfg(feature = "jemalloc")]
#[global_allocator]
static GLOBAL: Jemalloc = Jemalloc;
```

---

## Security Considerations

### Input Validation

```rust
pub fn validate_tool_name(name: &str) -> Result<(), ValidationError> {
    if name.is_empty() {
        return Err(ValidationError::Empty);
    }

    if name.len() > 255 {
        return Err(ValidationError::TooLong);
    }

    if name.contains('/') || name.contains('\\') {
        return Err(ValidationError::InvalidCharacter);
    }

    Ok(())
}
```

### Path Traversal Prevention

```rust
use std::path::{Path, PathBuf};

pub fn sanitize_path(path: &Path) -> Result<PathBuf, SecurityError> {
    let canonical = path.canonicalize()?;

    // Ensure path is within allowed directory
    let allowed = PathBuf::from("/usr/bin");
    if !canonical.starts_with(&allowed) {
        return Err(SecurityError::PathTraversal);
    }

    Ok(canonical)
}
```

### Rate Limiting

```rust
use std::collections::HashMap;
use std::time::{Duration, Instant};

pub struct RateLimiter {
    requests: HashMap<String, Vec<Instant>>,
    max_requests: usize,
    window: Duration,
}

impl RateLimiter {
    pub fn check(&mut self, key: &str) -> bool {
        let now = Instant::now();
        let window_start = now - self.window;

        let requests = self.requests
            .entry(key.to_string())
            .or_insert_with(Vec::new);

        requests.retain(|&time| time > window_start);

        if requests.len() >= self.max_requests {
            return false;
        }

        requests.push(now);
        true
    }
}
```

---

## Testing Strategies

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tool_detection() {
        let detector = ToolDetector::new();
        let tools = detector.detect_all();
        assert!(!tools.is_empty());
    }

    #[test]
    fn test_cache_expiration() {
        let cache = MultiLevelCache::new(10, Duration::from_secs(1));
        cache.insert("key".to_string(), "value".to_string());
        assert_eq!(cache.get(&"key".to_string()), Some("value".to_string()));

        std::thread::sleep(Duration::from_secs(2));
        assert_eq!(cache.get(&"key".to_string()), None);
    }
}
```

### Integration Tests

```rust
#[cfg(test)]
mod integration_tests {
    use super::*;

    #[tokio::test]
    async fn test_hook_execution() {
        let dispatcher = HookDispatcher::new();
        let event = create_test_event();
        let results = dispatcher.dispatch("pretool", event).await;
        assert!(results.is_ok());
    }
}
```

### Property-Based Tests

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_path_resolution_always_returns_valid_path(
        name in "[a-zA-Z0-9_-]{1,50}"
    ) {
        if let Some(path) = resolve_binary(&name) {
            assert!(Path::new(&path).exists());
        }
    }
}
```

### Fuzz Testing

```rust
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(name) = std::str::from_utf8(data) {
        let _ = resolve_binary(name);
    }
});
```

---

## Performance Optimization Checklist

- [ ] Use multi-level caching (L1/L2/L3)
- [ ] Implement parallel processing (Rayon/Tokio)
- [ ] Add circuit breakers for resilience
- [ ] Implement retry with exponential backoff
- [ ] Use zero-copy where possible
- [ ] Minimize allocations in hot paths
- [ ] Use SIMD for text processing
- [ ] Profile with `perf` or `flamegraph`
- [ ] Benchmark with Criterion.rs
- [ ] Monitor with metrics and logging
- [ ] Test on all target platforms
- [ ] Validate security boundaries
- [ ] Document performance characteristics

---

## References

- [Rust Performance Book](https://nnethercote.github.io/perf-book/)
- [Criterion.rs Documentation](https://docs.rs/criterion/)
- [Rayon Documentation](https://docs.rs/rayon/)
- [Tokio Documentation](https://tokio.rs/)
- [Hyperfine Documentation](https://github.com/sharkdp/hyperfine)
