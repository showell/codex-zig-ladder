#!/bin/bash
# The end-to-end row for an EMITTER change, run from inside a sandbox.
#
#   cd ~/runs/<stamp>-<label>/ladder && ./verify_emitter.sh
#
# It exists because the same six legs have now been assembled by hand twice
# in one day, and the second assembly quietly measured a tree two commits
# behind the one under test: the sandbox was cut at 18:54 and the change
# landed at 19:20. A script cannot make that mistake -- it stamps the two
# HEADs it is actually running on into CHAIN-STATUS.txt before it starts.
#
# WHY IT BUILDS RATHER THAN COUNTS. An earlier verification of finding 47
# counted @compileError markers and called the fix done. Markers are the
# emitter's self-report about itself, `--transpile` builds nothing, and
# three programs had traded a diagnostic for a build FAILURE where the count
# could see neither. Every leg here either compiles zig or runs a guest.
#
# THE LEGS, and what each one is the only witness to:
#
#   0 natives     codexir + zigemit from this codex tree. Everything else
#                 reads these, so a stale binary here poisons all of it.
#   1b h2 matrix  findings/probe-h2-lambda-types.codex, seven cases, and
#                 unlike leg 1 it has an `.expected` banked from BARE METAL,
#                 so it is a correctness oracle and not a marker count. Case
#                 f answers `x!`: a repair that defaults an unrecovered
#                 parameter to Integer fails there instead of passing. Case
#                 g is unknowable by construction and a refusal there is the
#                 honest answer, so the leg prints the line-by-line diff
#                 rather than one bit.
#   1 tvar matrix findings/probe-tvar-recovery.codex, seven cases, one
#                 function each. Case (g) -- a closure returning a declared
#                 generic type -- is the one that reproduces, and a
#                 DIAGNOSTIC there is the intended outcome, not a build.
#                 THIS LEG IS FAMILY-SPECIFIC: a chain for some other class
#                 swaps it for that class's probe and says so.
#   2 corpus      corpus_run.py --run over the census: builds, runs, and
#                 diffs against .expected. The match count is the number.
#   3 codexzig    the single binary, ending in its FIXED POINT -- it
#                 re-emits its own bundle byte-identically or it is not the
#                 same compiler twice.
#   4 roc ports   roc_ports_run.py. Somebody else's suite, somebody else's
#                 expected values, and the only leg here written by people
#                 who have never seen this emitter.
#   5 sweep       ast/allcycles.sh, the rungs against bare-metal truth.
#                 The only leg that consults an oracle outside the zig arm.
#
# A RED LEG DOES NOT STOP THE CHAIN. Each verdict is information and the
# later legs stay worth having; stopping early would trade five facts for
# one. The exception is leg 0: with no natives there is nothing to measure.
set -u
cd "$(dirname "$0")" || exit 2
. ../env || { echo "verify_emitter: no ../env -- run this from inside a sandbox" >&2; exit 2; }
S="$SANDBOX"
STATUS="$S/CHAIN-STATUS.txt"

say() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$STATUS"; }
leg() {
    local n="$1"; shift
    say "$n START"
    if "$@" > "$S/$n.log" 2>&1; then say "$n GREEN"; else say "$n RED (exit $?)"; fi
}

say "CHAIN START -- codex $(git -C "$CODEX_ROOT" rev-parse --short HEAD), ladder $(git rev-parse --short HEAD)"

leg leg0-natives ./native_build.sh
[ -s native/codexir ] || { say "STOPS: no natives, nothing downstream can be measured"; exit 1; }

# Inline rather than a leg, because its verdict is three lines of prose and
# not an exit code: what matters is WHICH outcome case (g) reaches.
say "leg1-tvar-matrix START"
python3 - <<'PY' 2>&1 | tee "$S/leg1-tvar-matrix.log" | tail -5 | tee -a "$STATUS"
import subprocess, sys, re, pathlib, os
sys.path.insert(0, os.getcwd())
import corpus_run
src = pathlib.Path('findings/probe-tvar-recovery.codex')
unit, miss = corpus_run.resolve(src)
assert not miss, miss
ir = subprocess.run(['native/codexir'], input=unit.encode(), capture_output=True, timeout=120)
zg = subprocess.run(['native/zigemit'], input=ir.stderr, capture_output=True, timeout=120)
z = zg.stderr.decode(); pathlib.Path('probe.zig').write_text(z)
marks = sorted(set(re.findall(r'zig plug: [^"]*', z)))
print('  matrix markers:', marks or 'NONE')
tvar = [m for m in marks if 'type variable' in m]
p = subprocess.run(corpus_run.BOUNDED + ['timeout', '300', 'zig', 'run', 'probe.zig'],
                   capture_output=True, timeout=330)
