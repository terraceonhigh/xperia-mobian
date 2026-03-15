# Rootfs Modifications from Stock Mobian SM6350 (Golden State)

All changes made to the Mobian weekly rootfs on the microSD card.
This documents the known-good state where the lock screen displays.

## Services Added
| Service | Purpose | File |
|---------|---------|------|
| `bind-shell.service` | Bind shell on port 4444 for remote access | `/etc/systemd/system/bind-shell.service` |

## Services Masked
| Service | Reason |
|---------|--------|
| `droid-juicer.service` | Hangs trying to read firmware from UFS (not working) |
| `systemd-firstboot.service` | Not needed |

## Files Modified
| File | Change |
|------|--------|
| `/usr/sbin/mobile-usb-gadget` | Changed ECM to RNDIS (Linux hosts support RNDIS) |
| `/etc/greetd/config.toml` | Auto-login as mobian (not used — phrog.conf override active) |

## Files Added
| File | Purpose |
|------|---------|
| `/usr/local/bin/bind-shell.sh` | Python bind shell script (used by bind-shell.service) |
| `/usr/lib/modules/6.12-sm6350/kernel/drivers/input/touchscreen/s6sy761.ko` | Cross-compiled Samsung S6SY761 touch driver (present but not auto-loaded) |
| `/etc/sudoers.d/mobian-nopasswd` | `mobian ALL=(ALL) NOPASSWD: ALL` |

## Packages Installed
| Package | Version | Purpose |
|---------|---------|---------|
| `openssh-server` | 1:10.2p1-5 | SSH access on port 22 |

## Credentials
| Item | Value |
|------|-------|
| mobian password | `1234` |
| SSH key | Mac pubkey in `/home/mobian/.ssh/authorized_keys` |

## What Is NOT Modified (critical for display)
- `/usr/libexec/phrog-greetd-session` — stock, no WLR env vars
- `/etc/greetd/phrog.toml` — stock, runs phrog-greetd-session as _greetd
- `/usr/lib/systemd/system/greetd.service.d/phrog.conf` — stock override
- `/usr/share/glib-2.0/schemas/` — no custom overrides, compiled clean
- `/etc/modules-load.d/` — only stock `modules.conf`
- `/lib/firmware/qcom/` — no a619_gmu.bin or a615_zap files
- MSM DRM module (`msm.ko`) — present but NOT loaded
