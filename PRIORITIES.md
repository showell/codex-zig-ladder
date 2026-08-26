# What is next, in order

Kept here rather than in anybody's head or memory file. If a memory or an
essay disagrees with this file, this file wins. The README's "Processing a
new Update" is the ceremony's step list; on a conflict about ORDER, that
list is the spine and this file adds items and says where they slot.

This is the queue, not the diary. **Done items leave the list and are not
filed anywhere** -- measurements go to JUSTIFICATIONS.md, findings to the
register, and everything else is in git. An item here carries only what is
still true and still to do. There was a DONE.md until 2026-08-25; it was
deleted rather than pruned, because a list of finished work is a thing
nobody reads and everybody has to maintain.

**Cite an item by its TITLE, never by its number.** Numbers are positional
and every rewrite reshuffles them. This file has already accumulated two
references to items that no longer exist -- the refusal-gaps item said
"rebase onto item 2's tip" and the stack item credited "item 3.5's
instrument", both of which left the queue on 2026-08-24 and took their
numbers with them. Two citations in the findings register named a
"PRIORITIES item 1" from a numbering three rewrites old, and were
repointed on 2026-08-25.

**The ergonomic items live in [ERGONOMICS.md](ERGONOMICS.md) since
2026-08-25.** This file is defects and outbound: finding them, proving
them, getting them to Damian. That file is tooling: transport speed,
real sandboxes, foot-guns removed. Splitting them stopped the one
argument that every re-sort had to hold again -- an hour saved on the
verification chain against a wrong answer already shipped are not
comparable, and pretending they sit on one axis is what kept putting
tooling in front of the register.

**The external review is gone, file and item, 2026-08-25** (Steve's
call: stale, and mostly clutter by now). `REVIEW-2026-08-19.md` is in
git if anyone wants it. Batch 2 landed on 2026-08-22 (`e91fdb3`) and
Batch 1 was mined down to nothing over the following days; the last live
finding in it -- the plug fingerprint covering the two chapters instead
of the bundle -- was fixed on the way out, and it was worse than the
review knew: `plug-build-lib.ps1:220-221` bundles PlugTypes and
IRTextParser too, so 6,100 of the plug's 9,537 lines were outside the
guard. What died unfiled with it: a `tests/` directory for the refusers,
and consolidating the three copy-paste QEMU drivers into `codex_vm`.

(Rewritten 2026-08-23, again 2026-08-24, split 2026-08-25. The 08-23
rewrite cut 700 lines to 150 live ones; the 08-24 one re-sorted by
objective; this one moved ergonomics out and re-ordered what is left so
the work that does not need the box comes first.)

## Objectives

Every item opens with an **Objective** naming what it is FOR in one word,
because the same 40-minute run means different things depending on the
answer, and mistaking one for another misprices the work. The vocabulary
is open; these are the words in use.

- **HUNTING.** Fishing for defects that are not ours -- the project's
  product, and the reason the ladder exists. A surprise is the payoff; a
  clean pass is a mild disappointment.
- **DUE_DILIGENCE.** Verifying our own changes break nothing. Green earns
  no celebration; only a red result is information.
- **ERGONOMICS.** Making the work faster and safer. **Not in this file
  any more** -- [ERGONOMICS.md](ERGONOMICS.md) is its queue. The word
  stays in this list because items here cite it.
- **INTEGRITY.** Making the instrument honest. A measurement that can lie
  is worse than no measurement, because the next reader believes it.
  HUNTING and DUE_DILIGENCE are worth exactly what this is worth.
- **OUTBOUND.** Getting a finding to Damian. Nothing else moves the
  project's product across the fence, and nothing happens automatically.

**The venue rule (Steve, 2026-08-22): everything computes on this box.**
Every job below -- natives, tiers, census, sweeps, rebanks -- runs in a
sandbox (`./sandbox.sh <label>`, `. ../env`, detached with a log). Every
compute entry point refuses on a host without `CODEX_LADDER_VENUE`
(`bb39139`), which `~/.codex_ladder_env` exports. One compute job at a
time.

