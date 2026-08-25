"""The compute lock for the Python entry points, and the one rule for what
counts as a compute job.

The same lock take_compute_lock in ast/oracle_lib.sh takes -- one file,
one rule: one compute job per host (the droplet side is flocked inside
its wrappers). Refuse loudly, never queue: two 3 GB guests on this box
thrash at 2% CPU each instead of failing (2026-08-20).

Re-entrant down the process tree via LADDER_COMPUTE_LOCK, exactly as the
shell side is, so a locked script driving a locked script never refuses
its own parent -- and the variable dies with the holder, so it cannot
leak past a crash.

The lock binds only the processes that take it, so there is a second
check: refuse beside a job that computes WITHOUT it (process review D3).
Identifying that job is the substance of this file -- see job_program --
and the shell side calls in here for it rather than keeping a second
spelling that can drift from this one.

    ./compute_lock.py --evidence   the lockless-job check alone, no lock
    ./compute_lock.py --selftest   the identification rule against real
                                   command lines; touches no processes
"""

import fcntl
import os
import re
import subprocess

from ladder_root import LADDER

# What names a compute job. Matched against the program a process is
# EXECUTING and never against its full argv, which is what both spellings
# of this check did until 2026-08-25: a string in a shell's -c is not a
# job, and reading it as one refused real runs twice.
#   - A rebank refused itself beside the shell whose command line merely
#     NAMED ast/rebank_all.sh (2026-08-22, and again 08-24 -- that time
#     into a log nobody was tailing, so for four minutes the run simply
#     did not exist).
#   - A watcher polling `pgrep -f "native_build.sh|tiers_run.py"` matched
#     its own command line and waited for itself, so a job that had
#     FINISHED read as still running (2026-08-25).
# The old spelling carried a `'grep' not in args` exception for the
# second class. That excused one spelling of the mistake instead of
# removing the class, and it is gone with the class.
EVIDENCE = re.compile(r'qemu-system|rebank_all|allcycles\.sh|corpus_run|native_build')

# Programs that run some OTHER program: strip them and ask again.
WRAPPERS = {'nohup', 'env', 'setsid', 'nice', 'ionice', 'stdbuf', 'timeout',
            'time'}
# Programs that run a SCRIPT named in their arguments -- or, with -c, a
# command string, which is not a program of their own at all.
INTERPRETERS = {'sh', 'bash', 'dash', 'zsh', 'ksh',
                'python', 'python3', 'perl', 'ruby', 'pwsh', 'powershell'}

_fd = None  # held for the life of the process; flock dies with it


def _command_flag(flag, head):
    """True for the flags that mean "the program is on the command line"
    rather than in a file: sh/python -c, including inside a cluster like
    -lc, and pwsh -Command."""
    if flag == '-':                       # the program arrives on stdin
        return True
    low = flag.lower().lstrip('-')
    if head in ('pwsh', 'powershell'):    # -c, -co, -Command
        return bool(low) and 'command'.startswith(low)
    if flag.startswith('--'):
        return low == 'command'
    return 'c' in low


def job_program(args):
    """The program a process is EXECUTING, or None if it is executing no
    program of its own -- an inline -c command string, an interactive
    shell.

    Load-bearing: this is what the lockless-job check matches EVIDENCE
    against, and matching the full argv instead is the defect recorded
    above. Erring toward None is the safe direction, deliberately: the
    flock is the primary protection and this check is the backstop for
    jobs that never take it, so a missed job costs a check we already
    have, while a false one refuses a run that was entitled to go.
    """
    argv = args.split()
    while argv:
        # A login shell is argv[0] '-bash'; the dash is the login
        # marker, not part of the name.
        head = os.path.basename(argv[0]).lstrip('-')
        if head in WRAPPERS:
            argv = argv[1:]
            # The wrapper's own flags, VAR=VAL assignments and timeouts.
            while argv and (argv[0].startswith('-') or '=' in argv[0]
                            or argv[0][0].isdigit()):
                argv = argv[1:]
            continue
        if head in INTERPRETERS:
            for a in argv[1:]:
                if a.startswith('-') and a != '--':
                    if _command_flag(a, head):
                        return None
                    continue
                if a == '--':
                    continue
                return a
            return None       # an interpreter with no script runs nothing
        return argv[0]
    return None


