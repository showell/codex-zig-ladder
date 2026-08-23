"""The laptop's compute lock, for the Python entry points.

The same lock take_compute_lock in ast/oracle_lib.sh takes -- one file,
one rule: one compute job per host (the droplet side is flocked inside
its wrappers). Refuse loudly, never queue: two 3 GB guests on this box
thrash at 2% CPU each instead of failing (2026-08-20).

Re-entrant down the process tree via LADDER_COMPUTE_LOCK, exactly as the
shell side is, so a locked script driving a locked script never refuses
its own parent -- and the variable dies with the holder, so it cannot
leak past a crash. The evidence check refuses beside a legacy job that
computes without taking the lock (process review D3), excluding our own
process, whose command line matches these very patterns.
"""

import fcntl
import os
import re
import subprocess

from ladder_root import LADDER

EVIDENCE = re.compile(r'qemu-system|rebank_all|allcycles\.sh|corpus_run|native_build')

_fd = None  # held for the life of the process; flock dies with it


def require_venue():
    """The laptop does not compute (Steve, 2026-08-22, firmly: no
    fallbacks). Only the ladder droplet's ~/.codex_ladder_env exports
    CODEX_LADDER_VENUE; any host without it refuses before the lock."""
    if not os.environ.get('CODEX_LADDER_VENUE'):
        raise SystemExit('NOT A COMPUTE VENUE: CODEX_LADDER_VENUE is unset. '
                         'Ladder jobs run on the droplet only (sandbox.sh '
                         'there, . ../env). The laptop orchestrates.')


def take():
    global _fd
    require_venue()
    if os.environ.get('LADDER_COMPUTE_LOCK'):
        return
    _fd = open(LADDER / '.compute.lock', 'w')
    try:
        fcntl.flock(_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit('COMPUTE LOCK HELD -- another sweep/build/census '
                         'owns this laptop; refusing')
    os.environ['LADDER_COMPUTE_LOCK'] = str(os.getpid())
    # Our own ancestor chain and immediate children are excluded: the
    # caller's own command line matches these very patterns, and so can
    # the shell that launched it.
    me = os.getpid()
    ps = subprocess.run(['ps', '-eo', 'pid=,ppid=,args='],
                        capture_output=True, text=True).stdout
    rows = []
    parent = {}
    for line in ps.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        pid, ppid, args = int(parts[0]), int(parts[1]), parts[2]
        rows.append((pid, ppid, args))
        parent[pid] = ppid
    skip = set()
    # A detached job has lost its launcher from the ancestor chain; the
    # launcher names itself in LADDER_LAUNCHER_PID so its chain is excused
    # too, since its command line names the very script that is running.
    roots = [me]
    launcher = os.environ.get('LADDER_LAUNCHER_PID')
    if launcher and launcher.isdigit():
        roots.append(int(launcher))
    for p in roots:
        while p > 1 and p not in skip:
            skip.add(p)
            p = parent.get(p, 0)
    for pid, ppid, args in rows:
        if pid in skip or ppid == me:
            continue
        if EVIDENCE.search(args) and 'grep' not in args:
            raise SystemExit('COMPUTE JOB RUNNING WITHOUT THE LOCK -- '
                             f'refusing beside: {args[:70]}')
