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
} > /tmp/guardprobe.log 2>&1
tail -12 /tmp/guardprobe.log

echo
echo "=== 2. corpus: the depot's self-contained tests, native, against its .expected"
python3 "$T/corpus_run.py" --run > /tmp/corpus.log 2>&1
tail -30 /tmp/corpus.log

echo
echo "=== done at $(date +%H:%M). logs: /tmp/guardprobe.log /tmp/corpus.log"
