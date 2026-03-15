# Mobian on Sony Xperia 10 III (pdx213)

Mainline Linux (Debian/Mobian) on the Sony Xperia 10 III.

## Device
- **Model**: Sony Xperia 10 III (XQ-BT52)
- **Codename**: pdx213 / Lena
- **SoC**: Qualcomm Snapdragon 690 5G (SM6350)
- **Kernel**: Mainline Linux 6.12-sm6350 (sm6350-mainline fork)
- **Distro**: Mobian (Debian Trixie)
- **Base image**: Mobian SM6350 weekly

## Status
- Boot: working (mainline kernel boots from microSD rootfs)
- Display: simpledrm only (bootloader-initialized framebuffer, no GPU driver)
- GPU: NOT working (missing a619_gmu.bin, a615_zap.mbn firmware)
- Touch: Samsung S6SY761 — driver loads, generates events, but axis properties not applied
- Bluetooth: untested (no UI access)
- UFS (internal storage): NOT working (microSD rootfs required)
- WiFi/Modem: NOT working (blocked by UFS — firmware on internal storage)

## Critical Issue: Display
The display uses `simpledrm` (bootloader-initialized framebuffer). Once any
compositor (phoc/wlroots) does a DRM modeset, the bootloader framebuffer is
destroyed and the display goes black permanently until reboot. The OLED panel
cannot be re-initialized without a proper MSM DRM/DSI driver, which requires
GPU firmware that we cannot extract (UFS not working).

## Partition Layout
- `boot_a`: Mobian boot.img (mainline kernel + initramfs + DTB)
- `vbmeta_a/b`: Disabled (flags=3)
- `vbmeta_system_a/b`: Disabled (flags=3)
- `dtbo_a/b`: Erased
- Rootfs: microSD card (ext4, 29.7GB)

## Boot Image Format (Sony ABL Requirements)
- Header version: **0** (not v2!)
- Kernel: **gzip-compressed** (vmlinuz.gz + DTB concatenated)
- Base address: **0x10000000** (AOSP mkbootimg default)
- Page size: 4096
- `fastboot boot` NOT supported — must flash to boot_a

## Boot Images
- `boot-mobian.img` — Original Mobian weekly SM6350 boot image (known good)
- `boot-mobian-touch.img` — Modified DTB with touchscreen-size-x/y properties

## Infrastructure
- Phone stays plugged into Fedora laptop (192.168.1.122)
- Fastboot/adb: container `xperia` on Fedora laptop
- SSH to phone: `ssh -J terrace@192.168.1.122 mobian@10.66.0.1`
- SD card reader: Fedora laptop, mounts at /dev/sda

## Recovery
Flash stock boot to restore Android:
```
fastboot flash boot_a stock-boot.img
fastboot flash vbmeta_a vbmeta-stock.img
fastboot flash vbmeta_b vbmeta-stock.img
fastboot flash vbmeta_system_a vbmeta-system-stock.img
fastboot flash vbmeta_system_b vbmeta-system-stock.img
fastboot flash dtbo_a dtbo-stock.img
fastboot flash dtbo_b dtbo-stock.img
```
