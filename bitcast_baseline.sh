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
# `grep -c` PRINTS 0 and EXITS 1 on no match, so `|| echo 0` appends a second
# zero and the comparison below dies on "0\n0". The count alone is correct.
n_to=$(grep -c "no emitter for real-to-bits" "$S/rb.zig" 2>/dev/null)
n_from=$(grep -c "no emitter for bits-to-real" "$S/rb.zig" 2>/dev/null)

# ONLY THE OUTER CALL CAN SURFACE A MARKER, and demanding both was demanding
# something impossible. Every `bits-to-real` in real-bitcast-f64 sits INSIDE a
# `real-to-bits` call; the emitter refuses the outer expression and never
# descends into the argument, so the test yields 12 real-to-bits markers and
# necessarily ZERO for bits-to-real however unimplemented it is. The first cut
# of this check read that structural zero as "the arm is not the baseline".
if [ "$n_to" -gt 0 ]; then
  say "absence check A GREEN -- real-to-bits refused, $n_to markers"
else
  say "ABSENCE CHECK A FAILED -- real-to-bits is not refused here; this is not the baseline"; exit 1
fi

# So bits-to-real gets its own probe, where it is the OUTERMOST refusable call.
# `real-to-int` is implemented at PR 100's head -- that is what this branch is
# stacked on -- so the outer call emits and the inner one is left to answer for
# itself. On the fixed arm this same probe prints `probe 0`.
cat > "$S/probe.codex" <<'PROBE'
Chapter: BitsToRealProbe

  cites Foreword chapter Console

Section: Report

  opening : [Console] Nothing
  opening = act
    print-line-uni ("probe " & show (real-to-int (bits-to-real #0)))
  end
PROBE
./native/codexir < "$S/probe.codex" 2> "$S/probe.ir" > /dev/null \
  && ./native/zigemit < "$S/probe.ir" 2> "$S/probe.zig" > /dev/null
n_probe=$(grep -c "no emitter for bits-to-real" "$S/probe.zig" 2>/dev/null)
if [ "$n_probe" -gt 0 ]; then
  say "absence check B GREEN -- bits-to-real refused in the probe, $n_probe markers"
else
  say "ABSENCE CHECK B FAILED -- bits-to-real is not refused here; this is not the baseline"; exit 1
fi

say "--- corpus at PR 100 head"
./corpus_run.py --run > "$S/corpus.log" 2>&1 && say "corpus swept" || say "corpus RED (exit $?)"
say "DONE -- now: ./two_arm_diff.py $S $FIXED"
