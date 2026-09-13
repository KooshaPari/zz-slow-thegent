"""Tests for the security.secrets module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


class TestScanSecrets:
    """Tests for scan_secrets function."""

    def test_empty_content_returns_empty_list(self) -> None:
        """Empty content returns no matches."""
        from thegent.security.secrets import scan_secrets

        result = scan_secrets("")
        assert result == []

    def test_github_pat_detected(self) -> None:
        """GitHub Personal Access Token is detected."""
        from thegent.security.secrets import scan_secrets

        content = "ghp_abcdefghij1234567890abcdefghijklmnop"
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "GitHub Personal Access Token"

    def test_github_oauth_token_detected(self) -> None:
        """GitHub OAuth Token is detected."""
        from thegent.security.secrets import scan_secrets

        content = "gho_abcdefghij1234567890abcdefghijklmnop"
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "GitHub OAuth Token"

    def test_slack_token_detected(self) -> None:
        """Slack token is detected."""
        from thegent.security.secrets import scan_secrets

        content = "xoxb-FAKE_TOKEN_FOR_TESTING_ONLY_1234567890AbCdEfGhIj"
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "Slack Token"

    def test_openai_api_key_detected(self) -> None:
        """OpenAI API key is detected."""
        from thegent.security.secrets import scan_secrets

        content = "sk-abcdefghij1234567890abcdefghijklmnopqrstuvwxyzABC"
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "OpenAI API Key"

    def test_openai_project_key_detected(self) -> None:
        """OpenAI Project key is detected."""
        from thegent.security.secrets import scan_secrets

        content = "sk-proj-abcdefghij1234567890abcdefghijklmnopqrstuvwxyzABC"
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "OpenAI Project Key"

    def test_aws_access_key_detected(self) -> None:
        """AWS Access Key ID is detected."""
        from thegent.security.secrets import scan_secrets

        content = "AKIAIOSFODNN7EXAMPLE"
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "AWS Access Key ID"

    def test_private_key_detected(self) -> None:
        """Private key is detected."""
        from thegent.security.secrets import scan_secrets

        content = """-----BEGIN RSA PRIVATE KEY-----
MIIBOgIBAAJBALRiMLAHudeSA2FAoS7JY9h0Xcl36Jq7mRmf9MDSxD3rDmWP
-----END RSA PRIVATE KEY-----"""
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "Private Key"

    def test_hardcoded_password_detected(self) -> None:
        """Hardcoded password is detected."""
        from thegent.security.secrets import scan_secrets

        content = 'password = "supersecretpassword123"'
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "Hardcoded Password"

    def test_api_key_detected(self) -> None:
        """API key pattern is detected."""
        from thegent.security.secrets import scan_secrets

        content = 'api_key = "abcdefghij1234567890ab"'
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["type"] == "API Key"

    def test_multiple_secrets_in_content(self) -> None:
        """Multiple secrets in content are all detected."""
        from thegent.security.secrets import scan_secrets

        content = """
ghp_abcdefghij1234567890abcdefghijklmnop
sk-abcdefghij1234567890abcdefghijklmnop
AKIAIOSFODNN7EXAMPLE
"""
        result = scan_secrets(content)
        assert len(result) == 3

    def test_no_secrets_in_clean_content(self) -> None:
        """Clean content with no secrets returns empty list."""
        from thegent.security.secrets import scan_secrets

        content = "This is just normal code without any secrets in it."
        result = scan_secrets(content)
        assert result == []

    def test_line_number_is_correct(self) -> None:
        """Line numbers are correctly reported."""
        from thegent.security.secrets import scan_secrets

        content = (
            "line one\nline two\nline three with sk-key1234567890abcdefghijk\nline five"
        )
        result = scan_secrets(content)
        assert len(result) == 1
        assert result[0]["line"] == 3

    def test_context_is_provided(self) -> None:
        """Context around match is provided."""
        from thegent.security.secrets import scan_secrets

        content = (
            "some code\nAPI_KEY='sk-abcdefghij1234567890abcdefghijklmnop'\nmore code"
        )
        result = scan_secrets(content)
        assert len(result) == 1
        assert "context" in result[0]


class TestScanSecretsFile:
    """Tests for scan_secrets_file function."""

    def test_reads_file_and_scans(self, tmp_path: Path) -> None:
        """File is read and scanned for secrets."""
        from thegent.security.secrets import scan_secrets_file

        test_file = tmp_path / "test.txt"
        test_file.write_text("ghp_abcdefghij1234567890abcdefghijklmnop")
        result = scan_secrets_file(test_file)
        assert len(result) == 1

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """OSError is raised for missing file."""
        from thegent.security.secrets import scan_secrets_file

        with pytest.raises(OSError):
            scan_secrets_file(tmp_path / "nonexistent.txt")

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """Empty file returns no matches."""
        from thegent.security.secrets import scan_secrets_file

        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        result = scan_secrets_file(test_file)
        assert result == []


class TestRedactSecrets:
    """Tests for redact_secrets function."""

    def test_github_token_is_redacted(self) -> None:
        """GitHub token is redacted."""
        from thegent.security.secrets import redact_secrets

        content = "My token is ghp_abcdefghij1234567890abcdefghijklmnop"
        redacted = redact_secrets(content)
        assert "ghp_" not in redacted
        assert "[REDACTED]" in redacted

    def test_multiple_secrets_redacted(self) -> None:
        """Multiple secrets are all redacted."""
        from thegent.security.secrets import redact_secrets

        content = """
