#!/bin/bash
# plugs row 2.02: does dropping a shadowed match arm work, and is it inert?
set -u
cd "$(dirname "$0")" || exit 2
. ../env || exit 2
S="$SANDBOX"; ST="$S/CHAIN-STATUS.txt"
say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$ST"; }
say "DUP-ARMS -- codex $(git -C "$CODEX_ROOT" rev-parse --short HEAD), ladder $(git rev-parse --short HEAD)"
if ./native_build.sh > "$S/natives.log" 2>&1; then say "natives GREEN"; else say "natives RED"; exit 1; fi
# The stamp identifies THESE binaries for the rest of this run. It is not
# comparable to any other run's: the build directory is baked into both
# natives and every sandbox has a different one. What settles "did the fix
# reach the build" is gate 1 below, which is behavioural.
say "natives stamp: $(python3 -c 'import tiers_run; print(tiers_run.natives_stamp())' 2>/dev/null || echo '?')"

# 1. THE PRESENCE CHECK: the new test must build and run now. It fails with two
#    'duplicate switch value' errors against the plug as Update 53 ships it.
say "--- the new test through the fixed plug"
./native/codexir < "$CODEX_ROOT/codex/test/ops/match-shadowed-arm.codex" 2> "$S/msa.ir" > /dev/null \
  && ./native/zigemit < "$S/msa.ir" 2> "$S/msa.zig" > /dev/null \
  && (cd "$S" && "$HOME/zig-0.16.0/zig" run msa.zig > "$S/msa.out" 2>&1 || "$HOME/zig-0.16.0/zig" run msa.zig 2> "$S/msa.out" > /dev/null)
if grep -q "duplicate switch value" "$S/msa.out" 2>/dev/null; then say "TEST STILL REFUSED -- the fix did not take"; else say "test builds; output in msa.out"; fi

# 2. bare metal settles the .expected, with a control it cannot have influenced
say "--- bare metal for the new test, with real-saturating-finite as CONTROL"
./bare_expected.py real-saturating-finite match-shadowed-arm > "$S/bare.log" 2>&1 \
  && say "bare metal GREEN (control + new test both matched)" || say "bare metal RED -- see bare.log"

# 3. the corpus, at head. This gate is the EXIT CODE of corpus_run.py and
#    nothing more: it says the sweep completed, NOT that the corpus held still.
#    Inertness needs a bank taken from this same tree, and reading the verdict
#    diff against an older one measures the base change too. corpus_run.py says
#    so itself, above its rows -- read the HEAD of the log, not the tail.
say "--- corpus at head (completion only; see the log's banner for the bank)"
./corpus_run.py --run > "$S/corpus.log" 2>&1 && say "corpus swept" || say "corpus RED (exit $?)"
say "DONE"
