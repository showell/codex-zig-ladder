#!/bin/bash
# One night, two branch verifications: the heap-unification PR's evidence
# package (cold-reviewed 2026-08-20, JUSTIFIED-WITH-CAVEATS -- the
# caveats are implemented here), then the refusal-gaps batch's. Built to
# run unattended and RETIRE once both PRs send (workaround-hygiene:
# delete this in the commit that records the second PR).
#
# Phases, each stamped, chain stops at the first failure:
#   A  heap ladder sweep: all-local allcycles under nr-heap (the cold
#      review's cheaper alternative -- same 14/14-vs-u48-bank evidence
#      as the two-venue path, ~25 min cheaper, and it exercises the TCP
#      transport under the branch, which the all-ring path never does)
#   B  heap census replay: natives from nr-heap, corpus_run --changed
#      WITHOUT --bank; the movement table printed here IS the PR's
#      evidence table. Gated on A being green.
#   B2 RSS rider: max RSS of one big rung's run under the branch
#      emitter (the design predicts max-over-definitions; the baseline
#      is JUSTIFICATIONS' ~240 MB arena figure)
#   C  gaps ladder sweep: allcycles under nr-gaps
#   D  gaps census replay: natives from nr-gaps, --changed, no --bank.
#      NOTE the movement here is (PR 76 + gaps batch) vs the verbatim
#      bank -- the gaps-only slice is read against the hunt's recorded
#      verbatim->76 movement.
#   E  restore: natives rebuilt from the pinned checkout, the tracked
#      corpus trio (transpile.json, gaps.json, run.jsonl) checked out
#      back to the banked state, native shas verified against census
#      meta.tools. If the chain dies mid-way, run this phase by hand.
#
# The RUN_MEM_CAP raise to 2200 MB this depends on is already committed
# (the heap emitter's 1.5 GiB reservation; see JUSTIFICATIONS).
set -u
T="$(cd "$(dirname "$0")" && pwd)"
PIN=$HOME/showell_repos/NewRepository
HEAP=$HOME/showell_repos/nr-heap
GAPS=$HOME/showell_repos/nr-gaps
STAMP() { echo "@@@@ $1 $(date +%H:%M:%S)"; }
trap 'echo "@@@@ CHAIN ENDED at phase $PHASE $(date +%H:%M:%S)"' EXIT

CODEX_ROOT="$PIN" . "$T/ast/oracle_lib.sh"
take_compute_lock

# Pre-flight, cheap and loud (cold review pre-launch checks).
PHASE=preflight; STAMP preflight
for repo in "$PIN" "$HEAP" "$GAPS"; do
    [ -z "$(git -C "$repo" status --porcelain)" ] || { echo "DIRTY TREE at $repo -- refusing"; exit 1; }
done
CODEX_ROOT="$HEAP" python3 "$T/seed_identity.py" | grep -q "Update 48" || { echo "nr-heap seed does not derive Update 48"; exit 1; }
CODEX_ROOT="$GAPS" python3 "$T/seed_identity.py" | grep -q "Update 48" || { echo "nr-gaps seed does not derive Update 48"; exit 1; }
[ "$(zig version)" = "0.16.0" ] || { echo "zig moved from 0.16.0; the movement tables would conflate toolchain with emitter"; exit 1; }

PHASE=A; STAMP "A: heap ladder sweep (allcycles, nr-heap)"
CODEX_ROOT="$HEAP" "$T/ast/allcycles.sh" > "$T/logs/overnight-heap-sweep.log" 2>&1 \
    || { echo "HEAP SWEEP RED -- see logs/overnight-heap-sweep.log:"; tail -12 "$T/logs/overnight-heap-sweep.log"; exit 1; }
grep -E "SWEEP: " "$T/logs/overnight-heap-sweep.log"

PHASE=B; STAMP "B: heap census replay"
CODEX_ROOT="$HEAP" "$T/native_build.sh" > "$T/logs/overnight-heap-natives.log" 2>&1 \
    || { echo "HEAP NATIVE BUILD FAILED:"; tail -8 "$T/logs/overnight-heap-natives.log"; exit 1; }
CODEX_ROOT="$HEAP" python3 "$T/corpus_run.py" --changed > "$T/logs/overnight-heap-census.log" 2>&1 \
    || { echo "HEAP CENSUS FAILED:"; tail -8 "$T/logs/overnight-heap-census.log"; exit 1; }
grep -A 60 "verdict diff" "$T/logs/overnight-heap-census.log" | head -64

PHASE=B2; STAMP "B2: heap RSS rider (fibx under the branch emitter)"
( cd "$T/ast" && ulimit -v $((2560 * 1024)) && /usr/bin/time -v timeout 900 zig run fibx.zig 2>&1 || true ) \
    | grep -E "Maximum resident|Elapsed" || echo "(rider inconclusive -- non-blocking)"

PHASE=C; STAMP "C: gaps ladder sweep (allcycles, nr-gaps)"
CODEX_ROOT="$GAPS" "$T/ast/allcycles.sh" > "$T/logs/overnight-gaps-sweep.log" 2>&1 \
    || { echo "GAPS SWEEP RED -- see logs/overnight-gaps-sweep.log:"; tail -12 "$T/logs/overnight-gaps-sweep.log"; exit 1; }
grep -E "SWEEP: " "$T/logs/overnight-gaps-sweep.log"

PHASE=D; STAMP "D: gaps census replay"
CODEX_ROOT="$GAPS" "$T/native_build.sh" > "$T/logs/overnight-gaps-natives.log" 2>&1 \
    || { echo "GAPS NATIVE BUILD FAILED:"; tail -8 "$T/logs/overnight-gaps-natives.log"; exit 1; }
CODEX_ROOT="$GAPS" python3 "$T/corpus_run.py" --changed > "$T/logs/overnight-gaps-census.log" 2>&1 \
    || { echo "GAPS CENSUS FAILED:"; tail -8 "$T/logs/overnight-gaps-census.log"; exit 1; }
grep -A 80 "verdict diff" "$T/logs/overnight-gaps-census.log" | head -84

PHASE=E; STAMP "E: restore to the pinned mainline"
CODEX_ROOT="$PIN" "$T/native_build.sh" > "$T/logs/overnight-restore-natives.log" 2>&1 \
    || { echo "RESTORE NATIVE BUILD FAILED:"; tail -8 "$T/logs/overnight-restore-natives.log"; exit 1; }
git -C "$T" checkout -- corpus/transpile.json corpus/gaps.json corpus/run.jsonl
python3 - "$T" <<'PY'
import hashlib, json, pathlib, sys
T = pathlib.Path(sys.argv[1])
meta = json.load(open(T / 'corpus' / 'census.json'))
want = meta.get('meta', {}).get('tools') or meta.get('tools')
for name in ('codexir', 'zigemit'):
    got = hashlib.sha256((T / 'native' / name).read_bytes()).hexdigest()[:16]
    exp = want[name][:16] if isinstance(want, dict) else None
    state = 'RESTORED' if got == exp else f'MISMATCH (want {exp})'
    print(f'  {name}: {got} {state}')
    if got != exp:
        raise SystemExit('restore did not restore; investigate before any census carries verdicts')
PY

PHASE=done; STAMP "chain complete"
CODEX_ROOT="$PIN" python3 "$T/ladder_status.py"
