# Mergiraf Setup Guide

Mergiraf is an AST-aware merge driver for Git. When multiple agents concurrently edit
the same Python, Rust, or TypeScript file, Git's default line-based 3-way merge often
produces spurious conflicts. Mergiraf resolves most of these automatically by
understanding the code structure.

---

## 1. Installation

### macOS (Homebrew)

```bash
brew install mergiraf
```

### Linux / cargo

```bash
cargo install mergiraf
```

### Verify

```bash
mergiraf --version   # should print: mergiraf 0.x.y
```

---

## 2. Register the Git Merge Driver

### Option A — Programmatic (recommended for agent environments)

```python
from thegent.mesh.smart_merge import configure_mergiraf_driver
from pathlib import Path

# Register driver for this repo only (writes to .git/config + .gitattributes)
configure_mergiraf_driver(repo_root=Path("."))

# Or register globally (writes to ~/.gitconfig, skips .gitattributes)
configure_mergiraf_driver(global_config=True)
```

### Option B — Manual

Add the following to your `.git/config` (local) or `~/.gitconfig` (global):

```ini
[merge "mergiraf"]
    name = mergiraf
    driver = mergiraf merge --git %O %A %B -p %P
```

- `%O` — base (common ancestor)
- `%A` — ours (overwritten in-place with merged result)
- `%B` — theirs
- `%P` — logical path in the repository (used by mergiraf for language detection)

---

## 3. `.gitattributes` Entries

Add to your project's `.gitattributes`:

```gitattributes
# mergiraf AST-aware merge driver
*.py  merge=mergiraf
*.rs  merge=mergiraf
*.ts  merge=mergiraf
*.tsx merge=mergiraf
*.js  merge=mergiraf
*.jsx merge=mergiraf
*.java merge=mergiraf
*.go  merge=mergiraf
```

These tell Git to invoke the `mergiraf` driver for the listed file types.

---

## 4. Runtime API

### `is_mergiraf_available() -> bool`

```python
from thegent.mesh.smart_merge import is_mergiraf_available

if is_mergiraf_available():
    print("mergiraf is installed and on PATH")
```

### `merge_files(base, ours, theirs, output, *, path_hint=None) -> bool`

Performs an AST-aware 3-way merge. Returns `True` for a clean merge, `False` if
conflict markers remain. Always writes to `output`.

```python
from pathlib import Path
from thegent.mesh.smart_merge import merge_files

clean = merge_files(
    base=Path("base.py"),
    ours=Path("ours.py"),
    theirs=Path("theirs.py"),
    output=Path("merged.py"),
    path_hint="src/parser.py",  # optional: helps mergiraf detect the language
)

if not clean:
    print("Conflicts remain — check merged.py for <<<< markers")
```

### `configure_mergiraf_driver(repo_root=None, *, global_config=False) -> bool`

Registers the git merge driver. Returns `False` if mergiraf is not installed.

---

## 5. Fallback Behavior

If mergiraf is not installed, `merge_files` automatically falls back to
`git merge-file --diff3`. If `git` is also unavailable, it copies the `ours`
version to `output` and returns `False`. The agent workflow is never blocked.

| Tool available | Strategy                              |
| -------------- | ------------------------------------- |
| mergiraf       | AST-aware 3-way merge                 |
| git only       | `git merge-file --diff3`              |
| neither        | Copy `ours` to output, return `False` |

---

## 6. Supported Languages

Run `mergiraf languages` to see the full list. As of v0.16, supported languages include
Python, Rust, TypeScript, JavaScript, Java, Go, C, C++, and more.

---

## 7. Troubleshooting

**Mergiraf not recognized after install:**
Ensure the binary is on your `PATH`:

```bash
echo $PATH
which mergiraf
```

**Conflicts still appear for `.py` files:**
Confirm `.gitattributes` is committed and contains `*.py merge=mergiraf`.

**Debugging a bad merge:**

```bash
mergiraf merge base.py ours.py theirs.py -o merged.py --debug /tmp/merge-debug/
```
