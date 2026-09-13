# Hybrid Mac/Windows Development Environment Architecture

**Status:** Architecture & Planning | **Date:** 2026-02-16
**Goal:** Cloud-based bi-directional sync of all work projects between Mac (access/client) and Windows 11 PC (compute/storage base)

---

## Executive Summary

This architecture enables seamless development across Mac and Windows 11 systems:

- **Mac**: Access client, agent chat clients (Cursor, Claude Code), light dev work, final installs
- **Windows 11 PC**: Compute base (64GB RAM, 16GB VRAM, 8-core CPU, 5TB storage), heavy compute, storage
- **Sync**: Bi-directional cloud sync of entire `kush/` directory including POSIX/OS-specific programs, configs, terminals, everything
- **Remote Access**: Parsec RDP for direct terminal access to Windows PC

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Mac Laptop                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Agent Clients (Cursor, Claude Code)                     │  │
│  │  - Chat interface                                         │  │
│  │  - Light editing                                          │  │
│  │  - Final installs/user-facing clients                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Sync Client (Syncthing / Resilio Sync)                  │  │
│  │  - Bi-directional sync                                   │  │
│  │  - Conflict resolution                                    │  │
│  │  - Selective sync                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Parsec Client                                            │  │
│  │  - Remote desktop to Windows PC                          │  │
│  │  - Low-latency terminal access                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ VPN / Direct LAN
                              │ (WireGuard / Tailscale)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Windows 11 PC                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Compute Base                                            │  │
│  │  - 64GB RAM                                               │  │
│  │  - 16GB VRAM                                              │  │
│  │  - 8-core CPU                                             │  │
│  │  - 5TB NVME/HDD                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Sync Server (Syncthing / Resilio Sync)                  │  │
│  │  - Master repository                                      │  │
│  │  - Conflict resolution                                    │  │
│  │  - Version history                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Development Environment                                  │  │
│  │  - WSL2 (Ubuntu/Debian)                                   │  │
│  │  - Native Windows tools                                   │  │
│  │  - Docker Desktop                                         │  │
│  │  - All project dependencies                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Parsec Host                                              │  │
│  │  - Remote desktop server                                  │  │
│  │  - Hardware acceleration                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Sync Architecture

### 2.1 Sync Technology Selection

**Primary Option: Syncthing**

- ✅ Open-source, self-hosted
- ✅ Bi-directional sync
- ✅ Conflict resolution (versioning)
- ✅ Selective sync
- ✅ Cross-platform (Mac, Windows, Linux)
- ✅ Encrypted (TLS)
- ✅ No cloud dependency
- ✅ File versioning and trash

**Alternative: Resilio Sync**

- ✅ Commercial (free tier available)
- ✅ Better performance for large files
- ✅ Selective sync
- ✅ Encrypted
- ❌ Requires license for advanced features

**Recommendation:** Start with **Syncthing** (OSS-first policy). Migrate to Resilio if performance issues arise.

### 2.2 Sync Scope

**Full Sync (`kush/` directory):**

```
kush/
├── thegent/              # Full project sync
├── [other-projects]/     # All projects
├── .config/              # Cross-platform configs
├── .local/               # Local data
├── .cache/               # Cache (selective sync)
└── .sync/                # Sync metadata (excluded)
```

**Selective Sync (Large/OS-Specific):**

- `node_modules/` - Sync on-demand or exclude
- `.venv/` - Exclude, recreate per-platform
- `dist/`, `build/` - Exclude, rebuild per-platform
- OS-specific binaries - Platform-specific folders

### 2.3 Conflict Resolution Strategy

**Three-Way Merge:**

1. **Automatic**: Syncthing versioning (keep both, rename)
2. **Manual**: Git merge for code files
3. **Last-Write-Wins**: For cache/temp files

**Conflict Detection:**

- `.sync/conflicts/` directory
- Git status checks before sync
- Pre-sync hooks to prevent conflicts

### 2.4 Sync Performance Optimization

**Bandwidth Management:**

- Rate limiting: 50 Mbps upload, 100 Mbps download
- Schedule: Full sync during off-hours
- Incremental: Real-time for active files

**File Filtering:**

- Ignore patterns: `.git/`, `__pycache__/`, `.DS_Store`, `Thumbs.db`
- Large file threshold: >100MB prompt before sync
- Smart sync: Only sync changed files

---

## 3. Network Architecture

### 3.1 Connectivity Options

**Option 1: Direct LAN (Preferred)**

