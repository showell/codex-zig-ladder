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

## DONE 2026-08-27: the ports branch refuses a commit that is not a test file

A compiler fix landed on `roc-ports-batch2` TWICE in one evening, both times
because `git rebase` leaves HEAD on the branch it just rebased and the next
commit went wherever HEAD happened to be. Both had to be cherry-picked onto
`roc-ports-type-recovery` and the ports branch reset, and the second one was
caught only because a sandbox's START line printed a commit that did not
contain the fix being measured.

`.git/hooks/pre-commit` in the depot clone now refuses any staged file outside
`codex/test/` while on that branch, and prints the four commands that move it.
Verified by trying to commit a `Desugarer.codex` change to it.

Local to this box, since hooks are not tracked. **The general shape is worth
keeping in mind: a rule that has been broken twice is a rule the tool should
enforce, not one to be more careful about.**

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

## verify_emitter.sh must die with its children

**KEYBOARD. Entry point: `verify_emitter.sh`, the `leg` function.**

Objective: **ERGONOMICS.**

Killing the chain does not kill what the chain started. Measured twice on
2026-08-27, both times while abandoning a run whose commit had been
superseded:

- `kill` on `verify_emitter.sh` left `ast/allcycles.sh` running. It went
  on to start a FRESH guest after the chain was already gone.
- The next chain's leg 0 then died in one second on *"A GUEST IS ALREADY
  RUNNING, and it did not take the lock"* -- the compute lock working
  exactly as designed, refusing beside an orphan nobody owned.
- The orphan had to be hunted by PID both times. The second one had been
  alive eighteen seconds when it was found, which means it was started
  AFTER the kill, by a child that had not noticed its parent was gone.

The failure is loud, which is the only reason this is an ergonomics item
and not a defect: the lock catches it, names it, and refuses. The cost is
the two minutes of hunting and the false start.

**The fix is the shape, not another guard.** `leg` should run each leg in
its own process group and the script should `trap` INT/TERM to signal that
group, so one signal reaches the whole tree. `pkill -f` is NOT the answer
and must not become it: run from a Claude shell it matches the shell's own
command line -- observed on 2026-08-27, `pgrep -af 'verify_emitter|qemu'`
returned the very bash running the pgrep -- so a `-f` pattern broad enough
to catch the legs is broad enough to kill the session issuing it.

**A second, smaller thing in the same file.** `ast/ringplug_build.sh:36`
pipes `ring_compile.py` through `grep -E "error|SIZE" | head -10`. When
the compile refused for a reason matching neither word, the pipe swallowed
it and the caller printed a bare `PLUG COMPILE FAILED` with no
diagnostic -- and the pipe masks the exit code besides. That is the
standing pipe trap, in a script we own. The refusal message was recovered
only by running `ring_compile.py` by hand.

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

**Amended 2026-08-29, and it makes the item cheaper.** The stamp is
machine-checkable WITHIN a tree and nowhere else. Both natives already bake
their build directory in as a literal -- `<sandbox>/ladder/ast` reads out of
zigemit and codexir with a plain `grep -a` -- so the sha over their bytes
moves whenever the sandbox does. Two builds of identical source in two
sandboxes never stamp alike. Anything that compares stamps across runs is a
guard that cannot fire, and `dup.sh` shipped one; it is gone.

Two consequences. Comparing a stamp to a remembered value is worthless, so
"did my change reach this build" needs a BEHAVIOURAL falsifier -- a program
that compiles one way and not the other -- and never a stamp. And the
PROVENANCE line this item asks for is half-written already: the tree a
binary was built in is recoverable from the binary, so the file only owes
the two commits and the timestamp.

## The corpus bank's staleness gate can only ever say "stale" (2026-08-29)

`corpus_run.py` opens its verdict diff with
`*** THE BANK IS NOT ABOUT THIS TREE ***` whenever `bank_describes_this_tree`
is false, and that function compares `meta.tools`: the shas of the two native
binaries. Zig bakes the build directory into each binary for its stack
traces, so those shas move whenever the tree moves -- and every ladder run
happens in a fresh sandbox on purpose.

The gate therefore fires on every run regardless of what the source did. A
bank taken today is "not about this tree" tomorrow. It is the mirror of the
stamp guards deleted in `bd570e7`: one could only ever pass, this one can
only ever fail, and both look like checks.

**Measured, not argued.** Four mutually distinct tool identities for what is
substantially one toolchain: bank `6c1711aa/6eb2621b`, main checkout
`10850a2d/9fdf7112`, dup-arms `dfed25e4/8e5b843f`, dup-baseline
`c27ca4e2/f715286e`. The main checkout's binaries carry
`/home/steve/runs/20260826T160728Z-u50-harness-lift/ladder/ast` -- built in a
sandbox on 08-26 and copied in, path and all.

