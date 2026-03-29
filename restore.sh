#!/usr/bin/env bash
set -euo pipefail

# Restore binary assets from the GitHub Release.
# Usage: ./restore.sh
# Requires: gh (GitHub CLI), authenticated

REPO="terraceonhigh/xperia-mobian"
TAG="blobs-v1"
TMP_DIR="/tmp/xperia-restore"

mkdir -p "$TMP_DIR"

echo "=== Downloading release assets from $REPO @ $TAG ==="
gh release download "$TAG" --repo "$REPO" --dir "$TMP_DIR" --clobber

echo ""
echo "=== Placing files ==="

# Move each asset back to its original path.
# Asset naming convention: '--' encodes directory separators.
# Split files have a '.part-NN' suffix and need reassembly.
for asset in "$TMP_DIR"/*; do
    name="$(basename "$asset")"

    # Skip split parts on first pass (handled below)
    if [[ "$name" == *.part-* ]]; then
        continue
    fi

    # Convert '--' back to '/'
    dest="${name//--//}"
    mkdir -p "$(dirname "$dest")"
    mv "$asset" "$dest"
    echo "  $dest"
done

echo ""
echo "=== Reassembling split files ==="

# Find unique split file prefixes
declare -A seen
for asset in "$TMP_DIR"/*.part-* 2>/dev/null; do
    name="$(basename "$asset")"
    prefix="${name%.part-*}"
    if [[ -z "${seen[$prefix]+x}" ]]; then
        seen[$prefix]=1
        # Convert '--' back to '/'
        dest="${prefix//--//}"
        mkdir -p "$(dirname "$dest")"
        echo "  $dest (from parts)..."
        cat "$TMP_DIR/${prefix}".part-* > "$dest"
        rm -f "$TMP_DIR/${prefix}".part-*
    fi
done

# Cleanup
rm -rf "$TMP_DIR"

echo ""
echo "=== Done ==="
echo "All binary assets restored. You can verify with:"
echo "  ls -lh images/ build/"
