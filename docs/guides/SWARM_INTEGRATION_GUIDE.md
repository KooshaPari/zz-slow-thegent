# Swarm Controller Integration Guide

Guide for integrating the Self-Healing Swarm Controller with your agent execution system (thegent, Prefect, etc.).

## Overview

The Swarm Controller provides a standardized interface for:
- Monitoring agent health and metrics
- Detecting and auto-healing failures
- Dynamic scaling based on queue depth
- Resource-aware throttling

Integration points:
1. **Agent Metrics API**: Update agent status via CLI
2. **Work Stream**: Read `docs/reference/WORK_STREAM.md` for queue depth
3. **State File**: Read `.claude/swarm_state.json` for agent status
4. **Logging**: Read `.claude/swarm_controller.log` for decisions

## Integration Pattern

### 1. Agent Lifecycle Integration

When spawning an agent:

```bash
# After agent starts
export AGENT_ID="agent-1"
export AGENT_PID=$(pgrep -f "your-agent-process")

# Register with swarm controller
python3 scripts/swarm_controller.py --update-metrics $AGENT_ID \
  pid=$AGENT_PID \
  task_progress=0 \
  error_count=0
```

When agent completes work:

```bash
# Record completion
python3 scripts/swarm_controller.py --update-metrics $AGENT_ID \
  task_progress=10 \
  error_count=0
```

If agent encounters error:

```bash
# Record error
python3 scripts/swarm_controller.py --update-metrics $AGENT_ID \
  error_count=$(cat /tmp/agent-errors.count) \
  last_error="timeout on task"
```

### 2. Work Stream Integration

The controller reads `docs/reference/WORK_STREAM.md` to:
- Get queue depth (pending items)
- Apply backpressure (if claimed > 10)
- Scale agents based on demand

**Your system should:**
1. Update `docs/reference/WORK_STREAM.md` with work items
2. Mark items as `CLAIMED` when agent takes them
3. Mark items as `COMPLETED` when finished

**Example work stream format:**
```markdown
# WORK_STREAM

| ID | Status | Agent | Description |
|----|--------|-------|-------------|
| WI-001 | PENDING | - | Task A |
| WI-002 | CLAIMED | agent-1 | Task B |
| WI-003 | COMPLETED | agent-1 | Task C |
```

### 3. Metrics Update Pattern

Recommended pattern for continuous metrics updates:

```python
import json
import subprocess
from pathlib import Path


class AgentMetricsReporter:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.metrics = {
            "task_progress": 0,
            "error_count": 0,
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
        }

    def update(self, **kwargs):
        """Update metrics and report to controller."""
        self.metrics.update(kwargs)
        self._report()

    def _report(self):
        """Report metrics to swarm controller."""
        args = ["python3", "scripts/swarm_controller.py", "--update-metrics", self.agent_id]
        for key, value in self.metrics.items():
            args.append(f"{key}={value}")
        subprocess.run(args, check=False)


# Usage
reporter = AgentMetricsReporter("agent-1")
reporter.update(task_progress=5, error_count=0)
reporter.update(cpu_percent=45.2)
```

### 4. Resource Awareness

Before launching new agents:

```bash
# Check system resources
PRESSURE=$(python3 scripts/swarm_controller.py --status | \
  python3 -c "import json, sys; s=json.load(sys.stdin); print(s['system']['cpu_percent'])")

if (( $(echo "$PRESSURE > 80" | bc -l) )); then
  echo "System under pressure, don't launch new agent"
  exit 1
fi

# Launch agent
python3 -m your_agent_system run
```

### 5. Queue Depth Monitoring

Before accepting new work:

```bash
# Check if backpressure is active
BACKPRESSURE=$(python3 scripts/swarm_controller.py --status | \
  python3 -c "import json, sys; s=json.load(sys.stdin); \
  print(s['queue']['claimed'] > 10)")

if [[ "$BACKPRESSURE" == "True" ]]; then
  echo "Queue backpressure active, stop accepting work"
  exit 1
fi

# Accept new work item
accept_work_item
```

## Integration Examples

### Example 1: thegent Integration