ghp_abcdefghij1234567890abcdefghijklmnop
sk-abcdefghij1234567890abcdefghijklmnop
"""
        redacted = redact_secrets(content)
        assert "ghp_" not in redacted
        assert "sk-" not in redacted

    def test_clean_content_unchanged(self) -> None:
        """Content without secrets is unchanged."""
        from thegent.security.secrets import redact_secrets

        content = "This is clean code."
        redacted = redact_secrets(content)
        assert redacted == content

    def test_empty_content_returns_empty(self) -> None:
        """Empty content returns empty."""
        from thegent.security.secrets import redact_secrets

        assert redact_secrets("") == ""


class TestDetectSecretType:
    """Tests for detect_secret_type function."""

    def test_github_pat_type_detected(self) -> None:
        """GitHub PAT type is correctly identified."""
        from thegent.security.secrets import detect_secret_type

        result = detect_secret_type("ghp_abcdefghij1234567890abcdefghijklmnop")
        assert result == "GitHub Personal Access Token"

    def test_openai_key_type_detected(self) -> None:
        """OpenAI key type is correctly identified."""
        from thegent.security.secrets import detect_secret_type

        result = detect_secret_type("sk-abcdefghij1234567890abcdefghijklmnop")
        assert result == "OpenAI API Key"

    def test_unknown_type_returns_none(self) -> None:
        """Unknown secret type returns None."""
        from thegent.security.secrets import detect_secret_type

        result = detect_secret_type("randomstring123")
        assert result is None

    def test_empty_returns_none(self) -> None:
        """Empty string returns None."""
        from thegent.security.secrets import detect_secret_type

        assert detect_secret_type("") is None


class TestSecretMatch:
    """Tests for SecretMatch class."""

    def test_to_dict(self) -> None:
        """SecretMatch converts to dict correctly."""
        from thegent.security.secrets import SecretMatch

        match = SecretMatch(
            secret_type="GitHub PAT",
            matched_text="ghp_xxx",
            line_number=5,
            context="token = ghp_xxx",
        )
        result = match.to_dict()
        assert result["type"] == "GitHub PAT"
        assert result["line"] == 5
        assert result["context"] == "token = ghp_xxx"

    def test_repr(self) -> None:
        """SecretMatch has readable repr."""
        from thegent.security.secrets import SecretMatch

        match = SecretMatch(
            secret_type="GitHub PAT",
            matched_text="ghp_xxx",
            line_number=5,
        )
        assert "GitHub PAT" in repr(match)
        assert "line=5" in repr(match)


class TestBinaryFallback:
    """Tests for binary fallback behavior."""

    def test_falls_back_to_python_when_binary_not_found(self) -> None:
        """Falls back to Python scanner when binary unavailable."""
        from thegent.security.secrets import scan_secrets

        with patch("thegent.security.secrets._binary_available", return_value=False):
            content = "ghp_abcdefghij1234567890abcdefghijklmnop"
            result = scan_secrets(content)
            assert len(result) == 1
            assert result[0]["type"] == "GitHub Personal Access Token"
