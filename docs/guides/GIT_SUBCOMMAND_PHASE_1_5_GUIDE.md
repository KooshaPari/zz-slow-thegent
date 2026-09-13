# Git Subcommand Phase 1.5 User Guide

## Quick Start

### Feature 1: Operation-Specific Cache TTLs

Use shorter TTLs for frequently-changing data, longer TTLs for stable data.

```bash
# Default behavior (15s cache for status)
thegent-hooks git status

# Custom TTL (5s cache only)
thegent-hooks git --ttl 5 status

# Very short TTL (1s) for high-churn repo
thegent-hooks git --ttl 1 status --porcelain
```

**When to use custom TTLs:**

- High-churn repos: Use 1-5 seconds
- Stable repos: Use 30-60 seconds
- CI/CD pipelines: Use 10-15 seconds
- Interactive shells: Use 30-60 seconds

### Feature 2: Lock Detection & Auto-Recovery

Detect and report stale `.git/index.lock` files automatically.

```bash
# Check if repo is locked (no execution)
thegent-hooks git --detect-lock status
# Exit 0: no lock, Exit 2: lock detected, Exit 1: error

# Auto-recovery stale locks (wait up to 30s)
thegent-hooks git commit -m "message"  # Auto-waits

# Custom lock timeout (up to 60s)
thegent-hooks git --wait-timeout 60 add file.txt

# Environment override
THEGENT_GIT_LOCK_TIMEOUT=120 thegent-hooks git push
```

**Diagnostic output:**

```
GIT-LOCK-DETECTED: .git/index.lock (age: 15.2s, stale: true)
GIT-MUTEX: Stealing stale lock (15 seconds old) from crashed process...
GIT-MUTEX: Waiting for git index.lock (timeout: 30s)...
```

### Feature 3: Agent Metadata Tracing

Tag git operations with agent information for auditing and cost tracking.

```bash
# Set metadata
export THEGENT_AGENT_ID=copilot-xyz
export SESSION_ID=session-abc123
export THEGENT_CORRELATION_ID=deploy-456

# Run any git operation
thegent-hooks git commit -m "Deploy update"
thegent-hooks git push
thegent-hooks git add file.txt

# Metadata is stored in git config
git config user.thegent_agent      # Output: copilot-xyz
git config user.thegent_session    # Output: session-abc123
git config user.thegent_correlation # Output: deploy-456
```

**Audit trail example:**

```bash
# View who made changes
git log --format="%an <%ae> - %s" -n 5
# Output: copilot-xyz <session-abc123@thegent.local> - Deploy update

# Filter commits by agent
git log --grep="user.thegent_agent" --all
```

## Common Scenarios

### Scenario 1: Multi-Agent CI/CD Pipeline

**Problem:** Multiple agents running git operations concurrently cause lock contention.

**Solution:**

```bash
# In CI/CD script for each agent
export THEGENT_AGENT_ID="agent-${CI_RUNNER_ID}"
export SESSION_ID="$(uuidgen)"
export THEGENT_CORRELATION_ID="${CI_PIPELINE_ID}"

thegent-hooks git fetch origin
thegent-hooks git checkout -b feature/${CI_COMMIT_SHA:0:8}
thegent-hooks git add .
thegent-hooks git commit -m "CI: auto-update"
thegent-hooks git push origin feature/${CI_COMMIT_SHA:0:8}
```

### Scenario 2: High-Performance Git in Tight Loops

**Problem:** Script calls `git status` hundreds of times, each causing process overhead.

**Solution:**

```bash
# Cache status for 5 seconds only
for i in {1..100}; do
  # First call: executed, cached
  # Calls 2-5s: served from cache
  # Call 6+: re-executed
  thegent-hooks git --ttl 5 status --porcelain
  sleep 0.1
done
```

### Scenario 3: Stale Lock Recovery in Automated Systems

**Problem:** Crashed git processes leave `.git/index.lock` behind, blocking other operations.

**Solution:**

```bash
#!/bin/bash
# Auto-detect and wait for lock recovery
if thegent-hooks git --detect-lock status ; then
  echo "No lock, proceeding..."
  thegent-hooks git pull
else
  echo "Lock detected, waiting for auto-recovery..."
  thegent-hooks git --wait-timeout 60 pull
fi
```

### Scenario 4: Cost Attribution and Auditing

**Problem:** Need to track which agent made which git changes for billing/auditing.

**Solution:**

```bash
# Set global aliases with metadata
cat >> ~/.gitconfig <<EOF
[alias]
    thegent = "! export THEGENT_AGENT_ID=$(whoami) && \
              export SESSION_ID=$(date +%s%N) && \
              thegent-hooks git"
EOF

# Use for all operations
git thegent status
git thegent add file.txt
git thegent commit -m "changes"

# Later: query audit log
git log --format="%an (session: %ae)" --all | sort | uniq -c
```

## Configuration

### Persistent Configuration

Create `.thegent/git-config.json`:

```json
{
  "cache_ttl_defaults": {
    "rev-parse": 5,
    "status": 15,
    "ls-files": 15,
    "log": 30,
    "diff": 30,
    "show": 30,
    "default": 60
  },
  "lock_timeout": 30,
  "stale_lock_age": 10,
  "cache_dir": "~/.git-cache"
}
```

### Environment Variables

Set in `.bashrc` or `.zshrc`:

```bash
# Cache configuration
export THEGENT_CACHE_DIR="${HOME}/.git-cache"
export GIT_CACHE_TTL=60

# Lock configuration
export THEGENT_GIT_LOCK_TIMEOUT=30

# Agent metadata (typically set per-session or per-script)
export THEGENT_AGENT_ID="$(whoami)-$(hostname)"
export SESSION_ID="$(uuidgen)"
```

## Troubleshooting

