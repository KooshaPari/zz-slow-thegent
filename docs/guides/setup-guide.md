# CRUN Setup & Installation Guide

**Get CRUN running on your machine in 15 minutes**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Environment Configuration](#environment-configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before installing CRUN, ensure you have the following:

### System Requirements

- **Operating System:** macOS, Linux, or Windows (WSL2 recommended)
- **RAM:** Minimum 4GB (8GB+ recommended for production)
- **Disk Space:** 2GB minimum for installation and dependencies

### Required Software

| Component | Version     | Purpose                                   |
| --------- | ----------- | ----------------------------------------- |
| Python    | 3.11 - 3.13 | CRUN requires Python 3.11+                |
| pip or uv | Latest      | Package manager for Python dependencies   |
| Git       | 2.0+        | Optional, for version control integration |

### Optional Components (for full features)

| Component  | Version | Purpose                                          |
| ---------- | ------- | ------------------------------------------------ |
| NATS       | 2.10+   | For distributed agent coordination               |
| Redis      | 7.0+    | For caching and state management                 |
| PostgreSQL | 12+     | For persistent planning data (SQLite is default) |

### Check Your Python Version

```bash
python3 --version
# Expected output: Python 3.11.x, 3.12.x, or 3.13.x
```

If you don't have a compatible Python version, install it:

- **macOS:** `brew install python@3.12`
- **Ubuntu/Debian:** `apt-get install python3.12 python3.12-venv`
- **Windows:** Download from [python.org](https://www.python.org/downloads/)

---

## Installation

### Step 1: Clone or Navigate to the Project

```bash
# If you have the source code
cd /path/to/crun

# Or clone from repository (if available)
git clone <repository-url>
cd crun
```

### Step 2: Create a Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
.\venv\Scripts\activate.bat
```

### Step 3: Install CRUN

#### Basic Installation (CLI + Core Features)

```bash
pip install -e .
```

#### With All Features

```bash
pip install -e ".[all]"
```

#### Specific Features

```bash
# GUI support (PyQt6)
pip install -e ".[gui]"

# Terminal UI
pip install -e ".[tui]"

# AI features
pip install -e ".[ai]"

# Distributed coordination (NATS, Redis)
pip install -e ".[distributed]"

# Development tools
pip install -e ".[dev]"

# API/Server features
pip install -e ".[api]"
```

### Step 4: Verify Installation

```bash
# Check installation
crun --help

# You should see the CRUN CLI help with all available commands
```

---

## Environment Configuration

### Step 1: Copy Example Environment File

```bash
cp .env.example .env
```

### Step 2: Edit Configuration

Edit `.env` with your favorite editor:

```bash
nano .env  # or vim, code, etc.
```

### Step 3: Configure Required Variables

The most important variables to set:

```env
# Application settings
CRUN_ENVIRONMENT=development          # development, testing, staging, production
CRUN_DEBUG=true                        # Enable debug logging

# Agent configuration (choose one provider)
CRUN_AGENTS_AGENT_TYPE=claude          # or 'openai', 'openrouter'
CRUN_AGENTS_MAX_WORKERS=10             # Number of parallel agents
CRUN_AGENTS_EXECUTION_TIMEOUT=300      # Timeout in seconds

# API Keys (required for AI features)
# Set your OpenAI, Anthropic, or OpenRouter API key as environment variable
# export OPENAI_API_KEY=sk-...
# export ANTHROPIC_API_KEY=sk-ant-...
# export OPENROUTER_API_KEY=sk-or-...
```

### Step 4: Configure Optional Features

#### For PostgreSQL Database (Production)

```env
CRUN_DB_URL=postgresql://user:password@localhost:5432/crun
CRUN_DB_HOST=localhost
CRUN_DB_PORT=5432
CRUN_DB_NAME=crun
```

#### For Redis Caching

```env
# Redis is used for state management
# Default is local SQLite (no setup required)
```

#### For NATS Messaging

```env
# NATS is used for distributed coordination
# Default is disabled (single-machine mode)
```

### Step 5: Verify Configuration

```bash
# Source the .env file
source .env

# Verify key settings
echo $CRUN_ENVIRONMENT
echo $CRUN_AGENTS_AGENT_TYPE
```

---

## Initial Verification

Run these commands to verify your setup:

### 1. Check CLI Works

```bash
crun --version
crun --help
```

**Expected Output:**

```
Usage: crun [OPTIONS] COMMAND [ARGS]...

CRUN v3.0 - Multi-Agent Orchestration System

Options:
  --help  Show this message and exit.

Commands:
  plan          Planning and task management commands
  ai-plan       AI-assisted plan generation and monitoring
  gui           Launch graphical interface
  tui           Launch terminal UI
  monitor       Real-time monitoring dashboards
  ...
```

### 2. Test Basic Commands

```bash
# List available commands
crun ai-plan --help
crun plan --help

# Check system configuration
crun --version
```

### 3. Run Quick Test

```bash
# Create a sample project description
cat > sample_project.txt << 'EOF'
Create a simple Python CLI tool that:
- Reads CSV files
- Filters data by column value
- Exports filtered results to JSON
EOF

# Generate a plan (this requires API keys to be set)
crun ai-plan generate-massive sample_project.txt -o test_plan.md
```

**Expected Outcome:**

- A file `test_plan.md` is created with a multi-thousand line plan
- Plan includes tasks, subtasks, dependencies, and timelines

---

## Troubleshooting

### Issue: Python Version Mismatch

**Problem:** `ERROR: Python 3.9 is not compatible. Requires Python 3.11+`

**Solution:**

```bash
# Check your Python version
python3 --version

# If needed, install correct version
# macOS: brew install python@3.12
# Ubuntu: apt-get install python3.12

# Create venv with specific Python version
python3.12 -m venv venv
source venv/bin/activate
```

### Issue: Virtual Environment Not Activated

**Problem:** `command not found: crun` or `pip: not found`

**Solution:**

```bash
# Make sure virtual environment is activated
# macOS/Linux:
source venv/bin/activate

# You should see (venv) at the start of your prompt
# (venv) $ _
```

### Issue: Missing Dependencies

**Problem:** `ImportError: No module named 'pheno'`

**Solution:**

```bash
# Reinstall in editable mode
pip install -e ".[all]"

# Or install development dependencies
pip install -e ".[dev]"
```

### Issue: API Key Not Found

**Problem:** When running `crun ai-plan generate-massive`: `Error: API key required`

**Solution:**

```bash
# Set API key as environment variable
export OPENROUTER_API_KEY=or-your-key-here

# Or edit .env file with your API key
# Then reload: source .env
```

### Issue: Port Already in Use

**Problem:** When launching GUI/server: `Address already in use: 0.0.0.0:8000`

**Solution:**

```bash
# Either kill the process using the port:
lsof -ti:8000 | xargs kill -9

# Or use a different port:
CRUN_PORT=8001 crun gui
```

### Issue: Memory Issues

**Problem:** `MemoryError` or `OSError: too many open files`

**Solution:**

```bash
# Increase file descriptor limit (macOS/Linux)
ulimit -n 10240

# Or set in .env:
CRUN_RESOURCES_MIN_FD_LIMIT=4096
CRUN_RESOURCES_TARGET_FD_LIMIT=10240
```

### Issue: GUI Won't Start

**Problem:** `No display available` or GUI window doesn't appear

**Solution:**

```bash
# Use TUI instead of GUI
crun tui

# Or use CLI mode (no GUI)
crun plan --help
```

---

## Next Steps

After successful installation:

1. **Read the CLI Reference:** See [CLI Reference Guide](../api/cli-reference.md) for all available commands
2. **Try Examples:** Check the `examples/` directory for sample projects
3. **Deploy:** Follow [Deployment Guide](../deployment/deployment-overview.md) for production setup
4. **Configure Advanced Features:** See the full configuration options in `/crun/docs/CONFIGURATION.md`

---

## Getting Help

If you encounter issues:

1. **Check Logs:** `tail -f .crun/logs/crun.log`
2. **Run Diagnostics:** `CRUN_DEBUG=true crun --version` to enable verbose logging
3. **FAQ:** See [Frequently Asked Questions](../troubleshooting/faq.md)
4. **Documentation:** Review full docs in `/crun/docs/`

---

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-20
