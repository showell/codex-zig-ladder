#!/bin/bash
# Everything that is ready to run unattended, in the order that matters.
# Written 2026-08-18. Roughly 40 minutes, most of it the corpus.
#
#   1. wait for any sweep in flight to finish (they share QEMU and the machine)
#   2. confirm the match-guard probe on BARE METAL, which is the half of that
#      finding we have not measured -- the zig side already prints the wrong
#      answer, and this is what makes it a divergence rather than a suspicion
#   3. run the depot's own self-contained tests through the native chain and
#      diff against ITS expected output
#
# Each step writes its own log and none depends on the previous one succeeding,
# because a failure in step 2 is itself a result worth having in the morning.
set -u
T="$(cd "$(dirname "$0")" && pwd)"
export CODEX_ROOT="${CODEX_ROOT:-$HOME/showell_repos/NewRepository}"

# Logs live in the repo, not /tmp: WSL wipes /tmp on VM restart, and the
# 2026-08-19 hang took step 1's only copy of the bare-metal verdict with it.
L="$T/logs"
mkdir -p "$L"

echo "=== waiting for any sweep in flight"
while ps -eo args | grep -q '[a]llcycles.sh'; do sleep 30; done
echo "=== clear at $(date +%H:%M)"

echo
echo "=== 1. match guard on bare metal (the seed, one small compile)"
{
    cd "$T/ast"
    python3 - <<'PY'
import pathlib
src = pathlib.Path('../findings/probe-match-guard.codex').read_bytes()
pathlib.Path('guardprobe-cdx.blob').write_bytes(b"CDX map\n" + src + b"\x04")
print(f"blob written, {len(src)} bytes of source")
PY
    cd "$T"
    python3 -u ring_compile.py ast/guardprobe-cdx.blob ast/guardprobe.cdx 2>&1 | tail -3
    python3 - <<'PY'
import codex_vm
out = codex_vm.run_cdx('ast/guardprobe.cdx', timeout=300, idle_timeout=60)
lines = [l for l in out.decode(errors='replace').splitlines()
         if not l.startswith(("WD:", "HEAP:", "STACK:"))]
print("BARE METAL SAYS:")
for l in lines:
    print("   ", l)
print()
print("ZIG SAID:            guard-taken 1 / guard-taken 1 / otherwise 0")
print("THE LANGUAGE SAYS:   guard-taken 0 / guard-taken 1 / otherwise 0")
PY
} > $L/guardprobe.log 2>&1
tail -12 $L/guardprobe.log

echo
echo "=== 2. corpus: the depot's self-contained tests, native, against its .expected"
python3 "$T/corpus_run.py" --run > $L/corpus.log 2>&1
tail -30 $L/corpus.log

echo
echo "=== 3. does the HOSTED compiler reproduce the SEED's IR, byte for byte?"
# The README's own closing open question: nothing yet establishes that a
# seed-independent chain produces the same IR. Every unit's seed-produced .ir is
# on disk from today's rebank, and native/codexir produces the same artifact
# with no QEMU, so the experiment is a diff. Green means the seed is one step
# closer to out of the loop. Red is a finding, which is the point of the
# project -- though a framing difference between the two IR writers would also
# show as red, so a mismatch wants reading before it is believed.
#
# This is also the memory stress case the heap work exists to serve: whole and
# clamp are 14 MB of IR from a 2.5 MB unit.
{
    cd "$T"
    for m in lex parse desugar scope check lower text pingpong lir fib fibx whole; do
        [ -s "ast/$m.ir" ] || { echo "  $m: no banked ir, skipped"; continue; }
        [ -s "ast/$m-subject.codex" ] || { echo "  $m: no subject, skipped"; continue; }
        timeout 900 ./native/codexir < "ast/$m-subject.codex" 2> "corpus/$m.hosted.ir" > /dev/null
        rc=$?
        if [ $rc -ne 0 ]; then
            echo "  $m: codexir FAILED (rc=$rc)"; continue
        fi
        if cmp -s "ast/$m.ir" "corpus/$m.hosted.ir"; then
            echo "  $m: IDENTICAL to the seed's IR ($(stat -c%s "ast/$m.ir") bytes)"
        else
            echo "  $m: DIFFERS  seed $(stat -c%s "ast/$m.ir")  hosted $(stat -c%s "corpus/$m.hosted.ir")"
        fi
    done
} 2>&1 | tee $L/iridentity.log

echo
echo "=== done at $(date +%H:%M). logs: $L/{guardprobe,corpus,iridentity}.log"
