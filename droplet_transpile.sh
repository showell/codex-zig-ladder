#!/bin/bash
# Transpile an IR through the ring plug on the droplet: the plug_run_ring
# counterpart of droplet_compile.sh, same held-ssh contract (logs stream
# live, the exit code is the completion signal, flock refuses a second
# job loudly).
# Usage: droplet_transpile.sh <in.ir> <out.zig>
#
# The staleness check runs HERE, where the checkout lives: plug_run_ring's
# refuse_stale_ringplug re-bundles and compares against ast/ringplug.cdx.fp
# before anything is pushed. The droplet then receives the verified kernel
# and invokes run_ring_plug with an explicit plug_cdx, which skips the
# droplet-side re-bundle it has no checkout to perform. The ringplug and
# its fp travel per job only when the fp moved; the seed guard from
# droplet_compile.sh is not needed here (the ring plug IS the kernel).
set -e
T="$(cd "$(dirname "$0")" && pwd)"
HOST=steve@162.243.1.123
IR=$1
OUT=$2
[ -s "$IR" ] || { echo "no IR at $IR"; exit 1; }

CODEX_ROOT="${CODEX_ROOT:?droplet_transpile.sh needs CODEX_ROOT for the staleness check}" \
python3 -c "
import pathlib, plug_run_ring
plug_run_ring.refuse_stale_ringplug(pathlib.Path('$T'))
print('ringplug fresh against the checkout')"

FP=$(cat "$T/ast/ringplug.cdx.fp")
REMOTE_FP=$(ssh "$HOST" 'cat ring/ringplug.cdx.fp 2>/dev/null || true')
if [ "$FP" != "$REMOTE_FP" ]; then
    echo "pushing ringplug.cdx (fp moved)"
    scp -q "$T/ast/ringplug.cdx" "$HOST:ring/ringplug.cdx"
    scp -q "$T/ast/ringplug.cdx.fp" "$HOST:ring/ringplug.cdx.fp"
fi

scp -qC "$IR" "$HOST:ring/job.ir"
ssh "$HOST" 'cd ring && rm -f out.zig out.zig.cce out.zig.blob && CODEX_ACCEL=tcg nice -n 15 flock -n lock python3 -u -c "
import plug_run_ring
plug_run_ring.run_ring_plug(\"job.ir\", \"out.zig\", plug_cdx=\"ringplug.cdx\", mem_mb=1300)"'
rm -f "$OUT"
scp -qC "$HOST:ring/out.zig" "$OUT"
[ -s "$OUT" ] || { echo "no zig came back"; exit 1; }
