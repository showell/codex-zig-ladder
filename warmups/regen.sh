#!/bin/bash
# Rebuild every warmup's artifacts from its checked-in source: the IR the
# plug consumes, and a bare-metal truth to diff the zig run against. Run
# after a seed change, or whenever the .ir files are missing.
set -e
T="$(cd "$(dirname "$0")/.." && pwd)"  # ladder-root-bootstrap: reaches the LADDER only; the checkout comes from ladder_root
. "$T/ast/oracle_lib.sh"
# One guest per warmup: each is compiled bare-metal through the seed.
S=$T/warmups

cd $S
# The three originals are the default; a name on the command line
# regenerates just that one, which is what a new probe wants -- the whole
# set is three guests and a probe is one.
srcs=("$@")
[ ${#srcs[@]} -eq 0 ] && srcs=(hello recurse fib)
for src in "${srcs[@]}"; do
    echo "=== $src ==="
    python3 - "$src" <<'PY'
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd().parent))  # ladder-root-bootstrap
from cite_resolve import resolve

# What the seed compiles is the CITE-RESOLVED unit, the same one corpus_run
# and tier_run hand to their front ends. The blob step skipped this because
# the three originals reach only builtins and needed nothing -- which meant
# a warmup could not use a foreword definition at all, and the first probe
# that wanted `map-list` halted on CDX3002 without ever reaching the plug.
# resolve() also pulls in the two chapters the DESUGARER writes calls to, so
# a comprehension resolves whether or not the source cites anything.
p = sys.argv[1]
unit, missing = resolve(pathlib.Path(f'{p}.codex'))
if missing:
    sys.exit('unresolved cites: ' + '; '.join(f'{q} chapter {n}' for _, q, n in missing))
src = unit.encode()
open(f'{p}-cdx.blob', 'wb').write(b"CDX map\n" + src + b"\x04")
open(f'{p}-ir-cce.blob', 'wb').write(b"IR-CCE\n" + src + b"\x04")
PY
    (cd $T && python3 -u ring_compile.py warmups/${src}-cdx.blob warmups/${src}.cdx 2>&1 | tail -1)
    [ -s ${src}.cdx ] || { echo "COMPILE FAILED: no ${src}.cdx"; exit 1; }
    (cd $T && python3 -u ring_compile.py warmups/${src}-ir-cce.blob warmups/${src}.ir 2>&1 | tail -1)
    [ -s ${src}.ir ] || { echo "COMPILE FAILED: no ${src}.ir"; exit 1; }
    (cd $T && python3 - "$src" <<'PY'
import sys
import codex_vm
p = sys.argv[1]
out = codex_vm.run_cdx(f'warmups/{p}.cdx', timeout=300, idle_timeout=60)
lines = [l for l in out.decode(errors='replace').splitlines()
         if not l.startswith(("WD:", "HEAP:", "STACK:"))]
open(f'warmups/{p}.truth', 'w').write("\n".join(lines) + "\n")
print(f"banked warmups/{p}.truth: {lines}")
PY
    )
done
