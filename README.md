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

| Feature | Status | Notes |
|---|---|---|
| Boot | **Working** | Mainline kernel, microSD rootfs |
| Display | **Working** | simpledrm, 1080x2520 AMOLED, scale=2 |
| Touch | **Working** | Samsung S6SY761 via I2C, auto-loads ~100s after boot |
| Power button | **Working** | Sleep/wake works |
| WiFi | **Working** | WCN3990 (ath10k_snoc), connects to WPA2 |
| Modem | **Running** | MPSS stable, rmtfs + pd-mapper working |
| UFS | **Working** | Internal storage, all 79 partitions visible |
| USB networking | **Working** | RNDIS, SSH via jump host |
| GPU | simpledrm only | msm DRM module exists but not enabled |
| Sound | Not working | Needs ADSP + codec DTS work |
| Bluetooth | Not working | Firmware present, needs UART DTS node |
| Cellular | Not configured | Modem runs but no telephony stack |
| Battery | Not working | Needs kernel rebuild (SMB5 charger driver) |
| Camera | Not working | Needs CCI/ISP pipeline |
| Sensors | Not working | Needs DTS enable |
| Suspend | Not tested | Critical for battery life |

## DTB Modifications

The Mobian weekly boot image DTB is patched with three scripts (in order):

1. **`patch-wifi.py`** — Adds WCN3990 WiFi regulator supplies (`vdd-0.8-cx-mx`, `vdd-1.8-xo`, `vdd-1.3-rfa`, `vdd-3.3-ch0/ch1`) and sets WiFi node `status = "okay"`
2. **`patch-remoteproc.py`** — Enables ADSP, MPSS, CDSP remoteproc nodes
3. **`patch-rmtfs.py`** — Adds `qcom,rmtfs-mem` reserved memory (3MB at 0x9b000000), `firmware-name` properties on remoteproc nodes, enables UFS controller + PHY

## Firmware

Sony firmware extracted from stock ROM (`XQ-BT52_EE UK_62.1.A.0.675.zip`) and Sony Open Devices blobs. Installed to phone SD card rootfs at `/lib/firmware/`.

| Category | Location |
|---|---|
| Modem (MPSS) | `/lib/firmware/qcom/sm6350/modem.mdt` + `.b*` |
| ADSP | `/lib/firmware/qcom/sm6350/adsp.mdt` + `.b*` |
| CDSP | `/lib/firmware/qcom/sm6350/cdsp.mdt` + `.b*` |
| WiFi (WCN3990) | `/lib/firmware/ath10k/WCN3990/hw1.0/bdwlan.*` |
| Bluetooth | `/lib/firmware/qca/` |
| GPU (Adreno 619) | `/lib/firmware/qcom/a619_gmu.bin`, `a630_sqe.fw` |

## Boot Image Format

Sony ABL requirements:
- Header version: **0** (not v2)
- Kernel: **raw/uncompressed** (kernel + DTB concatenated, NOT gzipped)
- Base address: **0x10000000**
- Page size: 4096
- `fastboot boot` NOT supported — must flash to `boot_a`

## Boot Images

| Image | Description |
|---|---|
| `boot-mobian-rmtfs.img` | **Current best** — WiFi + modem + UFS + rmtfs (everything working) |
| `boot-mobian-wifi-rproc.img` | WiFi + remoteproc, no UFS/rmtfs |
| `boot-mobian-noavdd2.img` | Touch fix only, no WiFi/modem |
| `boot-mobian.img` | Original Mobian weekly (Golden baseline) |

## Known Quirks

- **Don't restart Phosh** — `systemctl restart phosh` crashes the I2C DMA controller, killing touch. Always do a full `sudo reboot`.
- **WiFi MAC randomization** — breaks ath10k. Must use `802-11-wireless.cloned-mac-address permanent` in NetworkManager.
- **WiFi doesn't auto-connect** after reboot. Run `sudo nmcli con up wifi-wlan0`.
- **Touch loads late** (~100s) — `avdd` supply not found, falls back to dummy regulator.
- **Gzip kernel = bootloop** — Sony ABL rejects gzipped kernels with "devices is corrupt".

## Infrastructure

- **Direct SSH (WiFi)**: `ssh mobian@192.168.1.175`
- **SSH (USB)**: `ssh -J terrace@192.168.1.122 mobian@10.66.0.1`
- **Fastboot**: `ssh terrace@192.168.1.122 "sudo /var/home/terrace/.local/bin/fastboot ..."`
- **Build machine**: Bazzite `192.168.1.91`, DTB work at `~/tmp-dtb/`

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
