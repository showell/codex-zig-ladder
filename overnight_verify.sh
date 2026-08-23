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
# PHASE_FROM=C runs the gaps half alone (phases C, D, E). The two branches
# are independent, so the heap half going red on 2026-08-21 does not hold
# the gaps PR's evidence hostage. Phase E always runs -- it is the restore,
# not a step -- and every skip prints a SKIP line.
#
# Every zig run here is resident-bounded through bounded_run (cgroup
# MemoryMax, oracle_lib.sh); the old address-space caps are gone.
# MORNING READER: on the droplet, "CHAIN ENDED at phase done" with a
# tool-sha NOTE in phase E is the fully-green outcome -- cross-venue
# native binaries differ by host CPU, and E's rebuild is the restore,
# not the sha match. A rung dying on exactly `timeout 600` reads as
# 1-vCPU venue, not emitter. All arms ride the ring here (see
# CODEX_ALL_RING below); the TCP transport's coverage stays with
# laptop runs, deliberately.
set -u
export CODEX_ALL_RING=1
T="$(cd "$(dirname "$0")" && pwd)"
PIN=$HOME/showell_repos/NewRepository
HEAP=$HOME/showell_repos/nr-heap
GAPS=$HOME/showell_repos/nr-gaps
STAMP() { echo "@@@@ $1 $(date +%H:%M:%S)"; }
PHASE=init
trap 'echo "@@@@ CHAIN ENDED at phase $PHASE $(date +%H:%M:%S)"' EXIT

CODEX_ROOT="$PIN" . "$T/ast/oracle_lib.sh"
take_compute_lock

# PHASE_FROM resumes the chain at a later phase. PHASE_FROM=C runs the gaps
# half on its own, which is what the heap half going red asks for: the two
# branches are independent and the gaps PR is not blocked by the heap one.
# Skips are announced, never silent -- a chain that quietly did less than its
# name says is the failure mode this whole file exists to avoid.
PHASE_FROM="${PHASE_FROM:-A}"
phase_no() {
    case "$1" in A) echo 1 ;; B) echo 2 ;; B2) echo 3 ;; C) echo 4 ;; D) echo 5 ;; E) echo 6 ;; *) echo 0 ;; esac
}
FROM_NO="$(phase_no "$PHASE_FROM")"
[ "$FROM_NO" = 0 ] && { echo "PHASE_FROM=$PHASE_FROM is not one of A B B2 C D E"; exit 1; }
skip() {
    [ "$(phase_no "$1")" -lt "$FROM_NO" ] || return 1
    echo "@@@@ SKIP $1 (PHASE_FROM=$PHASE_FROM)"
    return 0
}

# Pre-flight, cheap and loud (cold review pre-launch checks).
PHASE=preflight; STAMP preflight
for repo in "$PIN" "$HEAP" "$GAPS"; do
    [ -z "$(git -C "$repo" status --porcelain)" ] || { echo "DIRTY TREE at $repo -- refusing"; exit 1; }
done
CODEX_ROOT="$HEAP" python3 "$T/seed_identity.py" | grep -q "Update 48" || { echo "nr-heap seed does not derive Update 48"; exit 1; }
CODEX_ROOT="$GAPS" python3 "$T/seed_identity.py" | grep -q "Update 48" || { echo "nr-gaps seed does not derive Update 48"; exit 1; }
[ "$(zig version)" = "0.16.0" ] || { echo "zig moved from 0.16.0; the movement tables would conflate toolchain with emitter"; exit 1; }

if ! skip A; then
    PHASE=A; STAMP "A: heap ladder sweep (allcycles, nr-heap)"
    CODEX_ROOT="$HEAP" "$T/ast/allcycles.sh" > "$T/logs/overnight-heap-sweep.log" 2>&1 \
        || { echo "HEAP SWEEP RED -- see logs/overnight-heap-sweep.log:"; tail -12 "$T/logs/overnight-heap-sweep.log"; exit 1; }
    grep -E "SWEEP: " "$T/logs/overnight-heap-sweep.log"
fi

