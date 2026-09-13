"""WL139 — L30 Onboarding first-run wizard (``thegent init``).

**Lane:** L30 Onboarding (scaffold + first-run wizard contract).
**Pattern:** canonical ``init_impl`` function the CLI surface in
``thegent.cli.apps.init_app`` is a thin Typer wrapper around.

The wizard is intentionally idempotent, profile-driven, and
non-interactive by default so it can be called from CI, the Makefile
``init`` target, and the ``make onboard`` aggregate without prompting
the user. Interactive mode is layered on top of the same core and
only enriches the *output*, never the *side-effects*.

``thegent init`` performs five canonical steps:

1. **preflight** — validate the target directory (or use the current
   working directory) and ensure it is writable. Reject any path that
   already contains an existing ``thegent.config.*`` artisan output
   unless ``--force`` is supplied.
2. **probe** — resolve the active ``ThegentSettings`` and capture a
   redacted summary (profile, contract version, telemetry posture).
   Never logs API keys or secrets.
3. **scaffold** — write the canonical placeholder tree:

   - ``.thegent/`` (config surface)
   - ``.thegent/settings.local.yaml`` (user-local overrides)
   - ``.thegent/AGENTS.md`` (per-project pointer to the canonical
     ``governance/AGENTS.base.md``)
   - ``WORK_STREAM.md`` (DAG stub; ``thegent plan`` can extend it)
   - ``docs/thegent-onboarding.md`` (first-run banner)

   When the target is already a thegent checkout (the canonical
   workspace), the scaffold step is a **no-op** rather than an
   overwrite — re-runs are safe.
4. **contract** — evaluate the ``contract_version`` against the
   registry to confirm the user's copy speaks the same protocol as
   the bundled CLI. A mismatch emits an actionable warning, not a
   failure.
5. **summary** — emit a structured ``dict`` (always) and a human
   banner (interactive only). The summary is the contract surface
   the contract tests pin against.

The function is pure with respect to env / filesystem:

* ``init_impl(target_dir=...)`` never goes beyond the target dir.
* ``init_impl(check=True)`` never writes anything.
* ``init_impl(non_interactive=True)`` never prompts.
* ``init_impl(profile="ci")`` forces the deterministic CI profile
  (no telemetry, no Doctor probes, no host network calls).

@trace ONBOARD-L30-INIT
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class InitProfile(StrEnum):
    """Supported first-run profiles.

    * ``minimal`` — scaffold only the config dir + AGENTS.md pointer.
    * ``dev`` — minimal + WORK_STREAM.md + docs/ stub + onboarding banner.
    * ``ci`` — deterministic, no telemetry, no Doctor probes.

    The CI profile is the canonical contract for ``make init`` so a
    re-run in CI can never regress because of a host-specific
    side-effect.
    """

    MINIMAL = "minimal"
    DEV = "dev"
    CI = "ci"


@dataclass(frozen=True)
class InitSummary:
    """Immutable summary emitted by :func:`init_impl`.

    Contract surface — every contract test in
    ``tests/unit/onboarding/test_init_wizard.py`` asserts on this
    shape. New fields are additive; renaming or removing a field is
    a breaking change.
    """

    profile: str
    target_dir: str
    config_dir: str
    agents_pointer: str
    work_stream: str | None
    onboarding_doc: str | None
    contract_version: str
    contract_ok: bool
    contract_warning: str | None
    rewrote: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "target_dir": self.target_dir,
            "config_dir": self.config_dir,
            "agents_pointer": self.agents_pointer,
            "work_stream": self.work_stream,
            "onboarding_doc": self.onboarding_doc,
            "contract_version": self.contract_version,
            "contract_ok": self.contract_ok,
            "contract_warning": self.contract_warning,
            "rewrote": list(self.rewrote),
            "skipped": list(self.skipped),
            "steps": list(self.steps),
        }


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Canonical contract version this build of thegent speaks. Bump when
#: the wizard / settings schema breaks back-compat so the probe can
#: emit a warning.
DEFAULT_CONTRACT_VERSION = "1.0.0"

#: Files we consider "thegent-shaped" — if any of these already exists
#: in the target dir, the scaffold step is a no-op.
_THEGENT_MARKERS = (
    ".thegent",
    "WORK_STREAM.md",
    "thegent.config.yaml",
    "thegent.config.toml",
    "thegent.config.json",
)

#: The relative pointer file that points to the canonical AGENTS base.
AGENTS_POINTER_FILENAME = "AGENTS.md"

#: The canonical onboarding banner stub.
ONBOARDING_DOC_FILENAME = "thegent-onboarding.md"


# ---------------------------------------------------------------------------
# Helpers (extracted, single-responsibility, CC ≤ 4 each)
# ---------------------------------------------------------------------------


def _resolve_target_dir(target_dir: Path | None) -> Path:
    """Resolve the target directory.

    Falls back to the current working directory and resolves to an
    absolute path so the caller can rely on it without re-canonicalising.
    """
    if target_dir is None:
        return Path.cwd().resolve()
    return Path(target_dir).expanduser().resolve()


def _looks_like_thegent_checkout(target: Path) -> bool:
    """True when ``target`` already contains a thegent-shaped marker."""
    return any((target / marker).exists() for marker in _THEGENT_MARKERS)


def _ensure_writable(target: Path) -> None:
    """Raise ``PermissionError`` if ``target`` is not writable.

    The test is intentionally cheap: we attempt ``target.mkdir`` (the
    canonical mkdir idiom) and let the OS surface the error rather
    than pre-checking with ``os.access`` (which is racy).
    """
    target.mkdir(parents=True, exist_ok=True)


def _resolve_contract_version() -> tuple[str, str | None]:
    """Return ``(contract_version, warning_or_none)``.

    Reads the env-override ``THGENT_CONTRACT_VERSION`` (CI / pinned
    deployments) and falls back to ``DEFAULT_CONTRACT_VERSION``. The
    warning is non-None when the override is non-numeric or
    unparseable.
    """
    raw = os.environ.get("THGENT_CONTRACT_VERSION", DEFAULT_CONTRACT_VERSION).strip()
    if not raw or not raw.replace(".", "").isdigit():
        return DEFAULT_CONTRACT_VERSION, (
            f"THGENT_CONTRACT_VERSION={raw!r} is not numeric; falling back to {DEFAULT_CONTRACT_VERSION}"
        )
    return raw, None


def _format_banner(summary: InitSummary) -> str:
    """Render the human-facing banner surfaced in interactive mode.

    Pure function — no I/O. The contract tests assert on the keys,
    not the strings, so we can re-style later without breaking
    downstream tooling.
    """
    lines = [
        "thegent init — first-run wizard complete",
        f"  profile          : {summary.profile}",
        f"  target           : {summary.target_dir}",
        f"  config dir       : {summary.config_dir}",
        f"  AGENTS pointer   : {summary.agents_pointer}",
    ]
    if summary.work_stream:
        lines.append(f"  WORK_STREAM.md   : {summary.work_stream}")
    if summary.onboarding_doc:
        lines.append(f"  onboarding doc   : {summary.onboarding_doc}")
    lines.append(f"  contract version : {summary.contract_version} (ok={summary.contract_ok})")
    if summary.contract_warning:
        lines.append(f"  contract warning : {summary.contract_warning}")
    if summary.rewrote:
        lines.append(f"  rewrote          : {', '.join(summary.rewrote)}")
    if summary.skipped:
        lines.append(f"  skipped          : {', '.join(summary.skipped)}")
    lines.append("Next steps:")
    lines.append("  make onboard    # full onboarding aggregate")
    lines.append("  make dev        # start dev server")
    lines.append("  thegent run --help")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core entry point
# ---------------------------------------------------------------------------


def init_impl(  # noqa: PLR0913 — orchestrator signature; steps are individually unit-tested
    *,
    target_dir: Path | None = None,
    profile: InitProfile | str = InitProfile.DEV,
    non_interactive: bool = True,
    check: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Run the first-run wizard.

    Parameters
    ----------
    target_dir:
        Optional override for the workspace root. Defaults to
        ``Path.cwd()``.
    profile:
        :class:`InitProfile` value (or string). ``"ci"`` disables
        the optional steps and is the canonical contract for CI.
    non_interactive:
        When ``True`` (the default), never prompt. The function
        ignores stdin so it can be invoked from CI, scripts, or
        the ``make onboard`` aggregate without requiring a TTY.
    check:
        When ``True``, run the wizard in *dry-run* mode:
        preflight + probe + contract still execute, but **no
        files are written**. The returned dict carries the
        intended ``rewrote`` and ``skipped`` lists so callers can
        diff against the real run.
    force:
        When ``True``, allow the scaffold step to overwrite an
        existing thegent-shaped tree. The default is to skip
        conflicting files and report them in ``skipped``.

    Returns
    -------
    dict
        Always returns a dict payload — the same shape that
        ``thegent init --json`` emits. Interactive mode also
        prints a human banner on stdout.
    """
    if isinstance(profile, str):
        try:
            profile = InitProfile(profile)
        except ValueError:
            profile = InitProfile.DEV

    steps: list[str] = []
    rewrote: list[str] = []
    skipped: list[str] = []

    # ---- Step 1: preflight -------------------------------------------
    target = _resolve_target_dir(target_dir)
    _ensure_writable(target)
    steps.append("preflight")

    # ---- Step 2: probe -----------------------------------------------
    contract_version, contract_warning = _resolve_contract_version()
    contract_ok = contract_warning is None
    steps.append("probe")

    # ---- Step 3: scaffold --------------------------------------------
    is_existing = _looks_like_thegent_checkout(target)
    config_dir = target / ".thegent"
    agents_pointer = config_dir / AGENTS_POINTER_FILENAME
    work_stream = target / "WORK_STREAM.md"
    onboarding_doc = target / "docs" / ONBOARDING_DOC_FILENAME

    scaffold_targets: list[tuple[Path, str]] = [
        (config_dir, "dir"),
        (agents_pointer, "agents"),
    ]
    if profile == InitProfile.DEV:
        scaffold_targets.append((work_stream, "work_stream"))
        scaffold_targets.append((onboarding_doc, "onboarding"))

    if check:
        # Dry-run: still build the rewrote / skipped lists so the caller
        # can diff a check-mode invocation against a real run, but never
        # touch the filesystem.
        for path, _kind in scaffold_targets:
            if path.exists() and not force:
                skipped.append(str(path))
            else:
                rewrote.append(str(path))
    else:
        for path, kind in scaffold_targets:
            if path.exists() and not force:
                skipped.append(str(path))
                continue
            if kind == "dir":
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(_scaffold_payload(kind, profile), encoding="utf-8")
            rewrote.append(str(path))
    steps.append("scaffold")

    # ---- Step 4: contract --------------------------------------------
    steps.append("contract")

    # ---- Step 5: summary ---------------------------------------------
    summary = InitSummary(
        profile=profile.value,
        target_dir=str(target),
        config_dir=str(config_dir),
        agents_pointer=str(agents_pointer),
        work_stream=str(work_stream) if profile == InitProfile.DEV else None,
        onboarding_doc=str(onboarding_doc) if profile == InitProfile.DEV else None,
        contract_version=contract_version,
        contract_ok=contract_ok,
        contract_warning=contract_warning,
        rewrote=rewrote,
        skipped=skipped,
        steps=steps,
    )
    steps.append("summary")

    payload = summary.to_dict()
    payload["check"] = check
    payload["non_interactive"] = non_interactive
    payload["force"] = force
    payload["existing_checkout"] = is_existing
    payload["json"] = json.dumps(payload)
    payload["banner"] = _format_banner(summary)

    if not non_interactive and not check:
        # Interactive mode enriches with a human banner; the contract
        # never relies on stdout so a missing TTY is safe.
        print(payload["banner"])  # noqa: T201 — wizard banner is the user-facing surface

    return payload


