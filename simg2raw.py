#!/usr/bin/env python3
"""Convert Android sparse image to raw, streaming to stdout."""
import struct
import sys

SPARSE_MAGIC = 0xed26ff3a

def main():
    f = sys.stdin.buffer
    hdr = f.read(28)
    magic, major, minor, hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, checksum = struct.unpack('<IHHHHIIII', hdr)

    if magic != SPARSE_MAGIC:
        sys.stderr.write("Not a sparse image!\n")
        sys.exit(1)

    total_size = total_blks * blk_sz
    sys.stderr.write(f"Sparse: {total_blks} blocks x {blk_sz} = {total_size/1024/1024/1024:.1f}GB, {total_chunks} chunks\n")

    # Skip rest of header
    if hdr_sz > 28:
        f.read(hdr_sz - 28)

    out = sys.stdout.buffer
    zeros = b'\x00' * blk_sz

    for i in range(total_chunks):
        chunk_hdr = f.read(chunk_hdr_sz)
        chunk_type, reserved, chunk_sz, total_sz = struct.unpack('<HHII', chunk_hdr)
        data_sz = total_sz - chunk_hdr_sz

        if chunk_type == 0xCAC1:  # RAW
            remaining = data_sz
            while remaining > 0:
                to_read = min(remaining, 4 * 1024 * 1024)
                out.write(f.read(to_read))
                remaining -= to_read
        elif chunk_type == 0xCAC2:  # FILL
            fill = f.read(4)
            fill_block = fill * (blk_sz // 4)
            for _ in range(chunk_sz):
                out.write(fill_block)
        elif chunk_type == 0xCAC3:  # DONT_CARE
            for _ in range(chunk_sz):
                out.write(zeros)
        elif chunk_type == 0xCAC4:  # CRC32
            f.read(data_sz)

        if (i + 1) % 3000 == 0:
            sys.stderr.write(f"  {i+1}/{total_chunks} chunks\n")

    sys.stderr.write("Done.\n")

if __name__ == "__main__":
    main()
