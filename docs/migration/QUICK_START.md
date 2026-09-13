# Quick Start Guide

## 🚀 Fix Performance Issues in 5 Minutes

### Step 1: Fix `which` Timeout (30 seconds)

```bash
cd thegent
bash scripts/fix-which-timeout.sh
source ~/.zshrc  # or ~/.bashrc
```

**Verify:**

```bash
time which codex  # Should be instant (<10ms)
```

### Step 2: Build Rust Extensions (2 minutes)

```bash
bash scripts/build-all-rust-extensions.sh
```

**Verify:**

```python
python3 -c "from thegent_discovery import DiscoveryInterface; print('✅ OK')"
```

### Step 3: Test Performance (30 seconds)

```bash
# Compare before/after
hyperfine 'which codex'  # Should be <10ms
```

---

## ✅ What You Get

- ⚡ **10-100x faster** operations
- 🔒 **No more timeouts** - `which` completes instantly
- 🛡️ **No fork failures** - Process count stays low
- 🎯 **Better reliability** - Circuit breakers and retries

---

## 🐛 Troubleshooting

### `which` Still Slow?

1. **Restart shell:**

   ```bash
   exec zsh  # or exec bash
   ```

2. **Check process count:**

   ```bash
   ps aux | wc -l  # Should be <200
   ```

3. **Monitor system:**
   ```bash
   bash scripts/monitor-process-count.sh
   ```

### Build Fails?

1. **Install Rust:**

   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Install maturin:**

   ```bash
   cargo install maturin
   ```

3. **Check logs:**
   ```bash
   cat /tmp/maturin-*.log
   ```

---

## 📚 Next Steps

- **[User Guide](./USER_GUIDE.md)** - Learn how to use the new tools
- **[Performance Analysis](./COMPREHENSIVE_PERFORMANCE_ANALYSIS.md)** - Understand the improvements
- **[Migration Plan](./IMPLEMENTATION_ROADMAP.md)** - See the full roadmap

---

**That's it!** You're now running a faster, more reliable thegent. 🎉

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
