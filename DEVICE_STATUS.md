# Sony Xperia 10 III (pdx213) — Mobian Port Status

**Last verified**: 2026-03-16
**Status**: Boots to Phosh lock screen, WiFi + touch + modem working
**OS**: Mobian (Debian) with kernel 6.12.68 on SM6350 (Snapdragon 690 5G)

---

## Architecture

The phone boots from two components:

1. **Boot image** on internal `boot_a` partition — contains the kernel, initramfs, and device tree blob (DTB)
2. **Root filesystem** on a **microSD card** — standard Mobian Debian rootfs with firmware and customizations

The boot image's kernel cmdline tells the initramfs which rootfs to mount via `mobile.root=UUID=a1132a8f-...`.

## What Works

| Feature | Status | Notes |
|---------|--------|-------|
| Display | Working | simpledrm (bootloader framebuffer), scale=2 |
| Touch | Working | Samsung s6sy761, loads ~100s after boot via `enable-touch.sh` |
| WiFi | Working | WCN3990/ath10k_snoc, WPA2, must use `cloned-mac-address=permanent` |
| Modem (MPSS) | Running | Remoteproc stable, not tested for calls/data |
| UFS (internal storage) | Working | 79 partitions visible at /dev/sda |
| Power button | Working | Screen on/off |
| USB gadget | Working | RNDIS (Linux USB networking, not macOS compatible) |

## What Doesn't Work

| Feature | Status | Notes |
|---------|--------|-------|
| Battery charging | No driver | `CONFIG_CHARGER_QCOM_SMB2` needed. Phone only charges when off or in fastboot. |
| GPU acceleration | simpledrm only | msm DRM module must NOT be loaded (breaks framebuffer) |
| Bluetooth | Not configured | Firmware present in /lib/firmware/qca/, needs UART DTS node |
| Camera | Not tested | |
| Audio | Not tested | |
| Sensors | Not tested | |

## Critical Rules (Do Not Break Display)

The display uses `simpledrm` — a simple framebuffer initialized by the bootloader. It is fragile. **Do NOT**:

- Set `WLR_RENDERER_ALLOW_SOFTWARE=1` in any phrog/greetd config
- Load the `msm` DRM kernel module (`modprobe msm`)
- Install GPU firmware files (a619_gmu.bin, a615_zap) to the rootfs
- Add gschema overrides for idle/power settings
- Modify phrog.toml or phrog.conf
- Run `systemctl restart phosh` — **always do a full reboot instead**

Any of these will cause the compositor to attempt a modeset, destroying the bootloader framebuffer permanently until the next reboot.

---

## Recovery Procedure

### You need

- The phone
- A microSD card (32GB, contains the rootfs)
- A Linux machine with a USB port and SD card reader (we use a Fedora Atomic laptop at 192.168.1.122)
- This repository cloned to a Mac at `/Users/terrace/Labs/Xperia/`

### Step 0: Charge the phone

Plug in USB and wait 15+ minutes. The phone only charges in fastboot mode or when powered off — Linux has no charging driver.

### Step 1: Enter fastboot mode

Hold **Volume Up** while plugging in the USB cable. The phone auto-powers on and enters fastboot.

Verify: `sudo fastboot devices` should show `HQ616S35A9`.

### Step 2: Flash the boot image

The correct boot image is:

```
build/boot-mobian-rmtfs.img
```

**WARNING**: Do NOT use `images/boot-mobian-touch.img` — it is an older, incomplete image. We lost an entire evening to this mistake. Always use the one in `build/`.

```bash
fastboot flash boot_a build/boot-mobian-rmtfs.img
```

### Step 3: Ensure SD card rootfs is ready

If the SD card already has the working rootfs, skip to Step 4.

If you need to reflash the SD card from the backup dump:

