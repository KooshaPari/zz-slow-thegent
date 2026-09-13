<DONE>
# Environment Variable Migration Status

**Date**: 2026-02-19
**Status**: ✅ In Progress
**Goal**: Migrate from `os.environ`/`os.getenv` to `ThegentSettings` for better configuration management

---

## ✅ Completed Migrations

### Files Migrated

1. ✅ `src/thegent/dex_main.py` - Uses `settings.dex_force_yolo`
2. ✅ `src/thegent/governance/heliosShield_bridge.py` - Uses `settings.harness_root`
3. ✅ `src/thegent/cli_impl.py` - Uses `settings.sandbox_env_filter` instead of `os.environ.get("THGENT_SANDBOX_ENV_FILTER")`

---

## 📋 Remaining Files to Migrate

### High Priority

- `src/thegent/install.py` - Uses `os.environ.get("SHELL")` (3 places) - **Note**: System env var, may keep as-is
- `src/thegent/install.py` - Uses `os.environ.get("APPDATA")` - **Note**: Windows-specific, may keep as-is
- `src/thegent/install.py` - Uses `os.environ["PATH"]` manipulation - **Note**: Runtime PATH manipulation, keep as-is

### Medium Priority

- `src/thegent/main.py` - Various `os.environ` usages
- `src/thegent/cli.py` - Various `os.environ` usages
- `src/thegent/agents/cliproxy_manager.py` - Environment variable access
- `src/thegent/agents/direct_agents.py` - Environment variable access
- `src/thegent/mcp_server.py` - Environment variable access
- `src/thegent/integration/harmonized_paths.py` - Environment variable access
- `src/thegent/tui/widgets/terminal_pane.py` - Environment variable access
- `src/thegent/isolation/sub_user_provider.py` - Environment variable access
- `src/thegent/infra/terminal_keepalive.py` - Environment variable access
- `src/thegent/doctor.py` - Environment variable access
- `src/thegent/forensics/snapshot.py` - Environment variable access
- `src/thegent/shell_cli.py` - Environment variable access

---

## 🔍 Notes

### System Environment Variables (Keep as-is)

These are system-level environment variables that should remain as `os.environ`:

- `SHELL` - User's shell
- `PATH` - System PATH (runtime manipulation)
- `APPDATA` - Windows app data directory
- `HOME` - User home directory
- `USER` - Current user

### THGENT\_\* Variables (Migrate to Settings)

All `THGENT_*` environment variables should be migrated to `ThegentSettings`:

- ✅ `THGENT_SANDBOX_ENV_FILTER` → `settings.sandbox_env_filter`
- ✅ `THGENT_DEX_FORCE_YOLO` → `settings.dex_force_yolo`
- ✅ `THGENT_HARNESS_ROOT` → `settings.harness_root`
- Others: Check `config.py` for available settings

---

## 🐛 Known Issues

### 1. Droid Cmd Hanging

- **Status**: ⏳ Pending Investigation
- **Description**: Running droid cmd hangs
- **Todo**: Investigate droid execution path

### 2. Type Error Outside Venv

- **Status**: ⏳ Pending Investigation
- **Description**: thegent gives type issue when run outside thegent dir/venv
- **Note**: Installation verified - works from /tmp
- **Todo**: Check type checking configuration

---

## ✅ Installation Verification

```bash
# Verified: thegent imports work from any directory
cd /tmp && python3 -c "from thegent.config import ThegentSettings; s = ThegentSettings(); print('✅ Works')"
# Result: ✅ Works
```

---

## Next Steps

1. Continue migrating THGENT\_\* environment variables to settings
2. Investigate droid cmd hang issue
3. Check type checking configuration for outside-venv usage
4. Update tests if needed

---

**Last Updated**: 2026-02-19
