#!/bin/bash
# Build boot image for pdx213 entirely on Mac, flash via WiFi SSH.
# Usage: ./build.sh [flash]
#   Without args: builds boot-mobian-rmtfs.img in build/
#   With "flash": also scp + dd to phone and reboot
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD="$DIR/build"
PHONE="mobian@192.168.1.175"

# Check prerequisites
for tool in dtc python3; do
    command -v "$tool" >/dev/null || { echo "Missing: $tool"; exit 1; }
done
for f in "$BUILD/zImage-raw" "$BUILD/initrd.img" "$BUILD/device-wifi-rproc.dts"; do
    [ -f "$f" ] || { echo "Missing: $f (scp from Bazzite ~/tmp-dtb/ first)"; exit 1; }
done

echo "=== Patching DTS ==="
# patch-wifi.py and patch-remoteproc.py are already baked into device-wifi-rproc.dts
# We only need to run patch-rmtfs.py on top
python3 "$DIR/patch-rmtfs.py" "$BUILD/device-wifi-rproc.dts" "$BUILD/device-patched.dts"

echo "=== Compiling DTB ==="
dtc -I dts -O dtb -o "$BUILD/device-patched.dtb" "$BUILD/device-patched.dts" 2>/dev/null

echo "=== Building boot image ==="
cat "$BUILD/zImage-raw" "$BUILD/device-patched.dtb" > "$BUILD/zImage-combined"
python3 "$DIR/mkbootimg.py" \
    --kernel "$BUILD/zImage-combined" \
    --ramdisk "$BUILD/initrd.img" \
    --base 0x10000000 \
    --pagesize 4096 \
    --header_version 0 \
    --cmdline "mobile.root=UUID=a1132a8f-e803-4518-9869-49f5a7d2c173 mobile.qcomsoc=qcom/sm6350 mobile.vendor=sony mobile.model=xperia-lena-pdx213 init=/sbin/init ro quiet splash" \
    -o "$BUILD/boot-mobian-rmtfs.img"

echo "=== Done: $BUILD/boot-mobian-rmtfs.img ==="
ls -la "$BUILD/boot-mobian-rmtfs.img"

if [ "$1" = "flash" ]; then
    echo "=== Flashing via WiFi SSH ==="
    scp "$BUILD/boot-mobian-rmtfs.img" "$PHONE:/tmp/boot-mobian-rmtfs.img"
    ssh "$PHONE" "echo mobian | sudo -S dd if=/tmp/boot-mobian-rmtfs.img of=/dev/disk/by-partlabel/boot_a bs=4096 2>&1 && echo 'Flash OK, rebooting...' && echo mobian | sudo -S reboot"
    echo "=== Phone is rebooting ==="
fi
