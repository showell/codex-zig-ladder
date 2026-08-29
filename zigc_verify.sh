#!/bin/bash
# Build zigc and check it against the seed on the same program.
#
# zigc is the ladder's most quotable artifact and, until this script, the
# only one nothing re-ran. README "zigc: the compiler as an ordinary
# process" records that it built clean, compiled a subject in about three
# seconds against a minute for the VM round trip, and produced a CDX
# byte-identical to the seed's -- but that measurement sat in prose with no
# runner behind it, in a tree where every other claim has one. A number
# nothing re-checks is a number that was true once.
#
# The check is the one gen_zigc_harness.py names in its own docstring, and
# it is stronger than a rung: "compile a program with the zig binary,
# compile the same program with the seed, and the two CDX files must be
# equal". No bare-metal arm runs this harness, so there is no truth file to
# diff -- the seed IS the oracle here, directly.
#
# What zigc is NOT, both from the README and worth re-reading before
# quoting any of this:
#   - not the driver. It stands in for opening.codex and skips proof
#     pruning, dropped-def handling and mode flags. A subject needing none
#     of those matches byte for byte; a subject needing them legitimately
#     differs, and that is two drivers disagreeing, not two compilers.
#   - not a native-code compiler. zigc runs natively; its OUTPUT is still a
#     kernel image, which is what the Codex compiler is for.
#
#   ./zigc_verify.sh [subject.codex]     default: ast/repro.codex
#
# The BUILD of zigc does not depend on the subject, and it is the expensive
# half: a seed compile of a 13.9 MB IR, the ring plug, and the transport.
# Screening candidate subjects used to pay all of it per candidate, which is
# why "find a subject that needs none of the driver's extras" -- a SEARCH --
# had been stuck. So the binary is cached beside its fingerprint, the way
# ast/ringplug.cdx already is: content, never mtime, and it says out loud
# when it reuses. `rm zigc` forces a rebuild; there is no flag for it.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/ast/oracle_lib.sh"

SUBJ="${1:-$T/ast/repro.codex}"
[ -s "$SUBJ" ] || { echo "no subject at $SUBJ"; exit 2; }
REPO="$(python3 "$T/ladder_root.py" codex)"
PLUG="$REPO/codex/plugs/zig/build-output/zig-plug.cdx"
# Presence check only: the ring arm re-bundles its own kernel, but a tree
# with no built plug at all has not had cycle.sh run and nothing below
# would work.
[ -s "$PLUG" ] || { echo "no built plug at $PLUG; run cycle.sh first"; exit 1; }

echo "### zigc_verify $(date +%H:%M:%S)"
echo "    subject $SUBJ"
echo "    plug    $PLUG"

cd "$T/ast"

# 1. The harness, then the subject. Same shape as every rung: generate,
#    remove the old one first so a generator crash cannot bundle yesterday's.
rm -f ZigcHarness.codex zigc-subject.codex
python3 gen_zigc_harness.py || { echo "HARNESS GEN FAILED"; exit 1; }
[ -s ZigcHarness.codex ] || { echo "HARNESS GEN FAILED: no ZigcHarness.codex"; exit 1; }
if ! bout=$(~/.local/pwsh/pwsh -NoProfile -File ./bundle_zigc.ps1 2>&1); then
    printf '%s\n' "$bout" | tail -5; echo "BUNDLE FAILED"; exit 1
fi
printf '%s\n' "$bout" | tail -1
[ -s zigc-subject.codex ] || { echo "BUNDLE FAILED: no zigc-subject.codex"; exit 1; }
python3 "$T/check_bundles.py" zigc || { echo "BUNDLE REFUSED"; exit 1; }

