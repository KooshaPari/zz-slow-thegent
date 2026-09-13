"""Tests for thegent.mesh.merge — SmartMerge conflict resolution (Phase 7).

FR traceability:
  TGNT-P7.3 (import union auto-resolve)
  TGNT-P7.4 (JSON/YAML structural merge)
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest import mock

import orjson as json
import pytest

from thegent.mesh.merge import SmartMerge

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sm(tmp_path: Path) -> SmartMerge:
    """SmartMerge instance rooted in a temporary directory."""
    return SmartMerge(tmp_path)


# ---------------------------------------------------------------------------
# TGNT-P7.3: resolve_imports — Python import union
# ---------------------------------------------------------------------------


class TestResolveImportsPython:
    """Import union auto-resolution for Python files. @trace TGNT-P7.3"""

    def test_union_of_disjoint_imports(self, sm: SmartMerge):
        """Disjoint Python imports are merged into a sorted union. @trace TGNT-P7.3"""
        content_a = "import os\nx = 1"
        content_b = "import sys\ny = 2"
        result = sm.resolve_imports(content_a, content_b, language="python")
        lines = result.splitlines()
        # Both imports present and sorted
        assert "import os" in lines
        assert "import sys" in lines
        assert lines.index("import os") < lines.index("import sys")

    def test_duplicate_imports_deduplicated(self, sm: SmartMerge):
        """Duplicate imports appear only once. @trace TGNT-P7.3"""
        content_a = "import os\nimport json\nx = 1"
        content_b = "import os\nimport sys\ny = 2"
        result = sm.resolve_imports(content_a, content_b, language="python")
        assert result.count("import os") == 1

    def test_from_imports_handled(self, sm: SmartMerge):
        """'from X import Y' lines are recognized as imports. @trace TGNT-P7.3"""
        content_a = "from pathlib import Path\nx = 1"
        content_b = "from os import getcwd\ny = 2"
        result = sm.resolve_imports(content_a, content_b, language="python")
        assert "from os import getcwd" in result
        assert "from pathlib import Path" in result

    def test_non_import_lines_preserved(self, sm: SmartMerge):
        """Non-import lines from both contents are present. @trace TGNT-P7.3"""
        content_a = "import os\nx = 1"
        content_b = "import sys\ny = 2"
        result = sm.resolve_imports(content_a, content_b, language="python")
        assert "x = 1" in result
        assert "y = 2" in result

    def test_imports_sorted_alphabetically(self, sm: SmartMerge):
        """Import lines are sorted alphabetically. @trace TGNT-P7.3"""
        content_a = "import zlib\nimport abc"
        content_b = "import json"
        result = sm.resolve_imports(content_a, content_b, language="python")
        import_lines = [l for l in result.splitlines() if l.startswith("import ")]
        assert import_lines == sorted(import_lines)

    def test_empty_contents(self, sm: SmartMerge):
        """Empty inputs produce an empty-ish result without error. @trace TGNT-P7.3"""
        result = sm.resolve_imports("", "", language="python")
        # Should not raise; result is a string (possibly just a blank line separator)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# TGNT-P7.3: resolve_imports — JavaScript/TypeScript import union
# ---------------------------------------------------------------------------


class TestResolveImportsJavaScript:
    """Import union auto-resolution for JS/TS files. @trace TGNT-P7.3"""

    def test_js_import_statements(self, sm: SmartMerge):
        """ES module import lines are recognized. @trace TGNT-P7.3"""
        content_a = 'import React from "react";\nconst x = 1;'
        content_b = 'import Vue from "vue";\nconst y = 2;'
        result = sm.resolve_imports(content_a, content_b, language="javascript")
        assert 'import React from "react";' in result
        assert 'import Vue from "vue";' in result

    def test_require_statements(self, sm: SmartMerge):
        """CommonJS require() lines are recognized. @trace TGNT-P7.3"""
        content_a = 'require("fs");\nconst x = 1;'
        content_b = 'require("path");\nconst y = 2;'
        result = sm.resolve_imports(content_a, content_b, language="javascript")
        assert 'require("fs");' in result
        assert 'require("path");' in result

    def test_typescript_language_alias(self, sm: SmartMerge):
        """language='typescript' triggers the JS import detection branch. @trace TGNT-P7.3"""
        content_a = 'import { Component } from "angular";'
        content_b = 'import { Pipe } from "angular";'
        result = sm.resolve_imports(content_a, content_b, language="typescript")
        assert 'import { Component } from "angular";' in result
        assert 'import { Pipe } from "angular";' in result


# ---------------------------------------------------------------------------
# TGNT-P7.4: merge_structural — JSON merge via jq
# ---------------------------------------------------------------------------


class TestMergeStructuralJSON:
    """JSON structural merge via jq subprocess. @trace TGNT-P7.4"""

    def test_json_merge_success(self, sm: SmartMerge, tmp_path: Path):
        """Successful JSON merge returns True and writes output. @trace TGNT-P7.4"""
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        out = tmp_path / "out.json"

        a.write_text(json.dumps({"x": 1}).decode())
        b.write_text(json.dumps({"y": 2}).decode())

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0)
            # Simulate jq writing to output via stdout redirection
            result = sm.merge_structural(a, b, out)

        assert result is True
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "jq" in cmd
        assert ".[0] * .[1]" in cmd

    def test_json_merge_jq_failure(self, sm: SmartMerge, tmp_path: Path):
        """Returns False when jq subprocess fails. @trace TGNT-P7.4"""
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        out = tmp_path / "out.json"

        a.write_text(json.dumps({"x": 1}).decode())
        b.write_text(json.dumps({"y": 2}).decode())

        with mock.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "jq"),
        ):
            result = sm.merge_structural(a, b, out)

        assert result is False

    def test_json_merge_jq_not_found(self, sm: SmartMerge, tmp_path: Path):
        """Returns False when jq is not installed. @trace TGNT-P7.4"""
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        out = tmp_path / "out.json"

        a.write_text(json.dumps({"x": 1}).decode())
        b.write_text(json.dumps({"y": 2}).decode())

        with mock.patch(
            "subprocess.run",
            side_effect=FileNotFoundError("jq not found"),
        ):
            result = sm.merge_structural(a, b, out)

        assert result is False


# ---------------------------------------------------------------------------
# TGNT-P7.4: merge_structural — YAML merge via ruamel.yaml
# ---------------------------------------------------------------------------


class TestMergeStructuralYAML:
    """YAML structural merge via ruamel.yaml deep merge. @trace TGNT-P7.4"""

    def test_yaml_merge_success(self, sm: SmartMerge, tmp_path: Path):
        """Successful YAML merge returns True. @trace TGNT-P7.4"""
        a = tmp_path / "a.yaml"
        b = tmp_path / "b.yaml"
        out = tmp_path / "out.yaml"

        a.write_text("x: 1\n")
        b.write_text("y: 2\n")

        mock_yaml_instance = mock.MagicMock()
        mock_yaml_instance.load.side_effect = [{"x": 1}, {"y": 2}]

        mock_yaml_cls = mock.MagicMock(return_value=mock_yaml_instance)
        mock_ruamel = mock.MagicMock()
        mock_ruamel.yaml.YAML = mock_yaml_cls

        with mock.patch.dict("sys.modules", {"ruamel": mock_ruamel, "ruamel.yaml": mock_ruamel.yaml}):
            result = sm.merge_structural(a, b, out)

        assert result is True

    def test_yaml_merge_import_error(self, sm: SmartMerge, tmp_path: Path):
        """Returns False when ruamel.yaml is not installed. @trace TGNT-P7.4"""
        a = tmp_path / "a.yml"
        b = tmp_path / "b.yml"
        out = tmp_path / "out.yml"

        a.write_text("x: 1\n")
        b.write_text("y: 2\n")

        with mock.patch.dict("sys.modules", {"ruamel": None, "ruamel.yaml": None}):
            result = sm.merge_structural(a, b, out)

        assert result is False

    def test_yml_extension_accepted(self, sm: SmartMerge, tmp_path: Path):
        """Both .yaml and .yml extensions trigger the YAML path. @trace TGNT-P7.4"""
        a = tmp_path / "a.yml"
        b = tmp_path / "b.yml"
        out = tmp_path / "out.yml"

        a.write_text("x: 1\n")
        b.write_text("y: 2\n")

        mock_yaml_instance = mock.MagicMock()
        mock_yaml_instance.load.side_effect = [{"x": 1}, {"y": 2}]

        mock_yaml_cls = mock.MagicMock(return_value=mock_yaml_instance)
        mock_ruamel = mock.MagicMock()
        mock_ruamel.yaml.YAML = mock_yaml_cls

        with mock.patch.dict("sys.modules", {"ruamel": mock_ruamel, "ruamel.yaml": mock_ruamel.yaml}):
            result = sm.merge_structural(a, b, out)

        assert result is True

    def test_unsupported_extension_returns_false(self, sm: SmartMerge, tmp_path: Path):
        """Unsupported extensions (e.g. .toml) return False. @trace TGNT-P7.4"""
        a = tmp_path / "a.toml"
        b = tmp_path / "b.toml"
        out = tmp_path / "out.toml"

        a.write_text("[a]\nx = 1\n")
        b.write_text("[b]\ny = 2\n")

        result = sm.merge_structural(a, b, out)
        assert result is False


# ---------------------------------------------------------------------------
# TGNT-P7.4: _deep_merge helper
# ---------------------------------------------------------------------------


class TestDeepMerge:
    """Tests for the _deep_merge helper method. @trace TGNT-P7.4"""

    def test_flat_merge(self, sm: SmartMerge):
        """Flat dicts are merged with b overriding a on conflict. @trace TGNT-P7.4"""
        a = {"x": 1, "y": 2}
        b = {"y": 3, "z": 4}
        result = sm._deep_merge(a, b)
        assert result == {"x": 1, "y": 3, "z": 4}

    def test_nested_merge(self, sm: SmartMerge):
        """Nested dicts are recursively merged. @trace TGNT-P7.4"""
        a = {"top": {"a": 1, "b": 2}}
        b = {"top": {"b": 3, "c": 4}}
        result = sm._deep_merge(a, b)
        assert result == {"top": {"a": 1, "b": 3, "c": 4}}

    def test_scalar_overrides_dict(self, sm: SmartMerge):
        """When b has a scalar where a has a dict, b wins (ours-wins). @trace TGNT-P7.4"""
        a = {"key": {"nested": 1}}
        b = {"key": "scalar"}
        result = sm._deep_merge(a, b)
        assert result == {"key": "scalar"}

    def test_empty_b_returns_a_unchanged(self, sm: SmartMerge):
        """Empty b dict does not alter a. @trace TGNT-P7.4"""
        a = {"x": 1, "y": 2}
        result = sm._deep_merge(a, {})
        assert result == {"x": 1, "y": 2}

    def test_empty_a_returns_b(self, sm: SmartMerge):
        """Empty a dict becomes b. @trace TGNT-P7.4"""
        b = {"x": 1}
        result = sm._deep_merge({}, b)
        assert result == {"x": 1}

    def test_deeply_nested_three_levels(self, sm: SmartMerge):
        """Three-level deep nesting merges correctly. @trace TGNT-P7.4"""
        a = {"l1": {"l2": {"l3a": 1}}}
        b = {"l1": {"l2": {"l3b": 2}}}
        result = sm._deep_merge(a, b)
        assert result == {"l1": {"l2": {"l3a": 1, "l3b": 2}}}


# ---------------------------------------------------------------------------
# TGNT-P7.3 / P7.4: predict_conflicts (shared utility)
# ---------------------------------------------------------------------------


class TestPredictConflicts:
    """Tests for predict_conflicts method. @trace TGNT-P7.3"""

    def test_no_conflicts_disjoint_files(self, sm: SmartMerge):
        """No conflicts when agents touch different files. @trace TGNT-P7.3"""
        intents = [
            {"agent_id": "a1", "files": ["foo.py"], "type": "write"},
            {"agent_id": "a2", "files": ["bar.py"], "type": "write"},
        ]
        assert sm.predict_conflicts(intents) == []

    def test_single_conflict_detected(self, sm: SmartMerge):
        """Conflict detected when two agents write the same file. @trace TGNT-P7.3"""
        intents = [
            {"agent_id": "a1", "files": ["shared.py"], "type": "write"},
            {"agent_id": "a2", "files": ["shared.py"], "type": "write"},
        ]
        conflicts = sm.predict_conflicts(intents)
        assert len(conflicts) == 1
        file_, agent_a, agent_b = conflicts[0]
        assert file_ == "shared.py"
        assert {agent_a, agent_b} == {"a1", "a2"}

    def test_multiple_conflicts(self, sm: SmartMerge):
        """Multiple overlapping files generate multiple conflict tuples. @trace TGNT-P7.3"""
        intents = [
            {"agent_id": "a1", "files": ["x.py", "y.py"], "type": "write"},
            {"agent_id": "a2", "files": ["y.py", "z.py"], "type": "write"},
            {"agent_id": "a3", "files": ["z.py"], "type": "write"},
        ]
        conflicts = sm.predict_conflicts(intents)
        conflict_files = [c[0] for c in conflicts]
        assert "y.py" in conflict_files
        assert "z.py" in conflict_files

    def test_empty_intents(self, sm: SmartMerge):
        """Empty intent list yields no conflicts. @trace TGNT-P7.3"""
        assert sm.predict_conflicts([]) == []


# ---------------------------------------------------------------------------
# merge_ast_aware (baseline coverage, subprocess-mocked)
# ---------------------------------------------------------------------------


class TestMergeAstAware:
    """Tests for merge_ast_aware — mergiraf + git fallback. @trace TGNT-P7.3"""

    def test_mergiraf_success(self, sm: SmartMerge, tmp_path: Path):
        """Returns True when mergiraf exits cleanly. @trace TGNT-P7.3"""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"

        for f in (base, ours, theirs):
            f.write_text("content\n", encoding="utf-8")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0)
            result = sm.merge_ast_aware(base, ours, theirs, output)

        assert result is True

    def test_mergiraf_failure_falls_back_to_git(self, sm: SmartMerge, tmp_path: Path):
        """Falls back to git merge-file when mergiraf fails. @trace TGNT-P7.3"""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"

        for f in (base, ours, theirs):
            f.write_text("content\n", encoding="utf-8")

        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # mergiraf fails
                raise subprocess.CalledProcessError(1, "mergiraf")
            # git merge-file succeeds
            return mock.Mock(returncode=0)

        with mock.patch("subprocess.run", side_effect=side_effect):
            result = sm.merge_ast_aware(base, ours, theirs, output)

        assert result is True
        assert call_count == 2

    def test_both_mergiraf_and_git_fail(self, sm: SmartMerge, tmp_path: Path):
        """Returns False when both mergiraf and git merge-file fail. @trace TGNT-P7.3"""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"

        for f in (base, ours, theirs):
            f.write_text("content\n", encoding="utf-8")

        with mock.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "cmd"),
        ):
            result = sm.merge_ast_aware(base, ours, theirs, output)

        assert result is False

    def test_mergiraf_not_found_falls_back(self, sm: SmartMerge, tmp_path: Path):
        """FileNotFoundError from mergiraf triggers git fallback. @trace TGNT-P7.3"""
        base = tmp_path / "base.py"
        ours = tmp_path / "ours.py"
        theirs = tmp_path / "theirs.py"
        output = tmp_path / "out.py"

        for f in (base, ours, theirs):
            f.write_text("content\n", encoding="utf-8")

        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FileNotFoundError("mergiraf not found")
            return mock.Mock(returncode=0)

        with mock.patch("subprocess.run", side_effect=side_effect):
            result = sm.merge_ast_aware(base, ours, theirs, output)

        assert result is True
        assert call_count == 2
