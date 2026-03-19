# Bluetooth — pdx213 (Sony Xperia 10 III)

**Date**: 2026-03-18
**Status**: Tested failed — driver probes and loads firmware, but UART communication fails during setup phase

## Summary

The pdx213 uses a WCN3991 Bluetooth chip sharing the WCN3990 WiFi/BT combo silicon. The BT interface uses UART (serdev) via QUP1 (`serial@884000`). The kernel has all required modules built (`hci_uart`, `btqca`), and firmware files are present on the rootfs. The DTS node was missing — we added it, and the driver now probes successfully and downloads firmware. However, Bluetooth fails at the setup phase with UART communication errors, preventing the adapter from becoming operational.

## What We Tried

### Attempt 1: Top-level bluetooth node (FAILED — wrong placement)
**Date**: 2026-03-16 overnight
**Change**: Added `bluetooth { compatible = "qcom,wcn3991-bt"; ... }` as a child of `soc@0`, before `wifi@18800000`.
**Expected**: BT driver probes via platform device.
**Actual**:
- BT driver did NOT probe — `qcom,wcn3991-bt` is a serdev driver, not a platform driver. It must be a child of a UART node.
- WiFi broke: `ath10k_snoc: failed to enable wcn3990: -22 (EINVAL)` — the misplaced BT node's regulator references (shared with WiFi) caused regulator contention.
- No bluetooth-related dmesg output at all.
**Root cause**: Wrong DTS placement. The upstream has `bluetooth {}` as a child of `&uart1`, not as a SoC-level node.

### Attempt 2: BT node inside serial@884000, UART enabled (FAILED — missing alias)
**Date**: 2026-03-18
**Change**:
- Moved `bluetooth {}` inside `serial@884000`
- Set `status = "okay"` on `serial@884000`
**Expected**: UART probes, serdev creates BT device, driver binds.
**Actual**:
```
qcom_geni_serial 884000.serial: Invalid line -19
```
- `-19` = `ENODEV`. The GENI serial driver calls `of_alias_get_id(node, "serial")` to get a line number, but no aliases node existed in the DTB.
- No BT device created, no driver probe.
**Root cause**: Missing `aliases { serial1 = "/soc@0/geniqup@8c0000/serial@884000"; }` in the DTS. The upstream pdx213 DTS has this at line 32.

### Attempt 3: Added aliases + UART enabled (PARTIAL — firmware loads, setup fails)
**Date**: 2026-03-18
**Change**:
- Added `aliases { serial1 = "/soc@0/geniqup@8c0000/serial@884000"; }`
- UART enabled, BT node inside UART
**Expected**: Full BT probe and operational adapter.
**Actual**:
```
Bluetooth: hci0: QCA SOC Version  :0x40010320
Bluetooth: hci0: QCA ROM Version  :0x00000302
Bluetooth: hci0: QCA Patch Version:0x00000de9
Bluetooth: hci0: QCA controller version 0x03200302
Bluetooth: hci0: QCA Downloading qca/crbtfw32.tlv
Bluetooth: hci0: QCA Downloading qca/crnv32u.bin
Bluetooth: hci0: QCA setup on UART is completed
```
Firmware download succeeds. But then when bluetoothd tries to bring up the adapter:
```
Bluetooth: hci0: setting up wcn399x
Bluetooth: hci0: Frame reassembly failed (-84)
...
Bluetooth: hci0: command 0xfc00 tx timeout
Bluetooth: hci0: Reading QCA version information failed (-110)
Bluetooth: hci0: Retry BT power ON:0
```
- `-84` = `EILSEQ` (illegal byte sequence) — UART receiving garbled data
- `-110` = `ETIMEDOUT` — subsequent commands time out
- Quick Settings shows "Bluetooth On" but GNOME Settings toggle flicks back off
**Root cause theory**: Baud rate mismatch during second-phase setup, or missing UART DMA configuration.

