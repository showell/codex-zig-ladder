#!/usr/bin/env python3
"""Bank IR golds for the SAFARI app, outside every repo.

    ./bank_safari_golds.py            bank into $CODEX_GOLDS_ROOT/safari-...
    ./bank_safari_golds.py --force    overwrite a bank that already exists

Safari is a better-shaped corpus than `codex/test/`: one program, decomposed
into chapters a person wrote on purpose, and `build/*-unit.codex` holds 27 of
them already RESOLVED and committed -- which is the form `native/codexir`
reads, since it resolves no cites of its own.

WHAT IS BANKED IS THE UNIT AS BYTES. Those files are build output that safari
tracks deliberately, and safari's own finding 14 says its freshness check
cannot see a source change -- so a unit may lag `port/`. That is safari's
question, not this bank's: MANIFEST.tsv carries each unit's sha256, so a gold
is reproducible from the bytes that made it whether or not they were current.

The bank goes to `$CODEX_GOLDS_ROOT/safari-<safari>-cx-<codex>`, the way
`bank_golds.py` puts the codex corpus outside both repos, and a consumer
reaches it through $CODEX_GOLDS: named, never guessed. rust-codex-compiler is
clean by construction, so nothing here is ever vendored into it.

WHAT PROVENANCE HAS TO ANSWER. Not "which repo was this near" -- which is all
a pin gives you -- but "could I make these bytes again, and would I know if I
could not". So the file records the producing BINARY by hash and not just the
tree it came from, the SCRIPT by hash because the ladder tree it sits in may
be dirty, the seed the compiler was bootstrapped from, the host and venue, the
wall-clock moment, and a DETERMINISM CHECK that recompiles one unit and
compares. A pin is a hint; a hash is a fact.

THE COMPILER IS THE NATIVES, NOT THE CHECKOUT. `native/codexir` is a binary
built at some past moment from some past pin; the checkout's HEAD moves
independently and does not describe it. Keying a bank on HEAD produces a path
like `...-cx-58b08c38` for golds that `a961dcb6`'s compiler actually made --
a name that is wrong and confident. The bank is keyed on the NATIVES STAMP,
which is a hash of the two binaries and therefore cannot drift from them, and
`native/PROVENANCE` supplies the pin they were built from.

Five things that would make a bank lie, and what stops each:

  * a DIRTY safari worktree makes the pin a fiction. The directory is then
    named `...-dirty` -- a bank that cannot be mistaken for a clean one by
    anybody reading its path, which no flag achieves.
  * a REFUSED compile exits 0 and writes `CODEGEN-HALTED: ...` where the IR
    would go. Banking that as IR is the mistake that put 13 programs in the
    wrong bucket on 2026-08-27; it goes to refused.tsv, the second gold set.
  * an existing bank is never overwritten without --force.
  * a run that dies part way says so in PROVENANCE rather than reading as a
    whole one.
  * the checkout's HEAD is recorded as what it is -- the tree at gold time --
    and never as the compiler's identity.

Cost, measured: 11.6 MB of unit, 27 programs, under a minute. No QEMU and no
compute lock -- native/codexir is a host binary, and the largest unit here is
1.2 MB against the 2.98 MB compiler that compiles on this box routinely.
"""

import argparse
import datetime
import hashlib
import os
import pathlib
import platform
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import CODEX, LADDER

SAFARI = pathlib.Path(os.environ.get('SAFARI_ROOT', pathlib.Path.home() / 'showell_repos' / 'safari-codex'))
GOLDS_ROOT = pathlib.Path(os.environ.get('CODEX_GOLDS_ROOT', pathlib.Path.home() / 'golds'))
CODEXIR = LADDER / 'native' / 'codexir'
TIMEOUT = 300


