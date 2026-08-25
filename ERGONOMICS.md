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

**As of 2026-08-25 there are no tasks here** -- only standing notes,
which are decisions kept so they are not relitigated or deleted as dead
weight. An empty queue is the normal state for this file, not a sign
that something is missing from it.

---

## Standing: the compute lock is one line at one door

Not a task. It is here because the shape of it took a day to find and
should not be rediscovered.

**`codex_vm.launch` takes the lock, and nothing else that starts a guest
does.** That line is the only place in this tree that runs qemu, so an
entry point cannot forget to ask. It was 22 scattered
`take_compute_lock` calls until 2026-08-25 -- and seven entry points had
never called it at all, which is the more useful fact: they had been
starting guests unguarded for months with nothing going wrong. The
discipline was doing the work.

**The check is two questions, and neither can drift.** Is the flock
held? Is any process on this box executing `qemu-system-*`? The second
is what catches a FOREIGN guest -- `build/compile.ps1` in the Codex tree
boots one at `-m 3072` and asks nobody, measured 2026-08-25 -- and it
needs no interpreter resolution and no argv guessing, because a guest is
a real binary in argv[0].

**What was deleted, and why it is not coming back.** The old check tried
to recognise our OWN jobs by name in `ps`, through shells, interpreters
and `-c` strings. Every incident this mechanism ever caused came from
that: a rebank refusing itself beside its own launcher (08-22, and again
08-24 into a log nobody was tailing, so a run looked launched for four
minutes when it had already refused), a watcher matching its own `pgrep`
and waiting for itself (08-25), three spellings of the rule drifting
apart, and `LADDER_LAUNCHER_PID` -- a whole excuse mechanism for the
false positives. None of it was ever needed: our own jobs hold the
flock, so recognising them is redundant work.

**The ledger, which is the argument.** The hazard fired once (2026-08-20,
two 3 GB guests thrashing at 2% each). The mechanism fired against us
four times. If it ever starts costing more than it saves again, the next
step is not another guard -- it is to stop refusing and start STAMPING:
two guests never produce a wrong answer, only a wrong timing, so the
honest instrument would record "a second guest was live" in the run's
provenance and let the measurement say so itself.

**The one asymmetry left is not ours to close.** A ladder job refuses
beside a `compile.ps1` guest; a `compile.ps1` started beside a live
sweep is refused by nothing, because it asks nothing. Fixing that means
teaching an upstream script about a lock that is ours, and
`build/plug-run.ps1` is generated besides. The mitigation is discipline:
nothing in the codex tree gets run by hand while a sweep is up.

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
