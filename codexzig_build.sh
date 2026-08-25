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
# was studied and rejected -- the two share 68 identical cx_* prelude symbols
# and 26 more colliding top-level names, so a textual merge is 94 duplicates
# to rename inside generated code): the merge happens BEFORE the emitter
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
. "$T/ast/oracle_lib.sh"
. "$T/ast/native_lib.sh"
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
    if cmp -s "$W/pipe.zig" "$W/one.zig"; then
        echo "### AGREE: byte-identical"
    else
        echo "### DIFFER -- this is a finding, not a flake."
        echo "    The known deliberate delta is strip-fun-args: the compiler's"
        echo "    carries a ForAllEff arm the plug's copy lacks. Check that"
        echo "    first (ast/bundle_codexzig.ps1 says why), then look further."
        diff "$W/pipe.zig" "$W/one.zig" | head -20
        exit 1
    fi
    exit 0
fi

ring_plug_fresh
build_one codexzig gen_codexzig_harness.py bundle_codexzig.ps1 codexzig-subject.codex
echo "############ codexzig built -- try: $OUT/codexzig < ast/fib.codex 2> fib.zig"
