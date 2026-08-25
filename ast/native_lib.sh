# Building a native tool: bundle the subject, compile it to IR with the seed,
# push that IR through the ring plug, build the emitted zig. Four steps, and
# the last is the only one that is not a VM.
#
# Shared by native_build.sh (codexir, zigemit) and codexzig_build.sh, which
# build the same way from different chapter sets. It lives here because a
# second copy of build_one is a second place for the marker scan, the deck
# count and the rm-first discipline to drift -- this tree has spent a day
# deleting exactly that shape.
#
# Callers set T (ladder root) and OUT (where the binary lands), and source
# ast/oracle_lib.sh first.

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
# The transpile step boots the RING plug, so a stale ringplug.cdx silently
# stamps yesterday's emitter onto today's tools (2026-08-19: the smoke test
# caught fresh natives carrying the pre-multibyte prelude). Every caller
# rebuilds it from source before its first build_one; plug_run_ring.py
# refuses a stale one as the backstop. It is a CALL and not a line in this
# file because sourcing a library must not start a guest.
ring_plug_fresh() {
    echo "############ ring plug"
    bash "$T/ast/ringplug_build.sh"
}

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

