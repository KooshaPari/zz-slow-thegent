# Cross-Platform Setup Guide

## Overview

Complete cross-platform installation for thegent supporting:

- ✅ **macOS** (Intel & Apple Silicon)
- ✅ **Linux** (Ubuntu, Debian, Fedora, Arch, etc.)
- ✅ **Windows 11** (Native PowerShell)
- ✅ **WSL2** (Windows Subsystem for Linux)
- ✅ **PowerShell** (pwsh on all platforms)

## Installation Scripts

### Bash/Zsh Script (Unix-like)

```bash
# macOS, Linux, WSL2
chmod +x install.sh
./install.sh
```

### PowerShell Script (All Platforms)

```powershell
# Windows, macOS, Linux, WSL2
pwsh -ExecutionPolicy Bypass -File install.ps1
```

## Platform-Specific Details

### macOS

**Package Manager:** Homebrew
**Shell:** zsh (default), bash, PowerShell (via Homebrew)

**Installation:**

```bash
./install.sh
```

**Features:**

- Full Homebrew integration
- Native zsh support
- Apple Silicon optimized

---

### Linux (Ubuntu/Debian)

**Package Manager:** apt
**Shell:** bash, zsh, PowerShell (via snap/package)

**Installation:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y curl git
./install.sh
```

**Features:**

- Automatic package manager detection
- Supports apt, yum, dnf, pacman
- WSL2 detection and optimization

---

### Windows 11 (Native)

**Package Manager:** Scoop (recommended) or Chocolatey
**Shell:** PowerShell (pwsh)

**Installation:**

```powershell
# Option 1: PowerShell script
pwsh -ExecutionPolicy Bypass -File install.ps1

# Option 2: Bash script (via Git Bash/WSL)
./install.sh
```

**Features:**

- Scoop integration
- PowerShell profile configuration
- Windows PATH integration

---

### WSL2 (Windows Subsystem for Linux)

**Package Manager:** apt (Ubuntu) or distro-specific
**Shell:** bash, zsh, PowerShell (via pwsh)

**Installation:**

```bash
# In WSL2 terminal
./install.sh

# Or PowerShell
pwsh -ExecutionPolicy Bypass -File install.ps1
```

**Features:**

- Automatic WSL2 detection
- Windows PATH integration
- Cross-platform file access
- Windows interop tools (wslu)

---

## Cross-Platform Tools

### Universal Tools (Work on All Platforms)

| Tool        | macOS | Linux | Windows | WSL2 |
| ----------- | ----- | ----- | ------- | ---- |
| **mise**    | ✅    | ✅    | ✅      | ✅   |
| **tea**     | ✅    | ✅    | ✅      | ✅   |
| **chezmoi** | ✅    | ✅    | ✅      | ✅   |
| **Python**  | ✅    | ✅    | ✅      | ✅   |
| **Node.js** | ✅    | ✅    | ✅      | ✅   |
| **Ruby**    | ✅    | ✅    | ✅      | ✅   |
| **Rust**    | ✅    | ✅    | ✅      | ✅   |
| **Bun**     | ✅    | ✅    | ✅      | ✅   |

### Platform-Specific Tools

| Tool           | macOS | Linux | Windows | WSL2 |
| -------------- | ----- | ----- | ------- | ---- |
| **Homebrew**   | ✅    | ✅    | ❌      | ✅   |
| **Scoop**      | ❌    | ❌    | ✅      | ❌   |
| **apt/yum**    | ❌    | ✅    | ❌      | ✅   |
| **PowerShell** | ✅    | ✅    | ✅      | ✅   |

## Installation Flow

### 1. Platform Detection

- Automatically detects OS (macOS, Linux, Windows, WSL2)
- Detects package manager (Homebrew, apt, Scoop, etc.)
- Detects shell (bash, zsh, PowerShell)

### 2. Package Manager Installation

- Installs Homebrew (macOS/Linux) if missing
- Installs Scoop (Windows) if missing
- Updates system packages

### 3. Core Tools Installation

- **mise** - Version manager
- **tea** - Ephemeral package runner
- **chezmoi** - Dotfile manager

### 4. System Packages

- Git, curl, wget
- Development tools (Python, Node, Ruby, Rust)
- Shell tools (fzf, ripgrep, fd, bat, etc.)

### 5. Configuration

- mise global tool versions
- Shell configuration (.zshenv or PowerShell profile)
- Templates directory
- Helper scripts

### 6. thegent Setup

- Installs dependencies
- Builds Rust extensions
- Sets up shell symlinks (Unix-like)

## Shell Configuration

### Bash/Zsh (Unix-like)

**File:** `~/.zshenv` or `~/.bashrc`

```bash
# mise hook
if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate zsh)"
fi

