#!/bin/bash
# plugs row 2.07: do real-to-bits and bits-to-real work, and are they inert?
#
# THE FIXED ARM, at codex 2f7e7375 (zig-plug-real-bitcast). Its baseline is
# NOT plain Update 53 -- it is 13edc9a6, the head of PR 100, because this
# branch is STACKED on that one. Sweeping against plain U53 would measure the
# f64 conversion pair a second time and the bitcast pair together, and no
# reading of the rows could separate them. bitcast_baseline.sh is that arm.
#
# PREDICTION, written before it runs. Zero verdicts move and 614 of 614
# emitted .zig are BYTE-IDENTICAL. The two builtins are emitted only where a
# program calls them, no corpus program can call them today (they are refused
# on the baseline arm), and PR 98's tree-shaker -- absorbed into U53 -- means
# a part added to zig-prelude-parts reaches only the files that use it.
#
# WHAT WOULD CHANGE MY MIND, and each of these is a finding, not a nuisance:
#   - every .zig differs by the same two functions -> the shaker is NOT
#     shaking prelude parts, and every prelude edit to date has been
#     perturbing the whole corpus invisibly.
#   - a verdict moves -> a program reached these builtins by a path I did not
#     predict, and the scope claim in the commit message is wrong.
#   - some .zig differ and some do not -> read every one; that is the shape
#     that hid a real 2.02 instance inside the dup-arms run.
set -u
cd "$(dirname "$0")" || exit 2
. ../env || exit 2
S="$SANDBOX"; ST="$S/CHAIN-STATUS.txt"
say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$ST"; }
say "BITCAST FIXED -- codex $(git -C "$CODEX_ROOT" rev-parse --short HEAD), ladder $(git rev-parse --short HEAD)"

if ./native_build.sh > "$S/natives.log" 2>&1; then say "natives GREEN"; else say "natives RED -- see natives.log"; exit 1; fi
# Identifies these binaries within this run only: zig bakes the build
# directory into both, so no two sandboxes stamp alike even on identical
# source. The arm is established by the presence check below, which is
# behavioural and can actually fail.
say "natives stamp: $(python3 -c 'import tiers_run; print(tiers_run.natives_stamp())' 2>/dev/null || echo '?')"

# 1. THE PRESENCE CHECK, baseline-free: the new test must build AND agree with
#    its .expected. A gate that passes because the change did not execute looks
#    exactly like one that passes because it is right.
say "--- presence check: real-bitcast-f64 must build and match through the fixed plug"
T="$CODEX_ROOT/codex/test/ops/real-bitcast-f64"
if ./native/codexir < "$T.codex" 2> "$S/rb.ir" > /dev/null \
   && ./native/zigemit < "$S/rb.ir" 2> "$S/rb.zig" > /dev/null; then
  # THE EMITTED PROGRAM PRINTS TO STDERR, which is the plug's convention and
  # not an accident: cx_print_line writes there so a transpiled program's
  # output cannot be confused with the transpiler's own stdout. Comparing
  # `.expected` against stdout therefore diffs it against an EMPTY FILE and
  # reports a clean run as RED -- which is what this check did on its first
  # outing. dup.sh already knew; this did not mirror it.
  ( cd "$S" && "$HOME/zig-0.16.0/zig" run rb.zig > "$S/rb.stdout" 2> "$S/rb.err" )
  # A zig BUILD failure also lands on stderr, so this is not "trust stderr":
  # the diff below is what separates a program that ran from one that did not.
  if grep -q "no emitter for real-to-bits\|no emitter for bits-to-real" "$S/rb.zig"; then
    say "PRESENCE CHECK FAILED -- the plug still refuses the builtins; the change did not reach the build"; exit 1
  elif diff -u "$T.expected" "$S/rb.err" > "$S/rb.diff" 2>&1; then
    say "presence check GREEN -- builds and matches .expected ($(wc -l < "$S/rb.err") lines)"
  else
    say "PRESENCE CHECK RED -- built but DIFFERS from .expected; see rb.diff"
    head -20 "$S/rb.diff" | tee -a "$ST"
  fi
else
  say "PRESENCE CHECK RED -- codexir/zigemit failed; see rb.ir rb.zig"; exit 1
fi

# 2. Bare metal settles the .expected, with a control it cannot have influenced.
#    Already read once in 20260830T153846Z-u53-bitcast-expected; repeated here
#    so this sandbox's record stands on its own.
say "--- bare metal for the new test, with real-saturating-finite as CONTROL"
./bare_expected.py real-saturating-finite real-bitcast-f64 > "$S/bare.log" 2>&1 \
  && say "bare metal GREEN (control + new test both matched)" || say "bare metal RED -- see bare.log"

# 3. The corpus at head. This gate is the EXIT CODE and nothing more: it says
#    the sweep finished, NOT that the corpus held still. Inertness is
#    two_arm_diff.py against the baseline arm, and only that.
say "--- corpus at head (completion only; inertness comes from two_arm_diff.py)"
./corpus_run.py --run > "$S/corpus.log" 2>&1 && say "corpus swept" || say "corpus RED (exit $?)"

# 4. The tier SET, never --zig alone. The u50 close-out ran the zig arm by
#    itself and could not see a disagreement that STOPPED; that is how
#    finding 39's STALE row survived.
say "--- tier set"
./tiers_run.py > "$S/tiers.log" 2>&1 && say "tiers GREEN" || say "tiers RED (exit $?) -- see tiers.log"
say "DONE -- fixed arm complete"
