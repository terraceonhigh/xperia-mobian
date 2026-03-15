#!/bin/bash
# enable-touch.sh — Enable touchscreen on pdx213 after boot
#
# Requires boot-mobian-noavdd2.img (DTB with avdd-supply and
# touch-en-regulator removed). This script:
#   1. Sets TLMM GPIO 10 high (powers touch IC AVDD rail)
#   2. Resets touch IC via GPIO 21 (low 0.5s, high, 2s settle)
#   3. Loads s6sy761.ko or unbinds/rebinds if already loaded
#
# The initial insmod often probes before the IC is fully ready,
# causing I2C DMA errors on subsequent reads. The reliable pattern
# is: insmod (may partially fail), unbind, reset, rebind.
#
# Run from Mac after the phone has booted to lock screen.
# A background process holds the GPIO chardev fd to keep AVDD high.
#
# Usage: ./enable-touch.sh

set -euo pipefail

JUMP_HOST="terrace@192.168.1.122"
PHONE="mobian@10.66.0.1"

echo "Enabling touchscreen on phone via ${JUMP_HOST}..."

ssh -J "$JUMP_HOST" "$PHONE" bash -s << 'REMOTE'
set -euo pipefail

# Step 1: Set GPIO 10 high (touch AVDD power rail)
echo "Powering touch IC (GPIO 10 HIGH)..."
sudo python3 << 'PYEOF'
import os, struct, fcntl, time, sys

GPIOHANDLE_REQUEST_OUTPUT = 0x02
GPIO_GET_LINEHANDLE_IOCTL = 0xC16CB403

def request_gpio(chip_fd, gpio_num, initial, label_str):
    req = bytearray(364)
    struct.pack_into("<I", req, 0, gpio_num)
    struct.pack_into("<I", req, 256, GPIOHANDLE_REQUEST_OUTPUT)
    req[260] = initial
    label = label_str.encode()
    req[324:324+len(label)] = label
    struct.pack_into("<I", req, 356, 1)
    try:
        result = fcntl.ioctl(chip_fd, GPIO_GET_LINEHANDLE_IOCTL, bytes(req))
    except OSError as e:
        if e.errno == 16:  # EBUSY — already held
            print(f"GPIO {gpio_num} already held (OK)")
            return -1
        print(f"ERROR: GPIO {gpio_num}: {e}")
        sys.exit(1)
    result_buf = bytearray(result)
    return struct.unpack_from("<i", result_buf, 360)[0]

fd = os.open("/dev/gpiochip1", os.O_RDWR)
avdd_fd = request_gpio(fd, 10, 1, "touch_avdd")
os.close(fd)

if avdd_fd >= 0:
    print("GPIO 10 HIGH (AVDD on)")
    pid = os.fork()
    if pid == 0:
        while True:
            time.sleep(3600)
    else:
        print(f"AVDD held by pid {pid}")
PYEOF

# Step 2: Load module if not already loaded
if ! lsmod | grep -q s6sy761; then
  echo "Loading s6sy761..."
  sudo insmod /usr/lib/modules/6.12-sm6350/kernel/drivers/input/touchscreen/s6sy761.ko 2>&1 || true
fi

# Step 3: Unbind (the initial probe often has I2C errors)
echo "Unbinding for clean re-probe..."
echo '0-0048' | sudo tee /sys/bus/i2c/drivers/s6sy761/unbind >/dev/null 2>&1 || true
sleep 0.5

# Step 4: Reset touch IC via GPIO 21 (0.5s low, 2s settle)
echo "Resetting touch IC (GPIO 21)..."
sudo python3 << 'PYEOF'
import os, struct, fcntl, time

GPIOHANDLE_REQUEST_OUTPUT = 0x02
GPIO_GET_LINEHANDLE_IOCTL = 0xC16CB403
GPIOHANDLE_SET_LINE_VALUES_IOCTL = 0xC040B409

fd = os.open("/dev/gpiochip1", os.O_RDWR)
req = bytearray(364)
struct.pack_into("<I", req, 0, 21)
struct.pack_into("<I", req, 256, GPIOHANDLE_REQUEST_OUTPUT)
req[260] = 0
label = b"touch_rst"
req[324:324+len(label)] = label
struct.pack_into("<I", req, 356, 1)
result = fcntl.ioctl(fd, GPIO_GET_LINEHANDLE_IOCTL, bytes(req))
result_buf = bytearray(result)
rst_fd = struct.unpack_from("<i", result_buf, 360)[0]
os.close(fd)

print("Reset LOW")
time.sleep(0.5)
values = bytearray(64)
values[0] = 1
fcntl.ioctl(rst_fd, GPIOHANDLE_SET_LINE_VALUES_IOCTL, bytes(values))
print("Reset HIGH")
os.close(rst_fd)
time.sleep(2)
print("IC ready")
PYEOF

# Step 5: Rebind — clean probe after reset
echo "Rebinding driver..."
for i in 1 2 3; do
  echo "0-0048" | sudo tee /sys/bus/i2c/drivers/s6sy761/bind >/dev/null 2>&1 && break
  echo "  Retry $i..."
  sleep 1
done

sleep 0.5

# Verify
if ls /dev/input/event3 >/dev/null 2>&1; then
  echo "OK: Touch enabled"
  dmesg | grep s6sy761 | tail -3
else
  echo "ERROR: No event3 device"
  dmesg | grep -i s6sy | tail -5
  exit 1
fi
REMOTE
