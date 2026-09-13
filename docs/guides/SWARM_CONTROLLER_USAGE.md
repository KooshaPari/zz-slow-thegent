# Self-Healing Swarm Controller Usage Guide

## Overview

The Self-Healing Swarm Controller is a Python-based orchestration system that monitors agent health, detects issues, and automatically heals via graceful pausing, intelligent restarting, and dynamic scaling.

**Key Features:**

- **Health Monitoring**: Polls agent status every 10 seconds
- **Graceful Pause**: SIGSTOP-based pausing preserves agent state
- **Automatic Restart**: Exponential backoff with max retry limits
- **Dynamic Scaling**: Scale up/down based on queue depth and resources
- **Resource Management**: Detects CPU/memory pressure and throttles
- **Queue Management**: Prevents overload via backpressure
- **Persistent State**: All decisions logged to `.claude/swarm_controller.log`

---

## Quick Start

### 1. Installation

The controller requires Python 3.8+ and the following dependencies:

```bash
pip install psutil pyyaml
```

Or install via project requirements:

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
pip install -r requirements.txt
```

### 2. Run Monitoring Loop

Start the controller in monitor mode with auto-healing enabled:

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
python scripts/swarm_controller.py --monitor --auto-heal --config config/swarm_controller_config.yaml
```

This will:

- Poll agent status every 10 seconds
- Detect stale agents (>30s no update), SLO breaches, and errors
- Pause unhealthy agents gracefully
- Auto-restart with exponential backoff (2s, 4s, 8s, 16s)
- Scale up/down based on queue depth
- Log all decisions to `.claude/swarm_controller.log`

### 3. Check Swarm Status

In another terminal, get real-time status:

```bash
python scripts/swarm_controller.py --status
```

Output:

```json
{
  "timestamp": "2026-02-19T10:30:45.123456",
  "agents": {
    "agent-1": {
      "status": "healthy",
      "restart_count": 0,
      "cpu_percent": 45.2,
      "memory_percent": 32.1,
      "error_count": 0
    },
    "agent-2": {
      "status": "paused",
      "restart_count": 1,
      "cpu_percent": 0.0,
      "memory_percent": 0.0,
      "error_count": 2
    }
  },
  "queue": {
    "pending": 5,
    "claimed": 3,
    "completed": 12
  },
  "system": {
    "cpu_percent": 62.5,
    "memory_percent": 48.2
  }
}
```

### 4. Generate Health Report

Get a human-readable health report:

```bash
python scripts/swarm_controller.py --report
```

Output:

```
Swarm Controller Health Report - 2026-02-19T10:30:45.123456
======================================================================
Agents: 4/5 healthy
Queue: 5 pending, 3 claimed, 12 completed
System: CPU 62.5%, Memory 48.2%

Agent Details:
  agent-1: healthy (restarts: 0, errors: 0, cpu: 45.2%, mem: 32.1%)
  agent-2: paused (restarts: 1, errors: 2, cpu: 0.0%, mem: 0.0%)
  agent-3: healthy (restarts: 0, errors: 0, cpu: 51.3%, mem: 38.5%)
  agent-4: unhealthy (restarts: 1, errors: 5, cpu: 72.1%, mem: 61.2%)
  agent-5: restarting (restarts: 2, errors: 1, cpu: 0.0%, mem: 0.0%)
```

---

## Configuration

### Config File: `config/swarm_controller_config.yaml`

All behavior is controlled via YAML configuration. Key sections:

#### Health Monitoring

```yaml
config:
  health_check_interval: 10 # Check every 10 seconds
  stale_threshold: 30 # Alert if no update for 30s
  slo_time_multiplier: 1.5 # Alert if >150% of expected time
```

#### Scaling

```yaml
config:
  scale_up_queue_threshold: 5 # Scale up when pending > 5
  scale_down_queue_threshold: 2 # Scale down when pending < 2
  max_concurrent_agents: 10 # Never run >10 agents
  min_concurrent_agents: 1 # Always run >=1 agent
```

#### Resource Management

```yaml
config:
  cpu_threshold: 80.0 # Throttle if CPU >80%
  memory_threshold: 70.0 # Throttle if Memory >70%
  max_open_files_threshold: 1000 # Alert if >1000 open files
```

#### Restart Policy

```yaml
config:
  max_restart_attempts: 3 # Max 3 auto-restarts
  restart_backoff: # Exponential backoff delays
    - 2 # Attempt 1: wait 2s
    - 4 # Attempt 2: wait 4s
    - 8 # Attempt 3: wait 8s
    - 16 # Attempt 4+: wait 16s
```