### Issue: Cache Misses Causing Slow Operations

**Symptoms:** `git status` takes >1s even with caching enabled

**Debug:**

```bash
# Enable verbose output
THEGENT_CACHE_DIR=/tmp/debug-cache \
  thegent-hooks git --ttl 60 status

# Check cache hits
ls -la /tmp/debug-cache/
```

**Solutions:**

1. Increase TTL: `--ttl 30` instead of `--ttl 5`
2. Check cache directory permissions
3. Verify `GIT_CACHE_TTL` environment variable

### Issue: Lock Timeouts (Operation Hangs)

**Symptoms:** `git add` hangs for 30 seconds then fails

**Debug:**

```bash
ls -la .git/index.lock
stat .git/index.lock | grep Modify
```

**Solutions:**

1. Increase timeout: `--wait-timeout 60`
2. Remove stale lock manually: `rm .git/index.lock`
3. Set lower timeout if lock is stuck: `--wait-timeout 5`
4. Check for running git processes: `ps aux | grep git`

### Issue: Metadata Not Showing in Git Log

**Symptoms:** Metadata variables set but not appearing in commits

**Debug:**

```bash
git config --local --list | grep thegent
```

**Solutions:**

1. Ensure variables exported: `export THEGENT_AGENT_ID=...`
2. Check git user config isn't overriding: `git config user.name`
3. Verify thegent-hooks binary is being used: `which thegent-hooks`

## Performance Tips

### Optimize for Read-Heavy Operations

```bash
# For repos where status rarely changes
export GIT_CACHE_TTL=300  # 5 minutes
thegent-hooks git status  # Very fast subsequent calls
```

### Optimize for Write-Heavy Operations

```bash
# For repos with frequent commits
export GIT_CACHE_TTL=5    # 5 seconds
thegent-hooks git status  # Refreshes often
```

### Optimize for CI/CD Pipelines

```bash
#!/bin/bash
# Fast paths with minimal lock contention
export THEGENT_GIT_LOCK_TIMEOUT=60
export GIT_CACHE_TTL=10

# Checkout might create lock, wait longer
thegent-hooks git --wait-timeout 120 checkout main

# Status is safe, use normal timeout
thegent-hooks git status

# Push is safe, normal timeout
thegent-hooks git push
```

## Advanced Usage

### Custom Cache Directory for CI

```bash
#!/bin/bash
# Each job gets isolated cache
JOB_ID=$CI_JOB_ID
CACHE_DIR="/tmp/git-cache-${JOB_ID}"
export THEGENT_CACHE_DIR="$CACHE_DIR"

thegent-hooks git status
thegent-hooks git add .

# Cleanup after job
rm -rf "$CACHE_DIR"
```

### Lock Detection with Alerting

```bash
#!/bin/bash
# Alert if lock persists
MAX_RETRIES=3
for i in {1..${MAX_RETRIES}}; do
  if thegent-hooks git --detect-lock status ; then
    echo "Repo unlocked, proceeding"
    thegent-hooks git pull
    exit 0
  fi

  echo "Lock detected, retry $i/${MAX_RETRIES}"
  sleep 5
done

# Alert after retries exhausted
echo "ERROR: Repo locked for >15 seconds" >&2
exit 1
```

### Agent Metadata with Context

```bash
#!/bin/bash
# Auto-tag commits with rich context
export THEGENT_AGENT_ID="$(whoami)@$(hostname)"
export SESSION_ID="$(date +%Y%m%d-%H%M%S)"
export THEGENT_CORRELATION_ID="$(git rev-parse --abbrev-ref HEAD)"

# Now all git operations include metadata
thegent-hooks git commit -m "Auto-update"

# Query later
git log --format="%an | %s" --all | head -20
```

## Integration with Other Tools

### With git-wrapper.sh

```bash
# Old behavior (basic caching)
git() { git_wrapper.sh "$@"; }

# Enhanced with Phase 1.5
git() {
  export THEGENT_AGENT_ID="${AGENT_ID:-$(whoami)}"
  thegent-hooks git "$@"
}
```

### With pre-commit hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit
export THEGENT_AGENT_ID="hook:pre-commit"
thegent-hooks git status --porcelain
```

### With GitHub Actions

```yaml
name: Build and Commit
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup git metadata
        run: |
          export THEGENT_AGENT_ID="github:${{ github.actor }}"
          export SESSION_ID="${{ github.run_id }}-${{ github.run_number }}"
          export THEGENT_CORRELATION_ID="${{ github.ref }}"
      - name: Build and commit
        run: |
          make build
          thegent-hooks git add .
          thegent-hooks git commit -m "build: $(date)"
          thegent-hooks git push
```

## FAQ

**Q: Can I disable caching for specific commands?**

A: Set `--ttl 0` to skip caching for that operation:

```bash
thegent-hooks git --ttl 0 status  # Always fresh
```

**Q: How do I clear the cache?**

A: Remove the cache directory:

```bash
rm -rf ~/.git-cache/
```

**Q: Does agent metadata affect git performance?**

A: No, metadata is just config values. Negligible overhead (<1ms).

**Q: Can I use different metadata for different branches?**

A: Yes, set variables before each operation:

```bash
THEGENT_CORRELATION_ID=main thegent-hooks git checkout main
THEGENT_CORRELATION_ID=feature thegent-hooks git checkout feature
```

**Q: What's the overhead of lock detection?**

A: Minimal. Detection is just a stat() call (<1ms).

## References

- **Full Reference:** `docs/reference/THEGENT_GIT_ENHANCEMENT_PHASE_1_5.md`
- **Implementation Summary:** `docs/reference/PHASE_1_5_IMPLEMENTATION_SUMMARY.md`
- **Architecture:** `docs/ARCHITECTURE_LAYERS.md`
