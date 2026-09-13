# Hardened Minimal `~/.zshrc` Template (2026)

## Goals

- Fast startup
- Predictable behavior
- Safer command workflow
- Optional AI helper hooks with explicit confirmation

## Template

```zsh
# ------------------------------
# Hardened Minimal zshrc (2026)
# ------------------------------

# Safety defaults
setopt NO_BEEP
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE
setopt SHARE_HISTORY
setopt EXTENDED_HISTORY
setopt INC_APPEND_HISTORY
setopt APPEND_HISTORY
setopt INTERACTIVE_COMMENTS
setopt NO_FLOW_CONTROL
setopt AUTO_CD
setopt CORRECT

# Keep permissions strict
umask 077

# History sizing
HISTFILE="${HOME}/.zsh_history"
HISTSIZE=200000
SAVEHIST=200000

# PATH (keep explicit and stable)
typeset -U path PATH
path=(
  "$HOME/.local/bin"
  "$HOME/bin"
  /opt/homebrew/bin
  /usr/local/bin
  /usr/bin
  /bin
  /usr/sbin
  /sbin
)
export PATH

# XDG-friendly defaults
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"

# Fast completion init (cache)
autoload -Uz compinit
if [[ -n "${ZDOTDIR:-}" ]]; then
  _zcompdump="${ZDOTDIR}/.zcompdump"
else
  _zcompdump="${HOME}/.zcompdump"
fi
compinit -d "$_zcompdump"

# Safer completions
zstyle ':completion:*' menu select
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "${XDG_CACHE_HOME}/zsh"
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'

# Core aliases
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
alias grep='grep --color=auto'
alias ..='cd ..'
alias ...='cd ../..'
alias g='git'

# Quality-of-life functions
mkcd() {
  [[ -n "$1" ]] || { echo "usage: mkcd <dir>" >&2; return 2; }
  mkdir -p -- "$1" && cd -- "$1"
}

# Startup profiling helper
timezsh() {
  repeat 5 /usr/bin/time zsh -i -c exit
}

# Optional: deferred heavy init (only if zsh-defer exists)
if (( $+commands[zsh-defer] )); then
  zsh-defer source "${HOME}/.config/zsh/heavy-init.zsh"
fi

# Optional: fast node manager (fnm) over nvm
if (( $+commands[fnm] )); then
  eval "$(fnm env --use-on-cd)"
fi

# Optional AI helper (suggestion only; no auto execute)
ai-cmd() {
  [[ -n "$*" ]] || { echo "usage: ai-cmd <plain english request>" >&2; return 2; }
  if (( $+commands[zsh-ai-cmd] )); then
    zsh-ai-cmd "$*"
  else
    echo "zsh-ai-cmd not installed" >&2
    return 1
  fi
}

# Explicit confirmation wrapper for risky commands
confirm-run() {
  [[ -n "$*" ]] || { echo "usage: confirm-run <command...>" >&2; return 2; }
  echo "About to run: $*"
  read -r "?Proceed? [y/N] " _ok
  [[ "$_ok" == [yY] ]] || return 1
  eval "$*"
}
```

## Optional plugin block

Load only if installed; keep list short.

```zsh
# zsh-autosuggestions
[[ -f /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]] && \
  source /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh

# zsh-syntax-highlighting
[[ -f /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]] && \
  source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
```

## Optional prompt block (Powerlevel10k)

```zsh
[[ -r "${HOME}/.p10k.zsh" ]] && source "${HOME}/.p10k.zsh"
```

## Hardening notes

- Keep AI helpers as suggestion-only.
- Avoid `curl ... | sh` installers unless verified.
- Keep plugin count low; measure with `timezsh` after each change.
- Prefer lazy/deferred load for heavy tooling.

## Quick install flow

```zsh
cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d%H%M%S)
# paste template into ~/.zshrc
exec zsh
timezsh
```
