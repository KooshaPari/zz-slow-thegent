"""Secrets scanning and management for thegent."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SECRET_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"github_pat_[a-zA-Z0-9_]{22,255}", "GitHub Fine-Grained PAT"),
    (r"xox[baprs]-[a-zA-Z0-9]{10,48}", "Slack Token"),
    (r"sk-[a-zA-Z0-9]{32,64}", "OpenAI API Key"),
    (r"sk-proj-[a-zA-Z0-9_-]{32,100}", "OpenAI Project Key"),
    (r"pk_live_[a-zA-Z0-9]{24,32}", "Stripe Live Key"),
    (r"pk_test_[a-zA-Z0-9]{24,32}", "Stripe Test Key"),
    (r"sq0[a-z]{3}-[a-zA-Z0-9_-]{22,43}", "Square Access Token"),
    (r"amzn_[a-zA-Z0-9]{20}", "AWS Access Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"[a-zA-Z0-9+/]{40,}=*", "Generic Secret (Base64)"),
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Private Key"),
    (r"password\s*[=:]\s*['\"][^'\"]{8,}['\"]", "Hardcoded Password"),
    (r"api[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9_-]{16,}['\"]", "API Key"),
    (r"secret[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9_-]{16,}['\"]", "Secret Key"),
    (r"bearer\s+[a-zA-Z0-9_-]{20,}", "Bearer Token"),
    (r"token[_-]?secret\s*[=:]\s*['\"][a-zA-Z0-9_-]{16,}['\"]", "Token Secret"),
]

BINARY_PATH = Path(__file__).parent / "scan-secrets"


class SecretMatch:
    """Represents a matched secret in content."""

    def __init__(
        self,
        secret_type: str,
        matched_text: str,
        line_number: int,
        context: str = "",
    ) -> None:
        """Initialize a secret match.

        Args:
            secret_type: Type of secret detected.
            matched_text: The actual matched text (should be redacted in output).
            line_number: Line number where match was found.
            context: Surrounding context text.
        """
        self.secret_type = secret_type
        self.matched_text = matched_text
        self.line_number = line_number
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with secret match data.
        """
        return {
            "type": self.secret_type,
            "line": self.line_number,
            "context": self.context,
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"SecretMatch(type={self.secret_type}, line={self.line_number})"


def _compile_patterns() -> list[tuple[re.Pattern[str], str]]:
    """Compile regex patterns for secret detection.

    Returns:
        List of (compiled_pattern, secret_type) tuples.
    """
    compiled = []
    for pattern, secret_type in SECRET_PATTERNS:
        try:
            compiled.append((re.compile(pattern, re.IGNORECASE), secret_type))
        except re.error as e:
            logger.warning(f"Invalid secret pattern '{pattern}': {e}")
    return compiled


def scan_secrets(content: str) -> list[dict[str, Any]]:
    """Scan content for secrets.

    Args:
        content: Text content to scan.

    Returns:
        List of secret match dictionaries.
    """
    if not content:
        return []

    if _binary_available():
        return _scan_with_binary(content)

    return _scan_with_python(content)


def _binary_available() -> bool:
    """Check if the scan-secrets binary is available.

    Returns:
        True if binary exists and is executable.
    """
    if not BINARY_PATH.exists():
        return False

    try:
        result = subprocess.run(
            [str(BINARY_PATH), "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _scan_with_binary(content: str) -> list[dict[str, Any]]:
    """Scan using the binary scanner.

    Args:
        content: Content to scan.

    Returns:
        List of secret matches.
    """
    try:
        result = subprocess.run(
            [str(BINARY_PATH), "scan-secrets", "--stdin"],
            input=content.encode(),
            capture_output=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(f"Binary scan failed with code {result.returncode}")
            return _scan_with_python(content)

        try:
            import json

            data = json.loads(result.stdout.decode())
            return data.get("matches", [])
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Binary returned non-JSON output, falling back to Python")
            return _scan_with_python(content)

    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning(f"Binary scan error: {e}, falling back to Python")
        return _scan_with_python(content)


def _scan_with_python(content: str) -> list[dict[str, Any]]:
    """Scan using pure Python regex.

    Args:
        content: Content to scan.

    Returns:
        List of secret matches.
    """
    matches = []
    lines = content.split("\n")
    compiled_patterns = _compile_patterns()

    for line_num, line in enumerate(lines, start=1):
        for pattern, secret_type in compiled_patterns:
            match = pattern.search(line)
            if match:
                matches.append(
                    {
                        "type": secret_type,
                        "line": line_num,
                        "context": line[:80],
                    }
                )

    return matches


def scan_secrets_file(file_path: Path) -> list[dict[str, Any]]:
    """Scan a file for secrets.

    Args:
        file_path: Path to file to scan.

    Returns:
        List of secret match dictionaries.

    Raises:
        OSError: If file cannot be read.
    """
    if not file_path.exists():
        raise OSError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8", errors="replace")
    return scan_secrets(content)


def redact_secrets(content: str) -> str:
    """Redact secrets in content for safe logging/display.

    Args:
        content: Content to redact.

    Returns:
        Content with secrets replaced by [REDACTED].
    """
    if not content:
        return content

    redacted = content
    compiled_patterns = _compile_patterns()

    for pattern, _ in compiled_patterns:
        redacted = pattern.sub("[REDACTED]", redacted)

    return redacted


def detect_secret_type(secret_candidate: str) -> str | None:
    """Detect the type of a secret candidate.

    Args:
        secret_candidate: Potential secret string.

    Returns:
        Secret type name or None if not recognized.
    """
    if not secret_candidate:
        return None

    for pattern, secret_type in SECRET_PATTERNS:
        if re.search(pattern, secret_candidate, re.IGNORECASE):
            return secret_type

    return None


__all__ = [
    "SecretMatch",
    "detect_secret_type",
    "redact_secrets",
    "scan_secrets",
    "scan_secrets_file",
]
