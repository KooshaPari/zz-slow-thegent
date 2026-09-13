# calibration API Reference

> **Source**: `src/thegent/ux/calibration.py`

WP-4008: Feedback loops and confidence calibration.

---

## ConfidenceCalibrator

Calibrates agent confidence scores based on operator feedback.

### Methods

#### ConfidenceCalibrator.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### ConfidenceCalibrator.calibrate

```python
calibrate(self: Any, agent_name: str, raw_confidence: float)
```

Apply calibration bias to a raw confidence score.

---

#### ConfidenceCalibrator.record_feedback

```python
record_feedback(self: Any, agent_name: str, provided_confidence: float, actual_success: bool)
```

Record feedback to update bias map.

---

---

## calibrate

```python
calibrate(self: Any, agent_name: str, raw_confidence: float)
```

Apply calibration bias to a raw confidence score.

---

## record_feedback

```python
record_feedback(self: Any, agent_name: str, provided_confidence: float, actual_success: bool)
```

Record feedback to update bias map.

---