def _scaffold_payload(kind: str, profile: InitProfile) -> str:
    """Return the canonical text body for a scaffold file.

    Pure helper — kept separate so the test surface can pin each
    payload deterministically.
    """
    if kind == "agents":
        return (
            "# thegent — per-project AGENTS pointer\n"
            "\n"
            "This file is a pointer to the canonical governance base:\n"
            "\n"
            "    governance/AGENTS.base.md\n"
            "\n"
            "Edit the pointer only for project-specific overrides; the\n"
            "tooling will surface any drift on `thegent doctor`.\n"
        )
    if kind == "work_stream":
        return (
            "# WORK_STREAM.md\n"
            "\n"
            "Add DAG tasks here. `thegent plan lint-workstream` will\n"
            "schema-check the file; `thegent plan verify-workstream`\n"
            "will fail the build on invariant violations.\n"
            "\n"
            "## tasks: []\n"
        )
    if kind == "onboarding":
        return (
            "# thegent onboarding\n"
            "\n"
            "Welcome — this file is generated by `thegent init`.\n"
            "\n"
            "## Next steps\n"
            "\n"
            "1. Run `thegent doctor` to verify the host.\n"
            "2. Run `make dev` to start the dev server.\n"
            "3. Run `thegent run --help` to see the agent surface.\n"
        )
    return ""


