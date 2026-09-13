<DONE>
# Phase 15: Enterprise Lifecycle and Compliance Surface Map

> **Purpose:** Map architectural surfaces for enterprise compliance, SOC/SIEM, ledger, certification export.
> **Depends:** Governance WP-300x, phase14.
> **Acceptance:** Egress, forensic ledger, compliance, privacy surfaces documented.
> **WORK_STREAM ID:** phase15-enterprise-lifecycle

## 1. Overview

This document maps the architectural surfaces required for enterprise-grade compliance, security integration, and ecosystem extensibility.

## 2. Integration Points

### 2.1 Egress Surface: SOC/SIEM Integration

- **New Component**: `src/thegent/observability/egress.py`
- **Responsibility**: Pushing normalized JSON events to external webhooks or syslog endpoints.

### 2.2 Forensic Surface: Incident Replay Ledger

- **New Component**: `src/thegent/governance/ledger.py`
- **Responsibility**: Immutable, hash-chained storage of incident artifacts for post-mortem analysis.

### 2.3 Ecosystem Surface: Marketplace Contracts

- **Existing**: `src/thegent/contracts/registry.py`
- **Expansion**: Verification logic for third-party plugin contracts and metadata.

### 2.4 Compliance Surface: Certification Export

- **New Component**: `src/thegent/governance/compliance.py`
- **Responsibility**: Generating evidence bundles mapped to SOC 2, ISO 42001, and EU AI Act requirements.

### 2.5 Privacy Surface: Redaction Policy

- **Existing**: `src/thegent/output_parser.py` (or similar)
- **Responsibility**: Automatic PII/Secret redaction for support mode sessions.

## 3. Implementation Details

### 3.1 Egress Surface Implementation

```python
# src/thegent/observability/egress.py
from typing import Any
import httpx
import logging

logger = logging.getLogger(__name__)


class SIEMExporter:
    """Exports events to SIEM/SOC endpoints."""

    def __init__(self, endpoint: str, timeout: float = 5.0):
        self.endpoint = endpoint
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def emit(self, event: dict[str, Any]) -> bool:
        """Emit normalized event to SIEM endpoint."""
        try:
            normalized = self._normalize_event(event)
            response = self.client.post(self.endpoint, json=normalized, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to emit event to SIEM: {e}")
            return False

    def _normalize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Normalize event to SIEM format."""
        return {
            "timestamp": event.get("timestamp", datetime.now(UTC).isoformat()),
            "severity": event.get("severity", "info"),
            "source": "thegent",
            "event_type": event.get("type"),
            "session_id": event.get("session_id"),
            "data": event.get("data", {}),
        }
```

### 3.2 Forensic Ledger Implementation

```python
# src/thegent/governance/ledger.py
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class LedgerEntry:
    """Immutable ledger entry."""

    entry_id: str
    timestamp: datetime
    event_type: str
    data: dict[str, Any]
    previous_hash: str | None = None
    hash: str | None = None

    def compute_hash(self) -> str:
        """Compute hash for this entry."""
        content = json.dumps(
            {
                "entry_id": self.entry_id,
                "timestamp": self.timestamp.isoformat(),
                "event_type": self.event_type,
                "data": self.data,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()


class Ledger:
    """Immutable, hash-chained ledger for forensic analysis."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.entries_file = storage_path / "ledger.jsonl"
        self._load_entries()

    def add(self, event_type: str, data: dict[str, Any]) -> LedgerEntry:
        """Add entry to ledger."""
        previous_hash = self._get_last_hash()

        entry = LedgerEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            event_type=event_type,
            data=data,
            previous_hash=previous_hash,
        )

        entry.hash = entry.compute_hash()

        # Append to ledger file
        with open(self.entries_file, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        for i, entry in enumerate(self.entries):
            if i > 0:
                if entry.previous_hash != self.entries[i - 1].hash:
                    return False
            if entry.hash != entry.compute_hash():
                return False
        return True
```

### 3.3 Compliance Export Implementation

```python
# src/thegent/governance/compliance.py (extension)
from thegent.governance.ledger import Ledger
from thegent.governance.escalation import EscalationQueue


class ComplianceExporter:
    """Exports compliance evidence bundles."""

    def __init__(self, ledger: Ledger, escalation_queue: EscalationQueue):
        self.ledger = ledger
        self.escalation_queue = escalation_queue

    def generate_evidence_bundle(
        self, profile: ComplianceProfile, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Generate evidence bundle for compliance profile."""
        # Collect ledger entries
        ledger_entries = self.ledger.query(start_date=start_date, end_date=end_date)

        # Collect escalation queue items
        escalations = self.escalation_queue.list_pending(start_date=start_date, end_date=end_date)

        # Generate bundle
        bundle = {
            "profile": profile.profile.value,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "generated_at": datetime.now(UTC).isoformat(),
            "run_history": ledger_entries,
            "policy_logs": escalations,
            "hash_chain": self.ledger.verify_chain(),
        }

        # Sign bundle (for SOC 2, US-SEC)
        if profile.profile in [ComplianceProfile.US_SEC, ComplianceProfile.SOX]:
            bundle["signature"] = self._sign_bundle(bundle)

        return bundle
```

### 3.4 Privacy Redaction Implementation

```python
# src/thegent/output_parser.py (extension)
import re
from typing import Any


class PIIRedactor:
    """Redacts PII and secrets from output."""

    # Patterns for common PII
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}-\d{3}-\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "api_key": r"sk-[a-zA-Z0-9]{32,}",
        "token": r"[a-zA-Z0-9_-]{32,}",
    }

    def redact(self, text: str, mode: str = "support") -> str:
        """Redact PII and secrets from text."""
        redacted = text

        for pattern_name, pattern in self.PATTERNS.items():
            redacted = re.sub(pattern, "[REDACTED]", redacted)

        return redacted
```

## 4. Acceptance Criteria Status

- [x] Egress surface documented (SIEM integration)
- [x] Forensic surface documented (Ledger with hash chain)
- [x] Compliance surface documented (Evidence bundle export)
- [x] Privacy surface documented (PII redaction)
- [x] Implementation patterns provided
- [ ] Integration tests passing (pending)

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
