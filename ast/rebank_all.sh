#!/bin/bash
# Re-bank every rung's truth arm, then sweep the plug against the fresh bank.
#
# A new seed invalidates BOTH arms: it compiles the bare-metal truth binary
# and it produces the IR-CCE the plug consumes. Running allcycles.sh against
# a stale bank compares a new plug to an old answer and means nothing, so
# this runs first after any seed change.
#
# The list is LADDER_UNITS in oracle_lib.sh, shared with allcycles.sh: what
# gets compiled is a unit, and a unit banks a truth file for every subject it
# carries. LADDER_RUNGS is still what bank_truth.py checks it has, which is the
# point of keeping both names -- twelve compiles have to produce fourteen
# truths, and a unit that quietly ran one subject would be caught there.
# This said `lex..pingpong` for a while after six more rungs existed, and
# allcycles.sh had its own copy that was missing clamp: two lists, two
# different ideas of what the ladder is, and a rung absent from one is a rung
# whose truth goes stale while its diff still reports green.
#
# Ordered cheapest rung first and stops on the first failure, because the
# failure modes here are shared -- a deck overflow or a ring-size wall hits
# every rung the same way, and finding that out on lex costs minutes where
# finding it out on pingpong costs hours.
set -e
. "$(dirname "$0")/oracle_lib.sh"

# An hours-class run does not belong to a terminal: run bare, this script
# relaunches itself detached into a timestamped log and prints where to
# watch (D4). The child takes the real lock; the parent runs both of its
# refusals first, so a held lock OR a job computing without one reaches
# the terminal rather than a log nobody is tailing yet.
if [ -z "$REBANK_DETACHED" ]; then
    flock -n "$T/.compute.lock" true || {
        echo "COMPUTE LOCK HELD -- another sweep/build/census owns this laptop; refusing"
        exit 1
    }
    # Both halves of the refusal have to reach the TERMINAL, and only this
    # copy can speak to it. On 2026-08-24 the lock was genuinely free, so
    # the check above passed and the run detached; the child then refused
    # on the evidence check and printed it into a log nobody was tailing
    # yet, and for four minutes the run looked launched and did not exist.
    # The child still checks -- it is the one that computes -- but the
    # answer is the same answer, taken here while there is someone to
    # tell.
    python3 "$T/compute_lock.py" --evidence || exit 1
    mkdir -p "$T/logs"
    log="$T/logs/rebank-$(date +%Y%m%d-%H%M%S).log"
    # The detached child is re-parented to init, so this copy is no longer
    # one of its ancestors -- and this copy IS executing rebank_all.sh, so
    # for the moment the two overlap the child sees a second rebank.
    # Hand it our pid to excuse that chain (2026-08-22: the u49 rebank
    # refused itself at launch beside its own launcher; the launching
    # SHELL used to match too, on the strength of naming the script, and
    # compute_lock.job_program ended that class on 2026-08-25).
    REBANK_DETACHED=1 LADDER_LAUNCHER_PID=$$ nohup "$0" > "$log" 2>&1 &
    echo "rebank detached (pid $!); watch with: tail -f $log"
    exit 0
fi
take_compute_lock

# The log's last line must say how far a dead run got (C1): "recorded",
# not "banked" -- the working truths are recorded here, the bank is
# bank_truth.py's act alone (D1).
recorded=0
started=$SECONDS
summary_done=""
trap '[ -z "$summary_done" ] && echo "### REBANK INTERRUPTED: $recorded/$(echo $LADDER_UNITS | wc -w) units recorded, $((SECONDS - started))s in"' EXIT

for m in $LADDER_UNITS; do
    rung_stamp "$m"
    truth_arm "$m"
    recorded=$((recorded + 1))
    echo "############ $m recorded ($recorded/$(echo $LADDER_UNITS | wc -w), $((SECONDS - started))s elapsed)"
done

summary_done=1
echo "############ all truths recorded ($((SECONDS - started))s); sweeping the plug against them"
"$T/ast/allcycles.sh"
