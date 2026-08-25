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
    set -- $(ls -d "$T"/truth/u*/ 2>/dev/null | xargs -n1 basename | sort -V | tail -2)
    OLD=$1; NEW=$2
    [ -n "$NEW" ] || { echo "fewer than two banks under truth/"; exit 1; }
fi
echo "diffing $OLD -> $NEW"
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
