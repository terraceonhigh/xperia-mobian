# Rootfs Modifications from Stock Mobian SM6350

All changes made to the Mobian weekly rootfs on the microSD card.

## Services Added
| Service | Purpose | File |
|---------|---------|------|
| `bind-shell.service` | Bind shell on port 4444 for remote access | `/etc/systemd/system/bind-shell.service` |
| `touchscreen.service` | insmod s6sy761.ko before greetd | `/etc/systemd/system/touchscreen.service` |

## Services Masked
| Service | Reason |
|---------|--------|
| `droid-juicer.service` | Hangs forever trying to read firmware from UFS (not working) |
| `systemd-firstboot.service` | Not needed |

## Files Modified
| File | Change |
|------|--------|
| `/usr/sbin/mobile-usb-gadget` | Changed ECM to RNDIS (macOS doesn't support RNDIS either, but Linux does) |
| `/etc/greetd/config.toml` | Auto-login as mobian to phosh-session (bypasses phrog greeter) |
| `/usr/libexec/phrog-greetd-session` | Added `export WLR_RENDERER_ALLOW_SOFTWARE=1` |

## Files Added
| File | Purpose |
|------|---------|
| `/usr/local/bin/bind-shell.sh` | Python bind shell script |
| `/usr/lib/modules/6.12-sm6350/kernel/drivers/input/touchscreen/s6sy761.ko` | Cross-compiled Samsung S6SY761 touch driver |
| `/etc/modules-load.d/touchscreen.conf` | Auto-load s6sy761 module |
| `/etc/sudoers.d/mobian-nopasswd` | `mobian ALL=(ALL) NOPASSWD: ALL` |

## Packages Installed
| Package | Version | Purpose |
|---------|---------|---------|
| `openssh-server` | 1:10.2p1-5 | SSH access |

## State
| Item | Value |
|------|-------|
| mobian password | `1234` |
| Mac SSH key | copied to `/home/mobian/.ssh/authorized_keys` |
| depmod | run for 6.12-sm6350 |

## Display Problem
The `WLR_RENDERER_ALLOW_SOFTWARE=1` env var was added to phrog-greetd-session
to allow phoc to start with llvmpipe software rendering (no GPU firmware).
However, this does NOT fix the display — the compositor's DRM modeset destroys
the bootloader-initialized simpledrm framebuffer, and the display goes permanently
black. The framebuffer (/dev/fb0) shows all zeros after phoc starts.

## What Was Working Before (and what changed)
In earlier boots, the user reported "Phosh is up" and could see the lock screen.
The display eventually stopped working. Possible causes:
1. The gschema override we added/removed may have corrupted the compiled schemas
2. The phrog.toml was modified and restored but may not be identical
3. depmod or module loading order may have changed boot timing
4. The display may have always been the Mobian splash lingering, not actual Phosh
