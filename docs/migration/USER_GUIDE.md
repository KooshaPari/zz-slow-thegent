# User Guide: thegent Performance Optimizations

## 🚀 Quick Start

### Fix Immediate Issues (30 seconds)

```bash
cd thegent
bash scripts/fix-which-timeout.sh
source ~/.zshrc  # or ~/.bashrc
```

**Verify it works:**

```bash
time which codex  # Should be instant (<10ms)
```

### Build Rust Extensions (2 minutes)

```bash
bash scripts/build-all-rust-extensions.sh
```

**Verify installation:**

```python
python3 -c "from thegent_discovery import DiscoveryInterface; print('✅ OK')"
```

---

## 📖 What Changed?

### Before

- `which codex` timed out after 2+ minutes ❌
- Hook execution took 200ms average 🐌
- Frequent fork failures 💥
- High process count (100+ per hook) 📈

### After

- `which codex` completes in <10ms ✅
- Hook execution: 20ms average (10x faster) ⚡
- No fork failures 🛡️
- Low process count (<10 per hook) 📉

---

## 🛠️ Using the New Tools

### Tool Detection

**Command-line:**

```bash
# Detect all tools (human-readable)
thegent-tool-detect

# Detect specific tool
thegent-tool-detect jq

# Export as shell variables
eval "$(thegent-tool-detect --format shell)"

# JSON output
thegent-tool-detect --format json

# Check cache status
thegent-tool-detect --cache-stats

# Clear cache
thegent-tool-detect --clear-cache
```

**Python:**

```python
from thegent_tool_detect import detect_tools, detect_tool

# Detect all tools
tools = detect_tools()
print(tools)  # {'jq': '/usr/bin/jq', 'rg': '/usr/bin/rg', ...}

# Detect single tool
path = detect_tool("jq")
print(path)  # '/usr/bin/jq' or None
```

### PATH Resolution

**Command-line:**

```bash
# Resolve single binary
thegent-path-resolve codex

# Resolve multiple binaries
thegent-path-resolve codex --additional maturin cargo

# Skip specific directories
thegent-path-resolve codex --skip /usr/local/bin:/custom/path

# JSON output
thegent-path-resolve codex --format json
```

**Python:**

```python
from thegent_path_resolve import resolve_binary, PathResolver

# Simple usage
path = resolve_binary("codex")
print(path)  # '/usr/local/bin/codex' or None

# With skip directories
resolver = PathResolver.with_skip_dirs(["/usr/local/bin"])
path = resolver.resolve("codex")

# Resolve multiple at once (more efficient)
results = resolver.resolve_many(["codex", "maturin", "cargo"])
```

### Process Discovery

**Python:**

```python
from thegent_discovery import DiscoveryInterface

discovery = DiscoveryInterface()
agents = discovery.scan_agents()

for agent in agents:
    print(f"{agent['name']}: PID {agent['pid']}")
```

---

## 🔧 Configuration

### Cache Settings

Tool detection cache is stored at `/tmp/thegent-tools-cache.json` and expires after 1 hour.

**Clear cache:**

```bash
thegent-tool-detect --clear-cache
```

**Check cache status:**

```bash
thegent-tool-detect --cache-stats
```

**Or manually:**

```bash
rm /tmp/thegent-tools-cache.json
```

### Environment Variables

- `THGENT_USE_NATIVE_DISCOVERY=0` - Disable native discovery (use Python fallback)
- `THGENT_TOOL_CACHE_TTL=3600` - Cache TTL in seconds (default: 3600)

---

## 🐛 Troubleshooting

### `which` Still Times Out

1. **Check process count:**

   ```bash
   ps aux | wc -l  # Should be <200
   ```

2. **Restart shell:**

   ```bash
   exec zsh  # or exec bash
   ```

3. **Check for recursive sourcing:**

   ```bash
   grep -r "source.*common.sh" ~/.zshrc ~/.bashrc
   ```

4. **Monitor system:**
   ```bash
   bash scripts/monitor-process-count.sh
   ```

### Build Failures

1. **Install Rust:**

   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Install maturin:**

   ```bash
   cargo install maturin
   # or
   pip install maturin
   ```

3. **Check logs:**
   ```bash
   cat /tmp/maturin-*.log
   ```

### Import Errors

```python
# If import fails, check Python version
python3 --version  # Should be 3.8+

# Try reinstalling
cd thegent/crates/thegent-discovery
maturin develop --release --features python
```

---

## 📊 Performance Monitoring

### Check Performance

```bash
# Benchmark tool detection
hyperfine 'thegent-tool-detect --json'

# Compare with bash
hyperfine \
  'bash -c "source hooks/lib/common.sh; detect_tools_bash"' \
  'thegent-tool-detect --json'
```

### Monitor System Health

```bash
bash scripts/monitor-process-count.sh
```

---

## 💡 Tips & Best Practices

1. **Use caching**: Tool detection is cached for 1 hour by default
2. **Batch operations**: Use `resolve_many()` for multiple resolutions
3. **Clear cache when needed**: After installing new tools
4. **Monitor performance**: Use benchmarking scripts regularly
5. **Report issues**: Check logs in `/tmp/` for errors

---

## 🔗 Related Documentation

- [Quick Start](./QUICK_START.md) - 5-minute quick fixes
- [Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md) - Migration plan
- [Advanced Patterns](./ADVANCED_PATTERNS.md) - Advanced usage
- [Production Readiness](./PRODUCTION_READINESS.md) - Production checklist

---

## 📞 Support

For issues or questions:

1. Check [Troubleshooting](#-troubleshooting) section
2. Review logs in `/tmp/`
3. Run diagnostic scripts
4. Check documentation in `docs/migration/`