#### Queue Management

```yaml
config:
  max_claimed_per_agent: 5 # Agent can claim max 5 items
  backpressure_claimed_threshold: 10 # Stop accepting work if >10 claimed
```

### Customize Configuration

Edit `config/swarm_controller_config.yaml` to adjust behavior:

```yaml
config:
  # More aggressive scaling
  scale_up_queue_threshold: 3 # Scale up sooner
  max_concurrent_agents: 20 # Allow more agents

  # Stricter resource management
  cpu_threshold: 70.0 # More sensitive
  memory_threshold: 60.0 # More sensitive

  # Faster restart backoff
  restart_backoff: [1, 2, 4, 8] # Restart sooner
```

Then restart the controller:

```bash
python scripts/swarm_controller.py --monitor --auto-heal --config config/swarm_controller_config.yaml
```

---

## Agent Management Commands

### Pause an Agent

Gracefully pause an agent (saves state, sends SIGSTOP):

```bash
python scripts/swarm_controller.py --pause-agent agent-id
```

The agent will:

1. Receive SIGSTOP signal
2. Stop executing (but retain memory state)
3. Be marked as `paused` in state
4. Can be resumed later with SIGCONT

### Resume an Agent

Resume a paused agent:

```bash
python scripts/swarm_controller.py --resume-agent agent-id
```

The agent will:

1. Receive SIGCONT signal
2. Resume execution from where it paused
3. Be marked as `healthy` in state

### Update Agent Metrics

Manually update agent metrics (useful for external integrations):

```bash
python scripts/swarm_controller.py --update-metrics agent-id task_progress=5 error_count=0
```

This updates:

- `task_progress`: Progress counter
- `error_count`: Number of errors
- `cpu_percent`: CPU usage
- `memory_percent`: Memory usage
- Any other field in `AgentMetrics`

---

## State Files

The controller maintains state in two files:

### `.claude/swarm_state.json`

JSON file containing all agent metrics. Updated after each monitoring cycle.

```json
{
  "agent-1": {
    "agent_id": "agent-1",
    "pid": 12345,
    "status": "healthy",
    "last_heartbeat": 1708358445.123,
    "last_activity": 1708358445.123,
    "task_progress": 5,
    "restart_count": 0,
    "restart_timestamps": [],
    "cpu_percent": 45.2,
    "memory_percent": 32.1,
    "open_files": 42,
    "error_count": 0,
    "slo_breaches": 0,
    "session_start_time": 1708358400.0
  }
}
```

### `.claude/swarm_controller.log`

Text log file with all controller decisions and events.

```
2026-02-19 10:30:00 [INFO] Starting swarm controller monitor
2026-02-19 10:30:10 [DEBUG] Starting monitoring cycle
2026-02-19 10:30:10 [INFO] Agent agent-1 status change: healthy -> healthy
2026-02-19 10:30:10 [WARNING] Agent agent-2 is stale (no update for 35.2s)
2026-02-19 10:30:10 [INFO] Agent agent-2 status change: healthy -> unhealthy
2026-02-19 10:30:10 [INFO] Restarting agent agent-2 (attempt 1, delay 2s)
2026-02-19 10:30:10 [DEBUG] Monitoring cycle complete
```

---

## Health Monitoring Logic

### Agent Status States

| Status       | Meaning                     | Action                             |
| ------------ | --------------------------- | ---------------------------------- |
| `healthy`    | Operating normally          | Continue monitoring                |
| `paused`     | Gracefully paused (SIGSTOP) | Can resume with SIGCONT            |
| `unhealthy`  | Detection issue detected    | Attempt restart or escalate        |
| `restarting` | In middle of restart        | Monitor during restart delay       |
| `dead`       | Failed all restart attempts | Escalate to L1 manual intervention |

### Health Checks

The controller detects unhealthy agents via:

1. **Stale Detection** (>30 sec no heartbeat)
   - Agent hasn't been heard from in N seconds
   - Indicates process crash or freeze
   - Action: Restart with backoff

2. **SLO Breach** (>150% of expected time)
   - Task taking longer than expected
   - Rough estimate: expected_time = task_progress \* 10 seconds
   - Action: Log warning, track breaches

3. **High Error Count** (>5 errors)
   - Agent has logged multiple errors
   - Action: Mark unhealthy, attempt restart

4. **Resource Pressure**
   - System CPU >80% or Memory >70%
   - Action: Pause low-priority agents

### Auto-Restart Logic

When an agent becomes unhealthy:

