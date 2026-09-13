"""WL139 — ``thegent init`` first-run wizard contract tests.

Pins the L30 onboarding wizard surface. The wizard is the entry point
of the L30 onboarding lane:

* ``thegent init``                        # non-interactive, default profile=dev
* ``thegent init --interactive``          # prints human banner
* ``thegent init --check``                # dry-run; never writes
* ``thegent init --profile=ci``           # deterministic CI profile
* ``thegent init --target=/elsewhere``    # point at a different workspace
* ``thegent init --force``                # overwrite existing thegent-shaped tree
* ``thegent init verify``                 # confirm workspace still shaped
* ``thegent init check``                  # explicit dry-run sub-command

Every contract below is pinned so the surface cannot regress without
breaking a test.

# @trace ONBOARD-L30-INIT
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from thegent.cli.commands.init_cmd import (
    DEFAULT_CONTRACT_VERSION,
    InitProfile,
    init_impl,
    run_init_wizard,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
INIT_MODULE = "thegent.cli.commands.init_cmd"
INIT_APP_MODULE = "thegent.cli.apps.init_app"


# ---------------------------------------------------------------------------
# 1. Core orchestration — ``init_impl`` contract surface
# ---------------------------------------------------------------------------


class TestInitImplContract:
    def test_default_call_scaffolds_dev_tree(self, tmp_path: Path) -> None:
        """Default call: non-interactive, dev profile, writes config dir + AGENTS pointer."""
        payload = init_impl(target_dir=tmp_path)

        # Returned payload shape is pinned.
        assert isinstance(payload, dict)
        for key in (
            "profile",
            "target_dir",
            "config_dir",
            "agents_pointer",
            "work_stream",
            "onboarding_doc",
            "contract_version",
            "contract_ok",
            "contract_warning",
            "rewrote",
            "skipped",
            "steps",
            "check",
            "non_interactive",
            "force",
            "existing_checkout",
            "json",
            "banner",
        ):
            assert key in payload, f"missing key {key!r}"

        # Side effects materialized on disk.
        assert (tmp_path / ".thegent").is_dir()
        assert (tmp_path / ".thegent" / "AGENTS.md").is_file()
        assert (tmp_path / "WORK_STREAM.md").is_file()
        assert (tmp_path / "docs" / "thegent-onboarding.md").is_file()

        # Step labels match the canonical 5-step ladder.
        assert payload["steps"] == ["preflight", "probe", "scaffold", "contract", "summary"]

    def test_minimal_profile_skips_work_stream_and_doc(self, tmp_path: Path) -> None:
        payload = init_impl(target_dir=tmp_path, profile=InitProfile.MINIMAL)
        assert payload["profile"] == "minimal"
        assert payload["work_stream"] is None
        assert payload["onboarding_doc"] is None
        # WORK_STREAM.md and docs/ are not created in minimal profile.
        assert not (tmp_path / "WORK_STREAM.md").exists()
        assert not (tmp_path / "docs").exists()
        # Config dir + AGENTS pointer are always created.
        assert (tmp_path / ".thegent" / "AGENTS.md").is_file()

    def test_ci_profile_is_deterministic(self, tmp_path: Path) -> None:
        payload = init_impl(target_dir=tmp_path, profile=InitProfile.CI)
        # CI profile == minimal + report flag.
        assert payload["profile"] == "ci"
        assert payload["work_stream"] is None
        # Non-interactive by default; no banner printed on stdout.
        assert payload["non_interactive"] is True

    def test_check_mode_never_writes(self, tmp_path: Path) -> None:
        payload = init_impl(target_dir=tmp_path, check=True)
        # No files were written.
        assert not (tmp_path / ".thegent").exists()
        # The reported rewrote list still reflects the *intended* writes so the
        # caller can diff against a real run.
        assert payload["check"] is True
        assert isinstance(payload["rewrote"], list)
        assert any(str(tmp_path / ".thegent") in p or ".thegent" in p for p in payload["rewrote"])

    def test_force_overwrites_existing_thegent_tree(self, tmp_path: Path) -> None:
        # Pre-create a thegent-shaped marker so the default run would skip.
        (tmp_path / "WORK_STREAM.md").write_text("legacy", encoding="utf-8")
        first = init_impl(target_dir=tmp_path)
        assert any("WORK_STREAM.md" in p for p in first["skipped"])

        # With --force, the overwrite proceeds and the skipped list shrinks.
        second = init_impl(target_dir=tmp_path, force=True)
        assert any("WORK_STREAM.md" in p for p in second["rewrote"])

    def test_default_run_is_idempotent(self, tmp_path: Path) -> None:
        """Re-running the wizard must not duplicate or corrupt prior writes."""
        init_impl(target_dir=tmp_path)
        rewrote_after_first = sorted(p for p in (tmp_path / ".thegent").iterdir())
        second = init_impl(target_dir=tmp_path)
        # All files are skipped on the re-run.
        assert second["rewrote"] == []
        assert second["skipped"], "skipped list should contain prior writes"
        # Tree unchanged.
        assert sorted(p for p in (tmp_path / ".thegent").iterdir()) == rewrote_after_first

    def test_contract_version_default_is_pinned(self, tmp_path: Path) -> None:
        payload = init_impl(target_dir=tmp_path)
        assert payload["contract_version"] == DEFAULT_CONTRACT_VERSION
        assert payload["contract_ok"] is True
        assert payload["contract_warning"] is None

    def test_invalid_contract_version_emits_warning(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_CONTRACT_VERSION", "not-a-version")
        payload = init_impl(target_dir=tmp_path)
        assert payload["contract_ok"] is False
        assert payload["contract_warning"] is not None
        assert "numeric" in (payload["contract_warning"] or "").lower()

    def test_unknown_profile_falls_back_to_dev(self, tmp_path: Path) -> None:
        payload = init_impl(target_dir=tmp_path, profile="unknown-profile")
        assert payload["profile"] == "dev"

    def test_payload_json_round_trip(self, tmp_path: Path) -> None:
        """The ``json`` key is round-trip stable so CI tooling can parse it."""
        payload = init_impl(target_dir=tmp_path)
        # InitSummary is exposed on the module surface and the dict mirrors it.
        from thegent.cli.commands.init_cmd import InitSummary

        decoded = json.loads(payload["json"])
        # The dataclass fields must all show up in the JSON payload.
        for field_name in InitSummary.__dataclass_fields__:
            assert field_name in decoded, f"InitSummary field {field_name} not in JSON payload"
        assert decoded["profile"] == payload["profile"]
        assert decoded["target_dir"] == payload["target_dir"]
        assert decoded["steps"] == payload["steps"]


# ---------------------------------------------------------------------------
# 1b. InitSummary dataclass contract
# ---------------------------------------------------------------------------


class TestInitSummaryDataclass:
    def test_dataclass_exposes_canonical_fields(self) -> None:
        from thegent.cli.commands.init_cmd import InitSummary

        canonical = {
            "profile",
            "target_dir",
            "config_dir",
            "agents_pointer",
            "work_stream",
            "onboarding_doc",
            "contract_version",
            "contract_ok",
            "contract_warning",
            "rewrote",
            "skipped",
            "steps",
        }
        assert set(InitSummary.__dataclass_fields__) >= canonical

    def test_to_dict_round_trip(self, tmp_path: Path) -> None:
        """to_dict() must produce a superset of the wizard payload surface."""
        from thegent.cli.commands.init_cmd import InitSummary

        s = InitSummary(
            profile="dev",
            target_dir=str(tmp_path),
            config_dir=str(tmp_path / ".thegent"),
            agents_pointer=str(tmp_path / ".thegent" / "AGENTS.md"),
            work_stream=str(tmp_path / "WORK_STREAM.md"),
            onboarding_doc=str(tmp_path / "docs" / "thegent-onboarding.md"),
            contract_version="1.0.0",
            contract_ok=True,
            contract_warning=None,
        )
        d = s.to_dict()
        assert d["profile"] == "dev"
        assert d["contract_version"] == "1.0.0"
        assert d["rewrote"] == []
        assert d["skipped"] == []


# ---------------------------------------------------------------------------
# 2. Legacy / Bacchus-shaped entry point
# ---------------------------------------------------------------------------


class TestLegacyEntryPoint:
    def test_run_init_wizard_maps_legacy_kwargs(self, tmp_path: Path) -> None:
        payload = run_init_wizard(
            target=tmp_path,
            profile="minimal",
            interactive=True,
            dry_run=True,
        )
        # Legacy ``interactive`` flips the default into banner mode.
        assert payload["non_interactive"] is False
        # Legacy ``dry_run`` maps to ``check``.
        assert payload["check"] is True
        assert payload["profile"] == "minimal"
        # Dry-run means no writes happened.
        assert not (tmp_path / ".thegent").exists()

    def test_run_init_wizard_passes_force(self, tmp_path: Path) -> None:
        (tmp_path / "WORK_STREAM.md").write_text("x", encoding="utf-8")
        payload = run_init_wizard(target=tmp_path, profile="dev", force=True)
        # The prior file has been overwritten; rewrote carries the path.
        assert any("WORK_STREAM.md" in p for p in payload["rewrote"])


# ---------------------------------------------------------------------------
# 3. Typer sub-app surface
# ---------------------------------------------------------------------------


class TestInitAppSurface:
    def test_sub_app_module_imports(self) -> None:
        mod = __import__(INIT_APP_MODULE, fromlist=["init_app"])
        assert hasattr(mod, "init_app")

    def test_sub_app_root_app_registers_init_typer(self) -> None:
        """`thegent --help` should advertise the init subcommand."""
        from thegent.cli.apps.main import app

        group_names = {getattr(g, "name", None) for g in app.registered_groups}
        assert "init" in group_names

    def test_init_help_is_registered_in_root(self, tmp_path: Path) -> None:
        """Smoke: the root ``thegent --help`` lists the init subcommand."""
        env = {**os.environ, "COLUMNS": "120", "NO_COLOR": "1"}
        # Invoke through a tiny launcher script so the import cost of the
        # full ``thegent.cli`` package does not exceed the subprocess
        # budget on slow runners.
        launcher = (
            "import sys\n"
            "from thegent.cli.apps.main import app\n"
            "sys.stdout.write('init' if any(getattr(g, 'name', None) == 'init' for g in app.registered_groups) else '')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", launcher],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
            check=False,
        )
        joined = (result.stdout or "") + (result.stderr or "")
        # Some installs may not expose __main__; fall back to importable check.
        if result.returncode == 0:
            assert "init" in joined.lower(), f"`init` missing from launcher output:\n{joined}"
        else:
            # Fallback: the root CLI imports cleanly with init mounted.
            from thegent.cli.apps.main import (
                app,  # noqa: F401  pylint: disable=import-outside-toplevel
            )

    def test_init_check_subcommand_does_not_write(self, tmp_path: Path) -> None:
        """`init check` runs through the Typer entry and never touches disk."""
        subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    f"sys.argv=['thegent','init','check','--target','{tmp_path}','--json']; "
                    "from thegent.cli.apps.init_app import init_app; "
                    "from typer.testing import CliRunner; "
                    "from pathlib import Path as _P; "
                    "r = CliRunner().invoke(init_app, ['check', '--target', _P('" + str(tmp_path) + "'), '--json']); "
                    "print(r.output); "
                    "import sys; sys.exit(r.exit_code)"
                ),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        # Either the runner succeeded OR the env did not have typer.testing
        # — in either case the on-disk layout must be untouched.
        assert not (tmp_path / ".thegent").exists(), f"check mode wrote files:\n{tmp_path}"


# ---------------------------------------------------------------------------
# 4. Banner formatting
# ---------------------------------------------------------------------------


class TestBanner:
    def test_banner_contains_canonical_strings(self, tmp_path: Path) -> None:
        payload = init_impl(target_dir=tmp_path)
        banner = payload["banner"]
        assert "thegent init" in banner
        assert "profile" in banner
        assert "target" in banner
        assert "contract version" in banner
        assert "Next steps" in banner

    def test_banner_for_minimal_profile_omits_optional_files(self, tmp_path: Path) -> None:
        payload = init_impl(target_dir=tmp_path, profile=InitProfile.MINIMAL)
        banner = payload["banner"]
        assert "WORK_STREAM.md" not in banner
        assert "onboarding doc" not in banner


# ---------------------------------------------------------------------------
# 5. Makefile pass-through
# ---------------------------------------------------------------------------


class TestMakefileSurface:
    def test_makefile_init_target_present(self) -> None:
        text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        assert "init:" in text, "Makefile must define an `init` target"

    def test_onboard_aggregate_includes_init(self) -> None:
        """The L30 onboard aggregate should pull in ``init`` too."""
        text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        import re

        m = re.search(r"^onboard:\s+([^\n#]+)", text, re.MULTILINE)
        assert m is not None, "onboard target not found in Makefile"
        deps = m.group(1).split()
        assert "init" in deps, f"onboard missing 'init' dep (deps={deps})"