# 2. Subject to IR through the seed, then IR to zig through the plug.
#    decks=172 because this subject IS the passes_to_x86 chapter set with an
#    I/O boundary bolted on -- 55,746 lines against codexir's 55,745 -- and
#    native_build.sh compiles that size class with exactly this flag.
#    HOSTED_DECK_BYTES is a different deck: it is the one the BUILT zigc
#    gives itself at run time, baked into the harness source. This one is
#    the deck the SEED needs to compile the harness at all, and the first
#    run of this script passed no flags and was refused for it --
#    "CDX9002: Deck overflow in CHECK; deck floor exceeded", loudly and
#    before emitting anything, which is the honest direction to be wrong in.
python3 - <<'PY' || { echo "BLOB WRITE FAILED"; exit 1; }
src = open('zigc-subject.codex', 'rb').read()
open('zigc-ir-cce.blob', 'wb').write(b"IR-CCE decks=172\n" + src + b"\x04")
print(f"blob written ({len(src)} bytes of source), decks=172")
PY
cd "$T"

# The ring plug moves up here because it is the other half of what decides
# the binary, and it is cheap when current -- its own build re-bundles and
# compares a sha before spending any QEMU. Building it first means the
# fingerprint below can name the plug that WOULD transpile this subject,
# rather than the one that did, three runs ago.
bash "$T/ast/ringplug_build.sh" > ast/ringplug.build.log 2>&1 \
    || { echo "RING PLUG BUILD FAILED:"; tail -8 ast/ringplug.build.log; exit 1; }

# What the built zigc depends on, and nothing else: the bundled harness, the
# plug bundle that transpiles it, the seed that compiles it, and the zig that
# links it. Four shas, so a change to any of them misses and every other run
# hits. The subject is deliberately NOT in this list -- it arrives on stdin
# at step 4 and cannot reach the binary, which is the whole point.
#
# The list moved to tool_identity.py on 2026-08-29, when corpus_run.py needed
# the same four for the same reason. It was correct here first; what it did
# not have was a name.
want=$(python3 -c "import sys; sys.path.insert(0, '.'); import tool_identity; print(tool_identity.built_from('zigc') or '')")
[ -n "$want" ] || { echo "FINGERPRINT FAILED"; exit 1; }

if [ -x "$T/zigc" ] && [ "$(cat "$T/zigc.fp" 2>/dev/null)" = "$want" ]; then
    echo "    zigc already built from this harness, plug, seed and zig"
    echo "    ($(echo $want | head -c 12)) -- not rebuilding. rm zigc to force."
else
rm -f ast/zigc.ir ast/zigc.zig
python3 -u ring_compile.py ast/zigc-ir-cce.blob ast/zigc.ir 2>&1 | tail -5
[ -s ast/zigc.ir ] || { echo "COMPILE FAILED: no zigc.ir"; exit 1; }
# The RING, not TCP. arm_for sends ir_to_x86 and passes_to_x86 through the
# ring and everything else over TCP, and this subject is the passes_to_x86
# chapter set -- its IR is 13.9 MB. The first run of this script used the
# TCP arm and the guest dropped the connection at byte 7,770,000; the
# agreement retry then tried four chunk sizes and refused rather than
# picking one, which is the check doing its job. plug_run_ring takes the
# IR and the output and re-bundles the ring plug itself, so it needs no
# plug path.
python3 -u plug_run_ring.py ast/zigc.ir ast/zigc.zig > ast/zigc.transport.log 2>&1 \
    || { echo "TRANSPORT FAILED (ast/zigc.transport.log):"; tail -6 ast/zigc.transport.log; exit 1; }
[ -s ast/zigc.zig ] || { echo "TRANSPORT FAILED: no zigc.zig"; exit 1; }