## What to pick up next

**Ordered so the work that does not need the box comes first.** Every
item says which it is:

- **KEYBOARD** -- reading, editing, PR-writing, a `zig run` that takes
  seconds. Runs beside a sweep without touching it; the box has two CPUs
  and ERGONOMICS.md "two CPUs, so keyboard work runs beside a compute
  job" is the standing statement of that.
- **BOX** -- wants QEMU, a natives build, a sweep or a rebank, and
  therefore the lock. One at a time, in a sandbox, detached, with a log.

**Every tag names the ENTRY POINT it means.** A cold read of this queue on
2026-08-25 found three cost claims wrong, and all three came from an item
describing a step in prose while the script that performs it starts a
guest -- "one light run" for a plug with no runner on this host, "3
seconds" for a script with five QEMU legs. One script name per bullet
makes the claim checkable: follow it to `codex_vm.launch`, which every
guest in the tree goes through, and if it reaches there it is BOX.

An item marked BOX is not blocked on anything else; it is blocked on the
box being free. When one is running, the KEYBOARD items above it are the
list.

## The native loop, which changes what is cheap

    native/codexir   .codex -> IR      ~0.1s
    native/zigemit   IR     -> .zig    ~0.05s

Built by `native_build.sh` (11 min on the droplet), no QEMU in either once
built. A Codex source to a running zig program is a third of a second.
**Rebuild both after any emitter change**; the verification chain after
one is natives -> `tiers_run.py` -> `corpus_run.py` -> rebank+sweep, about
an hour end to end, one detached job.

The ladder is still the ladder: expensive, per-Update, and it answers "does
the whole compiler survive transpilation". Everything below is the cheap
loop unless it says otherwise.

---

## 1. One question left behind PR 87, and it needs no plug

**Objective: OUTBOUND, already sent; this is the loose end.** Does a
well-typed Codex program exist in which a definition **tail-calls itself
at non-full arity**? A definition's body has the definition's return
type, and such a call has a function type, so possibly none does.

PR 87 reports the python plug's TCO gate as a MISSING GUARD on exactly
that shape and says plainly that the reachability is unestablished.
Settling it promotes the row to a live defect or closes it. **It is a
type-checker question: no python, no toolchain we lack, KEYBOARD.** If
one exists, the second half is to emit python for it and read
`emit-py-tco-jump`'s output directly rather than inferring from the
answer, since the stale-temporary path produces a plausible number.

**Everything else in this family is answered and upstream.** The
corpus gap and COMPILER-18's precondition -- a second CALL SITE, which
defeats `inline-single-caller` so the partial-application object is
really built and really entered -- are PR 86 and its follow-up comment.
The register carries the five-program table.

**The reusable lesson, which cost the most to learn:** the branch that
became PRs 86 and 87 was ONE branch, and its headline claim was false --
row 1.57 already listed python as compliant on the path that claim
needed. One page, two rows, flat contradiction, caught by a cold read
and not by me. **Cold-read every outbound artifact before it goes.** The
same read caught a reproducer that was full-arity and could not
reproduce, an unverified negative about thirty emitters we have no
toolchain for, and a citation off by two lines.

## 2. Diagnostics as a banked set

**Objective: INTEGRITY. KEYBOARD to build, then one `ast/rebank_all.sh`
to bank -- a sweep will NOT do.** `<unit>-subject.cdx.diags` is written
only by the truth arm's bare-metal compile (`oracle_lib.sh:231-235`);
`ensure_ir.sh` says in its own prose that it writes none, and
`bank_truth.py` copies only `.truth` and `.truth.prov`, so nothing on
disk carries a diags population today. The rebank is the only producer.