```bash
# Flash the dump (30GB, ~25 minutes to write)
sudo dd if=images/sdcard-dump.img of=/dev/sdX bs=4M status=progress conv=fsync

# IMPORTANT: Disable droid-juicer (hangs forever on pdx213, blocks display manager)
sudo mount /dev/sdX /mnt/sdcard
sudo mkdir -p /mnt/sdcard/var/lib/droid-juicer
echo '{"status": "done"}' | sudo tee /mnt/sdcard/var/lib/droid-juicer/status.json
sudo ln -sf /dev/null /mnt/sdcard/etc/systemd/system/droid-juicer.service
sudo sync && sudo umount /mnt/sdcard
```

**Why droid-juicer**: Mobian ships `droid-juicer.service` to extract Android vendor firmware on first boot. It has configs for Fairphone, Google Pixel, etc. — but NOT Sony pdx213. Without a config, it hangs forever, and because it has `Before=plymouth-quit.service display-manager.service`, it blocks greetd/Phosh from ever starting.

### Step 4: Insert SD card and boot

Put the SD card in the phone, then:

```bash
fastboot reboot
```

**Expected**: Mobian spinner (10-30 seconds) → Phosh lock screen.

### Step 5: Connect via SSH

WiFi may auto-connect to the saved network (TELUS3530). If not, you need physical access to the lock screen, or:

```bash
# If WiFi is connected:
ssh mobian@192.168.1.83    # password: mobian

# If not, connect manually after login:
sudo nmcli con up wifi-wlan0
```

### Button combos

| Action | Buttons |
|--------|---------|
| Force power off | Hold Power + Volume Up |
| Enter fastboot | Volume Up while plugging in USB |
| `fastboot boot` | NOT supported on Sony ABL — must flash to boot_a |

---

## Boot Image Build Pipeline

Everything needed to rebuild the boot image is on the Mac:

```bash
cd /Users/terrace/Labs/Xperia
./build.sh          # builds build/boot-mobian-rmtfs.img
./build.sh flash    # builds + flashes to phone via WiFi SSH
```

### Prerequisites

- `dtc` (device tree compiler) — `brew install dtc`
- `python3`
- `mkbootimg.py` (in repo root, from AOSP)
- `patch-rmtfs.py` (in repo root, adds rmtfs-mem/firmware-name/UFS to DTS)

### Input files (in `build/`)

| File | What it is | Origin |
|------|-----------|--------|
| `zImage-raw` | Uncompressed Mobian 6.12.68 aarch64 kernel | Extracted from Mobian boot image |
| `initrd.img` | Mobian initramfs | Extracted from Mobian boot image |
| `device-wifi-rproc.dts` | Base device tree source with WiFi + remoteproc | Built up from stock DTB via successive patches |

### Pipeline

```
device-wifi-rproc.dts
  → patch-rmtfs.py → device-patched.dts   (adds rmtfs-mem, firmware-name, UFS)
  → dtc            → device-patched.dtb
  → cat zImage-raw device-patched.dtb → zImage-combined
  → mkbootimg.py   → boot-mobian-rmtfs.img
      --base 0x10000000
      --pagesize 4096
      --header_version 0
      --cmdline "mobile.root=UUID=... init=/sbin/init ro quiet splash"
```

**Key format constraints**:
- Header version **must be 0** (not v2)
- Kernel must be **uncompressed** (not gzipped) — gzip causes "devices is corrupt" bootloop
- Base address must be **0x10000000**
- Kernel + DTB are **concatenated** (cat), not in separate header fields

---

## Firmware

All firmware was extracted from Sony Open Devices packages and the stock firmware image:

- **Source**: `SW_binaries_for_Xperia_Android_13_4.19_v1b_lena.zip` + `XQ-BT52_EE UK_62.1.A.0.675.zip`
- **Extraction**: SIN files → sinunpack/simg2img → raw images → mount and copy

