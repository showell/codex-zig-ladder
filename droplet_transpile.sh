#!/bin/bash
# Transpile an IR through a plug kernel on the droplet: the plug_run
# counterpart of droplet_compile.sh, same held-ssh contract (logs stream
# live, the exit code is the completion signal, flock refuses a second
# job loudly).
# Usage: droplet_transpile.sh <in.ir> <out.zig> [ring|tcp]   (default ring)
#
# Staleness checks run HERE, where the checkout lives, before anything is
# pushed -- the droplet has no checkout to re-bundle against:
#   ring: plug_run_ring.refuse_stale_ringplug (re-bundles, compares
#         ast/ringplug.cdx.fp), the same check the local arm runs.
#   tcp:  plug_provenance's contract -- sha of ZigEmitter+ZigPlug sources
#         against build-output/zig-plug.fingerprint.
# The kernel travels only when the droplet's fingerprint copy differs.
# The droplet invokes the driver with an explicit kernel path, skipping
# the droplet-side re-bundle. Both arms cap the guest at mem_mb=1300 --
# the droplet holds 2 GB total and the appliance must never swap.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
REPO="$(python3 "$T/ladder_root.py" codex)"
HOST=steve@162.243.1.123
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
    FP_FILE="$REPO/codex/plugs/zig/build-output/zig-plug.fingerprint"
    [ -s "$FP_FILE" ] || { echo "no zig-plug.fingerprint; run sweep_prep.sh or cycle.sh"; exit 1; }
    NOW=$(cat "$REPO/codex/plugs/zig/ZigEmitter.codex" "$REPO/codex/plugs/zig/ZigPlug.codex" | sha256sum | cut -d' ' -f1)
    [ "$NOW" = "$(cat "$FP_FILE")" ] || {
        echo "zig-plug.cdx is stale against the checkout's plug sources; run sweep_prep.sh or cycle.sh"
        exit 1
    }
    KERNEL="$REPO/codex/plugs/zig/build-output/zig-plug.cdx"
    RNAME=zig-plug.cdx
    ;;
*)
    echo "unknown arm '$ARM' (ring|tcp)"; exit 1 ;;
esac

FP=$(cat "$FP_FILE")
REMOTE_FP=$(ssh "$HOST" "cat ring/$RNAME.fp 2>/dev/null || true")
if [ "$FP" != "$REMOTE_FP" ]; then
    echo "pushing $RNAME (fingerprint moved)"
    scp -qC "$KERNEL" "$HOST:ring/$RNAME"
    ssh "$HOST" "printf '%s' '$FP' > ring/$RNAME.fp"
fi

scp -qC "$IR" "$HOST:ring/job.ir"
if [ "$ARM" = ring ]; then
    ssh "$HOST" 'cd ring && rm -f out.zig out.zig.cce out.zig.blob && CODEX_ACCEL=tcg nice -n 15 flock -n lock python3 -u -c "
import plug_run_ring
plug_run_ring.run_ring_plug(\"job.ir\", \"out.zig\", plug_cdx=\"ringplug.cdx\", mem_mb=1300)"'
else
    ssh "$HOST" 'cd ring && rm -f out.zig && CODEX_ACCEL=tcg nice -n 15 flock -n lock python3 -u -c "
import plug_run_checked
ok = plug_run_checked.run_verified(\"zig-plug.cdx\", \"job.ir\", \"out.zig\", mem_mb=1300)
raise SystemExit(0 if ok else 1)"'
fi
rm -f "$OUT"
scp -qC "$HOST:ring/out.zig" "$OUT"
[ -s "$OUT" ] || { echo "no zig came back"; exit 1; }
