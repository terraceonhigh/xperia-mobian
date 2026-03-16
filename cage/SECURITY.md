# Claude Code Cage — Security Design & Operations Manual

## Purpose

This document describes the security architecture used to allow Claude Code to
operate mostly unattended on Bazzite (192.168.1.91) while containing the blast
radius of a prompt injection or model compromise.

**Design goals:**
- Claude has everything it needs to build, inspect, and iterate on the pmOS port
- A compromised Claude cannot meaningfully exfiltrate data
- A compromised Claude cannot install persistent malicious code anywhere
- A compromised Claude cannot affect the host machine or other systems
- Hard-brick fastboot partitions are denied at the Mac level regardless

---

## Architecture

```
Mac (Claude Code + settings.local.json)
    │
    │  SSH with dedicated caged key (~/.ssh/claude_xperia_cage)
    │  IdentitiesOnly=yes — no fallback to other keys
    ▼
Bazzite sshd (192.168.1.91)
    │
    │  authorized_keys forced command — ALL connections via Claude's key
    │  are routed to entrypoint.sh regardless of what Claude requested.
    │  SSH options: restrict (no port-forwarding, no X11, no agent, no pty)
    ▼
cage/entrypoint.sh
    │
    │  Layer 1: Blocklist — deny dangerous substrings in any position
    │           (sudo, podman, ssh, curl, wget, base64, python3 -c, ...)
    │  Layer 2: Allowlist — only permitted first commands pass
    │           (pmbootstrap, git, cat, ls, grep, tail, sha512sum, ...)
    │  Audit:   every request logged to cage-audit.log (allow and deny)
    ▼
Rootless Podman Container (localhost/xperia-cage:latest)
    │
    │  --userns=keep-id          host UID mapped in, no real root
    │  --security-opt=no-new-privileges
    │  --cap-drop=ALL + --cap-add=SYS_PTRACE (proot needs ptrace)
    │  network: pasta (default rootless) — outbound internet OK,
    │           host LAN (192.168.1.x) NOT reachable from inside
    │
    │  Mounts:
    │    ~/Lab/xperia-pmos/pmaports/        → rw  (package files)
    │    ~/Lab/xperia-pmos/.pmbootstrap/    → rw  (build artifacts)
    │    ~/Lab/xperia-pmos/.venv/           → ro  (pmbootstrap runtime)
    │    ~/Lab/xperia-pmos/stock-partitions/ → ro (reference firmware)
    │    ~/.config/pmbootstrap_v3.cfg       → rw  (build config)
    │
    │  NOT mounted (inaccessible):
    │    ~/.ssh/          — private keys
    │    ~/Lab/xperiaGSI/ — stock firmware images
    │    All other host paths
    ▼
pmbootstrap → proot → Alpine chroot (build environment)
```

---

## What a Compromised Claude CAN Do

| Action | Impact |
|--------|--------|
| Corrupt APKBUILD / deviceinfo files | Visible in `git diff`; easy to detect and revert |
| Corrupt build artifacts in .pmbootstrap/ | Recoverable with `pmbootstrap zap` |
| Download malicious APK packages during build | Isolated inside Alpine chroot in .pmbootstrap/ |
| Exhaust disk space via builds | Worst case: `pmbootstrap zap` cleans it |
| Exfiltrate pmaports contents | All open-source; no secrets |

---

## What a Compromised Claude CANNOT Do

| Action | Prevented by |
|--------|-------------|
| Run arbitrary commands on Bazzite host | SSH forced command; all cmds hit entrypoint |
| Access ~/.ssh/, authorized_keys, private keys | Not mounted in container |
| Access ~/Lab/xperiaGSI/ or other projects | Not mounted in container |
| Install backdoor on Bazzite | Host filesystem not writable from container |
| Add cron jobs, systemd units | Blocked in blocklist + no host filesystem access |
| Lateral movement to other LAN hosts | host LAN not reachable from container network |
| Exfil via curl/wget/nc | Blocked in blocklist |
| Exfil via covert encoding (base64, xxd) | Blocked in blocklist |
| Use SSH/SCP/rsync to move data | Blocked in blocklist |
| Escalate privileges | --no-new-privileges + --cap-drop=ALL |
| Persist between container runs | --rm removes container on exit |
| Hard-brick the phone | Deny rules in Mac settings.local.json |

---

## Remaining Attack Surface

