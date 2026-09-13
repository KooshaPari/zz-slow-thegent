# Design Principles

## Core Philosophy

**Maximal performance, optimal design, zero over-engineering.**

---

## Principles

### 1. Performance First

- **Measure everything**: Benchmark before and after
- **Optimize hot paths**: Focus on frequently called code
- **Cache aggressively**: But keep it simple
- **Parallelize wisely**: Use rayon/tokio where it helps

### 2. Simplicity Over Cleverness

- **Prefer simple solutions**: If it works, it's good enough
- **Avoid premature optimization**: Optimize when needed, not "just in case"
- **Clear code**: Readable code is maintainable code
- **Minimal dependencies**: Only add what's necessary

### 3. Intuitive APIs

- **Self-documenting**: Function names should be clear
- **Sensible defaults**: Should work out of the box
- **Helpful errors**: Tell users what went wrong and how to fix it
- **Progressive disclosure**: Simple for common cases, powerful for advanced

### 4. Reliability

- **Fail gracefully**: Don't crash on errors
- **Circuit breakers**: Prevent cascading failures
- **Retry logic**: But with limits
- **Monitoring**: Know when things go wrong

### 5. Cross-Platform

- **Use Rust crates**: They handle platform differences
- **Test everywhere**: macOS, Linux, Windows
- **Document differences**: When platform-specific behavior exists
- **Fallback gracefully**: When platform features aren't available

---

## Code Style

### Rust

```rust
// ✅ Good: Clear, simple, efficient
pub fn detect_tools(&self) -> HashMap<String, String> {
    if let Ok(cached) = self.load_cache() {
        if self.is_cache_valid(&cached) {
            return cached.tools;
        }
    }
    self.scan_tools()
}

// ❌ Bad: Over-engineered, unclear
pub fn detect_tools_with_advanced_caching_and_fallback_strategy(
    &self,
    cache_strategy: CacheStrategy,
    fallback: FallbackStrategy,
) -> Result<HashMap<String, String>, DetectionError> {
    // 200 lines of complex logic...
}
```

### Error Handling

```rust
// ✅ Good: Simple, clear
pub fn resolve(&self, name: &str) -> Option<String> {
    which_in(name, Some(self.build_safe_path()))
        .ok()
        .map(|p| p.to_string_lossy().to_string())
}

// ❌ Bad: Over-complicated
pub fn resolve(&self, name: &str) -> Result<String, ResolveError> {
    match self.validate_name(name)? {
        ValidatedName::Standard(n) => {
            // Complex validation logic...
        }
        // ...
    }
}
```

### CLI Design

```bash
# ✅ Good: Simple, intuitive
thegent-tool-detect jq
thegent-tool-detect --format json
thegent-tool-detect --clear-cache

# ❌ Bad: Over-complicated
thegent-tool-detect --tool-name=jq --output-format=json --cache-strategy=lru --ttl=3600
```

---

## Performance Guidelines

### When to Optimize

1. **Measure first**: Don't optimize without data
2. **Hot paths**: Focus on frequently called code
3. **User-visible**: Optimize what users notice
4. **Bottlenecks**: Fix the slowest parts first

### Optimization Techniques

1. **Caching**: Cache expensive operations
2. **Parallelization**: Use rayon/tokio for I/O-bound work
3. **Zero-copy**: Minimize data copying
4. **SIMD**: For text processing (when available)
5. **Memory maps**: For large files

### When NOT to Optimize

1. **Premature optimization**: Don't optimize "just in case"
2. **One-time operations**: Don't optimize code that runs once
3. **Readability cost**: Don't sacrifice clarity for micro-optimizations
4. **Over-engineering**: Simple is better than clever

---

## API Design

### Good APIs

```rust
// Simple, clear, works out of the box
let detector = ToolDetector::new();
let tools = detector.detect_all();

// Advanced usage available but not required
let detector = ToolDetector::with_cache_file("/custom/path");
```

### Bad APIs

```rust
// Over-complicated, requires configuration for simple cases
let detector = ToolDetector::builder()
    .cache_strategy(CacheStrategy::Lru)
    .ttl(Duration::from_secs(3600))
    .parallel(true)
    .build()?;
```

---

## Testing Philosophy

### What to Test

1. **Happy paths**: Common use cases
2. **Error cases**: What happens when things go wrong
3. **Edge cases**: Boundary conditions
4. **Performance**: Benchmark critical paths

### What NOT to Test

1. **Implementation details**: Test behavior, not internals
2. **Trivial code**: Don't test getters/setters
3. **Third-party code**: Trust dependencies
4. **Over-testing**: 100% coverage isn't always worth it

---

## Documentation Standards

### Code Comments

```rust
// ✅ Good: Explains why, not what
// Use atomic write to prevent cache corruption during concurrent access
let temp_file = format!("{}.tmp", self.cache_file.to_string_lossy());

// ❌ Bad: States the obvious
// Write to temp file
let temp_file = format!("{}.tmp", self.cache_file.to_string_lossy());
```

### Documentation

- **Examples**: Show how to use, not just what it does
- **Clear**: Use simple language
- **Complete**: Cover common use cases
- **Concise**: Don't repeat yourself

---

## Summary

**Keep it simple, make it fast, make it work.**

- Performance: Measure, optimize hot paths, cache wisely
- Simplicity: Prefer simple solutions, avoid over-engineering
- Intuitive: Clear APIs, sensible defaults, helpful errors
- Reliable: Fail gracefully, monitor, retry with limits
- Cross-platform: Use Rust crates, test everywhere

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
