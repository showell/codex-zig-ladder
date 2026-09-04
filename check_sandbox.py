#!/usr/bin/env python3
"""ONE SANDBOX, ONE COMMIT. Refuse if either checkout has moved since it was cut.

    python3 check_sandbox.py            # checks $SANDBOX, or the tree we are in

**THE RULE, and it is the most important one here (Steve, 2026-09-04): every
time we change commits, we make another sandbox.** A sandbox is a measurement of
one commit. Move a checkout inside it and everything measured before the move is
now attributed to a tree that no longer exists, silently, with no marker in any
file that says so.

WHAT IT COST, which is why this exists rather than being written in a README.
`20260903T234633Z-u56-rebank2` recorded fourteen bare-metal truths in 1,793
seconds -- a complete, correct set for `u56-candidate`, the thing an hours-class
run is for. Its codex checkout was then moved. The truths were still the right
bytes, but `bank_truth.py`'s provenance gate could no longer save them: they ran
under seed `81f9e817` and the tree on disk had `fcbabf07`. The measurement was
recoverable only because a SECOND sandbox happened to hold the same bytes and
had not been touched.

That gate caught it, and it caught it at the end, hours later, in the one place
where the answer was already paid for. This asks the same question at second
zero, where the answer is free and the fix is `./sandbox.sh <label>` again.

WHAT IT DOES NOT CHECK: whether the working tree is DIRTY. A dirty tree is a
different failure and `bank_truth` reads content rather than commits, so it
already refuses one. This is about the commit moving out from under a run.
"""
import os
import pathlib
import subprocess
import sys


def prov_get(path, key):
    for line in path.read_text().splitlines():
        parts = line.split('\t', 1)
        if len(parts) == 2 and parts[0] == key:
            return parts[1].strip()
    return None


def head_of(repo):
    r = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    root = os.environ.get('SANDBOX')
    if not root:
        # Walk up: a rung script is run from inside the sandbox it belongs to.
        d = pathlib.Path.cwd().resolve()
        while d != d.parent:
            if (d / 'PROVENANCE').is_file():
                root = str(d)
                break
            d = d.parent
    if not root:
        print('check_sandbox: not in a sandbox (no $SANDBOX, no PROVENANCE above) '
              '-- nothing to check')
        return 0
    root = pathlib.Path(root)
    prov = root / 'PROVENANCE'
    if not prov.is_file():
        print(f'check_sandbox: {root} has no PROVENANCE -- not a sandbox')
        return 0

    moved = []
    for key, sub in (('codex-sha', 'codex'), ('work-sha', prov_get(prov, 'work-dir') or 'ladder')):
        want = prov_get(prov, key)
        repo = root / sub
        if not want or not (repo / '.git').exists():
            continue
        now = head_of(repo)
        if now and now != want:
            moved.append((sub, want, now))

    if not moved:
        return 0
    print()
    print('REFUSING: ONE SANDBOX, ONE COMMIT -- a checkout has moved since this '
          'sandbox was cut.')
    for sub, want, now in moved:
        print(f'  {sub}: cut at {want[:12]}, now at {now[:12]}')
    print()
    print('  Everything measured before the move is attributed to a tree that is '
          'no longer here.')
    print('  Cut a new sandbox for the new commit rather than reusing this one:')
    print()
    print('      ./sandbox.sh <label> [ladder-ref] [codex-repo] [codex-ref]')
    print()
    return 1


if __name__ == '__main__':
    sys.exit(main())
