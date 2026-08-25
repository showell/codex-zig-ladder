# Ergonomics

Making the work faster and safer: transport speed, real sandboxes,
foot-guns removed. This file is the queue for that; `PRIORITIES.md` is
the queue for finding defects and getting them to Damian, and the two
were one file until 2026-08-25.

**Why they split.** An ergonomic item's payoff multiplies across
everything below it, which is a real argument and which kept putting
tooling work in front of a defect register. Mixed into one list, the two
kinds compete on a single axis they do not share: an hour saved on the
verification chain and a silent wrong answer already shipped are not
comparable, and every re-sort had to re-litigate that. Split, each is
ordered against its own kind. **The rule between the files: nothing here
outranks an open correctness defect of ours.**

**Cite an item by its TITLE, never by its number.** Same rule as
`PRIORITIES.md`, same reason -- numbers are positional and every rewrite
reshuffles them.

**Done items leave this file** and are not filed anywhere; measurements
go to `JUSTIFICATIONS.md` and everything else is in git.

---

## The compute lock protects the job that asks, not the box

`compute_lock.py` refuses a job when it can SEE another one computing.
Since 2026-08-25 it identifies what it sees by the program a process is
EXECUTING and not by a string in that process's argv -- `job_program`,
with `--evidence` as the single entry point the shell side calls too, so
there is one spelling of the rule instead of two that had to be kept in
step. That closed the false-positive half of this item, which had cost
two real runs: a shell that merely NAMES a script and a watcher that
greps for one are not jobs. `tier_run.py --bare` and `tiers_run.py
--bare` take the lock now, because a bare column is a QEMU guest.

**The rule has a runner: `./compute_lock.py --selftest`** -- thirteen
real command lines, including both that bit us, and no processes
touched. Nothing calls it automatically; `PRIORITIES.md`'s Batch 3
`tests/` session is where it should land when that session happens.

What is left is the half that cannot be closed from this side. **The
codex tree's own plug scripts take no ladder lock at all.**
`codex/plugs/*/run.ps1` asks `build/plug-run.ps1` for a 3072 MB guest,
which is the ladder's whole guest budget on this box, and
`compute_lock.py`'s header records what two 3 GB guests do here: "thrash
at 2% CPU each instead of failing (2026-08-20)". The asymmetry is
exactly that a job is protected only when it ASKS -- a ladder job
starting beside such a guest refuses, because a `qemu-system` is a job
under any rule, while a plug script starting beside a live sweep is
refused by nothing. Fixing it means teaching an upstream script about a
lock that is ours, so until someone decides that is worth doing, the
mitigation is discipline: nothing in the codex tree gets run by hand
while a sweep is up.

## Wiring the python plug onto a transport that exists here

Only if it is ever wanted. `codex/plugs/python/build-output` has never
existed in this tree, and the run leg (`build/plug-run.ps1:49-53`) goes
straight to `tools/codex-vm.exe`, which is not built here and has no
QEMU fallback -- though `vm-config.ps1:821` defines one it never calls.
The ladder's zig plug sidesteps this with its own `plug_run.py`. Pointing
the python plug at the same transport is the work, and nothing needs it
today: finding 36 goes out hedged instead, per the standing rule in
`PRIORITIES.md`.

## Standing: the straw scripts are NOT retired

The keyboard-tempo tools -- `droplet_compile.sh`, `droplet_transpile.sh`
and the two-venue sweep -- stay. Both models share the box under the
compute lock, and the straw scripts are what a question asked at the
keyboard uses; retiring them because the detached path exists would
trade the fast answer for the thorough one. Pushes go through the deploy
keys (`github-ladder`, `github-nr`) since 2026-08-23. This is a decision
to keep, not a task: it is here so nobody deletes them as dead weight.

## Standing: two CPUs, so keyboard work runs beside a compute job

This box has two (dedicated, since 2026-08-23). A sweep, a rebank or a
native build owns one of them and the compute lock; reading, editing,
PR-writing and any light `zig run` do not have to wait for it. The
laptop-era habit of holding everything until the box went quiet is
retired -- **what still holds is one COMPUTE job at a time**, which
`compute_lock.py` enforces, and not one TASK at a time. `PRIORITIES.md`
orders its queue on this: items there are marked KEYBOARD or BOX.
