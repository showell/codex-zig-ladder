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

for m in $LADDER_UNITS; do
    echo "############ re-banking $m ($(unit_rungs $m))"
    truth_arm "$m"
    echo "############ $m banked"
done

echo "############ all banked; sweeping the plug against the new bank"
"$T/ast/allcycles.sh"
