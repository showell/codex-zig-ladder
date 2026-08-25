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
greps for one are not jobs.

**Every ladder entry point that starts a guest takes the lock now** --
`tier_run.py --bare` and `tiers_run.py --bare` (a bare column IS a
guest), `cycle.sh`, `ast/ringplug_build.sh`, `ast/ensure_ir.sh`,
`warmups/regen.sh`, `ring_refill_test.sh`, `recon.sh`, and
`ast/f4_boot.py` past its `--parse` branch. Every one of those was
missing it, and the omission is invisible from the script: none of them
names QEMU, because the guest is two files away behind
`ring_compile.py` and `plug_run.py`. The list was found by asking which
files reach those two, which is a question worth re-asking whenever a
new entry point lands.

**The rule has a runner: `./compute_lock.py --selftest`** -- thirteen
real command lines, including both that bit us, and no processes
touched. Nothing calls it automatically -- there is no test runner in
this tree to hang it on, and one file's worth of cases did not seem
worth inventing one for.

What is left is not what this item claimed, and the correction is
measured (2026-08-25; the walk-through is the essay
`what-run-ps1-does-on-this-box`). **`codex/plugs/*/run.ps1` starts
nothing on this box.** It calls `build/compile.ps1` without `-Kernel`,
which then wants `build-output/bare-metal/Codex.cdx` from a `build.ps1`
this checkout has never run, and exits in one second. **`compile.ps1`
itself is the live one**: hand it `-Kernel seed/Codex.cdx` and it boots
`qemu-system-x86_64 ... -m 3072` in four seconds and asks no lock. Our
check sees that guest and refuses the ladder job beside it -- a
`qemu-system` is a job under any rule -- and nothing refuses in the
other direction, which is the asymmetry stated exactly.

Closing it from here is not worth doing: it means teaching an upstream
script about a lock that is ours, and `build/plug-run.ps1` is generated
from `codex/build/plugrunScript.codex` besides, so it cannot be
hand-edited at all. **The residue is one line of discipline: nothing in
the codex tree gets run by hand while a sweep is up.**

The other half of what this item used to carry -- that no plug can be
run here, because `plug-run.ps1` has no VM host on Linux -- turned out to
be a defect of theirs rather than a chore of ours. It is in
`PRIORITIES.md`'s outbound queue.

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
