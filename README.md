# Mobian on Sony Xperia 10 III (pdx213)

Mainline Linux (Debian/Mobian) on the Sony Xperia 10 III.

## Device
- **Model**: Sony Xperia 10 III (XQ-BT52)
- **Codename**: pdx213 / Lena
- **SoC**: Qualcomm Snapdragon 690 5G (SM6350)
- **Kernel**: Mainline Linux 6.12-sm6350 (sm6350-mainline fork)
- **Distro**: Mobian (Debian Trixie)
- **Base image**: Mobian SM6350 weekly

## Status (Golden tag)
- Boot: working
- Display: working (phrog greeter shows lock screen via simpledrm)
- GPU: simpledrm only (no hardware acceleration)
- Touch: driver probes successfully but **kills simpledrm display** (see ROOTFS_MODS.md)
- UFS (internal storage): NOT working (microSD rootfs required)
- WiFi/Modem: NOT working (firmware on internal storage, UFS broken)
- Bluetooth: untested
- SSH: working (`ssh -J terrace@192.168.1.122 mobian@10.66.0.1`)

## Display Notes
The display uses `simpledrm` (bootloader-initialized framebuffer). The phrog
greeter (phoc compositor) renders to this framebuffer successfully in its
stock configuration. Key constraints:
- Do NOT set `WLR_RENDERER_ALLOW_SOFTWARE=1` — this causes phoc to use
  llvmpipe which does a modeset that destroys the bootloader framebuffer
- Do NOT load the `msm` DRM kernel module — conflicts with simpledrm
- Do NOT install GPU firmware (a619_gmu.bin) — triggers MSM DRM probe
- The phrog greeter must run in its stock configuration
- Screen will blank after idle timeout unless _greetd gsettings are set (see ROOTFS_MODS.md)
- simpledrm DPMS off is irrecoverable — must prevent blanking, not try to wake

## GPU Firmware (for future work)
The Adreno 619 GPU needs firmware not included in Debian's `firmware-qcom-soc`:
- `a619_gmu.bin` — GMU firmware (available from FairBlobs/FP4-firmware)
- `a615_zap.mdt` + `.b00-.b02` — ZAP shader (available from FairBlobs/FP4-firmware)
- `a630_sqe.fw` — already in firmware-qcom-soc
- The `msm` DRM module (`CONFIG_DRM_MSM=m`) exists but needs deps: `drm_exec`, `gpu-sched`, `drm_display_helper`
- Enabling GPU requires the MSM DRM driver to take over from simpledrm

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
- `boot-mobian.img` — Original Mobian weekly SM6350 boot image (Golden)
- `boot-mobian-touch.img` — Modified DTB with touchscreen-size-x/y properties

## Infrastructure
- Phone stays plugged into Fedora laptop (192.168.1.122)
- Fastboot/adb: container `xperia` on Fedora laptop (`sudo podman exec xperia fastboot ...`)
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
