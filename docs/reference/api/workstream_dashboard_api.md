# workstream_dashboard API Reference

> **Source**: `src/thegent/tui/workstream_dashboard.py`

Workstream Dashboard TUI using Textual.

Real-time monitoring dashboard for workstream items, sessions, and auto-launch system.

---

## ConcurrencyPanel

Panel showing concurrency limits and usage.

**Inherits from**: `Static`

### Methods

#### ConcurrencyPanel.**init**

```python
__init__(self: Any)
```

---

#### ConcurrencyPanel.update_concurrency

```python
update_concurrency(self: Any, running: int, limit: int)
```

Update concurrency display.

---

---

## DependenciesTable

Table showing item dependencies.

**Inherits from**: `DataTable`

### Methods

#### DependenciesTable.**init**

```python
__init__(self: Any)
```

---

#### DependenciesTable.update_dependencies

```python
update_dependencies(self: Any, deps: list[dict[(str, Any)]])
```

Update dependencies table.

---

---

## GardenerPanel

Panel showing auto-launch system health and gardening status.

**Inherits from**: `Static`

### Methods

#### GardenerPanel.**init**

```python
__init__(self: Any)
```

---

#### GardenerPanel.update_health

```python
update_health(self: Any, health_data: dict[(str, Any)])
```

Update health display.

---

---

## KPIPanel

KPI panel showing TRAFFIC metrics.

**Inherits from**: `Static`

### Methods

#### KPIPanel.**init**

```python
__init__(self: Any)
```

---

#### KPIPanel.update_kpis

```python
update_kpis(self: Any, kpis: dict[(str, Any)])
```

Update KPI display.

---

---

## ReputationTable

Table showing agent reputation scores.

**Inherits from**: `DataTable`

### Methods

#### ReputationTable.**init**

```python
__init__(self: Any)
```

---

#### ReputationTable.update_scores

```python
update_scores(self: Any, scores: dict[(str, float)])
```

Update reputation scores table.

---

---

## SessionsTable

Table showing active sessions.

**Inherits from**: `DataTable`

### Methods

#### SessionsTable.**init**

```python
__init__(self: Any)
```

---

#### SessionsTable.update_sessions

```python
update_sessions(self: Any, sessions: list[dict[(str, Any)]])
```

Update sessions table.

---

---

## StatsPanel

Statistics panel showing key metrics.

**Inherits from**: `Static`

### Methods

#### StatsPanel.**init**

```python
__init__(self: Any)
```

---

#### StatsPanel.update_stats

```python
update_stats(self: Any, stats: dict[(str, Any)])
```

Update statistics display.

---

---

## WorkstreamDashboard

Real-time workstream monitoring dashboard.

**Inherits from**: `App`

### Methods

#### WorkstreamDashboard.**init**

```python
__init__(self: Any)
```

---

#### WorkstreamDashboard.action_quit

```python
action_quit(self: Any)
```

Quit the dashboard.

---

#### WorkstreamDashboard.action_refresh

```python
action_refresh(self: Any)
```

Manual refresh action.

---

#### WorkstreamDashboard.compose

```python
compose(self: Any)
```

Compose the dashboard layout.

---

#### WorkstreamDashboard.on_mount

```python
on_mount(self: Any)
```

Initialize dashboard on mount.

---

---

## WorkstreamItemsTable

Table showing workstream items.

**Inherits from**: `DataTable`

### Methods

#### WorkstreamItemsTable.**init**

```python
__init__(self: Any)
```

---

#### WorkstreamItemsTable.update_items

```python
update_items(self: Any, items: list[dict[(str, Any)]])
```

Update workstream items table.

---

---

## XPTable

Table showing agent XP and levels.

**Inherits from**: `DataTable`

### Methods

#### XPTable.**init**

```python
__init__(self: Any)
```

---

#### XPTable.update_xp

```python
update_xp(self: Any, xp_data: list[dict[(str, Any)]])
```

Update XP table.

---

---

## action_quit

```python
action_quit(self: Any)
```

Quit the dashboard.

---

## action_refresh

```python
action_refresh(self: Any)
```

Manual refresh action.

---

## compose

```python
compose(self: Any)
```

Compose the dashboard layout.

---

## on_mount

```python
on_mount(self: Any)
```

Initialize dashboard on mount.

---

## run_dashboard

Run the workstream dashboard.

---

## update_concurrency

```python
update_concurrency(self: Any, running: int, limit: int)
```

Update concurrency display.

---

## update_dependencies

```python
update_dependencies(self: Any, deps: list[dict[(str, Any)]])
```

Update dependencies table.

---

## update_health

```python
update_health(self: Any, health_data: dict[(str, Any)])
```

Update health display.

---

## update_items

```python
update_items(self: Any, items: list[dict[(str, Any)]])
```

Update workstream items table.

---

## update_kpis

```python
update_kpis(self: Any, kpis: dict[(str, Any)])
```

Update KPI display.

---

## update_scores

```python
update_scores(self: Any, scores: dict[(str, float)])
```

Update reputation scores table.

---

## update_sessions

```python
update_sessions(self: Any, sessions: list[dict[(str, Any)]])
```

Update sessions table.

---

## update_stats

```python
update_stats(self: Any, stats: dict[(str, Any)])
```

Update statistics display.

---

## update_xp

```python
update_xp(self: Any, xp_data: list[dict[(str, Any)]])
```

Update XP table.

---
