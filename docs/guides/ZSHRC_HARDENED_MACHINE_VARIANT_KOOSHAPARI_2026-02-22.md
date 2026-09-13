# Hardened `zsh` Variant (Kooshapari Machine)

Targeted for:

- macOS arm64
- Homebrew at `/opt/homebrew`
- Plugin layout under `~/.zsh/plugins`
- Existing stack: `mise`, `fzf-tab`, `zsh-autosuggestions`, `fast-syntax-highlighting`, `starship`/`p10k`

## 1) `~/.zshrc` (fast boot + safe defaults)

```zsh
# thegent hardened machine-specific zshrc

[[ -z "${PS1:-}" ]] && return

# Base env
[[ -f "$HOME/.zshenv" ]] && source "$HOME/.zshenv"

# Security + history
setopt NO_BEEP HIST_IGNORE_DUPS HIST_IGNORE_SPACE SHARE_HISTORY
setopt EXTENDED_HISTORY INC_APPEND_HISTORY APPEND_HISTORY
setopt INTERACTIVE_COMMENTS NO_FLOW_CONTROL AUTO_CD CORRECT
umask 077
HISTFILE="${HOME}/.zsh_history"
HISTSIZE=200000
SAVEHIST=200000

# Stable PATH
typeset -U path PATH
path=(
  /opt/homebrew/bin
  /opt/homebrew/sbin
  "$HOME/.local/bin"
  "$HOME/bin"
  /usr/local/bin
  /usr/bin
  /bin
  /usr/sbin
  /sbin
)
export PATH

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"

# Compinit once/day pattern
autoload -Uz compinit add-zsh-hook
_compinit_deferred() {
  add-zsh-hook -d precmd _compinit_deferred
  local dump="${ZDOTDIR:-$HOME}/.zcompdump"
  if [[ -n ${dump}(#qN.mh+24) ]]; then
    compinit -d "$dump" 2>/dev/null
  else
    compinit -C -d "$dump" 2>/dev/null
  fi
}
add-zsh-hook precmd _compinit_deferred

# Fast initial prompt, replace after theme loads
PS1='%n@%m %1~ %# '

# Load local machine customizations
[[ -f "$HOME/.zshrc.local" ]] && source "$HOME/.zshrc.local"

# Notification env
export THGENT_NOTIFY_ENABLE=1
export THGENT_NOTIFY_VOICE_MODE=all
export THGENT_NOTIFY_VOICE_NAME="Siri"
export THGENT_NOTIFY_COOLDOWN_SEC=8
```

## 2) `~/.zshrc.local` (plugins + tools + prompt)

```zsh
# machine-specific local customizations

# Toolchain activation (mise first)
if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate zsh 2>/dev/null)"
fi

# Optional: Bun marker
if command -v bun >/dev/null 2>&1; then
  export USE_BUN_TOOLS=1
fi

# Defer heavy plugin/theme load until first prompt draw
autoload -Uz add-zsh-hook

_load_plugins_deferred() {
  add-zsh-hook -d precmd _load_plugins_deferred

  [[ -f "${HOME}/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh" ]] && \
    source "${HOME}/.zsh/plugins/fzf-tab/fzf-tab.plugin.zsh"

  [[ -f "${HOME}/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh" ]] && \
    source "${HOME}/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh"

  [[ -f "${HOME}/.zsh/plugins/fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh" ]] && \
    source "${HOME}/.zsh/plugins/fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh"
}
add-zsh-hook precmd _load_plugins_deferred

_load_prompt_deferred() {
  add-zsh-hook -d precmd _load_prompt_deferred
  if command -v starship >/dev/null 2>&1; then
    eval "$(starship init zsh 2>/dev/null)"
  elif [[ -f "${HOME}/.zsh/themes/powerlevel10k/powerlevel10k.zsh-theme" ]]; then
    source "${HOME}/.zsh/themes/powerlevel10k/powerlevel10k.zsh-theme"
  fi
}
add-zsh-hook precmd _load_prompt_deferred

# TTY self-heal for Ghostty/extended-key mode desync
_tty_self_heal() {
  stty sane 2>/dev/null || true
  stty intr '^C' quit '^\\' erase '^?' kill '^U' 2>/dev/null || true
  [[ -t 1 ]] && printf '\e[>4;0m' || true
  [[ -t 1 ]] && printf '\e[<u' || true
}
add-zsh-hook precmd _tty_self_heal

# Safe helpers
mkcd() {
  [[ -n "$1" ]] || { echo "usage: mkcd <dir>" >&2; return 2; }
  mkdir -p -- "$1" && cd -- "$1"
}

timezsh() {
  repeat 5 /usr/bin/time zsh -i -c exit
}

# AI helper as suggestion-only (never auto-run generated command)
ai-cmd() {
  [[ -n "$*" ]] || { echo "usage: ai-cmd <request>" >&2; return 2; }
  if (( $+commands[zsh-ai-cmd] )); then
    zsh-ai-cmd "$*"
  else
    echo "zsh-ai-cmd not installed" >&2
    return 1
  fi
}
```

## 3) Homebrew install set (machine-aligned)

```zsh
brew install fzf mise starship zsh-autosuggestions zsh-syntax-highlighting
```

## 4) Verification

```zsh
exec zsh
timezsh
zsh -i -c 'echo shell_ok'
```

## 5) Guardrails

- Keep plugin count minimal.
- Keep AI plugins suggestion-only.
- Prefer deferred loading over startup-time `eval` for heavy tools.
- Review any `curl | sh` installer before use.
