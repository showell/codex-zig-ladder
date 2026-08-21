#!/bin/bash
# The two-venue sweep's shared prep: bundle BOTH plugs once, compile both
# kernels on the droplet, stamp the same fingerprints the local scripts
# stamp, and push the kernels plus the TCP-arm drivers to the appliance.
# sweep_canary.sh and sweep_long.sh consume what this leaves behind; a
# sweep is only coherent if every rung sees the same plug, which is why
# bundling happens here and nowhere else in the two-venue path.
#
# The bundling entrypoints and fingerprint semantics are the same ones
# cycle.sh and ast/ringplug_build.sh use (Build-TranspilerPlug with the
# compile step stubbed; sha of the bundled source for the ring fp, sha of
# the two plug sources for the TCP fingerprint) -- only the compile venue
# moved. Those two scripts remain the all-local authority.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
REPO="$(python3 "$T/ladder_root.py" codex)"
HOST=steve@162.243.1.123
. "$T/sweep_lib.sh"
take_compute_lock

echo "### sweep_prep $(date +%H:%M:%S)"

# WHOSE PLUG. CODEX_ROOT means two opposite things depending on what is being
# built, and nothing used to say which one it was pointing at. For a truth arm
# or a tier the pin is CORRECT -- bare metal is the oracle and must be the
# released compiler. For a plug build the pin is almost always WRONG, because
# the whole point is to measure a branch that has moved. Same variable,
# inverted role, and one wrong export silently builds the unmodified plug and
# then measures it against a hypothesis about a modified one.
#
# So say it, first line, before spending four minutes of QEMU on it. Not a
# refusal: building the pin's plug is a legitimate baseline, and a guard that
# forbids a legitimate thing gets switched off.
plug_branch=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')
plug_head=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo '?')
plug_dirty=$(git -C "$REPO" status --porcelain 2>/dev/null | head -1)
echo "### plug source: $REPO"
echo "###   branch $plug_branch at $plug_head${plug_dirty:+  (working tree DIRTY)}"
echo "###   $(git -C "$REPO" log --oneline -1 2>/dev/null | cut -c1-72)"

# --- the TCP plug (zig-plug.cdx) ---
PLUG_DIR="$REPO/codex/plugs/zig"
PLUG_SRC="$PLUG_DIR/build-output/plug-source.codex"
PLUG_CDX="$PLUG_DIR/build-output/zig-plug.cdx"
rm -f "$PLUG_SRC"
~/.local/pwsh/pwsh -NoProfile -Command "
\$ErrorActionPreference = 'Stop'
. $REPO/codex/plugs/common/plug-build-lib.ps1
function Build-PlugCdx { Write-Host '[bundle only, compile skipped]' }
Build-TranspilerPlug -PlugDir $PLUG_DIR -PlugName zig -Chapters @('ZigEmitter', 'ZigPlug')
" | tail -1
[ -s "$PLUG_SRC" ] || { echo "BUNDLE FAILED: no plug-source.codex"; exit 1; }
python3 - "$PLUG_SRC" "$T/.prep-plug.blob" <<'PY'
import sys
src = open(sys.argv[1], 'rb').read()
open(sys.argv[2], 'wb').write(b"CDX map\n" + src + b"\x04")
print(f"plug blob: {len(src)} bytes")
PY
rm -f "$PLUG_CDX"
"$T/droplet_compile.sh" "$T/.prep-plug.blob" "$PLUG_CDX"
[ -s "$PLUG_CDX" ] || { echo "PLUG COMPILE FAILED"; exit 1; }
cat "$PLUG_DIR/ZigEmitter.codex" "$PLUG_DIR/ZigPlug.codex" \
    | sha256sum | cut -d' ' -f1 > "$PLUG_DIR/build-output/zig-plug.fingerprint"
rm -f "$T/.prep-plug.blob"

# --- the ring plug (ast/ringplug.cdx) ---
cd "$T/ast"
rm -f ringplug-source.codex
~/.local/pwsh/pwsh -NoProfile -File ./bundle_ringplug.ps1 | tail -1
[ -s ringplug-source.codex ] || { echo "BUNDLE FAILED: no ringplug-source.codex"; exit 1; }
python3 - ringplug-source.codex "$T/.prep-ring.blob" <<'PY'
import sys
src = open(sys.argv[1], 'rb').read()
open(sys.argv[2], 'wb').write(b"CDX map\n" + src + b"\x04")
print(f"ring blob: {len(src)} bytes")
PY
cd "$T"
rm -f ast/ringplug.cdx
"$T/droplet_compile.sh" "$T/.prep-ring.blob" "$T/ast/ringplug.cdx"
[ -s ast/ringplug.cdx ] || { echo "RING PLUG COMPILE FAILED"; exit 1; }
sha256sum ast/ringplug-source.codex | cut -d' ' -f1 > ast/ringplug.cdx.fp
rm -f "$T/.prep-ring.blob"

# --- push the ring kernel, its fingerprint, and the drivers ---
# Only the ring kernel travels: the TCP plug cannot boot inside the
# appliance's 1300 MB cap (see remote_arm_for in sweep_lib.sh), so the
# freshly compiled zig-plug.cdx stays in build-output for the LOCAL
# arms, where plug_provenance still wants it fresh.
scp -qC "$T/ast/ringplug.cdx" "$HOST:ring/ringplug.cdx"
scp -q "$T/ast/ringplug.cdx.fp" "$HOST:ring/ringplug.cdx.fp"
scp -q "$T/plug_run.py" "$T/plug_run_checked.py" "$T/pcap_parity.py" "$T/plug_run_ring.py" "$T/cce.py" "$HOST:ring/"

echo "### sweep_prep done $(date +%H:%M:%S): both kernels compiled on the droplet and pushed"
