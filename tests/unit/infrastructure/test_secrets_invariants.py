"""Tests for the L27 Secrets-Scan lane — ``scripts/check_secrets_invariants.sh``.

Validates that:

* ``Makefile`` exposes a ``secrets-scan`` target with a docstring and the
  expected body rule.
* ``scripts/check_secrets_invariants.sh`` exists, has valid bash syntax,
  and exits non-zero on a synthetic broken configuration.
* The script's seven canonical checks each pass on the canonical
  workspace (gitleaks.toml valid, trufflehog.yml present, .gitignore
  covers canonical secret-bearing patterns, no live-key leaks).
* The script catches each violation in isolation when run against an
  isolated sandbox.
* The path-based allowlist (``path_is_allowlisted``) function correctly
  permits canonical docs / tests / fixtures / example files and rejects
  secret-bearing source files.

Focused; runs in well under 1 second per case.
"""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_secrets_invariants.sh"
MAKEFILE = REPO_ROOT / "Makefile"
GITLEAKS_CFG = REPO_ROOT / "gitleaks.toml"
TRUFFLEHOG_CFG = REPO_ROOT / "trufflehog.yml"
GITIGNORE = REPO_ROOT / ".gitignore"


# ---------------------------------------------------------------------------
# Makefile surface
# ---------------------------------------------------------------------------


def test_makefile_has_secrets_scan_phony_target() -> None:
    """Makefile must list ``secrets-scan`` in its .PHONY block (multi-line)."""
    content = MAKEFILE.read_text(encoding="utf-8")
    # Collect the .PHONY block (lines starting with .PHONY: plus their
    # backslash-continuations AND the final non-continued line).
    lines = content.splitlines()
    block_lines: list[str] = []
    in_phony = False
    for _idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(".PHONY:"):
            in_phony = True
            block_lines.append(stripped)
            continue
        if in_phony:
            if line.endswith("\\") or line.rstrip().endswith("\\"):
                block_lines.append(line)
                continue
            # Final, un-continued line of the .PHONY block.
            block_lines.append(line)
            break
    block = "\n".join(block_lines)
    assert "secrets-scan" in block, f"secrets-scan missing from .PHONY block:\n{block}"


def test_makefile_secrets_scan_target_has_docstring() -> None:
    """``secrets-scan:`` rule must carry a ``## docstring`` for ``make help``."""
    content = MAKEFILE.read_text(encoding="utf-8")
    body = "\n".join(content.splitlines())
    assert "secrets-scan: ##" in body, "secrets-scan must have a '## ' docstring"


def test_makefile_secrets_scan_target_runs_script() -> None:
    """``secrets-scan`` body must shell out to the invariants script."""
    body_lines = MAKEFILE.read_text(encoding="utf-8").splitlines()
    found_rule = False
    for idx, line in enumerate(body_lines):
        if line.startswith("secrets-scan:"):
            tail = "\n".join(body_lines[idx : idx + 3])
            assert "scripts/check_secrets_invariants.sh" in tail, (
                f"secrets-scan body must invoke scripts/check_secrets_invariants.sh; got: {tail!r}"
            )
            found_rule = True
            break
    assert found_rule, "secrets-scan rule not found"


