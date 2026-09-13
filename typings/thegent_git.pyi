"""Type stubs for thegent_git — native Rust extension (PyO3/maturin).

Source: crates/thegent-git/src/lib.rs
Module name: thegent_git (set via tool.maturin.module-name in pyproject.toml)

All functions accept an optional `path` as the first positional argument
(defaults to "."). Positional-only semantics match the PyO3 #[pyo3(signature)]
declarations in the Rust source.
"""


# ---------------------------------------------------------------------------
# Basic operations (gix-based)
# ---------------------------------------------------------------------------

def get_head_sha(path: str | None = None) -> str | None:
    """Return the HEAD commit SHA for the repo at *path*, or None if unborn."""

def get_branch_name(path: str | None = None) -> str | None:
    """Return the current branch short-name, or None if HEAD is detached."""

def is_dirty(path: str | None = None) -> bool:
    """Return True if the working tree has any modifications or untracked files."""

def get_status(path: str | None = None) -> dict[str, object]:
    """Return a dict with keys: branch, sha, staged, unstaged, untracked."""

# ---------------------------------------------------------------------------
# Write operations (Rust Command — faster than Python subprocess)
# ---------------------------------------------------------------------------

def add_files(
    path: str | None = None,
    files: list[str] | None = None,
) -> bool:
    """Stage *files* in the repo at *path* (git add --)."""

def rev_parse(path: str | None = None, ref_: str = ...) -> str | None:
    """Resolve *ref_* to a full SHA (git rev-parse equivalent)."""

def diff_stat(path: str | None = None, ref_: str = ...) -> str:
    """Return diff --stat output for *ref_* (e.g. 'HEAD', 'a..b', '--cached')."""

def create_commit(
    path: str | None = None,
    tree_hash: str = ...,
    message: str = ...,
    parents: list[str] = ...,
) -> str | None:
    """Create a commit object via git commit-tree; returns the new commit SHA."""

def update_ref(
    path: str | None = None,
    ref_: str = ...,
    new_hash: str = ...,
) -> bool:
    """Update *ref_* to point at *new_hash* (git update-ref equivalent)."""

def merge_base(
    path: str | None = None,
    commit1: str = ...,
    commit2: str = ...,
) -> str | None:
    """Find the merge-base of *commit1* and *commit2* (git merge-base)."""
