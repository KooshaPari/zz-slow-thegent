# alerting API Reference

> **Source**: `src/thegent/routing/alerting.py`

Alerting integration for LiteLLM routing.

Provides alert management for routing events including budget exceeded,
high latency, and provider errors. Supports webhook notifications.

---

## Alert

Routing alert.

### Methods

#### Alert.to_json

```python
to_json(self: Any)
```

Serialize alert to JSON dict.

---

---

## AlertManager

Manage routing alerts with webhook support.

### Methods

#### AlertManager.**init**

```python
__init__(self: Any, webhook_url: Any, min_severity: str)
```

Initialize alert manager.

**Parameters**:

- `webhook_url`: Optional webhook URL for alert delivery.
- `min_severity`: Minimum severity level to send (info, warning, critical).

---

#### AlertManager.alert_budget_exceeded

```python
alert_budget_exceeded(self: Any, daily_spend: float, budget: float)
```

Create and send budget exceeded alert.

**Parameters**:

- `daily_spend`: Current daily spend in USD.
- `budget`: Configured budget limit in USD.

**Returns**: The created Alert.

---

#### AlertManager.alert_cooldown_triggered

```python
alert_cooldown_triggered(self: Any, model: str, provider: str, cooldown_seconds: float, reason: str)
```

Create and send cooldown triggered alert.

**Parameters**:

- `model`: The model in cooldown.
- `provider`: The provider.
- `cooldown_seconds`: Duration of cooldown.
- `reason`: Why cooldown was triggered.

**Returns**: The created Alert.

---

#### AlertManager.alert_high_latency

```python
alert_high_latency(self: Any, model: str, latency_ms: float, threshold_ms: float, provider: Any)
```

Create and send high latency alert.

**Parameters**:

- `model`: The model that had high latency.
- `latency_ms`: Observed latency in milliseconds.
- `threshold_ms`: Configured threshold in milliseconds.
- `provider`: Optional provider name.

**Returns**: The created Alert.

---

#### AlertManager.alert_provider_error

```python
alert_provider_error(self: Any, provider: str, error: str, model: str, is_rate_limit: bool)
```

Create and send provider error alert.

**Parameters**:

- `provider`: The provider that had an error.
- `error`: Error message or type.
- `model`: The model being used.
- `is_rate_limit`: Whether this was a rate limit error.

**Returns**: The created Alert.

---

#### AlertManager.clear_pending_alerts

```python
clear_pending_alerts(self: Any)
```

Clear pending alerts list.

---

#### AlertManager.get_pending_alerts

```python
get_pending_alerts(self: Any)
```

Get list of alerts that weren't sent (no webhook configured).

---

#### AlertManager.send_alert

```python
send_alert(self: Any, alert: Alert)
```

Send alert to configured webhook.

**Parameters**:

- `alert`: The alert to send.

**Returns**: True if sent successfully, False otherwise.

---

#### AlertManager.webhook_url

```python
webhook_url(self: Any)
```

Configured webhook URL.

---

---

## alert_budget_exceeded

```python
alert_budget_exceeded(self: Any, daily_spend: float, budget: float)
```

Create and send budget exceeded alert.

**Parameters**:

- `daily_spend`: Current daily spend in USD.
- `budget`: Configured budget limit in USD.

**Returns**: The created Alert.

---

## alert_cooldown_triggered

```python
alert_cooldown_triggered(self: Any, model: str, provider: str, cooldown_seconds: float, reason: str)
```

Create and send cooldown triggered alert.

**Parameters**:

- `model`: The model in cooldown.
- `provider`: The provider.
- `cooldown_seconds`: Duration of cooldown.
- `reason`: Why cooldown was triggered.

**Returns**: The created Alert.

---

## alert_high_latency

```python
alert_high_latency(self: Any, model: str, latency_ms: float, threshold_ms: float, provider: Any)
```

Create and send high latency alert.

**Parameters**:

- `model`: The model that had high latency.
- `latency_ms`: Observed latency in milliseconds.
- `threshold_ms`: Configured threshold in milliseconds.
- `provider`: Optional provider name.

**Returns**: The created Alert.

---

## alert_provider_error

```python
alert_provider_error(self: Any, provider: str, error: str, model: str, is_rate_limit: bool)
```

Create and send provider error alert.

**Parameters**:

- `provider`: The provider that had an error.
- `error`: Error message or type.
- `model`: The model being used.
- `is_rate_limit`: Whether this was a rate limit error.

**Returns**: The created Alert.

---

## clear_pending_alerts

```python
clear_pending_alerts(self: Any)
```

Clear pending alerts list.

---

## get_alert_manager

Get global alert manager instance.

Initializes with settings from config on first call.

---

## get_pending_alerts

```python
get_pending_alerts(self: Any)
```

Get list of alerts that weren't sent (no webhook configured).

---

## reset_alert_manager

Reset the global alert manager (useful for testing).

---

## send_alert

```python
send_alert(self: Any, alert: Alert)
```

Send alert to configured webhook.

**Parameters**:

- `alert`: The alert to send.

**Returns**: True if sent successfully, False otherwise.

---

## to_json

```python
to_json(self: Any)
```

Serialize alert to JSON dict.

---

## webhook_url

```python
webhook_url(self: Any)
```

Configured webhook URL.

---
