# Environment Variable Migration Progress - 2026-02-19

**Status:** ✅ Hook Fixed | ⏳ Migrations In Progress

---

## Summary

- **Total files using os.environ/os.getenv:** 70+ files
- **Files migrated:** 4 files
- **Settings added:** 2 new settings
- **Remaining:** ~66 files (many use non-THGENT vars or runtime values)

---

## ✅ Completed Migrations

### 1. `src/thegent/dex_main.py` ✅

- **Before:** `os.environ["THGENT_DEX_FORCE_YOLO"] = "1"`
- **After:** `settings.dex_force_yolo = True`
- **Settings added:** `dex_force_yolo: bool`

### 2. `src/thegent/governance/sharecli_bridge.py` ✅

- **Before:** `os.getenv("HARNESS_ROOT")`
- **After:** `settings.harness_root`
- **Settings added:** `harness_root: Path`

### 3. `src/thegent/main.py` ✅

- **Before:** `os.environ.get("THGENT_CONTROL_PLANE_URL", "http://127.0.0.1:3848")`
- **After:** `settings.control_plane_url`
- **Settings added:** `control_plane_url: str`

### 4. `src/thegent/execution.py` ✅ (partial)

- **Before:** `os.environ.get("THGENT_CRITICAL_LANE_SLOTS")`
- **After:** `settings.critical_lane_slots`
- **Note:** `critical_lane_slots` already existed in ThegentSettings
- **Note:** `THGENT_SESSION_ID` left as-is (runtime value, not a config setting)

---

## 📋 New Settings Added to ThegentSettings

1. **`dex_force_yolo: bool`**
   - Default: `False`
   - Description: Force YOLO mode: skip permissions, disable sandbox and approvals

2. **`harness_root: Path`**
   - Default: `Path("~/.agent-harness").expanduser()`
   - Description: ShareCLI harness root directory

3. **`control_plane_url: str`**
   - Default: `"http://127.0.0.1:3848"`
   - Description: Control plane server URL

---

## 🔍 Analysis: Files Using os.environ

### Categories of Usage

1. **THGENT\_\* configuration variables** (~30-40 files)
   - Should be migrated to ThegentSettings
   - Most already have corresponding settings

2. **Runtime values** (~10-15 files)
   - `THGENT_SESSION_ID`, `THGENT_RUN_ID`, etc.
   - These change per execution and are not configuration
   - Can remain as `os.environ` or be passed as parameters

3. **System/environment variables** (~20-30 files)
   - `PATH`, `HOME`, `USER`, `SHELL`, etc.
   - These are system-level and should remain as `os.environ`

4. **Third-party/application vars** (~5-10 files)
   - Variables for external tools (e.g., `REDIS_URL`, `DATABASE_URL`)
   - May or may not need migration depending on usage

---

## ⏳ Next Steps

### High Priority Files to Migrate

1. **`src/thegent/cli/legacy/cli_impl.py`** (7 occurrences)
   - Likely has multiple THGENT\_\* vars

2. **`src/thegent/clode_main.py`** (7 occurrences)
   - Main CLI entry point, likely has important config

3. **`src/thegent/shell_cli.py`** (7 occurrences)
   - Shell CLI, likely has shell-related config

4. **`src/thegent/agents/cliproxy_manager.py`** (5 occurrences)
   - Agent management, likely has agent config

5. **`src/thegent/agents/codex_proxy.py`** (5 occurrences)
   - Codex proxy, likely has proxy config

### Migration Strategy

1. **Analyze each file** to identify THGENT\_\* vars
2. **Check if setting exists** in ThegentSettings
3. **Add missing settings** if needed
4. **Migrate the code** to use `ThegentSettings()`
5. **Verify syntax** and test

### Files to Skip (Runtime Values)

- Files using `THGENT_SESSION_ID`, `THGENT_RUN_ID` (runtime values)
- Files using system vars (`PATH`, `HOME`, `USER`, etc.)
- Files copying entire `os.environ` for subprocess execution

---

## 📊 Progress Tracking

| Category           | Total   | Migrated | Remaining  |
| ------------------ | ------- | -------- | ---------- |
| Configuration vars | ~40     | 4        | ~36        |
| Runtime values     | ~15     | 0        | ~15 (skip) |
| System vars        | ~30     | 0        | ~30 (skip) |
| **Total**          | **~85** | **4**    | **~81**    |

---

## ✅ Verification

- ✅ Hook script fixed and working
- ✅ All migrated files pass syntax check
- ✅ Settings are properly typed and documented
- ✅ No regressions detected

---

**Next:** Continue migrating high-priority files systematically.
