#!/usr/bin/env python3
"""Convert Android sparse image(s) to raw image."""
import struct
import sys

SPARSE_MAGIC = 0xED26FF3A
CHUNK_RAW = 0xCAC1
CHUNK_FILL = 0xCAC2
CHUNK_DONT_CARE = 0xCAC3
CHUNK_CRC32 = 0xCAC4

def unsparse(input_files, output_file):
    with open(output_file, 'wb') as out:
        for fname in input_files:
            with open(fname, 'rb') as f:
                # Read sparse header
                magic, major, minor, hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, crc = \
                    struct.unpack('<IHHHHIIII', f.read(28))

                if magic != SPARSE_MAGIC:
                    print(f"Error: {fname} is not a sparse image (magic=0x{magic:08X})")
                    sys.exit(1)

                print(f"{fname}: v{major}.{minor}, {total_blks} blocks ({blk_sz} bytes), {total_chunks} chunks")

                # Skip any extra header bytes
                if hdr_sz > 28:
                    f.read(hdr_sz - 28)

                for i in range(total_chunks):
                    chunk_type, reserved, chunk_sz, total_sz = \
                        struct.unpack('<HHII', f.read(chunk_hdr_sz))

                    data_sz = total_sz - chunk_hdr_sz

                    if chunk_type == CHUNK_RAW:
                        out.write(f.read(data_sz))
                    elif chunk_type == CHUNK_FILL:
                        fill = f.read(4)
                        out.write(fill * (chunk_sz * blk_sz // 4))
                    elif chunk_type == CHUNK_DONT_CARE:
                        out.write(b'\x00' * chunk_sz * blk_sz)
                    elif chunk_type == CHUNK_CRC32:
                        f.read(data_sz)  # skip CRC
                    else:
                        print(f"Warning: unknown chunk type 0x{chunk_type:04X} at chunk {i}, skipping {data_sz} bytes")
                        f.read(data_sz)

    print(f"Wrote {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input1.img [input2.img ...] output.img")
        sys.exit(1)
    unsparse(sys.argv[1:-1], sys.argv[-1])
