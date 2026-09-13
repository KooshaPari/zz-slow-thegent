<DONE>
# Governance Compliance Reports Research

> **WORK_STREAM ID:** research-governance-compliance-reports
> **Priority:** P2
> **Depends:** WP-3006, research-phase13-compliance-profiles
> **Status:** ✅ Research Complete

## Summary

This document provides research and implementation guidance for automated compliance report generation and distribution in thegent governance system.

## Architecture Options

### Option A: Scheduled Reports

**Approach**: Generate reports on a fixed schedule (daily, weekly, monthly)

**Pros**:

- Predictable workload
- Easy to automate
- Consistent reporting cadence

**Cons**:

- Delayed visibility
- May miss urgent issues
- Fixed format may not suit all needs

### Option B: On-Demand Reports

**Approach**: Generate reports when requested via CLI/API

**Pros**:

- Immediate visibility
- Flexible date ranges
- Customizable content

**Cons**:

- Manual trigger required
- Potential performance impact
- No automatic distribution

### Option C: Real-Time Dashboards

**Approach**: Continuous real-time compliance monitoring dashboard

**Pros**:

- Immediate visibility
- Proactive issue detection
- Interactive exploration

**Cons**:

- Higher resource usage
- Requires dashboard infrastructure
- May be overwhelming

### Recommended: Option A + C (Scheduled + Real-Time)

**Approach**: Combine scheduled reports with real-time dashboard

**Benefits**:

- Scheduled reports for audit trails and compliance evidence
- Real-time dashboard for operational monitoring
- Comprehensive coverage

## Implementation Details

### 3.1 Report Generator

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from thegent.governance.compliance import ComplianceProfile


@dataclass
class ComplianceReport:
    """Compliance report structure."""

    profile: ComplianceProfile
    start_date: datetime
    end_date: datetime
    generated_at: datetime
    summary: dict
    violations: list[dict]
    evidence: list[dict]
    signature: Optional[str] = None


class ComplianceReportGenerator:
    """Generates compliance reports."""

    def __init__(self, profile: ComplianceProfile):
        self.profile = profile

    def generate_report(self, start_date: datetime, end_date: datetime) -> ComplianceReport:
        """Generate compliance report for date range."""
        # Collect evidence
        evidence = self._collect_evidence(start_date, end_date)

        # Analyze compliance
        violations = self._analyze_compliance(evidence)

        # Generate summary
        summary = self._generate_summary(violations, evidence)

        # Create report
        report = ComplianceReport(
            profile=self.profile,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(UTC),
            summary=summary,
            violations=violations,
            evidence=evidence,
        )

        # Sign report (for SOC 2, US-SEC)
        if self.profile.profile in [ComplianceProfile.US_SEC, ComplianceProfile.SOX]:
            report.signature = self._sign_report(report)

        return report

    def _collect_evidence(self, start_date: datetime, end_date: datetime) -> list[dict]:
        """Collect compliance evidence for date range."""
        from thegent.governance.ledger import Ledger
        from thegent.governance.escalation import EscalationQueue

        ledger = Ledger()
        escalation_queue = EscalationQueue()

        evidence = []

        # Collect ledger entries
        ledger_entries = ledger.query(start_date=start_date, end_date=end_date)
        evidence.extend(ledger_entries)

        # Collect escalation queue items
        escalations = escalation_queue.list_pending(start_date=start_date, end_date=end_date)
        evidence.extend(escalations)

        return evidence

    def _analyze_compliance(self, evidence: list[dict]) -> list[dict]:
        """Analyze evidence for compliance violations."""
        violations = []

        for control in self.profile.get_mandatory_controls():
            if not self._check_control_compliance(control, evidence):
                violations.append(
                    {
                        "control_id": control.id,
                        "control_name": control.name,
                        "severity": "high" if control.mandatory else "medium",
                        "description": f"Control {control.id} not satisfied",
                    }
                )

        return violations

    def _generate_summary(self, violations: list[dict], evidence: list[dict]) -> dict:
        """Generate report summary."""
        return {
            "total_controls": len(self.profile.get_mandatory_controls()),
            "compliant_controls": len(self.profile.get_mandatory_controls()) - len(violations),
            "violations": len(violations),
            "evidence_count": len(evidence),
            "compliance_percentage": (
                (len(self.profile.get_mandatory_controls()) - len(violations))
                / len(self.profile.get_mandatory_controls())
                * 100
            ),
        }
```

### 3.2 Scheduled Report Runner

```python
from apscheduler.schedulers.background import BackgroundScheduler
from thegent.governance.compliance import ComplianceProfile


class ScheduledReportRunner:
    """Runs scheduled compliance reports."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.generators = {profile: ComplianceReportGenerator(profile) for profile in ComplianceProfile}

    def schedule_reports(self) -> None:
        """Schedule all compliance reports."""
        # Daily reports for critical profiles
        self.scheduler.add_job(
            self._generate_daily_report, trigger="cron", hour=0, minute=0, args=[ComplianceProfile.US_SEC]
        )

        # Weekly reports for standard profiles
        self.scheduler.add_job(
            self._generate_weekly_report,
            trigger="cron",
            day_of_week="monday",
            hour=0,
            minute=0,
            args=[ComplianceProfile.GDPR],
        )

        # Monthly reports for all profiles
        self.scheduler.add_job(self._generate_monthly_report, trigger="cron", day=1, hour=0, minute=0)

    def _generate_daily_report(self, profile: ComplianceProfile) -> None:
        """Generate daily report."""
        generator = self.generators[profile]
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=1)

        report = generator.generate_report(start_date, end_date)
        self._distribute_report(report)

    def _distribute_report(self, report: ComplianceReport) -> None:
        """Distribute report to stakeholders."""
        # Save to file system
        self._save_report(report)

        # Send via email/webhook if configured
        if self._should_notify(report):
            self._send_notification(report)
```

### 3.3 Real-Time Dashboard

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


class ComplianceDashboard:
    """Real-time compliance dashboard."""

    def __init__(self):
        self.app = FastAPI()
        self.generator = ComplianceReportGenerator(ComplianceProfile.US_SEC)
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup dashboard routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Main dashboard view."""
            # Get real-time compliance status
            status = self._get_realtime_status()
            return self._render_dashboard(status)

        @self.app.get("/api/compliance/status")
        async def compliance_status():
            """API endpoint for compliance status."""
            return self._get_realtime_status()

    def _get_realtime_status(self) -> dict:
        """Get real-time compliance status."""
        # Get last 24 hours
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(hours=24)

        report = self.generator.generate_report(start_date, end_date)

        return {
            "compliance_percentage": report.summary["compliance_percentage"],
            "violations": len(report.violations),
            "last_updated": report.generated_at.isoformat(),
        }
```

## Acceptance Criteria

- [x] Architecture options evaluated (A, B, C)
- [x] Hybrid approach recommended (A + C)
- [x] Report generator designed (`ComplianceReportGenerator`)
- [x] Scheduled report runner designed (`ScheduledReportRunner`)
- [x] Real-time dashboard designed (`ComplianceDashboard`)
- [ ] Implementation complete (pending)
- [ ] Integration tests passing (pending)

## References

- [Compliance Profile Mapping](./phase13-compliance-profile-mapping.md)
- [Governance WP Gaps](./GOVERNANCE_WP_GAPS_EXPANDED.md)
- [WORK_STREAM.md](../reference/WORK_STREAM.md)
