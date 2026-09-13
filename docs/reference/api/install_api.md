# install API Reference

> **Source**: `src/thegent/install.py`

Install module for managed installation and synchronization of thegent components.

---

## BundleItem

**Inherits from**: `BaseModel`

---

## BundleManifest

Optional external manifest describing installable third-party bundles.

**Inherits from**: `BaseModel`

---

## ConfigManifest

**Inherits from**: `BaseModel`

---

## FileAction

**Inherits from**: `StrEnum`

---

## FileManifest

**Inherits from**: `BaseModel`

---

## InstallManager

### Methods

#### InstallManager.**init**

```python
__init__(self: Any, dry_run: bool, verbose: bool)
```

---

#### InstallManager.install_file

```python
install_file(self: Any, source: Path, target: Path, mode: InstallMode)
```

---

#### InstallManager.save_manifest

```python
save_manifest(self: Any)
```

---

#### InstallManager.uninstall

```python
uninstall(self: Any)
```

---

#### InstallManager.update_config

```python
update_config(self: Any, config_path: Path, key_path: str, value: Any)
```

Update a JSON config file at a specific key path (e.g. 'mcpServers.thegent').

---

---

## InstallManifest

**Inherits from**: `BaseModel`

---

## InstallMode

**Inherits from**: `StrEnum`

---

## cleanup_old_backups

```python
cleanup_old_backups(keep_count: int, console: Any)
```

Remove old backups, keeping only the most recent ones.

**Parameters**:

- `keep_count`: Number of backups to keep (default: 10)
- `console`: Rich console for output

**Returns**: (removed_count, removed_files)

---

## clone_git_repo

```python
clone_git_repo(repo_url: str, target_dir: Path, console: Any, dry_run: bool, branch: Any)
```

Clone a git repository. Returns (success, message).

---

## create_symlink

```python
create_symlink(source: Path, target: Path, dry_run: bool)
```

Legacy shim for tests.

---

## get_backup_dir

---

## get_bundle_manifest_path

```python
get_bundle_manifest_path(bundle_manifest: Any)
```

Get the bundle manifest path.

**Parameters**:

- `bundle_manifest`: Optional path to a bundle manifest file.

**Returns**: The path to the bundle manifest file.

---

## get_default_bundle_manifest_path

Default location for the third-party bundle manifest.

---

## get_home_dir

---

## get_manifest_path

---

## get_source_dest_mapping

```python
get_source_dest_mapping(thegent_root: Path, bundle: str)
```

Legacy shim for tests.

---

## install_file

```python
install_file(self: Any, source: Path, target: Path, mode: InstallMode) -> FileAction
```

---

## install_homebrew

```python
install_homebrew(console: Any, dry_run: bool)
```

Install Homebrew if not present. Returns (success, message).

---

## install_mise

```python
install_mise(console: Any, dry_run: bool, use_nix: bool, settings: ThegentSettings | None)
```

Install mise (formerly rtx) via Homebrew or Nix. Returns (success, message).

---

## install_system_dependencies

```python
install_system_dependencies(console: Any, dry_run: bool, install_homebrew_pkg: bool, install_mise_pkg: bool, use_nix: bool, git_repos: Any)
```

Install system-wide dependencies: Homebrew, mise, git repos.

**Parameters**:

- `console`: Rich console for output
- `dry_run`: If True, only show what would be done
- `install_homebrew_pkg`: Install Homebrew if missing
- `install_mise_pkg`: Install mise if missing
- `use_nix`: Use Nix instead of Homebrew for mise
- `git_repos`: List of dicts with 'url', 'target', optional 'branch'

**Returns**: dict with 'homebrew', 'mise', 'git_repos' status

---

## list_backups

```python
list_backups(console: Any)
```

List all available backups. Returns list of backup paths.

---

## list_bundle_names

```python
list_bundle_names(bundle_manifest: Any)
```

List available bundle names from the bundle manifest.

**Parameters**:

- `bundle_manifest`: Optional path to a bundle manifest file.

**Returns**: List of bundle names available in the bundle manifest.

---

## load_bundle_manifest

```python
load_bundle_manifest(path: Any)
```

Load third-party bundle definitions from an external JSON manifest.

Expected schema:
{
"bundles": {
"name": {
"items": [
{"source": "...", "target": "...", "mode": "smart|force|editable"}
]
}
}
}

---

## resolve_bundles

```python
resolve_bundles(bundle_names: Any, bundle_manifest: Any, thegent_root: Path, home: Path, cwd: Path, fallback_mode: InstallMode)
```

Resolve selected bundles to install tuples.

---

## restore_shell_config

```python
restore_shell_config(backup_path: Path, console: Any)
```

Restore shell config from backup. Returns (success, message).

---

## run_install

```python
run_install(target: str, mode: str, dry_run: bool, verbose: bool, url: Any, install_service: bool, bundles: Any, bundle_manifest: Any, bundle_conflict_policy: Any) -> dict
```

---

## run_install_system

```python
run_install_system(prefix: Path, dry_run: bool, verbose: bool)
```

Install thegent for agent-as-system-user. Layout: bin, share/thegent/hooks, etc/thegent, var/lib/thegent.

---

## run_wizard

```python
run_wizard(url: Any)
```

Interactive installation wizard using rich.

---

## save_manifest

```python
save_manifest(self: Any) -> None
```

---

## service_install

---

## service_start

---

## service_uninstall

---

## setup_harness

```python
setup_harness(verbose: bool)
```

WP-11006: Install/update heliosShield harness.

---

## setup_hooks

```python
setup_hooks(cwd: Any, dry_run: bool, verbose: bool)
```

Install thegent hooks into .git/hooks. Returns counts dict.

---

## setup_skills

```python
setup_skills(cwd: Any, template: str, dry_run: bool, verbose: bool)
```

Sync skills template to project. Returns counts dict.

---

## should_exclude

```python
should_exclude(path: Any)
```

Legacy shim for tests.

---

## smart_copy_file

```python
smart_copy_file(source: Path, target: Path, dry_run: bool)
```

Legacy shim for tests.

---

## uninstall

```python
uninstall(self: Any) -> dict[(str, int)]
```

---

## uninstall_mise_hooks

```python
uninstall_mise_hooks(console: Any, dry_run: bool, settings: ThegentSettings | None)
```

Remove mise hooks from shell config files. Returns (success, messages).

---

## uninstall_system_dependencies

```python
uninstall_system_dependencies(console: Any, dry_run: bool, uninstall_mise_pkg: bool, remove_hooks: bool)
```

Uninstall system dependencies: remove hooks, optionally uninstall mise.

**Parameters**:

- `console`: Rich console for output
- `dry_run`: If True, only show what would be done
- `uninstall_mise_pkg`: Also uninstall mise package (via brew/nix)
- `remove_hooks`: Remove shell hooks (default: True)

**Returns**: dict with uninstall status

---

## update_config

```python
update_config(self: Any, config_path: Path, key_path: str, value: Any)
```

Update a JSON config file at a specific key path (e.g. 'mcpServers.thegent').

---

## validate_bundle_manifest

```python
validate_bundle_manifest(bundle_manifest: Any)
```

Validate a bundle manifest file.

**Parameters**:

- `bundle_manifest`: Optional path to a bundle manifest file.

**Returns**: Tuple of (is_valid, list of issues).

---

## verify_mise_installation

```python
verify_mise_installation(console: Any, settings: ThegentSettings | None)
```

Verify mise installation and configuration. Returns (success, messages).

---
