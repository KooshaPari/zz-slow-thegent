# Complete System Installation Guide

## Overview

The `install.sh` script sets up your entire system for thegent, installing all required packages, tools, configurations, and templates.

## What Gets Installed

### Package Managers

- **Homebrew** - System package manager for macOS
- **mise** - Version manager (replaces pyenv, rbenv, nvm)
- **tea** - Ephemeral package runner (like npmx for everything)
- **chezmoi** - Dotfile manager for multi-device sync

### Development Tools

- **Python 3.12.9** - Via mise
- **Node.js 24.13.1** - Via mise
- **Ruby 3.3.7** - Via mise
- **Git** - Version control
- **GitHub CLI (gh)** - GitHub integration

### Shell Tools

- **fzf** - Fuzzy finder
- **ripgrep (rg)** - Fast grep replacement
- **fd** - Fast find replacement
- **bat** - Cat replacement with syntax highlighting
- **exa** - Modern ls replacement
- **zoxide** - Smart cd replacement
- **starship** - Cross-shell prompt

### Utilities

- **jq** - JSON processor
- **yq** - YAML processor
- **git-delta** - Git diff viewer

### Configuration Files Created

- `~/.tool-versions` - Global tool versions for mise
- `~/.mise.toml` - mise configuration
- `~/tea.yml` - tea dependencies
- `~/Brewfile` - Homebrew package list
- `~/.zshenv` - Shell environment setup

### Templates Created

- `~/.templates/.tool-versions` - Project tool versions template
- `~/.templates/.mise.toml` - mise config template
- `~/.templates/tea.yml` - tea config template
- `~/.templates/script.sh` - Shell script template
- `~/.templates/README.md` - Project README template

### Helper Scripts

- `~/.local/bin/check-legacy-tools` - Check migration status
- `~/.local/bin/new-project` - Create new project with templates

## Installation

### Quick Install

```bash
# Download and run
curl -fsSL https://raw.githubusercontent.com/yourusername/dotfiles/main/install.sh | bash

# Or clone and run
git clone https://github.com/yourusername/dotfiles.git
cd dotfiles
./install.sh
```

### Manual Install

```bash
# Make executable
chmod +x install.sh

# Run installation
./install.sh
```

## What Happens During Installation

1. **OS Check** - Verifies macOS
2. **Homebrew Install** - Installs Homebrew if missing
3. **System Packages** - Installs all packages via Homebrew
4. **mise Setup** - Configures mise and installs tool versions
5. **tea Setup** - Configures tea for ephemeral tools
6. **chezmoi Setup** - Initializes dotfile manager
7. **Brewfile Creation** - Creates package list for future sync
8. **Shell Config** - Sets up zsh configuration
9. **Templates** - Creates project templates
10. **Helper Scripts** - Creates utility scripts
11. **thegent Setup** - Installs thegent and dependencies
12. **Documentation** - Creates help files

## After Installation

### 1. Restart Terminal

Close and reopen your terminal to load new configurations.

### 2. Verify Installation

```bash
# Check tool versions
mise list

# Verify tools work
python --version  # Should show 3.12.9
node --version    # Should show 24.13.1
ruby --version    # Should show 3.3.7

# Check helper scripts
check-legacy-tools
new-project test-project
```

### 3. Use thegent

```bash
# Navigate to thegent directory
cd ~/temp-PRODVERCEL/485/kush/thegent

# thegent should be ready to use
# Run thegent commands as needed
```

## Multi-Device Setup

### Using chezmoi

```bash
# Initialize chezmoi with your git repo
chezmoi init https://github.com/yourusername/dotfiles.git

# Add files to track
chezmoi add ~/.zshrc
chezmoi add ~/.mise.toml
chezmoi add ~/.tool-versions

# On new machine
chezmoi init https://github.com/yourusername/dotfiles.git
chezmoi apply
```

### Using Homebrew Bundle

```bash
# On machine 1: Create Brewfile
brew bundle dump

# On machine 2: Install from Brewfile
brew bundle install
```

## Troubleshooting

### Installation Fails

1. **Check internet connection** - All tools download from internet
2. **Check Homebrew** - Ensure Homebrew is working: `brew doctor`
3. **Check permissions** - May need sudo for some operations
4. **Check disk space** - Ensure enough free space

### Tools Not Found After Install

1. **Restart terminal** - New PATH may not be loaded
2. **Source shell config**: `source ~/.zshenv`
3. **Check PATH**: `echo $PATH | tr ':' '\n'`
4. **Verify installation**: `which mise`, `which python`

### thegent Not Working

1. **Check thegent directory exists**: `ls ~/temp-PRODVERCEL/485/kush/thegent`
2. **Check dependencies**: `cd ~/temp-PRODVERCEL/485/kush/thegent && npm list`
3. **Run make install**: `cd ~/temp-PRODVERCEL/485/kush/thegent && make install`
4. **Check shell symlinks**: `ls -la ~/.zsh_*`

## Customization

### Add More Packages

Edit `~/Brewfile` and run:

```bash
brew bundle install
```

### Change Tool Versions

Edit `~/.tool-versions`:

```
python 3.13.0
node 22.0.0
```

Then run:

```bash
mise install
```

### Add More Templates

Add files to `~/.templates/` directory.

## Uninstallation

To remove everything:

```bash
# Remove Homebrew packages
brew bundle cleanup --force

# Remove mise tools
rm -rf ~/.local/share/mise

# Remove configs (be careful!)
rm ~/.tool-versions ~/.mise.toml ~/tea.yml ~/Brewfile

# Remove templates
rm -rf ~/.templates

# Remove helper scripts
rm ~/.local/bin/check-legacy-tools ~/.local/bin/new-project
```

## Support

- See `INSTALL_COMPLETE.md` for post-installation guide
- See `SYSTEM_WIDE_ALTERNATIVES.md` for tool alternatives
- See `LEGACY_TOOLS_MIGRATION.md` for migration details

## Next Steps

1. ✅ Run `install.sh`
2. ✅ Restart terminal
3. ✅ Verify installation
4. ✅ Start using thegent!
