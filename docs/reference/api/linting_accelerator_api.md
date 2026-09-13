# linting_accelerator API Reference

> **Source**: `src/thegent/utils/linting_accelerator.py`

Linting accelerator: run oxlint as fast pre-filter before ESLint.

# @trace FR-UX-011

oxlint is a Rust-based JS/TS linter that is 50-100x faster than ESLint.
This module integrates it as a drop-in accelerator:

- `fast=True` -&gt; run oxlint first; fall back to ESLint only if oxlint
  is unavailable (or skip ESLint entirely for CI speed).
- `fast=False` -&gt; always run ESLint (standard behaviour).
- `run_ruff` -&gt; Python linting via ruff (similar philosophy).

All three runners return a uniform `list[LintResult]` so callers can
process results without caring which backend was used.

---

## LintResult

A single diagnostic produced by any linter backend.

### Methods

---

## LintingAccelerator

Unified linting interface with oxlint fast-path.

Usage::

    acc = LintingAccelerator()
    results = acc.lint([Path("src/")], fast=True)
    for r in results:
        print(r)

### Methods

#### LintingAccelerator.is_eslint_available

```python
is_eslint_available(self: Any)
```

Return `True` if `eslint` is found on `$PATH`.

**Returns**: `True` when the `eslint` binary can be located via
:func:`shutil.which`; `False` otherwise.

---

#### LintingAccelerator.is_oxlint_available

```python
is_oxlint_available(self: Any)
```

Return `True` if `oxlint` is found on `$PATH`.

**Returns**: `True` when the `oxlint` binary can be located via
:func:`shutil.which`; `False` otherwise.

---

#### LintingAccelerator.is_ruff_available

```python
is_ruff_available(self: Any)
```

Return `True` if `ruff` is found on `$PATH`.

**Returns**: `True` when the `ruff` binary can be located via
:func:`shutil.which`; `False` otherwise.

---

#### LintingAccelerator.lint

```python
lint(self: Any, paths: list[Path], fast: bool, oxlint_config: Any, eslint_config: Any)
```

Run linting and return all diagnostics.

When `fast=True` (default):

1. If `oxlint` is available, run oxlint and return its results.
   This is 50-100x faster than ESLint and catches the majority of
   issues.
2. If `oxlint` is **not** available, fall back to ESLint.

When `fast=False`:

- Always run ESLint (standard, thorough behaviour).

**Parameters**:

- `paths`: List of files or directories to lint.
- `fast`: Use oxlint fast-path when available.
- `oxlint_config`: Optional path to `oxlintrc.json`.
- `eslint_config`: Optional path to an ESLint config file.

**Returns**: Combined list of :class:`LintResult` from whichever backend(s)
were executed.

---

#### LintingAccelerator.run_eslint

```python
run_eslint(self: Any, paths: list[Path], config: Any)
```

Run `eslint --format json` and return parsed diagnostics.

**Parameters**:

- `paths`: List of files or directories to lint.
- `config`: Optional path to an ESLint config file. When
  `None`, ESLint uses its default discovery logic.

**Returns**: List of :class:`LintResult` objects, one per diagnostic.

---

#### LintingAccelerator.run_oxlint

```python
run_oxlint(self: Any, paths: list[Path], config: Any)
```

Run `oxlint` and return parsed diagnostics.

**Parameters**:

- `paths`: List of files or directories to lint.
- `config`: Optional path to an `oxlintrc.json` config file.
  When `None`, oxlint auto-discovers `oxlintrc.json`
  in the working directory.

**Returns**: List of :class:`LintResult` objects, one per diagnostic.

---

#### LintingAccelerator.run_ruff

```python
run_ruff(self: Any, paths: list[Path])
```

Run `ruff check --output-format json` and return diagnostics.

**Parameters**:

- `paths`: List of Python files or directories to lint.

**Returns**: List of :class:`LintResult` objects, one per diagnostic.

---

---

## is_eslint_available

```python
is_eslint_available(self: Any)
```

Return `True` if `eslint` is found on `$PATH`.

**Returns**: `True` when the `eslint` binary can be located via
:func:`shutil.which`; `False` otherwise.

---

## is_oxlint_available

```python
is_oxlint_available(self: Any)
```

Return `True` if `oxlint` is found on `$PATH`.

**Returns**: `True` when the `oxlint` binary can be located via
:func:`shutil.which`; `False` otherwise.

---

## is_ruff_available

```python
is_ruff_available(self: Any)
```

Return `True` if `ruff` is found on `$PATH`.

**Returns**: `True` when the `ruff` binary can be located via
:func:`shutil.which`; `False` otherwise.

---

## lint

```python
lint(self: Any, paths: list[Path], fast: bool, oxlint_config: Any, eslint_config: Any)
```

Run linting and return all diagnostics.

When `fast=True` (default):

1. If `oxlint` is available, run oxlint and return its results.
   This is 50-100x faster than ESLint and catches the majority of
   issues.
2. If `oxlint` is **not** available, fall back to ESLint.

When `fast=False`:

- Always run ESLint (standard, thorough behaviour).

**Parameters**:

- `paths`: List of files or directories to lint.
- `fast`: Use oxlint fast-path when available.
- `oxlint_config`: Optional path to `oxlintrc.json`.
- `eslint_config`: Optional path to an ESLint config file.

**Returns**: Combined list of :class:`LintResult` from whichever backend(s)
were executed.

---

## run_eslint

```python
run_eslint(self: Any, paths: list[Path], config: Any)
```

Run `eslint --format json` and return parsed diagnostics.

**Parameters**:

- `paths`: List of files or directories to lint.
- `config`: Optional path to an ESLint config file. When
  `None`, ESLint uses its default discovery logic.

**Returns**: List of :class:`LintResult` objects, one per diagnostic.

**Raises**:

- `FileNotFoundError`: If `eslint` is not installed.
- `ValueError`: If the JSON output from ESLint cannot be parsed.

---

## run_oxlint

```python
run_oxlint(self: Any, paths: list[Path], config: Any)
```

Run `oxlint` and return parsed diagnostics.

**Parameters**:

- `paths`: List of files or directories to lint.
- `config`: Optional path to an `oxlintrc.json` config file.
  When `None`, oxlint auto-discovers `oxlintrc.json`
  in the working directory.

**Returns**: List of :class:`LintResult` objects, one per diagnostic.

**Raises**:

- `FileNotFoundError`: If `oxlint` is not installed.
- `ValueError`: If the JSON output from oxlint cannot be parsed.

---

## run_ruff

```python
run_ruff(self: Any, paths: list[Path])
```

Run `ruff check --output-format json` and return diagnostics.

**Parameters**:

- `paths`: List of Python files or directories to lint.

**Returns**: List of :class:`LintResult` objects, one per diagnostic.

**Raises**:

- `FileNotFoundError`: If `ruff` is not installed.
- `ValueError`: If the JSON output from ruff cannot be parsed.

---
