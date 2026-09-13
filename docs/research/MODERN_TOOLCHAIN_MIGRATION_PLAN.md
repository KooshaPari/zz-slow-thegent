<DONE>
# Modern Toolchain Migration Plan: pip/npm -> uv/bun & mise -> proto

**Status**: 🛠 **IN-PROGRESS** | **Date**: 2026-02-19
**Purpose**: Full modernization of the agentic workstation toolchain to achieve maximum performance (Rust/Zig-based tools) and unified management.

## 1. The Python Migration: `pip` -> `uv`

### 1.1 Strategy

- **Replace `pip install`** with `uv pip install`.
- **Replace `pipx`** with `uv tool install`.
- **Project Environments**: Use `uv venv` and `uv sync`.
- **Global Packages**: Migrate core AI/ML libs to `uv` managed tools where applicable.

### 1.2 Audit Results (Global Pip)

- **AI/ML**: `accelerate`, `litellm`, `openai`, `praw`.
- **Infrastructure**: `granian`, `uvicorn`, `httpx`, `opentelemetry`.
- **CLI Utilities**: `rich`, `typer`, `click`, `textual`.

### 1.3 Migration Steps

1. Ensure `uv` is installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
2. Alias `pip` to `uv pip` in `.zshrc.agent` and `thegent.profile.ps1`.
3. Migrate `thegent` installation to `uv tool install thegent`.

---

## 2. The JS Migration: `npm` -> `bun`

### 2.1 Strategy

- **Replace `npm install`** with `bun install`.
- **Replace `npm run`** with `bun run`.
- **Runtime**: Use `bun` as the default runtime for all agent-spawned JS tasks.

### 2.2 Migration Steps

1. Ensure `bun` is installed (`curl -fsSL https://bun.sh/install | bash`).
2. Update `trace/frontend/package.json` and others to support Bun lockfiles.
3. Replace global npm tools with `bun install -g`.

---

## 3. The Toolchain Manager: `mise` vs `proto`

### 3.1 Evaluation

| Feature         | `mise` (current)         | `proto` (proposed)       | `nix` (alternate)        |
| :-------------- | :----------------------- | :----------------------- | :----------------------- |
| **Language**    | Rust                     | Rust                     | C++/Nix                  |
| **Plugins**     | asdf-compatible (Legacy) | WASM-based (Modern/Safe) | Nix expressions          |
| **Speed**       | Very Fast                | Extremely Fast           | Varies (Fast evaluation) |
| **Safety**      | High                     | Maximum (WASM Sandboxed) | Maximum (Functional)     |
| **Ease of Use** | High                     | Very High                | Low (Steep curve)        |

### 3.2 Decision: `proto` for Agent Runtime

`proto` is preferred for agent-led environments because its WASM plugin system allows for cryptographically verified tool installation, which aligns with Tier 8 (Security & Forensics) of the AX Spec.

### 3.3 Migration Steps

1. Install `proto` (`curl -fsSL https://moonrepo.dev/install/proto.sh | bash`).
2. Mirror `mise` configuration into `.prototools`.
3. Gradually phase out `mise` hooks in favor of `proto use`.

---

## 4. Implementation Timeline

- **Phase 1 (Now)**: Update `install.sh` and `install.ps1` to prefer `uv` and `bun`.
- **Phase 2**: Add migration aliases to agent shell profiles.
- **Phase 3**: Implement `thegent tool migrate` command to automate the global package transition.
