#!/usr/bin/env bash
# Compile a probe on BARE METAL — the seed, in QEMU — and print its
# diagnostics.
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
# Usage: run_seed_probe.sh <probe.codex>
# One QEMU guest: respects the one-compute-job rule via codex_vm's lock.
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
# The ring transport wants a FRAMED blob, not raw source: a "CDX map"
# header line carrying the mode flags, then the source, then \x04 as
# end-of-input. oracle_lib.sh:176 is the authority for this shape.
# Writing raw text instead makes the guest read the bytes and then wait
# forever for an EOT that never comes -- it sits at 0.3% CPU looking
# exactly like a slow compile. That cost 15 minutes on 2026-08-26.
blob = b"CDX map\n" + unit.encode() + b"\x04"
out = pathlib.Path(f"seedprobe-{stem}.blob")
out.write_bytes(blob)
print(f"  unit {len(unit)} chars -> {out} ({len(blob)} framed bytes)")
PY

echo "  compiling on the seed (QEMU) ..."
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