err = p.stderr.decode()
pathlib.Path('probe-build.log').write_text(err)
if p.returncode == 0:
    print('  matrix RUNS ->', p.stderr.decode().split())
    print('  (cases a-f answer 7 11 42 5 3 42; case g must NOT reach here silently)')
    print('  leg1-tvar-matrix RED (case g built and ran; the refusal never fired)')
else:
    first = next((l for l in err.splitlines() if 'error:' in l), '')
    detail = first.split('error:')[-1].strip()
    print('  matrix DOES NOT BUILD ->', detail[:70])
    if not tvar:
        print('  leg1-tvar-matrix RED (no type-variable marker; case g is not diagnosed)')
    elif 'zig plug:' in err:
        print('  leg1-tvar-matrix GREEN (zig reports the plug marker itself)')
    else:
        print('  leg1-tvar-matrix RED (marker is in the file, zig reports "%s" instead)' % detail[:40])
PY

say "leg1b-h2-matrix START"
python3 - <<'H2PY' 2>&1 | tee "$S/leg1b-h2-matrix.log" | tail -12 | tee -a "$STATUS"
import subprocess, sys, re, pathlib, os
sys.path.insert(0, os.getcwd())
import corpus_run
src = pathlib.Path('findings/probe-h2-lambda-types.codex')
want = [l for l in pathlib.Path('findings/probe-h2-lambda-types.expected').read_text().splitlines() if l != '']
unit, miss = corpus_run.resolve(src)
assert not miss, miss
ir = subprocess.run(['native/codexir'], input=unit.encode(), capture_output=True, timeout=120)
zg = subprocess.run(['native/zigemit'], input=ir.stderr, capture_output=True, timeout=120)
z = zg.stderr.decode(); pathlib.Path('probe-h2.zig').write_text(z)
marks = sorted(set(re.findall(r'zig plug: [^"]*', z)))
print('  h2 markers:', marks or 'NONE')
p = subprocess.run(corpus_run.BOUNDED + ['timeout', '300', 'zig', 'run', 'probe-h2.zig'],
                   capture_output=True, timeout=330)
err = p.stderr.decode()
pathlib.Path('probe-h2-build.log').write_text(err)
if p.returncode != 0:
    first = next((l for l in err.splitlines() if 'error:' in l), '')
    print('  h2 DOES NOT BUILD ->', first.split('error:')[-1].strip()[:70])
    print('  leg1b-h2-matrix RED (no values to compare)')
else:
    got = [l for l in p.stdout.decode().splitlines() if l != '']
    for i, case in enumerate('abcdefg'):
        g = got[i] if i < len(got) else '(missing)'
        w = want[i] if i < len(want) else '(missing)'
        print('  case %s  want %-4s got %-4s %s' % (case, w, g, 'ok' if g == w else 'MISMATCH'))
    if got == want:
        print('  leg1b-h2-matrix GREEN (all seven, case f recovered rather than defaulted)')
    else:
        print('  leg1b-h2-matrix RED (%d of %d lines match)' % (sum(1 for a, b in zip(got, want) if a == b), len(want)))
H2PY

leg leg2-corpus ./corpus_run.py --run
say "  $(grep -E 'programs;|^match [0-9]+' "$S/leg2-corpus.log" | tail -2 | tr '\n' ' ')"

leg leg3-codexzig ./codexzig_build.sh
say "  $(grep -c 'fixed point holds' "$S/leg3-codexzig.log") fixed point"

leg leg4-roc-ports ./roc_ports_run.py
say "  $(grep -E '^### [0-9]+ match' "$S/leg4-roc-ports.log" | tail -1)"

leg leg5-sweep ./ast/allcycles.sh
say "  $(grep -c 'ORACLE PASS' "$S/leg5-sweep.log") rungs green"

say "CHAIN DONE."
