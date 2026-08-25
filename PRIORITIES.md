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

## 1. A fresh sandbox can sweep now, and the wiring is proven from empty

**Objective: ERGONOMICS. DONE except the census bullet.** The problem it
was written for: `allcycles.sh` runs the zig and ring arms against truths
already banked, but `zig_arm` refused without a per-sandbox
`ast/<rung>.ir` and a fresh sandbox had none, so every sweep after an
emitter change paid a full rebank first -- roughly 27 minutes of truth arm
to produce inputs the bank could have provided -- before the 11 minutes
that answer the question actually asked.

The f35 chain lost a run to it on 2026-08-23, and the finding-40 fix paid
the full 27 minutes on 2026-08-24 with an unchanged seed and an unchanged
bare-metal arm -- nothing about the rebank was in question, it was there
to make files. It was charged against every emitter change, which is the
change we make most, which is why it sat at the front of this list.

**WRITTEN, NOT RUN (`ed6abff`).** `ast/ensure_ir.sh` is the truth arm's
first half -- bundle, IR-CCE blob, `ring_compile`, `stamp-ir` -- and
`allcycles.sh` calls it for any unit whose `.ir` is missing or refused.
A new file rather than a function in `oracle_lib.sh` on purpose: the
truth sidecars hash that file whole, so adding to it would invalidate
every recorded truth's provenance, which is the item below biting the
first change that would have edited it.

**AND IT IS NOT ENOUGH -- checked 2026-08-24 before running it.** The
`.ir` is only half of what a fresh sandbox is missing. `zig_verdict`
diffs the arm against the WORKING `ast/<rung>.truth` and calls
`truth_prov.py check` on it first; a fresh sandbox has neither the truth
nor its sidecar, so the sweep still cannot start. Measured in sandbox
`20260824T225947Z-ensure-ir-test`: 0 working truths, 0 sidecars, 14
truths sitting in the bank, and `truth_prov.py check lex` answering
`STALE TRUTH for lex: no provenance sidecar (rerun the truth arm)`.

**The provenance decision was taken, and it was the clean one.** The bank
now carries what each truth was measured under: `bank_truth.py` copies
every `.truth.prov` sidecar in beside its truth, so a restored truth is
fully checkable afterwards and `truth/uNN/SEED` is no longer the only
provenance in the bank. The weaker alternative -- restore on seed alone
and label the sweep bank-restored -- was not needed, so the gate that
refuses a truth from another seed is intact rather than loosened.

**RUN, AND THE NUMBER IS SMALLER THAN THE ESTIMATE (2026-08-24).** Sandbox
`20260824T225947Z-ensure-ir-test`, from nothing: **14/14 rungs green in
1499 s** against **2294 s** for the full rebank+sweep of the same 12 units
earlier the same evening (1637 s rebank + 657 s sweep). That is **13
minutes back, not the 27 this item claimed** -- about 35% off, not 71%.

The estimate was wrong because `ensure_ir.sh` skips the cheaper half of
the truth arm, not the dearer one. What it drops is the bare-metal binary
compile and the subject RUN; what it still pays, per unit, is the bundle
and the IR-CCE compile through the ring -- and the ring compile is where
the time is (JUSTIFICATIONS' Nagle entry: 148 s of stream on the
`ir_to_x86` unit alone). Reading the truth arm top to bottom would have
shown that before the run did.

It is still the right change: 35% off the loop we run most, and a fresh
sandbox can now sweep AT ALL, which was the actual goal and is not a
percentage. But the item's own headline number was an estimate presented
as a saving, which is the shape of claim this queue is supposed to catch.

Left:

- ~~**The restore path has not been exercised from empty.**~~ **DONE
  2026-08-25** (`~/runs/20260825T001111Z-restore-from-empty`). The run
  existed to test the WIRING rather than the plug, and the wiring fired:
  from a tree with no artifacts at all, `allcycles.sh` took the restore
  branch ("restored 14 truths and their sidecars into ast/", all 14
  passing `check_rung` against that tree), `ensure_ir.sh` rebuilt all
  twelve `.ir` files, and the sweep came back **14/14 green in 1525 s** --
  within 2% of the 1499 s measured when the truths were already on disk,
  so the integrated path costs what the manual one did. Its honesty
  footers all fired too: census declined to compare, and the summary said
  the truths were bank-restored rather than re-measured.
- **The census still declines to compare** when any IR was rebuilt, which
  is honest and leaves a cheap sweep with no census at all. The
  banked-diagnostics item below is the real answer.

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

