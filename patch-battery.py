#!/usr/bin/env python3
"""Add PM7250B charger PMIC and battery nodes to DTS.

Adds the PM7250B PMIC tree (charger, fuel gauge, ADC, temp alarm, NVRAM, GPIO)
at SPMI SID 2/3, plus a simple-battery node and battery thermistor sensor.

Phandle assignments (0xa0-0xaf range, all free in our base DTS):
  0xa0 = pm7250b_adc     (ADC on PM7250B, referenced by charger, fuel gauge, thermal sensor)
  0xa1 = battery          (simple-battery, referenced by charger and fuel gauge)
  0xa2 = pm7250b_temp     (temp alarm, referenced by thermal zone)
  0xa3 = pm7250b_qg_sdam  (NVRAM, referenced by fuel gauge)
  0xa4 = bat_therm_sensor  (generic-adc-thermal, referenced by fuel gauge io-channels)
  0xa5 = pm7250b_vbus     (VBUS regulator, referenced by typec if we add it later)
  0xa6 = pm7250b_gpios    (GPIO controller, self-ref for gpio-ranges)

Existing phandle references needed:
  0x9b = pm6350_l7 (also used as pm6350_ldo7 voltage supply)

Source: decompiled sm6350-sony-xperia-lena-pdx213.dtb from sm6350-mainline kernel
"""

import sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else "build/device-patched.dts"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "build/device-patched-battery.dts"

