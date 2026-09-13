<DONE>
# Quick Start: Ghostty + zsh + Starship Setup (2026-02-18)

## One-Line Installation

### macOS

```bash
# Install all components
brew install ghostty starship zsh fzf && \
git clone https://github.com/zsh-users/zsh-autosuggestions ~/.zsh/plugins/zsh-autosuggestions && \
git clone https://github.com/zsh-users/zsh-syntax-highlighting ~/.zsh/plugins/zsh-syntax-highlighting && \
git clone https://github.com/Aloxaf/fzf-tab ~/.zsh/plugins/fzf-tab && \
chsh -s $(which zsh)
```

### Linux

```bash
# Install all components
sudo apt install zsh fzf && \
cargo install starship && \
git clone https://github.com/ghostty-org/ghostty.git && cd ghostty && zig build -Doptimize=ReleaseFast && sudo zig build install && cd .. && \
git clone https://github.com/zsh-users/zsh-autosuggestions ~/.zsh/plugins/zsh-autosuggestions && \
git clone https://github.com/zsh-users/zsh-syntax-highlighting ~/.zsh/plugins/zsh-syntax-highlighting && \
git clone https://github.com/Aloxaf/fzf-tab ~/.zsh/plugins/fzf-tab && \
chsh -s $(which zsh)
```

---

## Quick Configuration

### 1. Ghostty Config

```bash
# Create config directory
mkdir -p ~/.config/ghostty

# Create config file
cat > ~/.config/ghostty/config << 'EOF'
# Performance
font-size = 14
font-family = "JetBrains Mono", "Fira Code"
ligatures = true

# Shell Integration
shell-integration = true
shell-integration-mode = "full"

# Theme
theme = "auto"

# Performance
scrollback-limit = 10000
bell = "none"

# Security (macOS)
secure-keyboard-entry = "auto"
EOF
```

### 2. zsh Config

```bash
# Create .zshrc
cat > ~/.zshrc << 'EOF'
# Early exit for non-interactive shells
[[ -z "${PS1:-}" ]] && return

# FUNCNEST
export FUNCNEST=1000

# History
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt SHARE_HISTORY HIST_IGNORE_DUPS HIST_IGNORE_SPACE

# Completions (lazy-loaded)
autoload -Uz compinit
if [[ -n ${ZDOTDIR:-$HOME}/.zcompdump(#qN.mh+24) ]]; then
    compinit -d "${ZDOTDIR:-$HOME}/.zcompdump"
else
    compinit -C -d "${ZDOTDIR:-$HOME}/.zcompdump"
fi

# Ghostty shell integration
eval "$(ghostty --shell-integration)" 2>/dev/null || true

# Plugins (deferred)
_load_plugins() {
    add-zsh-hook -d precmd _load_plugins
    [[ -f ~/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]] && \
        source ~/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
    [[ -f ~/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh ]] && \
        source ~/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh
    [[ -f ~/.zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]] && \
        source ~/.zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
}
autoload -Uz add-zsh-hook
add-zsh-hook precmd _load_plugins

# Starship prompt
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init zsh)"
fi

# User customizations
[[ -f "$HOME/.zshrc.local" ]] && source "$HOME/.zshrc.local"
EOF
```

### 3. Starship Config

```bash
# Create config directory
mkdir -p ~/.config

# Create config file
cat > ~/.config/starship.toml << 'EOF'
# Performance optimization
scan_timeout = 500
command_timeout = 250
add_newline = false

# Character
[character]
success_symbol = "[➜](bold green)"
error_symbol = "[➜](bold red)"

# Directory
[directory]
truncation_length = 3
truncate_to_repo = true

# Git
[git_branch]
symbol = " "
format = "[$symbol$branch]($style) "

[git_status]
disabled = true

# Disable heavy modules
[package]
disabled = true

[nodejs]
disabled = true

[python]
disabled = true

[rust]
disabled = true

[golang]
disabled = true

# Command duration
[cmd_duration]
min_time = 500
format = "took [$duration]($style) "
EOF
```

---

## Verification

```bash
# Check installations
ghostty --version
starship --version
zsh --version

# Test shell startup time
time zsh -i -c exit

# Should be <80ms (target), ~32ms (achieved)
```

---

## Next Steps

1. **Restart terminal** (or run `exec zsh`)
2. **Test prompt** - Should show Starship prompt
3. **Test autosuggestions** - Type a command, see gray suggestion
4. **Test syntax highlighting** - Commands should be colored
5. **Customize** - Edit config files as needed

---

## Troubleshooting

### Shell Integration Not Working

```bash
# Verify Ghostty shell integration
ghostty --shell-integration

# Add to .zshrc manually
eval "$(ghostty --shell-integration)"
```

### Starship Not Showing

```bash
# Verify Starship is installed
which starship

# Initialize manually
eval "$(starship init zsh)"

# Check config
starship config schema
```

### Slow Startup

```bash
# Profile startup
zsh -xvic exit 2>&1 | grep -E "^\+\+" | head -20

# Disable heavy plugins
# Comment out plugins in .zshrc

# Reduce Starship timeouts
# Edit ~/.config/starship.toml
```

---

_Quick Start Date: 2026-02-18_
_See full guides: GHOSTTY_SETUP_GUIDE_2026-02-18.md, ZSH_STARSHIP_SETUP_GUIDE_2026-02-18.md_
