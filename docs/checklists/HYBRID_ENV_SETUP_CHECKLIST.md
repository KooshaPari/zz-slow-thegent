# Hybrid Mac/Windows Environment Setup Checklist

**Status:** Checklist | **Date:** 2026-02-16
**Use this checklist to track setup progress**

---

## Phase 1: Foundation Setup

### Windows PC Setup

- [ ] Install Syncthing
  - [ ] Download from https://syncthing.net/
  - [ ] Install and launch
  - [ ] Web UI accessible at http://localhost:8384
  - [ ] Get device ID

- [ ] Create directory structure
  - [ ] Create `D:\kush\` directory
  - [ ] Create subdirectories: `projects/`, `configs/`, `bin/`, `scripts/`

- [ ] Install Tailscale
  - [ ] Download from https://tailscale.com/
  - [ ] Install and sign in
  - [ ] Get device IP
  - [ ] Verify connection

- [ ] Install Parsec Host
  - [ ] Download from https://parsec.app/
  - [ ] Install and enable hosting
  - [ ] Set access code
  - [ ] Configure GPU acceleration

- [ ] Install WSL2
  - [ ] Install Ubuntu/Debian
  - [ ] Configure basic tools
  - [ ] Test terminal access

- [ ] Configure Firewall
  - [ ] Allow Syncthing (22000/TCP, 22000/UDP)
  - [ ] Allow Parsec (UDP 8000-8010)
  - [ ] Allow SSH (22/TCP)

### Mac Setup

- [ ] Install Syncthing
  - [ ] `brew install syncthing`
  - [ ] Launch Syncthing
  - [ ] Web UI accessible at http://localhost:8384
  - [ ] Get device ID

- [ ] Create directory structure
  - [ ] Create `~/kush/` directory
  - [ ] Create subdirectories: `projects/`, `configs/`, `bin/`, `scripts/`

- [ ] Install Tailscale
  - [ ] `brew install tailscale`
  - [ ] `tailscale up`
  - [ ] Connect to Tailscale network
  - [ ] Verify connection to Windows PC

- [ ] Install Parsec Client
  - [ ] Download from https://parsec.app/
  - [ ] Install client
  - [ ] Connect to Windows PC using access code
  - [ ] Test connection (<20ms latency)

### Device Pairing

- [ ] Exchange Syncthing device IDs
  - [ ] Add Windows device on Mac
  - [ ] Add Mac device on Windows
  - [ ] Verify both show as "Connected"

- [ ] Create shared folder
  - [ ] Create `kush` folder on Windows (`D:\kush\`)
  - [ ] Create `kush` folder on Mac (`~/kush/`)
  - [ ] Share folder between devices
  - [ ] Test sync (create test file)

---

## Phase 2: Sync Configuration

### Ignore Patterns

- [ ] Create `.stignore` file
  - [ ] Add Git patterns (`.git/`, `.gitignore`)
  - [ ] Add build artifacts (`dist/`, `build/`, `target/`)
  - [ ] Add dependencies (`node_modules/`, `.venv/`, `vendor/`)
  - [ ] Add OS-specific (`.DS_Store`, `Thumbs.db`, `__pycache__/`)
  - [ ] Add cache patterns (`.cache/`, `.local/`)
  - [ ] Test ignore patterns

### Versioning & Conflicts

- [ ] Configure versioning
  - [ ] Enable simple file versioning
  - [ ] Set retention: 30 days
  - [ ] Test versioning

- [ ] Set up conflict resolution
  - [ ] Create conflict resolution script
  - [ ] Test conflict scenario
  - [ ] Verify versioning working

### Config Directory Structure

- [ ] Create `kush/configs/` structure
  - [ ] Create subdirectories: `shell/`, `vscode/`, `cursor/`, `nvim/`, `git/`, `docker/`, `task/`
  - [ ] Create platform-specific: `mac/`, `windows/`, `wsl/`
  - [ ] Initialize Git repo
  - [ ] Create `.gitignore`

### Shell Config Sync

- [ ] Backup existing configs
  - [ ] Backup `.zshrc` (Mac)
  - [ ] Backup `.bashrc` (WSL2)

- [ ] Move configs to sync directory
  - [ ] Move to `kush/configs/shell/`
  - [ ] Create platform-detection functions

- [ ] Create symlinks
  - [ ] Mac: `~/.zshrc` → `~/kush/configs/shell/.zshrc`
  - [ ] WSL2: `~/.bashrc` → `~/kush/configs/shell/.bashrc`

- [ ] Test shell configs
  - [ ] Test on Mac
  - [ ] Test on Windows (WSL2)
  - [ ] Verify sync

### Editor Config Sync

- [ ] VS Code configs
  - [ ] Backup existing settings
  - [ ] Move to `kush/configs/vscode/`
  - [ ] Create symlinks/junctions
  - [ ] Test on both platforms

- [ ] Cursor configs
  - [ ] Backup existing settings
  - [ ] Move to `kush/configs/cursor/`
  - [ ] Create symlinks
  - [ ] Test on both platforms

### Terminal Config Sync

- [ ] iTerm2 (Mac)
  - [ ] Backup settings
  - [ ] Export profiles to `kush/configs/iterm2/`
  - [ ] Create import script

- [ ] Windows Terminal
  - [ ] Backup settings
  - [ ] Export to `kush/configs/windows-terminal/`
  - [ ] Create import script

- [ ] WSL Terminal
  - [ ] Backup configs
  - [ ] Move to `kush/configs/wsl/`
  - [ ] Test on both platforms

---

## Phase 3: Project Migration

### Project Directory Setup

- [ ] Create `kush/projects/` directory
- [ ] Move `thegent/` project
  - [ ] Move to `D:\kush\projects\thegent\`
  - [ ] Update Git remote paths if needed
  - [ ] Verify Git working

- [ ] Move other projects
  - [ ] Move all projects to `kush/projects/`
  - [ ] Verify Git repos working
  - [ ] Test sync

### Dependency Management

- [ ] Document platform-specific dependencies
- [ ] Create setup scripts
  - [ ] Mac setup script
  - [ ] Windows setup script
  - [ ] WSL2 setup script

- [ ] Test dependency recreation
  - [ ] Python venv (Mac)
  - [ ] Python venv (Windows)
  - [ ] Node.js `node_modules`
  - [ ] Rust `target/`

- [ ] Create verification script
  - [ ] Check dependencies
  - [ ] Verify platform compatibility

### Build Verification

- [ ] Test builds on Windows
  - [ ] `thegent` build
  - [ ] Other projects

- [ ] Test builds on Mac
  - [ ] `thegent` build
  - [ ] Other projects

- [ ] Fix platform-specific issues
- [ ] Document build notes

---

## Phase 4: Compute Offloading

### SSH Setup

- [ ] Enable OpenSSH Server (Windows)
  - [ ] Install OpenSSH Server
  - [ ] Start service
  - [ ] Configure key-based auth

- [ ] Configure SSH keys
  - [ ] Generate key pair on Mac
  - [ ] Copy public key to Windows
  - [ ] Test SSH connection

- [ ] Configure SSH config
  - [ ] Create `~/.ssh/config` entry
  - [ ] Test remote command execution

### Remote Execution

- [ ] Research `thegent` remote execution
- [ ] Create remote execution wrapper
- [ ] Test `thegent run --remote windows-pc`
- [ ] Integrate with CLI
- [ ] Document usage

### Service Migration

- [ ] Install Docker Desktop (Windows)
- [ ] Install process-compose (Windows)
- [ ] Move dev services
  - [ ] Move `process-compose.yaml`
  - [ ] Test services running
  - [ ] Configure port forwarding

- [ ] Test remote service access
  - [ ] Access from Mac
  - [ ] Verify connectivity

### Heavy Compute Testing

- [ ] Test large builds on Windows
- [ ] Test parallel test execution
- [ ] Benchmark build times
- [ ] Document performance improvements

---

## Phase 5: Optimization & Polish

### Sync Performance

- [ ] Configure bandwidth limits
  - [ ] Upload: 50 Mbps
  - [ ] Download: 100 Mbps

- [ ] Set up sync schedule
  - [ ] Full sync: Off-hours
  - [ ] Incremental: Real-time

- [ ] Configure selective sync
- [ ] Test performance
- [ ] Document metrics

### Parsec Optimization

- [ ] Optimize settings
  - [ ] Resolution
  - [ ] FPS
  - [ ] Hardware encoding

- [ ] Test latency and FPS
- [ ] Fine-tune adaptive quality
- [ ] Document optimal settings

### Backup Automation

- [ ] Create backup script (Windows)
- [ ] Set up Task Scheduler
  - [ ] Daily backups
  - [ ] Weekly full backups

- [ ] Configure retention (30 days)
- [ ] Test backup restoration

### Documentation

- [ ] Create setup guide
- [ ] Create troubleshooting guide
- [ ] Document platform-specific notes
- [ ] Create runbooks
- [ ] Update architecture document

---

## Verification Checklist

### Functionality

- [ ] Bi-directional sync working
- [ ] Configs syncing correctly
- [ ] Parsec remote desktop <20ms latency
- [ ] Builds running on Windows PC
- [ ] Agent clients working on Mac
- [ ] Zero data loss
- [ ] <5 minute sync lag for active files

### Performance

- [ ] Sync bandwidth: >50 Mbps
- [ ] Parsec FPS: >60 FPS
- [ ] Parsec latency: <20ms
- [ ] Build time improvement: >2x faster on Windows

### Reliability

- [ ] Uptime: >99% sync availability
- [ ] Conflict rate: <1% of files
- [ ] Backup success rate: 100%
- [ ] Recovery time: <1 hour

---

## Notes

**Date Started:** **\*\***\_\_\_**\*\***

**Date Completed:** **\*\***\_\_\_**\*\***

**Issues Encountered:**

1.
2.
3.

**Lessons Learned:**

1.
2.
3.

---

**Checklist Version:** 1.0
**Last Updated:** 2026-02-16

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [HYBRID_ENV_IMPLEMENTATION_PLAN.md](../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md) — implementation plan
- [HYBRID_MAC_WIN_DEV_ENVIRONMENT.md](../architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md) — architecture