- Same network: Mac ↔ Windows PC
- Low latency: <1ms
- High bandwidth: 1 Gbps+
- Setup: Static IPs or mDNS

**Option 2: VPN (Tailscale/WireGuard)**

- Cross-network: Mac ↔ Windows PC
- Encrypted tunnel
- Low latency: <10ms
- Setup: Tailscale mesh VPN (recommended)

**Option 3: Cloud Relay (Fallback)**

- Internet-based: Mac ↔ Windows PC
- Higher latency: 20-50ms
- Lower bandwidth: ISP-dependent
- Setup: Syncthing relay servers

**Recommendation:** Use **Tailscale** for VPN mesh. Falls back to direct LAN when on same network.

### 3.2 Network Security

**Encryption:**

- Syncthing: TLS 1.3 (device certificates)
- Tailscale: WireGuard protocol
- Parsec: AES-256 encryption

**Authentication:**

- Device certificates (Syncthing)
- Tailscale auth keys
- Parsec access code

**Firewall Rules:**

- Windows: Allow Syncthing (22000/TCP, 22000/UDP)
- Windows: Allow Parsec (UDP 8000-8010)
- Mac: Allow Syncthing (22000/TCP, 22000/UDP)

---

## 4. Storage Architecture

### 4.1 Windows PC Storage Layout

```
D:\kush\                    # Primary sync directory (NVME)
├── projects/               # All project code
│   ├── thegent/
│   ├── [project-2]/
│   └── [project-N]/
├── configs/                # Cross-platform configs
│   ├── .config/
│   ├── .local/
│   └── dotfiles/
├── cache/                  # Cache (excluded from sync)
│   ├── .cache/
│   └── node_modules/
└── archive/                # Long-term storage (HDD)

E:\backup\                  # Backup storage (HDD)
└── kush-snapshots/         # Time-machine style backups
```

### 4.2 Mac Storage Layout

```
~/kush/                     # Synced directory (local SSD)
├── projects/               # Synced projects
├── configs/                # Synced configs
└── .sync/                  # Sync metadata (local only)

~/.cache/kush/             # Local cache (not synced)
~/.local/kush/             # Local data (not synced)
```

### 4.3 Backup Strategy

**Windows PC (Primary):**

- Daily: Incremental backup to `E:\backup\kush-snapshots/`
- Weekly: Full backup to external HDD
- Versioning: 30 days retention

**Mac (Secondary):**

- Time Machine: Local snapshots
- Cloud: iCloud Drive for critical configs (optional)

**Disaster Recovery:**

