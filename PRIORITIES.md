# What is next, in order

Kept here rather than in anybody's head or memory file. If a memory or an
essay disagrees with this file, this file wins. The README's "Processing a
new Update" is the ceremony's step list; on a conflict about ORDER, that
list is the spine and this file adds items and says where they slot.

This is the queue, not the diary. **Done items leave the list** -- DONE.md
holds one line and a pointer each, measurements go to JUSTIFICATIONS.md,
findings to the register. An item here carries only what is still true and
still to do.

**Cite an item by its TITLE, never by its number.** Numbers are positional
and every rewrite reshuffles them. This file has already accumulated two
references to items that no longer exist -- the refusal-gaps item said
"rebase onto item 2's tip" and the stack item credited "item 3.5's
instrument", both of which left the queue on 2026-08-24 and took their
numbers with them. DONE.md's older entries name numbers from the
numbering in force when they were written; read them as history, not as
pointers into this file.

(Rewritten 2026-08-23, again 2026-08-24. The 08-23 rewrite cut 700 lines
to 150 live ones; this one re-sorted by objective, put ERGONOMICS at the
front, and dropped the parked notebook/Prism bookmark -- that work is the
essay-repl-server's REPL now, and Steve tracks it himself.)

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
- **ERGONOMICS.** Making the work faster and safer: transport speed, real
  sandboxes, foot-guns removed. **This is why ergonomic items sit at the
  front of the queue** -- they are the only kind whose payoff multiplies
  across everything below them, and an hour saved on the verification
  chain is an hour returned every time it runs.
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

## 1. A fresh sandbox cannot sweep, and that costs half an hour every time

**Objective: ERGONOMICS.** `allcycles.sh` runs the zig and ring arms
against truths already banked, but `zig_arm` refuses without a per-sandbox
`ast/<rung>.ir`, and a fresh sandbox has none. So every sweep after an
emitter change pays a full rebank first -- roughly 27 minutes of truth arm
to produce inputs the bank could have provided -- before the 11 minutes
that answer the question actually asked.

Make `allcycles.sh` REGENERATE a refused or missing `.ir` instead of
stopping: `ring_compile.py` per unit plus `stamp-ir` is the whole cost.
The f35 chain lost a run to this on 2026-08-23, and the finding-40 fix
paid the full 27 minutes for it on 2026-08-24 with an unchanged seed and
an unchanged bare-metal arm -- nothing about the rebank was in question,
it was there to make files.

This is the highest-leverage item in the queue: it is charged against
every emitter change, which is the change we make most.

## 2. Launching a detached job is a foot-gun with a live tripwire

**Objective: ERGONOMICS.** `ast/rebank_all.sh` relaunches itself detached
so a dead terminal cannot kill an hour-long run. The detached child is
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

Two things to fix, and the first matters more:

- **A refusal must reach the launcher, not only the log.** The parent's
  early `flock -n` check exists for this and did not fire, because the
  lock was genuinely free; what refused was the child's evidence check,
  after detaching. Have the child report a refusal back to the terminal
  (or have the parent run the evidence check too, while it is still an
  ancestor of nothing and can speak).
- **Walk the launcher's ancestry before it exits**, or record it: pass
  the whole chain rather than a pid that is about to die.

Until then: launch through a wrapper script whose own argv does not match
`EVIDENCE` (`qemu-system|rebank_all|allcycles\.sh|corpus_run|native_build`),
and never leave a `sleep` in the launching shell.

## 3. Provenance watches one file too many

**Objective: ERGONOMICS.** The truth sidecars hash `oracle_lib.sh` whole,
so a guard-or-comment edit to the zig-arm half invalidates every recorded
truth's provenance -- it cost a full truth-arm re-measurement on
2026-08-20. Segregate by volatility: the truth-arm machinery (mode_flags,
truth_arm, split plumbing) into its own sourced file the sidecar watches;
the zig-arm half free to move. Do it right after a bank lands, never
between recording and banking.

## 4. Execute the rung renames (proposed, not started)

**Objective: ERGONOMICS.** `RENAME-PROPOSAL.md` has the mapping and
migration plan (temporary file; the executing commit deletes it). No
re-bank needed -- no rung name appears inside a banked truth -- so 42
files move by `git mv` unchanged. The hazard is a foot-gun of the worst
kind: `ast/` outputs are gitignored, and three sites spell old names as
literals (`ast/f3_run.zig:222`, `ast/f4_boot.py:26-29`,
`overnight_verify.sh:99-100`); a missed one reads yesterday's dump and
passes GREEN. Clean the orphans before the first sweep. Waits until the
findings that cite current names stop being re-read.

## 5. The refusal-gaps branch, rebased and re-verified

**Objective: HUNTING, reached through our own gap-filling** -- every
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

## 6. Every unhandled construct must refuse BY NAME

**Objective: INTEGRITY, and it is the one that sets the queue.** Four
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

## 7. The tiers stay green, and each one earns its keep

**Objective: DUE_DILIGENCE that keeps turning into HUNTING.** The tiers
and probes exist (DONE.md 2026-08-21); `tiers_run.py` runs them as a set
per Update with `findings/gold/EXPECTED.txt` as the ledger of admitted
disagreements (`ex` noted, `!!` red, `??` stale -- both of the last two
want a human). Standing rules: run after any emitter change; add a row
whenever a finding names a primitive that has none; Codex when the
property is observable from inside a program so bare metal is the oracle,
zig-only otherwise and labelled so; never print an address; keep a
control column.

The set is 22 tiers and GREEN. Two of them are the argument for the
practice, because each produced a finding on its FIRST run:

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

**Objective: INTEGRITY, already half done.** `stack_probe.py` -- finding
37's instrument -- bisects the emitted thread stack against real
documents and censuses the failing backtrace, so "512 MB" is a number
with a mechanism behind it rather than a constant nobody has questioned.
Left:

- **Nothing is banked.** The only measurement so far is a branch-arm one
  and deliberately not gold: a `uNN` bank stands behind the release's
  emitter. Bank when a verbatim-emitter run exists.
- **Only `codexir` is measured.** `zigemit` and the other natives have
  their own recursion and are unmeasured, so what one input needs is
  known and what every input needs is not. The 512 MB must not be
  lowered before that sweep.
- **`zig-main`'s prose names the wrong cycle** -- it blames the lexer's
  scan-token/skip-prose-line pair, which measures flat (100,000
  consecutive prose lines run in a 256 KB stack). A justification that
  is wrong is worse than none, since the next reader trusts it. Correct
  it upstream beside the parser fix (PR 82).

## 9. Diagnostics as a banked set

**Objective: INTEGRITY.** A pinned count (CDX6020 x43 in
`check_diags.py`) says something changed; a banked set diffed like a
truth file says WHAT, and retires the pins that move whenever the unit
list changes rather than when the source does.

## 10. The external review, batches 1 and 3

**Objective: INTEGRITY** -- these are wrong-bank and wrong-PASS closers.
`REVIEW-2026-08-19.md` (Marley, ~34 findings); Batch 2 is done (DONE.md
2026-08-22). Each batch's first act is re-checking its list against the
tree, since several have been fixed in passing.

- **Batch 1, keyboard-only:** `plug_run` truncation-reads-as-success,
  QEMU orphan try/finally, rm-stale-artifacts-first family, checks that
  report but do not refuse, small correctness (f4_boot, plugcycle,
  seed_identity label, pcap coverage), doc seams. Commit per finding.
- **Batch 3, structural, its own session, net first:** `tests/` for the
  refusers, THEN driver consolidation into codex_vm and the
  harness/bundler dedup; unify the two plug fingerprint guards on the
  ring model.
- Declined or deferred with reasons in the review response: tracked
  census json stays; LICENSE is Steve's call; errors='replace'
  byte-compare rides Batch 3.

## 11. Venue plumbing, what is left of it

**Objective: ERGONOMICS.** Pushes go through the deploy keys
(`github-ladder`, `github-nr`) since 2026-08-23. The straw scripts
(`droplet_compile/transpile`, the two-venue sweep) are NOT retired: they
are the keyboard-tempo tools, and both models share the box under the
compute lock. Nothing else here is open; the sandbox and `.ir` items
above carry what used to sit in this one.

---

## Outbound queue

**Standing: a finding in `findings/README.md` reaches Damian only when
someone opens a PR carrying it. Nothing notifies anyone.** The route is
`contrib/README.md`: a small branch off `upstream/master` with a
`Ladder:` line naming a ladder tag, and the entry written into
`codex/plugs/plugs-backlog.md` or `codex/compiler/compiler-backlog.md`.
Formats differ -- the compiler backlog is a TABLE, the plugs backlog is
bold prose entries.

**Standing: re-verify every line citation against the PR's base**, not
against the tree the finding was made on. They usually agree; PR 78 is
why it is a step rather than a courtesy.

**Standing: a cold agent reviewing an outbound artifact needs the REPO,
not just the artifact.** PR 78's first review was firewalled from the
tree and its findings were mostly "I cannot verify this"; the second
opened every cited line and found two false claims, which is why 78 was
closed rather than left open and wrong.

Open, none landed:

- **PR 77** -- the heap unification, sent 2026-08-23 on `8cb8a0e4`
  (21 commits on the u49 pin); verified at ladder tag `pr77-verified`.
  Everything below that is stacked waits on this one.
- **PR 79** -- finding 39, the closure-representation defect, one
  `compiler-backlog.md` row (COMPILER-18) off `upstream/master`
  5b8091e2, tag `closure-arity`. Doc-only: THEIRS, and we have no fix.
  Asks ONE ruling -- whether the closure gains a remaining-arity word,
  or under-application is refused where emitted -- and deliberately does
  not add a pinning fixture, because accepting a red arm is Damian's
  call. **Tier 14 is now the fixture, on our side of the fence.**
- **PR 80** -- finding 41, the curried-application rule, one
  `plugs-backlog.md` row (1.57) off 5b8091e2, tag `curried-apply`.
  Doc-only: THEIRS. Asks ONE ruling -- whether over-application is
  required of every plug that keeps an arity map, or whether some are
  exempt and `DevelopersRulebook.md:258` should say which. The row
  states in its own text that riscv's and java's runtime consequence is
  INFERRED from the dispatch code, because the plug harness is
  PowerShell and this host has none.
- **PR 81** -- finding 33's fix, the zig plug's tail-call loop.
  **Stacked on PR 77**: cut from `zig-plug-heap-unification`, so its
  first 21 commits are 77's and only the last four are this PR's; the
  true three-dot diff is two files. Stacked deliberately rather than
  rebased, because the 14/14 sweep verified THAT tree and a rebase would
  have made the branch a tree nothing had measured. Tag `tail-calls`.
- **PR 82** -- finding 37, the parser's mutual-tail top-level scans, two
  commits off 5b8091e2: the `Syntax/Parser.codex` restructure and its
  `COMPILER-19` row. Tag `parser-self-tail`. Measured on our tail-call
  branch (the pin's plug has no self-TCO, so the change would have
  flattened nothing there), but the commit carries the parser change
  ALONE, and that rebase is VERIFIED rather than assumed: `Parser.codex`
  at 5b8091e2 is byte-identical to the base it was measured against, and
  the file the commit produces is byte-identical to the verified one.

Ready or nearly so:

- **Finding 40's fix**, branch `zig-plug-curried-apply` (`835639b7`, off
  `8cb8a0e4`), NOT sent. Both sites in one commit: `emit-zig-apply`
  gains an `args > ar` branch, and `zig-closure-make` stops passing
  type-spine parameters flat. Tier 14 is back in the set and the set is
  green; **what it waits on is the sweep**, because an emitter change
  that has only passed its own reproducer has not been priced. When it
  goes it is a sibling of PR 81, stacked on 77, not stacked on 81.
- **Finding 36** (python plug's TCO keys on name, not arity) -- MEDIUM
  confidence, reproducer NOT run, wants a `plugs-backlog.md` row once it
  is. It is the same rule as findings 40 and 41 broken at a fourth site,
  so **if PR 80 draws a ruling, 36 and 40 both follow from it** rather
  than needing their own arguments. Cheapest order is to wait for 80.
- **The one-line corpus fix that would have caught all four.**
  `codex/plugs/test-input/partial.codex` covers over-application of a
  LOCAL, but its only definition is `add3`, which does not return a
  function -- so the branch every one of these plugs gets wrong is
  unreachable from the corpus. `test-plugs.ps1` then never compiles what
  it emitted. Worth offering upstream alongside PR 80: it is the
  cheapest thing in this queue and it is the reason the family drifted.

## Per-Update ceremony

README "Processing a new Update" is the spine: read the release, pin a
branch, tier bare columns, rebank on the droplet, bank over green arms,
`bank_diff.sh`, re-pin POLICY from the census, README timings and table,
tag `uNN-14of14`; then rebase the branches, natives, tiers, census. u49
took one evening end to end (DONE.md 2026-08-22) and the next one should
take less, since the droplet does all of it now.
