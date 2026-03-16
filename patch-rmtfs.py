#!/usr/bin/env python3
"""Add qcom,rmtfs-mem node, firmware-name properties, and enable UFS in DTS.

Changes:
1. Add rmtfs-mem reserved memory node at 0x9b000000 (2MB, right after modem PIL)
2. Add firmware-name properties to ADSP, MPSS, CDSP remoteproc nodes
3. Enable UFS controller and UFS PHY (needed for modemst1/modemst2 partitions)
"""

import sys
INPUT = sys.argv[1] if len(sys.argv) > 1 else "/home/terrace/tmp-dtb/device-wifi-rproc.dts"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "/home/terrace/tmp-dtb/device-wifi-rproc-rmtfs.dts"

with open(INPUT) as f:
    lines = f.readlines()

output = []
changes = 0

# State tracking
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # Insert rmtfs-mem node before the closing }; of reserved-memory section
    # The last node in reserved-memory is memory@ffd00000, ending with };
    # We insert after that node but before the section close
    if stripped == "memory@ffd00000 {":
        # Write memory@ffd00000 node as-is
        output.append(line)
        i += 1
        while i < len(lines):
            output.append(lines[i])
            if lines[i].strip() == "};":
                break
            i += 1
        i += 1
        # Now insert rmtfs-mem node before the reserved-memory closing };
        output.append("\n")
        output.append("\t\trmtfs@9b000000 {\n")
        output.append('\t\t\tcompatible = "qcom,rmtfs-mem";\n')
        output.append("\t\t\treg = <0x00 0x9b000000 0x00 0x300000>;\n")
        output.append("\t\t\tno-map;\n")
        output.append("\t\t\tqcom,client-id = <0x01>;\n")
        output.append("\t\t\tqcom,vmid = <0x0f>;\n")  # QCOM_SCM_VMID_MSS_MSA = 15
        output.append("\t\t\tphandle = <0x9f>;\n")
        output.append("\t\t};\n")
        changes += 1
        print("Added rmtfs-mem node at 0x9b000000")
        continue

    # Add firmware-name to ADSP remoteproc (after memory-region line)
    if "qcom,sm6350-adsp-pas" in stripped:
        output.append(line)
        i += 1
        while i < len(lines):
            output.append(lines[i])
            if "memory-region" in lines[i] and "0x56" in lines[i]:
                # Insert firmware-name after memory-region
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                output.append(indent + 'firmware-name = "qcom/sm6350/adsp.mdt";\n')
                changes += 1
                print("Added firmware-name to ADSP")
            i += 1
            if lines[i-1].strip().startswith("status ="):
                break
        continue

    # Add firmware-name to MPSS remoteproc
    if "qcom,sm6350-mpss-pas" in stripped:
        output.append(line)
        i += 1
        while i < len(lines):
            output.append(lines[i])
            if "memory-region" in lines[i] and "0x61" in lines[i]:
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                output.append(indent + 'firmware-name = "qcom/sm6350/modem.mdt";\n')
                changes += 1
                print("Added firmware-name to MPSS")
            i += 1
            if lines[i-1].strip().startswith("status ="):
                break
        continue

    # Add firmware-name to CDSP remoteproc
    if "qcom,sm6350-cdsp-pas" in stripped:
        output.append(line)
        i += 1
        while i < len(lines):
            output.append(lines[i])
            if "memory-region" in lines[i] and "0x64" in lines[i]:
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                output.append(indent + 'firmware-name = "qcom/sm6350/cdsp.mdt";\n')
                changes += 1
                print("Added firmware-name to CDSP")
            i += 1
            if lines[i-1].strip().startswith("status ="):
                break
        continue

    # Enable UFS controller: ufs@1d84000
    if '"qcom,sm6350-ufshc"' in stripped:
        output.append(line)
        i += 1
        while i < len(lines):
            if 'status = "disabled"' in lines[i]:
                output.append(lines[i].replace("disabled", "okay"))
                changes += 1
                print("Enabled UFS controller")
                i += 1
                break
            output.append(lines[i])
            i += 1
        continue

    # Enable UFS PHY: phy@1d87000
    if '"qcom,sm6350-qmp-ufs-phy"' in stripped:
        output.append(line)
        i += 1
        while i < len(lines):
            if 'status = "disabled"' in lines[i]:
                output.append(lines[i].replace("disabled", "okay"))
                changes += 1
                print("Enabled UFS PHY")
                i += 1
                break
            output.append(lines[i])
            i += 1
        continue

    output.append(line)
    i += 1

with open(OUTPUT, "w") as f:
    f.writelines(output)

print("Wrote %s with %d changes" % (OUTPUT, changes))