- Git repositories: GitHub/GitLab (already in place)
- Configs: Encrypted backup to cloud storage
- Database dumps: Weekly exports to `E:\backup\`

---

## 5. Compute Offloading Architecture

### 5.1 Compute Tasks on Windows PC

**Heavy Compute:**

- Builds (Docker, native compiles)
- Test suites (parallel execution)
- ML model training/inference
- Video/image processing
- Large file operations

**Services:**

- Databases (PostgreSQL, Redis)
- Development servers (process-compose, Docker)
- CI/CD runners (GitHub Actions self-hosted)
- MCP servers (thegent serve)

### 5.2 Mac Client Tasks

**Light Compute:**

- Code editing
- Git operations (fetch, commit, push)
- Light linting/formatting
- Terminal sessions (SSH to Windows)

**Agent Clients:**

- Cursor IDE
- Claude Code
- Agent chat interfaces
- UI/UX work

### 5.3 Remote Execution

**SSH to Windows:**

```bash
# Mac → Windows SSH
ssh user@windows-pc-ip
cd /mnt/d/kush/thegent
task build
```

**Parsec RDP:**

- Full desktop access
- Low-latency terminal
- GPU acceleration
- Multi-monitor support

**thegent Remote Execution:**

```bash
# Mac: Run command on Windows
thegent run --remote windows-pc "Build project" gemini
```

---

## 6. Configuration Synchronization

### 6.1 Cross-Platform Configs

**Shell Configs:**

- `.zshrc`, `.bashrc` → `kush/configs/shell/`
- Platform-specific sections with `[[ "$OSTYPE" == "darwin*" ]]`

**Editor Configs:**

- VS Code: `kush/configs/vscode/`
- Cursor: `kush/configs/cursor/`
- Neovim: `kush/configs/nvim/`

**Terminal Configs:**

- iTerm2 (Mac): `kush/configs/iterm2/`
- Windows Terminal: `kush/configs/windows-terminal/`
- Alacritty: `kush/configs/alacritty/`

**Tool Configs:**

- Git: `kush/configs/git/.gitconfig`
- Docker: `kush/configs/docker/`
- Taskfile: `kush/configs/task/`

### 6.2 OS-Specific Configs

**Mac-Specific:**

- `~/Library/Application Support/` → Symlink to `kush/configs/mac/`
- Homebrew: `kush/configs/homebrew/Brewfile`

**Windows-Specific:**

- `%APPDATA%` → Junction to `D:\kush\configs\windows\`
- Chocolatey: `kush/configs/chocolatey/packages.config`
- WSL2: `kush/configs/wsl/`

### 6.3 Config Sync Strategy

**Symlinks/Junctions:**

- Mac: `ln -s ~/kush/configs/shell/.zshrc ~/.zshrc`
- Windows: `mklink /J %APPDATA%\Code D:\kush\configs\vscode`

**Version Control:**

- All configs in Git: `kush/configs/.git/`
- Platform detection in scripts
- Conditional loading

---

## 7. Program Synchronization

### 7.1 Cross-Platform Programs

**Python:**

- Virtual environments: `.venv/` excluded, recreate per-platform
- `requirements.txt`, `pyproject.toml` synced
- `uv`, `pip` configs synced

**Node.js:**

- `node_modules/` excluded
- `package.json`, `pnpm-lock.yaml` synced
- `.nvmrc` synced

**Rust:**

- `target/` excluded
- `Cargo.toml`, `Cargo.lock` synced

**Go:**

- `vendor/` excluded
- `go.mod`, `go.sum` synced

### 7.2 OS-Specific Programs

**Mac:**

- Homebrew binaries: `/opt/homebrew/bin/` (not synced)
- MacPorts: `/opt/local/bin/` (not synced)
- Symlinks to synced scripts: `~/kush/bin/`

**Windows:**

- Chocolatey binaries: `C:\ProgramData\chocolatey\bin\` (not synced)
- Portable apps: `D:\kush\bin\windows\` (synced)
- WSL2 binaries: `/usr/local/bin/` (WSL-specific)

### 7.3 Binary Compatibility

**Strategy:**

- Source code synced
- Binaries rebuilt per-platform
- Portable binaries in `kush/bin/` (Go, Rust static binaries)

**Scripts:**

- Shell scripts: Platform detection
- Python scripts: Cross-platform
- Batch/PowerShell: Windows-only

---

## 8. Terminal Setup Synchronization

### 8.1 Terminal Configs

**Mac (iTerm2):**

- Profiles: `kush/configs/iterm2/profiles/`
- Themes: `kush/configs/iterm2/themes/`
- Scripts: `kush/configs/iterm2/scripts/`

**Windows (Windows Terminal):**

- Settings: `kush/configs/windows-terminal/settings.json`
- Profiles: `kush/configs/windows-terminal/profiles/`
- Color schemes: `kush/configs/windows-terminal/colors/`

**WSL2 (Ubuntu):**

- `.bashrc`, `.zshrc`: `kush/configs/wsl/`
- `tmux.conf`: `kush/configs/wsl/tmux.conf`
- `nvim/`: `kush/configs/nvim/`

### 8.2 Terminal Tools

**Cross-Platform:**

- `tmux`, `screen`: Configs synced
- `zsh`, `bash`: Configs synced
- `starship` prompt: Config synced
- `fzf`, `ripgrep`: Configs synced

**Platform-Specific:**

- Mac: `iterm2-shell-integration`
- Windows: `clink`, `cmder`
- WSL2: Native Linux tools

---

## 9. Parsec Remote Desktop Setup

### 9.1 Parsec Configuration

**Windows PC (Host):**

- Install Parsec
- Enable hosting
- Set access code
- Configure GPU acceleration
- Multi-monitor setup

**Mac (Client):**

- Install Parsec client
- Connect to Windows PC
- Configure resolution/scaling
- Set up keyboard shortcuts

### 9.2 Parsec Optimization

**Network:**

- Use wired connection (Windows PC)
- 5 GHz WiFi (Mac)
- Port forwarding: UDP 8000-8010

**Performance:**

- Hardware encoding (NVENC)
- 60 FPS target
- Adaptive quality
- Low latency mode

**Security:**

- Access code required
- Two-factor auth (optional)
- VPN recommended for remote access

---

## 10. Implementation Phases

### Phase 1: Foundation (Week 1)

**Windows PC Setup:**

- [ ] Install Syncthing
- [ ] Configure `D:\kush\` directory
- [ ] Set up Tailscale VPN
- [ ] Install Parsec host
- [ ] Configure WSL2 (Ubuntu)

**Mac Setup:**

- [ ] Install Syncthing
- [ ] Configure `~/kush/` directory
- [ ] Install Tailscale client
- [ ] Install Parsec client
- [ ] Test connectivity

**Deliverable:** Basic sync and remote access working

---

### Phase 2: Sync Configuration (Week 2)

**Sync Setup:**

- [ ] Create Syncthing device pair (Mac ↔ Windows)
- [ ] Configure `kush/` folder sync
- [ ] Set up ignore patterns (`.git/`, `node_modules/`, etc.)
- [ ] Configure versioning (30 days)
- [ ] Test bi-directional sync

**Config Sync:**

- [ ] Create `kush/configs/` structure
- [ ] Set up symlinks/junctions
- [ ] Sync shell configs
- [ ] Sync editor configs
- [ ] Sync terminal configs

**Deliverable:** Full config sync working

---

### Phase 3: Project Migration (Week 3)

**Project Sync:**

- [ ] Move projects to `D:\kush\projects/`
- [ ] Sync `thegent/` project
- [ ] Sync other projects
- [ ] Test builds on both platforms
- [ ] Fix platform-specific issues

**Dependency Management:**

- [ ] Exclude `.venv/`, `node_modules/`
- [ ] Document platform-specific setup
- [ ] Create setup scripts per-platform

**Deliverable:** All projects syncing correctly

---

### Phase 4: Compute Offloading (Week 4)

**Remote Execution:**

- [ ] Set up SSH from Mac to Windows
- [ ] Configure `thegent` remote execution
- [ ] Test heavy builds on Windows
- [ ] Set up process-compose on Windows
- [ ] Configure Docker Desktop on Windows

**Service Migration:**

- [ ] Move databases to Windows
- [ ] Move dev servers to Windows
- [ ] Configure port forwarding
- [ ] Test remote service access

**Deliverable:** Compute offloading functional

---

### Phase 5: Optimization & Polish (Week 5)

**Performance:**

- [ ] Optimize sync bandwidth
- [ ] Tune Parsec settings
- [ ] Configure selective sync
- [ ] Set up backup automation

**Documentation:**

- [ ] Document setup process
- [ ] Create troubleshooting guide
- [ ] Document platform-specific notes
- [ ] Create runbooks

**Deliverable:** Production-ready setup

---

## 11. Technology Stack

### 11.1 Sync Layer

| Component               | Technology                 | Purpose                  |
| ----------------------- | -------------------------- | ------------------------ |
| **Sync Engine**         | Syncthing                  | Bi-directional file sync |
| **VPN**                 | Tailscale                  | Secure mesh VPN          |
| **Conflict Resolution** | Syncthing versioning + Git | File conflicts           |

### 11.2 Remote Access

| Component            | Technology        | Purpose           |
| -------------------- | ----------------- | ----------------- |
| **Remote Desktop**   | Parsec            | Low-latency RDP   |
| **SSH**              | OpenSSH (Windows) | Terminal access   |
| **Remote Execution** | thegent + SSH     | Command execution |

### 11.3 Storage

| Component           | Technology         | Purpose          |
| ------------------- | ------------------ | ---------------- |
| **Primary Storage** | NVME SSD (Windows) | Fast access      |
| **Backup Storage**  | HDD (Windows)      | Long-term backup |
| **Versioning**      | Syncthing + Git    | File history     |

### 11.4 Development

| Component              | Technology      | Purpose               |
| ---------------------- | --------------- | --------------------- |
| **WSL2**               | Ubuntu/Debian   | Linux environment     |
| **Docker**             | Docker Desktop  | Containerization      |
| **Process Management** | process-compose | Service orchestration |

---

## 12. Security Considerations

### 12.1 Data Encryption

**At Rest:**

- Windows: BitLocker encryption (optional)
- Mac: FileVault encryption (optional)
- Syncthing: TLS encryption (mandatory)

**In Transit:**

- Syncthing: TLS 1.3
- Tailscale: WireGuard encryption
- Parsec: AES-256 encryption
- SSH: AES-256-GCM

### 12.2 Access Control

**Device Authentication:**

- Syncthing: Device certificates
- Tailscale: Auth keys
- Parsec: Access code

**User Authentication:**

- Windows: Windows Hello / Password
- Mac: Touch ID / Password
- SSH: Key-based auth

### 12.3 Network Security

**Firewall:**

- Windows Firewall: Allow Syncthing, Parsec, SSH
- Mac Firewall: Allow Syncthing, Parsec
- Tailscale: Built-in firewall rules

**VPN:**

- Tailscale mesh VPN (recommended)
- WireGuard (alternative)
- Direct LAN (when on same network)

---

## 13. Monitoring & Maintenance

### 13.1 Sync Monitoring

**Syncthing:**

- Web UI: `http://localhost:8384`
- Sync status dashboard
- Conflict alerts
- Bandwidth usage