**What it costs.** U53.log carried "re-bank the corpus census at U53, so
there is finally a comparand that records its own base" as an open item. It
would not have worked: the new bank goes stale the moment the next sandbox is
cut. The 2026-08-29 dup-arms run paid for this the long way -- its corpus leg
could conclude nothing, and settling the question needed a whole second arm.

**BUILT the same day** (`tool_identity.py`, Steve's call to go ahead). The
tool identity is now SOURCE-derived: the sha of the bundled subject, the ring
plug bundle that transpiles it, the seed that compiles it and the zig that
links it -- the four inputs `build_one` actually feeds a native, none of which
mentions a path. `zigc_verify.sh` had exactly this list inline since 08-25 and
was its first user; it calls the module now.

Measured before it was believed: the same four inputs in a different sandbox
give the same fingerprint, an unbundled tree answers "cannot tell" rather than
a wrong number, a byte added to the plug bundle moves BOTH tools, and a byte
added to one subject moves only that one. `bank_describes_this_tree` answers
three ways now -- same, different, and UNKNOWABLE for a pre-08-29 bank whose
`tools` field holds binary shas that cannot be compared to anything. **`same`
is reachable for the first time.**

The root-cause fix -- keeping the path out of the binaries so they are
reproducible -- was NOT done and is a separate question. It trades against the
panic traces the corpus reads when a program crashes, and nothing needs it now
that identity comes from source.

**Re-banking the corpus census at U53 is now worth doing**, and was not before:
a bank written today records `built_from` and a run tomorrow can agree with it.
Until that bank exists, a bank diff is still not evidence. Two arms, or
nothing.

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

## DONE 2026-09-01: a truth bank is named for the SEED, and the seed does not identify the tree

**Objective: INTEGRITY.** Found 2026-09-01 while setting up the Rust front
end's golds, before it cost anything.

`bank_truth.py` writes to `truth_dir(s['slug'])`, and the slug comes from
`seed_identity.update_label(seed_sha256())` -- so a run on this box today banks
to `truth/u53/`. **Our ten open PRs do not move the seed** (`seed/Codex.cdx` is
tracked upstream and a PR against the compiler source does not rebuild it), so
running `bank_truth.py` on `master-plus-outbound` would write our unlanded
branches over the RELEASE bank under the name `u53`, and every later comparison
would silently measure against our own stack.

Nothing refuses it. `truth_prov` checks the seed and the harness content, and
both match -- the harness did not move, only the compiler under it. The banked
set records `SEED` and `ARMS` and **no codex commit at all**, so a bank cannot
say which tree it describes beyond naming a seed that several trees share.

The measurement that shows it is real: rebanked on `master-plus-outbound`,
`lex.truth` goes 5,339 -> 5,335 tokens with its first difference at
`L262C11 |entry|` -- PR 114's added line in `scan-string-body`. `parse.truth`
is byte-identical to `truth/u53/`. Same seed, two different trees, and only one
of them is Update 53.

`rebank.sh` already states the rule for the CORPUS census -- *"BANK AT THE
RELEASE, NOT AT OUR STACK ... a bank taken on our stack would silently fold our
own branches into every future comparison"* -- and `bank_truth.py` is the same
argument with no guard behind it.

**Fixed.** `seed_identity.tree_stamp()` answers the question SEED could not,
and `bank_truth.py` refuses on it. The release commit needs no lookup table:
the seed changes only when a release rebuilds it, so THE NEWEST COMMIT
REACHABLE FROM HEAD THAT TOUCHED `seed/Codex.cdx` is the release this checkout
descends from, and HEAD must BE it. Deriving it rather than tabulating it is
what keeps it honest across Updates nobody has taught it about -- the failure
`update_label` has now had twice.

The gate applies only where a name can collide: an unreleased seed already
banks as `seed-<hash>`, so only a bank named `uNN` can overwrite a release.
`--force` still gets through and must TYPE a reason, which lands in the bank;
a `--force` with no reason is the silent overwrite wearing a flag, and is
refused. Every bank now carries `TREE` beside `SEED` -- head, branch, release
commit, verdict.

**Both arms shown to fire**, because a gate nobody has watched work is a gate
nobody knows works. `tree_stamp` takes a rev so the refusal can be exercised
without checking anything out. At `u53-rebank`: `HEAD is it`, and banking
proceeds to the ordinary rung checks. Pointed at the sandbox's
`master-plus-outbound` checkout -- **the exact run that would have overwritten
`truth/u53` this morning** -- it refuses before touching a file and names the
branch. `truth/u53` byte-identical after all three probes.

`codex_branch()` moved here from `bank_golds.py` on the way, that being its
second caller.

The Rust golds never needed the gate: `bank_golds.py` keys on the pin and banks
outside every repo, so the release banks stay what they say.
