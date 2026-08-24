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
set -e
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/ast/oracle_lib.sh"
take_compute_lock

SUBJ="${1:-$T/ast/repro.codex}"
[ -s "$SUBJ" ] || { echo "no subject at $SUBJ"; exit 2; }
REPO="$(python3 "$T/ladder_root.py" codex)"
PLUG="$REPO/codex/plugs/zig/build-output/zig-plug.cdx"
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
rm -f ast/zigc.ir ast/zigc.zig
python3 -u ring_compile.py ast/zigc-ir-cce.blob ast/zigc.ir 2>&1 | tail -5
[ -s ast/zigc.ir ] || { echo "COMPILE FAILED: no zigc.ir"; exit 1; }
python3 -u plug_run_checked.py "$PLUG" ast/zigc.ir ast/zigc.zig > ast/zigc.transport.log 2>&1 \
    || { echo "TRANSPORT FAILED (ast/zigc.transport.log):"; tail -6 ast/zigc.transport.log; exit 1; }
[ -s ast/zigc.zig ] || { echo "TRANSPORT FAILED: no zigc.zig"; exit 1; }

# A marker means the plug refused a construct and said so. zigc built with
# none in the README's run; if that changes it is a finding, not a detail.
marks=$(grep -c '@compileError("zig plug:' ast/zigc.zig || true)
echo "    zigc.zig: $(wc -l < ast/zigc.zig) lines, $marks plug refusal markers"
[ "$marks" -eq 0 ] || { echo "PLUG REFUSED $marks constructs -- read them before believing anything below"; exit 1; }

# 3. Build it.
rm -f "$T/zigc"
zbuild_start=$SECONDS
zig build-exe ast/zigc.zig -femit-bin="$T/zigc" || { echo "ZIG BUILD FAILED"; exit 1; }
echo "    zig build-exe: $((SECONDS - zbuild_start))s"

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