if ! skip B; then
    PHASE=B; STAMP "B: heap census replay"
    CODEX_ROOT="$HEAP" "$T/native_build.sh" > "$T/logs/overnight-heap-natives.log" 2>&1 \
        || { echo "HEAP NATIVE BUILD FAILED:"; tail -8 "$T/logs/overnight-heap-natives.log"; exit 1; }
    CODEX_ROOT="$HEAP" python3 "$T/corpus_run.py" --changed > "$T/logs/overnight-heap-census.log" 2>&1 \
        || { echo "HEAP CENSUS FAILED:"; tail -8 "$T/logs/overnight-heap-census.log"; exit 1; }
    grep -A 60 "verdict diff" "$T/logs/overnight-heap-census.log" | head -64
fi

if ! skip B2; then
    PHASE=B2; STAMP "B2: heap RSS rider (ir_to_x86 under the branch emitter)"
    ( cd "$T/ast" && bounded_run "$ZIG_ARM_MEMORY_MAX" /usr/bin/time -v timeout 900 zig run ir_to_x86.zig 2>&1 || true ) \
        | grep -E "Maximum resident|Elapsed" || echo "(rider inconclusive -- non-blocking)"
fi

if ! skip C; then
    PHASE=C; STAMP "C: gaps ladder sweep (allcycles, nr-gaps)"
    CODEX_ROOT="$GAPS" "$T/ast/allcycles.sh" > "$T/logs/overnight-gaps-sweep.log" 2>&1 \
        || { echo "GAPS SWEEP RED -- see logs/overnight-gaps-sweep.log:"; tail -12 "$T/logs/overnight-gaps-sweep.log"; exit 1; }
    grep -E "SWEEP: " "$T/logs/overnight-gaps-sweep.log"
fi

if ! skip D; then
    PHASE=D; STAMP "D: gaps census replay"
    CODEX_ROOT="$GAPS" "$T/native_build.sh" > "$T/logs/overnight-gaps-natives.log" 2>&1 \
        || { echo "GAPS NATIVE BUILD FAILED:"; tail -8 "$T/logs/overnight-gaps-natives.log"; exit 1; }
    CODEX_ROOT="$GAPS" python3 "$T/corpus_run.py" --changed > "$T/logs/overnight-gaps-census.log" 2>&1 \
        || { echo "GAPS CENSUS FAILED:"; tail -8 "$T/logs/overnight-gaps-census.log"; exit 1; }
    grep -A 80 "verdict diff" "$T/logs/overnight-gaps-census.log" | head -84
fi

PHASE=E; STAMP "E: restore to the pinned mainline"
CODEX_ROOT="$PIN" "$T/native_build.sh" > "$T/logs/overnight-restore-natives.log" 2>&1 \
    || { echo "RESTORE NATIVE BUILD FAILED:"; tail -8 "$T/logs/overnight-restore-natives.log"; exit 1; }
git -C "$T" checkout -- corpus/transpile.json corpus/gaps.json corpus/run.jsonl \
    || { echo "RESTORE CHECKOUT FAILED -- the corpus trio is still branch data"; exit 1; }
python3 - "$T" <<'PY'
import hashlib, json, pathlib, sys
T = pathlib.Path(sys.argv[1])
meta = json.load(open(T / 'corpus' / 'census.json'))
want = meta.get('meta', {}).get('tools') or meta.get('tools')
for name in ('codexir', 'zigemit'):
    got = hashlib.sha256((T / 'native' / name).read_bytes()).hexdigest()[:16]
    exp = want[name][:16] if isinstance(want, dict) else None
    state = 'RESTORED' if got == exp else f'NOTE: differs from banked meta ({exp})'
    print(f'  {name}: {got} {state}')
    if got != exp:
        # Cross-venue, this is expected: the banked shas are laptop-built
        # binaries and zig targets the native host CPU. The rebuild ITSELF
        # is the restore; the sha match only proves same-host identity.
        print(f'  ({name} freshly rebuilt from the pin; a binary-sha match '
              'is only expected on the host that banked the census)')
PY

PHASE=done; STAMP "chain complete"
CODEX_ROOT="$PIN" python3 "$T/ladder_status.py"
