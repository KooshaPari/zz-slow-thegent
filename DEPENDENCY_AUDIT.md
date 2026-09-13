# Dependency & Code Audit Report

## Date: 2026-02-23

---

## 1. PYTHON DEPENDENCIES

### 1.1 Current Stack (pyproject.toml)

| Category          | Package           | Version      | Notes                    |
| ----------------- | ----------------- | ------------ | ------------------------ |
| **Core**          | pydantic          | >=2.12.5     |                          |
|                   | pydantic-settings | >=2.8.1      |                          |
|                   | typer             | >=0.16.0     | CLI framework            |
|                   | rich              | >=13.9.4     | TUI                      |
| **HTTP**          | httpx             | >=0.28.1     |                          |
|                   | starlette         | >=0.46.0     |                          |
|                   | uvicorn           | >=0.34.0     |                          |
| **Caching**       | PersistDict       | >=0.2.0      | NEW - replaces diskcache |
| **Monitoring**    | opentelemetry-\*  | >=1.31.0     |                          |
|                   | structlog         | >=24.0.0     |                          |
| **Async**         | tenacity          | >=9.0.0      | Retry logic              |
| **Serialization** | orjson            | cpython only | Fast JSON                |
|                   | tomli/tomli_w     | >=2.2.1      | TOML                     |
|                   | tomlkit           | >=0.13.2     | TOML                     |
| **Validation**    | fastjsonschema    | >=2.21.1     |                          |
| **CLI**           | textual           | >=1.0.0      |                          |
| **LLM**           | litellm           | >=1.81.13    |                          |
| **Docs**          | vitepress         | >=1.6.4      |                          |
| **Dev**           | pytest            | >=9.0.2      |                          |
|                   | ruff              | >=0.15.1     | Linting                  |

---

## 2. NPM/JS DEPENDENCIES

### 2.1 Locked Versions

| Package           | Version | Status               |
| ----------------- | ------- | -------------------- |
| minimatch         | 10.2.1  | Fixed CVE-2026-26996 |
| esbuild           | latest  | Fixed                |
| ajv               | latest  | Fixed                |
| markdown-it-katex | latest  | Fixed                |
| puppeteer         | latest  | Updated              |
| vitepress         | 1.6.4   | Current              |
| @playwright/test  | 1.58.2  | Current              |

---

## 3. CUSTOM CODE AUDIT

### 3.1 Parser/Normalizer Functions (91 files)

**Total: 91 files** with parse*/validate*/normalize*/sanitize* functions

#### Duplication Opportunities:

| Pattern           | Files Using | Recommendation                      |
| ----------------- | ----------- | ----------------------------------- |
| `def parse_*`     | 50+         | Consolidate to utils/parsers.py     |
| `def validate_*`  | 30+         | Consolidate to utils/validators.py  |
| `def normalize_*` | 20+         | Consolidate to utils/normalizers.py |
| `def sanitize_*`  | 5+          | Consolidate to utils/sanitizers.py  |

#### YAML Usage (58 files):

- Direct `import yaml` in 58 files
- Custom wrapper: `from thegent.infra.fast_yaml_parser import yaml_load, yaml_dump`
- Recommendation: Use orjson + yaml everywhere

#### JSON Usage:

- `import json` - 7 files (should use orjson)
- `from thegent.utils.json_utils import json_dumps, json_loads` - Preferred pattern
- Recommendation: Standardize on json_utils

#### hashlib Usage:

- Direct `import hashlib` in 30+ files
- Recommendation: Create utils/hash_utils.py

---

## 4. DEPRECATION CANDIDATES

### 4.1 Replace with Stdlib

| Package     | Files | Alternative                      |
| ----------- | ----- | -------------------------------- |
| ruamel.yaml | 58    | PyYAML or stdlib yaml            |
| jsonschema  | 5     | fastjsonschema (already in deps) |

### 4.2 Consolidate into Shared Utils

| Pattern       | Count | Target File                  |
| ------------- | ----- | ---------------------------- |
| parse\_\*     | 50+   | thegent/utils/parsers.py     |
| validate\_\*  | 30+   | thegent/utils/validators.py  |
| normalize\_\* | 20+   | thegent/utils/normalizers.py |
| sanitize\_\*  | 5+    | thegent/utils/sanitizers.py  |

---

## 5. SECURITY FIXES APPLIED

| CVE            | Package           | Action                    |
| -------------- | ----------------- | ------------------------- |
| CVE-2025-69872 | diskcache         | Replaced with PersistDict |
| CVE-2026-26996 | minimatch         | Upgraded to 10.2.1        |
| CVE-2025-23207 | markdown-it-katex | Updated via bun           |
| -              | esbuild           | Updated via bun           |
| -              | ajv               | Updated via bun           |

---

## 6. RECOMMENDATIONS

### Priority 1: Consolidation (Low Effort)

1. Create `thegent/utils/parsers.py` - consolidate parse functions
2. Create `thegent/utils/validators.py` - consolidate validate functions
3. Replace `import yaml` with `from thegent.infra.fast_yaml_parser import yaml_load, yaml_dump`
4. Replace `import json` with `from thegent.utils.json_utils import json_dumps, json_loads`

### Priority 2: Dependency Cleanup (Medium Effort)

1. Remove ruamel.yaml if not used directly
2. Standardize on orjson for all JSON operations
3. Create hash_utils.py for hashlib wrappers

### Priority 3: Modernization (Higher Effort)

1. Consider pydantic v2 full adoption
2. Exploreattrs for classes
3. Consider attrs or dataclasses for simple DTOs

---

## 7. STATS

- Total Python files: 1000+
- Files with custom parsers: 91
- YAML imports: 58
- JSON imports (stdlib): 7
- hashlib direct imports: 30+
- tenacity usage: 20+

---

_Generated 2026-02-23_
