#!/bin/bash
# Flash Mobian to Sony Xperia 10 III (pdx213)
# Phone must be in fastboot mode (vol-up + power during boot)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGES_DIR="$SCRIPT_DIR/../images"

echo "=== Mobian Flash for pdx213 ==="
echo "Ensure phone is in fastboot mode."
echo ""

# Check fastboot
if ! fastboot devices | grep -q .; then
    echo "ERROR: No fastboot device found."
    exit 1
fi

echo "[1/4] Disabling AVB verification..."
fastboot flash vbmeta_a "$IMAGES_DIR/vbmeta-disabled.img"
fastboot flash vbmeta_b "$IMAGES_DIR/vbmeta-disabled.img"
fastboot flash vbmeta_system_a "$IMAGES_DIR/vbmeta-system-disabled.img"
fastboot flash vbmeta_system_b "$IMAGES_DIR/vbmeta-system-disabled.img"

echo "[2/4] Erasing DTBO..."
fastboot erase dtbo_a
fastboot erase dtbo_b

echo "[3/4] Flashing boot image..."
fastboot flash boot_a "$IMAGES_DIR/boot-mobian.img"

echo "[4/4] Rebooting..."
fastboot reboot

echo ""
echo "Done! Insert microSD with Mobian rootfs if not already inserted."
echo "Default credentials: mobian / 1234"
