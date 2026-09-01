#!/usr/bin/env python3
"""Bank a corpus transpile as an IR GOLD SET, outside every repo.

    ./bank_golds.py                       bank corpus/ under $CODEX_GOLDS_ROOT
    ./bank_golds.py --dest <dir>          somewhere else
    ./bank_golds.py --force               overwrite a bank that already exists

`corpus_run.py --transpile` writes `corpus/<name>.ir` and a `transpile.json`
saying what happened to every program. Those are STAGE OUTPUTS: the next run
rewrites them, and the corpus README's own rule is that a stage output is
regenerated and a bank is taken deliberately. This takes the bank.

WHY OUTSIDE BOTH REPOS. The consumer is `rust-codex-compiler`, which is to be
clean by construction -- no generated files, no binaries, no measurements
committed. So the golds are not vendored into it and not committed here
either. They live in a directory named for the CODEX PIN that produced them,
and a consumer reaches them through $CODEX_GOLDS the way every ladder script
reaches the checkout through $CODEX_ROOT: named, never guessed.

WHAT A GOLD IS WORTH IS ITS PROVENANCE. An `.ir` file is a claim some earlier
run made about a compiler that has since moved. The PROVENANCE file here
records the pin, the seed, and the natives stamp, so a comparison that is not
clean can be recognised as not clean BEFORE anybody reads the rows. Golds cut
against a different base measure the base change, not yours.

THE REFUSALS ARE THE SECOND GOLD SET, not an error log. A program the compiler
declines is a diagnostic the Rust front end must also produce, and `refused.tsv`
is where the linting work starts. It is written with the same care as the IR.

THE RUNG TRUTHS COME HERE TOO, AND NOT TO `bank_truth.py`. A truth bank is
named for the SEED (`seed_identity.update_label` -> `truth/u53/`), and a stack
of unlanded PRs does not move the seed: `bank_truth.py` run on
master-plus-outbound would write our own branches over the release bank under
the name `u53`, and nothing in it compares the checkout's HEAD to the release
that seed belongs to. So the per-rung truths measured on a non-release tree are
banked HERE, beside the IR, keyed by the pin that produced them. The release
banks stay what they say they are.

They are also the first two Rust layers' golds: `lex.truth` is a token dump
with offset, length, line and column, and `parse.truth` a def-level dump. One
subject each -- enough to start a lexer, not enough to finish one, which is
what the corpus is for.
"""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
from ladder_root import CODEX, LADDER
# `which branch` is one question with one answer. bank_truth.py became the
# second caller when it started recording the tree beside the seed, so the
# definition moved to seed_identity rather than being written twice.
from seed_identity import codex_branch

WORK = LADDER / 'corpus'
DEFAULT_ROOT = pathlib.Path(os.environ.get('CODEX_GOLDS_ROOT', pathlib.Path.home() / 'golds'))


