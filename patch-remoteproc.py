#!/usr/bin/env python3
"""Enable MPSS, ADSP, and CDSP remoteproc nodes in device DTS."""

with open("/home/terrace/tmp-dtb/device-wifi.dts") as f:
    lines = f.readlines()

# Track which remoteproc node we're in
current_rproc = None
changes = 0
output = []

for i, line in enumerate(lines):
    stripped = line.strip()

    # Detect remoteproc nodes by compatible
    if "qcom,sm6350-adsp-pas" in stripped:
        current_rproc = "adsp"
    elif "qcom,sm6350-mpss-pas" in stripped:
        current_rproc = "mpss"
    elif "qcom,sm6350-cdsp-pas" in stripped:
        current_rproc = "cdsp"

    # Enable the remoteproc nodes
    if current_rproc and 'status = "disabled"' in stripped:
        output.append(line.replace("disabled", "okay"))
        print("Enabled %s remoteproc" % current_rproc)
        changes += 1
        current_rproc = None
        continue

    output.append(line)

with open("/home/terrace/tmp-dtb/device-wifi-rproc.dts", "w") as f:
    f.writelines(output)

print("Wrote device-wifi-rproc.dts with %d changes" % changes)
