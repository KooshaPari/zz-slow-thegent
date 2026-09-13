# tracker API Reference

> **Source**: `src/thegent/cost/tracker.py`

WP-Y4: Per-run cost aggregation and budget alerts.

Aggregates actual cost per run and provides budget alerting for the orchestration layer.

---

## CostEntry

Single cost entry for a token or API call.

### Methods

#### CostEntry.to_dict

```python
to_dict(self: Any)
```

Convert entry to dictionary.

---

---

## RunCostTracker

Track and aggregate costs across runs.

### Methods

#### RunCostTracker.**init**

```python
__init__(self: Any, cost_dir: Any)
```

Initialize tracker.

**Parameters**:

- `cost_dir`: Directory to store cost reports.

---

#### RunCostTracker.end_run

```python
end_run(self: Any)
```

End run and return aggregated costs.

Saves a summary JSON for the run and appends to the global aggregate log.

**Returns**: Dictionary containing run summary.

---

#### RunCostTracker.record_entry

```python
record_entry(self: Any, entry: CostEntry)
```

Record a cost entry.

**Parameters**:

- `entry`: The cost entry to record.

---

#### RunCostTracker.start_run

```python
start_run(self: Any, run_id: str)
```

Start tracking a new run.

**Parameters**:

- `run_id`: Unique identifier for the run.

---

---

## end_run

```python
end_run(self: Any)
```

End run and return aggregated costs.

Saves a summary JSON for the run and appends to the global aggregate log.

**Returns**: Dictionary containing run summary.

---

## get_run_cost_tracker

Get global run cost tracker instance.

---

## record_entry

```python
record_entry(self: Any, entry: CostEntry)
```

Record a cost entry.

**Parameters**:

- `entry`: The cost entry to record.

---

## start_run

```python
start_run(self: Any, run_id: str)
```

Start tracking a new run.

**Parameters**:

- `run_id`: Unique identifier for the run.

---

## to_dict

```python
to_dict(self: Any)
```

Convert entry to dictionary.

---
