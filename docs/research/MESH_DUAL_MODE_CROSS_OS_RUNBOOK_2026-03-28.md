# Phenotype Mesh — Dual-Mode Cross-OS Runbook

**Date**: 2026-03-28
**Status**: Implementation Complete
**Author**: Research Agent

---

## 1. Architecture

### 1.1 Dual-Mode Design

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Phenotype Mesh (Dual-Mode)                        │
├──────────────────────────┬───────────────────────────────────────────┤
│                          │                                           │
│   PRIMARY (Free, 0-cost)│   FALLBACK (Self-hosted, unlimited)      │
│                          │                                           │
│   Tailscale              │   Headscale                               │
│   • 100 devices free     │   • Unlimited devices                     │
│   • Hosted control plane  │   • Self-hosted on OrbStack/VPS          │
│   • Zero config          │   • Full ACL + audit                      │
│   • macOS/Win/Linux/BSD  │   • OrbStack VM on macOS                 │
│                          │   • VPS for Linux/Windows                 │
│                          │                                           │
│   Auto-activates when    │   Auto-activates when:                   │
│   device count < 100     │   device count >= 100                    │
│                          │   OR user runs: mesh connect headscale   │
└──────────────────────────┴───────────────────────────────────────────┘
```

**Key insight**: Both modes can run simultaneously (dual-homed nodes). Switch is transparent.

### 1.2 Device Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Live Tailscale Network                           │
├──────────────┬──────────────┬──────────────────────────────────────┤
│ macOS Laptop │ Win11 Desktop│ Future: Containers/Runners           │
│ kooshas-laptop│ kooshas-desk │ (Headscale on OrbStack/VPS)        │
│ 100.112.14.98│ 100.96.135.160│                                    │
│ 🟢 online    │ 🔴 offline   │                                     │
└──────────────┴──────────────┴──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│               Headscale OrbStack VM (macOS hypervisor)              │
├─────────────────────────────────────────────────────────────────────┤
│ headscale VM (Ubuntu 24.04 arm64)                                   │
│ OrbStack IP: 192.168.139.156                                       │
│ Headscale API: http://192.168.139.156:8080                        │
│ Tailscale IPs: 100.64.0.x/10 (CGNAT range)                        │
│ Registered nodes: 0 (clean start)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 OrbStack Role (macOS only)

OrbStack replaces Docker Desktop with:

- **Lower overhead** than Docker Desktop (native hypervisor, ~0% CPU when idle vs 5-10% for Docker Desktop)
- **Linux VMs** (not just containers) — perfect for Headscale server
- **Docker + K8s** support if needed later
- **Fast boot** (seconds vs minutes for full VMs)
- **ARM64 native** on M-series Macs (like this MacBook)

Cost: Free (OrbStack) vs $0-$10/mo (VPS for Headscale)

---

## 2. Cross-OS Setup

### 2.1 macOS (Primary Host) ✅ Already Done

```bash
# Install everything via Homebrew
brew install --cask orbstack tailscale
brew install headscale-cli sops age

# Or use our setup script
mesh setup all

# Connect to mesh
mesh connect auto   # Auto-selects best mode

# Verify
mesh status
mesh doctor
```

### 2.2 Windows 11 (WSL Extension)

```powershell
# Option A: winget (easiest)
winget install --id Tailscale.Tailscale --accept-package-agreements --accept-source-agreements

# Option B: scoop
scoop bucket add extras
scoop install tailscale

# Option C: manual
# Download from https://tailscale.com/download/windows

# After install, open Tailscale and login
# Your device will appear in: mesh status

# For WSL2 integration (seamless with Windows host):
# WSL2 shares Windows network stack — Tailscale runs on Windows host
# No extra setup needed in WSL
```

**WSL-specific secrets sync**:

```bash
# In WSL, access secrets via the Windows-mounted filesystem
export SOPS_AGE_KEY_FILE=/mnt/c/Users/kooshapari/.config/age/phenotype.key
export PHENOTYPE_SOPS_SECRETS=/mnt/c/Users/kooshapari/.local/state/phenotype/secrets/secrets.env.age

