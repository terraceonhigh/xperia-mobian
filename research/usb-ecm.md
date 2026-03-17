# USB ECM Networking Research — pdx213

**Date**: 2026-03-16
**Status**: Research complete, implementation requires kernel rebuild

## Current State

- Kernel has `CONFIG_USB_CONFIGFS_RNDIS=y` and `CONFIG_USB_F_RNDIS=y`
- macOS has no RNDIS support (HoRNDIS kext dead on modern macOS)
- macOS natively supports CDC ECM — devices appear as Ethernet interfaces
- USB networking currently only works from Linux hosts (Fedora laptop)

## Kernel Config Changes Needed

```
# Enable in config-mobian-working:
CONFIG_USB_CONFIGFS_ECM=y       # was: # CONFIG_USB_CONFIGFS_ECM is not set
CONFIG_USB_F_ECM=y              # will be auto-selected by above

# Optional — NCM is newer/faster than ECM, also macOS compatible:
CONFIG_USB_CONFIGFS_NCM=y       # was: # CONFIG_USB_CONFIGFS_NCM is not set
```

## Mobian USB Gadget Setup

Mobian uses `mobile-usb-gadget.service` to configure the USB gadget at boot. The service was failing on boot (observed in boot.log). Need to check:
1. What script it runs — likely creates ConfigFS gadget with RNDIS function
2. Whether adding ECM function requires script changes or just kernel config
3. Whether both RNDIS + ECM can be offered simultaneously (composite gadget)

### Typical ConfigFS ECM setup:
```bash
mkdir -p /sys/kernel/config/usb_gadget/g1/functions/ecm.usb0
# Set host/dev MAC addresses
echo "host_mac" > /sys/kernel/config/usb_gadget/g1/functions/ecm.usb0/host_addr
# Link to configuration
ln -s /sys/kernel/config/usb_gadget/g1/functions/ecm.usb0 /sys/kernel/config/usb_gadget/g1/configs/c.1/
```

## Implementation Plan

1. Enable ECM (and optionally NCM) in kernel config
2. Rebuild kernel
3. Check `mobile-usb-gadget.service` script on phone — may need modification to create ECM function alongside or instead of RNDIS
4. Test from Mac: should appear as `en*` Ethernet interface

## Risk

Low — USB gadget config is userspace. If ECM doesn't work, RNDIS still functions for Linux hosts. Worst case: USB networking breaks until gadget script is fixed (SSH via WiFi still works).
