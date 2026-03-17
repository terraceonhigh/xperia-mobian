# Bluetooth Research — pdx213

**Date**: 2026-03-16
**Status**: Patch ready, boot image built, UNTESTED

## Summary

Bluetooth on SM6350/pdx213 uses the **WCN3991** chip with the `qcom,wcn3991-bt` driver. Unlike older Qualcomm BT, this uses QMI transport (not UART HCI), so the node is a simple top-level DTS entry.

All kernel modules are already built in the Mobian 6.12.68 kernel:
- `CONFIG_BT_QCA=m`
- `CONFIG_BT_HCIUART=m` with `CONFIG_BT_HCIUART_QCA=y`
- `CONFIG_SERIAL_QCOM_GENI=y`

Firmware is already on the rootfs at `/lib/firmware/qca/crnv32u.bin`.

The ONLY missing piece was the DTS node.

## What was added

A `bluetooth` node was added to the DTS (via `patch-bluetooth.py`), placed as a sibling of the WiFi node in the SoC bus:

```dts
bluetooth {
    compatible = "qcom,wcn3991-bt";
    vddio-supply = <&pm6350_l11>;   /* phandle 0x47 */
    vddxo-supply = <&pm6350_l7>;    /* phandle 0x9b, shared with WiFi */
    vddrf-supply = <&pm6150l_l2>;   /* phandle 0x9c, shared with WiFi */
    vddch0-supply = <&pm6150l_l10>; /* phandle 0x9d, shared with WiFi */
    swctrl-gpios = <&tlmm 69 GPIO_ACTIVE_HIGH>;  /* phandle 0x46, gpio 0x45 */
    firmware-name = "crnv32u.bin";
};
```

## Reference

Upstream source: `sm6350-kernel/arch/arm64/boot/dts/qcom/sm6350-sony-xperia-lena-pdx213.dts` lines 831-839.

## Build artifact

```
build/boot-mobian-bt.img    (26MB, built 2026-03-16)
```

This image contains everything from `boot-mobian-rmtfs.img` PLUS the bluetooth node.

## How to test

1. Flash: `fastboot flash boot_a build/boot-mobian-bt.img`
2. Boot and SSH in
3. Check: `dmesg | grep -i bluetooth`
4. Check: `hciconfig` or `bluetoothctl show`
5. If BT adapter appears, try pairing

## Rollback

Flash the original working image: `fastboot flash boot_a build/boot-mobian-rmtfs.img`

## Risks

Low — if the BT driver fails to probe, it doesn't affect WiFi or display. The regulators are shared with WiFi (already working), so power sequencing should be fine. Worst case: module fails to load, BT doesn't appear, everything else still works.
