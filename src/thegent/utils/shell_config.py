"""Shell configuration manager: audit and consolidate shell scripts.

Audits Zsh configuration files across a project to identify:
- Duplicate function definitions across files
- Source relationships between files
- Alias definitions
- Consolidation opportunities
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Patterns for parsing shell scripts
_FUNCTION_PATTERN = re.compile(
    r"^\s*(?:function\s+(\w[\w.-]*)\s*\(\s*\)|(\w[\w.-]*)\s*\(\s*\))\s*\{",
    re.MULTILINE,
)
_ALIAS_PATTERN = re.compile(
    r"^\s*alias\s+(\w[\w.-]*)=",
    re.MULTILINE,
)
_SOURCE_PATTERN = re.compile(
    r"""^\s*(?:source|\.)[ \t]+["']?([^"'\s\n]+)["']?""",
    re.MULTILINE,
)

# Extensions and names considered shell config files
_ZSH_EXTENSIONS = frozenset({".zsh", ".zshrc", ".zshenv", ".zprofile", ".zlogin", ".zlogout"})
_ZSH_NAMES = frozenset(
    {
        ".zshrc",
        ".zshenv",
        ".zprofile",
        ".zlogin",
        ".zlogout",
        "zshrc",
        "zshenv",
    }
)


def _is_shell_config(path: Path) -> bool:
    """Return True if the path is a shell configuration file."""
    suffix = path.suffix.lower()
    name = path.name.lower()
    return suffix in _ZSH_EXTENSIONS or name in _ZSH_NAMES or suffix == ".sh"


def _resolve_source(source_str: str, relative_to: Path) -> Path | None:
    """Resolve a sourced path string to an absolute Path.

    Only a small set of well-known shell variables whose values can be
    determined statically at audit time are expanded.  Any remaining shell
    variable reference (``$VAR`` or ``${VAR}`` or backtick) causes the
    function to return ``None`` (unresolvable).
    """
    # Expand ${ZDOTDIR:-$HOME} compound form only (bare $ZDOTDIR is unknown).
    source_str = re.sub(r"\$\{ZDOTDIR:-\$HOME\}", str(Path.home()), source_str)
    source_str = re.sub(r"\$\{XDG_CONFIG_HOME:-[^}]*\}", str(Path.home() / ".config"), source_str)
    # Expand bare $HOME / ${HOME}
    source_str = re.sub(r"\$\{HOME\}|\$HOME(?!\w)", str(Path.home()), source_str)
    # Expand bare $XDG_CONFIG_HOME / ${XDG_CONFIG_HOME}
    source_str = re.sub(
        r"\$\{XDG_CONFIG_HOME\}|\$XDG_CONFIG_HOME(?!\w)",
        str(Path.home() / ".config"),
        source_str,
    )
    # Skip dynamic/variable paths that cannot be resolved statically
    if "$" in source_str or "`" in source_str:
        return None
    candidate = Path(source_str)
    if candidate.is_absolute():
        return candidate
    return relative_to / candidate


@dataclass
class ShellConfigFile:
    """Represents a parsed shell configuration file.

    Attributes:
        path: Absolute path to the file.
        sources: Absolute paths of files this config sources (best-effort resolution).
        functions: Names of shell functions defined in this file.
        aliases: Names of aliases defined in this file.
        raw_sources: Raw source strings (before path resolution).
    """

    path: Path
    sources: list[Path] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    raw_sources: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, path: Path) -> ShellConfigFile:
        """Parse a shell config file and extract metadata.

        Args:
            path: Path to the shell configuration file.

        Returns:
            Populated ShellConfigFile instance.

        Raises:
            OSError: If the file cannot be read.
        """
        text = path.read_text(encoding="utf-8", errors="replace")
        parent = path.parent

        functions: list[str] = []
        for m in _FUNCTION_PATTERN.finditer(text):
            name = m.group(1) or m.group(2)
            if name:
                functions.append(name)

        aliases = [m.group(1) for m in _ALIAS_PATTERN.finditer(text)]

        raw_sources: list[str] = []
        resolved_sources: list[Path] = []
        for m in _SOURCE_PATTERN.finditer(text):
            raw = m.group(1)
            raw_sources.append(raw)
            resolved = _resolve_source(raw, parent)
            if resolved is not None:
                resolved_sources.append(resolved)

        return cls(
            path=path.resolve(),
            sources=resolved_sources,
            functions=functions,
            aliases=aliases,
            raw_sources=raw_sources,
        )


class ShellConfigAuditor:
    """Audit and consolidate shell configuration files.

    Usage::

        auditor = ShellConfigAuditor()
        configs = auditor.audit([Path("shell"), Path("scripts")])
        dupes = auditor.find_duplicates(configs)
        issues = auditor.check_sourcing_order(configs)
        merged = auditor.generate_consolidated(configs)
    """

    def audit(self, search_dirs: list[Path]) -> list[ShellConfigFile]:
        """Discover and parse shell config files in the given directories.

        Walks each directory recursively and parses all files identified as
        shell configuration files (Zsh or generic shell scripts).

        Args:
            search_dirs: List of directories to search.

        Returns:
            List of parsed ShellConfigFile instances, sorted by path.
        """
        configs: list[ShellConfigFile] = []
        seen: set[Path] = set()
        for directory in search_dirs:
            directory = Path(directory)
            if not directory.is_dir():
                continue
            for candidate in sorted(directory.rglob("*")):
                if not candidate.is_file():
                    continue
                if not _is_shell_config(candidate):
                    continue
                abs_path = candidate.resolve()
                if abs_path in seen:
                    continue
                seen.add(abs_path)
                try:
                    configs.append(ShellConfigFile.parse(candidate))
                except OSError:
                    # Skip unreadable files gracefully
                    continue
        return configs

    def find_duplicates(self, configs: list[ShellConfigFile]) -> dict[str, list[Path]]:
        """Find function names that are defined in more than one file.

        Args:
            configs: List of parsed shell config files.

        Returns:
            Mapping from function name to the list of files that define it.
            Only entries with two or more files are included.
        """
        index: dict[str, list[Path]] = {}
        for cfg in configs:
            for func in cfg.functions:
                index.setdefault(func, []).append(cfg.path)
        return {name: paths for name, paths in index.items() if len(paths) > 1}

    def find_duplicate_aliases(self, configs: list[ShellConfigFile]) -> dict[str, list[Path]]:
        """Find alias names that are defined in more than one file.

        Args:
            configs: List of parsed shell config files.

        Returns:
            Mapping from alias name to the list of files that define it.
            Only entries with two or more files are included.
        """
        index: dict[str, list[Path]] = {}
        for cfg in configs:
            for alias in cfg.aliases:
                index.setdefault(alias, []).append(cfg.path)
        return {name: paths for name, paths in index.items() if len(paths) > 1}

    def generate_consolidated(self, configs: list[ShellConfigFile]) -> str:
        """Generate a merged shell script from all config files.

        Each file's content is included with a header comment indicating
        its origin. Duplicate function definitions are warned about in
        inline comments.

        Args:
            configs: List of parsed shell config files.

        Returns:
            Single string containing the consolidated shell script content.
        """
        if not configs:
            return "# No shell configuration files found.\n"

        duplicates = self.find_duplicates(configs)
        duplicate_names = set(duplicates.keys())

        parts: list[str] = [
            "#!/usr/bin/env zsh",
            "# Consolidated shell configuration — auto-generated by ShellConfigAuditor",
            "# DO NOT edit manually; regenerate from source files.",
            "",
        ]

        for cfg in configs:
            parts.append(f"# {'=' * 72}")
            parts.append(f"# Source: {cfg.path}")
            parts.append(f"# {'=' * 72}")

            # Warn about any duplicate functions in this file
            dupes_here = [fn for fn in cfg.functions if fn in duplicate_names]
            if dupes_here:
                parts.append(f"# WARNING: duplicate function(s) from this file: {', '.join(dupes_here)}")

            try:
                content = cfg.path.read_text(encoding="utf-8", errors="replace").rstrip()
            except OSError:
                parts.append("# ERROR: Could not read file")
                parts.append("")
                continue

            parts.append(content)
            parts.append("")

        return "\n".join(parts) + "\n"

    def check_sourcing_order(self, configs: list[ShellConfigFile]) -> list[str]:
        """Detect potential sourcing issues among the config files.

        Checks:
        - Files that source other files not present in the discovered set.
        - Circular sourcing chains.
        - Files that are sourced but have no functions or aliases.

        Args:
            configs: List of parsed shell config files.

        Returns:
            List of human-readable issue strings. Empty list means no issues.
        """
        known_paths: set[Path] = {cfg.path for cfg in configs}
        path_to_cfg: dict[Path, ShellConfigFile] = {cfg.path: cfg for cfg in configs}
        issues: list[str] = []

        for cfg in configs:
            for sourced in cfg.sources:
                if sourced not in known_paths:
                    issues.append(f"{cfg.path.name}: sources '{sourced}' which is not in the discovered set")

        # Detect circular sourcing
        def _has_cycle(start: Path, visited: set[Path], stack: set[Path]) -> bool:
            visited.add(start)
            stack.add(start)
            cfg = path_to_cfg.get(start)
            if cfg:
                for sourced in cfg.sources:
                    if sourced not in visited:
                        if _has_cycle(sourced, visited, stack):
                            return True
                    elif sourced in stack:
                        return True
            stack.discard(start)
            return False

        visited: set[Path] = set()
        for path in known_paths:
            if path not in visited and _has_cycle(path, visited, set()):
                issues.append(f"Circular sourcing detected involving: {path.name}")

        # Files with no functions or aliases
        for cfg in configs:
            if not cfg.functions and not cfg.aliases:
                issues.append(
                    f"{cfg.path.name}: defines no functions or aliases (may be config-only, sourcing-only, or empty)"
                )

        return issues

    def sourcing_graph(self, configs: list[ShellConfigFile]) -> dict[str, list[str]]:
        """Build a human-readable sourcing dependency graph.

        Args:
            configs: List of parsed shell config files.

        Returns:
            Mapping from file name to list of sourced file names/paths.
        """
        return {cfg.path.name: [str(s) for s in cfg.sources] for cfg in configs if cfg.sources}
