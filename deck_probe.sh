#!/bin/bash
# Measure the deck on the units that have one, and print the number.
#
# Four rungs run the x86-64 back end and therefore reserve a deck: fibx and
# scale (the fibx unit), whole and clamp (the whole unit). `emit-build`
# reserves defs*65536 + 25165824 for it and lifts the main frontier to exactly
# its top, and the plug's prelude reports what was actually used as a CX-DECK
# line on STDOUT -- see cx_deck_report in ZigEmitter.
#
# This is NOT a sweep and does not claim to be one. sweep_long.sh runs every
# unit and its GREEN means the whole ladder agreed; this runs two and answers
# one question, so it gets its own name rather than a units override on that
# script. A partial sweep reporting GREEN is exactly the kind of thing that
# gets believed later for more than it said.
#
# Transpile happens on the droplet (QEMU, the expensive half), zig build/run
# happens here -- the same split sweep_long uses, so the deck is exercised
# locally and the report lands in this script's stdout.
#
#   ./deck_probe.sh              fibx and whole
#   DECK_UNITS="fibx" ./deck_probe.sh
set -u
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/sweep_lib.sh"
take_compute_lock

units="${DECK_UNITS:-fibx whole}"
echo "### deck_probe $(date +%H:%M:%S) -- units: $units"
fail=0
for m in $units; do
    echo "########## $m"
    out=$(remote_ring_arm "$m" 2>&1); rc=$?
    # The verdict and the measurement, and nothing else: these runs print
    # thousands of lines of compiler output on the way past.
    printf '%s\n' "$out" | grep -E 'CX-DECK|ORACLE|MISMATCH|FAILED|STALE IR|UNPROVENANCED|panic:' || true
    if [ "$rc" -ne 0 ]; then
        # The panic MESSAGE, not the tail. A zig panic prints the message first
        # and then a stack trace, so `tail` reliably catches the trace and
        # misses the only line that says anything -- which is how `whole`'s
        # crossing numbers were lost on the first run.
        echo "  -- $m did not complete. The line that matters:"
        printf '%s\n' "$out" | grep -E 'panic:|CODEGEN-HALTED|MISMATCH|error:' | head -3 \
            || printf '%s\n' "$out" | tail -4
        fail=1
    fi
done

echo "### deck_probe done $(date +%H:%M:%S)"
echo
echo "Reading a CX-DECK line: headroom is reserved minus used, so NEGATIVE means"
echo "the deck overran and the guard should have refused the crossing. The"
echo "'reserved' field is a check on the instrument, not an output -- it should"
echo "equal defs*65536 + 25165824 for that unit, and if it does not then the"
echo "parked frontier is not the ceiling and the other fields mean nothing."
exit $fail
