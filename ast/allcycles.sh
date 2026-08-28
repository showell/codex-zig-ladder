#!/bin/bash
# Rebuild the plug once, then run EVERY milestone oracle against it.
# The ladder only means anything if the lower rungs stay green: an emitter
# change made for one phase reaches all of them, and a milestone that
# passed yesterday proves nothing about the plug built today.
set -e
. "$(dirname "$0")/oracle_lib.sh"

# A detached sweep that dies must not be indistinguishable from one still
# running: the trap makes the log's last line say how far it got (C1).
rungs_green=0
rungs_total=$(echo $LADDER_RUNGS | wc -w)
started=$SECONDS
summary_done=""
trap '[ -z "$summary_done" ] && echo "### SWEEP INTERRUPTED: $rungs_green/$rungs_total rungs green, $((SECONDS - started))s in"' EXIT

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
# A sweep needs a per-sandbox <unit>.ir, which a FRESH sandbox does not
# have; the arms refuse without one. Making those files is the truth arm's
# first half, so this used to mean a full rebank -- bare-metal binary and
# subject run included -- before the sweep could start. ensure_ir.sh does
# the half that is actually needed. It is silent when the .ir is already
# good, so a sweep after a rebank looks exactly as it did.
# A fresh sandbox is missing THREE things, and the list was arrived at by
# running it rather than by reasoning: the generated harness, the .ir to
# transpile, and the truths to diff against. ensure_ir.sh below covers the
# first two -- the harness only after a first run handed pwsh a
# LexHarness.codex that was never there. The truths are already banked,
# so restore them rather than re-measuring; restore_truths.py copies each
# banked sidecar with its truth and then checks it through the same gate
# the arms use, so a seed that does not match refuses here with a name
# instead of rung by rung an hour in. Silent and harmless when the working
# truths are already there.
if ! python3 "$T/restore_truths.py" > "$T/ast/.restore.log" 2>&1; then
    # Not fatal on its own: a bank with no sidecars (taken before
    # 2026-08-24) cannot be restored from, and a tree that already has its
    # truths does not need to be. The arms refuse individually and loudly
    # if what is on disk is not usable, which is the check that matters.
    echo "--- restore_truths: nothing restored (see ast/.restore.log)"
    sed 's/^/    /' "$T/ast/.restore.log" | head -8
else
    sed 's/^/    /' "$T/ast/.restore.log" | grep -E 'restored|NOTE|harness' | head -6
fi

ir_rebuilt=""
for m in $LADDER_UNITS; do
    if [ ! -s "$T/ast/${m}.ir" ] \
       || ! python3 "$T/truth_prov.py" check-ir "$m" "$(mode_flags $m)" >/dev/null 2>&1; then
        bash "$T/ast/ensure_ir.sh" "$m" || { echo "ENSURE_IR FAILED for $m"; exit 1; }
        ir_rebuilt="$ir_rebuilt $m"
    fi
done

for m in $LADDER_UNITS; do
    rung_stamp "$m"
    # NOT `arm | head`: under a pipe the exit status is head's, so a
    # failing rung reports nothing and the sweep still says it passed.
    out=$($(arm_for "$m") "$m" 2>&1) || fail=1
    # Counted per RUNG, not per unit: each subject prints exactly one
    # ORACLE PASS, so a composite unit with one red subject still credits
    # the green one and the tally matches what a tag would claim.
    rungs_green=$((rungs_green + $(printf '%s\n' "$out" | grep -c 'ORACLE PASS' || true)))
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
    # ir_to_codex_roundtrip carries a claim its arm diff cannot make: that
    # emitting text from stage 1's text reproduces it. Checked in the sweep
    # so it cannot be skipped by running the rung on its own.
    [ "$m" = ir_to_codex_roundtrip ] && { roundtrip_fixed_point || fail=1; }
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
# The pinned counts were taken over BOTH halves of every unit. ensure_ir.sh
# writes no <unit>-subject.cdx.diags, so a sweep that rebuilt any IR is
# judging a smaller population, and a smaller population under-counts every
# pin -- which reads as drift and is not. Say which sweep this was instead
# of comparing anyway.
#
# Measured on Update 52, and it qualifies the sentence above: the OTHER half
# does not exist either. All twelve <unit>.ir.diags were absent, because the
# IR arm runs passes=text-plug and emits no diagnostics at all, so there is
# nothing to write. "Both halves" has described one half for as long as it
# has been written here. Nothing is wrong with the counts -- they were pinned
# over the same one half -- but a reader was entitled to think otherwise.
# bank_diags.py records the absent files on every bank so this stays visible
# rather than being rediscovered.
#
# The real answer is still a banked diagnostics set, and it now exists:
# bank_diags.py, banked under diags/<slug>.txt, diffed with --diff.
if [ -n "$ir_rebuilt" ]; then
    echo "CENSUS NOT COMPARED: the IR for$ir_rebuilt was rebuilt by"
    echo "  ensure_ir.sh, so no bare-metal .diags exists for those units and"
    echo "  this population is not the one the counts are pinned over. Run"
    echo "  ast/rebank_all.sh for a census that can be believed."
else
    python3 "$T/check_diags.py" --census $diag_files || fail=1
fi

summary_done=1
echo "SWEEP: $rungs_green/$rungs_total rungs green ($((SECONDS - started))s elapsed)"
# What a reader must not have to reconstruct: whether the IR under this
# sweep came from the run that also measured bare metal, or was rebuilt
# here from source.
[ -n "$ir_rebuilt" ] && echo "  IR REBUILT for$ir_rebuilt -- bare metal was NOT re-measured in this sweep"
# The two claims a sweep can make are not the same one. Against truths this
# run measured, green says bare metal and the plug agree today. Against
# truths restored from the bank, green says the plug still reproduces the
# BANK -- which is the ladder's question, but it is not a statement about
# bare metal, and a log read next week must not have to infer which it was.
[ -s "$T/ast/.restore.log" ] && grep -q '^restored [1-9]' "$T/ast/.restore.log" \
    && echo "  TRUTHS RESTORED FROM THE BANK -- this sweep says the plug still reproduces the bank, NOT that bare metal was re-measured"
# A green sweep records truths and diffs in the working tree and nothing
# else: "banked" is bank_truth.py's word, and a session that reads this
# log after a crash must not believe the bank was taken (D1).
[ "$fail" -eq 0 ] && echo "NOT BANKED -- run bank_truth.py to take the bank"
exit $fail