```python
# thegent-integration.py
import subprocess
import json
from pathlib import Path


class ThegentSwarmBridge:
    def __init__(self):
        self.controller_cmd = "python3 scripts/swarm_controller.py"

    def spawn_agent(self, agent_id: str, task: str) -> int:
        """Spawn agent and register with controller."""
        # Spawn agent (your implementation)
        proc = subprocess.Popen(
            ["thegent", "free", task],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Register with controller
        subprocess.run(
            [self.controller_cmd, "--update-metrics", agent_id, f"pid={proc.pid}", "task_progress=0", "error_count=0"]
        )

        return proc.pid

    def report_progress(self, agent_id: str, progress: int, errors: int):
        """Report agent progress."""
        subprocess.run(
            [self.controller_cmd, "--update-metrics", agent_id, f"task_progress={progress}", f"error_count={errors}"]
        )

    def can_spawn_agent(self) -> bool:
        """Check if system can spawn new agent."""
        result = subprocess.run([self.controller_cmd, "--status"], capture_output=True, text=True)

        if result.returncode != 0:
            return True  # Assume OK if controller not ready

        status = json.loads(result.stdout)
        cpu = status["system"]["cpu_percent"]
        memory = status["system"]["memory_percent"]

        # Don't spawn if resources constrained
        return cpu < 80 and memory < 70
```

### Example 2: Prefect Integration

```python
# prefect_swarm_integration.py
from prefect import task, flow
from prefect.engine import get_state
import subprocess


class PrefectSwarmReporter:
    @staticmethod
    def report_task_start(agent_id: str, task_name: str):
        subprocess.run(["python3", "scripts/swarm_controller.py", "--update-metrics", agent_id, "task_progress=1"])

    @staticmethod
    def report_task_complete(agent_id: str, task_name: str):
        subprocess.run(["python3", "scripts/swarm_controller.py", "--update-metrics", agent_id, "task_progress=10"])

    @staticmethod
    def report_task_error(agent_id: str, error_msg: str):
        subprocess.run(
            [
                "python3",
                "scripts/swarm_controller.py",
                "--update-metrics",
                agent_id,
                f"last_error={error_msg}",
                "error_count=1",
            ]
        )


@flow(name="prefect-swarm-flow")
def my_flow():
    agent_id = "prefect-worker-1"

    # Pre-task: report start
    PrefectSwarmReporter.report_task_start(agent_id, "my_task")

    try:
        # Run task
        result = my_task()

        # Post-task: report completion
        PrefectSwarmReporter.report_task_complete(agent_id, "my_task")

        return result
    except Exception as e:
        # Error: report to controller
        PrefectSwarmReporter.report_task_error(agent_id, str(e))
        raise


@task
def my_task():
    # Your task logic
    pass
```

### Example 3: Custom Agent System

```bash
#!/bin/bash
# run_agent.sh - Wrapper for custom agent system

AGENT_ID=$1
TASK=$2

# Check if swarm controller allows launching
if ! python3 scripts/swarm_controller.py --status > /dev/null 2>&1; then
  echo "Swarm controller not running, starting it"
  python3 scripts/swarm_controller.py --monitor &
  sleep 2
fi

# Register agent
python3 scripts/swarm_controller.py --update-metrics "$AGENT_ID" \
  pid=$$ \
  task_progress=0 \
  error_count=0

# Run agent task
python3 -m your_agent_system run "$TASK"
RESULT=$?

# Report completion
if [ $RESULT -eq 0 ]; then
  python3 scripts/swarm_controller.py --update-metrics "$AGENT_ID" \
    task_progress=10 \
    error_count=0
else
  python3 scripts/swarm_controller.py --update-metrics "$AGENT_ID" \
    error_count=1 \
    last_error="exit code $RESULT"
fi

exit $RESULT
```

## Pause/Resume Pattern

When system needs resources, gracefully pause agents:

```bash
# Monitor system resources
while true; do
  PRESSURE=$(python3 scripts/swarm_controller.py --status | \
    python3 -c "import json, sys; s=json.load(sys.stdin); \
    print(max(s['system']['cpu_percent'], s['system']['memory_percent']))")

  if (( $(echo "$PRESSURE > 85" | bc -l) )); then
    echo "High resource pressure, pausing agents"

    # Pause agents one by one
    for agent_id in agent-1 agent-2 agent-3; do
      python3 scripts/swarm_controller.py --pause-agent "$agent_id"
      sleep 1
    done
  fi

  # Check if pressure reduced
  PRESSURE=$(python3 scripts/swarm_controller.py --status | \
    python3 -c "import json, sys; s=json.load(sys.stdin); \
    print(max(s['system']['cpu_percent'], s['system']['memory_percent']))")

  if (( $(echo "$PRESSURE < 70" | bc -l) )); then
    echo "Resources freed, resuming agents"
    for agent_id in agent-1 agent-2 agent-3; do
      python3 scripts/swarm_controller.py --resume-agent "$agent_id"
      sleep 1
    done
  fi

  sleep 5
done
```

