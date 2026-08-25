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
# watch (D4). Every guest under the child is guarded at the door by
# codex_vm.launch; the parent asks the same question first so the answer
# reaches the terminal rather than a log nobody is tailing yet.
if [ -z "$REBANK_DETACHED" ]; then
    # This copy detaches and exits, so a refusal from the child lands in a
    # log nobody is tailing yet -- on 2026-08-24 that made a run look
    # launched for four minutes when it had already refused. Ask the same
    # question here, where there is still someone to tell. The child (and
    # every guest under it) is still guarded at the door by
    # codex_vm.launch; this is only about who hears the answer.
    python3 "$T/compute_lock.py" --probe || exit 1
    mkdir -p "$T/logs"
    log="$T/logs/rebank-$(date +%Y%m%d-%H%M%S).log"
    # LADDER_LAUNCHER_PID is gone with the check that needed it: the old
    # detector scanned ps for anything whose command line NAMED a job, so
    # a detached child saw its own launcher and refused itself (twice --
    # 2026-08-22 and 08-24). Nothing recognises jobs by name any more; a
    # guest is a qemu-system process, and this script is not one.
    REBANK_DETACHED=1 nohup "$0" > "$log" 2>&1 &
    echo "rebank detached (pid $!); watch with: tail -f $log"
    exit 0
fi

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
