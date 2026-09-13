# Hybrid Mac/Windows Environment Quick Start Guide

**Status:** Quick Reference | **Date:** 2026-02-16
**Related:** [Architecture](../architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md) | [Implementation Plan](../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md)

---

## Prerequisites

- Windows 11 PC (64GB RAM, 16GB VRAM, 8-core CPU, 5TB storage)
- Mac Laptop
- Both devices on same network (or VPN)
- Admin access on both devices

---

## Quick Setup (30 Minutes)

### Step 1: Install Syncthing (Both Devices)

**Windows:**

```powershell
# Download from https://syncthing.net/downloads/
# Install and launch
# Web UI: http://localhost:8384
```

**Mac:**

```bash
brew install syncthing
syncthing
# Web UI: http://localhost:8384
```

### Step 2: Install Tailscale (Both Devices)

**Windows:**

```powershell
# Download from https://tailscale.com/download/windows
# Install and sign in
```

**Mac:**

```bash
brew install tailscale
tailscale up
```

### Step 3: Install Parsec (Both Devices)

**Windows (Host):**

```powershell
# Download from https://parsec.app/downloads
# Install, enable hosting, set access code
```

**Mac (Client):**

```bash
# Download from https://parsec.app/downloads
# Install and connect using access code
```

### Step 4: Pair Devices

1. **Get Device IDs:**
   - Windows: Syncthing Web UI → Actions → Show ID
   - Mac: Syncthing Web UI → Actions → Show ID

2. **Add Devices:**
   - Windows: Add Remote Device → Paste Mac Device ID
   - Mac: Add Remote Device → Paste Windows Device ID

3. **Create Shared Folder:**
   - Windows: Add Folder → `D:\kush\`
   - Mac: Add Folder → `~/kush/`
   - Share folder between devices

4. **Test Sync:**
   - Create test file on Mac: `touch ~/kush/test.txt`
   - Verify it appears on Windows: `D:\kush\test.txt`

---

## Directory Structure

```
kush/
├── projects/              # All project code
│   ├── thegent/
│   └── [other-projects]/
├── configs/               # Cross-platform configs
│   ├── shell/
│   ├── vscode/
│   ├── cursor/
│   ├── nvim/
│   ├── git/
│   ├── docker/
│   ├── task/
│   ├── mac/               # Mac-specific
│   ├── windows/           # Windows-specific
│   └── wsl/              # WSL2-specific
├── bin/                  # Portable binaries
│   ├── mac/
│   └── windows/
├── scripts/              # Cross-platform scripts
└── .sync/                # Sync metadata (excluded)
```

---

## Common Commands

### Syncthing

```bash
# Check sync status
# Web UI: http://localhost:8384

# View sync logs
# Web UI → Activity → Logs
```

### Tailscale

```bash
# Check connection status
tailscale status

# Get device IP
tailscale ip

# Ping Windows PC from Mac
ping <windows-pc-tailscale-ip>
```

### Parsec

```bash
# Connect to Windows PC
# Launch Parsec → Enter access code

# Check connection quality
# Parsec → Settings → Connection
```

### SSH (Mac → Windows)

```bash
# First-time setup
ssh user@windows-pc-tailscale-ip

# Configure SSH config
cat >> ~/.ssh/config << EOF
Host windows-pc
    HostName <windows-pc-tailscale-ip>
    User <windows-username>
    IdentityFile ~/.ssh/id_rsa
EOF

# Connect
ssh windows-pc
```

---

## Sync Configuration

### `.stignore` File

Create `kush/.stignore`:

```
# Git
.git/
.gitignore

# Build artifacts
dist/
build/
target/
*.o
*.so
*.dylib
*.dll
*.exe

# Dependencies
node_modules/
.venv/
venv/
vendor/
__pycache__/

# OS-specific
.DS_Store
Thumbs.db
desktop.ini

# Cache
.cache/
.local/
*.log
*.tmp

# Sync metadata
.sync/
.stversions/
```

### Sync Settings

**Versioning:**

- Type: Simple File Versioning
- Keep Versions: 30 days

**Bandwidth:**

- Upload: 50 Mbps
- Download: 100 Mbps

**Schedule:**

- Full sync: Off-hours (2 AM - 6 AM)
- Incremental: Real-time

---

## Config Sync Setup

### Shell Configs

**Mac:**

```bash
# Backup existing
cp ~/.zshrc ~/.zshrc.backup

# Move to sync directory
mv ~/.zshrc ~/kush/configs/shell/.zshrc

# Create symlink
ln -s ~/kush/configs/shell/.zshrc ~/.zshrc
```

**Windows (WSL2):**

```bash
# Backup existing
cp ~/.bashrc ~/.bashrc.backup

