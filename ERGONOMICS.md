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

## Launching a detached job is a foot-gun with a live tripwire

`ast/rebank_all.sh` relaunches itself detached so a dead terminal
cannot kill an hour-long run. The detached child is
reparented to init, so the shell that launched it is no longer an
ancestor -- and `compute_lock.py`'s lockless-job detector then sees that
shell's command line, which names the script, and refuses the run as a
legacy job computing without the lock. The script already knows: it hands
its pid over in `LADDER_LAUNCHER_PID` for exactly this, with a comment
recording that the u49 rebank refused itself this way on 2026-08-22.

The excuse does not always land. The launcher copy `exit 0`s immediately,
so by the time the child checks, that pid is gone from `ps` and the chain
cannot be walked back to the shell that still matches. **2026-08-24: a
rebank refused itself again this way and printed its refusal into a log
nobody was tailing** -- from the terminal it looked launched, and the
run simply did not exist for four minutes.

Three things to fix, and the first matters more:

- **A refusal must reach the launcher, not only the log.** The parent's
  early `flock -n` check exists for this and did not fire, because the
  lock was genuinely free; what refused was the child's evidence check,
  after detaching. Have the child report a refusal back to the terminal
  (or have the parent run the evidence check too, while it is still an
  ancestor of nothing and can speak).
- **Walk the launcher's ancestry before it exits**, or record it: pass
  the whole chain rather than a pid that is about to die.
- **The detector reads the wrong thing, and it already knows.** `EVIDENCE`
  is searched against the FULL argv of every process, so anything that
  merely mentions a job's name looks like the job -- which is why the
  check carries a `'grep' not in args` exception, a paper-over of the
  class rather than a fix. It bit again on 2026-08-25 in a different
  tool: a watcher waiting for the natives to finish with
  `pgrep -f "native_build.sh|tiers_run.py"` matched its own command
  line and waited for itself, so a job that had FINISHED read as still
  running. What identifies a job is the program it is executing, not a
  string in a shell's `-c`; match the script path (`comm`, or argv[0]
  resolved) and the exception can go with it.

Until then: launch through a wrapper script whose own argv does not match
`EVIDENCE` (`qemu-system|rebank_all|allcycles\.sh|corpus_run|native_build`),
never leave a `sleep` in the launching shell, and do not name a job in
the command line of anything that watches for it.

Verified still live 2026-08-25 against `compute_lock.py`: `roots` is
`[me, LADDER_LAUNCHER_PID]` and each is walked up through `parent`, so a
launcher pid that has already exited contributes nothing to `skip` and
the shell that still matches is never excused. Today's runs did not trip
it because `native_build.sh` and `allcycles.sh` do not self-detach --
their launching shell stays an ancestor. `rebank_all.sh` is the one that
does, and it is the one that has refused itself twice.

## The compute lock protects the job that asks, not the box

`compute_lock.py` refuses a job when it can SEE another one computing.
The protection is one-directional, and two live paths walk around it:

- **`tiers_run.py` and `tier_run.py` call `require_venue()` and never
  `take()`** (`tiers_run.py:170`, `tier_run.py:231`). A `--bare` column
  is a QEMU guest, so it can start beside a live sweep, and then that
  guest trips the lockless-job detector and refuses the NEXT ladder job.
  The zig-only mode is genuinely lock-free and lock-safe -- 45 seconds,
  no guest -- and that is worth keeping; it is the bare mode that wants
  the lock.
- **The codex tree's own plug scripts take no ladder lock at all.**
  `codex/plugs/*/run.ps1` asks `build/plug-run.ps1` for a 3072 MB guest,
  which is the ladder's whole guest budget on this box.
  `compute_lock.py:5-6` records what two 3 GB guests do here: "thrash at
  2% CPU each instead of failing (2026-08-20)".

Both are the same class -- a guest started by something that never asked
-- and the fix is the same as the one the detached-job item names: match
what a process is EXECUTING, not a string in some shell's `-c`, and have
the things that start guests take the lock. Found 2026-08-25 by a cold
read of the queue.

## Cache the built zigc

`zigc_verify.sh` redoes its whole expensive prefix on every invocation --
harness generation, the bundle, a `ring_compile.py` over a 13.9 MB IR,
and the ring-plug build -- none of which depend on the subject it was
asked to verify. So screening candidate subjects costs a full run each.
The zigc item in `PRIORITIES.md` is stuck on "find a subject that needs
none of the driver's extras", which is a search, and a search over an
uncached prefix is the expensive way to do it. Caching the built zigc
turns each candidate into `./zigc < candidate`, which is free.

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
