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
#   codexir <prog.codex 2>prog.ir && zigemit <prog.ir 2>prog.zig && zig build-exe prog.zig
#
# Both read /dev/stdin and neither looks at argv, so the redirect is not a
# style choice: this line said `codexir prog.codex` until 2026-08-25, and
# that form aborts with a core dump -- the empty read takes the 10-byte CCE
# path. A usage line nobody had run.
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
. "$T/src/oracle_lib.sh"
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
# The droplet venue was refused here from 2026-08-21 to 2026-08-22 while
# droplet_compile.sh pinned a 1300 MB guest on the 2 GB site box: a
# native build takes 3072 MB and the job did not fail there, it HANGED
# (three seconds of CPU in eighteen minutes). The venue is the 8 GB
# ladder droplet now and droplet_compile.sh pins 3072, so the toggle
# does what it says again; the measurement stays in JUSTIFICATIONS.md.
. "$T/src/native_lib.sh"
mkdir -p "$OUT"
ring_plug_fresh

build_one zigemit ""                       bundle_zigemit.ps1  zigemit-source.codex
build_one codexir gen_codexir_harness.py   bundle_codexir.ps1  codexir-subject.codex

echo "############ both built in $OUT"
