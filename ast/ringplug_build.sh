#!/bin/bash
# Build ast/ringplug.cdx: bundle the ring-fed plug and compile it
# bare-metal through the seed. Rerun after ANY ZigEmitter or
# ZigPlugRing change; the ten-rung sweep stays the emitter's
# correctness gate, this is only the packaging.
set -e
T="$(cd "$(dirname "$0")/.." && pwd)"  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
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
rm -f ast/ringplug.cdx
python3 -u ring_compile.py ast/ringplug-cdx.blob ast/ringplug.cdx 2>&1 | grep -E "error|SIZE" | head -10
[ -s ast/ringplug.cdx ] || { echo "PLUG COMPILE FAILED"; exit 1; }
# The fingerprint plug_run_ring.py refuses to boot without: the sha of the
# bundle this cdx was compiled from. The bundle is deterministic, so a
# re-bundle that hashes differently means the checkout's plug sources moved
# since this build.
sha256sum ast/ringplug-source.codex | awk '{print $1}' > ast/ringplug.cdx.fp
echo "ast/ringplug.cdx built ($(cat ast/ringplug.cdx.fp | head -c 12))"
