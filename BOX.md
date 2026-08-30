# Running a job on the BOX

A checklist for compute jobs on the ladder droplet. Items are here because
each one has already cost something; the reasoning and the incident ledger
behind them is the note
[what a BOX job costs when it is wrong](http://143.244.172.148:9100/notes/what-a-box-job-costs-when-it-is-wrong.md).

**Scope: any non-trivial process, not only a job that boots a guest.** The
items are written for compute runs because that is where they were paid for,
but a measurement, a rebase, a rebuild or a comparison earns the same list.

**The one-line version.** The failure mode on this box is not a crash. It is
a job that completes, reports a verdict, and the verdict is about something
other than what you thought. Every item below exists to make a result
ATTRIBUTABLE -- to a tree, to an arm, to a baseline, and to a change that
demonstrably executed.

This list is a tax on every run. An item that stops catching anything should
be deleted, not kept for completeness.

## Before

1. **DO WE NEED THIS NOW? Name the consumer and when they read it.** Not "is
   this a good idea" -- who reads the result, and how soon. A run whose answer
   nobody consumes for weeks is worse than not running it: it ages into
   something that has to be re-validated before it can be trusted, and the
   re-validation costs about what the run cost. If the honest answer is "we
   might want it later", the cheaper plan is almost always to run it LATER,
   when there is a question, against a tree nobody has to reason about the
   staleness of. Ask this before the box is touched and before anything below
   is worked.
2. `python3 ladder_status.py` -- seed, banks, tag, lock, what is computing.
   If any line disagrees with what you believe, stop and find out why.
3. Write one line: what this run settles, and **what result would change my
   mind.** No falsifier means the answer will confirm whatever was hoped.
4. **Know which branch you are running out of and WHAT IT CARRIES.** Not the
   name -- the contents. `git log <base>..HEAD` and `git diff --stat <base>`
   on every tree in play, and ask what each unlanded commit assumes about the
   other trees. A branch that mirrors a change which landed nowhere is the
   trap: ladder master carried a harness calling `ir-prune-unreachable-typedefs`,
   a compiler pass defined only on a parked branch, so it could not build
   natives against ANY release -- and its name said nothing at all about that.
5. Name the arm -- bare metal (the seed under QEMU) or ours (`native/codexir`).
   A question about *the compiler* takes the seed. "Whatever was in front of
   me" is not an answer.
6. **Every tree the job touches is clean and on the branch you think --
   including the ones it only reads.** `git status --short` and
   `rev-parse --abbrev-ref HEAD` on each. A SHARED checkout is the trap:
   moving `CODEX_ROOT` to a new pin moves it under every other project
   pointed at the same directory, and nothing announces that.
7. **Know what the job WRITES, and who else reads it.** Name the output paths
   before launching. A GITIGNORED artifact is the dangerous kind: no branch
   switch protects it, `git status` never shows it, and another project may
   resolve it by path with no idea which branch produced it. If a job would
   clobber something another project depends on, **redirect the job or plan to
   rebuild** -- never plan to restore by hand afterwards. A hand-copied
   artifact has no provenance, and `cp -p` in particular forges the mtime that
   somebody's change-detector is reading.
8. `./sandbox.sh <label>`, then `cd <path>/ladder && . ../env`. Without
   `. ../env` the sandbox is decoration and `CODEX_ROOT` still points at the
   shared checkout.
9. **Read the provenance of everything you will COMPARE AGAINST, before the
   run.** A bank, a census, a gold column, an `.expected` -- each is a claim
   some earlier run made, not ground truth, and each records what produced it:
   `corpus/census.json` has a `meta` block, `truth/uNN/` has `SEED` plus a
   prov sidecar per rung, `findings/gold/uNN/` keys each column on program text
   AND seed. If the comparand came from a different base than the run you are
   about to make, the diff measures the BASE CHANGE and not your change. Then
   either re-measure the baseline or say plainly, before showing anyone the
   rows, that the comparison is not clean. A verdict that "moved" against a
   stale baseline has moved for two reasons and the rows cannot tell you which.
10. Design the **presence check** now: one baseline-free assertion that the
   change is visible in the output. A soundness gate is blind to a no-op.
11. **A GATE YOU ARE SHIPPING MUST BE SHOWN TO FIRE.** Item 10 asks whether
   your CHANGE executed. This asks whether the CHECK would notice if the answer
   were wrong, which is a different question and the only one that survives a
   green run. A comparison whose every row reads `ok` has never executed its own
   mismatch branch -- so the branch that gives the test its entire value is the
   one line nobody has run, and a typo in it looks exactly like success.
   Perturb one expected value by the smallest amount that must fail, confirm
   that row and only that row goes red, and revert. One guest.
   `codex/test/forewords/gpu-devicemath-atan` was written, run, and read as
   proof with 34 rows of `ok` before anyone noticed its `MISMATCH` arm had never
   executed.
12. `python3 check_paths.py` and `python3 check_harness_gates.py` (5 s each), `compute_lock.py --probe` if detaching,
   and say the expected cost out loud before launching anything over 20 s.
   A job that takes no lock of its own -- the transpiler is one -- makes this
   check the only guard there is. `check_harness_gates.py` is the mechanical
   form of step 3: it asks whether what this branch's harnesses assume matches
   the compiler they are pointed at, and exits 1 when it does not.

## During

1. Detach with a log, announce the path, watch with a Monitor -- never piped
   through `head`, and **never watch by `pgrep -f` on the job's own command
   line.** Run from a session shell, the pattern matches the watcher's own
   argv and the watch waits forever on itself. Watch the LOG or the artifact
   the job writes, which is the thing you actually care about anyway.
2. Do not change HEAD, check out, or edit anything in the tree the run is
   reading. Branch surgery waits for the verdict.
3. Nothing in the codex tree gets run by hand while a sweep is up --
   `build/compile.ps1` boots a 3 GB guest and asks nobody.
4. Keyboard work belongs here. Two CPUs: one COMPUTE job at a time, not one
   task at a time.
5. To abort: signal the process group, then check for orphan guests. Never
   `pkill -f` from a session shell.

## After

1. Read the verdict from the file, and read the HEAD of it as well as the
   tail. Any claim of a maximum, count, set, or absence must come from a
   command that saw everything. **A tool that has something to warn you about
   prints it BEFORE the rows, which is exactly where `tail` cannot see it** --
   `corpus_run.py` prints `*** THE BANK IS NOT ABOUT THIS TREE ***` above its
   verdict diff, and a `tail -25` starts below it and shows only the rows the
   banner was disowning.
2. Run the presence check. A *perfectly* clean result on a change that should
   move bytes is a suspect, not a win.
3. Push any branch out of the sandbox immediately -- a sandbox commit lives
   on no branch and dies with the prune.
4. Carry the artifacts back (banks, gold, logs), then **RETIRE THE SANDBOX.
   Retiring is the default and keeping is the exception.** A `KEEP` needs what
   Before-1 needs: a named consumer and roughly when they read it. "It might
   save time later" is not one -- kept trees are footguns far more often than
   they are savings, because the next person reaches for the stale natives or
   the stale verdicts instead of rebuilding, and measures against a base
   nobody checked. If the answer is written down -- in `U<NN>.log`, a register
   entry, a PR body -- the sandbox holds nothing, and a run is reproducible
   from a pin in about fifteen minutes anyway. Write the retirement condition
   INTO the `KEEP` so it can actually fire.
5. Stamp provenance: ladder commit, codex commit, sandbox, natives.
6. **Add the line to `U<NN>.log`** -- what was run and what it answered, one
   line, pointing at the commit or the log that holds the detail.
7. Record anything the log does not carry where it survives the session --
   PRIORITIES, the register, JUSTIFICATIONS -- and close the PRIORITIES item
   the task came from.
8. **Commit any work from the current repo, if appropriate.** A run leaves
   tracked files changed in the repo it ran from and nothing announces it:
   `build.py` rewrites eight tracked artifacts, a sweep rewrites every emitted
   `.zig`. Run `git status` in EVERY repo the job touched, not just the one you
   were thinking about, and clear untracked clutter while you are there. Then
   verify the push landed -- `git ls-remote` against the local sha -- because a
   rebased branch fails non-fast-forward and the echo that says "pushed" is
   not the thing that pushed.
