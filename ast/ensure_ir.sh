#!/bin/bash
# Produce ast/<unit>.ir when a sweep needs one and the tree has none.
#
# allcycles.sh runs the zig and ring arms against truths ALREADY BANKED,
# but zig_arm refuses without a per-sandbox <unit>.ir, and a fresh sandbox
# carries none -- by design, since every ladder output is gitignored so a
# shared checkout cannot hand a run yesterday's artifact. Before this
# existed the only way to make those files was a full rebank: the whole
# truth arm, bare-metal binary and subject run included, roughly 27
# minutes spent producing INPUTS with the seed unchanged and the
# bare-metal arm not in question. The finding-40 fix paid it on
# 2026-08-24 and the f35 chain lost a run to it on 2026-08-23.
#
# This is the truth arm's first half and nothing else: bundle, blob,
# compile to IR-CCE, stamp. It does NOT compile the bare-metal binary and
# does NOT run it, so it writes no .truth and CANNOT be used to bank.
# Banking goes through ast/rebank_all.sh, which is the only thing that
# measures both arms.
#
# WHAT THIS COSTS THE SWEEP THAT USES IT: no <unit>-subject.cdx.diags is
# produced, so the diagnostics census sees a smaller population than the
# pinned counts were taken over. The caller must say so rather than
# compare anyway -- a census over half a population that reports against
# a whole-population pin is a number that lies in both directions.
#
# mode_flags and the unit lists come from oracle_lib.sh, sourced rather
# than copied: two spellings of a subject's mode flags would drift, and
# the drift would present as a plug defect.
set -e
. "$(dirname "${BASH_SOURCE[0]}")/oracle_lib.sh"

m="${1:-}"
[ -n "$m" ] || { echo "usage: ensure_ir.sh <unit>"; exit 2; }
case " $LADDER_UNITS " in
    *" $m "*) ;;
    *) echo "ensure_ir: $m is not a ladder unit ($LADDER_UNITS)"; exit 2 ;;
esac

# Already good? check-ir is the same gate the arms use, so "good" here and
# "acceptable" there cannot disagree. Silence on the happy path: a sweep
# printing twelve reassurances buries the one line that matters.
if [ -s "$T/ast/${m}.ir" ] \
   && python3 "$T/truth_prov.py" check-ir "$m" "$(mode_flags $m)" >/dev/null 2>&1; then
    exit 0
fi

echo "--- ensure_ir: ${m}.ir is missing or refused; rebuilding it from source"
cd "$T/ast"

# The subject is removed first so a bundle refusal cannot leave a stale one
# that looks fresh -- the failure that once let four rungs compile the
# PREVIOUS subject and banked truth from two of them.
rm -f "${m}-subject.codex"
if ! bout=$(~/.local/pwsh/pwsh -NoProfile -File "./bundle_${m}.ps1" 2>&1); then
    printf '%s\n' "$bout" | tail -5
    echo "BUNDLE FAILED for $m"; exit 1
fi
printf '%s\n' "$bout" | tail -1
[ -s "${m}-subject.codex" ] || { echo "BUNDLE FAILED: no ${m}-subject.codex"; exit 1; }

python3 "$T/check_bundles.py" "$m" || { echo "BUNDLE REFUSED for $m"; exit 1; }

# Only the IR-CCE blob. The CDX blob is the bare-metal binary's input and
# nothing here compiles one.
python3 - "$m" "$(mode_flags $m)" <<'PY' || { echo "BLOB WRITE FAILED for $m"; exit 1; }
import sys
m, flags = sys.argv[1], sys.argv[2]
src = open(f'{m}-subject.codex', 'rb').read()
open(f'{m}-ir-cce.blob', 'wb').write(b"IR-CCE" + flags.encode() + b"\n" + src + b"\x04")
print(f"ir-cce blob written ({len(src)} bytes of source), mode flags:{flags or ' none'}")
PY

cd "$T"
rm -f "ast/${m}.ir"
if ! python3 -u ring_compile.py "ast/${m}-ir-cce.blob" "ast/${m}.ir" 2>&1 | tail -20; then
    echo "COMPILE FAILED (IR-CCE) for $m -- see the diagnostics above"; exit 1
fi
[ -s "ast/${m}.ir" ] || { echo "COMPILE FAILED: no ${m}.ir"; exit 1; }

# Stamp the moment it is known good, for the same reason the truth arm
# does: the arms READ this file and never write it, so it outlives the run
# that made it and the sidecar is what tells yesterday's from today's.
python3 "$T/truth_prov.py" stamp-ir "$m" "$(mode_flags $m)" \
    || { echo "IR PROVENANCE STAMP FAILED for $m"; exit 1; }

# Judge what the compiler said, not just that it produced bytes. Only the
# IR half exists here; check_diags takes what it is given and says how many
# files it judged, so a shrinking population is visible rather than assumed.
if ! python3 "$T/check_diags.py" "ast/${m}.ir.diags"; then
    echo "DIAGNOSTICS REFUSED for $m (see check_diags.py POLICY)"; exit 1
fi
echo "--- ensure_ir: ${m}.ir rebuilt and stamped"
