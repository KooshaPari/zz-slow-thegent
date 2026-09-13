# Installation Guide

This guide provides step-by-step instructions for installing thegent on different platforms.

---

## One Command for New Users

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/bootstrap.sh | sh -s -- install
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/install.ps1 | iex
```

The bootstrap runs: install thegent → `install -t all` → `install-shims` → `setup` → `doctor`. For Nix users, see [Nix + home-manager](#nix--home-manager-declarative) for declarative setup.

---

## Toolchain Manager Policy (Canonical)

Use these roles consistently across macOS/Linux/Windows and across devices:

> **Control-plane note:** treat `thegent` as your declarative environment-management/install control plane ("nixfiles"-style). Runtime/tool dependencies remain pinned and executed by their native ecosystems; thegent governs installation targets, policy, and cross-platform orchestration.

- `mise`: runtime/version manager for language toolchains (Python/Node/Go/etc.) using repo pins (`.mise.toml`).
- `uv`: Python package + virtualenv manager for project dependencies and CLI installs.
- `Homebrew` (`Brewfile`): macOS system package manager for host tools.
- `nix`: optional strict/declarative mode (`flake.nix`, `home-manager`, `nix-darwin`) when teams need stronger reproducibility.

Important distinction:

- **End-user install** (just run thegent): use bootstrap, `uv tool install`, `pipx`, or package-manager install.
- **Repository development** (working on this repo): follow `task setup` + `task doctor`, which currently expects `brew` + `uv` and can optionally layer `mise`/`nix`.

---

## 1. Quick Installation (All Platforms)

### pip (default)

```bash
pip install thegent
```

### uv (recommended — fast, isolated)

```bash
uv tool install thegent
```

### pipx (isolated, no venv pollution)

```bash
pipx install thegent
```

### Bootstrap (one-liner)

**Unix:**

```bash
curl -fsSL https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/bootstrap.sh | sh -s -- install
```

**Windows:**

```powershell
irm https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/install.ps1 | iex
```

Installs via uv → pipx → pip, then runs `thegent install -t all`, `thegent install-shims`, `thegent setup`, and `thegent doctor`. Options: `--no-setup` (CLI only), `--full` (setup --full), `THGENT_BOOTSTRAP_DEPS=1` (install ripgrep, fd, jq).

---

## 2. Post-Installation Setup

After installation, run the setup command to configure your shell and environment:

```bash
thegent install --target all
```

**Full setup (one command):** Run everything — install to all targets, shims, lock-cleanup service, MCP service:

```bash
thegent setup --full
```

This runs: `install -t all`, `install-shims`, optional `install-shims --system` (with confirm), lock-cleanup daemon, and MCP launchd service on macOS. Use `thegent setup --full --no-wizard` to skip the provider wizard.

### Provider setup dependency (important)

`thegent setup` delegates provider onboarding to `cliproxyctl`.
`cliproxyctl` is a Go binary and is **not** installed by `uv tool install` / `uv pip install`.

If missing, setup now attempts to auto-install it from Go:

```bash
go install github.com/kooshapari/cliproxyapi-plusplus/cmd/server@latest

# If your environment cannot install this package from remote, setup also
# auto-builds from a local `cliproxyapi-plusplus` checkout when available:
# (cd ../cliproxyapi-plusplus && go build -o cli-proxy-api-plus ./cmd/server && ./cli-proxy-api-plus)
# then set THGENT_CLIPROXYCTL_BINARY to that binary path.
```

If you already have it elsewhere, point the CLI directly:

```bash
export THGENT_CLIPROXYCTL_BINARY=/path/to/cliproxyctl
```

Verify the installation:

```bash
thegent --help
thegent doctor
```

---

## 3. Platform-Specific Installation

### macOS

#### Homebrew (Recommended)

```bash
brew install thegent
```

#### Nix

```bash
nix profile install github:kooshapari/thegent
```

#### Nix + home-manager (declarative)

Add thegent to your flake and home-manager config. On `home-manager switch`, thegent is installed and `thegent install -t all` runs automatically:

```nix
# flake.nix
inputs.thegent.url = "github:kooshapari/thegent";

