#!/bin/bash
# The canary: the cheapest rungs through the droplet straw, FAIL-FAST --
# stop at the first red rung and say so. Its whole identity is answering
# "did I just break the emitter" in minutes (2-3 including the straw is
# the agreed budget; clear failure beats instant failure). Full coverage
# is sweep_long.sh's job; the all-local fallback is src/allcycles.sh.
#
# Assumes sweep_prep.sh ran since the last emitter edit; the per-job
# staleness checks in droplet_transpile.sh make forgetting that loud.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
. "$T/sweep_lib.sh"

# The split point is provisional until the rung_stamp timings from a few
# sweeps say where the knee is; these are the three cheapest by the
# README's cost figures.
CANARY_UNITS="lex parse desugar"

echo "### sweep_canary $(date +%H:%M:%S): $CANARY_UNITS"
for m in $CANARY_UNITS; do
    run_unit_remote "$m" || { echo "CANARY RED at $m -- stopping"; exit 1; }
done
echo "### CANARY GREEN $(date +%H:%M:%S)"
