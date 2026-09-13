<DONE>
# Agent File Search — Unified Tool Research

> **Purpose**: Research a single/better tool for agents (Claude Code, Cursor, Codex) to replace ls, rg, grep as individual commands.
> **Status**: Research | **Date**: 2026-02-16

---

## 1. Problem

Agents run `ls -l`, `grep`, `rg` as separate shell commands. Each has different semantics, exclusions, and performance. Agents often run `ls -l` in project root (5m+ in node_modules). Need a unified approach across Claude Code, Cursor, Codex.

---

## 2. Current Landscape

| Tool             | Replaces | Respects .gitignore | Exclusions          | Speed              |
| ---------------- | -------- | ------------------- | ------------------- | ------------------ |
| **ls**           | —        | No                  | No                  | Slow in large dirs |
| **find**         | —        | No                  | Manual              | Slow               |
| **grep**         | —        | No                  | Manual              | Medium             |
| **fd**           | ls, find | Yes                 | -E flag, .gitignore | 10–35x faster      |
| **rg** (ripgrep) | grep     | Yes                 | -g, .gitignore      | 10x faster         |

**thegent hooks** already use fd (find) and rg (grep) via `common.sh` — but hooks run in thegent's context. Agent shells (IDE terminals) may not have these.

---

## 3. Options

### 3.1 fd + rg (Two Tools, Canonical Pair)

**Recommendation**: Standardize on **fd** (discovery) + **rg** (content search).

| Task                | Use                              | Example                                 |
| ------------------- | -------------------------------- | --------------------------------------- |
| List files in dir   | `fd -t f -d 1` or `fd -t d -d 1` | `fd -t f -d 1 -E node_modules -E .venv` |
| Find files by name  | `fd pattern`                     | `fd "test_" -e py`                      |
| Search file content | `rg pattern`                     | `rg "def main" --type py`               |

**Pros**: Both respect .gitignore; fd has -E for extra exclusions; fast; OSS; cross-platform.
**Cons**: Two tools; agents must learn both.

### 3.2 MCP Tool: thegent_files (Single Unified Tool)

Add `thegent_files` MCP tool that wraps fd + rg with project exclusions. Works in Claude Code, Cursor, Codex when MCP connected.

```
thegent_files(mode="list"|"search", path=".", depth=1, pattern=None, exclude=None)
```

- **mode=list**: List files (fd). `path`, `depth`, `type` (f|d), `exclude` (default: node_modules, .venv, .git, dist, build).
- **mode=search**: Search content (rg). `pattern`, `path`, `type`, `exclude`.

**Pros**: Single tool; built-in exclusions; same behavior across platforms; no shell dependency.
**Cons**: Requires MCP; doesn't help when agent uses raw shell.

### 3.3 IDE-Native Tools (Cursor, Claude Code)

| Platform        | Built-in                             | Use case                         |
| --------------- | ------------------------------------ | -------------------------------- |
| **Cursor**      | @codebase, @file, semantic search    | Prefer over shell when available |
| **Claude Code** | read_file, list_dir, codebase_search | Prefer over shell when available |
| **Codex**       | Varies                               | May need shell fallback          |

**Recommendation**: When IDE provides file/codebase tools, use those first. Fall back to fd + rg (or thegent_files) for terminal/shell.

### 3.4 ugrep / Other Unified Tools

- **ugrep** (universal grep): Combines grep + find; respects .gitignore. Single binary.
- **fd** + **rg**: Industry standard; better maintained; thegent already uses them.

**Verdict**: fd + rg is sufficient. ugrep is an alternative if we want one binary.

---

## 4. Recommended Strategy

| Layer                         | Tool                                  | When                                     |
| ----------------------------- | ------------------------------------- | ---------------------------------------- |
| **IDE (Cursor, Claude Code)** | Native @codebase, read_file, list_dir | First choice when available              |
| **MCP (thegent serve)**       | `thegent_files` (future)              | When agent uses MCP tools                |
| **Shell (all platforms)**     | **fd** (list/find) + **rg** (search)  | Terminal fallback; document as canonical |

**Agent instruction (add to skills, CLAUDE.md):**

> For file discovery and search, use **fd** (list/find) and **rg** (content search). Both respect .gitignore. Prefer `fd -t f -d 1 -E node_modules -E .venv` over `ls -l`; prefer `rg pattern` over `grep`. When IDE provides @codebase or read_file, use those first.

---

## 5. Implementation Roadmap

| Task                                               | Effort           | Impact                          |
| -------------------------------------------------- | ---------------- | ------------------------------- |
| Document fd + rg as canonical in skills, CLAUDE.md | 1–2 edits        | High                            |
| Add `thegent_files` MCP tool (list + search)       | 15–25 tool calls | High — unified across platforms |
| Ensure fd, rg in agent PATH (Brewfile, setup)      | 1–2 edits        | Medium                          |
| .agentignore support for thegent_files             | 4–6 tool calls   | Medium                          |

---

## 6. fd + rg Quick Reference (for Agents)

```bash
# List files in current dir (replaces ls -l)
fd -t f -d 1 -E node_modules -E .venv -E dist -E build

# List dirs
fd -t d -d 1 -E node_modules -E .venv

# Find files by name
fd "test_" -e py
fd ".md" docs/

# Search content (replaces grep)
rg "def main" --type py
rg "TODO" -g "!node_modules" -g "!.venv"
```

