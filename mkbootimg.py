#!/usr/bin/env python3
"""Minimal Android boot image builder (header version 0 and 2).

Usage:
    # v0 (legacy Mobian style):
    python3 mkbootimg.py --kernel zImage --ramdisk initrd.img \
        --base 0x10000000 --pagesize 4096 --cmdline "..." -o boot.img

    # v2 (pmOS style, with separate DTB):
    python3 mkbootimg.py --kernel Image.gz --ramdisk initrd.img --dtb device.dtb \
        --base 0x0 --pagesize 4096 --header_version 2 --cmdline "..." -o boot.img
"""
import argparse
import struct

BOOT_MAGIC = b"ANDROID!"

def pad_to_page(data, pagesize):
    pad = pagesize - (len(data) % pagesize)
    if pad == pagesize:
        return data
    return data + b"\x00" * pad

def main():
    p = argparse.ArgumentParser(description="Build Android boot image (v0/v2)")
    p.add_argument("--kernel", required=True)
    p.add_argument("--ramdisk", required=True)
    p.add_argument("--dtb", help="DTB file (required for header_version >= 2)")
    p.add_argument("--base", default="0x00000000")
    p.add_argument("--pagesize", type=int, default=4096)
    p.add_argument("--cmdline", default="")
    p.add_argument("--header_version", type=int, default=0)
    p.add_argument("--kernel_offset", default="0x00008000")
    p.add_argument("--ramdisk_offset", default="0x01000000")
    p.add_argument("--second_offset", default="0x00000000")
    p.add_argument("--tags_offset", default="0x00000100")
    p.add_argument("--dtb_offset", default="0x01f00000")
    p.add_argument("-o", "--output", required=True)
    args = p.parse_args()

    base = int(args.base, 0)
    kernel_addr = base + int(args.kernel_offset, 0)
    ramdisk_addr = base + int(args.ramdisk_offset, 0)
    second_addr = base + int(args.second_offset, 0)
    tags_addr = base + int(args.tags_offset, 0)
    dtb_addr = base + int(args.dtb_offset, 0)

    with open(args.kernel, "rb") as f:
        kernel = f.read()
    with open(args.ramdisk, "rb") as f:
        ramdisk = f.read()

    dtb = b""
    if args.dtb:
        with open(args.dtb, "rb") as f:
            dtb = f.read()
    elif args.header_version >= 2:
        p.error("--dtb is required for header_version >= 2")

    cmdline = args.cmdline.encode("utf-8")
    if len(cmdline) > 512:
        cmdline_main = cmdline[:512]
        cmdline_extra = cmdline[512:1536]
    else:
        cmdline_main = cmdline
        cmdline_extra = b""

    # v0 header: 1632 bytes
    hdr = bytearray(struct.pack(
        "<8s"     # magic
        "I"       # kernel_size
        "I"       # kernel_addr
        "I"       # ramdisk_size
        "I"       # ramdisk_addr
        "I"       # second_size
        "I"       # second_addr
        "I"       # tags_addr
        "I"       # page_size
        "I"       # header_version
        "I"       # os_version
        "16s"     # name
        "512s"    # cmdline
        "32s"     # id
        "1024s",  # extra_cmdline
        BOOT_MAGIC,
        len(kernel), kernel_addr,
        len(ramdisk), ramdisk_addr,
        0, second_addr,
        tags_addr,
        args.pagesize,
        args.header_version,
        0,
        b"",
        cmdline_main,
        b"\x00" * 32,
        cmdline_extra,
    ))
    # hdr is now 1632 bytes

    if args.header_version >= 1:
        # v1 appends: recovery_dtbo_size(4) + recovery_dtbo_offset(8) + header_size(4)
        hdr += struct.pack("<I", 0)    # recovery_dtbo_size
        hdr += struct.pack("<Q", 0)    # recovery_dtbo_offset
        hdr += struct.pack("<I", 0)    # header_size (filled below)

    if args.header_version >= 2:
        # v2 appends: dtb_size(4) + dtb_addr(8)
        hdr += struct.pack("<I", len(dtb))
        hdr += struct.pack("<Q", dtb_addr)

    # Patch header_size field (at offset 1632 + 4 + 8 = 1644)
    if args.header_version >= 1:
        struct.pack_into("<I", hdr, 1644, len(hdr))

    with open(args.output, "wb") as f:
        f.write(pad_to_page(bytes(hdr), args.pagesize))
        f.write(pad_to_page(kernel, args.pagesize))
        f.write(pad_to_page(ramdisk, args.pagesize))
        # v1: recovery_dtbo (size=0, nothing to write)
        if args.header_version >= 2 and dtb:
            f.write(pad_to_page(dtb, args.pagesize))

    print(f"Created {args.output}: kernel={len(kernel)} ramdisk={len(ramdisk)} dtb={len(dtb)} hdr_ver={args.header_version}")

if __name__ == "__main__":
    main()