1. **Attempt 1**: Wait 2s, restart
2. **Attempt 2**: Wait 4s, restart
3. **Attempt 3**: Wait 8s, restart
4. **Max Exceeded**: Mark as `dead`, escalate to L1

If max retries exceeded after 3 failed restarts:

- Agent status set to `DEAD`
- Log message indicates escalation needed
- L1 team must investigate and manually restart

---

## Scaling Logic

### Scale UP

Triggered when:

- **Condition 1**: Pending queue items > 5 AND
- **Condition 2**: System resources available (CPU <60%, Memory <50%) AND
- **Condition 3**: Current agents < max (10)

**Action**: Spawn 1 new agent

**Use Case**: Work queue is growing faster than agents can process

### Scale DOWN

Triggered when:

- **Condition 1**: Pending queue items < 2 OR
- **Condition 2**: Resource pressure detected (CPU >80% or Memory >70%) AND
- **Condition 3**: Current agents > min (1)

**Action**: Pause 1 agent (gracefully with SIGSTOP)

**Use Case**: Work queue emptying or system needs resources

---

## Resource Management

### CPU Throttling

If system CPU >80%:

1. Log warning with current CPU%
2. Pause lowest-priority agent
3. Wait for resources to free up
4. Resume agent when CPU <70%

### Memory Throttling

If system memory >70%:

1. Log warning with current memory%
2. Pause lowest-priority agent
3. Wait for resources to free up
4. Resume agent when memory <60%

### Open File Limits

If agent has >1000 open files:

1. Log warning
2. Alert may indicate file descriptor leak
3. Monitor closely, may need restart

---

## Queue Management

### Backpressure

If claimed items > 10:

1. Stop accepting new work
2. Log backpressure warning
3. Wait for agents to complete claimed items
4. Resume accepting when claimed < 10

### Per-Agent Claiming

Each agent can claim max 5 items per phase:

- Prevents single agent from hoarding work
- Ensures fair distribution
- Can be configured via `max_claimed_per_agent`

---

## Integration with thegent

### Updating Agent Metrics

The controller reads/updates agent state via `.claude/swarm_state.json`. To integrate with `thegent`:

```bash
# After agent completes task
python scripts/swarm_controller.py --update-metrics agent-1 \
  task_progress=10 \
  error_count=0

# If agent has error
python scripts/swarm_controller.py --update-metrics agent-1 \
  error_count=2 \
  last_error="timeout"
```

### Publishing Status

The controller can publish status to `docs/reference/AGENTS_ACTIVE.md`:

```markdown
# AGENTS_ACTIVE

| Agent ID | Status  | PID   | Restarts | CPU % | Memory % | Errors | Last Activity       |
| -------- | ------- | ----- | -------- | ----- | -------- | ------ | ------------------- |
| agent-1  | healthy | 12345 | 0        | 45.2  | 32.1     | 0      | 2026-02-19 10:30:00 |
| agent-2  | paused  | 12346 | 1        | 0.0   | 0.0      | 2      | 2026-02-19 10:30:00 |
```

(TODO: Implement auto-publishing)

---

## Troubleshooting

### Agent Stuck in Pause State

**Symptoms**: Agent status shows `paused` but should be running

**Diagnosis**:

```bash
# Check log for pause/resume events
tail -100 .claude/swarm_controller.log | grep "agent-id"

# Check process state
ps aux | grep agent-id
# Look for "T" in STAT column (stopped process)
```

**Fix**:

```bash
# Manually resume agent
python scripts/swarm_controller.py --resume-agent agent-id

# Verify status
python scripts/swarm_controller.py --status
```

### Agent Keeps Restarting

**Symptoms**: Agent in `restarting` state, restart_count keeps incrementing

**Diagnosis**:

```bash
# Check for restart pattern in log
grep "Restarting agent agent-id" .claude/swarm_controller.log

# Check error messages
grep "agent-id" .claude/swarm_controller.log | grep ERROR
```

**Fix**:

1. Check agent logs for root cause
2. Update configuration (increase restart backoff delays)
3. Pause agent and investigate
4. Fix underlying issue
5. Resume agent

### System Under Sustained Resource Pressure

**Symptoms**: Log shows repeated "Resource pressure detected" messages

**Diagnosis**:

```bash
# Check CPU/memory trends
tail -100 .claude/swarm_controller.log | grep "Resource pressure"

# Check system resources
python scripts/swarm_controller.py --report
```

**Fix**:

1. Pause some agents manually: `--pause-agent`
2. Investigate what's using resources (top, Activity Monitor, etc.)
3. Scale down queue by pausing new work intake
4. Once freed up, resume agents

