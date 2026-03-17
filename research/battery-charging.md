# Battery & Charging Research — pdx213

**Date**: 2026-03-16
**Status**: Research complete, implementation requires kernel rebuild

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

## Risk

Medium — charger misconfiguration could theoretically cause battery issues, but the SMB2 driver has hardware safety limits. A kernel module that fails to probe is harmless.
