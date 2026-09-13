<DONE>
# Consolidation of os.environ Access (research-library-env-settings)

**Task**: P3 priority - Consolidate all direct `os.environ` access into `ThegentSettings` dependency injection (15+ files)

**Status**: Planning phase - delegating implementation to agents

---

## Summary of os.environ Usage

Found **9 files** with direct `os.environ` access (total ~30 occurrences):

### 1. **src/thegent/planning/auto_launch.py** (2 occurrences)

- Lines 120-122: `os.getenv("ANALYTICS_SITE_ID")`, `os.getenv("SIEM_ENDPOINT_URL")`
- **Impact**: High - core auto-launch system
- **Pattern**: Initialization parameters in `__init__`
- **Fix**: Add `analytics_site_id`, `siem_endpoint_url` to ThegentSettings

### 2. **src/thegent/mcp_manage.py** (2 occurrences)

- Lines 166-167: `os.environ.get("VIRTUAL_ENV")`, `os.environ["VIRTUAL_ENV"]`
- **Impact**: Medium - MCP setup helper
- **Pattern**: Virtual environment detection in function
- **Fix**: Add `virtual_env` to ThegentSettings

### 3. **src/thegent/install.py** (5 occurrences)

- Lines 251, 309, 397, 437, 1686: PATH, SHELL, APPDATA access
- **Impact**: High - system installer
- **Pattern**: Mixed (environment modification, shell detection, platform paths)
- **Fix**: Add settings for `shell_path`, `appdata_path`; be careful with PATH mutation

### 4. **src/thegent/dex_main.py** (3 occurrences)

- Lines 173, 211, 219: THGENT_CLIPROXY_ADAPTER mutation, env copy, PATH access
- **Impact**: Medium - DEX main entry
- **Pattern**: Environment setup for subprocess
- **Fix**: Add `cliproxy_adapter_force`, `cliproxy_path` to settings

### 5. **scripts/start_proxy_with_adapter.py** (4 occurrences)

- Lines 56, 67, 119, 120, 125: PATH lookup, env copy, THGENT_DEBUG, THGENT_RELOAD, CLIPROXY backend mutation
- **Impact**: Medium - standalone script
- **Pattern**: Script bootstrap and logging setup
- **Fix**: Add `debug`, `reload` to ThegentSettings (already exist!); add `cliproxy_backend_url`

### 6. **tests/test_unit_config_provider.py** (3 occurrences)

- Lines 48-50, 56: Mocking env vars in tests
- **Impact**: Low - test code
- **Pattern**: Test setup/teardown
- **Fix**: Refactor to use `MonkeyPatch` fixture or mock ThegentSettings instead

### 7. **tests/test_platform_paths.py** (4 occurrences)

- Lines 14-17, 38, 60: Mocking HOME, APPDATA, THGENT_CONFIG_DIR
- **Impact**: Low - test code
- **Pattern**: Test isolation
- **Fix**: Refactor to mock ThegentSettings

### 8. **tests/test_resource_leaks.py** (1 occurrence)

- Line 365: `os.getenv("CHECK_LEAKS")`
- **Impact**: Low - test code
- **Pattern**: Debug/control flag
- **Fix**: Add to ThegentSettings or move to pytest marker

### 9. **conftest.py** (1 occurrence)

- Line 13: `os.environ["THGENT_TESTING"] = "1"`
- **Impact**: Medium - global test setup
- **Pattern**: Setting flag for entire test suite
- **Fix**: Move to fixture or pytest configuration

---

## ThegentSettings Additions Required

| Name                   | Type         | Env Var                       | Files                                    | Notes                                     |
| ---------------------- | ------------ | ----------------------------- | ---------------------------------------- | ----------------------------------------- |
| `analytics_site_id`    | str          | `THGENT_ANALYTICS_SITE_ID`    | auto_launch.py                           | Default: "thegent"                        |
| `siem_endpoint_url`    | str \| None  | `THGENT_SIEM_ENDPOINT_URL`    | auto_launch.py                           | Optional                                  |
| `virtual_env`          | Path \| None | `VIRTUAL_ENV`                 | mcp_manage.py                            | System var, read-only                     |
| `shell_path`           | str          | `SHELL`                       | install.py                               | Default: "/bin/zsh"                       |
| `appdata_path`         | Path \| None | `APPDATA`                     | install.py                               | Platform-specific                         |
| `cliproxy_backend_url` | str          | `THGENT_CLIPROXY_BACKEND_URL` | dex_main.py, start_proxy_with_adapter.py | For proxy setup                           |
| `check_leaks`          | bool         | `CHECK_LEAKS`                 | test_resource_leaks.py                   | Test flag                                 |
| `testing_mode`         | bool         | `THGENT_TESTING`              | conftest.py                              | Already in settings as implicit test mode |