**Write the banker as a READER of a run's outputs, not a step inside
it** -- consuming `ast/*-subject.cdx.diags` and `ast/*.ir.diags` after
the fact. Then it can be written and debugged while a run is in flight
and a bug in it costs no compute. **And bank the harness set hash beside
the seed sha** (`truth_prov.set_hash`, the way `bank_truth.py` does for
truths): a diags bank without provenance has the hole the truth bank
closed on 2026-08-24, and this item exists because a number without
provenance says nothing.

**It rides a rebank we were running anyway; it must not ride one that
carries a bundler edit.** The population is a function of the bundled
subject text, so landing any harness or bundler change in the same run
makes a moved count unattributable between the Update, the emitter and
that change -- which is the failure `check_diags.py:70-75` already records
for CDX6020. One bundler change, one sandbox, one diff, per `e91fdb3`.

A pinned count (CDX6020 x43 in
`check_diags.py`) says something changed; a banked set diffed like a
truth file says WHAT, and retires the pins that move whenever the unit
list changes rather than when the source does. 2026-08-25 is the case
for it: the count had not moved, so the pin said nothing, while both
source citations under it had rotted -- one by an Update, one from the
day it was written.

It also closes the hole the cheap sweep leaves. `allcycles.sh` declines
to run the census at all when any `.ir` was rebuilt, which is honest and
which means the sweep we now run MOST is the one that reports no
diagnostics. A banked set is comparable whatever produced the IR.

## 3. Port Roc's closure/recursion snippets into the corpus

**Objective: HUNTING. KEYBOARD to port, BOX to bank.** (Steve, 2026-08-25.)

    https://github.com/roc-lang/roc/blob/main/src/eval/test/eval_closure_recursion_tests.zig

A zig runner holding many small Roc snippets, each with its expected
output. Port the snippets to Codex, give each a `.expected`, and put them in
the corpus.

**Why this file and not any other test suite.** It is closures and
recursion, which is where our findings cluster and keep clustering:
finding 38 (a self tail call in a definition returning a FUNCTION jumps to a
poison address), 39 (a partial-application closure carries no
remaining-arity), 40 (curried application), 42 (a self-tail loop reading a
top-level definition where the source reads its own parameter). Four
findings, one feature area, and our own tier rows for it were written by the
same people who wrote the emitter -- so they encode our assumptions about
what is worth testing. **This corpus was written by another language's team
who never heard of Codex, for the same feature area.** That is the property
we cannot manufacture, and it is the same argument that makes the depot's
`.expected` files worth more than our own comparisons.

**Each port is a judgement call, and the file should say which.** Roc is not
Codex: its closures, its effect story, its numeric defaults and its
evaluation order all differ. A snippet whose expected output depends on Roc
semantics we do not share is not a test of our emitter -- it is a
mistranslation waiting to be filed as a finding. Port what is portable, drop
what is not, and record next to each what was changed and why. A snippet
ported wrongly costs more than one not ported at all.

**The oracle question, before any of it is banked.** Our corpus verdicts
come from the depot's hand-verified `.expected`. These snippets arrive with
ROC's expected output, which is evidence about Roc. What makes a ported
snippet trustworthy here is bare metal agreeing with the zig arm on it, so
the port lands as corpus material first and only earns an `.expected` of its
own once the two arms have been read.

## 4. zigc has a runner now, and one inconclusive result

**Objective: INTEGRITY. BOX for the first run of a session, KEYBOARD
after it** -- the build is cached now, measured 2026-08-25: **first run
7 minutes, second run 8.7 seconds.** The item said KEYBOARD until a cold
read checked it and found `zigc_verify.sh:31` taking the compute lock
with five QEMU legs behind it; the quoted "3 seconds" and "under a
second" were `zig build-exe` and `./zigc < subj`, two steps out of six.
The build half is now behind a fingerprint of the four things that
decide the binary -- the bundled harness, the plug bundle, the seed and
the zig -- so screening candidate subjects costs the seed leg only.
`rm zigc` forces a rebuild. **That was the blocker on this item: the
work left is a SEARCH, and a search over an uncached prefix is the
expensive way to do one.** `zigc` -- the whole compiler as a Linux
process -- was the only claim in this tree with no runner behind it, and
Damian asked about it directly. `zigc_verify.sh` is that runner: it
builds zigc and compiles one program with both zigc and the seed, which
is the check `gen_zigc_harness.py`'s own docstring names and is stronger
than a rung, since the seed is the oracle directly.

