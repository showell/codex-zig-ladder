#!/bin/bash
# The full two-venue sweep: every unit through the droplet straw, zig
# build/run/diff local, full coverage with a running tally (a half-red
# sweep must be visible early, but when sweeping for real you want the
# complete verdict list -- fail-fast is sweep_canary.sh's identity, not
# this script's). Ends with the same diagnostics census allcycles.sh
# runs, over the same unit set.
#
# Assumes sweep_prep.sh ran since the last emitter edit; the per-job
# staleness checks in droplet_transpile.sh make forgetting that loud.
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/sweep_lib.sh"

fail=0
green=0
total=0
echo "### sweep_long $(date +%H:%M:%S)"
for m in $LADDER_UNITS; do
    total=$((total + 1))
    if run_unit_remote "$m"; then
        green=$((green + 1))
    else
        fail=1
    fi
    echo "--- tally: $green/$total green"
done

echo "=== diagnostics census ==="
diag_files=""
for _u in $LADDER_UNITS; do
    diag_files="$diag_files $T/src/${_u}-subject.cdx.diags $T/src/${_u}.ir.diags"
done
python3 "$T/check_diags.py" --census $diag_files || fail=1

if [ "$fail" -eq 0 ]; then
    echo "### SWEEP GREEN $(date +%H:%M:%S): $green/$total"
else
    echo "### SWEEP RED $(date +%H:%M:%S): $green/$total green"
fi
exit $fail
