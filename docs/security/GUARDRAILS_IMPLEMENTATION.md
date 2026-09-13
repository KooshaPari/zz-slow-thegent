# Comprehensive Security Guardrails Implementation

## Overview

This document describes the comprehensive security guardrails system implemented for thegent to ensure safe, secure, and efficient AI agent operations.

## Components

### 1. Command Validation (`security/guardrails.py`)

**Purpose**: Prevent dangerous commands from executing.

**Features**:

- Blocks commands that kill protected processes (agents, terminals)
- Prevents dangerous system operations (`rm -rf /`, `format`, etc.)
- Validates command length and argument count
- Rate limiting for command execution

**Protected Processes**:

- `cursor-agent`, `thegent`, `claude`, `codex`, `droid`, `opencode`, `copilot`
- Shell processes: `bash`, `zsh`, `sh`
- Terminal emulators: `ghostty`, `terminal`, `iterm`, `alacritty`, `kitty`

**Forbidden Patterns**:

- `kill -9 cursor-agent`
- `rm -rf /`
- `xargs kill`
- `pkill cursor`

### 2. Token Optimization (`security/context_optimizer.py`)

**Purpose**: Reduce token usage and costs while maintaining context quality.

**Strategies**:

- **Secret Removal**: Replaces API keys, passwords, tokens with environment variable placeholders
- **Smart Truncation**: Keeps important parts (start/end) when truncating
- **Whitespace Compression**: Reduces unnecessary whitespace
- **Context Compression**: Maintains context within token limits

**Example**:

```
Before: sk-abc123xyz789... (100K tokens)
After: ${OPENAI_API_KEY}... (50K tokens, secrets removed)
```

### 3. Input Sanitization (`security/input_sanitizer.py`)

**Purpose**: Prevent injection attacks and malicious inputs.

**Protections**:

- SQL injection detection
- XSS (Cross-Site Scripting) detection
- Command injection detection
- Filename validation
- Input length limits

### 4. Rate Limiting (`security/guardrails.py`)

**Purpose**: Prevent resource exhaustion and abuse.

**Limits**:

- Commands: 100/minute
- File operations: 200/minute
- Network requests: 50/minute
- Process kills: 10/5 minutes

### 5. Secret Management (`security/guardrails.py`)

**Purpose**: Use environment variables instead of hardcoded secrets.

**Mapping**:

- `openai_api_key` → `OPENAI_API_KEY`
- `anthropic_api_key` → `ANTHROPIC_API_KEY`
- `github_token` → `GITHUB_TOKEN`
- etc.

## Integration Points

### Command Execution

All command execution goes through validation:

```python
from thegent.security.guardrails import validate_command

is_allowed, error = validate_command(cmd)
if not is_allowed:
    raise ValueError(f"Blocked: {error}")
```

### Context Optimization

Prompts are automatically optimized:

```python
from thegent.security.context_optimizer import optimize_context

optimized = optimize_context(prompt, max_tokens=50000)
```

### Secret Access

Secrets accessed via environment variables:

```python
from thegent.security.guardrails import get_secret

api_key = get_secret("openai_api_key")  # Reads from OPENAI_API_KEY env var
```

## Configuration

Configure via environment variables (prefix: `THGENT_SECURITY_`):

```bash
THGENT_SECURITY_ENABLE_GUARDRAILS=true
THGENT_SECURITY_MAX_CONTEXT_TOKENS=100000
THGENT_SECURITY_TARGET_CONTEXT_TOKENS=50000
THGENT_SECURITY_RATE_LIMIT_COMMANDS_PER_MINUTE=100
```

## Security Invariants

System invariants that must always hold:

1. **No Agent Killing**: Agents cannot kill other agent processes
2. **No Root Deletion**: Cannot delete root filesystem
3. **No Dangerous Permissions**: Cannot set dangerous file permissions
4. **Rate Limits**: Operations must respect rate limits
5. **Input Validation**: All inputs must be validated and sanitized

## Token Optimization Strategies

1. **Secret Replacement**: `sk-abc123` → `${OPENAI_API_KEY}`
2. **Smart Truncation**: Keep first 45% + last 45%, truncate middle
3. **Whitespace Compression**: Reduce multiple spaces/newlines
4. **Context Window Management**: Maintain within token limits

## Best Practices

1. **Always use guardrails**: Never bypass security checks
2. **Use environment variables**: Never hardcode secrets
3. **Optimize context**: Use token optimization for large contexts
4. **Validate inputs**: Sanitize all user inputs
5. **Respect rate limits**: Don't exceed operation limits
6. **Log violations**: Monitor security events

## Monitoring

Security violations are logged:

- Blocked commands
- Rate limit violations
- Injection attempts
- Token optimization stats

Check logs for `SECURITY` or `GUARDRAILS` prefixes.