It builds clean and runs (17,994 lines, 0 plug refusals, 3 s to build,
under a second to compile). **The byte comparison is inconclusive**: the
README's subject `ast/repro-mid.codex` is gitignored and gone, and the
substituted `ast/repro.codex` produces output ~2 KB larger than the
seed's -- the direction expected from what zigc documents itself as
dropping (proof pruning, dropped-def handling). Two drivers, not two
compilers.

Left: find or write a subject that needs none of the driver's extras, so
the comparison means something. Until then the honest claim is "zigc
builds and runs". Getting there three times cost three wrong assumptions
of mine, each caught by a guard already in the tree -- no mode flags
(CDX9002), the TCP arm on a 13.9 MB IR (the agreement retry refused), and
a naive marker grep that counted a prelude guard
(`findings/prelude-comptime-guards.txt` exists for exactly that).

## 5. Every unhandled construct must refuse BY NAME

**Objective: INTEGRITY, and it is the one that sets the queue. BOX.**
Four
findings now fail as raw zig errors rather than a
`@compileError("zig plug: ...")` marker: `probe-tyvar-leak`,
`probe-show-types`, finding 32's `IrTry`, and finding 40's
`error: expected 1 argument(s)`. `zig-is-unmapped` and
`corpus_run.py --transpile` read only markers, so all four score ZERO in
the ranking that decides what gets worked on, however often they bite.

That is the defect worth fixing: not any one of the four, but a ranking
that cannot see them. The systemic answer -- every unhandled construct
refuses by name -- is worth more than any individual gap, and the census
in "The refusal-gaps branch" is where the count would show it.

## 6. The refusal-gaps branch, rebased and re-verified

**Objective: HUNTING, reached through our own gap-filling. BOX.** Every
family implemented promotes a slab of census programs into the comparing
stage where the depot's oracles can see them. Branch
`zig-plug-refusal-gaps` (fork, 11 commits off the PR-76 tip) has never
been rebased onto u49 nor verified since its cold review. In order:

- Rebase onto the heap branch, `zig-plug-heap-unification` tip
  `8cb8a0e4` (PR 77). **Drop `1b2f089a`** (the `@"..."` quoting):
  finding 35's `1249ad8a` supersedes it with transliteration, which also
  answers the cold review's "quoting breaks when a name is extended
  after sanitizing".
- Fix what the cold review found: f32 approx-eq needs bare metal's
  distinct f32 ordinal path (the band is f64-only); `IrApproxEqExact` as
  `==` diverges from ordinal-distance-0 on same-bits NaN (oracle 1, zig
  0) -- both are register candidates, not just fixes.
- Chain it. The census should promote ~90 refusals; any that lands on
  `differ` is a hunt result.

Residual classes after that batch, measured from the 08-20 census:
curried/oversaturated calls (5), `show` of a Real (2, mirror
`__show_real`, never guess), type-class dictionaries (2), MkTup2
out-of-unit (16 markers, own item: ctor-map + pattern arms), `sin`, one
non-exhaustive switch. Also queued: the JS plug's IrNumLit takes bits as
a NUMBER and its parseFloat is correctly rounded where bare metal's
`__text_to_double` is not -- probe before filing.

## 7. The tiers stay green, and each one earns its keep

**Objective: DUE_DILIGENCE that keeps turning into HUNTING. BOX** for
any new row, since a bare column costs QEMU. The tiers
and probes exist since 2026-08-21; `tiers_run.py` runs them as a set
per Update with `findings/gold/EXPECTED.txt` as the ledger of admitted
disagreements (`ex` noted, `!!` red, `??` stale -- both of the last two
want a human). Standing rules: run after any emitter change; add a row
whenever a finding names a primitive that has none; Codex when the
property is observable from inside a program so bare metal is the oracle,
zig-only otherwise and labelled so; never print an address; keep a
control column.

