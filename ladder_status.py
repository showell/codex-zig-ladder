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
import seed_identity
from ladder_root import LADDER


def ladder_units():
    """The unit list, read from its one authority (oracle_lib.sh)."""
    for line in (LADDER / 'ast' / 'oracle_lib.sh').read_text().splitlines():
        if line.startswith('LADDER_UNITS='):
            return line.split('=', 1)[1].strip().strip('"')
    raise SystemExit('LADDER_UNITS not found in ast/oracle_lib.sh')


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip()


def main():
    sha = seed_identity.seed_sha256()
    label = seed_identity.update_label(sha)
    print(f"seed     {sha[:16]}  ({'Update ' + str(label) if label else 'no release note names it'})")

    banks = sorted(p.name for p in (LADDER / 'truth').iterdir() if p.is_dir())
    print(f"banks    {', '.join(banks) if banks else 'none'}")

    tags = sh(f"git -C {LADDER} tag -l 'u*-14of14' | sort -V | tail -1")
    print(f"tag      {tags or 'none'}")

    fresh, stale, unproven = [], [], []
    for m in ladder_units().split():
        prov = LADDER / 'ast' / f'{m}.truth.prov'
        truth = LADDER / 'ast' / f'{m}.truth'
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
    procs = sh("ps -eo args | grep -E 'qemu-system|rebank_all|allcycles|corpus_run|native_build' | grep -v grep | cut -c1-60")
    print(f"lock     {'HELD' if held else 'free'}")
    print(f"compute  {procs if procs else 'nothing running'}")

    logs = sorted((LADDER / 'logs').glob('*.log'), key=lambda p: p.stat().st_mtime)
    if logs:
        last = logs[-1]
        tail = last.read_text(errors='replace').splitlines()
        print(f"log      {last.name}: {tail[-1] if tail else '(empty)'}")


if __name__ == '__main__':
    main()
