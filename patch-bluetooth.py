#!/usr/bin/env python3
"""Add Bluetooth (WCN3991) node to DTS as a child of UART1 (serial@884000).

Changes:
1. Adds aliases node with serial1 -> UART path (needed for line number assignment)
2. Adds UART1 sleep pinctrl states to TLMM (needed for stable BT communication)
3. Enables UART1 (status = "okay")
4. Replaces UART1 interrupt with interrupts-extended (adds GPIO 64 wake IRQ)
5. Adds sleep pinctrl reference to UART1
6. Adds bluetooth child node inside UART1

Supply phandles (mapped from our compiled DTB):
  vddio   = pm6350_l11  = 0x47
  vddxo   = pm6350_l7   = 0x9b  (shared with WiFi vdd-1.8-xo)
  vddrf   = pm6150l_l2  = 0x9c  (shared with WiFi vdd-1.3-rfa)
  vddch0  = pm6150l_l10 = 0x9d  (shared with WiFi vdd-3.3-ch0)
  swctrl  = TLMM GPIO 69, phandle 0x46
  GIC     = 0x01
  TLMM    = 0x46

New phandles for sleep pinctrl:
  0xa1 = qup-uart1-sleep-cts
  0xa2 = qup-uart1-sleep-rts
  0xa3 = qup-uart1-sleep-tx
  0xa4 = qup-uart1-sleep-rx

Reference: sm6350-kernel/arch/arm64/boot/dts/qcom/sm6350-sony-xperia-lena-pdx213.dts
"""

import sys
INPUT = sys.argv[1] if len(sys.argv) > 1 else "build/device-patched.dts"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "build/device-patched-bt.dts"

UART_PATH = "/soc@0/geniqup@8c0000/serial@884000"

# Sleep pinctrl nodes to add inside the TLMM pinctrl section
SLEEP_PINCTRL = """
\t\t\tqup-uart1-sleep-cts-state {
\t\t\t\tpins = "gpio61";
\t\t\t\tfunction = "gpio";
\t\t\t\tbias-bus-hold;
\t\t\t\tphandle = <0xa1>;
\t\t\t};

\t\t\tqup-uart1-sleep-rts-state {
\t\t\t\tpins = "gpio62";
\t\t\t\tfunction = "gpio";
\t\t\t\tbias-pull-down;
\t\t\t\tphandle = <0xa2>;
\t\t\t};

\t\t\tqup-uart1-sleep-tx-state {
\t\t\t\tpins = "gpio63";
\t\t\t\tfunction = "gpio";
\t\t\t\tbias-pull-up;
\t\t\t\tphandle = <0xa3>;
\t\t\t};

\t\t\tqup-uart1-sleep-rx-state {
\t\t\t\tpins = "gpio64";
\t\t\t\tfunction = "gpio";
\t\t\t\tbias-pull-up;
\t\t\t\tphandle = <0xa4>;
\t\t\t};
"""

with open(INPUT) as f:
    lines = f.readlines()

output = []
bt_inserted = False
aliases_added = False
sleep_pinctrl_added = False
i = 0

while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # 1. Add aliases node after qcom,board-id
    if stripped.startswith('qcom,board-id') and not aliases_added:
        output.append(line)
        i += 1
        output.append("\n")
        output.append("\taliases {\n")
        output.append('\t\tserial1 = "' + UART_PATH + '";\n')
        output.append("\t};\n")
        aliases_added = True
        print("Added aliases node: serial1 -> " + UART_PATH)
        continue

    # 2. Add sleep pinctrl states inside TLMM (before the ts-active-state node)
    if "ts-active-state" in stripped and not sleep_pinctrl_added:
        output.append(SLEEP_PINCTRL)
        sleep_pinctrl_added = True
        print("Added UART1 sleep pinctrl states to TLMM")
        output.append(line)
        i += 1
        continue

    # 3. Modify serial@884000: enable, add interrupts-extended, sleep pinctrl, BT child
    if "serial@884000 {" in stripped and not bt_inserted:
        output.append(line)
        i += 1

        depth = 1
        status_fixed = False
        interrupts_fixed = False
        pinctrl_fixed = False
        while i < len(lines) and depth > 0:
            uline = lines[i]
            ustripped = uline.strip()

            if "{" in ustripped and "}" not in ustripped:
                depth += 1
            if ustripped == "};":
                depth -= 1

            # Enable UART
            if 'status = "disabled"' in uline and not status_fixed:
                output.append(uline.replace("disabled", "okay"))
                status_fixed = True
                print("Enabled serial@884000 (UART1)")
                i += 1
                continue

            # Replace interrupts with interrupts-extended
            if ustripped.startswith("interrupts = ") and not interrupts_fixed:
                indent = uline[:len(uline) - len(uline.lstrip())]
                # interrupts-extended: GIC SPI 602 LEVEL_HIGH, TLMM GPIO 64 EDGE_FALLING
                output.append(indent + "interrupts-extended = <0x01 0x00 0x25a 0x04 0x46 0x40 0x02>;\n")
                interrupts_fixed = True
                print("Replaced interrupts with interrupts-extended (added GPIO 64 wake)")
                i += 1
                continue

            # Add sleep pinctrl after pinctrl-0
            if ustripped.startswith("pinctrl-0 =") and not pinctrl_fixed:
                output.append(uline)
                indent = uline[:len(uline) - len(uline.lstrip())]
                # Override pinctrl-names to include "sleep"
                # Find and replace the pinctrl-names line we already passed
                for j in range(len(output) - 1, max(len(output) - 5, 0), -1):
                    if 'pinctrl-names' in output[j]:
                        output[j] = indent + 'pinctrl-names = "default", "sleep";\n'
                        break
                output.append(indent + "pinctrl-1 = <0xa1 0xa2 0xa3 0xa4>;\n")
                pinctrl_fixed = True
                print("Added sleep pinctrl to UART1")
                i += 1
                continue

            # At closing }; of UART node, insert BT child
            if depth == 0 and ustripped == "};":
                output.append("\n")
                output.append("\t\t\t\tbluetooth {\n")
                output.append('\t\t\t\t\tcompatible = "qcom,wcn3991-bt";\n')
                output.append("\t\t\t\t\tvddio-supply = <0x47>;\n")
                output.append("\t\t\t\t\tvddxo-supply = <0x9b>;\n")
                output.append("\t\t\t\t\tvddrf-supply = <0x9c>;\n")
                output.append("\t\t\t\t\tvddch0-supply = <0x9d>;\n")
                output.append("\t\t\t\t\tswctrl-gpios = <0x46 0x45 0x00>;\n")
                output.append('\t\t\t\t\tmax-speed = <0x30d400>;\n')  # 3200000
                output.append('\t\t\t\t\tfirmware-name = "crnv32u.bin";\n')
                output.append("\t\t\t\t};\n")
                bt_inserted = True
                print("Inserted bluetooth node inside serial@884000")

            output.append(uline)
            i += 1
        continue

    output.append(line)
    i += 1

changes = sum([bt_inserted, aliases_added, sleep_pinctrl_added])
print(f"Wrote {OUTPUT} with {changes}/3 changes")

with open(OUTPUT, "w") as f:
    f.writelines(output)
