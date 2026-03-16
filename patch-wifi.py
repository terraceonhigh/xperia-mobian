#!/usr/bin/env python3
"""Add WiFi regulator supplies and enable WiFi in device DTS."""

with open("/home/terrace/tmp-dtb/device-mod2.dts") as f:
    lines = f.readlines()

# Track which regulators-X block we are in
in_pm6350 = False  # regulators-0 (pmic-id "a")
in_pm6150l = False  # regulators-1 (pmic-id "e")
current_ldo = None
insertions = {}  # line_index -> text to insert after

for i, line in enumerate(lines):
    stripped = line.strip()
    if "regulators-0 {" in stripped:
        in_pm6350 = True
        in_pm6150l = False
    elif "regulators-1 {" in stripped:
        in_pm6150l = True
        in_pm6350 = False

    # Track current ldo/regulator node
    if stripped.endswith("{") and not stripped.startswith("regulators"):
        node_name = stripped.split()[0]
        if node_name.startswith("ldo"):
            current_ldo = node_name  # e.g. "ldo4"
        else:
            current_ldo = None  # reset for non-ldo nodes like "bob"

    # Add phandles after regulator-initial-mode for target LDOs
    if "regulator-initial-mode" in stripped:
        tabs = "\t\t\t\t\t"
        if in_pm6350 and current_ldo == "ldo4":
            insertions[i] = tabs + "phandle = <0x9a>;\n"
        elif in_pm6350 and current_ldo == "ldo7":
            insertions[i] = tabs + "phandle = <0x9b>;\n"
        elif in_pm6150l and current_ldo == "ldo2":
            insertions[i] = tabs + "phandle = <0x9c>;\n"
        elif in_pm6150l and current_ldo == "ldo10":
            insertions[i] = tabs + "phandle = <0x9d>;\n"
        elif in_pm6150l and current_ldo == "ldo11":
            insertions[i] = tabs + "phandle = <0x9e>;\n"

# Now modify the WiFi node: add supplies and change status
output = []
in_wifi = False
wifi_done = False

for i, line in enumerate(lines):
    stripped = line.strip()

    if "wifi@18800000 {" in stripped:
        in_wifi = True

    if in_wifi and not wifi_done and 'status = "disabled"' in stripped:
        # Replace disabled with okay, add supply properties before status
        tabs = "\t\t\t"
        output.append(tabs + "vdd-0.8-cx-mx-supply = <0x9a>;\n")
        output.append(tabs + "vdd-1.8-xo-supply = <0x9b>;\n")
        output.append(tabs + "vdd-1.3-rfa-supply = <0x9c>;\n")
        output.append(tabs + "vdd-3.3-ch0-supply = <0x9d>;\n")
        output.append(tabs + "vdd-3.3-ch1-supply = <0x9e>;\n")
        output.append(line.replace("disabled", "okay"))
        wifi_done = True
        in_wifi = False
        # Also add insertion if any
        if i in insertions:
            output.append(insertions[i])
        continue

    output.append(line)
    if i in insertions:
        output.append(insertions[i])

with open("/home/terrace/tmp-dtb/device-wifi.dts", "w") as f:
    f.writelines(output)

print("Wrote device-wifi.dts")
print("Added %d phandles, modified WiFi node" % len(insertions))