The set is 22 tiers and GREEN -- re-measured 2026-08-25 against seed
6CF4A8E0 through natives built from the interim pin: **15 green, 7 noted,
0 unexpected, 0 stale**, in about 45 seconds with no QEMU in the path.

**The set runner's own `--zig` mode was broken from the commit that
introduced it until that run.** `--zig` means "the zig arm ALONE" to
`tier_run.py`, which prints one column and compares it to nothing;
`tiers_run.py` passed the flag down and then parsed for a summary line
that no longer existed, so every tier fell through to the last branch and
came back RED. The first run of it read as Update 50 breaking all 21
primitives. Nothing had ever run the mode, which is the lesson: a mode
nobody runs is a mode nobody knows is broken, and this one could only
report failure. It is a two-column run with the bare column pinned to
gold now, refusing by name up front if any column is missing or stale.

Two tiers are the argument for the practice, because each produced a
finding on its FIRST run:

- **Tier 13 (`prim-tailcall`)**, five rows byte-identical on both arms.
  Its sixth row broke both arms and minimizing it produced finding 38, a
  bare-metal fault; the row is gone and the hole is documented in the
  file rather than left as a red. `arg-swap` and `acc-grows` are the
  rows that matter -- an implementation that assigns loop parameters
  without temporaries fails them with a plausible number, not a crash.
- **Tier 14 (`prim-closure`)** produced finding 40, ours, and was
  EXCLUDED from the set until 2026-08-24 because the zig arm would not
  build it. It is back in, and it is now the live detector for
  COMPILER-18: the two controls agree across the arms and the one row
  that disagrees is `under-mutual`, admitted in EXPECTED.txt as `ex`.
  **The day bare metal keeps the arity, the arms will agree and the mark
  becomes `??`** -- the ledger announcing a fixed COMPILER-18 without
  anyone remembering to check. That is what a tier is for, and it could
  not do it while one arm refused to compile.

## 8. The stack is measured now, and the emitter's prose about it is wrong

**Objective: INTEGRITY, already half done. BOX.** `stack_probe.py` --
finding
37's instrument -- bisects the emitted thread stack against real
documents and censuses the failing backtrace, so "512 MB" is a number
with a mechanism behind it rather than a constant nobody has questioned.
Left:

- **Nothing is banked, and the blocker is GONE.** The only measurement so
  far was a branch-arm one and deliberately not gold, because a bank
  stands behind the release's emitter. Update 50 absorbed our emitter
  verbatim, so a verbatim-emitter run now exists and the condition this
  bullet was waiting on is met. Bank it.
- **Only `codexir` is measured.** `zigemit` and the other natives have
  their own recursion and are unmeasured, so what one input needs is
  known and what every input needs is not. The 512 MB must not be
  lowered before that sweep -- which is why the item below corrects the
  PROSE and leaves the constant alone.
- **`zig-main`'s prose was wrong, and the correction is SENT as PR 84**
  (2026-08-25). It blamed the lexer's scan-token/skip-prose-line pair,
  which measures FLAT, and then argued that self-tail-call elimination
  could never remove the need for the stack -- while PR 81, which emits
  those loops, and PR 82, which turned the parser's top-level scans into
  self recursion, stood beside it in the same push. Both claims in the
  replacement were read out of the swept `ast/parse.zig` rather than
  argued, and the residue that survives is counted: two arms of
  `parse-top-level` still leave through a mutual cycle, worth eight
  frames on the 2.5 MB subject and three on the parser. The constant is
  untouched. Verified inert first (ladder tag `stack-prose-verified`,
  JUSTIFICATIONS "A prose block moves the plug and not its output").

## Not an item: one zig program, and it exists now

