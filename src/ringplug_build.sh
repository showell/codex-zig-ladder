#!/bin/bash
# Build src/ringplug.cdx: bundle the ring-fed plug and compile it
# bare-metal through the seed. Rerun after ANY ZigEmitter or
# ZigPlugRing change; the ten-rung sweep stays the emitter's
# correctness gate, this is only the packaging.
set -e
T="$(cd "$(dirname "$0")/.." && pwd)"  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
. "$T/src/oracle_lib.sh"
# A ring compile is a guest. Re-entrant, so allcycles.sh and
# zigc_verify.sh -- which hold the lock when they call this -- are
# unaffected.
cd "$O"
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
want=$(sha256sum src/ringplug-source.codex | awk '{print $1}')
if [ -s src/ringplug.cdx ] && [ "$(cat src/ringplug.cdx.fp 2>/dev/null)" = "$want" ]; then
    echo "src/ringplug.cdx already matches this bundle ($(echo $want | head -c 12)) -- not recompiling"
    exit 0
fi
rm -f src/ringplug.cdx
if [ "${CODEX_NATIVE_VENUE:-local}" = droplet ]; then
    "$T/droplet_compile.sh" src/ringplug-cdx.blob src/ringplug.cdx
else
    # KEEP THE WHOLE OUTPUT. This was piped straight through
    # `grep -E "error|SIZE" | head -10`, which shows the summary on success and
    # DISCARDS EVERY OTHER REASON THE COMPILE COULD FAIL. Both refusals that
    # actually happen say neither word: a host with no CODEX_LADDER_VENUE, and
    # `compute_lock` refusing beside a foreign guest ("A GUEST IS ALREADY
    # RUNNING, and it did not take the lock"). Each then reads as a bare
    # PLUG COMPILE FAILED on a plug that compiles perfectly by hand -- three
    # wrong diagnoses on 2026-08-30 alone, one of them twelve minutes long.
    python3 -u ring_compile.py src/ringplug-cdx.blob src/ringplug.cdx \
        > src/ringplug-compile.log 2>&1
    rc=$?
    grep -E "error|SIZE" src/ringplug-compile.log | head -10
fi
[ -s src/ringplug.cdx ] || {
    echo "PLUG COMPILE FAILED (ring_compile rc=${rc:-?}); last lines of src/ringplug-compile.log:"
    tail -15 src/ringplug-compile.log 2>/dev/null | sed 's/^/    /'
    exit 1
}
# The fingerprint plug_run_ring.py refuses to boot without: the sha of the
# bundle this cdx was compiled from. The bundle is deterministic, so a
# re-bundle that hashes differently means the checkout's plug sources moved
# since this build.
sha256sum src/ringplug-source.codex | awk '{print $1}' > src/ringplug.cdx.fp
echo "src/ringplug.cdx built ($(cat src/ringplug.cdx.fp | head -c 12))"
