#!/bin/bash
# Take the corpus census at a release, with a SOURCE-DERIVED tool identity.
#
# The bank on disk before this was 2026-08-27 and recorded `tools` as binary
# shas, which name the directory a binary was built in as much as anything
# else. It could never describe another tree, so every run since printed
# THE BANK IS NOT ABOUT THIS TREE and no verdict diff was evidence. That is
# what cost the 2026-08-29 dup-arms change a whole second arm to settle a
# question a bank should have answered.
#
# tool_identity fixed the identity; this takes the bank that uses it.
#
# BANK AT THE RELEASE, NOT AT OUR STACK. The census is the baseline our PRs
# are measured against, so it has to be a tree Damian would recognise --
# plain upstream, no unlanded work underneath. A bank taken on our stack
# would silently fold our own branches into every future comparison.
set -u
cd "$(dirname "$0")" || exit 2
. ../env || exit 2
S="$SANDBOX"; ST="$S/CHAIN-STATUS.txt"
say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$ST"; }

say "REBANK -- codex $(git -C "$CODEX_ROOT" rev-parse --short HEAD), ladder $(git rev-parse --short HEAD)"

if ./native_build.sh > "$S/natives.log" 2>&1; then say "natives GREEN"; else say "natives RED"; exit 1; fi

# The fingerprints, before the bank is written. Sandbox B recomputes these
# from its own bundling and they must agree: that is the property the whole
# change rests on, and it is not tested by anything that stays in one tree.
say "built_from: $(python3 tool_identity.py | tr '\n' ' ')"

say "--- corpus at the release, banking"
./corpus_run.py --run --bank > "$S/corpus.log" 2>&1 && say "corpus swept" || { say "corpus RED (exit $?)"; exit 1; }

# PRESENCE CHECK, and it is the one that has never passed. A bank written by
# this tree must describe this tree. Before tool_identity the answer was
# 'different' by construction, whatever anything did.
python3 - <<'PY' | tee -a "$ST"
import sys
sys.path.insert(0, '.')
import corpus_run as cr
bank = cr.load_bank()
meta = bank.get('meta') or {}
if 'built_from' not in meta:
    print('BANK HAS NO built_from -- it was written by the old code'); sys.exit(1)
if 'tools' in meta:
    print('BANK STILL CARRIES `tools` -- the old field was not dropped'); sys.exit(1)
verdict, _ = cr.bank_describes_this_tree(bank)
print(f'bank meta: date {meta["date"]}, base {meta.get("base")}')
print(f'bank built_from: {meta["built_from"]}')
print(f'SELF-CHECK: bank_describes_this_tree -> {verdict}')
sys.exit(0 if verdict == 'same' else 1)
PY
[ "${PIPESTATUS[0]}" = 0 ] && say "self-check GREEN -- the bank describes the tree that wrote it" \
                           || { say "SELF-CHECK FAILED"; exit 1; }
say "DONE -- carry corpus/census.json back"
