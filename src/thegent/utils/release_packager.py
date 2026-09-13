"""WP-12009: Automation of release docs packaging.

Compiles PRD, WBS, and test artifacts into a deterministic release package.
"""

import hashlib
import json
from pathlib import Path
from typing import Any


class ReleasePackager:
    """Packager for system release documentation and artifacts."""

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root
        self.doc_paths = [
            "docs/docset/thegent-prd-final.md",
            "docs/docset/thegent-wbs-final.md",
            "docs/docset/thegent-wbs-phase10-12.md",
            "docs/guides/OPERATIONAL_LEARNING.md",
            "docs/reports/PHASE_10_12_CLOSURE.md",
            "docs/reports/PHASE_13_PROGRESS_REPORT.md",
            "docs/reports/PHASE_14_PROGRESS_REPORT.md",
            "docs/reports/PHASE_15_PROGRESS_REPORT.md",
            "docs/reports/FINAL_CLOSURE_NOTE.md",
            "docs/research/ADR-013-POLICY-FEDERATION.md",
            "docs/research/ADR-014-AUTONOMOUS-LEARNING.md",
            "docs/research/ADR-015-ENTERPRISE-COMPLIANCE.md",
            "docs/research/IN_DEPTH_TOOLING_AUDIT_2026.md",
            "docs/research/TEAMMATES_RESEARCH_AND_PLAN.md",
        ]

    def compile_package(self, version: str) -> dict[str, Any]:
        """Compile all required documents and generate checksums."""
        manifest: dict[str, Any] = {"version": version, "artifacts": []}

        for path_str in self.doc_paths:
            path = self.root / path_str
            if path.exists():
                content = path.read_text(encoding="utf-8")
                checksum = hashlib.sha256(content.encode()).hexdigest()
                manifest["artifacts"].append({"path": path_str, "checksum": checksum, "size_bytes": len(content)})
            else:
                manifest["artifacts"].append({"path": path_str, "status": "missing"})

        # Deterministic checksum for the entire package
        manifest_json = json.dumps(manifest, sort_keys=True)
        manifest["package_checksum"] = hashlib.sha256(manifest_json.encode()).hexdigest()

        return manifest