### Attempt 4: Added sleep pinctrl + interrupts-extended + max-speed (FAILED — same error)
**Date**: 2026-03-18
**Change** (cumulative, all applied together):
- Added 4 sleep pinctrl states to TLMM (cts/rts/tx/rx with bias settings matching upstream)
- Replaced `interrupts` with `interrupts-extended` adding GPIO 64 edge-falling wake IRQ
- Added `pinctrl-names = "default", "sleep"` and `pinctrl-1` with sleep state references
- Added `max-speed = <3200000>` (matching FP4)
**Expected**: Stable UART communication during setup phase.
**Actual**: Identical failure — `Frame reassembly failed (-84)` followed by timeouts. The sleep pinctrl and wake interrupt did not affect the probe-time behavior.

## Current Understanding

**Confirmed on hardware:**
- WCN3991 BT chip is present (Product ID 0x0000000a, SOC Version 0x40010320)
- UART1 (`serial@884000`) successfully probes with alias `serial1`
- Firmware download works: `crbtfw32.tlv` (126KB) + `crnv32u.bin` (5.5KB)
- Initial UART setup at default baud rate completes successfully
- The failure occurs during the second phase when bluetoothd sends HCI vendor command `0xfc00`
- WiFi is NOT affected when BT node is correctly placed inside the UART node

**Theory (unconfirmed):**
- The GENI UART may not be correctly switching baud rate to 3Mbaud+ for the second phase
- The UART may need DMA channels configured (other QUP UARTs in the DTS have `dmas` properties, but `serial@884000` does not)
- There may be a Mobian kernel 6.12.68 vs upstream 6.11 driver difference in the QCA setup sequence
- The `Frame reassembly` EILSEQ could indicate the chip is responding at a different baud rate than the host expects

## Artifacts

| File | Description |
|------|-------------|
| `patch-bluetooth.py` | DTS patch script — adds aliases, sleep pinctrl, UART interrupt override, BT node |
| `build/boot-mobian-bt.img` | Latest BT-enabled boot image (2026-03-18, includes all attempt 4 changes) |
| `build/boot-mobian-rmtfs.img` | Known-good baseline WITHOUT bluetooth |
| `build/device-patched-bt.dts` | Full patched DTS source with BT node |

## Phandle Map (for DTS work)

| Supply | Upstream label | Hex phandle | Shared with |
|--------|---------------|-------------|-------------|
| vddio | pm6350_l11 | 0x47 | — |
| vddxo | pm6350_l7 | 0x9b | WiFi vdd-1.8-xo |
| vddrf | pm6150l_l2 | 0x9c | WiFi vdd-1.3-rfa |
| vddch0 | pm6150l_l10 | 0x9d | WiFi vdd-3.3-ch0 |
| swctrl | TLMM GPIO 69 | 0x46 (chip), 0x45 (gpio) | — |
| GIC | intc | 0x01 | — |
| TLMM | tlmm | 0x46 | — |
| Sleep CTS pinctrl | — | 0xa1 | — |
| Sleep RTS pinctrl | — | 0xa2 | — |
| Sleep TX pinctrl | — | 0xa3 | — |
| Sleep RX pinctrl | — | 0xa4 | — |

## Next Steps (priority order)

1. **Check if UART needs DMA**: Compare `serial@884000` with other UART nodes that have `dmas` properties. The I2C nodes at `i2c@888000` etc. have DMA channels — the BT UART may need them too for reliable high-speed transfer.

2. **Compare Mobian 6.12 vs upstream 6.11 QCA driver**: Extract `/lib/modules/6.12-sm6350/kernel/drivers/bluetooth/hci_uart.ko` from the phone, decompile or check version strings. The setup sequence may differ.

3. **Try lower baud rate**: Add `max-speed = <115200>` to force the driver to stay at the initial baud rate. If BT works (slowly), it confirms the baud rate switch is the problem.

4. **Add DMA channels to UART node**: Look at `sm6350.dtsi` for the DMA controller phandles and channel assignments for QUP0 SE1.

5. **Test with upstream sm6350-mainline kernel**: If/when the 6.11→6.12 kernel boots, test BT with that kernel to rule out driver version issues.

## Rollback

Flash the baseline image to restore WiFi-working state without BT:
```bash
fastboot flash boot_a build/boot-mobian-rmtfs.img
```

The BT DTS changes are ONLY in `boot-mobian-bt.img` — the baseline `boot-mobian-rmtfs.img` is unmodified and confirmed working.
