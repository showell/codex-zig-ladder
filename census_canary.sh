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
# 61 of the 572 directly call a changed builtin. These seven cover all
# eleven changed builtins with nothing left uncovered, and each has an
# oracle:
#
#   lang-smoke              bit-shl, substring, text-split
#   tco-bitop-loop          all three shifts
#   deck-bracket-contract   __deck-set, __deck-enter
#   files-parse             bit-shru, char-code
#   arm64-proc-cells        bit-shl, peek-qword
#   atomic-smoke            address-of        (the ONLY corpus program that
#                                              calls it -- finding 31's only
#                                              witness in 572)
#   stringutils-test        text-replace, __list-with-capacity
#                                             (the only venue that can
#                                              falsify 2202d3e5)
#
# Needs natives built from the plug under test -- corpus_run.py runs on
# native/codexir and native/zigemit, and a stale pair answers for the wrong
# emitter. native_build.sh in a sandbox, and it is the expensive step.
#
# The set is deliberately not derived at runtime: it was computed once from
# the changed builtins, and a set that silently re-derives itself is a set
# nobody checks. When the branch changes which builtins it touches, redo the
# count and edit this list.
set -e
T="$(cd "$(dirname "$0")" && pwd)"

CANARY_PROGRAMS="lang-smoke,tco-bitop-loop,deck-bracket-contract,files-parse,arm64-proc-cells,atomic-smoke,stringutils-test"

echo "### census_canary $(date +%H:%M:%S)"
python3 -u "$T/corpus_run.py" --run --only "$CANARY_PROGRAMS"