def git(repo, *args):
    try:
        return subprocess.run(['git', '-C', str(repo), *args],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return '(unknown)'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')


def natives_origin():
    """What `native/PROVENANCE` says built these binaries.

    native/ is gitignored, so this file is the only record of where the tools
    came from; without it the stamp is checkable and unplaceable.
    """
    p = LADDER / 'native' / 'PROVENANCE'
    if not p.is_file():
        return '(no native/PROVENANCE -- origin unrecorded)'
    fields = {}
    for line in p.read_text().splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] in {'codex', 'ladder', 'built'}:
            fields[parts[0]] = parts[1].strip()
    return f'codex {fields.get("codex", "?")} / ladder {fields.get("ladder", "?")}'


def natives_stamp():
    """The same stamp bank_golds.py records: which codexir made these."""
    h = hashlib.sha256()
    for name in ('codexir', 'zigemit'):
        p = LADDER / 'native' / name
        if not p.is_file():
            return '(absent)'
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def seed_sha():
    """The seed the natives were bootstrapped from -- the arm's real root."""
    try:
        import seed_identity
        return seed_identity.seed_sha256()
    except Exception:
        return '(unknown)'


def file_facts(p):
    """Hash, size and mtime of a file that has no other identity."""
    if not p.is_file():
        return '(absent)'
    st = p.stat()
    when = datetime.datetime.utcfromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%SZ')
    return f'{sha256(p.read_bytes())} {st.st_size} bytes, mtime {when}'


def determinism_check(unit, banked):
    """Compile one unit a second time and compare.

    Nothing else here would notice a compiler that answers differently run to
    run, and every gold in the bank is worthless if one does. It costs one
    program and it is the difference between believing the arm is
    deterministic and having checked it on the day.
    """
    again, refusal = compile_one(unit)
    if refusal:
        return f'FAILED -- {unit.stem} refused on the second run ({refusal[0]})'
    if again != banked:
        return f'FAILED -- {unit.stem} compiled to different bytes on a second run'
    return f'PASS -- {unit.stem} recompiled byte-identical'