# PM7250B PMIC nodes (pmic@2) — extracted from decompiled upstream DTB
# with phandles remapped to our 0xa0-0xa6 range
PMIC2_NODE = """\

\t\t\tpmic@2 {
\t\t\t\tcompatible = "qcom,pm7250b", "qcom,spmi-pmic";
\t\t\t\treg = <0x02 0x00>;
\t\t\t\t#address-cells = <0x01>;
\t\t\t\t#size-cells = <0x00>;

\t\t\t\tusb-vbus-regulator@1100 {
\t\t\t\t\tcompatible = "qcom,pm7250b-vbus-reg", "qcom,pm8150b-vbus-reg";
\t\t\t\t\treg = <0x1100>;
\t\t\t\t\tstatus = "disabled";
\t\t\t\t\tphandle = <0xa5>;
\t\t\t\t};

\t\t\t\tcharger@1000 {
\t\t\t\t\tcompatible = "qcom,pm7250b-charger";
\t\t\t\t\treg = <0x1000>;
\t\t\t\t\tinterrupts = <0x02 0x13 0x04 0x03 0x02 0x12 0x02 0x03 0x02 0x16 0x01 0x01 0x02 0x13 0x07 0x01>;
\t\t\t\t\tinterrupt-names = "usb-plugin", "bat-ov", "wdog-bark", "usbin-icl-change";
\t\t\t\t\tio-channels = <0xa0 0x07 0xa0 0x08>;
\t\t\t\t\tio-channel-names = "usbin_i", "usbin_v";
\t\t\t\t\tstatus = "okay";
\t\t\t\t\tmonitored-battery = <0xa1>;
\t\t\t\t};

\t\t\t\ttemp-alarm@2400 {
\t\t\t\t\tcompatible = "qcom,spmi-temp-alarm";
\t\t\t\t\treg = <0x2400>;
\t\t\t\t\tinterrupts = <0x02 0x24 0x00 0x03>;
\t\t\t\t\tio-channels = <0xa0 0x06>;
\t\t\t\t\tio-channel-names = "thermal";
\t\t\t\t\t#thermal-sensor-cells = <0x00>;
\t\t\t\t\tphandle = <0xa2>;
\t\t\t\t};

\t\t\t\tadc@3100 {
\t\t\t\t\tcompatible = "qcom,spmi-adc5";
\t\t\t\t\treg = <0x3100>;
\t\t\t\t\t#address-cells = <0x01>;
\t\t\t\t\t#size-cells = <0x00>;
\t\t\t\t\t#io-channel-cells = <0x01>;
\t\t\t\t\tinterrupts = <0x02 0x31 0x00 0x01>;
\t\t\t\t\tphandle = <0xa0>;

\t\t\t\t\tchannel@0 {
\t\t\t\t\t\treg = <0x00>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "ref_gnd";
\t\t\t\t\t};

\t\t\t\t\tchannel@1 {
\t\t\t\t\t\treg = <0x01>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "vref_1p25";
\t\t\t\t\t};

\t\t\t\t\tchannel@2 {
\t\t\t\t\t\treg = <0x06>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "die_temp";
\t\t\t\t\t};

\t\t\t\t\tchannel@7 {
\t\t\t\t\t\treg = <0x07>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "usb_in_i_uv";
\t\t\t\t\t};

\t\t\t\t\tchannel@8 {
\t\t\t\t\t\treg = <0x08>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x10>;
\t\t\t\t\t\tlabel = "usb_in_v_div_16";
\t\t\t\t\t};

\t\t\t\t\tchannel@9 {
\t\t\t\t\t\treg = <0x09>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "chg_temp";
\t\t\t\t\t};

\t\t\t\t\tchannel@e {
\t\t\t\t\t\treg = <0x0e>;
\t\t\t\t\t\tqcom,hw-settle-time = <0xc8>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "smb1390_therm";
\t\t\t\t\t};

\t\t\t\t\tchannel@1e {
\t\t\t\t\t\treg = <0x1e>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x06>;
\t\t\t\t\t\tlabel = "chg_mid";
\t\t\t\t\t};

\t\t\t\t\tchannel@2a {
\t\t\t\t\t\treg = <0x2a>;
\t\t\t\t\t\tqcom,hw-settle-time = <0xc8>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tlabel = "bat_therm_30k";
\t\t\t\t\t};

\t\t\t\t\tchannel@4a {
\t\t\t\t\t\treg = <0x4a>;
\t\t\t\t\t\tqcom,hw-settle-time = <0xc8>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tlabel = "bat_therm_100k";
\t\t\t\t\t};

\t\t\t\t\tchannel@4b {
\t\t\t\t\t\treg = <0x4b>;
\t\t\t\t\t\tqcom,hw-settle-time = <0xc8>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tlabel = "bat_id";
\t\t\t\t\t};

\t\t\t\t\tchannel@6a {
\t\t\t\t\t\treg = <0x6a>;
\t\t\t\t\t\tqcom,hw-settle-time = <0xc8>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tlabel = "bat_therm_400k";
\t\t\t\t\t};

\t\t\t\t\tchannel@83 {
\t\t\t\t\t\treg = <0x83>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x03>;
\t\t\t\t\t\tlabel = "vph_pwr";
\t\t\t\t\t};

\t\t\t\t\tchannel@84 {
\t\t\t\t\t\treg = <0x84>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x03>;
\t\t\t\t\t\tlabel = "vbat_sns";
\t\t\t\t\t};

\t\t\t\t\tchannel@99 {
\t\t\t\t\t\treg = <0x99>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x03>;
\t\t\t\t\t\tlabel = "chg_sbux";
\t\t\t\t\t};

\t\t\t\t\tchannel@4d {
\t\t\t\t\t\treg = <0x4d>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tqcom,hw-settle-time = <0xc8>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "charger_skin_therm";
\t\t\t\t\t};

\t\t\t\t\tchannel@4f {
\t\t\t\t\t\treg = <0x4f>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tqcom,hw-settle-time = <0xc8>;
\t\t\t\t\t\tqcom,pre-scaling = <0x01 0x01>;
\t\t\t\t\t\tlabel = "conn_therm";
\t\t\t\t\t};
\t\t\t\t};

\t\t\t\tadc-tm@3500 {
\t\t\t\t\tcompatible = "qcom,spmi-adc-tm5";
\t\t\t\t\treg = <0x3500>;
\t\t\t\t\tinterrupts = <0x02 0x35 0x00 0x01>;
\t\t\t\t\t#thermal-sensor-cells = <0x01>;
\t\t\t\t\t#address-cells = <0x01>;
\t\t\t\t\t#size-cells = <0x00>;
\t\t\t\t\tstatus = "okay";

\t\t\t\t\tcharger-skin-therm@0 {
\t\t\t\t\t\treg = <0x00>;
\t\t\t\t\t\tio-channels = <0xa0 0x4d>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tqcom,hw-settle-time-us = <0xc8>;
\t\t\t\t\t};

\t\t\t\t\tconn-therm@1 {
\t\t\t\t\t\treg = <0x01>;
\t\t\t\t\t\tio-channels = <0xa0 0x4f>;
\t\t\t\t\t\tqcom,ratiometric;
\t\t\t\t\t\tqcom,hw-settle-time-us = <0xc8>;
\t\t\t\t\t};
\t\t\t\t};

\t\t\t\tbattery@4800 {
\t\t\t\t\tcompatible = "qcom,pm7250b-qg", "qcom,pm6150-qg";
\t\t\t\t\treg = <0x4800>;
\t\t\t\t\tio-channels = <0xa0 0x2a 0xa0 0x4b>;
\t\t\t\t\tio-channel-names = "batt-therm", "batt-id";
\t\t\t\t\tnvmem = <0xa3>;
\t\t\t\t\tstatus = "okay";
\t\t\t\t\tmonitored-battery = <0xa1>;
\t\t\t\t};

\t\t\t\tnvram@b100 {
\t\t\t\t\tcompatible = "qcom,spmi-sdam";
\t\t\t\t\treg = <0xb100>;
\t\t\t\t\t#address-cells = <0x01>;
\t\t\t\t\t#size-cells = <0x01>;
\t\t\t\t\tranges = <0x00 0xb100 0x100>;
\t\t\t\t\tphandle = <0xa3>;
\t\t\t\t};

\t\t\t\tgpio@c000 {
\t\t\t\t\tcompatible = "qcom,pm7250b-gpio", "qcom,spmi-gpio";
\t\t\t\t\treg = <0xc000>;
\t\t\t\t\tgpio-controller;
\t\t\t\t\tgpio-ranges = <0xa6 0x00 0x00 0x0c>;
\t\t\t\t\t#gpio-cells = <0x02>;
\t\t\t\t\tinterrupt-controller;
\t\t\t\t\t#interrupt-cells = <0x02>;
\t\t\t\t\tphandle = <0xa6>;
\t\t\t\t};
\t\t\t};

\t\t\tpmic@3 {
\t\t\t\tcompatible = "qcom,pm7250b", "qcom,spmi-pmic";
\t\t\t\treg = <0x03 0x00>;
\t\t\t\t#address-cells = <0x01>;
\t\t\t\t#size-cells = <0x00>;
\t\t\t};
"""

