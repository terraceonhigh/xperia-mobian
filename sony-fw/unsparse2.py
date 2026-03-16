#!/usr/bin/env python3
"""Convert Android sparse image(s) to raw, treating 0xCAC5 as raw data chunks."""
import struct
import sys

SPARSE_MAGIC = 0xED26FF3A
CHUNK_RAW = 0xCAC1
CHUNK_FILL = 0xCAC2
CHUNK_DONT_CARE = 0xCAC3
CHUNK_CRC32 = 0xCAC4
CHUNK_SONY_CRC = 0xCAC5  # Sony extension: CRC + raw data

def unsparse(input_files, output_file):
    with open(output_file, 'wb') as out:
        for fname in input_files:
            with open(fname, 'rb') as f:
                magic, major, minor, hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, crc = \
                    struct.unpack('<IHHHHIIII', f.read(28))

                if magic != SPARSE_MAGIC:
                    print(f"Error: {fname} is not a sparse image")
                    sys.exit(1)

                print(f"{fname}: v{major}.{minor}, {total_blks} blocks x {blk_sz}, {total_chunks} chunks")

                if hdr_sz > 28:
                    f.read(hdr_sz - 28)

                for i in range(total_chunks):
                    chunk_type, reserved, chunk_sz, total_sz = \
                        struct.unpack('<HHII', f.read(chunk_hdr_sz))
                    data_sz = total_sz - chunk_hdr_sz
                    expected_raw = chunk_sz * blk_sz

                    if chunk_type == CHUNK_RAW:
                        out.write(f.read(data_sz))
                    elif chunk_type == CHUNK_FILL:
                        fill = f.read(4)
                        out.write(fill * (expected_raw // 4))
                    elif chunk_type == CHUNK_DONT_CARE:
                        out.write(b'\x00' * expected_raw)
                    elif chunk_type == CHUNK_CRC32:
                        f.read(data_sz)
                    elif chunk_type == CHUNK_SONY_CRC:
                        # Sony CRC chunk: 4-byte CRC followed by raw data
                        # Or possibly 2-byte CRC. Let's check both.
                        data = f.read(data_sz)
                        # The raw data should be expected_raw bytes
                        # Try to find the offset where the data starts
                        if data_sz == expected_raw + 4:
                            # 4-byte CRC prefix
                            out.write(data[4:])
                        elif data_sz == expected_raw + 2:
                            # 2-byte CRC prefix
                            out.write(data[2:])
                        elif data_sz == expected_raw:
                            out.write(data)
                        else:
                            # Data is smaller than expected — might be compressed
                            # Just write what we have and pad
                            out.write(data)
                            if data_sz < expected_raw:
                                out.write(b'\x00' * (expected_raw - data_sz))
                    else:
                        data = f.read(data_sz)
                        print(f"Unknown chunk 0x{chunk_type:04X}, {data_sz} bytes for {expected_raw} expected")
                        out.write(data)
                        if data_sz < expected_raw:
                            out.write(b'\x00' * (expected_raw - data_sz))

    import os
    sz = os.path.getsize(output_file)
    print(f"Wrote {output_file} ({sz} bytes, {sz/1024/1024:.1f} MB)")

if __name__ == '__main__':
    unsparse(sys.argv[1:-1], sys.argv[-1])
