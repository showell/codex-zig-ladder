#!/usr/bin/env python3
"""Which corpus programs can SEE a change. Derived from the diff, not guessed.

    ./affected.py <base-ref> <head-ref>

THE ABSENCE OF THIS COST 28 MINUTES OF BOX TIME ON 2026-08-30. An arc tangent
was added to `Gpu chapter DeviceMath` and measured with a full two-arm corpus
sweep that came back 0 stage moves, 0 verdict moves, 582 of 582 byte-identical.
Nothing in that corpus cites DeviceMath. The zeroes meant the sweep never
touched the change, and the only reason anyone noticed was a presence check
predicting a program count that did not arrive. This module answers the question
that should have been asked first, before the box was touched: *how many
programs are downstream of what I just edited?*

NOT EVERY CHANGE NARROWS, and saying so is the point.

  * `codex/plugs/**` -- the emitter writes every program's output. GLOBAL.
  * `codex/compiler/**` -- likewise. GLOBAL.
  * `codex/build/**` -- the quire map and bundler decide what a unit even
    contains. GLOBAL.
  * a chapter anywhere else -- only the programs whose transitive cite closure
    reaches it.
  * `codex/test/**` -- the programs themselves, added or edited.

So a plug change still sweeps everything, and honestly: the value here is
telling you that a *library* change touches two programs BEFORE you spend forty
minutes proving it, and telling you which two.
"""
import pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from cite_resolve import CITE, quire_dirs
from ladder_root import CODEX

GLOBAL_PREFIXES = ('codex/plugs/', 'codex/compiler/', 'codex/build/')


def changed_paths(base, head, repo):
    out = subprocess.run(['git', '-C', str(repo), 'diff', '--name-only',
                          f'{base}..{head}'], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f'git diff failed:\n{out.stderr}')
    return [l for l in out.stdout.splitlines() if l.strip()]


def classify(paths):
    """(scope, detail). 'all' when nothing can be narrowed."""
    glob_hits = [p for p in paths if p.startswith(GLOBAL_PREFIXES)]
    if glob_hits:
        return 'all', glob_hits
    chapters, tests = set(), set()
    for p in paths:
        if not p.endswith('.codex'):
            continue
        if p.startswith('codex/test/'):
            tests.add(pathlib.Path(p).stem)
        else:
            chapters.add(pathlib.Path(p).stem)
    return 'derived', {'chapters': sorted(chapters), 'tests': sorted(tests)}


def closure(path, dirs, cache):
    """Every chapter name this file reaches through cites, transitively."""
    key = str(path)
    if key in cache:
        return cache[key]
    cache[key] = set()                       # cycle guard, set before recursing
    try:
        text = pathlib.Path(path).read_text(errors='replace')
    except OSError:
        return cache[key]
    reach = set()
    for quire, name in CITE.findall(text):
        reach.add(name)
        d = dirs.get(quire)
        if d:
            dep = CODEX / d / f'{name}.codex'
            if dep.is_file():
                reach |= closure(dep, dirs, cache)
    cache[key] = reach
    return reach


def programs_at(ref, repo):
    """Every test program AS OF A REF, not as of whatever a checkout is on.

    This read a working tree until 2026-08-30, and the working tree was on a
    different branch than the run: `--plan` for the arc tangent reported 4
    affected programs where the truth was 5, silently missing the new test
    because the checkout predated it. A population is a property of the ref
    being measured; anything else is a guess that looks like a fact.
    """
    out = subprocess.run(['git', '-C', str(repo), 'ls-tree', '-r',
                          '--name-only', ref, 'codex/test/'],
                         capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f'git ls-tree failed:\n{out.stderr}')
    return sorted(l for l in out.stdout.splitlines() if l.endswith('.codex'))


def cites_at(ref, repo, path):
    out = subprocess.run(['git', '-C', str(repo), 'show', f'{ref}:{path}'],
                         capture_output=True, text=True)
    return CITE.findall(out.stdout) if out.returncode == 0 else []


def affected(chapters, test_stems, ref, repo):
    """Programs whose cite closure reaches a changed chapter, plus changed tests."""
    dirs, cache = quire_dirs(), {}
    want, hits = set(chapters), []
    for rel in programs_at(ref, repo):
        stem = pathlib.PurePosixPath(rel).stem
        if stem in test_stems:
            hits.append((rel, 'changed test'))
            continue
        reach = set()
        for quire, name in cites_at(ref, repo, rel):
            reach.add(name)
            d = dirs.get(quire)
            if d:
                dep = CODEX / d / f'{name}.codex'
                if dep.is_file():
                    reach |= closure(dep, dirs, cache)
        if want & reach:
            hits.append((rel, 'cites ' + ', '.join(sorted(want & reach))))
    return hits


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__.strip().splitlines()[2].strip())
    base, head = sys.argv[1], sys.argv[2]
    repo = CODEX
    paths = changed_paths(base, head, repo)
    scope, detail = classify(paths)
    print(f'{len(paths)} file(s) changed between {base} and {head}')
    if scope == 'all':
        print('\nSCOPE: all -- nothing narrows. These paths affect every program:')
        for p in detail:
            print(f'  {p}')
        return 0
    total = len(programs_at(head, repo))
    hits = affected(detail['chapters'], set(detail['tests']), head, repo)
    print(f"\nSCOPE: derived -- chapters {detail['chapters'] or '(none)'}, "
          f"changed tests {detail['tests'] or '(none)'}")
    print(f'\n{len(hits)} of {total} programs affected (population as of {head}):')
    for rel, why in hits:
        print(f'  {rel[len("codex/test/"):]}   ({why})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