**Health Checks:**

- Daily sync status check
- Weekly conflict review
- Monthly backup verification

### 13.2 Performance Monitoring

**Metrics:**

- Sync latency
- Bandwidth usage
- Parsec FPS/latency
- Disk space usage

**Alerts:**

- Sync failures
- High conflict rate
- Low disk space
- Network connectivity issues

### 13.3 Maintenance Tasks

**Daily:**

- Check sync status
- Review conflicts

**Weekly:**

- Backup verification
- Clean up old versions
- Review sync logs

**Monthly:**

- Full backup
- Update software
- Review security settings

---

## 14. Troubleshooting Guide

### 14.1 Common Issues

**Sync Not Working:**

- Check Tailscale/VPN connectivity
- Verify Syncthing devices are connected
- Check firewall rules
- Review Syncthing logs

**Conflicts:**

- Review `.sync/conflicts/` directory
- Use Git merge for code files
- Manual resolution for configs

**Parsec Lag:**

- Check network latency
- Use wired connection
- Reduce resolution
- Enable hardware acceleration

**Build Failures:**

- Check platform-specific dependencies
- Recreate `.venv/` or `node_modules/`
- Verify PATH variables

---

## 15. Cost Analysis

### 15.1 Software Costs

| Software      | Cost                     | Notes                |
| ------------- | ------------------------ | -------------------- |
| **Syncthing** | Free (OSS)               | Self-hosted          |
| **Tailscale** | Free (up to 100 devices) | Mesh VPN             |
| **Parsec**    | Free (personal use)      | Remote desktop       |
| **Total**     | **$0/month**             | All free/open-source |

