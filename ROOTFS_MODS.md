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

## Screen Blanking Fix (gsettings for _greetd)

The phosh greeter (running as `_greetd`) blanks the screen after a few seconds
of idle. With simpledrm, DPMS off is **irrecoverable** — the screen stays dark
until reboot. Fix: set gsettings for the `_greetd` user via their dbus session.

These settings are persisted in `/var/lib/greetd/.config/dconf/user` on the SD card.

**To apply (run after boot, via SSH):**
```bash
DBUS_ADDR=$(sudo grep -z DBUS_SESSION_BUS_ADDRESS \
  /proc/$(pgrep -u _greetd -f phoc | head -1)/environ 2>/dev/null \
  | tr '\0' '\n' | grep DBUS_SESSION | cut -d= -f2-)
sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.desktop.session idle-delay 0
sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.settings-daemon.plugins.power idle-dim false
sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type nothing
```

Once applied, settings persist across reboots (stored in _greetd's dconf database).
Power button still works to sleep/wake the screen.

**What does NOT work (tested and failed):**
- Pre-building dconf database offline and placing on SD card — causes bootloop
- Wrapper scripts around phrog-greetd-session — breaks greetd session tracking
- Setting `WLR_RENDERER_ALLOW_SOFTWARE=1` — breaks pixman renderer path
- gsettings for `mobian` user only — _greetd runs the greeter separately
- systemd services `Before=greetd.service` — break Plymouth→phosh display transition

## What Is NOT Modified (critical for display)
- `/usr/libexec/phrog-greetd-session` — stock, no WLR env vars
- `/etc/greetd/phrog.toml` — stock, runs phrog-greetd-session as _greetd
- `/usr/lib/systemd/system/greetd.service.d/phrog.conf` — stock override
- `/usr/share/glib-2.0/schemas/` — no custom overrides, compiled clean
- `/etc/modules-load.d/` — only stock `modules.conf`
- `/lib/firmware/qcom/` — no a619_gmu.bin or a615_zap files
- MSM DRM module (`msm.ko`) — present but NOT loaded