| Category | Files | Location on rootfs |
|----------|-------|--------------------|
| Modem | modem.mdt + .b*, modemr.jsn, modemuw.jsn | `/lib/firmware/qcom/sm6350/` |
| ADSP | adsp.mdt + .b*, adspr.jsn, adsps.jsn, adspua.jsn | `/lib/firmware/qcom/sm6350/` |
| CDSP | cdsp.mdt + .b*, cdspr.jsn | `/lib/firmware/qcom/sm6350/` |
| Venus (video) | venus.mdt + .b* | `/lib/firmware/qcom/sm6350/` |
| WiFi DSP | wlanmdsp.mbn | `/lib/firmware/qcom/sm6350/` |
| WiFi board | bdwlan.* | `/lib/firmware/ath10k/WCN3990/hw1.0/` |
| Bluetooth | apbtfw1*.tlv, apnv1*.bin, crbtfw*.tlv, crnv*.bin | `/lib/firmware/qca/` |
| GPU | a619_gmu.bin, a630_sqe.fw, a615_zap.*, a620_zap.* | `/lib/firmware/qcom/` |
| IPA | lagoon_ipa_fws.*, ipa_fws.* | `/lib/firmware/qcom/sm6350/` |

---

## DTB Modifications (vs stock Mobian)

The patched DTB (`device-patched.dtb`) includes these changes on top of the stock Mobian SM6350 DTB:

1. **Touch**: Removed `avdd-supply` phandle and `touch-en-regulator` node (prevents regulator framework from killing AMOLED panel)
2. **WiFi**: Added 5 regulator supplies to WCN3990 node (pm6350 ldo4/ldo7, pm6150l ldo2/ldo10/ldo11), set `status = "okay"`
3. **Remoteproc**: Enabled MPSS, ADSP, CDSP remoteproc nodes with `firmware-name` properties
4. **RMTFS**: Added `qcom,rmtfs-mem` reserved memory at 0x9b000000, size 0x300000 (3MB)
5. **UFS**: Enabled `ufs@1d84000` controller and `phy@1d87000`

---

## Rootfs Customizations (vs stock Mobian)

The SD card rootfs has these changes on top of the stock Mobian SM6350 weekly image:

1. All firmware files installed (see Firmware section above)
2. WiFi NetworkManager connection saved (SSID: TELUS3530, `cloned-mac-address=permanent`)
3. `enable-touch.sh` script — toggles GPIO 10 via chardev ioctl then `insmod s6sy761.ko`
4. Screen blanking disabled via gsettings for `_greetd` user
5. Display scale=2 in `/etc/phosh/phoc.ini`
6. `droid-juicer.service` masked and status.json created

---

## Known Issues / Next Steps

1. **Battery charging**: No `power_supply` driver. Needs kernel config `CONFIG_CHARGER_QCOM_SMB2` + `CONFIG_BATTERY_QCOM_QG`. Phone slowly drains in Linux.
2. **USB networking from Mac**: Kernel has RNDIS only, macOS needs ECM. Rebuild kernel with `CONFIG_USB_CONFIGFS_ECM=y`.
3. **WiFi auto-connect**: MAC randomization breaks ath10k. Current workaround is `cloned-mac-address=permanent` in NM, but WiFi doesn't auto-reconnect after reboot — must run `sudo nmcli con up wifi-wlan0`.
4. **Touch late load**: s6sy761 takes ~100s to probe (dummy regulator fallback for avdd).
5. **Bluetooth**: Firmware present but no DTS UART node (`qcom,wcn3991-bt`).
6. **GPU**: msm.ko module exists but must NOT be loaded under simpledrm. Proper DRM requires enabling DSI controller and adding panel driver (`samsung,sofef01-m-ams597ut04` — not in upstream kernel).

## Lessons Learned

- **Boot image naming**: The `images/` directory contains old intermediate attempts. The working output is always `build/boot-mobian-rmtfs.img`. Verify by timestamp, not filename.
- **droid-juicer**: Must be disabled on any fresh Mobian rootfs before first boot on pdx213. It has no Sony config and will hang forever, blocking the display manager.
- **Battery**: Always charge in fastboot before a long debug session. Linux can't charge the battery.
- **Display fragility**: simpledrm framebuffer is destroyed by any attempt to use real GPU/DRM. Test one change at a time, always reboot.
