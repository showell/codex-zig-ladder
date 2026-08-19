#!/bin/bash
# Rebuild the plug once, then run EVERY milestone oracle against it.
# The ladder only means anything if the lower rungs stay green: an emitter
# change made for one phase reaches all of them, and a milestone that
# passed yesterday proves nothing about the plug built today.
set -e
. "$(dirname "$0")/oracle_lib.sh"
"$T/cycle.sh"
# Both plugs come from the same ZigEmitter, and a sweep that refreshed
# only one would report yesterday's emitter for whichever rungs use the
# other. Output captured, not discarded: a refusal used to send its
# PLUG COMPILE FAILED to /dev/null and kill the sweep with no message.
if ! ringout=$(bash "$T/ast/ringplug_build.sh" 2>&1); then
    printf '%s\n' "$ringout" | tail -10
    echo "RING PLUG BUILD FAILED -- sweep not run"
    exit 1
fi
echo "REBUILT"
fail=0
for m in $LADDER_UNITS; do
    echo "=== $m ($(unit_rungs $m)) ==="
    # NOT `arm | head`: under a pipe the exit status is head's, so a
    # failing rung reports nothing and the sweep still says it passed.
    out=$($(arm_for "$m") "$m" 2>&1) || fail=1
    # Sized for the worst case a unit can print: every subject it carries
    # showing fifteen lines of diff plus its heading. A unit whose second
    # subject's verdict fell off the end would read as a rung that never ran,
    # which is the failure this bound was widened to avoid.
    printf '%s\n' "$out" | head -34
    # A rung that says nothing is not a rung that passed. fibx once
    # exited 0 with its verdict truncated away, which reads identically
    # to a rung that never ran.
    case "$out" in
        *ORACLE*|*TRANSPORT\ FAILED*) ;;
        *) echo "NO VERDICT from $m -- treating as failure"; fail=1 ;;
    esac
    # pingpong carries a claim its arm diff cannot make: that emitting text
    # from stage 1's text reproduces it. Checked in the sweep so it cannot be
    # skipped by running the rung on its own.
    [ "$m" = pingpong ] && { pingpong_fixed_point || fail=1; }
done

# One census over every rung's diagnostics. The per-rung checks judge each
# compile; this is the only scale at which a pinned population means anything,
# and a class that fires benignly everywhere is exactly the shape CDX3006 had
# while it was hiding a real error from us.
echo "=== diagnostics census ==="
# The sweep's own units only. A bare *.diags also swept in whatever
# arith/irmem/guardprobe/codexir/ringplug last left behind, so the pinned
# counts measured a population that moved with which TOOLS had run lately,
# not with the source.
diag_files=""
for _u in $LADDER_UNITS; do
    diag_files="$diag_files $T/ast/${_u}-subject.cdx.diags $T/ast/${_u}.ir.diags"
done
python3 "$T/check_diags.py" --census $diag_files || fail=1

exit $fail
