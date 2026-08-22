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
# watch (D4). The child takes the real lock; the parent only refuses
# early so a held lock is reported to the terminal, not to a log nobody
# is tailing yet.
if [ -z "$REBANK_DETACHED" ]; then
    flock -n "$T/.compute.lock" true || {
        echo "COMPUTE LOCK HELD -- another sweep/build/census owns this laptop; refusing"
        exit 1
    }
    mkdir -p "$T/logs"
    log="$T/logs/rebank-$(date +%Y%m%d-%H%M%S).log"
    # The detached child is re-parented to init, so the shell that launched
    # it is no longer an ancestor -- and that shell's command line names
    # this script, which is exactly what the lockless-job detector looks
    # for. Hand it our pid so it can excuse our ancestry (2026-08-22: the
    # u49 rebank refused itself at launch beside its own launcher).
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