def test_make_help_shows_secrets_scan() -> None:
    """``make help`` must list the secrets-scan target."""
    result = subprocess.run(
        ["make", "help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "secrets-scan" in result.stdout, f"secrets-scan not listed in: {result.stdout!r}"


# ---------------------------------------------------------------------------
# Script surface
# ---------------------------------------------------------------------------


def test_script_exists_and_is_executable() -> None:
    """Invariants script must exist and be invokable via bash."""
    assert SCRIPT.exists(), f"missing {SCRIPT}"
    assert SCRIPT.is_file(), f"{SCRIPT} is not a file"
    assert shutil.which("bash") is not None, "bash must be on PATH"


def test_script_has_valid_bash_syntax() -> None:
    """Script must pass ``bash -n`` (no parse errors)."""
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"bash -n failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"


def test_script_exits_zero_on_canonical_workspace() -> None:
    """Script must exit 0 on the real workspace (all 7 checks pass)."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"unexpected exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "[make secrets-scan] OK" in result.stdout, f"expected OK marker in stdout: {result.stdout!r}"


def test_script_reports_all_seven_canonical_checks() -> None:
    """The seven canonical checks must all be reported."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    expected = [
        "gitleaks.toml exists",
        "gitleaks.toml has [allowlist] block",
        "gitleaks allowlist covers all 7 canonical placeholders",
        "gitleaks.toml declares >= 5 custom [[rules]]",
        "trufflehog.yml exists",
        ".gitignore excludes canonical secret-bearing artefacts",
        "no live-key pattern leaks",
    ]
    for needle in expected:
        assert needle in result.stdout, f"check missing: {needle}"


def test_gitleaks_config_exists_and_is_well_formed() -> None:
    """gitleaks.toml must exist, be parseable, and have a [[rules]] block."""
    assert GITLEAKS_CFG.exists(), f"missing {GITLEAKS_CFG}"
    content = GITLEAKS_CFG.read_text(encoding="utf-8")
    assert "[[rules]]" in content, "gitleaks.toml must define [[rules]]"
    assert "[allowlist]" in content, "gitleaks.toml must define [allowlist]"


def test_trufflehog_config_exists_and_is_non_empty() -> None:
    """trufflehog.yml must exist and be non-empty."""
    assert TRUFFLEHOG_CFG.exists(), f"missing {TRUFFLEHOG_CFG}"
    assert TRUFFLEHOG_CFG.stat().st_size > 0, "trufflehog.yml must not be empty"


def test_gitignore_covers_canonical_secret_bearing_patterns() -> None:
    """.gitignore must cover the canonical secret-bearing patterns."""
    content = GITIGNORE.read_text(encoding="utf-8")
    required_patterns = [
        ".env",
        ".env.*",
        ".env.example",  # un-ignore via negation
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
        "secrets.yaml",
    ]
    for pattern in required_patterns:
        assert pattern in content, f".gitignore missing pattern: {pattern}"


# ---------------------------------------------------------------------------
# Path-allowlist contract (the most error-prone surface)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "allowed_path",
    [
        ".env.example",
        ".env.template",
        ".env.local.example",
        "docs/SECURITY.md",
        ".github/workflows/security.yml",
        "tests/unit/audit/test_secrets.py",
        "tests/security/test_secrets.py",
        "examples/example.env",
        "fixtures/test.env",
        "tests/README.md",
        "docs/secrets.example.yaml",
        # Suffix-based: only files in src/ that explicitly name tests
        "src/foo/bar_test.py",
        "src/foo/users_test.go",
    ],
)
def test_path_allowlist_permits_canonical_paths(allowed_path: str, tmp_path: Path) -> None:
    """The script's path allowlist must permit canonical allowlist paths."""
    content = SCRIPT.read_text(encoding="utf-8")
    fn_match = "path_is_allowlisted() {"
    idx = content.find(fn_match)
    assert idx > 0, "path_is_allowlisted function not found in script"
    end = content.find("\n}\n", idx)
    assert end > 0, "closing brace of path_is_allowlisted not found"
    # Include the closing '}\n' so the extracted function is syntactically complete.
    fn_body = content[idx : end + 4]
    # Write a temp script that sources the function and invokes it.
    harness = tmp_path / "harness.sh"
    harness.write_text(fn_body + "\n" + f'path_is_allowlisted "{allowed_path}"\n')
    harness.chmod(0o755)
    result = subprocess.run(
        ["bash", str(harness)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"path_is_allowlisted({allowed_path!r}) failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.parametrize(
    "denied_path",
    [
        "src/thegent/foo.py",
        "crates/thegent-hooks/src/security.rs",
        "apps/byteport/backend/api/main.go",
        "config/database.yaml",
        "scripts/run_audit.py",
        "src/main.rs",
    ],
)
def test_path_allowlist_rejects_secret_bearing_paths(denied_path: str, tmp_path: Path) -> None:
    """The script's path allowlist must reject canonical secret-bearing source paths."""
    content = SCRIPT.read_text(encoding="utf-8")
    fn_match = "path_is_allowlisted() {"
    idx = content.find(fn_match)
    assert idx > 0, "path_is_allowlisted function not found in script"
    end = content.find("\n}\n", idx)
    assert end > 0, "closing brace of path_is_allowlisted not found"
    # Include the closing '}\n' so the extracted function is syntactically complete.
    fn_body = content[idx : end + 4]
    harness = tmp_path / "harness.sh"
    harness.write_text(fn_body + "\n" + f'if path_is_allowlisted "{denied_path}"; then exit 1; else exit 0; fi\n')
    harness.chmod(0o755)
    result = subprocess.run(
        ["bash", str(harness)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"path_is_allowlisted({denied_path!r}) should have REJECTED the path"


# ---------------------------------------------------------------------------
# Per-violation isolation (sandboxed fixtures)
# ---------------------------------------------------------------------------


def _run_script_in_sandbox(tmp: Path, source_root: Path) -> subprocess.CompletedProcess[str]:
    """Run a patched copy of the script against an isolated sandbox.

    ``source_root`` is the path the sandbox should treat as ROOT for
    config-file checks (gitleaks/trufflehog/.gitignore).  The script
    is patched so that its internal ROOT variable resolves to this
    path, while still being run with the real working directory.
    """
    sandbox_script = tmp / "check_secrets_invariants.sh"
    script_text = SCRIPT.read_text(encoding="utf-8")
    # Replace the ROOT derivation with a hard-coded path.
    patched = script_text.replace(
        'ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"',
        f'ROOT="{source_root}"',
    )
    sandbox_script.write_text(patched)
    sandbox_script.chmod(0o755)
    return subprocess.run(
        ["bash", str(sandbox_script)],
        cwd=tmp,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """Create a minimal sandbox with valid config files."""
    sandbox_dir = tmp_path / "secretsbox"
    sandbox_dir.mkdir()
    # Minimal valid gitleaks.toml with [allowlist] block and 5+ custom rules.
    sandbox_dir.joinpath("gitleaks.toml").write_text(
        textwrap.dedent(
            """\
            [allowlist]
            description = "test"
            regexTarget = "content"
            regexes = [
                '^agileplus-dev$',
                '^your-.+-here$',
                '^PLACEHOLDER_',
                '^test-secret$',
                '^example-key$',
                '^dummy-token$',
                '^fake-api-key$',
            ]

            [[rules]]
            id = "r1"
            description = "AWS"
            regex = '''AKIA[0-9A-Z]{16}'''

            [[rules]]
            id = "r2"
            description = "GitHub PAT"
            regex = '''ghp_[a-zA-Z0-9]{36,}'''

            [[rules]]
            id = "r3"
            description = "Anthropic"
            regex = '''sk-ant-[a-zA-Z0-9]{32,}'''

            [[rules]]
            id = "r4"
            description = "OpenRouter"
            regex = '''sk-or-v1-[a-f0-9]{32,}'''

            [[rules]]
            id = "r5"
            description = "Generic"
            regex = '''sk-[a-zA-Z0-9]{48}'''
            """
        )
    )
    sandbox_dir.joinpath("trufflehog.yml").write_text(
        textwrap.dedent(
            """\
            detectors:
              - aws
              - github
            """
        )
    )
    sandbox_dir.joinpath(".gitignore").write_text(
        textwrap.dedent(
            """\
            .env
            .env.*
            !.env.example
            *.pem
            *.key
            *.p12
            *.pfx
            secrets.yaml
            """
        )
    )
    return sandbox_dir


def test_script_fails_when_gitleaks_toml_missing(sandbox: Path, tmp_path: Path) -> None:
    """Missing gitleaks.toml must fail the script (non-zero exit)."""
    (sandbox / "gitleaks.toml").unlink()
    result = _run_script_in_sandbox(tmp_path, sandbox)
    assert result.returncode != 0, f"expected failure when gitleaks.toml missing; got: stdout={result.stdout!r}"
    assert "gitleaks.toml exists" in result.stdout, f"missing gitleaks.toml check: {result.stdout!r}"


def test_script_fails_when_gitleaks_allowlist_block_missing(sandbox: Path, tmp_path: Path) -> None:
    """gitleaks.toml without [allowlist] block must fail the script."""
    sandbox.joinpath("gitleaks.toml").write_text(
        textwrap.dedent(
            """\
            [[rules]]
            id = "r1"
            description = "AWS"
            regex = '''AKIA[0-9A-Z]{16}'''

            [[rules]]
            id = "r2"
            description = "GitHub"
            regex = '''ghp_[a-zA-Z0-9]{36,}'''

            [[rules]]
            id = "r3"
            description = "Anthropic"
            regex = '''sk-ant-[a-zA-Z0-9]{32,}'''

            [[rules]]
            id = "r4"
            description = "OpenRouter"
            regex = '''sk-or-v1-[a-f0-9]{32,}'''

            [[rules]]
            id = "r5"
            description = "Generic"
            regex = '''sk-[a-zA-Z0-9]{48}'''
            """
        )
    )
    result = _run_script_in_sandbox(tmp_path, sandbox)
    assert result.returncode != 0, f"expected failure when [allowlist] missing; got: stdout={result.stdout!r}"
    assert "[allowlist]" in result.stdout, f"missing [allowlist] check: {result.stdout!r}"


def test_script_fails_when_trufflehog_yml_missing(sandbox: Path, tmp_path: Path) -> None:
    """Missing trufflehog.yml must fail the script (non-zero exit)."""
    (sandbox / "trufflehog.yml").unlink()
    result = _run_script_in_sandbox(tmp_path, sandbox)
    assert result.returncode != 0, f"expected failure when trufflehog.yml missing; got: stdout={result.stdout!r}"
    assert "trufflehog.yml" in result.stdout, f"missing trufflehog.yml check: {result.stdout!r}"


def test_script_fails_when_gitignore_missing_patterns(sandbox: Path, tmp_path: Path) -> None:
    """.gitignore without required secret-bearing patterns must fail."""
    sandbox.joinpath(".gitignore").write_text(
        textwrap.dedent(
            """\
            .env
            .env.*
            !.env.example
            """
        )
    )
    result = _run_script_in_sandbox(tmp_path, sandbox)
    assert result.returncode != 0, f"expected failure when .gitignore incomplete; got: stdout={result.stdout!r}"
    assert ".gitignore" in result.stdout, f"missing .gitignore check: {result.stdout!r}"


def test_script_passes_when_sandbox_is_valid(sandbox: Path, tmp_path: Path) -> None:
    """A minimal-but-valid sandbox must pass all 7 checks."""
    result = _run_script_in_sandbox(tmp_path, sandbox)
    assert result.returncode == 0, f"valid sandbox failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "[make secrets-scan] OK" in result.stdout, f"expected OK marker; got: {result.stdout!r}"


# ---------------------------------------------------------------------------
# CI gate integration — pins the workflow file that runs the script
# on every push + PR so violations actually break the build.
# ---------------------------------------------------------------------------

CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "secrets-scan.yml"


def test_ci_workflow_exists() -> None:
    """``.github/workflows/secrets-scan.yml`` must exist (the L27 CI gate)."""
    assert CI_WORKFLOW.exists(), f"missing CI workflow: {CI_WORKFLOW}"
    content = CI_WORKFLOW.read_text(encoding="utf-8")
    assert content.startswith("name:"), "CI workflow must declare a name"
    assert "Secrets Scan" in content, "CI workflow name should reference Secrets Scan"


def test_ci_workflow_runs_the_invariants_script() -> None:
    """CI workflow must invoke ``scripts/check_secrets_invariants.sh``."""
    content = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "check_secrets_invariants.sh" in content, (
        "CI workflow must run the invariants script so violations break the build"
    )
    assert "make secrets-scan" in content, (
        "CI workflow must also exercise the Makefile target so the L30 onboarding surface is wired through CI"
    )


def test_ci_workflow_triggers_on_push_and_pull_request() -> None:
    """CI workflow must run on push and pull_request events."""
    content = CI_WORKFLOW.read_text(encoding="utf-8")
    # Check the on: block contains both triggers (multi-line YAML).
    assert "push:" in content and "pull_request:" in content, (
        "CI workflow must trigger on push and pull_request so the L27 static check runs on every commit"
    )


def test_ci_workflow_uses_minimal_permissions() -> None:
    """CI workflow must request only ``contents: read`` (no write scopes)."""
    import yaml  # type: ignore[import-not-found]

    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    perms = (data or {}).get("permissions") or {}
    assert perms == {"contents": "read"}, f"CI workflow permissions drifted from least-privilege; got {perms!r}"
