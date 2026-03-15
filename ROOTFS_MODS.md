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
| `/etc/phosh/phoc.ini` | Phoc compositor config: `[output:Unknown-1]` scale=4 (simpledrm output) |

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

## Touchscreen (s6sy761) — WORKING (with DTB mod + post-boot enable)

**Touch works with display intact** using a two-part workaround:

1. **Modified DTB** (`boot-mobian-noavdd2.img`): Removed `avdd-supply` property
   from the touchscreen node AND removed the `touch-en-regulator` node entirely.
   This prevents the kernel regulator framework from claiming TLMM GPIO 10.

2. **Post-boot enable** (`enable-touch.sh`): After boot:
   - Set GPIO 10 high via chardev (powers touch IC AVDD rail)
   - `insmod s6sy761.ko` (initial probe often has I2C DMA errors)
   - Unbind driver from device (`echo 0-0048 > .../unbind`)
   - Reset touch IC: GPIO 21 low for 0.5s, high, then 2s settle
   - Rebind driver (`echo 0-0048 > .../bind`) — clean probe succeeds

**Why this works:** The stock DTB's `avdd-supply` pointed to a GPIO-controlled
fixed regulator (`touch_en_vreg`) on TLMM GPIO 10. When s6sy761 probed, the
regulator framework drove GPIO 10 high, which killed the bootloader-initialized
AMOLED panel (shared power rail). By removing the regulator from the DT and
toggling GPIO 10 directly, the same electrical result occurs but without the
regulator framework's interaction that caused the display to die.

The initial `insmod` probe often partially succeeds (module loads, event device
created) but subsequent I2C reads fail with DMA errors (-EIO). This is because
the touch IC needs a hardware reset (GPIO 21) after AVDD power-on to initialize
properly. The reliable sequence is: power on → insmod → unbind → reset → rebind.

**Hardware details:**
- Touch I2C: `988000.i2c` (bus 0, addr 0x48)
- Touch interrupt: TLMM GPIO 22
- Touch reset pinctrl: GPIO 21
- `vdd-supply`: PMIC LDO (1.8V) — kept in DT, handled by kernel
- Touch AVDD: TLMM GPIO 10 (high = enabled) — toggled manually from userspace
- DSI controller: `dsi@ae94000` — status "disabled" in DT (panel is bootloader-configured)
- 14-point multitouch, 1080x2520 (from IC firmware registers)

**DTB changes (from stock Mobian SM6350 DTB):**
- Removed `avdd-supply = <0x48>` from `touchscreen@48` node
- Removed entire `touch-en-regulator` node (was: regulator-fixed, GPIO 10)

**Boot image:** `boot-mobian-noavdd2.img` flashed to `boot_a`

**What does NOT work (tested and failed):**
- Loading s6sy761.ko with stock DTB — regulator toggle kills simpledrm display
- Removing only `avdd-supply` (keeping `touch-en-regulator` node) — regulator
  framework still claims GPIO 10, can't toggle from userspace
- MSM DRM as alternative display driver — DSI controller disabled in DT, panel
  driver (`samsung,sofef01-m-ams597ut04`) not in kernel, `sofef00` driver doesn't
  match this panel

## What Is NOT Modified (critical for display)
- `/usr/libexec/phrog-greetd-session` — stock, no WLR env vars
- `/etc/greetd/phrog.toml` — stock, runs phrog-greetd-session as _greetd
- `/usr/lib/systemd/system/greetd.service.d/phrog.conf` — stock override
- `/usr/share/glib-2.0/schemas/` — no custom overrides, compiled clean
- `/etc/modules-load.d/` — only stock `modules.conf`
- MSM DRM module (`msm.ko`) — present but NOT loaded

## Boot Images
| Image | DTB Change | Purpose |
|-------|------------|---------|
| `boot-mobian.img` | Stock (Golden) | Original Mobian weekly, no touch |
| `boot-mobian-noavdd2.img` | Removed `avdd-supply` + `touch-en-regulator` | Touch-safe: allows manual GPIO 10 + insmod |
