# Claude Code Autonomous Startup Guide

How to get Claude Code running in caged autonomous mode for overnight Mobian development.

## Quick Start

```bash
# 1. Load SSH keys (passphrase required for id_ed25519)
ssh-add ~/.ssh/id_ed25519 ~/.ssh/claude_phone

# 2. Verify connectivity
ssh fedora echo ok
ssh phone-cage echo ok

# 3. Start Claude Code in autonomous mode
cd ~/Labs/Xperia
claude --dangerously-skip-permissions
```

## What the cage restricts

### On this Mac (enforced by hooks at `~/.claude/hooks/`)

**Bash commands — allowed:**
- SSH/SCP to `phone-cage`, `fedora`, `bazzite` only
- Read-only tools: `ls`, `cat`, `grep`, `find`, `diff`, etc.
- Build tools: `python3`, `dtc`, `make`, `podman`, `./build.sh`
- Git (push requires user approval prompt)
- `ssh-add`, `fastboot`
- File ops within project dir only

**Bash commands — blocked:**
- `sudo`, `brew install/uninstall`, `pip install`
- `rm -rf` outside project dir
- `mkfs`, `wipefs`, `diskutil erase`
- `curl|bash`, `osascript`, `launchctl`, `defaults write`
- SSH to unknown hosts

**File writes — restricted to:**
- `/Users/terrace/Labs/Xperia/` (project)
- `/Users/terrace/.claude/projects/-Users-terrace-Labs-Xperia/` (memory)
- `/Users/terrace/.claude/plans/` (plans)
- Blocks writes to `.ssh/`, `.env`, credentials, tokens

**Hook files location** (Claude cannot edit these):
- `~/.claude/hooks/validate-bash.sh`
- `~/.claude/hooks/validate-writes.sh`
- `~/.claude/settings.json` (registers the hooks)

### On the phone (enforced by OS — sudoers for `claude` user)

**Allowed sudo:**
- `journalctl`, `dmesg`, `lsmod` (diagnostics)
- `systemctl status/start/stop/restart` (service management)
- `nmcli`, `ip` (networking)
- `insmod`, `modprobe` (kernel modules)
- `cat`, `ls`, `find`, `grep` (reading system files)
- `reboot`

**Blocked sudo (password required = fails non-interactively):**
- `dd`, `mkfs`, `fdisk`, `parted` (partition ops)
- `rm`, `chmod`, `chown` (destructive file ops)
- `apt install/remove` (package changes)
- `tee`, `bash`, `sh` (arbitrary writes / escalation)

**To remove phone restrictions:** `ssh phone-usb 'echo mobian | sudo -S rm /etc/sudoers.d/claude-cage'`

## SSH hosts

| Alias | Target | User | Key | Notes |
|-------|--------|------|-----|-------|
| `fedora` | 192.168.1.122 | terrace | id_ed25519 | Fedora laptop, jump host |
| `phone-cage` | 10.66.0.1 via fedora | claude | claude_phone | Restricted phone user |
| `phone-usb` | 10.66.0.1 via fedora | mobian | id_ed25519 | Full phone access (your use) |
| `phone-wifi` | 192.168.1.83 | mobian | id_ed25519 | Direct WiFi (when available) |
| `bazzite` | 192.168.1.91 | terrace | id_ed25519 | Usually offline |

## Troubleshooting

**"Permission denied" on SSH**: Run `ssh-add ~/.ssh/id_ed25519` (needs passphrase)

**Phone unreachable at 10.66.0.1**: USB networking may be down. Check if phone is on. Try `ssh fedora 'ping -c 2 10.66.0.1'`. May need to reboot phone.

**Hook blocking a safe command**: Edit `~/.claude/hooks/validate-bash.sh` to add it to the allowlist.

**"Write blocked outside project directory"**: Edit `~/.claude/hooks/validate-writes.sh` to add the path to `ALLOWED_PREFIXES`.

**Phone bricked / won't boot**: See `DEVICE_STATUS.md` recovery procedure. TL;DR: flash `build/boot-mobian-rmtfs.img` to boot_a, NOT `images/boot-mobian-touch.img`.

## What Claude should work on

See the plan in the current session or start fresh. Safe autonomous tasks:
1. WiFi auto-reconnect config (`nmcli` — fully allowed)
2. System diagnostics and log analysis (read-only)
3. Bluetooth DTS research + patch preparation (local build)
4. Battery/USB ECM kernel config research (read-only)
5. Touch auto-load systemd service design (can't deploy without `mobian` user)