**Objective: INTEGRITY, already half done.** `stack_probe.py` -- finding
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
- **`zig-main`'s prose is still wrong, and Update 50 made it wronger.**
  It survived absorption verbatim at `ZigEmitter.codex:3221-3228`. It
  blames the lexer's scan-token/skip-prose-line pair, which measures FLAT
  (100,000 consecutive prose lines in a 256 KB stack; finding 37 measured
  the parser's `scan-top-level` as the real driver). It then says the
  limiting case "is MUTUAL recursion ... and no amount of
  self-tail-call elimination flattens that. Emitting loops for
  self-recursion would be a real feature and would still not remove the
  need for this." Both halves shipped in the same push it now sits in:
  PR 81 emits loops for self-recursion, and PR 82 turned that very scan
  from mutual into SELF recursion so that TCO does flatten it. A
  justification that is wrong is worse than none, since the next reader
  trusts it -- and this one now argues against two changes standing
  beside it in the tree. **OUTBOUND: a small prose-correction PR to the
  zig plug, constant untouched.** It was meant to ride PR 82 and did
  not, which is how a stale justification survives a fix.
- **The replacement prose is WRITTEN and its claims are now CHECKED, and
  it is still UNSENT.** Branch `zig-plug-stack-prose`, tip `87f55675`,
  off `upstream/master`, in a worktree under this session's scratchpad.
  Both mechanism claims were read out of the swept `ast/parse.zig` under
  seed 6CF4A8E0 rather than argued: `scan_class_instance_defs` is a
  `while (true)` with a `continue` at all four recursive sites and the
  name occurs twice in the file, so the loop claim holds as written.
  `parse_top_level` is a loop too, but two arms leave it -- `effect`
  through `parse_top_level_effect`, `claim` through `parse_claim_arm` and
  `parse_simple_claim` -- and each tail-calls `parse_top_level` back,
  which self-tail elimination does not reach. The sentence that said
  every top-level scan tail-calls ITSELF is corrected to name that
  residue and bound it: eight effect declarations and no claims in the
  2.5 MB back-end subject, three and none in the parser. **Sending is
  outward-facing and unauthorised -- ask Steve.** It needs a `Ladder:`
  trailer naming the tag from the ceremony section, and the worktree goes
  when it does.

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

## 12. zigc has a runner now, and one inconclusive result

**Objective: INTEGRITY.** `zigc` -- the whole compiler as a Linux
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

## Not an item: one zig program, for the zig community

Merging the two emitted natives into a single program to hand to the zig
community -- publicity, not engineering, and we keep the separate binaries
because the intermediate IR is what most of our questions are asked about.
Feasibility read and the two-function seam are in
[COMBINED_ZIG.md](COMBINED_ZIG.md). Unscheduled; nothing depends on it.

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

**ALL SIX LANDED 2026-08-25**, absorbed by Update 50's interim push
(github `111c0fea`, main 19116/19117/19125/19131/19133/19140; the
account is `docs/PM/Active/GitHubUpdates/GitHubUpdate50.md`). Every one
was closed upstream with credit and a checkable commit, and the queue
is EMPTY for the first time since it was written. What landed:

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

Ready or nearly so:

- **Finding 41 is RULED and off our plate** (call 21, 2026-08-24). The
  over-application rule binds every plug that keeps an arity map; riscv
  and java get wired in reek's close-out lane. The hedge worked exactly
  as intended -- we reported at source level, named who could verify with
  a toolchain we do not have, and retracted the promise to run java, and
  the ruling arrived anyway. **Keep the general rule: when a finding
  needs a toolchain we do not have, hedge the row and say who can settle
  it. Do not hold the finding back, and do not imply a follow-up.**

- **Finding 36 is NOW THE HEAD OF THE QUEUE** (python plug's TCO keys on
  name, not arity). It was deliberately held to see whether the rule
  bound; call 21 says it does, so 36 no longer has to argue the rule for
  itself and only owes its own reproducer. Still MEDIUM confidence,
  reproducer NOT run -- run it, then a `plugs-backlog.md` row.

- **The one-line corpus fix that would have caught all four.**
  `codex/plugs/test-input/partial.codex` covers over-application of a
  LOCAL, but its only definition is `add3`, which does not return a
  function -- so the branch every one of these plugs gets wrong is
  unreachable from the corpus. `test-plugs.ps1` then never compiles what
  it emitted. PR 80 has landed and its ruling names the wiring but not the
  corpus hole, so this is still unoffered and still the cheapest thing
  in this queue -- and it is the reason the family drifted. Send it with
  finding 36's row.

## Per-Update ceremony

README "Processing a new Update" is the spine: read the release, pin a
branch, tier bare columns, rebank on the droplet, bank over green arms,
`bank_diff.sh`, re-pin POLICY from the census, README timings and table,
tag `uNN-14of14`; then rebase the branches, natives, tiers, census. u49
took one evening end to end (DONE.md 2026-08-22) and the next one should
take less, since the droplet does all of it now.

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
- **Natives and tiers: DONE.** Sandbox
  `20260825T135832Z-u50-natives-tiers`, natives `d7e148e7b699` built from
  the pin, then `./tiers_run.py --zig` green: 15 green, 7 noted. It cost
  one instrument fix first -- see the tier item above.
- **The prose branch's due-diligence run is now the gate on sending it.**
  Steve called it on 2026-08-25: run the verify sweep FIRST. It cuts a
  sandbox on `zig-plug-stack-prose`, sweeps, and diffs every emitted
  `.zig` against the seed-6cf4a8e0 sweep's. He had earlier ruled it
  overkill, and the prose grew a second corrected claim since, which is
  what changed. The launcher lived in a previous session's scratchpad and
  needs rewriting.
