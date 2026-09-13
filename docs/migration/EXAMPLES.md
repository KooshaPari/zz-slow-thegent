# Usage Examples

## Command-Line Examples

### Tool Detection

```bash
# Detect all tools
thegent-tool-detect

# Output:
# Detected 6 tools:
#   fd: /usr/local/bin/fd
#   hash: /usr/bin/sha256sum
#   jq: /usr/local/bin/jq
#   pgrep: /usr/bin/pgrep
#   rg: /usr/local/bin/rg
#   timeout: /usr/bin/timeout

# Detect specific tool
thegent-tool-detect jq
# Output: /usr/local/bin/jq

# Export as shell variables
eval "$(thegent-tool-detect --format shell)"
echo $JQ_CMD  # /usr/local/bin/jq

# JSON output
thegent-tool-detect --format json
# Output: {"fd": "/usr/local/bin/fd", "jq": "/usr/local/bin/jq", ...}

# Check cache status
thegent-tool-detect --cache-stats
# Output:
# Cache Statistics:
#   Tools cached: 6
#   Age: 1234 seconds
#   Valid: yes
```

### PATH Resolution

```bash
# Resolve single binary
thegent-path-resolve codex
# Output: /usr/local/bin/codex

# Resolve multiple binaries
thegent-path-resolve codex --additional maturin cargo
# Output:
# /usr/local/bin/codex
# /Users/username/.cargo/bin/maturin
# /Users/username/.cargo/bin/cargo

# Skip directories
thegent-path-resolve codex --skip /usr/local/bin
# Output: (finds next match or exits with error)

# JSON output
thegent-path-resolve codex --format json
# Output: {"codex": "/usr/local/bin/codex"}
```

## Python Examples

### Tool Detection

```python
from thegent_tool_detect import detect_tools, detect_tool

# Detect all tools
tools = detect_tools()
print(tools)
# {'fd': '/usr/local/bin/fd', 'jq': '/usr/local/bin/jq', ...}

# Detect single tool
path = detect_tool("jq")
if path:
    print(f"Found jq at: {path}")
else:
    print("jq not found")
```

### PATH Resolution

```python
from thegent_path_resolve import resolve_binary, PathResolver

# Simple usage
path = resolve_binary("codex")
if path:
    print(f"Found codex at: {path}")

# With skip directories
resolver = PathResolver.with_skip_dirs(["/usr/local/bin"])
path = resolver.resolve("codex")

# Resolve multiple at once (more efficient)
resolver = PathResolver.new()
results = resolver.resolve_many(["codex", "maturin", "cargo"])
for name, path in results.items():
    if path:
        print(f"{name}: {path}")
```

### Process Discovery

```python
from thegent_discovery import DiscoveryInterface

discovery = DiscoveryInterface()
agents = discovery.scan_agents()

print(f"Found {len(agents)} agents:")
for agent in agents:
    print(f"  {agent['name']}: PID {agent['pid']} in {agent['cwd']}")
    if agent["session_id"]:
        print(f"    Session: {agent['session_id']}")
```

## Integration Examples

### Shell Script Integration

```bash
#!/usr/bin/env bash
# Use tool detection in shell scripts

# Source tool detection
eval "$(thegent-tool-detect --format shell)"

# Use detected tools
if [[ -n "$JQ_CMD" ]]; then
    echo "Using jq at: $JQ_CMD"
    "$JQ_CMD" '.version' package.json
fi
```

### Python Script Integration

```python
#!/usr/bin/env python3
"""Example script using thegent tools"""

from thegent_tool_detect import detect_tool
from thegent_path_resolve import resolve_binary
import subprocess

# Detect tools
jq_path = detect_tool("jq")
if jq_path:
    result = subprocess.run([jq_path, ".version"], input=open("package.json").read(), capture_output=True, text=True)
    print(f"Version: {result.stdout.strip()}")
```

### Hook Integration

```python
# In hook script
from thegent_tool_detect import detect_tools
from thegent_path_resolve import resolve_binary

# Fast tool detection
tools = detect_tools()
jq_cmd = tools.get("jq", "jq")  # Fallback to 'jq' if not found

# Fast PATH resolution
codex_path = resolve_binary("codex")
if codex_path:
    # Use codex_path
    pass
```

## Performance Comparison

### Before (Bash)

```bash
# Slow: 60ms
JQ_CMD="$(command -v jaq 2>/dev/null || command -v jq 2>/dev/null || echo jq)"
RG_CMD="$(command -v rg 2>/dev/null || true)"
FD_CMD="$(command -v fd 2>/dev/null || command -v fdfind 2>/dev/null || true)"
```

### After (Rust)

```python
# Fast: 1ms (cached), 10ms (uncached)
from thegent_tool_detect import detect_tools

tools = detect_tools()
```

**Improvement**: 60x faster (cached), 6x faster (uncached)

## Real-World Use Cases

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
- name: Detect tools
  run: |
    eval "$(thegent-tool-detect --format shell)"
    echo "Using jq: $JQ_CMD"
    echo "Using rg: $RG_CMD"
```

### Development Script

```bash
#!/usr/bin/env bash
# dev-script.sh

# Fast tool detection
eval "$(thegent-tool-detect --format shell)"

# Use tools
"$RG_CMD" "TODO" src/
"$JQ_CMD" '.dependencies' package.json
```

### Python Application

```python
# app.py
from thegent_tool_detect import detect_tools
from thegent_path_resolve import resolve_binary


class ToolManager:
    def __init__(self):
        self.tools = detect_tools()

    def get_tool(self, name: str) -> str:
        return self.tools.get(name, name)  # Fallback to name

    def resolve(self, name: str) -> str | None:
        return resolve_binary(name)
```


---
## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
