#!/bin/bash
# Restore stock Android on Sony Xperia 10 III (pdx213)
# Phone must be in fastboot mode (vol-up + power during boot)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGES_DIR="$SCRIPT_DIR/../images"

echo "=== Restore Stock Android for pdx213 ==="
echo "Ensure phone is in fastboot mode."
echo ""

if ! fastboot devices | grep -q .; then
    echo "ERROR: No fastboot device found."
    exit 1
fi

echo "[1/3] Restoring stock vbmeta..."
fastboot flash vbmeta_a "$IMAGES_DIR/vbmeta-stock.img"
fastboot flash vbmeta_b "$IMAGES_DIR/vbmeta-stock.img"
fastboot flash vbmeta_system_a "$IMAGES_DIR/vbmeta-system-stock.img"
fastboot flash vbmeta_system_b "$IMAGES_DIR/vbmeta-system-stock.img"

echo "[2/3] Restoring stock boot and dtbo..."
fastboot flash boot_a "$IMAGES_DIR/boot-stock.img"
fastboot flash dtbo_a "$IMAGES_DIR/dtbo-stock.img"
fastboot flash dtbo_b "$IMAGES_DIR/dtbo-stock.img"

echo "[3/3] Rebooting..."
fastboot reboot

echo "Done! Android should boot normally."