### 15.2 Hardware Costs

**Already Owned:**

- Windows 11 PC: ✅
- Mac Laptop: ✅
- 5TB Storage: ✅

**Optional:**

- External HDD for backup: ~$100
- Network switch (if needed): ~$50

---

## 16. Success Criteria

### 16.1 Functional Requirements

- [ ] Bi-directional sync working for all projects
- [ ] Configs syncing correctly
- [ ] Parsec remote desktop <20ms latency
- [ ] Builds running on Windows PC
- [ ] Agent clients working on Mac
- [ ] Zero data loss
- [ ] <5 minute sync lag for active files

### 16.2 Performance Requirements

- [ ] Sync bandwidth: >50 Mbps
- [ ] Parsec FPS: >60 FPS
- [ ] Parsec latency: <20ms
- [ ] Build time improvement: >2x faster on Windows

### 16.3 Reliability Requirements

- [ ] Uptime: >99% sync availability
- [ ] Conflict rate: <1% of files
- [ ] Backup success rate: 100%
- [ ] Recovery time: <1 hour

---

## 17. Next Steps

1. **Review & Approve Architecture** - User review of this document
2. **Phase 1 Implementation** - Set up foundation (Week 1)
3. **Phase 2 Implementation** - Configure sync (Week 2)
4. **Phase 3 Implementation** - Migrate projects (Week 3)
5. **Phase 4 Implementation** - Compute offloading (Week 4)
6. **Phase 5 Implementation** - Optimization (Week 5)

---

## Appendix A: Quick Reference

### Syncthing Setup

```bash
# Windows
# Download from https://syncthing.net/
# Install and configure folder: D:\kush\

# Mac
brew install syncthing
syncthing
# Configure folder: ~/kush/
```

### Tailscale Setup

```bash
# Windows
# Download from https://tailscale.com/
# Sign in and connect

# Mac
brew install tailscale
tailscale up
```

### Parsec Setup

```bash
# Windows (Host)
# Download from https://parsec.app/
# Enable hosting, set access code

# Mac (Client)
# Download from https://parsec.app/
# Connect using access code
```

