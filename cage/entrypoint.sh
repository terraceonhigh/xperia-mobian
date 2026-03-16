#!/usr/bin/env bash
# =============================================================================
# Claude Code Cage — SSH Forced Command Entrypoint
#
# Invoked automatically by sshd whenever Claude's caged key is used.
# $SSH_ORIGINAL_COMMAND contains the full command string Claude sent.
#
# Two-layer validation:
#   1. Blocklist  — deny dangerous substrings regardless of context
#   2. Allowlist  — permit only known-safe first commands
#
# After passing both checks, the command runs inside the Podman container
# where filesystem access is limited to the mounted workspace.
#
# Audit log: ~/Lab/xperia-pmos/cage-audit.log
# =============================================================================
set -euo pipefail

readonly AUDIT="$HOME/Lab/xperia-pmos/cage-audit.log"
readonly IMAGE="localhost/xperia-cage:latest"
readonly WS="$HOME/Lab/xperia-pmos"

_log()  { printf '%s [%s] %s\n' "$(date -Iseconds)" "$$" "$*" >> "$AUDIT"; }
_deny() { _log "DENY: ${SSH_ORIGINAL_COMMAND:-<empty>}"; printf 'denied\n' >&2; exit 1; }

CMD="${SSH_ORIGINAL_COMMAND:-}"
[[ -z "$CMD" ]] && _deny          # no interactive shells

_log "REQ: $CMD"

# =============================================================================
# LAYER 1 — BLOCKLIST
# Dangerous substrings denied regardless of where they appear in a pipeline.
# Covers compound commands (&&, ;, |) that might sneak past the allowlist.
# =============================================================================
blocked=(
    # Privilege escalation
    " sudo" ";sudo" "|sudo" "&&sudo"
    " su "  ";su "  "|su "

    # Container escape
    "podman" "docker" "nerdctl" "runc" "crun"

    # Lateral movement / data exfil
    " ssh "  ";ssh "  "|ssh "  "&&ssh "
    " scp "  " sftp " " rsync " " ftp "
    "curl"   "wget"   " nc "   "ncat"  "netcat" "socat" "telnet"

    # Covert encoding / channel
    "base64" " xxd " " od " " hexdump "

    # Persistence
    "crontab" "systemctl" " at "

    # Arbitrary code execution via interpreter flags
    "python3 -c" "python -c" "perl -e" "ruby -e" "node -e" "lua -e"

    # Shell injection via pipe
    "| bash" "|bash" "| sh " "|sh " "| zsh" "|zsh"

    # Key material (belt-and-suspenders; container mounts exclude .ssh anyway)
    ".ssh/"  "authorized_keys"  "id_rsa"  "id_ed25519"  "id_ecdsa"
)

for b in "${blocked[@]}"; do
    if [[ "$CMD" == *"$b"* ]]; then
        _log "DENY_BLOCK: $b"
        _deny
    fi
done

# =============================================================================
# LAYER 2 — ALLOWLIST
# Extract the first command token (basename, ignoring leading path).
# Only permitted base commands may appear as the entry point.
# =============================================================================
first_token="${CMD%% *}"           # everything before the first space
first_cmd="${first_token##*/}"     # strip leading path (e.g. .venv/bin/ → pmbootstrap)

case "$first_cmd" in
    pmbootstrap | \
    git         | \
    cat | ls | grep | tail | tac | head | wc | find | stat | file | diff | \
    sha512sum | sha256sum | md5sum | \
    echo | printf | \
    mkdir | touch | \
    cd | true | false | \
    sort | uniq | cut | awk | sed | tr | \
    tar | unzip | gzip | xz | bzip2 | \
    make | cp | mkbootimg | dtc | lz4 | zstd )
        ;;
    *)
        _log "DENY_ALLOW: first_cmd=$first_cmd"
        _deny
        ;;
esac

_log "ALLOW"

# =============================================================================
# EXECUTE — inside the cage container
#
# Mounts (all paths identical inside container to keep pmbootstrap happy):
#   pmaports/        rw  — package files Claude edits
#   .pmbootstrap/    rw  — build artifacts, Alpine chroot, logs
#   .venv/           ro  — pmbootstrap Python environment (no writes needed)
#   stock-partitions/ ro — reference firmware (read-only, never writable)
#   pmbootstrap_v3.cfg rw — config (pmbootstrap config command writes here)
#
# Security options:
#   --userns=keep-id         map host UID into container (no UID 0 privilege)
#   --no-new-privileges      prevent setuid/setcap escalation inside container
#   --cap-drop=ALL           drop all Linux capabilities
#   --cap-add=SYS_PTRACE     needed by proot (pmbootstrap's internal chroot)
#   network: default pasta   outbound internet allowed (APK downloads),
#                            host LAN (192.168.1.x) NOT reachable from inside
# =============================================================================
KERNEL_MOUNT=()
if [[ -d "${WS}/../sm6350-kernel" ]]; then
    KERNEL_MOUNT=(-v "${WS}/../sm6350-kernel:${WS}/../sm6350-kernel")
fi

exec podman run --rm \
    --userns=keep-id \
    --security-opt=no-new-privileges \
    --security-opt=label=disable \
    --cap-drop=ALL \
    --cap-add=SYS_PTRACE \
    -v "${WS}/pmaports:${WS}/pmaports" \
    -v "${WS}/.pmbootstrap:${WS}/.pmbootstrap" \
    -v "${WS}/.venv:${WS}/.venv:ro" \
    -v "${WS}/stock-partitions:${WS}/stock-partitions:ro" \
    "${KERNEL_MOUNT[@]}" \
    -v "$HOME/.config/pmbootstrap_v3.cfg:$HOME/.config/pmbootstrap_v3.cfg" \
    --env HOME="$HOME" \
    --env PATH="/usr/local/bin:/usr/bin:/bin:${WS}/.venv/bin" \
    --workdir "${WS}" \
    "$IMAGE" \
    /bin/bash -c "$CMD"
