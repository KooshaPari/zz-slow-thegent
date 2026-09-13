# CRUN Security Model

**Security architecture, authentication, authorization, and data protection practices**

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication Methods](#authentication-methods)
3. [Authorization Model](#authorization-model)
4. [Data Security](#data-security)
5. [Network Security](#network-security)
6. [API Security](#api-security)
7. [Known Security Considerations](#known-security-considerations)
8. [Security Best Practices](#security-best-practices)

---

## Security Overview

CRUN implements a multi-layered security model:

1. **Authentication:** Verify user/service identity
2. **Authorization:** Control what authenticated users can do
3. **Encryption:** Protect data in transit and at rest
4. **Audit Logging:** Track all significant actions
5. **Input Validation:** Prevent injection attacks
6. **Access Control:** Limit exposure of sensitive resources

### Security Principles

- **Least Privilege:** Grant minimum necessary access
- **Defense in Depth:** Multiple security layers
- **Secure by Default:** Safe defaults, explicit opt-in for risky features
- **Fail Secure:** Deny access on authentication failure
- **Audit Trail:** Log security-relevant events

---

## Authentication Methods

### 1. Environment Variable Authentication (Default)

For local/development use:

```bash
# Set in .env or shell
export CRUN_AUTH_TOKEN=secret-token-here

# CRUN will verify this token on startup
crun --help
```

**Security Level:** Low (suitable for development only)  
**Use Case:** Local development, testing  
**Pros:** Simple, no external dependencies  
**Cons:** Token in plaintext, shared machine risk

---

### 2. JWT Token Authentication (Production)

For API and multi-user scenarios:

```bash
# Generate secret key
openssl rand -hex 32
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Configure in .env
CRUN_JWT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Client includes JWT in requests
curl -H "Authorization: Bearer eyJhbGciOi..." http://localhost:8000/api/plans
```

**Token Structure:**
```
Header.Payload.Signature

Header: {alg: HS256, typ: JWT}
Payload: {sub: user123, exp: 1234567890, iat: 1234567800}
Signature: HMACSHA256(header + "." + payload, secret)
```

**Security Level:** Medium-High  
**Use Case:** API authentication, web services  
**Pros:** Stateless, can be distributed, self-contained claims  
**Cons:** Token interception risk, key management needed

**Token Lifecycle:**
```bash
# Issue token (login)
POST /api/auth/login
{
  "username": "user",
  "password": "pass"
}
Response: {"token": "eyJ..."}

# Use token (API request)
GET /api/plans
Headers: Authorization: Bearer eyJ...

# Refresh token (before expiry)
POST /api/auth/refresh
Headers: Authorization: Bearer eyJ...
Response: {"token": "eyJ...(new)"}

# Revoke token (logout)
POST /api/auth/logout
```

---

### 3. API Key Authentication

For service-to-service communication:

```bash
# Generate API key
crun generate-api-key --name "CI/CD Pipeline"
# Output: crun_abc123def456ghi789jkl012mno345

# Use in requests
curl -H "X-API-Key: crun_abc123..." http://localhost:8000/api/plans

# Revoke compromised key
crun revoke-api-key crun_abc123def456ghi789jkl012mno345
```

**Security Level:** Medium  
**Use Case:** CI/CD pipelines, third-party integrations  
**Pros:** Simple, can be rotated per service  
**Cons:** Leakage risk, logging issues

---

### 4. OAuth2 / OpenID Connect (Enterprise)

For enterprise deployments with centralized identity:

```bash
# Configure OAuth provider
CRUN_OAUTH_PROVIDER=https://accounts.google.com
CRUN_OAUTH_CLIENT_ID=...
CRUN_OAUTH_CLIENT_SECRET=...
CRUN_OAUTH_REDIRECT_URI=http://localhost:8000/callback

# User redirected to provider, authorized, redirected back
# CRUN exchanges authorization code for tokens
```

**Security Level:** High  
**Use Case:** Enterprise, multi-tenant  
**Providers:** Google, GitHub, Microsoft, Okta  
**Pros:** Centralized identity, user deprovisioning, audit trails  
**Cons:** External dependency, complex setup

---

## Authorization Model

CRUN uses Role-Based Access Control (RBAC):

### Roles

| Role | Capabilities | Use Case |
|------|--------------|----------|
| **Admin** | All operations | System owner |
| **Operator** | Create/monitor plans, view metrics | Production operator |
| **Developer** | Generate plans, analyze code, execute | Developer |
| **Viewer** | Read-only access to plans and results | Stakeholder, audit |
| **Anonymous** | No access (unless disabled) | N/A |

### Role Permissions

```
┌─────────────────────────────────────────────────────────────┐
│                    CRUN Permissions Matrix                   │
├─────────────────────────────────┬───┬──────┬─────┬───┬──────┤
│ Operation                       │Ad │Op    │Dev  │Viw│Anon  │
├─────────────────────────────────┼───┼──────┼─────┼───┼──────┤
│ View plans                      │✓  │✓     │✓    │✓  │-     │
│ Create plans                    │✓  │✓     │✓    │-  │-     │
│ Edit plans                      │✓  │✓     │✓    │-  │-     │
│ Delete plans                    │✓  │-     │-    │-  │-     │
│ Execute plans                   │✓  │✓     │✓    │-  │-     │
│ Monitor execution               │✓  │✓     │✓    │✓  │-     │
│ View metrics                    │✓  │✓     │✓    │✓  │-     │
│ Manage users                    │✓  │-     │-    │-  │-     │
│ Change settings                 │✓  │-     │-    │-  │-     │
│ View audit logs                 │✓  │✓     │-    │-  │-     │
│ Export data                     │✓  │✓     │✓    │✓  │-     │
│ Create API keys                 │✓  │✓     │✓    │-  │-     │
├─────────────────────────────────┼───┼──────┼─────┼───┼──────┤
Legend: ✓=allowed, -=denied, Ad=Admin, Op=Operator, Dev=Developer, Viw=Viewer
```

### Assigning Roles

```bash
# Admin assigns roles to users
crun user assign-role alice admin

# Via API
curl -X POST http://localhost:8000/api/users/bob/roles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "developer"}'
```

---

## Data Security

### Data at Rest

**Default Storage (SQLite):**
```bash
# Data stored in local SQLite database
.crun/crun.db

# File permissions (restrictive)
chmod 600 .crun/crun.db

# Not encrypted by default
# For encrypted DB, use PostgreSQL with SSL
```

**PostgreSQL Storage (Recommended for Production):**
```bash
# Store in production-grade database
CRUN_DB_URL=postgresql://user:pass@server:5432/crun

# Enable encryption on database side
# PostgreSQL: pgcrypto extension
CREATE EXTENSION pgcrypto;
CREATE TABLE secrets (
  id SERIAL,
  value bytea,
  -- Encrypt on insert
  CONSTRAINT secret_check CHECK (octet_length(value) > 0)
);
```

### Data in Transit

**HTTP (Insecure, avoid in production):**
```bash
# Unencrypted communication
http://localhost:8000/api/plans
# Risk: MITM attacks, credential sniffing
```

**HTTPS (Recommended):**
```bash
# Encrypted communication
https://localhost:8000/api/plans

# Enable in configuration
CRUN_ENABLE_HTTPS=true
CRUN_SSL_CERT_FILE=/path/to/cert.pem
CRUN_SSL_KEY_FILE=/path/to/key.pem
```

**TLS Version & Ciphers:**
```bash
# Force TLS 1.2+
CRUN_TLS_MIN_VERSION=1.2

# Strong cipher suites
CRUN_TLS_CIPHERS=HIGH:!aNULL:!MD5
```

### Sensitive Data Handling

**API Keys:** Never log or expose
```bash
# ❌ DON'T: Log API keys
logger.info(f"API Key: {api_key}")

# ✓ DO: Log only last 4 characters
logger.info(f"API Key: ...{api_key[-4:]}")
```

**Passwords:** Always hash, never store plaintext
```bash
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])
hashed = pwd_context.hash(password)

# Verify
pwd_context.verify(password, hashed)
```

**Secrets Configuration:**
```bash
# Use secret management systems
# AWS Secrets Manager, HashiCorp Vault, etc.

# For local development
.env                 # Gitignored, NOT in version control
.env.example         # Template, safe to commit
```

---

## Network Security

### Network Isolation

**Single Machine:**
```bash
# Bind to localhost only (default, secure)
CRUN_HOST=127.0.0.1
CRUN_PORT=8000

# Only accessible from local machine
# Avoid: CRUN_HOST=0.0.0.0  (all interfaces)
```

**Cloud Deployment:**
```bash
# Use private networks
# AWS: VPC, Security Groups
# GCP: VPC Networks
# Azure: Virtual Networks

# Firewall rules (example)
- SSH (22): Restricted to admin IP
- HTTP (80): Redirect to HTTPS
- HTTPS (443): Open to clients
- API (8000): Internal only
```

### Rate Limiting

```bash
# Prevent brute force and DoS attacks
CRUN_RATE_LIMIT_ENABLED=true
CRUN_RATE_LIMIT_REQUESTS=1000
CRUN_RATE_LIMIT_WINDOW=3600  # Per hour

# Per-endpoint configuration
# POST /api/auth/login: 10 requests/hour
# GET /api/plans: 1000 requests/hour
# POST /api/plans: 100 requests/hour
```

### CORS (Cross-Origin Resource Sharing)

```bash
# Restrict which domains can call CRUN API
CRUN_CORS_ENABLED=true
CRUN_CORS_ORIGINS=https://example.com,https://app.example.com

# Avoid: CRUN_CORS_ORIGINS=*  (allow all)
```

---

## API Security

### Input Validation

All inputs validated before processing:

```python
from pydantic import BaseModel, Field, validator


class PlanRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=10000)
    max_tokens: int = Field(default=4000, ge=100, le=10000)

    @validator("description")
    def no_script_injection(cls, v):
        # Prevent script injection
        if "<script>" in v.lower():
            raise ValueError("Invalid content")
        return v
```

### Output Sanitization

Sanitize sensitive data before returning:

```python
class PlanResponse(BaseModel):
    id: str
    description: str
    # ✓ DO: Exclude sensitive data
    # ✗ DON'T: Include API_KEY in response

    class Config:
        exclude = {"api_key", "password", "secret"}
```

### Error Handling

Generic error messages, detailed logging:

```python
# ✓ DO: Generic error to client
try:
    result = process()
except Exception:
    logger.exception("Processing failed")  # Detailed log
    return {"error": "Processing failed"}  # Generic response

# ✗ DON'T: Expose stack trace
except Exception as e:
    return {"error": str(e)}  # Leaks implementation details
```

### Authentication Headers

```bash
# Always use Authorization header, never in URL
# ✓ DO:
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/plans

# ✗ DON'T:
curl http://localhost:8000/api/plans?token=$TOKEN
# Token logged in server logs, browser history, etc.
```

---

## Known Security Considerations

### 1. Local File Access

**Risk:** Code execution on the machine  
**Mitigation:**
```bash
# Restrict workspace access to current user
chmod 700 .crun

# Use read-only for external projects
CRUN_WORKSPACE_ROOT=/mnt/external  # Mount read-only
```

### 2. Agent Command Execution

**Risk:** Agents execute arbitrary commands  
**Mitigation:**
```bash
# Run agents in sandboxed environment
CRUN_AGENT_SANDBOX=true

# Whitelist allowed commands
CRUN_AGENT_ALLOWED_COMMANDS=python,bash,npm,pip
```

### 3. Large File Processing

**Risk:** DoS via large file uploads  
**Mitigation:**
```bash
# Limit file size
CRUN_MAX_FILE_SIZE=100MB
CRUN_MAX_REQUEST_SIZE=500MB
```

### 4. External API Calls

**Risk:** SSRF (Server-Side Request Forgery)  
**Mitigation:**
```bash
# Whitelist allowed URLs
CRUN_ALLOWED_DOMAINS=api.openai.com,api.anthropic.com

# Prevent internal network access
CRUN_PREVENT_INTERNAL_IPS=true
```

### 5. Dependency Vulnerabilities

**Risk:** Using vulnerable packages  
**Mitigation:**
```bash
# Regular dependency updates
pip install --upgrade -r requirements.txt

# Security scanning
pip install bandit safety
bandit -r crun/
safety check
```

---

## Security Best Practices

### For Development

1. **Use Virtual Environments**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Never Commit Secrets**
   ```bash
   # .gitignore
   .env
   .env.local
   *.pem
   *.key
   ```

3. **Regular Updates**
   ```bash
   pip list --outdated
   pip install --upgrade pip
   ```

4. **Code Review**
   - Peer review all code
   - Security-focused review for sensitive code
   - Static analysis (bandit, ruff)

### For Production

1. **Use HTTPS/TLS**
   ```bash
   CRUN_ENABLE_HTTPS=true
   CRUN_SSL_CERT_FILE=/etc/ssl/certs/server.crt
   CRUN_SSL_KEY_FILE=/etc/ssl/private/server.key
   ```

2. **Strong Authentication**
   - Enforce JWT tokens
   - Enable multi-factor authentication if available
   - Rotate API keys regularly

3. **Database Security**
   ```bash
   # Use PostgreSQL, not SQLite
   # Enable SSL for database connections
   # Use strong credentials
   # Regular backups
   ```

4. **Network Security**
   - Firewall rules
   - VPN for remote access
   - Network segmentation
   - DDoS protection

5. **Monitoring & Logging**
   ```bash
   # Enable audit logging
   CRUN_AUDIT_LOG_ENABLED=true
   CRUN_AUDIT_LOG_FILE=.crun/audit.log
   
   # Monitor for suspicious activity
   # Alert on failed authentication attempts
   # Track privilege escalations
   ```

6. **Regular Backups**
   ```bash
   # Daily backups
   pg_dump crun > backup_$(date +%Y%m%d).sql
   
   # Test restore procedure
   psql crun < backup_*.sql
   ```

7. **Incident Response**
   - Document security incidents
   - Post-mortem analysis
   - Fix identified vulnerabilities
   - Notify affected users

### Security Checklist

```bash
# Pre-deployment checklist
- [ ] HTTPS enabled with valid certificate
- [ ] Strong JWT secret configured
- [ ] Database credentials secured
- [ ] API keys not hardcoded
- [ ] Input validation in place
- [ ] Output sanitization implemented
- [ ] Rate limiting enabled
- [ ] CORS restricted to known origins
- [ ] Audit logging enabled
- [ ] Backups tested
- [ ] Security headers configured
- [ ] Firewall rules verified
```

---

## Security Reporting

If you discover a security vulnerability:

1. **Do NOT** post publicly
2. **Email** security@example.com with:
   - Vulnerability description
   - Affected versions
   - Steps to reproduce
   - Proof of concept
3. **Allow** 90 days for response and patch
4. **Credit** will be given upon publication

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc7519)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-20