### SSH Setup

```bash
# Windows (OpenSSH Server)
# Settings → Apps → Optional Features → OpenSSH Server
# Enable and start service

# Mac
ssh user@windows-pc-tailscale-ip
```

---

## Appendix B: File Structure

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
│   ├── windows/          # Windows-specific
│   └── wsl/               # WSL2-specific
├── bin/                   # Portable binaries
│   ├── mac/
│   └── windows/
├── scripts/               # Cross-platform scripts
└── .sync/                 # Sync metadata (excluded)
```

---

## 18. Configuration Examples

### 18.1 Syncthing Configuration (`~/.config/syncthing/config.xml`)

```xml
<configuration version="37">
    <gui enabled="true" tls="true">
        <address>0.0.0.0:8384</address>
        <user>admin</user>
        <password>$2$hash...</password>
    </gui>

    <options>
        <autoUpgradeIntervalH>12</autoUpgradeIntervalH>
        <globalEnabled>true</globalEnabled>
        <localEnabled>true</localEnabled>
        <reconnectionIntervalS>60</reconnectionIntervalS>
        <relayReconnectIntervalM>5</relayReconnectIntervalM>
        <maxPendingCsrfTokens>50</maxPendingCsrfTokens>
        <progressUpdateIntervalS>500</progressUpdateIntervalS>
        <symlinksEnabled>true</symlinksEnabled>
        <trafficClass>0</trafficClass>
        <readOnly>0</readOnly>
    </options>

    <devices>
        <device id="MAC-DEVICE-ID" name="MacBook Pro">
            <address>dynamic</address>
            <compress>always</compress>
            <customCertPath></customCertPath>
            <autoAcceptFolders>true</autoAcceptFolders>
            <introducer>false</introducer>
        </device>
        <device id="WINDOWS-DEVICE-ID" name="Windows PC">
            <address>tailscale-ip:22000</address>
            <compress>always</compress>
            <autoAcceptFolders>true</autoAcceptFolders>
            <introducer>false</introducer>
        </device>
    </devices>

    <folders>
        <folder id="kush-sync" label="kush" path="D:/kush/">
            <filesystemType>basic</filesystemType>
            <ignorePerms>false</ignorePerms>
            <ignoreDeletePatterns></ignoreDeletePatterns>
            <ignoreUpdatePatterns></ignoreUpdatePatterns>
            <ignoreMask></ignoreMask>
            <paused>false</paused>
            <autoNormalize>true</autoNormalize>

            <versioning>
                <type>simple</type>
                <param key="keep">30</param>
            </versioning>

            <ignore>
                <pattern>.stignore</pattern>
                <pattern>.stversions/**</pattern>
                <pattern>.stfolder/**</pattern>
            </ignore>
        </folder>
    </folders>
</configuration>
```

### 18.2 Syncthing `.stignore` Patterns

```stignore
# Version control
.git/
.gitignore
.gitattributes

# Build artifacts
dist/
build/
target/
*.egg-info/
__pycache__/
*.pyc
*.pyo
node_modules/
.venv/
venv/
.env/

# OS-specific
.DS_Store
Thumbs.db
*.swp
*.swo
~*

# IDE
.idea/
.vscode/
*.sublime-*
*.sublime-project

# Cache
.cache/
.temp/
.tmp/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Large files
*.zip
*.tar.gz
*.7z
*.mp4
*.mov
*.pdf

# Sync metadata
.stignore
.stversions/
.stfolder/
.sync/
```

### 18.3 SSH Configuration (`~/.ssh/config`)

```ssh-config
# Windows PC via Tailscale
Host windows-pc-tailscale
    HostName 100.x.x.x          # Tailscale IP
    User developer
    Port 22
    IdentityFile ~/.ssh/id_ed25519_windows
    AddKeysToAgent yes
    ForwardAgent no
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Windows PC via LAN (fallback)
Host windows-pc-lan
    HostName 192.168.1.x        # Local IP
    User developer
    Port 22
    IdentityFile ~/.ssh/id_ed25519_windows
    AddKeysToAgent yes
    ForwardAgent no

# Global settings
Host *
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    PasswordAuthentication no
    ChallengeResponseAuthentication no
```

### 18.4 Tailscale ACL Configuration

```json
{
  "groups": {
    "group:devops": ["user@email.com"]
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:devops"],
      "dst": ["*:*"]
    },
    {
      "action": "accept",
      "src": ["tag:build-server"],
      "dst": ["tag:storage:*"]
    }
  ],
  "tagOwners": {
    "tag:build-server": ["user@email.com"],
    "tag:storage": ["user@email.com"]
  },
  "ssh": [
    {
      "action": "accept",
      "src": ["group:devops"],
      "dst": ["tag:build-server"],
      "users": ["root", "developer"]
    }
  ]
}
```

### 18.5 process-compose Configuration (Windows)

```yaml
version: "3.8"

processes:
  syncthing:
    command: syncthing
    working_dir: D:/kush/.sync/
    environment:
      - HOME=D:/Users/developer
      - SYNCTHING_HOME=D:/Users/developer/.config/syncthing
    readiness_probe:
      type: tcp
      port: 8384
    restart_policy: always
    priority: 10

  tailscaled:
    command: tailscaled --state D:/kush/.tailscale/state.json --socket D:/kush/.tailscale/sock
    working_dir: D:/kush/.tailscale/
    environment:
      - TS_STATE_DIR=D:/kush/.tailscale/state.json
    readiness_probe:
      type: tcp
      port: 41641
    restart_policy: always
    priority: 5

  thegent:
    command: python -m thegent serve
    working_dir: D:/kush/thegent/
    depends_on:
      - syncthing
      - tailscaled
    environment:
      - THGENT_HOME=D:/kush/.thegent
      - THGENT_CONFIG=D:/kush/config/thegent.yaml
    ports:
      - "3847:3847"
    readiness_probe:
      type: http
      path: /health
      port: 3847
    restart_policy: always
    priority: 20

  docker:
    command: D:/Program Files/Docker/Docker/resources/dockerd
    working_dir: D:/Program Files/Docker/
    environment:
      - DOCKER_CERT_PATH=D:/Users/developer/.docker/certs
      - DOCKER_HOST=tcp://localhost:2375
    readiness_probe:
      type: tcp
      port: 2375
    restart_policy: always
    priority: 1
```

### 18.6 thegent Remote Configuration

```yaml
# ~/.config/thegent/remote_hosts.yaml
hosts:
  windows-pc:
    description: "Primary development PC (Windows)"
    transport: ssh
    ssh_host: windows-pc-tailscale
    ssh_user: developer
    remote_path: D:/kush
    local_path: ~/kush
    sync_before:
      - "uv sync"
    sync_after:
      - "git status"
    env:
      THGENT_REMOTE: "true"
      PYTHONPATH: "D:/kush/thegent"
    tags:
      - primary
      - compute-heavy
      - gpu-available

  mac-laptop:
    description: "Mac development client"
    transport: local
    remote_path: ~/kush
    local_path: ~/kush
    env:
      THGENT_REMOTE: "false"
    tags:
      - client
      - lightweight

profiles:
  default:
    host: windows-pc
    sync_strategy: incremental
    create_backups: true

  ci:
    host: windows-pc
    sync_strategy: full
    create_backups: false
    env:
      CI: "true"
```

### 18.7 WSL2 Configuration

```bash
# ~/.wslconfig (Windows)
[wsl2]
memory=32GB
processors=8
swap=16GB
kernelCommandLine = "init=/init root=..."

[network]
hostname=wsl-dev

[boot]
command="service docker start"

# /etc/wsl.conf (WSL2)
[automount]
enabled = true
root = /mnt/
options = "metadata,uid=1000,gid=1000,umask=022"

[network]
hostname = wsl-dev

[interop]
enabled = true
appendWindowsPath = true
```

### 18.8 Docker Desktop Configuration (Windows)

```json
{
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "20GB",
      "defaultKeepStoragePerImage": "5GB"
    }
  },
  "experimental": true,
  "features": {
    "buildkit": true,
    "containerd": true
  },
  "metrics": true,
  "network": {
    "bridge": "docker0",
    "dns": ["8.8.8.8", "8.8.4.4"]
  },
  "storage": {
    "driver": "overlay2",
    "location": "D:/Docker/wsl"
  }
}
```

### 18.9 Cross-Platform Shell Config

```bash
# ~/kush/configs/shell/.hybrid_env.zsh

# Detect platform
platform_detection() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)
            if [ -f /proc/version ] && grep -q Microsoft /proc/version; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

# Get remote path based on local path
remote_path() {
    local local_path="$1"
    case "$(platform_detection)" in
        wsl|macos)
            echo "$local_path" | sed 's|~/kush/|D:/kush/|'
            ;;
        *)
            echo "$local_path"
            ;;
    esac
}

# Sync current directory to remote
sync-to-remote() {
    local remote_dir=$(remote_path "$(pwd)")
    rsync -avz --delete \
        --exclude='.venv' \
        --exclude='node_modules' \
        --exclude='.cache' \
        --exclude='dist' \
        --exclude='build' \
        --exclude='__pycache__' \
        ./ "$remote_dir"
}

# Run command on remote
run-remote() {
    local cmd="$*"
    ssh windows-pc-tailscale "cd D:/kush && $cmd"
}

# Compute offload aliases
alias compute='run-remote'
alias sync-up='sync-to-remote'
alias sync-down='rsync -avz --delete windows-pc-tailscale:D:/kush/ ./'
```

### 18.10 Performance Monitoring Script

```bash
#!/bin/bash
# ~/kush/scripts/monitor-hybrid.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Hybrid Environment Status ==="
echo ""

# Check Syncthing
echo -n "Syncthing: "
if curl -s --max-time 2 http://localhost:8384/rest/noauth/health | grep -q "OK"; then
    echo -e "${GREEN}Running${NC}"
else
    echo -e "${RED}Stopped${NC}"
fi

# Check Tailscale
echo -n "Tailscale: "
if tailscale status --json 2>/dev/null | grep -q "Self"; then
    IP=$(tailscale ip -4)
    echo -e "${GREEN}Connected ($IP)${NC}"
else
    echo -e "${RED}Disconnected${NC}"
fi

# Check SSH
echo -n "SSH to Windows: "
if ssh -o BatchMode=yes -o ConnectTimeout=2 windows-pc-tailscale "echo 'OK'" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}Available${NC}"
else
    echo -e "${RED}Unavailable${NC}"
fi

# Check Disk Usage
echo ""
echo "=== Disk Usage ==="
echo "Local (Mac): $(df -h ~ | tail -1 | awk '{print $5}') used"
ssh windows-pc-tailscale "df -h D:/kush" 2>/dev/null | tail -1 | awk '{print "Remote (Windows): " $5 " used"}'

# Check Sync Status
echo ""
echo "=== Sync Status ==="
echo "Mac → Windows: $(cat ~/.local/state/syncthing/connections.json 2>/dev/null | grep -o '"total"[^,]*' | head -1)"
```

---

## 19. Cross-References

| Topic               | Reference                                            |
| ------------------- | ---------------------------------------------------- |
| Compute Offloading  | `docs/plans/REMOTE_COMPUTE_IMPLEMENTATION_DETAIL.md` |
| TUI/Queue Design    | `docs/research/USER_QUEUE_TUI_AND_AGENT_POLL.md`     |
| DevOps Tooling      | `docs/research/CI_CD_DEVX_TOOLING.md`                |
| CLI Patterns        | `docs/research/API_CLI_DEVOPS_TOOLING.md`            |
| Implementation Plan | `docs/plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md`       |

---

## 20. Extension Summary

### Added in This Extension

| Section                        | Description                                                                                                 |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **18. Configuration Examples** | Added Syncthing, SSH, Tailscale, process-compose, remote hosts, WSL2, Docker, shell, and monitoring configs |
| **19. Cross-References**       | Added links to related documentation                                                                        |

### Key Configuration Patterns

| Pattern         | File  | Purpose                   |
| --------------- | ----- | ------------------------- |
| Syncthing XML   | 18.1  | Master sync configuration |
| `.stignore`     | 18.2  | Sync exclusion patterns   |
| SSH Config      | 18.3  | Remote access setup       |
| Tailscale ACL   | 18.4  | Network security          |
| process-compose | 18.5  | Service orchestration     |
| Remote Hosts    | 18.6  | Compute offloading        |
| WSL2 Config     | 18.7  | Linux environment         |
| Docker Config   | 18.8  | Container platform        |
| Shell Scripts   | 18.9  | Platform abstraction      |
| Monitoring      | 18.10 | Health checks             |

### Related Documents

| Document                                       | Purpose              |
| ---------------------------------------------- | -------------------- |
| `docs/guides/HYBRID_ENV_QUICK_START.md`        | Quick setup guide    |
| `docs/reference/HYBRID_ENV_SUMMARY.md`         | Architecture summary |
| `docs/plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md` | Implementation tasks |

---

**Document Version:** 1.1
**Last Updated:** 2026-02-17
**Extension:** Configuration Examples, Cross-References, Extension Summary
