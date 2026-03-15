#!/bin/bash
# fix-blanking.sh — Disable screen blanking for phosh greeter on pdx213
#
# Run from Mac after the phone has booted to lock screen.
# Sets gsettings for _greetd user to prevent idle blanking.
# Settings persist across reboots in _greetd's dconf database.
#
# Usage: ./fix-blanking.sh

set -euo pipefail

JUMP_HOST="terrace@192.168.1.122"
PHONE="mobian@10.66.0.1"

echo "Connecting to phone via ${JUMP_HOST}..."

ssh -J "$JUMP_HOST" "$PHONE" bash -s << 'REMOTE'
set -euo pipefail

DBUS_ADDR=$(sudo grep -z DBUS_SESSION_BUS_ADDRESS \
  /proc/$(pgrep -u _greetd -f phoc | head -1)/environ 2>/dev/null \
  | tr '\0' '\n' | grep DBUS_SESSION | cut -d= -f2-)

if [ -z "$DBUS_ADDR" ]; then
  echo "ERROR: Could not find _greetd dbus session. Is phoc running?"
  exit 1
fi

echo "Found dbus: $DBUS_ADDR"

sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.desktop.session idle-delay 0
sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.settings-daemon.plugins.power idle-dim false
sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type nothing

echo "Verifying..."
VAL=$(sudo -u _greetd DBUS_SESSION_BUS_ADDRESS="$DBUS_ADDR" \
  gsettings get org.gnome.desktop.session idle-delay)
echo "idle-delay = $VAL"

if [ "$VAL" = "uint32 0" ]; then
  echo "OK: Screen blanking disabled for _greetd"
else
  echo "WARN: idle-delay not set correctly"
  exit 1
fi
REMOTE
