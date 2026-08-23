#!/bin/bash
# Transpile an IR through a plug kernel on the droplet: the plug_run
# counterpart of droplet_compile.sh, same held-ssh contract (logs stream
# live, the exit code is the completion signal, flock refuses a second
# job loudly).
# Usage: droplet_transpile.sh <in.ir> <out.zig> [ring]
#
# Ring only: the tcp argument is still recognized so an old caller gets
# the reason instead of a mystery, but it refuses (see the case below).
# The staleness check runs HERE, where the checkout lives, before
# anything is pushed -- the droplet has no checkout to re-bundle
# against: plug_run_ring.refuse_stale_ringplug (re-bundles, compares
# ast/ringplug.cdx.fp), the same check the local arm runs.
# The kernel travels only when the droplet's fingerprint copy differs.
# The droplet invokes the driver with an explicit kernel path, skipping
# the droplet-side re-bundle, and caps the guest at mem_mb=3072, the seed
# guest's measured ceiling on the 8 GB ladder droplet (droplet_compile.sh
# has the measurement); the appliance must never swap.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
REPO="$(python3 "$T/ladder_root.py" codex)"
HOST=steve@143.244.172.148
# Keepalives, because the held ssh IS the job -- see droplet_compile.sh
# for the incident (a wifi blip SIGHUPed the remote session mid-sweep,
# killed the guest, and the laptop side hung on the dead link).
SSH_OPTS="-o ServerAliveInterval=15 -o ServerAliveCountMax=4 -o ConnectTimeout=20"
IR=$1
OUT=$2
ARM=${3:-ring}
[ -s "$IR" ] || { echo "no IR at $IR"; exit 1; }

case "$ARM" in
ring)
    CODEX_ROOT="${CODEX_ROOT:?droplet_transpile.sh needs CODEX_ROOT}" \
    python3 -c "
import pathlib, plug_run_ring
plug_run_ring.refuse_stale_ringplug(pathlib.Path('$T'))
print('ringplug fresh against the checkout')"
    KERNEL="$T/ast/ringplug.cdx"
    FP_FILE="$T/ast/ringplug.cdx.fp"
    RNAME=ringplug.cdx
    ;;
tcp)
    # The TCP plug's boot-time heap reservation needs >= 1600 MB of guest
    # RAM (measured 2026-08-20: connects at 1600, exits silently at 1500).
    # The 8 GB droplet's 3072 cap would hold it now, but the TCP kernel
    # does not travel (sweep_prep.sh pushes only the ring kernel, and
    # sweep_lib's remote_arm_for routes ring-only), so the arm stays
    # local until that plumbing exists -- a queued item, not a cap.
    echo "the TCP plug does not travel to the droplet yet -- use the ring arm"
    exit 1
    ;;
*)
    echo "unknown arm '$ARM' (ring|tcp)"; exit 1 ;;
esac

FP=$(cat "$FP_FILE")
REMOTE_FP=$(ssh $SSH_OPTS "$HOST" "cat ring/$RNAME.fp 2>/dev/null || true")
if [ "$FP" != "$REMOTE_FP" ]; then
    echo "pushing $RNAME (fingerprint moved)"
    scp -qC $SSH_OPTS "$KERNEL" "$HOST:ring/$RNAME"
    ssh $SSH_OPTS "$HOST" "printf '%s' '$FP' > ring/$RNAME.fp"
fi

scp -qC $SSH_OPTS "$IR" "$HOST:ring/job.ir"
ssh $SSH_OPTS "$HOST" 'cd ring && rm -f out.zig out.zig.cce out.zig.blob && CODEX_ACCEL=tcg nice -n 15 flock -n lock python3 -u -c "
import plug_run_ring
plug_run_ring.run_ring_plug(\"job.ir\", \"out.zig\", plug_cdx=\"ringplug.cdx\", mem_mb=3072)"'
rm -f "$OUT"
scp -qC $SSH_OPTS "$HOST:ring/out.zig" "$OUT"
[ -s "$OUT" ] || { echo "no zig came back"; exit 1; }