# home.nix
{ inputs, pkgs, ... }: {
  imports = [ inputs.thegent.homeManagerModules.thegent ];
  programs.thegent = {
    enable = true;
    package = inputs.thegent.packages.${pkgs.system}.thegent;  # optional; omit if using pip/uv
    installTargets = [ "claude-code" "cursor" "envrc" "shell" ];
    installShims = true;
    installLockCleanupService = true;
  };
}
```

See [DOTFILES_INTEGRATION.md](DOTFILES_INTEGRATION.md) for chezmoi, yadm, and other dotfile managers.

#### nix-darwin (macOS system services)

For MCP service and lock-cleanup timer via launchd:

```nix
# darwin-configuration.nix
{ inputs, pkgs, ... }: {
  imports = [ inputs.thegent.nixDarwinModules.thegent ];
  thegent = {
    enable = true;
    enableMcpService = true;
    enableLockCleanup = true;
    package = inputs.thegent.packages.${pkgs.system}.thegent;
  };
}
```

#### pip

```bash
pip3 install thegent
```

### Linux

#### Ubuntu/Debian (apt)

```bash
sudo apt update
sudo apt install thegent
```

#### CentOS/RHEL (yum)

```bash
sudo yum install thegent
```

#### Nix

```bash
nix profile install github:kooshapari/thegent
```

#### pip

```bash
pip3 install thegent
```

### Windows

#### Bootstrap (one command)

```powershell
irm https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/install.ps1 | iex
```

#### winget (Recommended)

```powershell
winget install kooshapari.thegent
```

#### pip

```powershell
pip install thegent
```

#### MSI Installer

1. Download the latest `thegent-setup.exe` from the [GitHub Releases](https://github.com/kooshapari/thegent/releases) page.
2. Run the installer and follow the on-screen instructions.

---

## 4. Shell Configuration

Configure your shell to enable autocompletion and path integration:

| Platform    | Command                                           |
| ----------- | ------------------------------------------------- |
| **macOS**   | `thegent install --target shell` (for zsh)        |
| **Linux**   | `thegent install --target shell` (for bash/zsh)   |
| **Windows** | `thegent install --target shell` (for PowerShell) |

### Shell completion

Enable tab completion for thegent commands:

```bash
# Zsh (add to ~/.zshrc)
thegent --install-completion zsh

# Bash
thegent --install-completion bash

# Fish
thegent --install-completion fish
```

Restart your shell or run `source ~/.zshrc` (or equivalent) to activate.

---

## 5. Project Setup (Optional)

For project-specific configuration:

```bash
# Install git hooks (pre-commit, pre-push)
thegent setup --hooks

# Sync thegent-skills to ~/.claude, ~/.cursor
thegent setup --skills
```

## 5.1 Bundle and Worktree Governance

For long-term cross-device/cross-platform setup hygiene:

- First-party install assets (repo-owned shell/config/hook files) should be tracked in this repo and installed by `thegent install`.
- Third-party/community assets should be declared in an external bundle manifest (`~/.config/thegent/third_party_bundles.json` by default) and installed via bundle options.
- Worktrees and nested git repos are execution surfaces, not canonical config storage.

Policy target for third-party bundles:

- Pin to immutable source refs (commit/tag).
- Record integrity metadata (checksum) in your governance process.
- Keep manifests versioned in your dotfiles/config repo so they sync across devices.

---

## 6. Provider Configuration

Configure your AI providers (Claude, OpenAI, Gemini, etc.) using the built-in login tool:

```bash
# Example for Claude
thegent cliproxy login claude

# Example for OpenAI/Codex
thegent cliproxy login codex
```

This will open your browser to complete the OAuth flow and store the necessary tokens securely.

---

## 7. Starting the MCP Server

To use thegent with tools like Cursor or Claude Code, start the MCP server:

```bash
thegent serve
```

For continuous background operation, install it as a service:

```bash
# macOS/Linux
thegent cliproxy service install
thegent cliproxy service start

# Linux (systemd)
thegent mcp service install
sudo systemctl start thegent-mcp
```

---

## 8. Dev Containers (Codespaces / VS Code)

Use thegent inside GitHub Codespaces or VS Code Dev Containers:

1. **In thegent repo:** Open in Codespaces or "Reopen in Container" — the `.devcontainer/` config installs thegent from source.
2. **In your project:** Add to `.devcontainer/devcontainer.json`:

```json
{
  "features": {
    "ghcr.io/devcontainers/features/python:1": {}
  },
  "postCreateCommand": "pip install uv && (uv tool install thegent 2>/dev/null || pip install thegent 2>/dev/null) || true",
  "remoteEnv": {
    "PATH": "${containerEnv:PATH}:${containerEnv:HOME}/.local/bin"
  },
  "forwardPorts": [3847]
}
```

---

## 9. System Install (Advanced)

For agent-as-system-user or CI deployments:

```bash
thegent install -t system
```

This installs to `/opt/thegent` (or `--prefix`). Afterward, run:

```bash
thegent install-shims --prefix /opt/thegent
```

This installs the git wrapper to `$prefix/bin` for nix/direnv compatibility. Use `--system` for `/usr/local` or `--prefix /custom/path` for a custom install root.

### Agent Harness Shim Install

To install the Rust harness shims directly:

```bash
zsh scripts/install-thegent-shims.sh
```

This installs `thegent-shims` plus user-facing harness wrappers in `~/.local/bin`:

- `dex -> codex` (adds `--search` and codex bypass flag unless `--native`)
- `clode -> claude` (adds skip-permissions flag unless `--native`)
- `roid -> droid` and `fanta -> ante` (exec path adds unsafe skip flag unless `--native`)
- `cline`, `roocode`, `opencode` passthrough wrappers

---

## 10. Real-World Installation Flow Example (macOS)

```bash
# 1. Install via Homebrew
brew install thegent

# 2. Post-installation setup
thegent install --target all

# 3. Verify installation
thegent doctor

# 4. Configure providers
thegent cliproxy login anthropic
thegent cliproxy login openai

# 5. Start MCP server
thegent serve

# 6. Verify everything works
thegent list-agents
thegent run "Hello, world!" --agent codex
```