def _ps():
    out = subprocess.run(['ps', '-eo', 'pid=,ppid=,args='],
                         capture_output=True, text=True).stdout
    rows, parent = [], {}
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        pid, ppid, args = int(parts[0]), int(parts[1]), parts[2]
        rows.append((pid, ppid, args))
        parent[pid] = ppid
    return rows, parent


def lockless_job():
    """The command line of the first process computing without the lock,
    or None.

    Our own ancestry is excused because we are the job about to compute.
    A detached job has lost its launcher from that chain, so the launcher
    names itself in LADDER_LAUNCHER_PID and its chain is excused too --
    belt and braces now that a shell merely naming a script no longer
    matches, but still real for the moment a self-detaching script and
    its own exiting copy overlap.

    Nothing else is excused. The old check also excused our immediate
    children, which was the same paper-over as the argv match: under
    job_program a child that matches IS a compute job, and the
    re-entrant case is exactly what LADDER_COMPUTE_LOCK is for.
    """
    rows, parent = _ps()
    roots = [os.getpid()]
    launcher = os.environ.get('LADDER_LAUNCHER_PID')
    if launcher and launcher.isdigit():
        roots.append(int(launcher))
    skip = set()
    for p in roots:
        while p > 1 and p not in skip:
            skip.add(p)
            p = parent.get(p, 0)
    for pid, ppid, args in rows:
        if pid in skip:
            continue
        prog = job_program(args)
        if prog and EVIDENCE.search(prog):
            return args
    return None


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
    running = lockless_job()
    if running:
        raise SystemExit('COMPUTE JOB RUNNING WITHOUT THE LOCK -- '
                         f'refusing beside: {running[:70]}')


# Real command lines, as `ps -eo args=` renders them. The first four are
# jobs; the rest are the processes that used to read as jobs and are the
# reason this rule exists. (program, refuses?)
SELFTEST = [
    ('qemu-system-x86_64 -m 3072 -accel tcg -kernel ast/lex.bin',
     'qemu-system-x86_64', True),
    ('/bin/bash /home/steve/runs/x/ladder/ast/rebank_all.sh',
     '/home/steve/runs/x/ladder/ast/rebank_all.sh', True),
    ('python3 -u corpus_run.py --transpile', 'corpus_run.py', True),
    ('nohup /bin/bash ./ast/allcycles.sh', './ast/allcycles.sh', True),
    ('/bin/bash /home/steve/runs/x/ladder/native_build.sh',
     '/home/steve/runs/x/ladder/native_build.sh', True),
    # The launching shell: names the script, executes no program of its own.
    ('bash -lc cd ~/runs/x/ladder && . ../env && ./ast/rebank_all.sh',
     None, False),
    ('/bin/sh -c nohup ./ast/rebank_all.sh > log 2>&1 &', None, False),
    # The watcher that waited for itself.
    ('pgrep -f native_build.sh|tiers_run.py', 'pgrep', False),
    # The exception that used to be needed, and is not.
    ('grep -E qemu-system|rebank_all|allcycles.sh', 'grep', False),
    ('python3 -c import codex_vm; codex_vm.run_cdx("ast/zigc-out.cdx")',
     None, False),
    ('pwsh -NoProfile -File ./bundle_zigc.ps1', './bundle_zigc.ps1', False),
    ('-bash', None, False),
    ('python3 -m corpus_run', 'corpus_run', True),
]


def selftest():
    bad = 0
    for args, want, refuses in SELFTEST:
        got = job_program(args)
        hit = bool(got and EVIDENCE.search(got))
        if got != want or hit != refuses:
            bad += 1
            print(f'FAIL {args!r}\n     program {got!r}, wanted {want!r}; '
                  f'refuses {hit}, wanted {refuses}')
    print(f'{len(SELFTEST) - bad}/{len(SELFTEST)} command lines identified'
          + ('' if not bad else f' -- {bad} WRONG'))
    raise SystemExit(1 if bad else 0)


if __name__ == '__main__':
    import sys
    if '--selftest' in sys.argv:
        selftest()
    elif '--evidence' in sys.argv:
        running = lockless_job()
        if running:
            print('COMPUTE JOB RUNNING WITHOUT THE LOCK -- refusing beside: '
                  + running[:70])
            raise SystemExit(1)
    else:
        raise SystemExit(__doc__)
