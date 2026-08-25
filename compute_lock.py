"""One compute job per host, taken at the one door that starts a guest.

The rule has not changed since 2026-08-20, when two 3 GB guests on this
box thrashed at 2% CPU each instead of failing: one guest at a time,
refuse loudly, never queue. What changed is where it is enforced.

It used to be taken by 22 entry points, each remembering to call
take_compute_lock for itself, because when it was written three files
started guests and there was no single door. There is one now --
codex_vm.launch, and nothing else in this tree runs qemu -- so the lock
lives there. An entry point cannot forget it, because it cannot start a
guest without going through the door.

That deleted the expensive half. The old check also scanned `ps` trying
to RECOGNISE our own jobs by name through shells, interpreters and -c
strings, and every incident this mechanism ever caused came from that:
a rebank refusing itself beside its own launcher (2026-08-22, again
08-24 into a log nobody was tailing), a watcher matching its own pgrep
and waiting for itself (08-25), and three spellings of the rule drifting
apart. None of it was ever needed. Our own jobs hold the flock, so
recognising them is redundant work; the only thing worth seeing is a
FOREIGN guest -- one started by something that never asks, like the
Codex tree's own build/compile.ps1 -- and a guest is a process whose
argv[0] is qemu-system-*. No interpreter to resolve, no argv string to
guess at, nothing to drift.

    ./compute_lock.py --probe   would take() refuse right now? For a
                                script about to detach, so the refusal
                                reaches the terminal and not a log
"""

import fcntl
import os
import subprocess

from ladder_root import LADDER

_fd = None  # held for the life of the process; flock dies with it


def require_venue():
    """The laptop does not compute (Steve, 2026-08-22, firmly: no
    fallbacks). Only the ladder droplet's ~/.codex_ladder_env exports
    CODEX_LADDER_VENUE; any host without it refuses before the lock."""
    if not os.environ.get('CODEX_LADDER_VENUE'):
        raise SystemExit('NOT A COMPUTE VENUE: CODEX_LADDER_VENUE is unset. '
                         'Ladder jobs run on the droplet only (sandbox.sh '
                         'there, . ../env). The laptop orchestrates.')


def guests():
    """Every QEMU guest on this host, as (pid, command line).

    A guest is a process EXECUTING qemu-system-*, which is the whole
    identification rule. ladder_status.py prints this; take() refuses on
    it.
    """
    out = subprocess.run(['ps', '-eo', 'pid=,args='],
                         capture_output=True, text=True).stdout
    found = []
    for line in out.splitlines():
        pid, _, args = line.strip().partition(' ')
        argv = args.split()
        if argv and os.path.basename(argv[0]).startswith('qemu-system'):
            found.append((int(pid), args.strip()))
    return found


def take():
    """Refuse unless this host is free to run a guest.

    Called by codex_vm.launch and by nothing else that starts one. Also
    called directly by corpus_run.py, which is an hours-class job that
    runs no guest at all and still wants the box to itself.

    Re-entrant down the process tree via LADDER_COMPUTE_LOCK, so a job
    that launches fourteen guests in turn checks once -- and, more to
    the point, never sees its own previous guest as somebody else's. The
    variable dies with the holder, so it cannot leak past a crash.
    """
    global _fd
    require_venue()
    if os.environ.get('LADDER_COMPUTE_LOCK'):
        return
    _fd = open(LADDER / '.compute.lock', 'w')
    try:
        fcntl.flock(_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit('COMPUTE LOCK HELD -- another sweep/build/census '
                         'owns this box; refusing')
    os.environ['LADDER_COMPUTE_LOCK'] = str(os.getpid())
    running = guests()
    if running:
        raise SystemExit('A GUEST IS ALREADY RUNNING, and it did not take the '
                         'lock -- refusing beside:\n  ' + running[0][1][:100])


def probe():
    """The refusal take() would give, or None -- without taking anything.

    For a script that is about to detach: ast/rebank_all.sh relaunches
    itself into a log, and on 2026-08-24 the child refused into a log
    nobody was tailing yet, so for four minutes the run looked launched
    and did not exist. The parent asks here, while there is still someone
    to tell.
    """
    fd = open(LADDER / '.compute.lock', 'w')
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return ('COMPUTE LOCK HELD -- another sweep/build/census owns this '
                'box; refusing')
    fcntl.flock(fd, fcntl.LOCK_UN)
    fd.close()
    running = guests()
    if running:
        return ('A GUEST IS ALREADY RUNNING, and it did not take the lock -- '
                'refusing beside:\n  ' + running[0][1][:100])
    return None


if __name__ == '__main__':
    import sys
    if '--probe' in sys.argv:
        msg = probe()
        if msg:
            print(msg)
            raise SystemExit(1)
    else:
        raise SystemExit(__doc__)
