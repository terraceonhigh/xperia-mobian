# Battery & Charging Research — pdx213

**Date**: 2026-03-18 (updated from 2026-03-16)
**Status**: DTS verified working on hardware, kernel module needed next

## Current State

- No `power_supply` device visible in sysfs
- Phone does not charge when running Linux — only charges in fastboot or powered off
- `CONFIG_CHARGER_QCOM_SMB2` is **available but disabled** in the Mobian 6.12.68 kernel config

## Kernel Config Changes Needed

```
# Enable in config-mobian-working:
CONFIG_CHARGER_QCOM_SMB2=m     # was: # CONFIG_CHARGER_QCOM_SMB2 is not set
```

## DTS Status

The current DTB only has **pm6350** PMICs (at `spmi@c440000/pmic@0` and `pmic@1`). There is **no charger PMIC node** in the DTS.

The Sony Xperia 10 III likely uses a **PMI632** (or PM7250B) as the charger/fuel-gauge PMIC. This would need:
1. A `pmic@2` (or similar) node under the SPMI bus with `compatible = "qcom,pmi632"` or `"qcom,pm7250b"`
2. Child nodes for the charger and fuel gauge
3. Regulators for the charger

### What the upstream DTS has

The upstream `sm6350-sony-xperia-lena-pdx213.dts` in the sm6350-mainline kernel may already have these nodes. Need to check:
- https://github.com/sm6350-mainline/linux — look at `arch/arm64/boot/dts/qcom/sm6350-sony-xperia-lena-pdx213.dts`

### FP4 Reference

The Fairphone 4 (also SM6350) uses PM7250B for charging. Its DTS would show the correct node structure.

## Implementation Plan

1. Check upstream sm6350-mainline DTS for charger PMIC nodes
2. Add charger PMIC node to `device-wifi-rproc.dts`
3. Enable `CONFIG_CHARGER_QCOM_SMB2=m` in kernel config
4. Rebuild kernel + boot image
5. Test: `cat /sys/class/power_supply/*/status`

## DTS Test Results (2026-03-18) — VERIFIED ON HARDWARE

Boot image `build/boot-mobian-battery.img` with PM7250B DTS additions:

**Working:**
- PM7250B PMIC registered at SPMI SID 2/3 (`/sys/bus/spmi/devices/0-02`, `0-03`)
- All child devices created: charger@1000, battery@4800, adc@3100, adc-tm@3500, nvram@b100, gpio@c000, temp-alarm@2400
- ADC reads real hardware values:
  - Battery voltage: 4.46V (vbat_sns)
  - USB input: 4.94V @ ~80mA (trickle, no driver)
  - Charger temp: 32.6°C, die temp: 33.5°C
- Charger device registered with `compatible = "qcom,pm7250b-charger"`, waiting for driver module

**Broken:**
- **Touch (s6sy761) probe failed with -5 (EIO)**: I2C read failed. The enable-touch.service also failed. Likely a boot timing issue — the additional PMIC probing may have changed GPIO/I2C initialization order, causing the touch IC to not be powered (GPIO 10) before the kernel tried to auto-probe. Needs investigation.
- **Battery thermal sensor**: `generic-adc-thermal: Thermal zone sensor register failed: -19` — ADC not ready when thermal zone tried to register. Ordering issue, non-critical.

**Artifacts:**
- `build/boot-mobian-battery.img` — DTS-only, no charger module
- `research/dmesg-battery-dts.txt` — full dmesg from this boot
- `patch-battery.py` — the DTS patch script

## Risk

Medium — charger misconfiguration could theoretically cause battery issues, but the SMB2 driver has hardware safety limits. A kernel module that fails to probe is harmless.

Touch regression needs to be resolved before merging battery DTS into the main boot image.

### Attempt 2 (v3 — stripped thermal nodes, 2026-03-18)
Removed `bat_therm_sensor` and `pm7250b-thermal` nodes, changed fuel gauge io-channels to use ADC directly instead of thermal sensor phandle. Same result: `gpi 900000.dma-controller: Error in Transaction` at touch probe time. Touch fails with EIO.

**Conclusion:** The GPI DMA regression is caused by the PM7250B PMIC tree itself, not the thermal sensor nodes. The mere presence of `pmic@2` and `pmic@3` under the SPMI bus is enough to break I2C DMA on QUP1 (`988000.i2c`).

**Theory:** The PM7250B PMIC registers many SPMI interrupt children. The SPMI PMIC ARB interrupt controller may be misconfigured for SID 2/3 in the Mobian kernel's DTB (the base DTB only expected SID 0/1). This could cause spurious interrupts or resource conflicts that affect the GPI DMA engine sharing the same interrupt controller hierarchy.

**Next steps:**
1. Try adding ONLY `pmic@2` with `#address-cells`/`#size-cells` and NO children — see if the bare PMIC registration breaks DMA
2. If bare PMIC is fine, add children one by one to find which one causes the regression
3. Check if the SPMI PMIC ARB node needs `qcom,ee` or `qcom,channel` updates for SID 2/3
4. Compare SPMI ARB configuration between our DTB and the upstream DTB

Full dmesg logs saved: `dmesg-battery-dts.txt` (v1), `dmesg-battery-dts-v2.txt` (v2, with touch disable), `dmesg-battery-dts-v3.txt` (v3, without thermal nodes)
