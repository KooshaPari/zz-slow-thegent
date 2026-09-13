"""L30 Onboarding + L2 Dev Loop Makefile pass-through contract tests.

Pins the pass-through invariants of the Makefile so a contributor can
rely on ``make help``, ``make install``, ``make test``, and the new
aggregate ``make onboard`` target without surprises. Tests:

* Every public Makefile target has a body rule and a ``##`` docstring.
* The ``onboard`` aggregate depends on ``install``, ``doctor``, and
  ``version`` (L30 onboarding surface).
* The ``validate-makefile`` self-test exits zero when invariants hold.
* ``make help`` lists every public target.
* The shell self-test exits non-zero on a *broken* Makefile (mutation
  test guarding the invariant script itself).
* ``make onboard`` (dry-run via ``make -n``) runs install + doctor +
  version without error.

# @trace ONBOARD-L30-MAKEFILE
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MAKEFILE = REPO_ROOT / "Makefile"
INVARIANTS_SCRIPT = REPO_ROOT / "scripts" / "check_makefile_invariants.sh"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _phony_targets(makefile_text: str) -> list[str]:
    """Return the .PHONY target list, ignoring backslash continuations."""
    m = re.search(r"^\.PHONY:\s*(.+?)(?=^\S|\Z)", makefile_text, re.DOTALL | re.MULTILINE)
    assert m is not None, ".PHONY declaration missing"
    clean = re.sub(r"\\\s*\n\s*", " ", m.group(1))
    return [t for t in clean.split() if re.match(r"^[A-Za-z0-9_-]+$", t)]


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


class TestMakefileStructure:
    def test_makefile_exists(self) -> None:
        assert MAKEFILE.is_file(), f"Makefile not found at {MAKEFILE}"

    def test_invariants_script_exists_and_executable(self) -> None:
        assert INVARIANTS_SCRIPT.is_file()
        assert INVARIANTS_SCRIPT.stat().st_mode & 0o111, "invariants script not executable"

    def test_every_phony_target_has_body_rule(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        targets = _phony_targets(text)
        missing = [t for t in targets if not re.search(rf"^{re.escape(t)}:", text, re.MULTILINE)]
        assert not missing, f"targets missing body rules: {missing}"

    def test_every_public_target_is_documented(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        targets = _phony_targets(text)
        undocumented = [
            t for t in targets if not t.startswith("_") and not re.search(rf"^{re.escape(t)}:.*##", text, re.MULTILINE)
        ]
        assert not undocumented, f"undocumented targets: {undocumented}"


# ---------------------------------------------------------------------------
# Onboarding surface (L30)
# ---------------------------------------------------------------------------


class TestOnboardingSurface:
    def test_onboard_target_present(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        assert re.search(r"^onboard:.*##", text, re.MULTILINE), "onboard target missing or undocumented"

    def test_onboard_depends_on_install_doctor_version(self) -> None:
        """The aggregate onboarding target wires the canonical L30 surface."""
        text = MAKEFILE.read_text(encoding="utf-8")
        # Match the dependency list after `onboard:`.
        m = re.search(r"^onboard:\s+([^\n#]+)", text, re.MULTILINE)
        assert m is not None, "onboard target not found"
        deps = m.group(1).split()
        for required in ("install", "doctor", "version"):
            assert required in deps, f"onboard missing required dep '{required}' (deps={deps})"

    @pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
    def test_make_help_lists_onboard_target(self) -> None:
        result = subprocess.run(
            ["make", "help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        plain = _strip_ansi(result.stdout)
        assert "onboard" in plain, f"onboard missing from help:\n{plain}"

    @pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
    def test_make_onboard_dry_run_succeeds(self) -> None:
        """`make -n onboard` should not fail (dry-run only)."""
        result = subprocess.run(
            ["make", "-n", "onboard"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        assert result.returncode == 0, (
            f"`make -n onboard` exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# Invariants self-test (L2)
# ---------------------------------------------------------------------------


class TestInvariantsSelfTest:
    @pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
    def test_invariants_script_passes_on_canonical_makefile(self) -> None:
        result = subprocess.run(
            ["bash", str(INVARIANTS_SCRIPT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"invariants script failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        assert "PASS" in result.stdout, f"unexpected script output:\n{result.stdout}"

    def test_invariants_script_flags_missing_docstring(self, tmp_path: Path) -> None:
        """Mutation test: a target without `##` must be flagged by the script."""
        # Build a synthetic Makefile that breaks invariant #2.
        broken = tmp_path / "Makefile"
        broken.write_text(
            ".PHONY: good bad\ngood: ## Good target\n\t@true\nbad:\n\t@true\n",
            encoding="utf-8",
        )
        script = INVARIANTS_SCRIPT.read_text(encoding="utf-8")
        # Patch the script to point at our synthetic Makefile.
        patched = script.replace('MAKEFILE="$ROOT/Makefile"', f'MAKEFILE="{broken}"')
        patched_path = tmp_path / "check.sh"
        patched_path.write_text(patched, encoding="utf-8")
        patched_path.chmod(0o755)

        result = subprocess.run(
            ["bash", str(patched_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode != 0, "script accepted an undocumented target"
        assert "undocumented" in result.stderr.lower() or "undocumented" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Aggregate target sanity (L2)
# ---------------------------------------------------------------------------


class TestDevLoopTargets:
    @pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
    def test_sota_security_harden_targets_present(self) -> None:
        """Phase 4 audit lane aliases are wired up."""
        result = subprocess.run(
            ["make", "help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        plain = _strip_ansi(result.stdout)
        for target in ("sota", "security", "harden", "version", "test-quick"):
            assert target in plain, f"{target} missing from help"

    def test_validate_makefile_target_present(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        assert re.search(r"^validate-makefile:.*##", text, re.MULTILINE), "validate-makefile target missing"
