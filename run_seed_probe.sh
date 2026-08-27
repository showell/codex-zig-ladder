#!/usr/bin/env bash
# Compile a probe on BARE METAL — the seed, in QEMU — and print both halves
# of what the compiler says about it: its DIAGNOSTICS and its IR WIRE.
#
# This exists because of an error worth not repeating. `native/codexir` is
# NOT the reference compiler: native_build.sh builds it by pushing the
# compiler's IR through the ring plug and compiling the emitted zig, so it
# is the compiler as OUR BACKEND renders it. Every diagnostic it prints is
# a diagnostic our own emitter produced.
#
# On 2026-08-26 a probe was reported to Damian as a type-checker soundness
# hole on the strength of `native/codexir` accepting a program. Their tree
# refused it at four seed revisions with a positive control. The likely
# reading is that our plug miscompiles the type checker until CDX2001
# stops firing -- which is ours, and worse.
#
# So: when the question is "what does the COMPILER do", the answer comes
# from here. When it is "what does our arm do", native/codexir answers.
# They are different questions and this script exists to keep them apart.
#
# BOTH MODES, ALWAYS, and no argument selects between them. "What does the
# compiler do" is one question with two halves and the wire is the half a
# `CDX map` compile cannot reach: H2 stood a full day at NOT YET RUN with
# its decisive falsifier -- does the seed's own IR-CCE wire carry `error`
# for a lambda parameter -- unanswerable by the only instrument pointed at
# bare metal. A probe that spends a guest to answer half a question is the
# false economy this tree keeps paying for, so the second guest is not
# optional. The framing is `oracle_lib.sh:176-177`'s, which every truth arm
# uses: the same transport, the same seed, one header word apart.
#
# Usage: run_seed_probe.sh <probe.codex>
# Two QEMU guests, one after the other: each respects the one-compute-job
# rule via codex_vm's lock, and neither runs while the other holds it.
set -eu
cd "$(dirname "$0")"
: "${CODEX_ROOT:?set CODEX_ROOT}"
src="${1:?usage: run_seed_probe.sh <probe.codex>}"
stem="$(basename "$src" .codex)"

python3 - "$src" "$stem" <<'PY'
import sys, pathlib, os
sys.path.insert(0, os.getcwd())
import corpus_run
src, stem = pathlib.Path(sys.argv[1]), sys.argv[2]
unit, miss = corpus_run.resolve(src)
if miss:
    print(f"UNRESOLVED cites: {miss}"); raise SystemExit(1)
# The ring transport wants a FRAMED blob, not raw source: a mode header
# line, then the source, then \x04 as end-of-input. oracle_lib.sh:176-177
# is the authority for this shape, and for the two mode words: `CDX map`
# compiles to a bare-metal image and `IR-CCE` emits the IR text wire from
# the same source, in the same guest shape.
# Writing raw text instead makes the guest read the bytes and then wait
# forever for an EOT that never comes -- it sits at 0.3% CPU looking
# exactly like a slow compile. That cost 15 minutes on 2026-08-26.
body = unit.encode() + b"\x04"
pathlib.Path(f"seedprobe-{stem}.blob").write_bytes(b"CDX map\n" + body)
pathlib.Path(f"seedprobe-{stem}-ir-cce.blob").write_bytes(b"IR-CCE\n" + body)
print(f"  unit {len(unit)} chars -> seedprobe-{stem}.blob and "
      f"seedprobe-{stem}-ir-cce.blob ({len(body) + 8} framed bytes)")
PY

echo "  compiling on the seed (QEMU), CDX map ..."
python3 ring_compile.py "seedprobe-${stem}.blob" "seedprobe-${stem}.cdx" || true

d="seedprobe-${stem}.cdx.diags"
echo
echo "############ BARE METAL verdict for ${stem}"
if [ -f "$d" ]; then
    echo "  diagnostics:"
    sed 's/^/    | /' "$d"
    if grep -qE 'CDX2001|CDX2010' "$d"; then
        echo "  -> the seed REFUSES this program."
    else
        echo "  -> diagnostics present, but no CDX2001/CDX2010."
    fi
else
    echo "  NO diagnostics file: the seed compiled it clean."
    echo "  -> the seed ACCEPTS this program."
fi

echo
echo "  compiling on the seed (QEMU), IR-CCE ..."
python3 ring_compile.py "seedprobe-${stem}-ir-cce.blob" "seedprobe-${stem}.ir" || true

echo
echo "############ BARE METAL wire for ${stem}"
python3 - "$stem" <<'PY'
import pathlib, re, sys
stem = sys.argv[1]
ir = pathlib.Path(f"seedprobe-{stem}.ir")
# ring_compile.py:300 writes `<out>.diags`, so this is the IR arm's own
# diagnostics file and NOT the blob's.
d = pathlib.Path(f"seedprobe-{stem}.ir.diags")
if d.is_file():
    print("  IR-CCE diagnostics (the CDX arm's may differ; both are the compiler):")
    print("\n".join("    | " + l for l in d.read_text().splitlines()))
if not ir.is_file() or not ir.stat().st_size:
    print(f"  NO wire: {ir} is missing or empty -- the IR-CCE compile produced nothing.")
    raise SystemExit(0)
s = ir.read_text('utf-8', 'replace')


def balanced(t, i):
    """The s-expression starting at t[i], parens balanced. The wire nests
    types arbitrarily deep -- `(fn (list int-default) ...)` -- so a regex
    stopping at the first `))` truncates a param list and reads as a
    definition with fewer parameters than it has."""
    depth = 0
    for j in range(i, len(t)):
        if t[j] == '(':
            depth += 1
        elif t[j] == ')':
            depth -= 1
            if depth == 0:
                return t[i:j + 1]
    return t[i:]


# A cell worth naming: the checker's error type, or a type variable that
# reached the wire unresolved. Both are types a plug has to answer for and
# neither is visible from the CDX arm at all.
#
# A tvar is matched AT ANY DEPTH and `error` only as the whole cell, which
# is not a symmetry worth removing. `error` is a leaf and cannot nest.
# A tvar can sit arbitrarily deep -- `roc-iter-map`'s refusing parameters
# are `(fn (tvar 44) (tvar 45))` and `(ctd "Iter" (args (tvar 44)))`, not
# bare cells -- and a scan that only reads whole cells calls that wire
# clean while the plug refuses to emit it. Reading `0 of 11` off a program
# that does not build is the fail-quiet this instrument exists against.
TVAR = re.compile(r'\(tvar \d+\)')
flagged = total = 0
for m in re.finditer(r'\(def "([^"]*)"', s):
    j = s.find('(params', m.start())
    if j < 0:
        continue
    params = balanced(s, j)
    cells = [balanced(params, k) for k in
             (p.start() for p in re.finditer(r'\(param "', params))]
    if not cells:
        continue
    marks = []
    for c in cells:
        ty = c[c.index('"', c.index('"') + 1) + 1:-1].strip()
        total += 1
        why = (['error'] if ty == 'error' else []) + sorted(set(TVAR.findall(ty)))
        if why:
            flagged += 1
            marks.extend(why)
    tail = '  <-- ' + ', '.join(dict.fromkeys(marks)) if marks else ''
    print(f"  {m.group(1):<24} {params}{tail}")
print(f"  ---- {flagged} of {total} parameter cells carry `error`, or an "
      f"unresolved `(tvar N)` at some depth; whole wire in {ir}")
PY