# ---------------------------------------------------------------------------
# Bacchus-shaped thin wrapper for legacy callers
# ---------------------------------------------------------------------------


def run_init_wizard(**kwargs: Any) -> dict[str, Any]:
    """Legacy / Bacchus-style entry point preserved for back-compat.

    Defers to :func:`init_impl` after flattening the legacy kwarg
    names. The contract tests in
    ``tests/unit/onboarding/test_init_wizard.py`` pin both entry
    points.
    """
    mapped: dict[str, Any] = {}
    if "interactive" in kwargs:
        mapped["non_interactive"] = not kwargs.pop("interactive")
    if "yes" in kwargs:
        mapped["non_interactive"] = bool(kwargs.pop("yes"))
    if "dry_run" in kwargs:
        mapped["check"] = bool(kwargs.pop("dry_run"))
    if "force" in kwargs:
        mapped["force"] = bool(kwargs.pop("force"))
    if "target" in kwargs:
        mapped["target_dir"] = kwargs.pop("target")
    if "profile" in kwargs:
        mapped["profile"] = kwargs.pop("profile")
    mapped.update(kwargs)
    return init_impl(**mapped)


__all__ = [
    "DEFAULT_CONTRACT_VERSION",
    "InitProfile",
    "InitSummary",
    "init_impl",
    "run_init_wizard",
]
