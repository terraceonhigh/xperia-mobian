#!/usr/bin/env bash
# =============================================================================
# Claude Code Cage — One-time Setup Script
# Run this ON BAZZITE (192.168.1.91) as terrace.
#
# Usage:
#   bash cage-setup.sh <path-to-claude-public-key>
#
# Example:
#   bash cage-setup.sh ~/.ssh/claude_xperia_cage.pub
#
# What it does:
#   1. Creates the cage directory at ~/Lab/xperia-pmos/cage/
#   2. Installs entrypoint.sh (already transferred alongside this script)
#   3. Builds the container image from Containerfile
#   4. Adds the forced-command authorized_keys entry for Claude's key
#   5. Smoke-tests the container
# =============================================================================
set -euo pipefail

PUBKEY_FILE="${1:?Usage: $0 <path-to-claude-public-key>}"
CAGE_DIR="$HOME/Lab/xperia-pmos/cage"
ENTRYPOINT="$CAGE_DIR/entrypoint.sh"
AUDIT="$HOME/Lab/xperia-pmos/cage-audit.log"
IMAGE="localhost/xperia-cage:latest"
AUTHKEYS="$HOME/.ssh/authorized_keys"

echo "==================================================================="
echo " Claude Code Cage Setup"
echo " Host: $(hostname)"
echo " User: $(whoami)"
echo " Date: $(date -Iseconds)"
echo "==================================================================="

# 1. Verify expected files are present
echo ""
echo "[1/5] Checking cage files..."
[[ -f "$CAGE_DIR/Containerfile" ]]  || { echo "ERROR: Containerfile not found at $CAGE_DIR/Containerfile"; exit 1; }
[[ -f "$ENTRYPOINT" ]]              || { echo "ERROR: entrypoint.sh not found at $ENTRYPOINT"; exit 1; }
echo "  OK: Containerfile present"
echo "  OK: entrypoint.sh present"

# 2. Lock down entrypoint permissions
echo ""
echo "[2/5] Setting entrypoint permissions..."
chmod 750 "$ENTRYPOINT"
echo "  OK: entrypoint.sh is 750 (rwxr-x---)"

# 3. Create audit log
echo ""
echo "[3/5] Initializing audit log..."
touch "$AUDIT"
chmod 600 "$AUDIT"
echo "  OK: $AUDIT (600)"

# 4. Build container image
echo ""
echo "[4/5] Building container image (this may take a minute)..."
podman build \
    --tag "$IMAGE" \
    --file "$CAGE_DIR/Containerfile" \
    "$CAGE_DIR"

IMAGE_ID=$(podman image inspect "$IMAGE" --format "{{.Id}}" | head -c 16)
echo "  OK: $IMAGE built (id: ${IMAGE_ID}...)"

# 5. Add authorized_keys entry
echo ""
echo "[5/5] Configuring authorized_keys..."
PUBKEY="$(cat "$PUBKEY_FILE")"

if grep -qF "claude-xperia-cage" "$AUTHKEYS" 2>/dev/null; then
    echo "  SKIP: claude-xperia-cage entry already present in authorized_keys"
else
    # Append forced-command entry
    # 'restrict' shorthand enables: no-port-forwarding, no-X11-forwarding,
    # no-agent-forwarding, no-pty, no-user-rc
    printf '\n# Claude Code caged key — all commands routed through entrypoint.sh\n' >> "$AUTHKEYS"
    printf 'command="%s",restrict %s\n' "$ENTRYPOINT" "$PUBKEY" >> "$AUTHKEYS"
    echo "  OK: forced-command entry added to $AUTHKEYS"
fi

# Smoke test: run a safe command in the container
echo ""
echo "--- Smoke test: container runs python3 ---"
podman run --rm \
    --userns=keep-id \
    --security-opt=no-new-privileges \
    --cap-drop=ALL \
    "$IMAGE" \
    python3 --version

echo ""
echo "==================================================================="
echo " Setup complete."
echo ""
echo " Entrypoint : $ENTRYPOINT"
echo " Container  : $IMAGE"
echo " Audit log  : $AUDIT"
echo " Public key : $(cat "$PUBKEY_FILE" | awk '{print $1, substr($2,1,20)"..."}')"
echo ""
echo " Test from Mac:"
echo "   ssh -i ~/.ssh/claude_xperia_cage -o IdentitiesOnly=yes \\"
echo "       terrace@192.168.1.91 'echo hello'"
echo "   (Expected: denied — 'echo hello' allowed, but test with pmbootstrap)"
echo ""
echo " To teardown everything:"
echo "   podman rmi $IMAGE"
echo "   rm -rf $CAGE_DIR"
echo "   rm $AUDIT"
echo "   # Remove the claude-xperia-cage line from $AUTHKEYS"
echo "   # Delete ~/.ssh/claude_xperia_cage* from Mac"
echo "==================================================================="
