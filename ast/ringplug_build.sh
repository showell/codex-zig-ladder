#!/bin/bash
# Build ast/ringplug.cdx: bundle the ring-fed plug and compile it
# bare-metal through the seed. Rerun after ANY ZigEmitter or
# ZigPlugRing change; the ten-rung sweep stays the emitter's
# correctness gate, this is only the packaging.
set -e
T="$(cd "$(dirname "$0")/.." && pwd)"  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
. "$T/ast/oracle_lib.sh"
# A ring compile is a guest. Re-entrant, so allcycles.sh and
# zigc_verify.sh -- which hold the lock when they call this -- are
# unaffected.
take_compute_lock
cd "$T/ast"
rm -f ringplug-source.codex
out=$(~/.local/pwsh/pwsh -NoProfile -File ./bundle_ringplug.ps1 2>&1) || { printf '%s\n' "$out" | tail -5; exit 1; }
printf '%s\n' "$out" | tail -1
python3 - <<'PY'
src = open('ringplug-source.codex', 'rb').read()
open('ringplug-cdx.blob', 'wb').write(b"CDX map\n" + src + b"\x04")
print(f"blob: {len(src)} bytes")
PY
cd "$T"
# Already current? The bundle is deterministic and the fingerprint IS the sha
# of it, so a matching fp beside a non-empty cdx means this exact plug has
# already been compiled -- possibly on the droplet by sweep_prep, minutes ago.
# Recompiling it would be a minute of QEMU spent to reach the file already on
# disk. The check is content, never mtime.
want=$(sha256sum ast/ringplug-source.codex | awk '{print $1}')
if [ -s ast/ringplug.cdx ] && [ "$(cat ast/ringplug.cdx.fp 2>/dev/null)" = "$want" ]; then
    echo "ast/ringplug.cdx already matches this bundle ($(echo $want | head -c 12)) -- not recompiling"
    exit 0
fi
rm -f ast/ringplug.cdx
if [ "${CODEX_NATIVE_VENUE:-local}" = droplet ]; then
    "$T/droplet_compile.sh" ast/ringplug-cdx.blob ast/ringplug.cdx
else
    python3 -u ring_compile.py ast/ringplug-cdx.blob ast/ringplug.cdx 2>&1 | grep -E "error|SIZE" | head -10
fi
[ -s ast/ringplug.cdx ] || { echo "PLUG COMPILE FAILED"; exit 1; }
# The fingerprint plug_run_ring.py refuses to boot without: the sha of the
# bundle this cdx was compiled from. The bundle is deterministic, so a
# re-bundle that hashes differently means the checkout's plug sources moved
# since this build.
sha256sum ast/ringplug-source.codex | awk '{print $1}' > ast/ringplug.cdx.fp
echo "ast/ringplug.cdx built ($(cat ast/ringplug.cdx.fp | head -c 12))"