**Built 2026-08-25 (Steve's call to take it up again): `codexzig_build.sh`,
`native/codexzig`, Codex source in and zig out in one process.** Not a
merge of two emitted zig files -- one Codex bundle, codexir's chapter set plus the emitter and the IR text
parser, with the pipe between the two halves replaced by a `let`.
Byte-identical to `codexir | zigemit` on 85 programs, and **a fixed point:
given its own 2.8 MB bundle it emits the 2,273,737 bytes of zig that the
seed-plus-ring-plug path emits from the same source, and a binary built from
that output emits them again.** (The two BINARIES differ, because
`zig build-exe` is not reproducible on zig 0.16.0 -- the same file at the
same path twice already gives different bytes. The emitted SOURCE is the
fixed point.)

**We keep the two separate binaries**, for the reason that has not changed:
the intermediate IR is what most of the ladder's questions are asked about.
codexzig is the artifact for other people, and it is also its own regression
test -- `--check` byte-compares it against the pipeline.

**It is verified, and it earns its keep as an instrument.** 577/577 corpus
programs byte-identical to the pipeline; 181 of them built, run and matching
the depot's `.expected`; all 14 unit subjects identical from 0.12 MB to
2.87 MB; and its own bundle a fixed point. Two runners keep those true --
`codexzig_corpus.py` and `codexzig_scale.py`. It also produced **finding 45**
(the deck reservation is advisory) in ten minutes and no QEMU, which is the
argument for it as more than publicity.

**What it does NOT replace: the bare-metal oracle.** Everything codexzig
checks is the zig arm against itself or against `.expected`. The rungs
compare the zig arm against BARE METAL, and a defect the plug and the seed
share -- or one the emitter makes identically on both paths -- is invisible
here and visible there. codexzig is the fastest way to learn that
transpilation still works across the whole compiler; it is not evidence that
the answer is right.

**If it is ever published**, three things settled while the idea was being
argued and are worth not re-deriving: lead with the strongest true claim,
which is that the emitted compiler's output is byte-identical to the native
x86-64 backend across all fourteen rungs -- "zig compiles another language"
is the weakest thing that is true here; say plainly and first that it is
machine-generated zig, because that audience will read one function and
know, and owning it reads as confidence; and the compiler is Damian's while
the ladder is only the witness, so anything published says which is which
and he sees it first.

---

## Outbound queue

**Standing: a finding in `findings/README.md` reaches Damian only when
someone opens a PR carrying it. Nothing notifies anyone.** The route is
`contrib/README.md`: a small branch off `upstream/master` with a
`Ladder:` line naming a ladder tag, and the entry written into
`codex/plugs/plugs-backlog.md` or `codex/compiler/compiler-backlog.md`.
Formats differ -- the compiler backlog is a TABLE, the plugs backlog is
bold prose entries.

**Standing (Steve, 2026-08-25): MEASURE AGAINST OUR FORK'S STACK, not
against bare `upstream/master`, and SAY SO IN THE PR.** The tree we believe
in is upstream plus everything we have sent and they have not yet taken --
the optimistic version of what we hope becomes the next Update. Testing
against bare upstream measures a compiler we already know is missing our
own fixes, so a number taken there is not a number about the thing we are
building. Stacking in the PR branch itself is optional; naming the stack the
numbers were measured on is not.

**Standing, learned the hard way the same day: REUSE THE WHOLE RUNNER, not
half of it.** `codexzig_corpus.py` fed `codexir` the raw `.codex` file where
`corpus_run.py` feeds it a CITE-RESOLVED unit. 77 of 181 well-behaved
programs came back "refused", naming types their cited chapters declare as
undeclared identifiers -- and `corpus_run`'s own comment on the line I did
not copy says exactly what it would look like: "codexir resolves nothing, so
without this the call arrives as an undefined name and the plug's fallback
fires, which looks exactly like an emitter gap and is not one." An hour went
into suspecting the emitter, then our own rename, then an unmerged fix,
before the sandbox's kept artifacts showed the IR itself was missing its
`(ctors ...)` line.

**Standing: re-verify every line citation against the PR's base**, not
against the tree the finding was made on. They usually agree; PR 78 is
why it is a step rather than a courtesy.

**Standing: the cold read is not optional, and it earns its keep every
time.** PR 88's first draft claimed 38 of 56 plugs were affected and the
other 18 "take other paths and are not affected"; the true answer is
that none of the 56 consults the host selection. The same draft had its
failure path backwards. Both were read rather than run, and both were
caught by the cold agent rather than by me -- which is now three
outbound artifacts in a row whose HEADLINE claim was the wrong one.

**Standing: a cold agent reviewing an outbound artifact needs the REPO,
not just the artifact.** PR 78's first review was firewalled from the
tree and its findings were mostly "I cannot verify this"; the second
opened every cited line and found two false claims, which is why 78 was
closed rather than left open and wrong.

**ALL SIX LANDED 2026-08-25**, absorbed by Update 50's interim push
(github `111c0fea`, main 19116/19117/19125/19131/19133/19140; the
account is `docs/PM/Active/GitHubUpdates/GitHubUpdate50.md`). Every one
was closed upstream with credit and a checkable commit, and the queue
emptied for the first time since it was written. **One is out again:
PR 84**, the zig plug's stack-note correction, sent 2026-08-25 and
verified inert first (ladder tag `stack-prose-verified`) -- the stack
item above has the substance. What landed:

- **PR 77** (19125) the zig one-heap, with the emit deck's flat term
  24 to 28 MB riding it; **PR 81** (19131) self tail calls become
  loops; **PR 83** (19133) over-application applies the rest. The
  released `ZigEmitter.codex` is byte-identical to the clean merge of
  81 and 83 on 77 -- verified here, not taken on trust.
- **PR 82** (19140) the parser's mutual-tail top-level scans, with its
  COMPILER-19 row. One duplicated prose block was trimmed on absorb and
  said so in the closeout; the trim is real and is the parse-side twin
  of the scan-side rationale, so the mechanism survives and the
  3,385-frame parse measurement does not.
- **PR 79** (19116) COMPILER-18 and **PR 80** (19117) plugs 1.57, both
  doc-only rows. 1.57 drew its ruling (call 21, RULED BINDING);
  COMPILER-18 is item 1 in the rulings queue and still open.

**The verbatim rule cost nothing this time.** Step 4's working rule is
sweep the release's emitter as shipped; the shipped emitter now IS our
work, so the `u50` pin is length ZERO and the arms measure the depot
with no local patch under them. That is the flow working as designed,
and it is worth saying once while it is true.

**Standing, learned from finding 41 (RULED, call 21, 2026-08-24): when a
finding needs a toolchain we do not have, hedge the row and name who can
settle it.** We reported riscv and java at source level, said the ladder
host has no JDK, and retracted the promise to run it -- and the ruling
arrived anyway. Do not hold the finding back, and do not imply a
follow-up we cannot make.

**The queue is EMPTY as of 2026-08-26, and EIGHT PRs are open:**

- **84** the zig plug's stack-note correction (verified inert first,
  ladder tag `stack-prose-verified`)