# Move to sync directory
mv ~/.bashrc ~/kush/configs/shell/.bashrc

# Create symlink
ln -s ~/kush/configs/shell/.bashrc ~/.bashrc
```

### VS Code Configs

**Mac:**

```bash
# Backup existing
cp -r ~/Library/Application\ Support/Code/User ~/Library/Application\ Support/Code/User.backup

# Move to sync directory
mv ~/Library/Application\ Support/Code/User ~/kush/configs/vscode/

# Create symlink
ln -s ~/kush/configs/vscode ~/Library/Application\ Support/Code/User
```

**Windows:**

```powershell
# Backup existing
xcopy %APPDATA%\Code\User %APPDATA%\Code\User.backup /E /I

# Move to sync directory
move %APPDATA%\Code\User D:\kush\configs\vscode\

# Create junction
mklink /J %APPDATA%\Code\User D:\kush\configs\vscode
```

---

## Troubleshooting

### Sync Not Working

1. **Check Tailscale connectivity:**

   ```bash
   tailscale status
   ping <windows-pc-ip>
   ```

2. **Check Syncthing connection:**
   - Web UI → Devices → Check status
   - Should show "Connected"

3. **Check firewall:**
   - Windows: Allow Syncthing (22000/TCP, 22000/UDP)
   - Mac: Allow Syncthing in Firewall settings

4. **Check logs:**
   - Syncthing Web UI → Activity → Logs

### Parsec Lag

1. **Check network:**
   - Use wired connection (Windows PC)
   - 5 GHz WiFi (Mac)

2. **Optimize settings:**
   - Reduce resolution
   - Enable hardware encoding
   - Lower FPS target

3. **Check latency:**
   - Parsec → Settings → Connection → Latency

### Conflicts

1. **Check conflict files:**

   ```bash
   find ~/kush -name "*.sync-conflict-*"
   ```

2. **Resolve conflicts:**
   - Code files: Use Git merge
   - Config files: Manual review
   - Cache files: Delete and resync

3. **Prevent conflicts:**
   - Use Git for code files
   - Avoid simultaneous edits
   - Use versioning

---

## Performance Tips

### Sync Performance

1. **Exclude large files:**
   - Add to `.stignore`: `*.iso`, `*.dmg`, `*.zip` (>100MB)

2. **Use selective sync:**
   - Don't sync `node_modules/`, `.venv/`
   - Recreate per-platform

3. **Schedule full sync:**
   - Off-hours: 2 AM - 6 AM
   - Incremental: Real-time

### Parsec Performance

1. **Optimize network:**
   - Wired connection (Windows PC)
   - 5 GHz WiFi (Mac)
   - Close bandwidth-heavy apps

2. **Optimize settings:**
   - Resolution: 1920x1080 (or lower)
   - FPS: 60 (or 30 if laggy)
   - Hardware encoding: Enabled

3. **Reduce latency:**
   - Use Tailscale (mesh VPN)
   - Direct LAN when possible
   - Close unnecessary apps

---

## Backup Strategy

### Windows PC (Primary)

```powershell
# Daily backup script
# Backup D:\kush\ to E:\backup\kush-snapshots\

# Weekly full backup
# Backup to external HDD

# Versioning: 30 days retention
```

### Mac (Secondary)

```bash
# Time Machine: Local snapshots
# iCloud Drive: Critical configs (optional)
```

---

## Security Checklist

- [ ] Syncthing TLS encryption enabled
- [ ] Tailscale mesh VPN configured
- [ ] Parsec access code set
- [ ] SSH key-based auth configured
- [ ] Firewall rules configured
- [ ] Device certificates secured
- [ ] Backup encryption enabled (optional)

---

## Next Steps

1. **Complete Quick Setup** (30 min)
2. **Configure Sync** (1 hour)
3. **Migrate Projects** (2-3 hours)
4. **Set Up Remote Execution** (1 hour)
5. **Optimize Performance** (1 hour)

**Total Time:** ~6-7 hours for basic setup

---

## Resources

- **Syncthing Docs:** https://docs.syncthing.net/
- **Tailscale Docs:** https://tailscale.com/kb/
- **Parsec Docs:** https://support.parsec.app/
- **Architecture Document:** [HYBRID_MAC_WIN_DEV_ENVIRONMENT.md](../architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md)
- **Implementation Plan:** [HYBRID_ENV_IMPLEMENTATION_PLAN.md](../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md)

---

**Document Version:** 1.0
**Last Updated:** 2026-02-16
**Status:** Quick Reference

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
