# Dotfile Manager Integration

Use thegent with chezmoi, yadm, dotbot, or other dotfile managers.

---

## 1. One-Command Setup (Recommended)

For most users, the bootstrap one-liner is enough:

```bash
curl -fsSL https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/bootstrap.sh | sh -s -- install
```

This installs thegent and runs `install -t all` + `install-shims`. No dotfile manager required.

---

## 2. chezmoi

### Option A: Run thegent via script

Add a script that runs on `chezmoi apply`:

```yaml
# ~/.local/share/chezmoi/run_once_install-thegent.sh
#!/usr/bin/env bash
set -e
if command -v thegent >/dev/null 2>&1; then
thegent install -t all
thegent install-shims
fi
```

```bash
chmod +x ~/.local/share/chezmoi/run_once_install-thegent.sh
```

### Option B: Template for .zshrc / .bashrc

If you manage shell config with chezmoi, ensure `~/.local/bin` is in PATH:

```bash
# {{ .chezmoi.sourceDir }}/dot_zshrc.tmpl
export PATH="${HOME}/.local/bin:${PATH}"
# ... rest of your config
```

### Option C: Managed thegent config

thegent writes to `~/.claude/`, `~/.cursor/`, `~/.config/thegent/`. To manage these with chezmoi:

```bash
# Add to chezmoi
chezmoi add ~/.config/thegent
chezmoi add ~/.claude/skills
```

---

## 3. yadm

Similar to chezmoi. Add a bootstrap script:

```bash
# ~/.local/bin/thegent-bootstrap
#!/usr/bin/env bash
thegent install -t all
thegent install-shims
```

Track it: `yadm add ~/.local/bin/thegent-bootstrap` (or run after `yadm clone`).

---

## 4. dotbot

Add to your `install.conf.yaml`:

```yaml
- shell:
    - command: thegent install -t all
      stdin: false
      stdout: true
    - command: thegent install-shims
      stdin: false
      stdout: true
```

---

## 5. Nix home-manager (Declarative)

For Nix users, home-manager is the preferred "dotfile" approach:

```nix
# flake.nix
inputs.thegent.url = "github:kooshapari/thegent";

# home.nix
{ inputs, pkgs, ... }: {
  imports = [ inputs.thegent.homeManagerModules.thegent ];
  programs.thegent = {
    enable = true;
    package = inputs.thegent.packages.${pkgs.system}.thegent;
    installTargets = [ "claude-code" "cursor" "envrc" "shell" ];
    installShims = true;
    installLockCleanupService = true;
  };
}
```

Run `home-manager switch` — no manual `thegent install` needed.

---

## 6. What thegent Installs

| Target      | Path                          |
| ----------- | ----------------------------- |
| claude-code | `~/.claude/` (skills, hooks)  |
| cursor      | `~/.cursor/` (rules)          |
| codex       | `~/.codex/`                   |
| droid       | `~/.factory/`                 |
| envrc       | `~/.envrc`                    |
| shell       | `~/.zshenv`, `~/.zshrc`, etc. |
| shims       | `~/.local/bin`                |

Choose which paths to manage with your dotfile manager; thegent will merge/overwrite on `install`.

---

## 7. Cross-Device Bundle Governance

For reproducible user/dev/agent environments across machines:

- Keep first-party config in git (repo + dotfiles manager).
- Keep third-party bundle definitions in a tracked manifest (default path: `~/.config/thegent/third_party_bundles.json`).
- Sync that manifest through your dotfiles workflow (chezmoi/yadm/etc.) so every device applies the same bundle set.
- Do not use `git worktree` directories or nested repos as canonical config storage; treat them as execution workspaces only.

Recommended governance fields for third-party items:

- immutable source reference (`commit` or `tag`)
- integrity value (`checksum`)
- owner/review metadata
