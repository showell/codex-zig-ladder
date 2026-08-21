#!/bin/bash
# Build the two native tools that take QEMU out of the pipeline.
#
#   codexir   .codex -> .ir     (the compiler, emitting IR instead of a CDX)
#   zigemit   .ir    -> .zig    (the plug, as a program instead of a kernel)
#
# Each is built the way zigc was: bundle the subject, compile it to IR with the
# seed, push that IR through the ring plug, and build the emitted zig. The last
# step is the only one that is not a VM, which is the whole point of building
# these -- afterwards the chain
#
#   codexir prog.codex 2>prog.ir && zigemit prog.ir 2>prog.zig && zig build-exe prog.zig
#
# is three native processes. Output lands on stderr because print-text is
# cx_print is std.debug.print; that is a wart, not a design, and it is why the
# 2> redirects are there.
#
# No arguments. Both tools, every time, in order, stopping on the first failure
# -- the failure modes are shared and finding them on the smaller subject first
# costs less.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/ast/oracle_lib.sh"
take_compute_lock
OUT="$T/native"

# VENUE. CODEX_NATIVE_VENUE=droplet sends the two QEMU stages to the
# appliance instead of running them here, which is the split sweep_long has
# used all along -- the droplet is a dedicated box and this laptop is 3.8 GB
# shared with everything else. Default stays local so the known-good path is
# the one you get by typing nothing.
#
# It is not only about speed. A native build is the longest QEMU job here and
# it stalled once today because a `zig run` was started beside it; the compute
# lock only binds scripts that ask for it. Moving the guest to another machine
# removes that failure mode rather than documenting it.
# ...except that the droplet cannot actually host THIS job, and finding that
# out costs a silent twenty minutes: droplet_compile.sh pins the guest at
# 1300 MB (2 GB box, no swap, shared with the live site) where a native build
# takes the 3072 MB default. 2026-08-21: sent here by hand, the first
# venue-routed stage primed its ring, printed `detaching`, and then burned
# THREE SECONDS of CPU in eighteen minutes. No error, no exit -- the guest
# just stopped. Ordinary rungs at 1300 MB are proven (the lex truth arm ran
# droplet-side byte-identical); this job is a bigger subject and is not.
#
# Refused here rather than documented, because a comment did not stop it --
# the warning was already in the sandbox env file, in these words, and the
# run was launched anyway. When the droplet grows or droplet_compile.sh stops
# pinning 1300, delete this block; until then the toggle is a trap for the
# stage that needs the most memory.
if [ "${CODEX_NATIVE_VENUE:-local}" = droplet ]; then
    echo "native_build: REFUSING the droplet venue." >&2
    echo "  droplet_compile.sh pins CODEX_MEM_MB=1300; a native build takes" >&2
    echo "  the 3072 MB default. It does not fail there, it HANGS." >&2
    echo "  Run it here (no CODEX_NATIVE_VENUE), or grow the droplet first." >&2
    exit 1
fi

seed_compile() {   # <blob> <out>
    if [ "${CODEX_NATIVE_VENUE:-local}" = droplet ]; then
        "$T/droplet_compile.sh" "$1" "$2"
    else
        python3 -u "$T/ring_compile.py" "$1" "$2" 2>&1 | tail -3
    fi
}
ring_transpile() {  # <ir> <zig> <log>
    if [ "${CODEX_NATIVE_VENUE:-local}" = droplet ]; then
        "$T/droplet_transpile.sh" "$1" "$2" ring > "$3" 2>&1
    else
        python3 -u "$T/plug_run_ring.py" "$1" "$2" > "$3" 2>&1
    fi
}
mkdir -p "$OUT"

# The transpile step boots the RING plug, so a stale ringplug.cdx silently
# stamps yesterday's emitter onto today's tools (2026-08-19: the smoke test
# caught fresh natives carrying the pre-multibyte prelude). Rebuild it from
# source first; plug_run_ring.py refuses a stale one as the backstop.
echo "############ ring plug"
bash "$T/ast/ringplug_build.sh"

build_one() {
    local name=$1 gen=$2 bundle=$3 subject=$4
    echo "############ $name"
    cd "$T/ast"
    if [ -n "$gen" ]; then python3 "$gen"; fi

    rm -f "$subject"
    ~/.local/pwsh/pwsh -NoProfile -File "./$bundle" | tail -1
    [ -s "$subject" ] || { echo "BUNDLE FAILED: no $subject"; return 1; }

    python3 - "$subject" "$name" <<'PY'
import sys
src = open(sys.argv[1], 'rb').read()
open(f'{sys.argv[2]}-ir.blob', 'wb').write(b"IR-CCE decks=172\n" + src + b"\x04")
print(f"blob: {len(src)} bytes of source")
PY

    cd "$T"
    echo "--- compiling $name to IR (seed, QEMU, venue: ${CODEX_NATIVE_VENUE:-local})"
    rm -f "ast/$name.ir"
    seed_compile "ast/$name-ir.blob" "ast/$name.ir"
    [ -s "ast/$name.ir" ] || { echo "COMPILE FAILED: no $name.ir"; return 1; }

    echo "--- transpiling $name through the plug (QEMU, venue: ${CODEX_NATIVE_VENUE:-local})"
    rm -f "ast/$name.zig"
    ring_transpile "ast/$name.ir" "ast/$name.zig" "ast/$name.transport.log" \
        || { echo "TRANSPORT FAILED ($name):"; tail -5 "ast/$name.transport.log"; return 1; }

    # A marker means the plug could not translate a CONSTRUCT, and the build
    # must not proceed to a binary that is quietly missing it. The prelude's
    # own comptime preconditions are not that; which ones exist, and why
    # skipping them hides nothing, is findings/prelude-comptime-guards.txt.
    local markers
    markers=$(grep -o '@compileError("[^"]*")' "ast/$name.zig" \
        | grep -vxF -f <(grep -v '^#' "$T/findings/prelude-comptime-guards.txt") \
        | sort | uniq -c || true)
    if [ -n "$markers" ]; then
        echo "REFUSED: untranslated constructs in $name.zig"
        echo "$markers"
        return 1
    fi

    echo "--- building the native binary"
    zig build-exe "ast/$name.zig" -femit-bin="$OUT/$name"
    ls -la "$OUT/$name" | awk '{print "    " $NF, $5, "bytes"}'
    echo "############ $name built"
}

build_one zigemit ""                       bundle_zigemit.ps1  zigemit-source.codex
build_one codexir gen_codexir_harness.py   bundle_codexir.ps1  codexir-subject.codex

echo "############ both built in $OUT"