# A marker means the plug refused a construct the subject actually uses,
# and it must stop the build. It must NOT count a prelude precondition --
# a defensive prong of a comptime type switch that nothing instantiates.
# findings/prelude-comptime-guards.txt is the list, and its own header
# records what counting them costs: cx_address_of "blocked every native
# build at the marker scan and printed a spurious gap: on every tier run,
# from a line in the prelude no subject reaches". A plain grep here did
# exactly that on the first run of this script. Read the same file
# native_build.sh and tier_run.py read, so a third spelling cannot drift
# from the two that already agree.
python3 - <<'PY' || { echo "read them before believing anything below"; exit 1; }
import pathlib, re, sys
MARKER = re.compile(r'@compileError\("zig plug: ([^"]*)"\)')
guards = {m.group(1) for ln in
          pathlib.Path('findings/prelude-comptime-guards.txt').read_text().splitlines()
          if ln.strip() and not ln.startswith('#')
          for m in [MARKER.search(ln)] if m}
zig = pathlib.Path('ast/zigc.zig').read_text()
marks = [m for m in MARKER.findall(zig) if m not in guards]
print(f"    zigc.zig: {len(zig.splitlines())} lines, "
      f"{len(marks)} plug refusals ({len(MARKER.findall(zig)) - len(marks)} prelude guards excluded)")
for m in marks:
    print(f"    PLUG REFUSED: {m}")
sys.exit(1 if marks else 0)
PY

# 3. Build it. The fingerprint is written LAST and only here, so a build
#    that died halfway leaves no stamp and the next run rebuilds rather
#    than trusting whatever binary is on disk.
rm -f "$T/zigc" "$T/zigc.fp"
zbuild_start=$SECONDS
zig build-exe ast/zigc.zig -femit-bin="$T/zigc" || { echo "ZIG BUILD FAILED"; exit 1; }
echo "    zig build-exe: $((SECONDS - zbuild_start))s"
printf '%s\n' "$want" > "$T/zigc.fp"
fi   # end of the build half; everything below depends on the SUBJECT

# 4. The two compiles of the same program.
run_start=$SECONDS
"$T/zigc" < "$SUBJ" > "$T/ast/zigc-out.cdx" || { echo "ZIGC RUN FAILED"; exit 1; }
zigc_secs=$((SECONDS - run_start))
python3 - "$SUBJ" <<'PY' || { echo "SEED BLOB FAILED"; exit 1; }
import sys
src = open(sys.argv[1], 'rb').read()
open('ast/seed-out.blob', 'wb').write(b"CDX map\n" + src + b"\x04")
PY
seed_start=$SECONDS
python3 -u ring_compile.py ast/seed-out.blob ast/seed-out.cdx 2>&1 | tail -3
seed_secs=$((SECONDS - seed_start))
[ -s ast/seed-out.cdx ] || { echo "SEED COMPILE FAILED: no seed-out.cdx"; exit 1; }

# 5. The verdict. Bytes first -- it is the whole claim.
echo
echo "    zigc  $(stat -c%s "$T/ast/zigc-out.cdx") bytes in ${zigc_secs}s"
echo "    seed  $(stat -c%s "$T/ast/seed-out.cdx") bytes in ${seed_secs}s"
if cmp -s "$T/ast/zigc-out.cdx" "$T/ast/seed-out.cdx"; then
    echo "### ZIGC PASS: the two CDX files are byte-identical"
else
    echo "### ZIGC DIFF: the CDX files differ -- this is a finding, not a flake."
    echo "    Before filing it, check whether this subject needs what zigc"
    echo "    deliberately drops (proof pruning, dropped-def handling, mode"
    echo "    flags): that is two DRIVERS disagreeing and is expected."
    cmp "$T/ast/zigc-out.cdx" "$T/ast/seed-out.cdx" | head -3
    exit 1
fi

# 6. And that the thing it emitted actually boots. Byte-identity already
#    implies it, so this is a cheap independent witness rather than a second
#    proof -- a CDX that matches and does not run would mean the comparison
#    is measuring the wrong bytes.
echo "--- booting zigc's own output"
python3 -c "import codex_vm; codex_vm.run_cdx('ast/zigc-out.cdx')" 2>&1 | tail -4
