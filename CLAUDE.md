# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a workspace for porting postmarketOS (pmOS) to the Sony Xperia 10 III (codename: pdx213, SoC: Qualcomm SM6350). The main artifact is a set of pmaports packages (device, firmware, kernel) being developed against MR !5472.

## Repository Layout

- `pmaports/` — Clone of [gitlab.com/postmarketOS/pmaports](https://gitlab.com/postmarketOS/pmaports), on branch `mr-5472`. This is the Alpine-based package tree for postmarketOS.
  - `device/` — Device packages organized by maturity: `main/` (stable), `community/` (maintained), `testing/` (WIP/new devices), `archived/`
  - `main/` — Core pmOS packages (initramfs, UIs, utilities, bootloaders)
  - `temp/` — Packages forked from Alpine with pmOS-specific patches
  - `modem/` — Modem/telephony packages (pd-mapper, qrtr, msm-modem, etc.)
  - `cross/` — Cross-compilation toolchain packages
- `.venv/` — Python venv with pmbootstrap installed locally (read-only reference; builds happen on Bazzite)

## Build Infrastructure

Builds run on the **Bazzite server** (`192.168.1.91`), not this Mac. This Mac holds pmaports for code inspection/editing only.

Key commands (run on Bazzite at `~/Lab/xperia-pmos/`):
```bash
.venv/bin/pmbootstrap init                    # configure device/UI/channel
.venv/bin/pmbootstrap build device-sony-pdx213  # build device package
.venv/bin/pmbootstrap install                 # build full rootfs image
.venv/bin/pmbootstrap export                  # export boot.img and rootfs
.venv/bin/pmbootstrap kconfig check           # validate kernel config against kconfigcheck.toml
.venv/bin/pmbootstrap log                     # tail build logs (can hang — use Ctrl-C)
.venv/bin/pmbootstrap zap                     # clean work directory
.venv/bin/pmbootstrap status                  # show current config
```

## pmaports Package Format

Each package is a directory containing an `APKBUILD` (Alpine package build script). Device packages additionally include:
- `deviceinfo` — key-value file defining hardware properties, flash method, boot offsets, DTB path
- `modules-initfs` — kernel modules to include in initramfs

Refer to the Fairphone 4 (`device/community/device-fairphone-fp4/`) as the primary reference — it uses the same SM6350 SoC and `linux-postmarketos-qcom-sm6350` kernel.

## Commit Style

Follow `COMMITSTYLE.md`. Key rules:
- Device packages: `manufacturer-codename: description` (e.g., `sony-pdx213: new device`)
- No directory prefix for device packages (unlike Alpine convention)
- New device + kernel + firmware = single commit
- Forked Alpine packages: `temp/package-name: fork from Alpine`

## Kernel Config Checks

`kconfigcheck.toml` defines required kernel config options by category (default, waydroid, containers, nftables, etc.). Device APKBUILDs declare which categories to check via `options="pmb:kconfigcheck-community"`. Run `pmbootstrap kconfig check` to validate.

## Reference Port

The Fairphone 4 (SM6350) is the closest working reference. Its `device-fairphone-fp4` package shows the expected dependencies for this SoC: hexagonrpcd, pd-mapper, tqftpserv, qbootctl, mesa-vulkan-freedreno, msm-modem, firmware packages, etc.

## Unattended Build Guardrails (--dangerously-skip-permissions)

These rules apply when running with `--dangerously-skip-permissions`:

### Allowed
- **SSH to Bazzite** (`terrace@192.168.1.91`): container management only (podman build/run/exec/cp/rm)
- **SSH to phone** (`mobian@<phone-ip>`): `dd` to `boot_a` or `boot_b`, `reboot`, read-only checks (dmesg, sysfs, systemctl status)
- **This Mac**: read any file, write only to `/Users/terrace/Labs/Xperia/` (project dir) and memory files
- **scp** between machines for build artifacts (boot images, DTBs)

### Forbidden
- Do NOT `rm -rf`, `mkfs`, or wipe any partition other than `boot_a`/`boot_b`
- Do NOT push to any git remote or create PRs/issues without explicit user approval
- Do NOT modify Bazzite host filesystem outside of `~/Lab/` and podman containers
- Do NOT install packages on Bazzite host (use containers)
- Do NOT touch `/etc`, systemd units, or network config on any machine
- Do NOT run `fastboot` commands (no USB access from Mac)
- Do NOT delete or overwrite the phone's rootfs partition (`mmcblk0`)
- Do NOT send messages to external services (Slack, email, GitHub comments)