# Or mount the encrypted secrets into WSL
# Add to /etc/wsl.conf on Windows side:
# [automount]
# options = "metadata,umask=22,fmask=11"
```

**Headscale on Windows** (future, when N > 100):

```powershell
# Download Headscale CLI
# https://github.com/juanfont/headscale/releases
# Or use our mesh script which auto-detects and configures
```

### 2.3 Linux (Headscale CLI + Tailscale)

```bash
# Ubuntu/Debian
curl -fsSL https://tailscale.com/install.sh | sh

# Or Headscale directly (for self-hosted)
# Download from https://github.com/juanfont/headscale/releases
wget https://github.com/juanfont/headscale/releases/download/v0.28.0/headscale_0.28.0_linux_amd64.tar.gz
tar -xzf headscale_0.28.0_linux_amd64.tar.gz
sudo mv headscale /usr/local/bin/
headscale version

# Connect to Tailscale
tailscale up --accept-routes

# Or connect to Headscale (our self-hosted mesh)
headscale nodes register --user <user> --key <pre-auth-key>
```

### 2.4 Linux (Headscale Server on VPS)

For when you want a persistent Headscale server accessible from anywhere:

```bash
# On a VPS (Hetzner, DigitalOcean, etc.) — $5-10/mo
curl -fsSL https://tailscale.com/install.sh | sh
# OR
wget https://github.com/juanfont/headscale/releases/download/v0.28.0/headscale_0.28.0_linux_amd64.tar.gz
tar -xzf headscale_0.28.0_linux_amd64.tar.gz
sudo mv headscale /usr/local/bin/

# Configure
sudo mkdir -p /var/lib/headscale /etc/headscale
sudo ./headscale configtest  # Verify config

# systemd service (see Headscale docs)
sudo systemctl enable --now headscale

# Register your nodes
# Get pre-auth key: mesh node add
# On each node:
#   macOS: headscale nodes register --key <key>
#   Win:   Use Headscale CLI
#   Linux: headscale nodes register --user phenotype --key <key>
```

---

## 3. Dual-Mode Auto-Switch

### 3.1 How It Works

```
mesh connect auto
  │
  ├── ts_node_count < 100?
  │     ├── YES → Connect Tailscale (primary)
  │     └── NO  → Warn + Connect Headscale (fallback)
  │
  └── "both" mode available for dual-homed nodes
```

### 3.2 Switching Modes

```bash
# Automatic (recommended)
mesh connect auto

# Force Tailscale only
mesh connect tailscale

# Force Headscale only
mesh connect headscale

# Both simultaneously (dual-homed)
mesh connect both

# Disconnect
mesh disconnect
```

### 3.3 Scale Triggers

| Device Count      | Mode                  | Action                            |
| ----------------- | --------------------- | --------------------------------- |
| 1-99              | Tailscale             | Free, hosted, zero config         |
| 100               | Tailscale → Headscale | `mesh connect auto` auto-switches |
| 101+              | Headscale             | Self-hosted, unlimited            |
| Future containers | Headscale             | Vault agent sidecar               |

---

## 4. Adding New Nodes

### 4.1 Get a Pre-Auth Key

```bash
# On macOS (Headscale server via OrbStack)
mesh node add phenotype 24h
# Output: hskey-auth-XXXXXXXXXXXXXXXXXXXXXX

# Or directly
headscale -c ~/.config/phenotype/mesh/headscale.yaml \
  preauthkeys create --user 1 --expiration 24h
```

### 4.2 Register Each OS

**macOS (to Headscale)**:

```bash
export HEADSCALE_URL="http://192.168.139.156:8080"
tailscale up \
  --login-server "$HEADSCALE_URL" \
  --authkey "hskey-auth-XXXXXXXXXXXXXXXXXXXXXX" \
  --hostname kooshas-laptop-headscale
