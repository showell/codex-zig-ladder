#!/bin/bash
# The matched arm for bitcast.sh, at codex 13edc9a6 -- THE HEAD OF PR 100, not
# plain Update 53.
#
# That choice is the whole point of this script. zig-plug-real-bitcast is
# STACKED on zig-plug-real-conversions, so a sweep against plain U53 carries
# the f64 conversion pair (row 2.06, already measured and already sent) and
# the bitcast pair (row 2.07, what we are measuring) in the same rows, with
# nothing to tell them apart. Cutting the baseline at PR 100's head makes the
# bitcast commit the only variable between the two arms.
#
# The corpus sweeps codex/test/ top-level only, so codex/test/ops/real-bitcast-f64
# is in NEITHER population. Both arms see an identical program set.
set -u
cd "$(dirname "$0")" || exit 2
. ../env || exit 2
S="$SANDBOX"; ST="$S/CHAIN-STATUS.txt"
say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$ST"; }
FIXED="${FIXED_RUN:?set FIXED_RUN to the bitcast fixed-arm sandbox}"
say "BITCAST BASELINE -- codex $(git -C "$CODEX_ROOT" rev-parse --short HEAD), ladder $(git rev-parse --short HEAD)"
say "comparand: $FIXED"

# The base must be PR 100's head and nothing else. A silent drift here voids
# the comparison, and the sha is the only thing that can say so.
HEAD_SHA=$(git -C "$CODEX_ROOT" rev-parse HEAD)
if [ "$HEAD_SHA" != "13edc9a63bf977265981f7af8c3e94e4ea114105" ]; then
  say "BASE WRONG -- expected 13edc9a6 (PR 100 head), got ${HEAD_SHA:0:8}"; exit 1
fi
say "base confirmed 13edc9a6 = PR 100 head"

if ./native_build.sh > "$S/natives.log" 2>&1; then say "natives GREEN"; else say "natives RED -- see natives.log"; exit 1; fi
say "natives stamp: $(python3 -c 'import tiers_run; print(tiers_run.natives_stamp())' 2>/dev/null || echo '?')"

# THE ABSENCE CHECK, baseline-free: this arm must still REFUSE the two
# builtins. If it emits them the tree is not PR 100's head and the whole
# comparison is void. The refusal is ZigEmitter's generic one, at :1194.
say "--- absence check: PR 100 head must refuse real-to-bits and bits-to-real"
T="$FIXED/codex/codex/test/ops/real-bitcast-f64"
./native/codexir < "$T.codex" 2> "$S/rb.ir" > /dev/null \
  && ./native/zigemit < "$S/rb.ir" 2> "$S/rb.zig" > /dev/null
n_to=$(grep -c "no emitter for real-to-bits" "$S/rb.zig" 2>/dev/null || echo 0)
n_from=$(grep -c "no emitter for bits-to-real" "$S/rb.zig" 2>/dev/null || echo 0)
if [ "$n_to" -gt 0 ] && [ "$n_from" -gt 0 ]; then
  say "absence check GREEN -- refused: $n_to real-to-bits, $n_from bits-to-real markers"
else
  say "ABSENCE CHECK FAILED -- this arm does not refuse (real-to-bits $n_to, bits-to-real $n_from); it is not the baseline"; exit 1
fi

say "--- corpus at PR 100 head"
./corpus_run.py --run > "$S/corpus.log" 2>&1 && say "corpus swept" || say "corpus RED (exit $?)"
say "DONE -- now: ./two_arm_diff.py $S $FIXED"
