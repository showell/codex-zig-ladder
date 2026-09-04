#!/bin/bash
# Build native/codexzig: ONE program, Codex source in, zig out.
#
#   codexzig < prog.codex 2> prog.zig
#
# The two-process pipeline does the same job today --
#
#   codexir prog.codex 2>prog.ir && zigemit prog.ir 2>prog.zig
#
# -- and it is this program's ORACLE, not merely its predecessor: the same
# input must give the same bytes. `./codexzig_build.sh --check <prog.codex>`
# builds both ways and compares. Keep the two tools; the intermediate IR is
# what most of the ladder's questions are asked about, and a merged binary
# that never writes it would be worse for every one of them. This is the
# artifact for people who want to see one program.
#
# Why it is one bundle and not two emitted zig files glued together (which
# was studied and rejected -- the two emitted files share hundreds of
# declarations, so a textual merge is a pile of duplicate symbols to rename
# inside generated code; the exact count moves with the emitter, which is
# part of why the merge is the wrong level): the merge happens BEFORE the emitter
# runs, in Codex, where the two halves already meet at a type --
# emit-zig-chapter takes the compiler's own IRChapter. So there is one
# program with one main, one arena and one thread, nothing generated gets
# patched, and those 94 duplicate symbols never exist.
#
# Output lands on stderr because print-text is cx_print is std.debug.print;
# that is the same wart native_build.sh documents, and it is why the 2> is
# there.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/src/oracle_lib.sh"
. "$T/src/native_lib.sh"
OUT="$T/native"
mkdir -p "$OUT"

if [ "${1:-}" = --check ]; then
    subj="${2:?usage: codexzig_build.sh --check <prog.codex>}"
    W=$(mktemp -d)
    trap 'rm -rf "$W"' EXIT
    for t in codexzig codexir zigemit; do
        [ -x "$OUT/$t" ] || { echo "MISSING $OUT/$t -- build it first"; exit 1; }
    done
    echo "### oracle check on $subj"
    # BOTH read /dev/stdin -- their harnesses say read-file-uni "/dev/stdin"
    # and nothing looks at argv. Handing them a PATH aborts with a core dump
    # (the 10-byte CCE path on an empty read), which is what the usage line
    # in native_build.sh used to show.
    "$OUT/codexir" < "$subj" 2> "$W/pipe.ir"
    "$OUT/zigemit" < "$W/pipe.ir" 2> "$W/pipe.zig"
    "$OUT/codexzig" < "$subj" 2> "$W/one.zig"
    echo "    two processes: $(stat -c%s "$W/pipe.zig") bytes"
    echo "    one  process:  $(stat -c%s "$W/one.zig") bytes"
    # AGREEMENT IS NOT ENOUGH: two tools that both refused, or both emitted a
    # bare prelude for input that is not Codex at all, agree perfectly. Before
    # 2026-08-25 this said AGREE for a file reading `this is not codex at all`
    # -- 36,697 bytes of prelude from each side, exit 0. So the halt marker is
    # a refusal, and so is a transpile that carries nothing from the subject.
    for f in "$W/pipe.zig" "$W/one.zig"; do
        if grep -q "^CODEGEN-HALTED:" "$f"; then
            echo "### CODEGEN-HALTED -- the compiler refused this subject, no zig was emitted:"
            grep -m1 "^CODEGEN-HALTED:" "$f" | sed "s/^/    /"
            exit 1
        fi
        if ! grep -q "^pub fn main" "$f"; then
            echo "### NOT A TRANSPILE: $f carries no 'pub fn main' -- refusing to"
            echo "    call this agreement. Both arms failing the same way is not a pass."
            exit 1
        fi
    done
    if cmp -s "$W/pipe.zig" "$W/one.zig"; then
        echo "### AGREE: byte-identical"
    else
        echo "### DIFFER -- this is a finding, not a flake."
        echo "    The known deliberate delta is strip-fun-args: the compiler's"
        echo "    carries a ForAllEff arm the plug's copy lacks. Check that"
        echo "    first (src/bundle_codexzig.ps1 says why), then look further."
        diff "$W/pipe.zig" "$W/one.zig" | head -20
        exit 1
    fi
    exit 0
fi

ring_plug_fresh
build_one codexzig gen_codexzig_harness.py bundle_codexzig.ps1 codexzig-subject.codex

# THE FIXED POINT, checked here because this is where both sides exist. The
# build just produced src/codexzig.zig the long way -- the seed under QEMU,
# then the ring plug under QEMU. The binary that came out of it must
# reproduce that file from the same source, byte for byte. It exercises
# every chapter of the compiler and the whole emitter, and it costs about a
# minute against the ten this build already spent.
#
# It had no runner until 2026-08-26. The consequence was exactly what a
# missing runner always costs: the byte count quoted in the README drifted
# 193 bytes from the artifact on disk and nothing noticed, because the claim
# was made once by hand.
echo "############ fixed point: codexzig re-emitting its own bundle"
SELF="$T/src/codexzig.self.zig"
rm -f "$SELF"
"$OUT/codexzig" < "$T/src/codexzig-subject.codex" 2> "$SELF" >/dev/null
if grep -q "^CODEGEN-HALTED:" "$SELF"; then
    echo "### CODEGEN-HALTED on its own bundle:"; head -1 "$SELF"; exit 1
fi
if cmp -s "$SELF" "$T/src/codexzig.zig"; then
    echo "    IDENTICAL to src/codexzig.zig ($(stat -c%s "$SELF") bytes) -- fixed point holds"
else
    echo "### NOT A FIXED POINT: what codexzig emits for its own bundle differs"
    echo "    from what the seed-plus-ring-plug path emitted for it."
    echo "    self $(stat -c%s "$SELF") bytes, build $(stat -c%s "$T/src/codexzig.zig") bytes"
    cmp "$SELF" "$T/src/codexzig.zig" | head -3
    exit 1
fi
echo "############ codexzig built -- try: $OUT/codexzig < src/fib-repl.codex 2> fib.zig"
