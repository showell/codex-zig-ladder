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

## The whole compiler concatenates on Linux, and it is 2,944,968 bytes

**Measured 2026-08-27, and it retires an assumption rather than proposing
work.** The standing belief was that building a compiler from our own fork
was out of reach. Three of the four reasons turn out not to exist.

**`build/concat-codex-self.ps1` RUNS HERE.** It produced a valid unit --
**2,944,968 bytes, 86 chapters**, `Foreword--Sha512` through
`Types--Unification` -- from `012a9d2e` in a throwaway worktree. The only
thing in its way was PATH SEPARATORS: two literals in the script
(`'codex\compiler'`, `'codex\foreword\core'`) and 98 in
`build/quire-map.ps1`, all of which `Join-Path` turns into a single
filename with backslashes in it on Linux. Nothing conceptual, nothing
about the language, nothing about the host.

**The size is the number that matters, and it is unremarkable:**

    whole compiler (this concat)    2,944,968 bytes
    the seed itself                 2,917,073 bytes
    passes_to_x86 subject           2,652,454 bytes   compiled EVERY REBANK
    codexir subject                 2,636,148 bytes   built here in 6 minutes

**Eleven per cent larger than the biggest thing this box already compiles
routinely**, in a 3 GB guest, in 384 seconds. Not a different order of
magnitude. `passes_to_x86` needs `decks=100`; upstream's own COMPILER-18
notes reach for `-Decks 200` on the full build, so the deck scale is the
knob to expect to turn, not the guest.

**PowerShell was never the barrier either.** `ast/oracle_lib.sh:159`
already shells out to `~/.local/pwsh/pwsh` for eighteen `.ps1` bundlers
on every rebank. And Linux is upstream's own supported host:
`build/vm-config.ps1:15` says "Windows-only; QEMU is the fallback and the
only host on Linux/WSL", while `build/compile.ps1` defaults to
`-MemMB 3072` -- our guest size -- with a retry ladder and `-MemNoCap`.

**What is NOT established.** Nobody has run the compile. The next step is
one seed compile of this 2.9 MB unit through `ring_compile`, which is the
same call the truth arm makes twelve times a rebank, and the honest
unknown is the deck scale rather than the memory. `CODEX_MEM_MB=3072` is
a real ceiling on this box -- the seed guest dies silently above it -- and
raising it is Steve's call.

**Why it is worth doing.** Today a compiler patch can only be tested
through `native/codexir`, which is the compiler as OUR PLUG renders it --
the arm confusion that has cost two wrong reports. A fork-built compiler
is the reference arm for our own changes. It would also let the five
lowering-blocked Roc ports run on our fork without waiting for an Update.

**A PR is possible but not a hand edit.** Both scripts carry "GENERATED
FROM THE CODEX SHELL DSL. Do not edit by hand." The fix belongs in the
generator under `codex/build/`, and the report to Damian is one sentence:
the build's path literals are Windows-only and `Join-Path` does not
normalise them, so the documented Linux host cannot run the documented
build.

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

## native_build.sh should stamp what it built

`native/` is gitignored, so nothing in git says which build is sitting in a
tree. `tiers_run.natives_stamp()` hashes the two binaries and every zig-arm
tier run prints the result, so the identity is machine-checkable -- what no
artifact records is the PROVENANCE behind that identity: which ladder
commit, which codex commit, which sandbox, when.

That gap bit on 2026-08-26. The main checkout's natives were a morning
stale (pre-lambda-lift) while a verified post-lift set sat in a finished
sandbox; the fix was `cp`, and afterwards the only record of what had
happened was a sentence in PRIORITIES. `native/PROVENANCE` is that record,
written by hand, which is exactly the kind of file that goes stale the next
time somebody copies binaries in a hurry.

**The fix is small:** `native_build.sh` writes `native/PROVENANCE` at the
end of a successful build -- stamp, ladder HEAD, codex HEAD and branch,
timestamp, and the tree it was built in. Then a hand-copy is the thing that
has to remember, rather than the normal path, and a stale file is visibly
inconsistent with the stamp beside it.

**Not worth more than that.** A signed manifest or a stamp baked into the
binaries would be the thorough version and neither is warranted: the stamp
already catches "are these the binaries I think", and this only has to
answer "where did they come from".

## Generated files do not belong in the repo tree (Steve, 2026-08-27)

**Steve's ruling, no action taken the night it was made:** *"gitignore is
the root of all evil. We should never be code-generating files right into
the repo. A much better scheme is to use the sandbox."* If we get this
wrong again, he will propose the methodology.

**What prompted it.** `ast/*Harness.codex` is generated by
`ast/gen_*_harness.py` and gitignored in place. On 2026-08-26 I edited
`ast/CodexIrHarness.codex` directly to add finding 49's error gate --
the artifact, not the source. The edit would have been silently
overwritten by the next generator run. **The only thing that caught it
was `git add` refusing the ignored path.** That is a guardrail made of a
side effect.

**Why the sandbox is the better home.** A generated file in the working
tree looks exactly like a source file: it is next to the sources, it
opens in an editor, and nothing about it says "your changes die at the
next build". A generated file under `~/runs/<stamp>/` cannot be confused
for a source, cannot be edited by habit, and cannot be committed by
accident. The gitignore is trying to say "this is not source" in the one
place a reader is least likely to look.

**Same shape as the night's other four errors**, which is why it is worth
writing down rather than shrugging at: `native/codexir` was the compiler
as our plug renders it rather than the reference; the seed probe fed raw
source where the transport wanted a framed blob; `sandbox.sh` defaulted
to codex HEAD and dragged in two unbuilt commits. Every one is "I had a
thing that looked like the thing I wanted."

**Not started.** The migration is not trivial -- `native_build.sh`,
`ast/oracle_lib.sh` and the bundlers all read these paths -- so it wants
its own sitting and Steve's methodology first.

## What the top-level README points at (Steve, 2026-08-27)

**`findings/README.md` YES. `PRIORITIES.md` no.**

The reasoning, which generalises: the README is the outward-facing door,
and the findings register is the PRODUCT -- the defects found, written so
someone else can read them. `PRIORITIES.md` is our own work order. A
visitor wants to know what this apparatus has caught; nobody outside
needs to know what we are doing next Tuesday.

It also means the two documents can drift apart on purpose. PRIORITIES
is allowed to be terse, internal and full of shorthand, because its
audience is us. The README and the register are not.

Raised while briefing cold-agent passes over the README. Pass one reads
the README ALONE (plus the upstream front page) and asks whether a
stranger can orient; pass two gets the register, the scripts and the
queue, and asks whether the README describes the system that actually
exists. Different failures: the first finds what is missing for someone
new, the second finds where the document has drifted from the code.