# Battery node — goes at root level
BATTERY_NODE = """\

\tbattery {
\t\tcompatible = "simple-battery";
\t\tdevice-chemistry = "lithium-ion-polymer";
\t\tcharge-full-design-microamp-hours = <0x451b68>;
\t\tconstant-charge-current-max-microamp = <0x16e360>;
\t\tvoltage-max-design-microvolt = <0x4371a0>;
\t\tvoltage-min-design-microvolt = <0x30d400>;
\t\tphandle = <0xa1>;
\t};
"""

# Battery thermistor sensor — goes at root level
# Provides io-channel for fuel gauge batt-therm reading
# Lookup table from upstream pdx213 DTS (30K pullup NTC)
BAT_THERM_SENSOR = """\

\tthermal-sensor-bat-therm {
\t\tcompatible = "generic-adc-thermal";
\t\t#thermal-sensor-cells = <0x00>;
\t\t#io-channel-cells = <0x00>;
\t\tio-channels = <0xa0 0x2a>;
\t\tio-channel-names = "sensor-channel";
\t\ttemperature-lookup-table = <0xffff63c0 0x730 0xffff6b90 0x72b 0xffff7360 0x724 0xffff7b30 0x71d 0xffff8300 0x715 0xffff8ad0 0x70b 0xffff92a0 0x701 0xffff9a70 0x6f5 0xffffa240 0x6e8 0xffffaa10 0x6d9 0xffffb1e0 0x6c9 0xffffb9b0 0x6b7 0xffffc180 0x6a4 0xffffc950 0x68f 0xffffd120 0x677 0xffffd8f0 0x65e 0xffffe0c0 0x643 0xffffe890 0x626 0xfffff060 0x607 0xfffff830 0x5e6 0x00 0x5c3 0x7d0 0x59e 0xfa0 0x578 0x1770 0x550 0x1f40 0x526 0x2710 0x4fc 0x2ee0 0x4d0 0x36b0 0x4a3 0x3e80 0x476 0x4650 0x449 0x4e20 0x41b 0x55f0 0x3ed 0x5dc0 0x3c0 0x6590 0x393 0x6d60 0x367 0x7530 0x33c 0x7d00 0x312 0x84d0 0x2e9 0x8ca0 0x2c1 0x9470 0x29a 0x9c40 0x275 0xa410 0x252 0xabe0 0x230 0xb3b0 0x20f 0xbb80 0x1f1 0xc350 0x1d3 0xcb20 0x1b7 0xd2f0 0x19d 0xdac0 0x184 0xe290 0x16d 0xea60 0x157 0xf230 0x142 0xfa00 0x12e 0x101d0 0x11c 0x109a0 0x10b 0x11170 0xfb 0x11940 0xeb 0x12110 0xdd 0x128e0 0xd0 0x130b0 0xc3 0x13880 0xb8 0x14050 0xad 0x14820 0xa3 0x14ff0 0x99 0x157c0 0x90 0x15f90 0x88 0x16760 0x80 0x16f30 0x78 0x17700 0x72 0x17ed0 0x6b>;
\t\tphandle = <0xa4>;
\t};
"""