- **85** finding 42, the self-tail loop reading a top-level definition
  where the source reads its own parameter -- OURS, three hunks, tag
  `shadow-loop-rename`
- **86** the plug corpus cannot reach the Rulebook's over-application
  case, plus COMPILER-18's third entry point; a follow-up comment
  carries the isolated precondition and CORRECTS the row it is on
- **87** the python plug's TCO keyed on name and not arity, LATENT
- **88** finding 43: no plug `run.ps1` consults the VM host selection in
  the config it sources, so no plug runs on Linux -- doc-only, plugs
  backlog 1.61, tag `plug-run-no-vm-host`, and it carries an ASK (is
  Linux a supported host for RUNNING plugs, or only for building them?)

- **89** `plugs/common/IRTextParser.codex` takes the `ir-` prefix its
  counterpart `IRTextEmitter` already uses on 99 of 106 definitions. Nine
  of its names collide with the compiler's own Lexer and Parser, so no
  program can carry both parsers; 31 definitions renamed, 156 insertions
  and 156 deletions, no semantics. Verified on the zig arm only and it
  says so -- three C# call sites move with it and we have no toolchain to
  run them. Tag `codexzig-fixed-point`.
- **90** finding 44 (COMPILER-20): a record's implicit type parameters are
  derived by the IR text emitter at serialisation time and not carried on
  the AST, so every consumer of the AST that is not the wire sees an
  incomplete type. Doc-only. Tag `codexzig-fixed-point`.