def compile_one(unit):
    """One unit to IR. Returns (ir_bytes, None) or (None, refusal)."""
    try:
        r = subprocess.run([str(CODEXIR)], input=unit.read_bytes(),
                           capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, ('timeout', f'over {TIMEOUT}s')
    if r.returncode != 0 or not r.stderr:
        return None, ('codexir', f'rc={r.returncode}')
    # Output lands on stderr because print-text is std.debug.print in the
    # emitted runtime -- the same wart corpus_run.py documents.
    halted = next((l for l in r.stderr.decode('utf-8', 'replace').splitlines()
                   if l.startswith('CODEGEN-HALTED')), None)
    if halted:
        return None, ('codex-refused', halted[:160])
    return r.stderr, None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--force', action='store_true', help='overwrite an existing bank')
    a = ap.parse_args()

    if not CODEXIR.is_file():
        raise SystemExit(f'{CODEXIR} missing; run native_build.sh (it needs QEMU once)')
    units = sorted((SAFARI / 'build').glob('*-unit.codex'))
    if not units:
        raise SystemExit(f'no build/*-unit.codex under {SAFARI}; is SAFARI_ROOT right?')

    safari_sha = git(SAFARI, 'rev-parse', 'HEAD')
    dirty = bool(git(SAFARI, 'status', '--porcelain'))
    # A dirty LADDER does not change the IR -- it only means the pin below is
    # not the script that ran, which the script's own hash settles. So it is
    # recorded and does not go in the directory name, where only things that
    # change the BYTES belong.
    ladder_dirty = bool(git(LADDER, 'status', '--porcelain'))
    stamp = natives_stamp()
    dest = GOLDS_ROOT / f'safari-{safari_sha[:12]}-cx-{stamp}{"-dirty" if dirty else ""}'
    if dest.exists() and not a.force:
        raise SystemExit(f'{dest} already exists; --force to overwrite')
    (dest / 'ir').mkdir(parents=True, exist_ok=True)

    started, t0 = utc_now(), time.monotonic()
    kept, refused, ir_bytes, finished = [], [], 0, False
    determinism = '(not reached)'
    first_ir = None
    try:
        for unit in units:
            ir, refusal = compile_one(unit)
            src_sha = sha256(unit.read_bytes())[:16]
            if refusal:
                refused.append((unit.stem, *refusal))
                continue
            out = dest / 'ir' / f'{unit.stem}.ir'
            out.write_bytes(ir)
            ir_bytes += len(ir)
            kept.append((unit.stem, unit.stat().st_size, src_sha, len(ir), sha256(ir)[:16]))
            if first_ir is None:
                first_ir = (unit, ir)
        if first_ir:
            determinism = determinism_check(*first_ir)
        finished = True
    finally:
        # Written whatever happened, so a run that dies part way leaves a bank
        # that SAYS it is partial rather than one that reads as whole.
        with (dest / 'MANIFEST.tsv').open('w') as f:
            f.write('name\tunit_bytes\tunit_sha256_16\tir_bytes\tir_sha256_16\n')
            for row in sorted(kept):
                f.write('\t'.join(str(x) for x in row) + '\n')
        with (dest / 'refused.tsv').open('w') as f:
            f.write('name\tstage\tdetail\n')
            for row in sorted(refused):
                f.write('\t'.join(str(x).replace('\t', ' ') for x in row) + '\n')
        (dest / 'PROVENANCE').write_text(
            'Safari IR gold set. Generated, never hand-edited; regenerate with\n'
            '  bank_safari_golds.py\n\n'
            f'  subject        {SAFARI}/build/*-unit.codex, as committed bytes\n'
            f'  safari pin     {safari_sha}\n'
            f'  safari desc    {git(SAFARI, "log", "-1", "--format=%h %s")}\n'
            f'  safari tree    {"DIRTY -- the pin above does not describe what was compiled" if dirty else "clean"}\n'
            f'  natives stamp  {stamp}   <- THE COMPILER. This is what made the IR.\n'
            f'  natives built  {natives_origin()}\n'
            f'  checkout HEAD  {git(CODEX, "rev-parse", "HEAD")}   (the tree at gold time; it did NOT build the natives)\n'
            f'  ladder pin     {git(LADDER, "rev-parse", "HEAD")}\n'
            f'  codexir        {file_facts(CODEXIR)}\n'
            f'  seed sha256    {seed_sha()}\n'
            f'  arm            native/codexir on stdin (host binary; no VM, no compute lock)\n'
            f'  determinism    {determinism}\n\n'
            f'  cut started    {started}\n'
            f'  cut took       {time.monotonic() - t0:.1f}s\n'
            f'  host           {platform.node()} {platform.system()} {platform.release()}\n'
            f'  venue          {os.environ.get("CODEX_LADDER_VENUE", "(unset)")}\n'
            f'  python         {platform.python_version()}\n'
            f'  script         {file_facts(pathlib.Path(__file__).resolve())}\n'
            f'  ladder tree    {"DIRTY -- the ladder pin does not describe the script above" if ladder_dirty else "clean"}\n'
            f'  completeness   {"whole subject set" if finished else "PARTIAL -- the run did not finish"}\n\n'
            f'  units with IR  {len(kept)} of {len(units)}\n'
            f'  units refused  {len(refused)}   (see refused.tsv -- the diagnostic gold set)\n'
            f'  IR bytes       {ir_bytes}\n\n'
            f'To reproduce:\n'
            f'  SAFARI_ROOT={SAFARI} CODEX_GOLDS_ROOT={GOLDS_ROOT} \\\n'
            f'    {LADDER}/bank_safari_golds.py --force\n'
            f'with native/ holding the binaries hashed above; native_build.sh\n'
            f'rebuilds them and needs QEMU once.\n')

    print(f'banked {len(kept)} IR golds ({ir_bytes/1e6:.1f} MB) '
          f'and {len(refused)} refusals to {dest}')
    print((dest / 'PROVENANCE').read_text())


if __name__ == '__main__':
    sys.exit(main())