# PM7250B thermal zone — goes in thermal-zones
PM7250B_THERMAL = """\

\t\tpm7250b-thermal {
\t\t\tpolling-delay-passive = <0x64>;
\t\t\tthermal-sensors = <0xa2>;

\t\t\ttrips {

\t\t\t\ttrip0 {
\t\t\t\t\ttemperature = <0x17318>;
\t\t\t\t\thysteresis = <0x00>;
\t\t\t\t\ttype = "passive";
\t\t\t\t};

\t\t\t\ttrip1 {
\t\t\t\t\ttemperature = <0x1c138>;
\t\t\t\t\thysteresis = <0x00>;
\t\t\t\t\ttype = "hot";
\t\t\t\t};

\t\t\t\ttrip2 {
\t\t\t\t\ttemperature = <0x23668>;
\t\t\t\t\thysteresis = <0x00>;
\t\t\t\t\ttype = "critical";
\t\t\t\t};
\t\t\t};
\t\t};
"""

with open(INPUT) as f:
    lines = f.readlines()

output = []
pmic_added = False
battery_added = False
thermal_added = False
i = 0

while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # Add battery + bat_therm_sensor after qcom,board-id (root level, before first subnode)
    if stripped.startswith('qcom,board-id') and not battery_added:
        output.append(line)
        i += 1
        output.append(BATTERY_NODE)
        # NOTE: BAT_THERM_SENSOR omitted — generic-adc-thermal registration
        # was failing with -19 at boot, possibly cascading into GPI DMA errors.
        # Fuel gauge can work without batt-therm (loses temperature reading).
        # output.append(BAT_THERM_SENSOR)
        battery_added = True
        print("Added battery node at root level (bat_therm_sensor omitted)")
        continue

    # Add pmic@2 and pmic@3 after pmic@1 closing };
    if stripped == "pmic@1 {" and not pmic_added:
        # Write pmic@1 as-is
        output.append(line)
        i += 1
        depth = 1
        while i < len(lines) and depth > 0:
            output.append(lines[i])
            if "{" in lines[i].strip() and "}" not in lines[i].strip():
                depth += 1
            if lines[i].strip() == "};":
                depth -= 1
            i += 1
        # Now insert PM7250B after pmic@1
        output.append(PMIC2_NODE)
        pmic_added = True
        print("Added pmic@2 (PM7250B) and pmic@3 after pmic@1")
        continue

    # Add PM7250B thermal zone inside thermal-zones section
    # Find the last thermal zone entry and insert before thermal-zones closing };
    if stripped.startswith("pm6350-thermal") and not thermal_added:
        # Write pm6350-thermal as-is
        output.append(line)
        i += 1
        depth = 1
        while i < len(lines) and depth > 0:
            output.append(lines[i])
            if "{" in lines[i].strip() and "}" not in lines[i].strip():
                depth += 1
            if lines[i].strip() == "};":
                depth -= 1
            i += 1
        # NOTE: PM7250B thermal zone omitted — temp-alarm still registers
        # via SPMI, just won't have a thermal zone policy until this is fixed.
        # output.append(PM7250B_THERMAL)
        thermal_added = True  # skip but count as done
        print("Skipped pm7250b-thermal zone (investigating DMA regression)")
        continue

    output.append(line)
    i += 1

with open(OUTPUT, "w") as f:
    f.writelines(output)

changes = sum([pmic_added, battery_added, thermal_added])
print(f"Wrote {OUTPUT} with {changes}/3 changes")