def sha256_file(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def git(repo, *args):
    try:
        return subprocess.run(['git', '-C', str(repo), *args],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return '(unknown)'


def seed_sha():
    """The seed the natives were bootstrapped from -- the arm's real identity."""
    try:
        import seed_identity
        return seed_identity.seed_sha256()
    except Exception:
        return '(unknown)'


def natives_stamp():
    """sha256 of codexir+zigemit, the same stamp tiers_run.py prints."""
    h = hashlib.sha256()
    for name in ('codexir', 'zigemit'):
        p = LADDER / 'native' / name
        if not p.is_file():
            return '(absent)'
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dest', help='bank directory (default $CODEX_GOLDS_ROOT/<codex-sha>)')
    ap.add_argument('--force', action='store_true', help='overwrite an existing bank')
    a = ap.parse_args()

    # `transpile.json` is written once, after the loop; `transpile.jsonl` is
    # appended per program and is corpus_run's own crash-safe record. Reading
    # only the first meant an interrupted run banked NOTHING, however many
    # programs it had finished -- and a chain script that promised to "bank
    # what it produced anyway" could not keep that promise. Measured
    # 2026-09-01: a transpile killed at 110 of 1,705 left a complete .jsonl
    # beside 88 usable .ir files and banked none of them.
    tj = WORK / 'transpile.json'
    tjl = WORK / 'transpile.jsonl'
    if tj.is_file():
        verdicts = json.loads(tj.read_text())
        rows = verdicts['results'] if isinstance(verdicts, dict) else verdicts
        partial = False
    elif tjl.is_file():
        rows = [json.loads(l) for l in tjl.read_text().splitlines() if l.strip()]
        partial = True
    else:
        raise SystemExit(f'no {tj} and no {tjl}; run corpus_run.py --transpile first')
    # Say it, and say it in the bank. A partial gold set is useful; a partial
    # gold set that reads as a whole one is the thing to prevent.
    if partial:
        print(f'PARTIAL: {tj.name} is absent, so this bank comes from '
              f'{tjl.name} -- {len(rows)} program(s) recorded by an '
              f'interrupted run, not a completed corpus.')

    codex_sha = git(CODEX, 'rev-parse', 'HEAD')
    dest = pathlib.Path(a.dest) if a.dest else DEFAULT_ROOT / codex_sha[:12]
    if dest.exists() and not a.force:
        raise SystemExit(f'{dest} already exists; --force to overwrite')
    (dest / 'ir').mkdir(parents=True, exist_ok=True)

    kept, refused, ir_bytes = [], [], 0
    for r in rows:
        name = r['name']
        src = WORK / f'{name}.ir'
        if r.get('stage') in {'clean', 'markers'} or src.is_file():
            if not src.is_file():
                refused.append((name, r.get('stage', '?'), r.get('detail', '')))
                continue
            out = dest / 'ir' / f'{name}.ir'
            out.write_bytes(src.read_bytes())
            n = out.stat().st_size
            ir_bytes += n
            kept.append((name, n, sha256_file(out)[:16], r.get('stage', '?')))
        else:
            refused.append((name, r.get('stage', '?'), r.get('detail', '')))

    # The rung truths, if this sandbox measured them. Copied with their
    # provenance sidecars: a truth without one is a measurement nobody can
    # place afterwards, which is bank_truth.py's rule and holds here too.
    truths = sorted((LADDER / 'ast').glob('*.truth'))
    if truths:
        (dest / 'rungs').mkdir(exist_ok=True)
        for t in truths:
            (dest / 'rungs' / t.name).write_bytes(t.read_bytes())
            sc = t.with_suffix('.truth.prov')
            if sc.is_file():
                (dest / 'rungs' / sc.name).write_bytes(sc.read_bytes())

    with (dest / 'MANIFEST.tsv').open('w') as f:
        f.write('name\tir_bytes\tir_sha256_16\tstage\n')
        for row in sorted(kept):
            f.write('\t'.join(str(x) for x in row) + '\n')
    with (dest / 'refused.tsv').open('w') as f:
        f.write('name\tstage\tdetail\n')
        for row in sorted(refused):
            f.write('\t'.join(str(x).replace('\t', ' ') for x in row) + '\n')

    (dest / 'PROVENANCE').write_text(
        'IR gold set. Generated, never hand-edited; regenerate with\n'
        '  corpus_run.py --transpile && bank_golds.py\n\n'
        f'  codex pin      {codex_sha}\n'
        f'  codex branch   {codex_branch()}\n'
        f'  codex desc     {git(CODEX, "log", "-1", "--format=%h %s")}\n'
        f'  ladder pin     {git(LADDER, "rev-parse", "HEAD")}\n'
        f'  ladder desc    {git(LADDER, "log", "-1", "--format=%h %s")}\n'
        f'  seed sha256    {seed_sha()}\n'
        f'  natives stamp  {natives_stamp()}\n'
        f'  completeness   {"PARTIAL -- from transpile.jsonl, the run did not finish" if partial else "whole corpus"}\n'
        f'  arm            native/codexir (bare metal via the seed, no VM at gold time)\n'
        f'  sandbox        {os.environ.get("SANDBOX", "(none)")}\n\n'
        f'  programs with IR   {len(kept)}\n'
        f'  programs refused   {len(refused)}   (see refused.tsv -- the diagnostic gold set)\n'
        f'  IR bytes           {ir_bytes}\n'
        f'  rung truths        {len(truths)}   (lex/parse/... -- the per-layer golds)\n')

    print(f'banked {len(kept)} IR golds ({ir_bytes/1e6:.1f} MB) '
          f'and {len(refused)} refusals to {dest}')
    print((dest / 'PROVENANCE').read_text())


if __name__ == '__main__':
    sys.exit(main())
