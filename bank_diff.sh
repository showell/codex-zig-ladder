#!/bin/bash
# Diff the two newest banks (or any named pair): the per-rung cmp loop
# from README step 5, with the Update numbers derived instead of
# hand-edited per rebank (process review S4).
# Usage: bank_diff.sh [old new]   e.g. bank_diff.sh u47 u48
#
# Truths only. Banks carry a .truth.prov sidecar beside each truth since
# 2026-08-25, and a sidecar records the seed it was measured under, so it
# differs across banks by construction -- comparing them says nothing
# about whether a rung MOVED, which is the only question this asks.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
if [ $# -eq 2 ]; then OLD=$1; NEW=$2
else
    # "The two newest" is a question about WHEN a bank was taken, and this
    # answered it from the NAME: `truth/u*/` sorted -V. Update 50's push
    # was interim, so its bank is `seed-6cf4a8e0` -- not a uNN, on
    # purpose -- and the glob skipped the newest bank in the tree without
    # a word, leaving a bare bank_diff.sh comparing u48 to u49 and
    # reporting it as today's answer. Order by when each bank first
    # landed in git, which is the same thing a bank IS: a measurement,
    # committed once.
    set -- $(cd "$T/truth" && for d in */; do
                 d=${d%/}
                 ts=$(git -C "$T" log --format=%ct --diff-filter=A -- "truth/$d" | tail -1)
                 echo "${ts:-$(stat -c %Y "$T/truth/$d")} $d"
             done | sort -n | tail -2 | cut -d' ' -f2)
    OLD=$1; NEW=$2
    [ -n "$NEW" ] || { echo "fewer than two banks under truth/"; exit 1; }
fi
echo "diffing $OLD -> $NEW"
# What each bank's zig arms said, because "all rungs byte-identical" is a claim
# about BARE METAL and reads like a clean bill of health for the ladder. Every
# Update is banked now, red arms included (bank_truth.py's header has the
# reason), so the caveat has to travel with the comparison or a bank the ladder
# never agreed with is indistinguishable from one it did. Banks taken before
# ARMS existed say so rather than guessing.
for b in "$OLD" "$NEW"; do
    if [ -f "$T/truth/$b/ARMS" ]; then
        echo "  $b arms: $(head -1 "$T/truth/$b/ARMS")"
    else
        echo "  $b arms: not recorded (banked before ARMS)"
    fi
done
moved=0
for f in "$T/truth/$OLD/$OLD"-*.truth; do
    m=${f##*/$OLD-}
    if [ ! -f "$T/truth/$NEW/$NEW-$m" ]; then
        echo "  $m: MISSING from $NEW"; moved=1
    elif ! cmp -s "$f" "$T/truth/$NEW/$NEW-$m"; then
        echo "  $m: differs"; moved=1
    fi
done
[ $moved -eq 0 ] && echo "  all rungs byte-identical"
exit 0