### Controller Process Dies

**Symptoms**: Controller stops logging, status checking fails

**Diagnosis**:

```bash
# Check if process still running
ps aux | grep swarm_controller

# Check last log entries
tail -50 .claude/swarm_controller.log
```

**Fix**:

1. Restart controller: `python scripts/swarm_controller.py --monitor`
2. Check for errors in logs
3. Ensure config file exists and is valid YAML

---

## Best Practices

### 1. Start with Conservative Settings

Begin with safe defaults, then tune:

```yaml
config:
  # Conservative: fewer agents, more resource headroom
  max_concurrent_agents: 5
  cpu_threshold: 70.0
  memory_threshold: 60.0
```

Monitor for a week, then adjust based on actual load.

### 2. Set Appropriate SLO Thresholds

Calibrate `slo_time_multiplier` based on your workload:

```yaml
config:
  # For CPU-bound work (tighter SLO)
  slo_time_multiplier: 1.2  # Alert at 120% of expected

  # For I/O-bound work (looser SLO)
  slo_time_multiplier: 2.0  # Alert at 200% of expected
```

### 3. Monitor the Monitor

Regularly check controller health:

```bash
# Weekly health review
python scripts/swarm_controller.py --report > /tmp/swarm_report.txt
# Review /tmp/swarm_report.txt

# Check for escalations
grep "Escalating" .claude/swarm_controller.log

# Check restart patterns
grep "Restarting agent" .claude/swarm_controller.log | wc -l
```

### 4. Use Pause Before Kill

Always prefer pausing over killing:

```yaml
config:
  graceful_pause_enabled: true # Enable SIGSTOP-based pausing
```

This preserves agent state and allows recovery.

### 5. Set Realistic Backoff

Tune restart backoff for your environment:

```yaml
config:
  # Fast restart (for development)
  restart_backoff: [1, 2, 4, 8]

  # Slow restart (for production, to avoid thundering herd)
  restart_backoff: [5, 10, 20, 30]
```

---

## Performance Tuning

### Reduce Monitoring Overhead

If controller CPU usage is high:

```yaml
config:
  # Check less frequently
  health_check_interval: 20 # was 10 seconds
```

### Reduce Memory Footprint

If controller memory usage is high:

```yaml
config:
  # Store less history
  restart_backoff: [2, 4, 8] # was [2, 4, 8, 16]
```

### Optimize Log File

Rotate logs periodically:

```bash
# Backup and rotate log every 7 days
mv .claude/swarm_controller.log .claude/swarm_controller.log.2026-02-12
gzip .claude/swarm_controller.log.2026-02-12
```

---

## API Reference

### SwarmController Class

```python
from scripts.swarm_controller import SwarmController, Config

# Load config
config = Config.from_yaml("config/swarm_controller_config.yaml")

# Create controller
controller = SwarmController(config)

# Monitor one cycle
controller.monitor_cycle()

# Get status
status = controller.get_status()

# Manage agents
controller.pause_agent("agent-id")
controller.resume_agent("agent-id")
controller.restart_agent("agent-id")

# Update metrics
controller.update_agent_metrics("agent-id", task_progress=5, error_count=0)
```

### CLI Commands

| Command                       | Purpose                        |
| ----------------------------- | ------------------------------ |
| `--monitor`                   | Run continuous monitoring loop |
| `--auto-heal`                 | Enable automatic healing       |
| `--config PATH`               | Specify config file            |
| `--status`                    | Print JSON status              |
| `--report`                    | Print health report            |
| `--pause-agent ID`            | Pause agent                    |
| `--resume-agent ID`           | Resume agent                   |
| `--update-metrics ID k=v ...` | Update metrics                 |
| `-v, --verbose`               | Enable verbose logging         |

---

## Future Enhancements

1. **Slack/Email Alerts**: Send notifications on escalation
2. **Web Dashboard**: Real-time visualization of swarm state
3. **Auto-Restart Integration**: Actually spawn new agents (currently logged)
4. **WORK_STREAM.md Publishing**: Auto-update `docs/reference/AGENTS_ACTIVE.md`
5. **Agent Group Management**: Manage agents by phase/type
6. **Distributed Swarms**: Support multiple controller instances
7. **Chaos Engineering**: Intentional failures for resilience testing

---

## Related Documents

- `config/swarm_controller_config.yaml` - Configuration reference
- `.claude/swarm_state.json` - Agent state snapshot
- `.claude/swarm_controller.log` - Detailed decision log
- `docs/reference/AGENTS_ACTIVE.md` - Active agent status (TODO: auto-publish)
