# CRUN Frequently Asked Questions (FAQ)

**Common questions from users and operators**

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Getting Started](#getting-started)
3. [Planning & Execution](#planning--execution)
4. [Performance & Scaling](#performance--scaling)
5. [Integration & APIs](#integration--apis)
6. [Troubleshooting](#troubleshooting)
7. [Security & Operations](#security--operations)

---

## Installation & Setup

### Q: What are the minimum system requirements?

**A:** CRUN requires:
- **Python:** 3.11 or higher
- **RAM:** 4GB minimum (8GB+ recommended)
- **Disk:** 2GB for installation + workspace
- **OS:** Linux, macOS, or Windows (WSL2)

For production deployments with 100+ agents, we recommend 16GB+ RAM.

---

### Q: Can I install CRUN on Windows?

**A:** Yes, on Windows 10/11:
1. **Native:** Limited support - command-line only
2. **WSL2** (Recommended): Full support
   ```bash
   # Install WSL2
   wsl --install -d Ubuntu
   # Then follow Linux installation steps
   ```
3. **Docker:** Full support via Docker Desktop

---

### Q: How do I update CRUN to a newer version?

**A:** To update:

```bash
# Activate virtual environment
source venv/bin/activate

# Update via pip
pip install --upgrade crun

# Or from source
git pull origin main
pip install -e ".[all]"
```

Check the changelog before updating for breaking changes.

---

### Q: Do I need all optional dependencies?

**A:** No, install only what you need:

```bash
# Minimal installation
pip install crun

# Or with specific features
pip install crun[gui]        # GUI support
pip install crun[tui]        # Terminal UI
pip install crun[distributed]  # Multi-machine
pip install crun[all]        # Everything
```

---

### Q: How do I set up API keys?

**A:** Set as environment variables or in `.env`:

```bash
# For OpenAI
export OPENAI_API_KEY=sk-...

# For Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# For OpenRouter
export OPENROUTER_API_KEY=sk-or-...

# Or add to .env
echo "OPENAI_API_KEY=sk-..." >> .env
source .env
```

---

## Getting Started

### Q: How do I generate my first plan?

**A:** Create a project description and generate:

```bash
# 1. Create description
cat > project.txt << 'EOF'
Build a task management app with:
- User authentication
- Real-time collaboration
- REST API
- React frontend
EOF

# 2. Generate plan
crun ai-plan generate-massive project.txt -o plan.md

# 3. View plan
less plan.md
```

The plan will contain 2000-3000 lines with tasks, subtasks, and dependencies.

---

### Q: What's the difference between CLI, TUI, and GUI?

**A:**

| Feature | CLI | TUI | GUI |
|---------|-----|-----|-----|
| **Interface** | Command-line | Terminal UI | Graphical |
| **Automation** | ✓ Script-friendly | - | - |
| **Remote** | ✓ SSH support | ✓ SSH support | ✗ Local only |
| **Performance** | Best | Good | Heaviest |
| **Learning** | Moderate | Easy | Easy |

**Which to use:**
- **CLI:** Automation, scripts, remote servers
- **TUI:** Interactive development, no GUI
- **GUI:** Visual design, learning

---

### Q: Can I use CRUN without GPU?

**A:** Yes, CRUN runs on CPU:

```bash
# Set to CPU-friendly model
crun ai-plan generate-massive project.txt \
    --model claude-3-haiku-4  # CPU-friendly
```

For best CPU performance, use smaller models:
- Claude 3 Haiku
- GPT-3.5 Turbo
- Mistral 7B

---

## Planning & Execution

### Q: How long does plan generation take?

**A:** Plan generation typically takes:

| Plan Size | Time | API Cost |
|-----------|------|----------|
| Small (500 lines) | 30s | $0.10 |
| Medium (1500 lines) | 1min | $0.50 |
| Large (3000 lines) | 2min | $1.00 |
| Massive (5000+ lines) | 3-5min | $2-3 |

Times vary by model and network. Use a higher-capacity model and larger `--max-depth`
for better quality, for example `anthropic/claude-sonnet-4` with `--max-depth 5`.

---

### Q: `--use-tot` and `--use-adapt` are not available anymore. What are the controls?

**A:**

Use the current planning controls:
- `--max-depth` to control plan complexity
- `--model` and `--fast-model` for quality/cost tradeoffs
- `--streaming/--no-streaming` for output behavior

---

### Q: Can I edit a generated plan?

**A:** Yes, multiple ways:

```bash
# Interactive editor (TUI)
crun tui

# Text editor
nano my_plan.md

# Programmatic edit
crun ai-plan edit my_plan.md
```

Edit YAML frontmatter to change metadata, edit task markdown to update descriptions.

---

### Q: How do I execute a plan?

**A:** Use the monitor command:

```bash
# Basic execution
crun ai-plan monitor my_plan.md

# Maximum parallelism
crun ai-plan monitor my_plan.md \
    --workers 20 \
    --priority critical_path

# With real-time monitoring
crun ai-plan monitor my_plan.md --follow
```

---

### Q: What's DAG execution?

**A:** DAG (Directed Acyclic Graph) execution:
- Analyzes task dependencies
- Executes independent tasks in parallel
- Respects task ordering constraints
- **Speed:** 2.75x faster on average
- **Cost:** Same (parallel work)

Execution uses CRUN's internal scheduling strategy by default.

---

### Q: Can I pause and resume execution?

**A:** No direct checkpoint resume flags are exposed in this CLI build. If you need safe retries, rerun the plan with:
`--dry-run` to validate state before re-execution.

---

### Q: How many parallel agents can I run?

**A:**

| Resources | Max Agents | Recommendation |
|-----------|------------|-----------------|
| 4GB RAM | 5 | 2 for stability |
| 8GB RAM | 20 | 10 for balance |
| 16GB RAM | 50 | 25 for speed |
| 32GB+ | 100+ | Scale as needed |

Set with:
```bash
crun ai-plan monitor plan.md --workers 20
```

---

## Performance & Scaling

### Q: Why is my plan generation slow?

**A:** Check these factors:

1. **Network latency:** ~1s baseline
2. **Model busy:** Peak times slower
3. **Plan complexity:** Larger plans take longer
4. **Planning depth/model choices:** higher depth and larger models increase runtime.

**Solutions:**
```bash
# Disable fancy features
crun ai-plan generate-massive project.txt

# Use faster model
crun ai-plan generate-massive project.txt --model claude-3-haiku

# Use OpenRouter for speed
export OPENROUTER_API_KEY=...
crun ai-plan generate-massive project.txt
```

---

### Q: How do I optimize for cost?

**A:**

1. **Use cheaper models:**
   ```bash
   --model claude-3-haiku  # Cheapest
   --model gpt-3.5-turbo   # Moderate
   ```

2. **Use default quality settings:**
   ```bash
   crun ai-plan generate-massive project.txt --max-depth 4
   ```

3. **Cache plans:**
   ```bash
   # Reuse generated plans instead of regenerating
   ```

4. **Batch execution:**
   ```bash
   # Run multiple plans separately
   crun ai-plan monitor plan1.md
   crun ai-plan monitor plan2.md
   crun ai-plan monitor plan3.md
   ```

**Typical costs:**
- Small plan: $0.10
- Medium plan: $0.50
- Large plan: $1-2

---

### Q: How do I monitor resource usage?

**A:** Check during execution:

```bash
# Monitor in separate terminal
watch -n 1 'ps aux | grep crun'

# Or use system tools
top -p $(pgrep -f "crun")

# Memory usage
ps -o pid,vsz,rss,comm $(pgrep -f "crun")

# File descriptors
lsof -p $(pgrep -f "crun") | wc -l
```

---

### Q: Can I scale to 1000+ agents?

**A:** Yes, requires distributed setup:

```bash
# 1. Use PostgreSQL for state
CRUN_DB_URL=postgresql://...

# 2. Use Redis for caching
REDIS_URL=redis://...

# 3. Use NATS for messaging
NATS_URL=nats://...

# 4. Run on Kubernetes
# Deploy using Helm charts or Docker

# 5. Scale workers
CRUN_AGENTS_MAX_WORKERS=1000
```

See [Deployment Guide](../deployment/deployment-overview.md) for details.

---

## Integration & APIs

### Q: Can I use CRUN programmatically (not CLI)?

**A:** Yes, via Python API:

```python
from crun.planning import generate_plan
from crun.execution import execute_plan

# Generate plan
plan = generate_plan(description="Build a web app", use_tot=True, max_tokens=4000)

# Execute plan
results = execute_plan(plan, max_parallel=10)
```

See `/crun/docs/api/python-api.md` for full API.

---

### Q: How do I integrate with CI/CD?

**A:** Use in pipelines:

```yaml
# GitHub Actions example
- name: Generate project plan
  run: |
    source venv/bin/activate
    crun ai-plan generate-massive spec.txt -o plan.md
    crun ai-plan monitor plan.md --workers 2

- name: Code quality check
  run: |
    crun monitor start --workspace ./src --languages python,typescript --lint --tests
```

---

### Q: Can I use CRUN as a webhook?

**A:** Yes, via API server:

```bash
# Start API server
python -m crun.api.server --port 8000

# Call endpoint
curl -X POST http://localhost:8000/api/plans \
  -H "Content-Type: application/json" \
  -d '{"description": "Build an app"}'
```

---

### Q: Does CRUN support custom agents?

**A:** Yes, implement custom agent:

```python
from crun.agents import BaseAgent


class CustomAgent(BaseAgent):
    async def execute(self, task):
        # Your implementation
        return result
```

Register in configuration, then use in plans.

---

## Troubleshooting

### Q: Why do I get "too many open files" error?

**A:** Increase file descriptor limit:

```bash
# Check current limit
ulimit -n

# Increase limit (bash session)
ulimit -n 10240

# Persist (macOS)
echo "ulimit -n 10240" >> ~/.bash_profile

# Persist (Linux systemd)
# Edit /etc/security/limits.conf:
# *   soft  nofile  10240
# *   hard  nofile  65536
```

---

### Q: My plan keeps timing out

**A:** Increase timeout:

```bash
# CLI timeout
timeout 3600 crun ai-plan monitor plan.md
```

---

### Q: Why aren't agents working?

**A:** Check:

```bash
# 1. Are agents initialized?
# No dedicated `crun status` command is exposed in the current CLI build.
# Check startup logs for agent initialization failures.

# 2. Is API key set?
echo $OPENAI_API_KEY

# 3. Check logs
tail -f .crun/logs/crun.log

# 4. Test manually
python -c "from crun.agents import Agent; a = Agent(); print(a.status())"
```

---

### Q: Can I run CRUN in offline mode?

**A:** Limited support:
- ✓ Can execute previously generated plans
- ✗ Cannot generate new plans (requires API)
- ✗ Cannot use AI features

```bash
# Execute existing plan (offline OK)
crun ai-plan monitor plan.md

# Generate plan (requires internet + API)
crun ai-plan generate-massive spec.txt  # Needs connection
```

---

## Security & Operations

### Q: How do I secure API keys?

**A:** Best practices:

```bash
# 1. Use environment variables (recommended)
export OPENAI_API_KEY=sk-...

# 2. Use .env file (not in git)
# .env (gitignored)
OPENAI_API_KEY=sk-...

# 3. Use secret management
# AWS Secrets Manager, HashiCorp Vault, etc.

# 4. Never commit keys to git
# Add to .gitignore:
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

---

### Q: Is my data stored locally?

**A:**

- **By default:** Yes, SQLite database in `.crun/` directory
- **With PostgreSQL:** Stored in remote database
- **Logs:** Stored in `.crun/logs/`
- **Cache:** Stored in `.crun/cache/`

Data never leaves your system unless you configure remote database.

---

### Q: Can I backup my data?

**A:** Yes:

```bash
# Backup everything
tar -czf crun_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    .crun/ .env

# For PostgreSQL
pg_dump crun > backup.sql

# Restore
psql crun < backup.sql
```

Schedule regular backups for production.

---

### Q: How often should I update CRUN?

**A:** Recommendations:

- **Security patches:** Immediately
- **Minor updates:** Weekly/monthly
- **Major versions:** After testing

Check release notes:
```bash
crun --version  # Current version
git log --oneline  # Recent changes
```

---

### Q: Can I run multiple CRUN instances?

**A:** Yes, with precautions:

```bash
# Multiple instances, same machine
CRUN_WORKSPACE_ROOT=/workspace1 crun gui --port 8000
CRUN_WORKSPACE_ROOT=/workspace2 crun gui --port 8001

# Multiple machines (distributed)
# Use shared PostgreSQL + Redis
# See deployment guide for setup
```

---

## Still Have Questions?

1. **Check Logs:** `tail -f .crun/logs/crun.log`
2. **See Docs:** `/crun/docs/` directory
3. **Run Examples:** `/crun/examples/`
4. **Check Tests:** `/crun/tests/`

---

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-20