- **91** finding 45 (COMPILER-21): the deck reservation is advisory --
  overrunning it is detected, printed, ignored, and then faults at twice the
  reservation. Doc-only, with a ten-second no-VM reproduction. Tag
  `deck-reservation-advisory`.
On top of the six that landed in Update 50's interim push. Nothing is
prepared and unsent, and the one question any of them left is the item
above.

## Per-Update ceremony

README "Processing a new Update" is the spine: read the release, pin a
branch, tier bare columns, rebank on the droplet, bank over green arms,
`bank_diff.sh`, re-pin POLICY from the census, README timings and table,
tag `uNN-14of14`; then rebase the branches, natives, tiers, census. u49
took one evening end to end and Update 50's interim absorb took two
sittings of a single day, most of it unattended.

**Update 50's interim push is mid-ceremony (seed `6CF4A8E0`).** Done: the
pin, the tier bare columns, the rebank (14/14 green, 731 s), the bank
(`truth/seed-6cf4a8e0/`, sidecars included), `bank_diff.sh`, the census
read, and the README's table and timings. What `bank_diff.sh` says is
worth keeping: **`parse.truth` moved and nothing else did.** It moved for
a reason already known -- Update 50 replaced the four `try-*` top-level
scans with `parse-top-item`, `scan-top-item` and `parse-top-def-item`
over two new item types, one def fewer and 17 tokens more -- so the
thirteen unmoved rungs are the story and the fourteenth is PR 82's shape
arriving. The census needed no re-pin (CDX6020 still reads 43); its two
source citations did, and they are cited by function now.

Left:

- **Tag: DONE.** `seed-6cf4a8e0-14of14` on `9a1e424`, pushed. Steve chose
  the name on 2026-08-25; it breaks the `uNN-14of14` shape on purpose,
  because what it names is a bank and not an Update.
- **Natives, tiers and the census: DONE.** Sandbox
  `20260825T135832Z-u50-natives-tiers`, natives `d7e148e7b699` built from
  the pin, then `./tiers_run.py --zig` green: 15 green, 7 noted. It cost
  one instrument fix first -- see the tier item above.
- **The census RE-PINNED, and it found something.** 593 programs, 325
  clean, banked to `corpus/census.json` (natives `48af65aa7cb7c47d` /
  `3550e6d78dc71c67`). Every emitted zig moved, as an emitter change
  requires, so all 325 were rerun; **three verdicts moved and one is a
  regression: `dtls-fragment`, match -> refused.** That is
  **finding 42**, ours, from PR 81 and already upstream -- a self-tail
  loop reading a top-level definition where the source reads its own
  parameter. The refusal is luck; the defect is silent. **It is now the
  most valuable thing in this file.**
- **The prose branch's due-diligence run: DONE and GREEN.** Sandbox
  `20260825T142003Z-prose-verify`, 14/14 rungs green in 1627 s, and all
  thirteen emitted `.zig` files byte-identical to the seed-6cf4a8e0
  sweep's -- from a plug whose bundle is 22 lines larger and whose
  fingerprint moved `1aba3c41196cb74e` -> `73dc2f1e8cd0ed81`
  (JUSTIFICATIONS, "A prose block moves the plug and not its output").
  The gate Steve set was satisfied and the correction went out the same
  day as PR 84.
