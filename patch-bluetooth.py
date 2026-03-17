#!/usr/bin/env python3
"""Add Bluetooth (WCN3991) node to DTS.

Adds a top-level bluetooth node with qcom,wcn3991-bt compatible,
matching the upstream sm6350-sony-xperia-lena-pdx213.dts.

Supply phandles (mapped from our compiled DTB):
  vddio   = pm6350_l11  = 0x47
  vddxo   = pm6350_l7   = 0x9b  (shared with WiFi vdd-1.8-xo)
  vddrf   = pm6150l_l2  = 0x9c  (shared with WiFi vdd-1.3-rfa)
  vddch0  = pm6150l_l10 = 0x9d  (shared with WiFi vdd-3.3-ch0)
  swctrl  = TLMM GPIO 69, phandle 0x46

Firmware: /lib/firmware/qca/crnv32u.bin (present on rootfs)

Reference: sm6350-kernel/arch/arm64/boot/dts/qcom/sm6350-sony-xperia-lena-pdx213.dts
"""

import sys
INPUT = sys.argv[1] if len(sys.argv) > 1 else "build/device-patched.dts"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "build/device-patched-bt.dts"

with open(INPUT) as f:
    lines = f.readlines()

# Find the wifi@18800000 node — we'll insert the bluetooth node just before it
# (as a sibling in the soc bus, matching upstream ordering)
output = []
inserted = False

BT_NODE = """\
\t\tbluetooth {
\t\t\tcompatible = "qcom,wcn3991-bt";
\t\t\tvddio-supply = <0x47>;
\t\t\tvddxo-supply = <0x9b>;
\t\t\tvddrf-supply = <0x9c>;
\t\t\tvddch0-supply = <0x9d>;
\t\t\tswctrl-gpios = <0x46 0x45 0x00>;
\t\t\tfirmware-name = "crnv32u.bin";
\t\t};

"""

for i, line in enumerate(lines):
    # Insert BT node just before the WiFi node
    if "wifi@18800000" in line and not inserted:
        output.append(BT_NODE)
        inserted = True
        print("Inserted bluetooth node before wifi@18800000")

    output.append(line)

if not inserted:
    print("WARNING: Could not find wifi@18800000 — inserting at end of soc")
    # Fallback: insert before the last closing };
    for i in range(len(output) - 1, -1, -1):
        if output[i].strip() == "};":
            output.insert(i, BT_NODE)
            inserted = True
            print("Inserted bluetooth node before final };")
            break

with open(OUTPUT, "w") as f:
    f.writelines(output)

print(f"Wrote {OUTPUT} ({'with' if inserted else 'WITHOUT'} bluetooth node)")
