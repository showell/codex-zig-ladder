#!/bin/bash
# The census canary: seven corpus programs that between them CALL every
# builtin the heap branch changed. Same idea as sweep_canary.sh -- minutes,
# not hours, answering "did we break something the ladder cannot see".
#
# Why these seven, and why the census at all. The ladder's twelve units are
# blind in places the corpus is not: `address-of`'s real call sites are
# rooted in `opening.codex`, which no rung can bundle; `text-replace` has
# zero call sites in any unit. The corpus is ~572 language tests with
# hand-written `.expected` files, written by someone who knew nothing about
# this plug, so it exercises exactly what we would not think to.
#
# 61 of the 572 directly call a changed builtin, and 28 of those 61 also
# TRANSPILE CLEAN -- which is the criterion that matters, because a program
# the emitter cannot translate never runs and covers nothing. The first
# version of this set was chosen on "calls a changed builtin" alone and five
# of its seven turned out to be blocked by unrelated gaps (`atomic-*`,
# `process-*`, `poke-16`, `map-list`, `bit-not`), so it delivered two
# verdicts, not seven. These six are drawn from the 28, each has a
# hand-written `.expected`, and together they reach every changed builtin
# that any clean program can reach:
#
#   deck-bracket-contract   __deck-set, __deck-enter          expect match
#   text-helper-native      text-replace, text-split          expect match
#   frameless-leaf-probe    bit-shl, bit-shru                 expect match
#   text-append-alias       char-code                         expect match
#   shadow-builtin-fold     substring                         expect DIFFER
#
# Four of the five are expected to MATCH, and were chosen that way: a rung
# that is red before you start cannot tell you anything by being red. Each
# carried verdict `match` in the 08-20 bank and still transpiles clean.
# `textscan-test` held the char-code slot first and is a standing `refused`
# (`expected type 'i64', found 'bool'`, shared with `stringutils-test` and
# `tls13-schedule`); `text-append-alias` covers the same builtin and is
# green, so it took the slot.
#
# `shadow-builtin-fold` is the exception and is kept deliberately. It is the
# ONLY program in 572 that calls `substring`, transpiles, and has an oracle
# -- the other two are `lang-smoke` (blocked on map-list) and
# `substring-over-read` (no `.expected`). It reports
# `want 99/99/77, got 3/3/5`: builtin interception ignoring user shadowing,
# which was found and FIXED on 2026-08-20 as `993d9f8b`, went upstream in
# PR 76, and PR 76 IS STILL UNABSORBED -- so the fix is on `u47-rebank` and
# not on the u48 pin this branch is cut from. The red is expected, external,
# and stable. Do not re-investigate it; if it ever stops differing, PR 76
# landed. The signal from this rung is the runner's `no verdict moved vs
# bank` line, not its tally.
#
# Three criteria, and the third was learned the hard way: calls a changed
# builtin, TRANSPILES CLEAN, and is not on hardware-only.txt. A first
# re-derivation included `smp-arm64-boot` for `peek-qword` -- clean, has an
# oracle, and classifies instead of running, so it covered nothing.
#
# THREE CHANGED BUILTINS ARE DARK HERE, and saying so is the point of this
# comment:
#
#   address-of  finding 31 / b85f1b98. `atomic-smoke` is the ONLY program in
#               572 that calls it, and it does not transpile (no emitter for
#               atomic-load/store/add/cas/exchange, memory-fence). The census
#               cannot witness this change at all until those land.
#   bit-shr     `tco-bitop-loop` is the only caller and is blocked by a
#               single missing builtin, `bit-not`. Least-cost unblock on the
#               board. Not urgent: all three shifts share 2a1177fa's masking
#               fix, and `probe-shift-count` already confirms all three
#               against the bare-metal gold column.
#   peek-qword  ten callers and not one of them is reachable: every single
#               one is either hardware-only or blocked on port/process/exc
#               builtins. Finding 26 has no census witness, and unlike the
#               other two that is not one missing emitter away.
#
# `__list-with-capacity` and `__linked-list-empty` are called by NO corpus
# program, so the branch's widest-reach change (17329ed9, 85 call sites) has
# no census witness either -- the ladder's rungs are its only coverage.
#
# Needs natives built from the plug under test -- corpus_run.py runs on
# native/codexir and native/zigemit, and a stale pair answers for the wrong
# emitter. native_build.sh in a sandbox, and it is the expensive step.
#
# The set is deliberately not derived at runtime: it was computed once from
# the changed builtins, and a set that silently re-derives itself is a set
# nobody checks. When the branch changes which builtins it touches, redo the
# count and edit this list -- and redo it against transpiles-clean, not
# against the call sites alone.
set -e
T="$(cd "$(dirname "$0")" && pwd)"

CANARY_PROGRAMS="deck-bracket-contract,text-helper-native,frameless-leaf-probe,text-append-alias,shadow-builtin-fold"

echo "### census_canary $(date +%H:%M:%S)"
python3 -u "$T/corpus_run.py" --run --only "$CANARY_PROGRAMS"
