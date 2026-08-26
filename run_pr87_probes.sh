#!/usr/bin/env bash
# The PR 87 falsifier probes, run as a set.
#
# Three shapes the Cobblestone compiler lane asked for after answering
# PR 87, each carrying its prediction in its own prose. Two are expected
# to be REFUSED by the type checker -- a refusal is the result, not a
# failure -- and one is expected to build and answer 5.
#
# They asked for the outcome either way, including a null result, so this
# prints what each probe actually did rather than a pass/fail tally.
set -u
cd "$(dirname "$0")"
: "${CODEX_ROOT:?set CODEX_ROOT}"

for probe in alias deck armb; do
  src="findings/probe-pr87-${probe}.codex"
  echo "############ ${probe}  (${src})"
  python3 - "$src" "$probe" <<'PY'
import subprocess, sys, pathlib, os, re
sys.path.insert(0, os.getcwd())
import corpus_run
src, name = pathlib.Path(sys.argv[1]), sys.argv[2]
unit, miss = corpus_run.resolve(src)
if miss:
    print(f"  UNRESOLVED cites: {miss}"); raise SystemExit
ir = subprocess.run(['native/codexir'], input=unit.encode(), capture_output=True, timeout=180)
diags = ir.stdout.decode() + ir.stderr.decode()
codes = sorted(set(re.findall(r'\bCDX\d{4}\b', diags)))
halted = 'CODEGEN-HALTED' in diags
print(f"  codexir rc={ir.returncode}  diagnostics={codes or 'NONE'}  halted={halted}")
if codes or halted:
    for line in diags.splitlines():
        if 'CDX' in line or 'HALTED' in line:
            print(f"    | {line.strip()[:150]}")
    raise SystemExit
zg = subprocess.run(['native/zigemit'], input=ir.stderr, capture_output=True, timeout=180)
z = zg.stderr.decode()
out = pathlib.Path(f'probe-pr87-{name}.zig'); out.write_text(z)
marks = sorted(set(re.findall(r'zig plug: [^"]*', z)))
print(f"  emitted {len(z)} bytes  markers={marks or 'NONE'}")
p = subprocess.run(corpus_run.BOUNDED + ['timeout', '120', 'zig', 'run', str(out)],
                   capture_output=True, timeout=150)
got = p.stderr.decode().strip()
if p.returncode != 0:
    first = next((l for l in got.splitlines() if 'error:' in l or 'panic:' in l), got[:120])
    print(f"  zig rc={p.returncode}: {first[:140]}")
else:
    exp = pathlib.Path(f'{src.parent}/{src.stem}.expected')
    want = exp.read_text().strip() if exp.exists() else None
    verdict = 'MATCH' if want is not None and got == want else ('no .expected' if want is None else f'DIFFER want {want!r}')
    print(f"  ran -> {got!r}   {verdict}")
PY
  echo
done
