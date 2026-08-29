#!/bin/bash
# Does the new census describe a tree it has never seen?
#
# rebank.sh's self-check proves a bank describes the tree that WROTE it,
# which is necessary and not sufficient: a fingerprint that quietly encoded
# the sandbox would pass it every time, exactly as the binary shas did. The
# claim that matters is cross-tree, and no run that stays in one tree can
# test it.
#
# So: a second tree, cut from the same two refs, bundled INDEPENDENTLY --
# its own pwsh, its own generator, its own bytes -- and asked whether the
# bank from the first tree is about it. Bundling boots no guest, so this
# costs about a minute and takes no compute lock.
#
#   CENSUS=<path to the banked census.json> ./census_confirm.sh
set -u
cd "$(dirname "$0")" || exit 2
. ../env || exit 2
CENSUS="${CENSUS:?set CENSUS to the census.json the other tree banked}"
S="$SANDBOX"

echo "confirming $CENSUS against a tree bundled here, from $(git -C "$CODEX_ROOT" rev-parse --short HEAD)"

# Bundle only. These are the three inputs tool_identity reads; none of the
# three steps starts a guest, and ringplug_build.sh is deliberately NOT used
# because its later half compiles.
cd ast
rm -f ringplug-source.codex zigemit-source.codex codexir-subject.codex
~/.local/pwsh/pwsh -NoProfile -File ./bundle_ringplug.ps1 | tail -1
~/.local/pwsh/pwsh -NoProfile -File ./bundle_zigemit.ps1  | tail -1
python3 gen_codexir_harness.py > /dev/null
~/.local/pwsh/pwsh -NoProfile -File ./bundle_codexir.ps1  | tail -1
cd ..

cp "$CENSUS" corpus/census.json
python3 - <<'PY'
import sys
sys.path.insert(0, '.')
import corpus_run as cr, tool_identity
bank = cr.load_bank()
want = (bank.get('meta') or {})['built_from']
now = tool_identity.natives()
for n in sorted(set(want) | set(now)):
    mark = 'agree' if want.get(n) == now.get(n) else '<- DIFFERS'
    print(f'  {n:9s} banked {want.get(n)}  here {now.get(n)}  {mark}')
verdict, _ = cr.bank_describes_this_tree(bank)
print(f'\nbank_describes_this_tree -> {verdict}')
# 'different' is a correct answer, not a malfunction, and this script cannot
# tell the two apart: it is handed a census and a tree and never learns
# whether they were meant to match. Cut from the banked refs, 'different'
# means the fingerprint failed to survive relocation. Cut from anything
# else, it means the check did its job. Say both and let the caller know
# which it asked for -- the alternative is a line that names a cause nobody
# computed, which is the habit this whole mechanism exists to break.
if verdict == 'same':
    print('SAME: the bank is about this tree, which it has never seen.')
    print('  Cut from the banked refs, that is the confirmation.')
else:
    print('DIFFERENT: this tree was not built from what the bank records.')
    print('  Cut from the banked refs, that is a FAILURE -- the identity did')
    print('  not survive relocation. Cut from any other ref, it is the check')
    print('  working: compare the refs before reading it either way.')
sys.exit(0 if verdict == 'same' else 1)
PY
