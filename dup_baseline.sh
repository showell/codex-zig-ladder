#!/bin/bash
# The matched arm for dup.sh: plain Update 53, so the shadowed-arm drop is the
# ONLY variable between the two corpus runs.
#
# dup.sh swept the corpus at head and could say only that the sweep finished.
# Its verdict diff went against a bank from 2026-08-27, two Updates back, and
# ZigEmitter.codex itself moved in between -- so those rows carry the base
# change and ours together and cannot be told apart. Re-banking at the FIXED
# tree would not fix that; it would make the bank equal the run by
# construction and measure nothing at all. What settles it is a second run
# against the same 614 programs with the plug reverted, which is this.
#
# The corpus sweeps codex/test/ top-level only, so test/ops/match-shadowed-arm
# is in NEITHER population. Both arms see an identical program set and the
# emitter is the only thing that differs.
#
# PREDICTION, written before it runs: ZERO verdicts move. zig-arm-shadowed
# fires only where an earlier trivially-guarded arm names the same switch
# value, which is exactly the shape zig rejects with `duplicate switch value`,
# so no program that BUILT at plain U53 can be touched. A moved row falsifies
# that and has to be read before the PR's table is written.
set -u
cd "$(dirname "$0")" || exit 2
. ../env || exit 2
S="$SANDBOX"; ST="$S/CHAIN-STATUS.txt"
say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$ST"; }
FIXED="${FIXED_RUN:?set FIXED_RUN to the dup-arms sandbox}"

say "BASELINE -- codex $(git -C "$CODEX_ROOT" rev-parse --short HEAD), ladder $(git rev-parse --short HEAD)"
say "comparand: $FIXED (codex 88daa0a8, natives 291590b54956)"

if ./native_build.sh > "$S/natives.log" 2>&1; then say "natives GREEN"; else say "natives RED"; exit 1; fi
STAMP=$(python3 -c 'import tiers_run; print(tiers_run.natives_stamp())' 2>/dev/null || echo '?')
say "natives stamp: $STAMP"
if [ "$STAMP" = "291590b54956" ]; then say "STAMP MATCHES THE FIXED ARM -- this is not a baseline"; exit 1; fi

# THE PRESENCE CHECK, baseline-free: this arm must still REFUSE the new test.
# If it builds, the tree is not plain U53 and the whole comparison is void.
say "--- presence check: plain U53 must refuse match-shadowed-arm"
MSA="$FIXED/codex/codex/test/ops/match-shadowed-arm.codex"
./native/codexir < "$MSA" 2> "$S/msa.ir" > /dev/null \
  && ./native/zigemit < "$S/msa.ir" 2> "$S/msa.zig" > /dev/null
( cd "$S" && "$HOME/zig-0.16.0/zig" run msa.zig > "$S/msa.out" 2>&1 )
if grep -q "duplicate switch value" "$S/msa.out"; then
  say "presence check GREEN -- refused, $(grep -c 'duplicate switch value' "$S/msa.out") duplicate-switch errors"
else
  say "PRESENCE CHECK FAILED -- plain U53 did not refuse; this arm is not the baseline"; exit 1
fi

say "--- corpus at plain U53"
./corpus_run.py --run > "$S/corpus.log" 2>&1 && say "corpus swept" || say "corpus RED (exit $?)"
say "DONE -- diff $S/corpus.log against $FIXED/corpus.log"