---

## Implementation Strategy

### Phase 1: Update ThegentSettings (Low risk)

1. Add new fields with proper types and defaults
2. Add field validators where needed (e.g., for APPDATA platform detection)
3. Update docstrings with env var names

### Phase 2: Update Source Code (High risk, per-file)

1. **auto_launch.py**: Pass settings to AnalyticsIntegration, SIEMEgress
2. **mcp_manage.py**: Add settings parameter to `_build_virtualenv_hook` function
3. **install.py**: Thread settings through functions, or read once at start
4. **dex_main.py**: Use settings for cliproxy_backend_url, remove env mutation
5. **start_proxy_with_adapter.py**: Use settings for debug, reload, cliproxy settings

### Phase 3: Update Tests (Low risk)

1. **test_unit_config_provider.py**: Use pytest fixtures with mocked ThegentSettings
2. **test_platform_paths.py**: Create fixture returning test settings
3. **test_resource_leaks.py**: Add pytest marker or use test fixture
4. **conftest.py**: Use pytest plugin/fixture instead of env mutation

---

## Key Considerations

### Environment Variables That Should NOT Be in Settings

- `VIRTUAL_ENV` - System variable, read-only, not user-configurable
- `PATH` - System variable, should be read once, not stored in settings
- `SHELL` - System variable, but CAN be overridden; include with default detection
- `APPDATA` - Platform-specific, read-only

### Mutation vs. Read-Only

- **Mutation in install.py line 251**: Sets `PATH` for installer. Better to pass `env` dict to subprocess instead.
- **Mutation in dex_main.py line 173**: Sets `THGENT_CLIPROXY_ADAPTER`. Better to pass to cliproxy config instead.
- **Mutation in start_proxy_with_adapter.py line 125**: Sets backend URL. Move to config file.

### Test Isolation

- Tests should NOT modify `os.environ` globally
- Use `MonkeyPatch` (pytest) or mock `ThegentSettings`
- `conftest.py` mutation of `os.environ` affects entire suite — move to fixture

---

## Delegation Plan

**Recommended agents**:

- **Batch 1 (High-impact source files)**: `thegent free --do-next`
  - auto_launch.py (2 changes)
  - mcp_manage.py (2 changes)
  - dex_main.py (3 changes)

- **Batch 2 (Install system)**: Specialized agent
  - install.py (5 changes, complex threading)

- **Batch 3 (Scripts)**: `thegent free --do-next`
  - start_proxy_with_adapter.py (4 changes)

- **Batch 4 (Tests)**: `thegent free --do-next`
  - test\_\*.py files (11 changes, low risk)
  - conftest.py (1 change)

**Verification**:

```bash
# Ensure no os.environ access outside of:
# - ThegentSettings._parse_* validators (intentional, needed for pydantic)
# - conftest.py setup fixture (one-time test setup)
grep -r "os\.environ\|os\.getenv" src/ --include="*.py" | grep -v "__pycache__"

# Should have 0 results after completion
```

---

## Open Questions

1. **VIRTUAL_ENV handling**: Should this be in settings as a calculated field, or detected at startup?
2. **PATH mutations in install.py**: Can we avoid mutating os.environ, or is it required for installer workflow?
3. **Test mode flag**: Should `THGENT_TESTING` be a formal settings field, or just a pytest plugin configuration?
4. **Platform detection**: Should APPDATA / SHELL be auto-detected from os.environ at settings init, or user-provided?

---

## Success Criteria

- [ ] All source code files (src/) read env vars through ThegentSettings
- [ ] Test files use mocked/fixture-based ThegentSettings
- [ ] conftest.py uses pytest plugin/fixture instead of os.environ mutation
- [ ] No regressions in pytest (all tests pass)
- [ ] No regressions in CLI (thegent commands work normally)
- [ ] Grep for `os.environ` in src/ returns 0 results (except validators)
