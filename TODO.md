# pdx213 pmOS Port — Remaining Work

## What's Working (2026-03-15)
- Display (simpledrm, 1080x2520, scale=2)
- Touch (s6sy761, loads ~100s after boot)
- WiFi (WCN3990/ath10k, manual connect only)
- Modem (MPSS running stable, rmtfs + pd-mapper working)
- UFS (internal storage, all 79 partitions)
- Power button, volume keys
- USB networking (RNDIS to Fedora laptop)
- SSH over WiFi from Mac (192.168.1.175)

## Priority 1 — Daily Driver Basics

### Cellular (calls/SMS/data)
- Modem is running but no telephony stack configured
- Need: ModemManager or oFono, plus QMI/MBIM interface
- Check if `wwan0` or `rmnet*` interfaces appear
- May need IPA (IP Accelerator) for mobile data — IPA node exists in DTS but firmware-name not set
- Test: `mmcli -L` to see if ModemManager detects the modem

### Suspend/Resume
- Critical for battery life — without it, phone dies in hours
- Needs PSCI support + wakeup source configuration in DTS
- Test: `echo mem > /sys/power/state`
- Wakeup sources: power button, modem, USB
- This will likely require significant debugging

### Battery Monitoring
- No power_supply driver loaded
- Needs kernel rebuild: `CONFIG_CHARGER_QCOM_SMB2=y` (SMB5 charger on PM7250B)
- Fuel gauge: Qualcomm QG or PM7250B BMS — check which config option
- Without this, no battery indicator, no low-battery shutdown

## Priority 2 — Phone Experience

### Sound
- Check if audio codec node exists in DTS (likely WCD9385 or similar)
- Needs ADSP running (currently offline — has firmware-name set, just not started)
- PulseAudio/PipeWire + UCM config for routing
- Speaker, earpiece, mic all separate paths

### Bluetooth
- WCN3990 BT firmware already at `/lib/firmware/qca/`
- Needs UART DTS node with `qcom,wcn3990-bt` compatible
- Likely on `serial@884000` — check downstream DTS
- Once DTS node added, btqca.ko should probe

### Sensors
- Accelerometer, gyroscope, proximity, ambient light
- Likely I2C devices — check downstream DTS for sensor hub or individual sensors
- Needed for: auto-rotate, screen-off during calls, ambient brightness
- May need iio-sensor-proxy for Phosh integration

### GPS/GNSS
- Runs as modem subsystem via QMI
- Needs ModemManager + geoclue or gpsd
- Should work once cellular is configured

### WiFi Auto-Connect
- MAC randomization breaks ath10k — connection fails with `config-failed`
- Fix: NetworkManager config to use permanent MAC on wlan0
- Add `/etc/NetworkManager/conf.d/` drop-in or fix connection profile

## Priority 3 — Nice to Have

### GPU Hardware Acceleration
- msm.ko exists, a619 firmware on phone
- Loading msm.ko breaks simpledrm — need proper DRM transition
- Needs: enable GPU node in DTS, set firmware-name for a615_zap
- Mesa freedreno driver should work once DRM is up
- Big quality-of-life improvement (smooth UI, video playback)

### Camera
- Hardest item. Front + rear triple cameras
- Needs: CCI (Camera Control Interface), CSIPHY, CSID, VFE/ISP pipeline
- libcamera + sensor drivers (likely IMX sensor)
- Probably last thing to tackle

### Vibration Motor
- Likely a PMIC LDO or GPIO-controlled motor
- Check downstream DTS for vibrator node

### NFC
- Sony devices have NFC — check for I2C NFC controller
- Low priority for Linux phone use

### LED Notifications
- RGB LED, likely PMIC GPIO or LPG (Light Pulse Generator)
- Check PM6350/PM7250B for LED nodes

### Display Scale
- Currently scale=2, user says "small but usable"
- Try scale=3 after next reboot (don't restart Phosh — reboot!)

## Priority 4 — pmOS Packaging

### Kernel Package
- Fork `linux-postmarketos-qcom-sm6350` or build custom kernel
- Enable: `CONFIG_CHARGER_QCOM_SMB2`, QG fuel gauge, any missing sensor drivers
- Apply DTS patches from patch-wifi.py, patch-remoteproc.py, patch-rmtfs.py as proper .patch files
- Run `pmbootstrap kconfig check` against kconfigcheck.toml

### Device Package
- Create `device-sony-pdx213/` in pmaports `device/testing/`
- deviceinfo: flash method, DTB path, boot offsets
- modules-initfs: s6sy761 if modular, ath10k_snoc, etc.
- Dependencies: hexagonrpcd, pd-mapper, tqftpserv, qbootctl, rmtfs, msm-modem

### Firmware Package
- Split firmware into `firmware-sony-pdx213-*` packages
- Modem, ADSP, CDSP, WiFi, Bluetooth, GPU, IPA, DSP hexagonfs
- Reference: FP4 firmware packaging

## Build Infrastructure Notes
- Builds on Bazzite `192.168.1.91` at `~/Lab/xperia-pmos/`
- DTB work dir: `~/tmp-dtb/`
- dtc: `/usr/src/kernels/6.17.7-ba25.fc43.x86_64/scripts/dtc/dtc`
- mkbootimg: `podman exec kernel-build mkbootimg`
- Boot image: raw (uncompressed) kernel+DTB, base 0x10000000, pagesize 4096, header v0
- **Never gzip the kernel** — causes "devices is corrupt" bootloop
- Fastboot on Fedora laptop: `sudo /var/home/terrace/.local/bin/fastboot`