### 1. APK mirror trust
pmbootstrap downloads Alpine packages during builds. A compromised mirror
could inject a malicious package into the Alpine chroot inside .pmbootstrap/.
The chroot is isolated from the host, so damage is contained to the workdir.
Mitigation: pmbootstrap verifies package signatures; the Alpine signing key
is trusted at pmOS infrastructure level.

### 2. pmaports RW access
Claude can write to pmaports (it needs to, for package development). A
compromised Claude could introduce a backdoor into APKBUILD scripts that
would be built into the package. Mitigation: review `git diff` before
building any changed package; never flash without checking diffs.

### 3. Network from container
The container has outbound internet access (for APK downloads). A
compromised Claude could potentially exfiltrate pmaports contents or
build logs via DNS or HTTPS to an internet host. Mitigation: pmaports
is all open-source anyway. If you need stronger isolation, use
`--network=none` and pre-populate the APK cache with `pmbootstrap zap --no-cache`.

### 4. Container image rebuild
The Containerfile is in pmaports-adjacent storage. If Claude edits it,
the next `podman build` could produce a different image. Mitigation: only
the human should rebuild the container image (cage-setup.sh requires
manual invocation).

---

## Files

| File | Location | Purpose |
|------|----------|---------|
| `cage/Containerfile` | Mac + Bazzite | Container image definition |
| `cage/entrypoint.sh` | Bazzite `~/Lab/xperia-pmos/cage/` | SSH forced command validator |
| `cage/cage-setup.sh` | Mac + Bazzite | One-time setup script |
| `cage/SECURITY.md` | Mac (this file) | This document |
| `cage-audit.log` | Bazzite `~/Lab/xperia-pmos/` | Per-connection audit log |
| `~/.ssh/claude_xperia_cage` | Mac | Claude's private key (never leaves Mac) |
| `~/.ssh/claude_xperia_cage.pub` | Mac | Claude's public key |

---

## Monitoring

```bash
# On Bazzite: watch the audit log in real time
tail -f ~/Lab/xperia-pmos/cage-audit.log

# Review denied commands
grep DENY ~/Lab/xperia-pmos/cage-audit.log

# Check running cage containers
podman ps --filter name=cage
```

---

## Teardown (Nuke Checklist)

When done with the pmOS project, remove everything:

### On Bazzite (192.168.1.91)
```bash
# Remove container image
podman rmi localhost/xperia-cage:latest

# Remove cage files
rm -rf ~/Lab/xperia-pmos/cage/

# Remove audit log
rm ~/Lab/xperia-pmos/cage-audit.log

# Remove Claude's key from authorized_keys
# Edit ~/.ssh/authorized_keys and delete the claude-xperia-cage line

# Optionally: remove entire project
rm -rf ~/Lab/xperia-pmos/
```

### On Mac
```bash
# Remove Claude's SSH keys
rm ~/.ssh/claude_xperia_cage ~/.ssh/claude_xperia_cage.pub

# Remove cage source files
rm -rf /Users/terrace/Labs/Xperia/cage/

# Remove the Xperia project entirely
rm -rf /Users/terrace/Labs/Xperia/
```

### Claude Code settings
- Remove or reset `/Users/terrace/Labs/Xperia/.claude/settings.local.json`
- Remove project memory files from `~/.claude/projects/-Users-terrace-Labs-Xperia/memory/`

---

## Key Design Decisions

**Why not just restrict the existing SSH key?**
The personal key remains unrestricted for interactive use. Claude gets a
separate key so the human's workflow is never affected by cage restrictions.

**Why Podman over Docker?**
Bazzite/Fedora ships Podman natively; rootless mode requires no daemon and
no root. Docker would need additional setup and has a root-owned daemon.

**Why bash in the container instead of exec?**
Some Claude commands are shell pipelines (`grep ... | tail ...`). Wrapping
in `bash -c` handles all of these correctly. The entrypoint's validation
already checked the command before handing it to bash.

**Why not --network=none?**
pmbootstrap downloads Alpine APK packages during builds. Without network,
all packages would need to be pre-cached. This adds operational complexity.
The pasta/slirp4netns default already blocks LAN access; only internet
is reachable, which is an acceptable tradeoff.

**Why SYS_PTRACE capability?**
proot (used internally by pmbootstrap for Alpine chroot) requires ptrace.
In a rootless user namespace, SYS_PTRACE only grants ptrace permission
within the same user namespace — it does not confer host-level ptrace
privileges. The risk is minimal.