```

**Windows (to Headscale)**:

```powershell
# Install Tailscale, then:
tailscale up --login-server http://192.168.139.156:8080 --authkey hskey-auth-XXXXXXXXXXXXXXXXXXXXXX --hostname kooshas-desktop-headscale
```

**Linux (to Headscale)**:

```bash
headscale nodes register \
  --user phenotype \
  --key hskey-auth-XXXXXXXXXXXXXXXXXXXXXX \
  --name linux-server
```

**WSL2 (via Windows host)**:
WSL2 automatically inherits Windows Tailscale. No extra registration needed.

---

## 5. Secrets Sync Across OSes

### 5.1 Age Key Distribution

The age private key stays on macOS (primary). Other machines need the **public key** to encrypt secrets they share, or the **private key** to decrypt.

**Option A: Private key on all machines (simple)**:

```bash
# Copy private key via mesh SSH
mesh ssh kooshas-laptop
# On macOS:
scp ~/.config/age/phenotype.key kooshas-desktop:~/.config/age/
```

**Option B: Private key on primary, others decrypt via mesh**:

```bash
# On secondary machines, use sops via mesh access
# The encrypted file can be accessed via:
# 1. Tailscale SSH: mesh ssh kooshas-laptop
# 2. scp via Tailscale IP: scp 100.112.14.98:~/.local/state/phenotype/secrets/secrets.env.age .
# 3. Headscale API (when connected to Headscale)
```

### 5.2 Multi-Recipient SOPS (Recommended)

Update `~/.sops.yaml` to include all device public keys:

```yaml
creation_rules:
  - path_regex: secrets/.*
    age:
      - age1e7enhngqnwd9syl2spwrsf5v56m7cjlzxw9dr5mk44dchfyl4ycqxvx83z # macOS
      - age1xxxx... # Windows desktop (after first run, add their pub key)
      - age1yyyy... # Linux VPS
    unencrypted_suffix: .example

  - path_regex: \.env$
    age:
      - age1e7enhngqnwd9syl2spwrsf5v56m7cjlzxw9dr5mk44dchfyl4ycqxvx83z
```

```bash
# On each device, generate key and share public key
age-keygen -o ~/.config/age/device.key
age-keygen -y ~/.config/age/device.key  # Print public key

# On macOS, update .sops.yaml with new public key
# Re-encrypt secrets: sops --encrypt secrets.env > secrets.env.age
# All devices can now decrypt
```

### 5.3 Secrets Per-OS Workflow

**macOS (primary, decrypts)**:

```bash
source ~/.zshrc.local
mclaude  # _load_secrets runs automatically
```

**Windows (via WSL or PowerShell)**:

```bash
# WSL
export SOPS_AGE_KEY_FILE=~/.config/age/phenotype.key
sops -d --input-type dotenv ~/.local/state/phenotype/secrets/secrets.env.age
```

**Linux VPS**:

```bash
export SOPS_AGE_KEY_FILE=~/.config/age/phenotype.key
source <(sops -d --input-type dotenv ~/.local/state/phenotype/secrets/secrets.env.age)
```

---

## 6. OrbStack vs Docker Desktop

| Feature      | OrbStack          | Docker Desktop                       |
| ------------ | ----------------- | ------------------------------------ |
| Overhead     | ~0% idle          | 5-10% idle                           |
| Linux VMs    | ✅ Native         | ❌ Containers only                   |
| Kubernetes   | ✅ Built-in       | ✅                                   |
| Performance  | Native hypervisor | Embedded VM                          |
| Cost         | Free              | $0/mo (personal) / $21/mo (business) |
| M-series Mac | ✅ Native ARM64   | Rosetta translation                  |
| GUI          | ✅                | ❌                                   |

**OrbStack for Headscale**: OrbStack's Linux VM is ideal for Headscale because:

1. It's a full Linux system (not a container)
2. WireGuard/Tailscale runs natively
3. Low overhead (~0% when idle)
4. Instant boot
5. Built into macOS hypervisor layer

---

## 7. Troubleshooting

### 7.1 Tailscale Issues

```bash
# Check status
mesh ts

# Restart on macOS
pkill -x Tailscale; open -a Tailscale

# Restart on Linux
sudo systemctl restart tailscaled

