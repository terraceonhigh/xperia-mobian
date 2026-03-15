#!/bin/bash
# enable-touch.sh — Enable touchscreen on pdx213 after boot
#
# Requires boot-mobian-noavdd2.img (DTB with avdd-supply and
# touch-en-regulator removed). This script:
#   1. Sets TLMM GPIO 10 high (powers touch IC AVDD rail)
#   2. Resets touch IC via GPIO 21 (reset pin)
#   3. Loads s6sy761.ko (touch driver)
#
# Run from Mac after the phone has booted to lock screen.
# The GPIO must be held high for the duration of use (a background
# process keeps the chardev fd open).
#
# Usage: ./enable-touch.sh

set -euo pipefail

JUMP_HOST="terrace@192.168.1.122"
PHONE="mobian@10.66.0.1"

echo "Enabling touchscreen on phone via ${JUMP_HOST}..."

ssh -J "$JUMP_HOST" "$PHONE" bash -s << 'REMOTE'
set -euo pipefail

# Check if touch is already working
if [ -e /dev/input/event3 ] && sudo timeout 0.1 cat /dev/input/event3 >/dev/null 2>&1; then
  echo "Touch already active on event3"
  exit 0
fi

# Step 1: Set GPIO 10 high (touch AVDD power rail)
# Step 2: Reset touch IC via GPIO 21
echo "Powering touch IC and resetting..."
sudo python3 << 'PYEOF'
import os, struct, fcntl, time, sys

GPIOHANDLE_REQUEST_OUTPUT = 0x02
GPIO_GET_LINEHANDLE_IOCTL = 0xC16CB403
GPIOHANDLE_SET_LINE_VALUES_IOCTL = 0xC040B409

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
        print(f"ERROR: GPIO {gpio_num} busy ({e})")
        sys.exit(1)
    result_buf = bytearray(result)
    return struct.unpack_from("<i", result_buf, 360)[0]

def set_gpio(line_fd, value):
    values = bytearray(64)
    values[0] = value
    fcntl.ioctl(line_fd, GPIOHANDLE_SET_LINE_VALUES_IOCTL, bytes(values))

fd = os.open("/dev/gpiochip1", os.O_RDWR)

# GPIO 10: AVDD power — set HIGH
avdd_fd = request_gpio(fd, 10, 1, "touch_avdd")
print("GPIO 10 HIGH (AVDD on)")

# GPIO 21: reset — assert LOW, wait, release HIGH
rst_fd = request_gpio(fd, 21, 0, "touch_rst")
print("GPIO 21 LOW (reset asserted)")
time.sleep(0.2)
set_gpio(rst_fd, 1)
print("GPIO 21 HIGH (reset released)")
os.close(rst_fd)

os.close(fd)

# Wait for IC to initialize after reset
time.sleep(1)
print("Touch IC ready")

# Fork a child to hold AVDD GPIO high
pid = os.fork()
if pid == 0:
    while True:
        time.sleep(3600)
else:
    print(f"AVDD held by pid {pid}")
PYEOF

# Step 3: Load touch driver
if lsmod | grep -q s6sy761; then
  echo "s6sy761 already loaded, rebinding..."
  echo '0-0048' | sudo tee /sys/bus/i2c/drivers/s6sy761/unbind >/dev/null 2>&1 || true
  sleep 0.5
  echo '0-0048' | sudo tee /sys/bus/i2c/drivers/s6sy761/bind >/dev/null 2>&1
else
  echo "Loading s6sy761..."
  sudo insmod /usr/lib/modules/6.12-sm6350/kernel/drivers/input/touchscreen/s6sy761.ko
fi

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
