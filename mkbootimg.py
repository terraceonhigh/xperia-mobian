#!/usr/bin/env python3
"""Minimal Android boot image builder (header version 0 only).

Usage:
    python3 mkbootimg.py --kernel zImage --ramdisk initrd.img \
        --base 0x10000000 --pagesize 4096 --cmdline "..." -o boot.img
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
    p = argparse.ArgumentParser(description="Build Android boot image (v0)")
    p.add_argument("--kernel", required=True)
    p.add_argument("--ramdisk", required=True)
    p.add_argument("--base", default="0x10000000")
    p.add_argument("--pagesize", type=int, default=4096)
    p.add_argument("--cmdline", default="")
    p.add_argument("--header_version", type=int, default=0)
    p.add_argument("-o", "--output", required=True)
    args = p.parse_args()

    base = int(args.base, 0)
    kernel_addr = base + 0x8000
    ramdisk_addr = base + 0x1000000
    second_addr = base + 0x0
    tags_addr = base + 0x100

    with open(args.kernel, "rb") as f:
        kernel = f.read()
    with open(args.ramdisk, "rb") as f:
        ramdisk = f.read()

    cmdline = args.cmdline.encode("utf-8")
    if len(cmdline) > 512:
        cmdline_main = cmdline[:512]
        cmdline_extra = cmdline[512:1536]
    else:
        cmdline_main = cmdline
        cmdline_extra = b""

    # Header v0: magic(8) + sizes/addrs(10*4=40) + name(16) + cmdline(512)
    # + id(32) + extra_cmdline(1024) = 1632 bytes, padded to pagesize
    header = struct.pack(
        "8s"      # magic
        "I"       # kernel_size
        "I"       # kernel_addr
        "I"       # ramdisk_size
        "I"       # ramdisk_addr
        "I"       # second_size
        "I"       # second_addr
        "I"       # tags_addr
        "I"       # page_size
        "I"       # header_version (0)
        "I"       # os_version
        "16s"     # name
        "512s"    # cmdline
        "32s"     # id (sha1 hash, can be zeros)
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
    )

    with open(args.output, "wb") as f:
        f.write(pad_to_page(header, args.pagesize))
        f.write(pad_to_page(kernel, args.pagesize))
        f.write(pad_to_page(ramdisk, args.pagesize))

    print(f"Created {args.output}: kernel={len(kernel)} ramdisk={len(ramdisk)}")

if __name__ == "__main__":
    main()
