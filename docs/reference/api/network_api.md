# network API Reference

> **Source**: `src/thegent/resources/network.py`

Network bandwidth monitoring for thegent resource management.

---

## BandwidthSample

Calculated bandwidth for a single network interface over a sampling interval.

---

## NetworkMonitor

Monitor network bandwidth using psutil.

Falls back to returning empty/zero results when psutil is unavailable.

### Methods

#### NetworkMonitor.get_stats

```python
get_stats(self: Any, interface: Any)
```

Return current I/O counters per interface.

**Parameters**:

- `interface`: If provided, return stats only for this interface.
  If None, return stats for all available interfaces.

**Returns**: List of NetworkStats, one per matching interface.
Returns an empty list when psutil is unavailable.

---

#### NetworkMonitor.get_total_bandwidth

```python
get_total_bandwidth(self: Any)
```

Return (send_bps, recv_bps) summed across all interfaces.

Takes two counter snapshots with a 1-second interval.

**Returns**: Tuple of (total_send_bps, total_recv_bps).
Returns (0.0, 0.0) when psutil is unavailable or no interfaces found.

---

#### NetworkMonitor.list_interfaces

```python
list_interfaces(self: Any)
```

Return the names of all available network interfaces.

**Returns**: List of interface name strings.
Returns an empty list when psutil is unavailable.

---

#### NetworkMonitor.sample_bandwidth

```python
sample_bandwidth(self: Any, interval_s: float)
```

Measure bandwidth by taking two samples separated by _interval_s_ seconds.

**Parameters**:

- `interval_s`: Seconds between the two counter snapshots.
  Must be positive; values &lt;= 0 are clamped to 0.01 s.

**Returns**: List of BandwidthSample (send_bps / recv_bps) per interface.
Returns an empty list when psutil is unavailable.

---

---

## NetworkStats

Raw I/O counters for a single network interface at a point in time.

---

## get_stats

```python
get_stats(self: Any, interface: Any)
```

Return current I/O counters per interface.

**Parameters**:

- `interface`: If provided, return stats only for this interface.
  If None, return stats for all available interfaces.

**Returns**: List of NetworkStats, one per matching interface.
Returns an empty list when psutil is unavailable.

---

## get_total_bandwidth

```python
get_total_bandwidth(self: Any)
```

Return (send_bps, recv_bps) summed across all interfaces.

Takes two counter snapshots with a 1-second interval.

**Returns**: Tuple of (total_send_bps, total_recv_bps).
Returns (0.0, 0.0) when psutil is unavailable or no interfaces found.

---

## list_interfaces

```python
list_interfaces(self: Any)
```

Return the names of all available network interfaces.

**Returns**: List of interface name strings.
Returns an empty list when psutil is unavailable.

---

## sample_bandwidth

```python
sample_bandwidth(self: Any, interval_s: float)
```

Measure bandwidth by taking two samples separated by _interval_s_ seconds.

**Parameters**:

- `interval_s`: Seconds between the two counter snapshots.
  Must be positive; values &lt;= 0 are clamped to 0.01 s.

**Returns**: List of BandwidthSample (send_bps / recv_bps) per interface.
Returns an empty list when psutil is unavailable.

---
