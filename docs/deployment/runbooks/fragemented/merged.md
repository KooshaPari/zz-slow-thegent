# Merged Fragmented Markdown

## Source: docs/deployment/runbooks

## Source: startup.md

# CRUN Startup Runbook

**Step-by-step operational guide for starting up CRUN system**

## Table of Contents

1. [Pre-Startup Checks](#pre-startup-checks)
2. [Startup Sequence](#startup-sequence)
3. [Health Checks](#health-checks)
4. [Verification Procedures](#verification-procedures)
5. [Common Startup Issues](#common-startup-issues)
6. [Shutdown Procedure](#shutdown-procedure)

---

## Pre-Startup Checks

Perform these checks **before** attempting to start CRUN:

### 1. System Resource Check

```bash
#!/bin/bash
# Check available resources

echo "=== System Resource Check ==="

# Check available memory
FREE_MEM=$(free -m | awk '/^Mem:/ {print $7}')
echo "Free Memory: ${FREE_MEM}MB (Minimum required: 2GB/2000MB)"

if [ $FREE_MEM -lt 2000 ]; then
    echo "⚠️  WARNING: Low memory available"
fi

# Check disk space
DISK_FREE=$(df -h . | awk 'NR==2 {print $4}')
echo "Disk Space Free: $DISK_FREE (Minimum required: 2GB)"

# Check CPU count
CPU_COUNT=$(nproc)
echo "Available CPUs: $CPU_COUNT"

# Check file descriptor limit
FD_LIMIT=$(ulimit -n)
echo "File Descriptor Limit: $FD_LIMIT (Minimum: 4096, Recommended: 10240)"

if [ $FD_LIMIT -lt 4096 ]; then
    echo "⚠️  WARNING: Increase file descriptor limit"
    echo "   Run: ulimit -n 10240"
fi
```

Run the check:

```bash
bash pre_startup_check.sh
```

**Expected Output:**

```
=== System Resource Check ===
Free Memory: 8192MB (Minimum required: 2GB/2000MB)
Disk Space Free: 50G (Minimum required: 2GB)
Available CPUs: 8
File Descriptor Limit: 1024 (Minimum: 4096, Recommended: 10240)
⚠️  WARNING: Increase file descriptor limit
   Run: ulimit -n 10240
```

### 2. File Descriptor Limit Configuration

```bash
# Increase file descriptor limit
ulimit -n 10240

# Verify change
ulimit -n
# Output should be: 10240
```

### 3. Environment Variables Check

```bash
# Verify required environment variables are set
echo "Checking environment variables..."

# Check API keys are set (for AI features)
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  WARNING: No API key found"
    echo "   Set: export OPENAI_API_KEY=sk-... OR export ANTHROPIC_API_KEY=sk-ant-..."
fi

# Check CRUN_ENVIRONMENT
echo "CRUN_ENVIRONMENT: ${CRUN_ENVIRONMENT:-not set}"

# Check workspace path
echo "CRUN_WORKSPACE_ROOT: ${CRUN_WORKSPACE_ROOT:-.}"
```

### 4. Dependency Check

```bash
# Verify Python version
echo "Python version:"
python3 --version

# Verify virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  ERROR: Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

# Check CRUN is installed
if ! command -v crun &> /dev/null; then
    echo "⚠️  ERROR: CRUN not found"
    echo "   Run: pip install -e .[all]"
    exit 1
fi

echo "✓ Virtual environment: $VIRTUAL_ENV"
echo "✓ CRUN installed: $(crun --version)"
```

### 5. Database Connectivity Check

```bash
# For PostgreSQL deployments
if [ "$CRUN_DB_HOST" != "" ]; then
    echo "Checking database connectivity..."

    psql -h $CRUN_DB_HOST -U $CRUN_DB_USERNAME -d $CRUN_DB_NAME \
        -c "SELECT 1" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "✓ Database connected"
    else
        echo "⚠️  ERROR: Cannot connect to database"
        echo "   Check credentials in .env"
        exit 1
    fi
fi
```

### 6. Service Dependencies Check

```bash
# Check if Redis is running (if configured)
if [ "$REDIS_ENABLED" == "true" ]; then
    redis-cli ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Redis running"
    else
        echo "⚠️  WARNING: Redis not running"
    fi
fi

# Check if NATS is running (if configured)
if [ "$NATS_ENABLED" == "true" ]; then
    nc -zv $NATS_HOST $NATS_PORT > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ NATS running"
    else
        echo "⚠️  WARNING: NATS not running"
    fi
fi
```

---

## Startup Sequence

Follow these steps **in order** to start CRUN:

### Step 1: Activate Virtual Environment

```bash
cd /path/to/crun
source venv/bin/activate

# Verify activation (prompt should show (venv))
# Expected: (venv) user@machine:crun$
```

### Step 2: Source Environment Variables

```bash
# Load .env file
source .env

# Verify key variables loaded
echo "Environment: $CRUN_ENVIRONMENT"
echo "Debug: $CRUN_DEBUG"
```

### Step 3: Start Database (if using external database)

```bash
# For PostgreSQL
sudo systemctl start postgresql

# For Redis
sudo systemctl start redis-server

# For NATS
nats-server -c nats.conf &
```

### Step 4: Create Required Directories

```bash
# Create log directory
mkdir -p .crun/logs
mkdir -p .crun/cache

# Verify permissions
chmod 755 .crun
chmod 755 .crun/logs
chmod 755 .crun/cache
```

### Step 5: Initialize Database (First Time Only)

```bash
# Create database schema
# There is no dedicated `crun init` command exposed in this branch.
# For PostgreSQL, initialize schema via your deployment tooling before first startup.
```

### Step 6: Start CRUN

Choose based on your deployment mode:

#### Option A: CLI Mode (Minimal)

```bash
# Run in foreground
crun --help

# Or run a background service
nohup crun gui &

# Or use systemd (production)
sudo systemctl start crun
```

#### Option B: GUI Mode

```bash
# Launch GUI (requires display)
crun gui --host 0.0.0.0 --port 8000
```

#### Option C: TUI Mode

```bash
# Launch Terminal UI
crun tui
```

#### Option D: Server Mode

```bash
# Start as HTTP server
python -m crun.api.server --host 0.0.0.0 --port 8000 --workers 4
```

### Step 7: Verify Service Started

```bash
# Check if CRUN process is running
ps aux | grep crun | grep -v grep

# Check port is listening (if using server mode)
netstat -tuln | grep 8000

# Or with ss (modern systems)
ss -tuln | grep 8000
```

---

## Health Checks

Perform these health checks after startup:

### 1. CLI Health Check

```bash
# Test CLI works
crun --version

# Expected output: CRUN 3.0.0
```

### 2. Service Health Check

```bash
# Check service status
sudo systemctl status crun

# Expected output:
# ● crun.service - CRUN Multi-Agent Orchestration
#    Loaded: loaded (/etc/systemd/system/crun.service; enabled; vendor preset: enabled)
#    Active: active (running) since...
```

### 3. HTTP Health Check

```bash
# If running as server
curl -s http://localhost:8000/health | jq .

# Expected output:
# {
#   "status": "healthy",
#   "version": "3.0.0",
#   "timestamp": "2026-02-20T12:00:00Z"
# }
```

### 4. Database Health Check

```bash
# Check database connection
python3 -c "
from crun.config import get_settings
settings = get_settings()
engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✓ Database connected')
"
```

### 5. Agent Pool Health Check

```bash
# Check CRUN process and logs
ps aux | grep crun | grep -v grep
tail -f .crun/logs/crun.log | sed -n '1,40p'

# There is currently no dedicated `crun status agents` command.
```

### 6. Log File Check

```bash
# Check logs for errors
tail -f .crun/logs/crun.log

# Look for ERROR or CRITICAL lines
grep -i error .crun/logs/crun.log
```

---

## Verification Procedures

### Procedure 1: Test Plan Generation

```bash
# Create a test project
cat > test_project.txt << 'EOF'
Build a simple CLI tool that:
- Reads a CSV file
- Filters rows based on column value
- Writes output to JSON
EOF

# Generate a plan
crun ai-plan generate-massive test_project.txt -o test_plan.md

# Verify plan created
if [ -f test_plan.md ]; then
    echo "✓ Plan generation working"
    wc -l test_plan.md  # Should be 1000+ lines
else
    echo "⚠️  Plan generation failed"
fi
```

### Procedure 2: Test Code Quality Analysis

```bash
# Test code quality on a sample directory
# Run monitor once over a sample directory
crun monitor start --workspace ./src --languages python,typescript --lint --tests

# Verify report created
echo "✓ Code quality command completed"
```

### Procedure 3: Test Execution

```bash
# Test plan execution
crun ai-plan monitor test_plan.md --workers 1

# Expected: Plan executes without errors
```

### Procedure 4: Test UI

```bash
# Test GUI launches (or TUI if no display)
crun gui --theme system &
sleep 5

# Check process is running
ps aux | grep crun | grep gui
```

---

## Common Startup Issues

### Issue 1: Virtual Environment Not Activated

**Symptom:**

```
bash: crun: command not found
```

**Solution:**

```bash
# Activate virtual environment
source venv/bin/activate

# Verify activation
which crun
# Should show: /path/to/crun/venv/bin/crun
```

---

### Issue 2: Python Version Incompatible

**Symptom:**

```
ERROR: This project requires Python 3.11+
```

**Solution:**

```bash
# Check Python version
python3 --version

# Use specific Python version
python3.12 -m venv venv
source venv/bin/activate
pip install -e ".[all]"
```

---

### Issue 3: API Key Not Found

**Symptom:**

```
Error: API key not configured for model
```

**Solution:**

```bash
# Set API key
export OPENAI_API_KEY=sk-your-key

# Or add to .env
echo "OPENAI_API_KEY=sk-your-key" >> .env
source .env

# Verify
echo $OPENAI_API_KEY
```

---

### Issue 4: Port Already in Use

**Symptom:**

```
ERROR: Address already in use 0.0.0.0:8000
```

**Solution:**

```bash
# Find process using port
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
CRUN_PORT=8001 crun gui
```

---

### Issue 5: Out of Memory

**Symptom:**

```
MemoryError: Unable to allocate memory
```

**Solution:**

```bash
# Reduce worker count
CRUN_AGENTS_MAX_WORKERS=2 crun gui

# Or increase system limits
ulimit -v unlimited
```

---

### Issue 6: Database Connection Failed

**Symptom:**

```
ERROR: Can't connect to database
```

**Solution:**

```bash
# Verify database is running
systemctl status postgresql

# Check credentials in .env
grep CRUN_DB .env

# Test connection manually
psql -h localhost -U crun -d crun -c "SELECT 1"
```

---

## Shutdown Procedure

### Graceful Shutdown

```bash
# If running in foreground (Ctrl+C)
# Press Ctrl+C to stop

# Or send SIGTERM signal
pkill -TERM -f "crun"

# Wait for graceful shutdown
sleep 5

# Verify process stopped
ps aux | grep crun | grep -v grep
```

### Systemd Shutdown

```bash
# Stop service
sudo systemctl stop crun

# Verify stopped
sudo systemctl status crun

# Check logs for shutdown messages
sudo journalctl -u crun -n 10
```

### Force Shutdown

```bash
# If process won't terminate gracefully
pkill -KILL -f "crun"

# Clean up any remaining resources
rm -f .crun/locks/*
```

### Backup Before Shutdown

```bash
# Back up current state
tar -czf crun_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    .crun/cache .crun/logs .crun/*.db
```

---

## Startup Checklist Script

```bash
#!/bin/bash
# startup_checklist.sh - Complete startup verification

set -e

echo "=== CRUN Startup Checklist ==="

# 1. Check resources
echo "1. Checking system resources..."
ulimit -n 10240

# 2. Activate venv
echo "2. Activating virtual environment..."
source venv/bin/activate

# 3. Load environment
echo "3. Loading environment..."
source .env

# 4. Create directories
echo "4. Creating required directories..."
mkdir -p .crun/{logs,cache}

# 5. Database check
echo "5. Checking database..."
if [ "$CRUN_DB_URL" != "" ]; then
    python3 -c "from sqlalchemy import create_engine; create_engine('$CRUN_DB_URL').connect()"
fi

# 6. Health check
echo "6. Running health check..."
crun --version

echo ""
echo "✓ All checks passed!"
echo "Ready to start CRUN"
echo ""
echo "To start, run:"
echo "  crun gui              # GUI mode"
echo "  crun tui              # Terminal UI"
echo "  crun --help           # CLI help"
```

Run the checklist:

```bash
bash startup_checklist.sh
```

---

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-20

---

Copied count: 1