# PATH
export PATH="$HOME/.local/bin:$PATH"
```

### PowerShell (All Platforms)

**File:** `$PROFILE` (platform-specific)

```powershell
# mise hook
if (Get-Command mise -ErrorAction SilentlyContinue) {
    mise activate pwsh | Out-String | Invoke-Expression
}

# PATH
$env:PATH = "$HOME\.local\bin;$env:PATH"
```

**Profile Locations:**

- Windows: `$HOME\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
- macOS/Linux: `~/.config/powershell/Microsoft.PowerShell_profile.ps1`

## WSL2 Specific Configuration

### Windows Integration

**File:** `~/.wslconfig`

```ini
[wsl2]
interop.appendWindowsPath=true
```

### Access Windows Files

```bash
# Windows drives accessible at:
/mnt/c/Users/YourName
/mnt/d/

# Windows executables (if PATH integrated)
notepad.exe
code.exe
```

## Verification

### Check Installation

```bash
# All platforms
mise list
python --version
node --version
ruby --version

# PowerShell
mise list
python --version
node --version
ruby --version
```

### Platform Detection

```bash
# Bash/Zsh
uname -s
echo $PLATFORM

# PowerShell
$PSVersionTable.Platform
(Get-Platform).Platform
```

## Multi-Device Sync

### Using chezmoi (Cross-Platform)

```bash
# Initialize
chezmoi init https://github.com/yourusername/dotfiles.git

# Add files
chezmoi add ~/.zshrc
chezmoi add ~/.mise.toml
chezmoi add $PROFILE  # PowerShell

# On new machine
chezmoi init https://github.com/yourusername/dotfiles.git
chezmoi apply
```

### Platform-Specific Sync

**macOS/Linux:**

```bash
brew bundle dump
```

**Windows:**

```powershell
scoop export > scoop-packages.json
```

## Troubleshooting

### Windows Issues

**PowerShell Execution Policy:**

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Scoop Installation:**

```powershell
iwr -useb get.scoop.sh | iex
```

### WSL2 Issues

**Windows PATH Not Working:**

```bash
# Check .wslconfig
cat ~/.wslconfig

# Restart WSL2
wsl --shutdown
```

**File Permissions:**

```bash
# Fix permissions
sudo chown -R $USER:$USER ~/.local
```

### Linux Issues

**Missing Dependencies:**

```bash
# Ubuntu/Debian
sudo apt-get install -y build-essential curl git

# Fedora
sudo dnf install -y gcc make curl git

# Arch
sudo pacman -S base-devel curl git
```

### macOS Issues

**Homebrew Not Found:**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
# or
eval "$(/usr/local/bin/brew shellenv)"
```

## Platform Comparison

| Feature             | macOS           | Linux           | Windows | WSL2            |
| ------------------- | --------------- | --------------- | ------- | --------------- |
| Native Performance  | ✅              | ✅              | ✅      | ⚠️              |
| Package Manager     | Homebrew        | apt/yum/etc     | Scoop   | apt/yum/etc     |
| Shell Options       | zsh, bash, pwsh | bash, zsh, pwsh | pwsh    | bash, zsh, pwsh |
| Windows Integration | ❌              | ❌              | ✅      | ✅              |
| File System         | APFS            | ext4            | NTFS    | ext4 (WSL)      |
| GUI Apps            | ✅              | ✅              | ✅      | ⚠️ (via X11)    |

## Best Practices

### 1. Use mise for Tool Versions

Works identically on all platforms:

```bash
mise install python@3.12
mise use python@3.12
```

### 2. Use tea for Ephemeral Tools

Run tools without installing:

```bash
tea python@3.12 script.py
```

### 3. Use chezmoi for Configs

Sync dotfiles across all platforms:

```bash
chezmoi add ~/.zshrc
chezmoi add $PROFILE
```

### 4. Platform-Specific Configs

Use chezmoi templates for platform differences:

```bash
chezmoi add --template ~/.zshrc
```

## Next Steps

1. ✅ Run installation script for your platform
2. ✅ Restart terminal/PowerShell
3. ✅ Verify installation: `mise list`
4. ✅ Start using thegent!

## Support

- See `INSTALL_README.md` for detailed installation guide
- See `SYSTEM_WIDE_ALTERNATIVES.md` for tool alternatives
- Platform-specific issues? Check troubleshooting section above

---

**Cross-platform support:** ✅ Complete
**Platforms:** macOS, Linux, Windows 11, WSL2
**Shells:** bash, zsh, PowerShell