# Force re-auth
tailscale up --force-reauth
```

### 7.2 Headscale Issues

```bash
# Check VM status
mesh hs
orbctl list

# Check Headscale logs
orb bash -c 'tail -50 /home/kooshapari/headscale/headscale.log'

# Verify API
curl http://192.168.139.156:8080/health

# Restart Headscale in VM
orb bash -c 'pkill headscale; sleep 1; nohup headscale -c /tmp/headscale_full.yaml serve &'

# Full VM restart
orbctl restart headscale
```

### 7.3 Connectivity Issues

```bash
# Run diagnostics
mesh doctor

# Test mesh connectivity
tailscale ping 100.96.135.160    # Ping desktop
ping -c 2 192.168.139.156         # Ping Headscale VM

# Test secrets decryption
SOPS_AGE_KEY_FILE=~/.config/age/phenotype.key \
  sops -d --input-type dotenv \
  ~/.local/state/phenotype/secrets/secrets.env.age
```

---

## 8. Commands Reference

```bash
# ── Mesh Management ───────────────────────────────────────────────────────
mesh status              # Show full status (Tailscale + Headscale)
mesh connect [mode]      # Connect (auto/tailscale/headscale/both)
mesh disconnect          # Disconnect mesh
mesh doctor              # Diagnose issues

# ── Node Management ──────────────────────────────────────────────────────
mesh node list           # List all registered nodes
mesh node add [user] [exp]  # Generate pre-auth key for new node
mesh ssh <hostname>      # SSH via mesh (Tailscale SSH)
mesh secrets             # Show secrets access info

# ── Individual Status ────────────────────────────────────────────────────
mesh ts                  # Tailscale-only status
mesh hs                  # Headscale-only status

# ── Setup ─────────────────────────────────────────────────────────────────
mesh setup tailscale      # Install Tailscale on current OS
mesh setup headscale     # Create Headscale VM (macOS OrbStack)
mesh setup all           # Install both

# ── Secrets ───────────────────────────────────────────────────────────────
SOPS_AGE_KEY_FILE=~/.config/age/phenotype.key \
  sops -d --input-type dotenv --output-type dotenv \
  ~/.local/state/phenotype/secrets/secrets.env.age

# ── OrbStack (macOS only) ─────────────────────────────────────────────────
orbctl list              # List VMs
orbctl start headscale   # Start Headscale VM
orbctl stop headscale    # Stop Headscale VM
orb ssh headscale        # SSH into Headscale VM
orb bash -c 'cmd'        # Run command in VM
```

---

## 9. File Reference

| File                                                 | Purpose                        |
| ---------------------------------------------------- | ------------------------------ |
| `thegent/scripts/shell/phenotype-mesh.sh`            | Dual-mode mesh manager         |
| `thegent/scripts/shell/phenotype_minimax_harness.sh` | MiniMax/CLIProxy harness       |
| `~/.config/phenotype/mesh/`                          | Mesh config directory          |
| `~/.config/age/phenotype.key`                        | Age private key (keep secret!) |
| `~/.local/state/phenotype/secrets/secrets.env.age`   | Encrypted secrets              |
| `~/.sops.yaml`                                       | SOPS multi-recipient config    |
| `~/.zshrc.local:94-101`                              | Mesh alias                     |

---

## 10. Next Steps

### Today

- [ ] Verify `mesh status` shows both Tailscale and Headscale VMs
- [ ] Test `mesh connect auto`
- [ ] Fix Windows desktop key expiry (Tailscale admin console → generate new key)
- [ ] Copy age public key to Windows side

### This Week

- [ ] Register Windows desktop on Headscale mesh (for self-hosted fallback)
- [ ] Add Windows machine public key to `~/.sops.yaml` for multi-recipient encryption
- [ ] Test secrets decryption on Windows/WSL
- [ ] Register Linux VPS (if deploying Headscale on VPS)

### This Month

- [ ] Deploy Headscale on VPS for persistent mesh (optional)
- [ ] Test Vault dev mode for dynamic credentials
- [ ] Set up GH Actions with Vault JWT auth
- [ ] Add container secrets via Vault Agent sidecar
