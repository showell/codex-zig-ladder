#!/usr/bin/env python3
"""Derived state, for humans and for sessions that just lost theirs.

Answers the questions a post-crash session must otherwise reconstruct by
hand from mtimes, ps, and grep (process review 2026-08-20, C2): which
seed and Update the checkout holds, which banks exist, what the newest
tag claims, whether the working truths were recorded under THIS seed,
whether anything is computing right now, and what the newest log last
said. Prints facts; decides nothing. PRIORITIES.md carries decisions.
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # ladder-root-bootstrap
import compute_lock
import seed_identity
from ladder_root import CODEX, LADDER


def ladder_rungs():
    """The rung list, read from its one authority (oracle_lib.sh). Rungs,
    not units: a truth and its sidecar are per-rung files, and a unit that
    carries two rungs has no truth of its own."""
    for line in (LADDER / 'src' / 'oracle_lib.sh').read_text().splitlines():
        if line.startswith('LADDER_RUNGS='):
            return line.split('=', 1)[1].strip().strip('"')
    raise SystemExit('LADDER_RUNGS not found in src/oracle_lib.sh')


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip()


def main():
    sha = seed_identity.seed_sha256()
    label = seed_identity.update_label(sha)
    print(f"seed     {sha[:16]}  ({'Update ' + str(label) if label else 'no release note names it'})")

    banks = sorted(p.name for p in (LADDER / 'truth').iterdir() if p.is_dir())
    print(f"banks    {', '.join(banks) if banks else 'none'}")

    # Newest by the date it was MADE, and every shape of the name. The
    # glob was 'u*-14of14' sorted -V, and the bank taken on 2026-08-25 is
    # `seed-6cf4a8e0-14of14` -- named for a bank rather than an Update,
    # on purpose, because Update 50's push was interim. So this line
    # answered `u49-14of14` for three days: a tool for a session that has
    # lost its state, naming the wrong bank with no way to tell.
    tags = sh(f"git -C {LADDER} for-each-ref --sort=-creatordate "
              f"--format='%(refname:short)' 'refs/tags/*-14of14' | head -1")
    print(f"tag      {tags or 'none'}")

    fresh, stale, unproven = [], [], []
    for m in ladder_rungs().split():
        prov = LADDER / 'src' / f'{m}.truth.prov'
        truth = LADDER / 'src' / f'{m}.truth'
        if not truth.is_file():
            unproven.append(m + '(missing)')
        elif not prov.is_file():
            unproven.append(m)
        elif prov.read_text().splitlines()[0].strip() == sha:
            fresh.append(m)
        else:
            stale.append(m)
    print(f"truths   {len(fresh)} recorded under this seed"
          + (f"; STALE SEED: {' '.join(stale)}" if stale else "")
          + (f"; no prov: {' '.join(unproven)}" if unproven else ""))

    lock = LADDER / '.compute.lock'
    held = False
    if lock.exists():
        held = subprocess.run(['flock', '-n', str(lock), 'true'],
                              capture_output=True).returncode != 0
    # What is computing comes from compute_lock, which owns the rule --
    # this printed its own regex until 2026-08-25, and it had drifted.
    # A guest is a qemu-system process; nothing else is asked about.
    # Facts only: a held lock beside nothing running is worth seeing, not
    # worth interpreting here.
    jobs = compute_lock.guests()
    print(f"lock     {'HELD' if held else 'free'}")
    if not jobs:
        print("compute  nothing running"
              + ("  (lock held by a process that is not computing)"
                 if held else ""))
    for pid, args in jobs:
        print(f"compute  {pid} {args[:60]}")

    # WHICH COMPILER a measurement was taken against. We measure on our
    # fork's stack -- the pin plus the PRs we have sent and they have not
    # taken -- so a session that has lost its state has to be told what is
    # applied before it trusts a number or moves the pin.
    #
    # Those changes lived as uncommitted working-tree edits until
    # 2026-08-26, which was an accident dressed up as a decision (Steve:
    # "that seems like an unnecessary footgun"). They are commits on a stack
    # branch now, so they survive a checkout and `git log` says what they
    # are. Loose edits are still reported, because an uncommitted change is
    # exactly the thing nobody remembers making.
    branch = sh(f"git -C {CODEX} rev-parse --abbrev-ref HEAD")
    stack = sh(f"git -C {CODEX} log --oneline upstream/master..HEAD")
    n = len(stack.splitlines()) if stack else 0
    print(f"codex    {branch} = upstream/master"
          + (f" + {n} commit{'s' if n != 1 else ''}" if n else " exactly"))
    for line in stack.splitlines():
        print(f"           {line}")
    loose = sh(f"git -C {CODEX} status --porcelain | awk '{{print $2}}'")
    if loose:
        print(f"UNCOMMITTED in the checkout: {' '.join(loose.split())}")

    logs = sorted((LADDER / 'logs').glob('*.log'), key=lambda p: p.stat().st_mtime)
    if logs:
        last = logs[-1]
        tail = last.read_text(errors='replace').splitlines()
        print(f"log      {last.name}: {tail[-1] if tail else '(empty)'}")


if __name__ == '__main__':
    main()