---

## 7. Tool Comparison Matrix

### 7.1 File Discovery Tools

| Tool           | Speed     | .gitignore | Exclusions | Cross-platform      | Maintenance |
| -------------- | --------- | ---------- | ---------- | ------------------- | ----------- |
| **fd**         | 10-35x ls | Yes        | -E flag    | Linux/macOS/Windows | Active      |
| **find**       | Slow      | No         | Manual     | Yes                 | Legacy      |
| **ls**         | Slowest   | No         | No         | Yes                 | Native      |
| **ripgrep -l** | Fast      | Yes        | -g         | Yes                 | Active      |
| **ugrep -g**   | Fast      | Yes        | -g         | Yes                 | Active      |
| **lsd**        | Medium    | No         | No         | Linux/macOS         | Active      |

### 7.2 Content Search Tools

| Tool      | Speed    | .gitignore | Exclusions   | Regex  | Maintenance |
| --------- | -------- | ---------- | ------------ | ------ | ----------- |
| **rg**    | 10x grep | Yes        | -g           | PCRE2  | Active      |
| **grep**  | Baseline | No         | Manual       | Basic  | Legacy      |
| **ugrep** | Fast     | Yes        | -g           | PCRE++ | Active      |
| **ack**   | Medium   | Yes        | --ignore-dir | Perl   | Moderate    |
| **ag**    | Fast     | Yes        | --ignore-dir | Rust   | Moderate    |

### 7.3 Unified/Bundled Tools

| Tool              | Replaces         | Pros                               | Cons           | Agent Fit     |
| ----------------- | ---------------- | ---------------------------------- | -------------- | ------------- |
| **ugrep**         | find + grep + ls | Single binary, fast                | Learning curve | Medium        |
| **fd + rg**       | find + grep      | Industry standard, well-documented | Two tools      | High          |
| **thegent_files** | MCP wrapper      | Built-in exclusions, MCP native    | MCP-only       | High (if MCP) |
| **IDE native**    | @codebase        | Semantic awareness                 | IDE-specific   | High (if IDE) |

### 7.4 Performance Comparison (Relative)

| Operation              | ls  | find | fd  | rg  | ugrep |
| ---------------------- | --- | ---- | --- | --- | ----- |
| `ls -l` in large dir   | 1x  | N/A  | 10x | N/A | N/A   |
| Find .py files         | N/A | 1x   | 15x | 8x  | 10x   |
| Search "TODO" in code  | N/A | N/A  | N/A | 10x | 8x    |
| Find + Search combined | N/A | 1x   | 5x  | 5x  | 4x    |

---

## 8. Implementation Checklist

### 8.1 Immediate Actions

- [ ] Document fd + rg as canonical in skills/
- [ ] Add fd + rg to Brewfile (ensure in PATH)
- [ ] Update CLAUDE.md with tool recommendations
- [ ] Create quick reference card for agents

### 8.2 MCP Tool Development

- [ ] Design `thegent_files` MCP tool interface
- [ ] Implement `list` mode (fd wrapper)
- [ ] Implement `search` mode (rg wrapper)
- [ ] Add default exclusions (node_modules, .venv, .git)
- [ ] Add `.agentignore` support
- [ ] Test on Linux, macOS, Windows

### 8.3 Agent Integration

- [ ] Update SKILL.md templates to use fd + rg
- [ ] Add fd + rg examples to agent training data
- [ ] Create fallback logic (IDE native → MCP → fd/rg → ls/grep)
- [ ] Document agent instruction for file operations

### 8.4 Verification

- [ ] Benchmark fd vs ls in node_modules-heavy project
- [ ] Benchmark rg vs grep in large codebase
- [ ] Test thegent_files MCP tool performance
- [ ] Verify exclusions work correctly

---

## 9. Cross-References

| Doc                                                                                       | Relevance                 |
| ----------------------------------------------------------------------------------------- | ------------------------- |
| [INDEXING_AND_OPTIMIZATION_SYSTEMS.md](../reference/INDEXING_AND_OPTIMIZATION_SYSTEMS.md) | Indexing systems overview |
| [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md)                     | Process optimization      |
| [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)  | Process automation        |

---

_Cross-ref: [INDEXING_AND_OPTIMIZATION_SYSTEMS.md](../reference/INDEXING_AND_OPTIMIZATION_SYSTEMS.md) · [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md)_

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Tool comparison matrix (§7), Implementation checklist (§8)

| Section | Added Content                                                          |
| ------- | ---------------------------------------------------------------------- |
| §7.1    | File Discovery Tools Comparison (fd, find, ls, ripgrep, ugrep, lsd)    |
| §7.2    | Content Search Tools Comparison (rg, grep, ugrep, ack, ag)             |
| §7.3    | Unified/Bundled Tools Matrix (ugrep, fd+rg, thegent_files, IDE native) |
| §7.4    | Performance Comparison (relative speeds)                               |
| §8      | Implementation Checklist (Immediate, MCP, Agent, Verification)         |

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md](./AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md) - Access audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
