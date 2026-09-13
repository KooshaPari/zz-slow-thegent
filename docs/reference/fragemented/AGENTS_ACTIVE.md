# AGENTS_ACTIVE

Active agent tracking for the swarm controller. This file is auto-updated by the Swarm Controller monitoring loop.

**Last Updated**: None (awaiting first controller run)

---

## Agent Status Summary

| Total | Healthy | Unhealthy | Paused | Dead | Queue Depth |
| ----- | ------- | --------- | ------ | ---- | ----------- |
| 0     | 0       | 0         | 0      | 0    | 0           |

---

## Active Agents

| Agent ID     | Status                     | PID | Restarts | CPU % | Memory % | Errors | Last Activity                                                                      |
| ------------ | -------------------------- | --- | -------- | ----- | -------- | ------ | ---------------------------------------------------------------------------------- |
| researcher-1 | IDLE (awaiting assignment) | --  | 0        | --    | --       | 0      | 2026-02-19 13:00 - Phase 2 already COMPLETED, notified L1, awaiting new assignment |

---

## Recent Events

### Healthy Agents

(None currently tracked)

### Paused Agents

(None currently tracked)

### Unhealthy Agents

(None currently tracked)

### Dead Agents

(None currently tracked)

---

## Health Trends

### Queue Depth (24h)

```
Pending:  [████░░░░░░░░░░░░░░] 5
Claimed:  [██░░░░░░░░░░░░░░░░] 2
Completed: [██████████████████] 50
```

### Agent Success Rate (24h)

```
Success: 95% [██████████████████░]
Errors:  5%  [█░░░░░░░░░░░░░░░░░]
```

### System Resources (24h)

```
CPU:     [████░░░░░░░░░░░░░░] avg 40%
Memory:  [███░░░░░░░░░░░░░░░] avg 35%
```

---

## Configuration

| Setting                    | Value   |
| -------------------------- | ------- |
| Health Check Interval      | 10s     |
| Stale Threshold            | 30s     |
| SLO Multiplier             | 1.5x    |
| Max Concurrent Agents      | 10      |
| Min Concurrent Agents      | 1       |
| CPU Threshold              | 80%     |
| Memory Threshold           | 70%     |
| Max Restart Attempts       | 3       |
| Scale Up Queue Threshold   | 5 items |
| Scale Down Queue Threshold | 2 items |

---

## Quick Links

- **Controller Log**: `.claude/swarm_controller.log`
- **Controller State**: `.claude/swarm_state.json`
- **Configuration**: `config/swarm_controller_config.yaml`
- **Usage Guide**: `docs/guides/SWARM_CONTROLLER_USAGE.md`
- **Work Stream**: `docs/reference/WORK_STREAM.md`

---

## Escalation Contacts

### Level 1 (Operational)

- Check logs: `tail -100 .claude/swarm_controller.log`
- Resume agent: `python scripts/swarm_controller.py --resume-agent <id>`
- Check health: `python scripts/swarm_controller.py --report`

### Level 2 (Engineering)

- Investigate root cause in agent logs
- Review controller configuration
- Check system resources (CPU, memory, disk)

### Level 3 (Critical)

- Dead agents (exceeded max restart attempts)
- Sustained resource pressure (>1 hour)
- Queue backlog growing (pending >> completed)

---

## Notes

This file is managed by the Swarm Controller. Manual updates are possible but will be overwritten on next controller cycle.

To manually update:

```bash
# Resume a paused agent
python scripts/swarm_controller.py --resume-agent <agent-id>

# Pause an agent
python scripts/swarm_controller.py --pause-agent <agent-id>

# Get current status
python scripts/swarm_controller.py --status

# Get health report
python scripts/swarm_controller.py --report
```
