#!/bin/bash
# Verify the multi-subject merge against a bank, and nothing else.
#
# The merge changed HOW the two big units are compiled and run, not WHAT each
# subject compiles, so every rung they carry must come back byte-identical to
# the bank. That makes this the rare expensive run with a predicted answer:
# anything other than "identical" is a finding rather than a number to write
# down.
#
#   ast/verify_merge.sh [bank]      default bank: u46
#
# Not part of the sweep. allcycles.sh compares the arms against each other;
# this compares the truth side against an EARLIER truth side, which is the only
# way to see that a change to the machinery moved an answer it should not have.
set -u
. "$(dirname "$0")/oracle_lib.sh"
BANK="${1:-u46}"
BANKDIR="$T/truth/$BANK"
[ -d "$BANKDIR" ] || { echo "no bank at $BANKDIR"; exit 2; }

# The bank is a set taken under one seed. Comparing against it while the tree
# holds another is comparing two compilers and calling the difference a
# regression, so the seed is checked before anything runs for half an hour.
banked_seed=$(head -1 "$BANKDIR/SEED" 2>/dev/null | tr 'A-Z' 'a-z')
now_seed=$(sha256sum "$REPO/seed/Codex.cdx" | cut -c1-16)
case "$banked_seed" in
    "${now_seed}"*) ;;
    *) echo "SEED MISMATCH: bank $BANK was taken under ${banked_seed:0:16}, tree holds $now_seed"
       echo "  a diff against this bank would be measuring the Update, not the merge"
       exit 2 ;;
esac

fail=0
for u in fibx whole; do
    echo "############ $u ($(unit_rungs $u))"
    truth_arm "$u" || { echo "TRUTH ARM FAILED for $u"; exit 1; }
done

echo "############ comparing every rung against bank $BANK"
for u in fibx whole; do
    for m in $(unit_rungs $u); do
        if diff -q "$BANKDIR/$BANK-$m.truth" "$T/ast/$m.truth" > /dev/null 2>&1; then
            echo "  IDENTICAL $m"
        else
            echo "  MOVED     $m -- $(diff "$BANKDIR/$BANK-$m.truth" "$T/ast/$m.truth" | grep -c '^[<>]') lines differ"
            diff "$BANKDIR/$BANK-$m.truth" "$T/ast/$m.truth" | head -8
            fail=1
        fi
    done
done

echo "############ zig arms, one per unit"
for u in fibx whole; do
    echo "=== $u ==="
    $(arm_for "$u") "$u" || fail=1
done

[ $fail = 0 ] && echo "MERGE VERIFIED: four rungs, two compiles, every answer unchanged"
exit $fail