## Status Monitoring

Continuously monitor swarm health:

```bash
# Watch health reports (every 10 seconds)
watch -n 10 'python3 scripts/swarm_controller.py --report'

# Log health snapshots hourly
*/60 * * * * python3 scripts/swarm_controller.py --report >> /var/log/swarm-health.log
```

## Alerting Integration

Send alerts when critical conditions detected:

```python
# swarm_alerter.py
import json
import subprocess
from datetime import datetime


def check_swarm_health():
    result = subprocess.run(["python3", "scripts/swarm_controller.py", "--status"], capture_output=True, text=True)

    if result.returncode != 0:
        return

    status = json.loads(result.stdout)
    alerts = []

    # Check for dead agents
    dead = sum(1 for a in status["agents"].values() if a["status"] == "dead")
    if dead > 0:
        alerts.append(f"CRITICAL: {dead} dead agent(s)")

    # Check for resource pressure
    if status["system"]["cpu_percent"] > 90:
        alerts.append(f"WARNING: CPU {status['system']['cpu_percent']:.1f}%")

    if status["system"]["memory_percent"] > 85:
        alerts.append(f"WARNING: Memory {status['system']['memory_percent']:.1f}%")

    # Check queue backlog
    if status["queue"]["pending"] > 20:
        alerts.append(f"WARNING: Queue backlog {status['queue']['pending']} items")

    # Send alerts
    for alert in alerts:
        send_alert(alert)


def send_alert(message: str):
    # Your alerting logic (email, Slack, etc.)
    print(f"[{datetime.now()}] {message}")


if __name__ == "__main__":
    check_swarm_health()
```

## Configuration Tuning

Adjust controller behavior for your workload:

### CPU-Bound Agents
```yaml
config:
  # Tighter SLO, less aggressive scaling
  slo_time_multiplier: 1.2
  scale_up_queue_threshold: 3
  cpu_threshold: 75.0
```

### I/O-Bound Agents
```yaml
config:
  # Looser SLO, more aggressive scaling
  slo_time_multiplier: 2.0
  scale_up_queue_threshold: 10
  cpu_threshold: 85.0
```

### High Reliability
```yaml
config:
  # Conservative scaling, quick detection
  health_check_interval: 5
  stale_threshold: 15
  max_restart_attempts: 5
  cpu_threshold: 70.0
```

## Testing Integration

Test your integration with mock agents:

```bash
# Start controller
python3 scripts/swarm_controller.py --monitor &
CONTROLLER_PID=$!

# Simulate agent lifecycle
python3 scripts/swarm_controller.py --update-metrics test-agent \
  pid=$$ \
  task_progress=0 \
  error_count=0

sleep 5

python3 scripts/swarm_controller.py --update-metrics test-agent \
  task_progress=10 \
  error_count=0

# Check status
python3 scripts/swarm_controller.py --report

# Cleanup
kill $CONTROLLER_PID
```

## Troubleshooting

### Controller Not Starting

```bash
# Check dependencies
python3 -c "import psutil, yaml; print('OK')"

# Check logs
tail -100 .claude/swarm_controller.log

# Check state file
cat .claude/swarm_state.json
```

### Agents Not Being Detected

```bash
# Verify agent update is working
python3 scripts/swarm_controller.py --update-metrics test-agent \
  pid=12345 \
  task_progress=5

# Check state
python3 scripts/swarm_controller.py --status | grep test-agent
```

### Wrong Scaling Decisions

```bash
# Check queue stats
python3 scripts/swarm_controller.py --status | python3 -c \
  "import json, sys; s=json.load(sys.stdin); print(s['queue'])"

# Adjust thresholds in config/swarm_controller_config.yaml
# Then restart controller
```

## Best Practices

1. **Always register agents** with the controller on startup
2. **Update metrics regularly** (not just on completion)
3. **Use graceful pause** instead of killing agents
4. **Monitor the monitor** - check controller logs weekly
5. **Tune configuration** for your workload (don't use defaults forever)
6. **Have escalation procedures** for when auto-heal fails
7. **Test integration** in staging before production

## Related Documents

- `docs/guides/SWARM_CONTROLLER_README.md` - Architecture and features
- `docs/guides/SWARM_CONTROLLER_USAGE.md` - Detailed CLI guide
- `config/swarm_controller_config.yaml` - Configuration reference
- `.claude/swarm_controller.log` - Controller decision log
