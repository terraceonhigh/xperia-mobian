#!/bin/bash
# enable-touch.sh — Enable touchscreen on pdx213 after boot
#
# Requires boot-mobian-noavdd2.img (DTB with avdd-supply and
# touch-en-regulator removed). This script:
#   1. Sets TLMM GPIO 10 high (powers touch IC AVDD rail)
#   2. Loads s6sy761.ko (touch driver)
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

# Check if touch is already loaded
if lsmod | grep -q s6sy761; then
  echo "s6sy761 already loaded"
  ls /dev/input/event* 2>/dev/null
  exit 0
fi

# Step 1: Set GPIO 10 high (touch AVDD power rail)
echo "Setting GPIO 10 (touch AVDD) high..."
sudo python3 << 'PYEOF'
import os, struct, fcntl, sys

GPIOHANDLE_REQUEST_OUTPUT = 0x02
GPIO_GET_LINEHANDLE_IOCTL = 0xC16CB403

fd = os.open("/dev/gpiochip1", os.O_RDWR)

req = bytearray(364)
struct.pack_into("<I", req, 0, 10)       # lineoffsets[0] = GPIO 10
struct.pack_into("<I", req, 256, GPIOHANDLE_REQUEST_OUTPUT)
req[260] = 1                              # default_values[0] = HIGH
label = b"touch_avdd"
req[324:324+len(label)] = label
struct.pack_into("<I", req, 356, 1)       # lines = 1

try:
    result = fcntl.ioctl(fd, GPIO_GET_LINEHANDLE_IOCTL, bytes(req))
except OSError as e:
    print(f"ERROR: GPIO 10 busy ({e}) — is touch-en-regulator still in DTB?")
    sys.exit(1)

result_buf = bytearray(result)
line_fd = struct.unpack_from("<i", result_buf, 360)[0]
os.close(fd)

# Fork a child to hold the GPIO high
pid = os.fork()
if pid == 0:
    import time
    while True:
        time.sleep(3600)
else:
    print(f"GPIO 10 HIGH (held by pid {pid})")
PYEOF

# Brief settle time for touch IC power-on
sleep 0.5

# Step 2: Load touch driver
echo "Loading s6sy761..."
sudo insmod /usr/lib/modules/6.12-sm6350/kernel/drivers/input/touchscreen/s6sy761.ko

# Verify
if lsmod | grep -q s6sy761; then
  echo "OK: Touch driver loaded"
  ls /dev/input/event*
  dmesg | grep s6sy761 | tail -3
else
  echo "ERROR: s6sy761 failed to load"
  dmesg | grep -i s6sy | tail -5
  exit 1
fi
REMOTE
