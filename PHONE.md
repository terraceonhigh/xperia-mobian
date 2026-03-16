# Sony Xperia 10 III (pdx213) — Device Notes

## Hardware
- **Model**: Sony Xperia 10 III (XQ-BT52)
- **Codename**: pdx213 / Lena
- **SoC**: Qualcomm Snapdragon 690 5G (SM6350)
- **Serial**: HQ616S35A9
- **Bootloader**: Unlocked (`secure:no`), A/B slots

## Button Combos
- **Force off**: Power + Volume Up (hold)
- **Fastboot mode**: Volume Up while plugging in USB (auto-powers on when plugged in, so just hold Vol Up)
- **Note**: `fastboot boot` is NOT supported — must flash to boot_a/boot_b

## Boot Setup
- Boots from **microSD card** (current rootfs is on SD)
- Boot image is on internal UFS `boot_a` partition
- A/B slots: currently using slot a, both marked successful

## Connectivity
- **USB on Mac**: RNDIS not supported natively (no macOS driver). Need Linux VM with USB passthrough (UTM) for USB networking
- **WiFi**: TELUS3530 network, IP has been 192.168.1.83 (can change)
- **USB on Fedora laptop** (192.168.1.122): RNDIS works, phone at 10.66.0.1

## Known Quirks
- Don't restart Phosh — crashes I2C bus, kills touch. Always full reboot
- Touch (s6sy761) probes ~100s after boot (avdd supply dummy regulator)
- WiFi MAC randomization breaks ath10k — needs permanent MAC config
