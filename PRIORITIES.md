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

## 1. Launching a detached job is a foot-gun with a live tripwire

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

## 2. A truth's provenance watches the arm that cannot have produced it

**Objective: ERGONOMICS.** A truth is a bare-metal measurement. Its
provenance should depend on exactly what produced it -- the seed, the
subject, the harness that built the subject, the truth arm that ran it --
and on nothing else. The zig arm cannot reach a bare-metal truth, so the
zig arm must not appear in that truth's key. It does, because
`truth_prov.set_hash` hashes `ast/oracle_lib.sh` whole and that one file
holds both arms: `mode_flags` and `truth_arm` beside `zig_verdict`,
`zig_arm` and `ring_arm`, with the shared plumbing (`take_compute_lock`,
`rung_stamp`, `harness_for`, `bounded_run`) between them.

That is the objective. How to reach it is open -- segregating the two
halves into separate sourced files is one answer and was the only one
this item used to name; hashing the truth-arm functions rather than the
file, or recording which functions a run used, are others. The right
answer is whichever makes a truth's key say what the truth depends on.

**Re-read 2026-08-25, and the cost is NARROWER than this item claimed.**
It said a zig-arm edit "invalidates every recorded truth's provenance".
That was true under the older, stricter gate. It is not true now:

- **Sweeps do not care.** `check_rung`, the per-use gate `zig_verdict`
  calls, checks the SEED half of the sidecar ONLY, and says so in its own
  docstring -- an emitter hunt edits harnesses deliberately and a verdict
  against the recorded truth is still the verdict wanted. Harness drift
  is REPORTED, not refused.
- **Banking does.** `bank_truth.py` refuses any truth whose recorded
  content hash no longer matches `set_hash` ("harness content moved since
  it ran"). So the cost lands on one window -- between a rebank and its
  bank -- which is what the old advice, "never between recording and
  banking", was really protecting.
- **The advice itself has gone stale the other way.** It said to do the
  split "right after a bank lands". Since 2026-08-25 the bank CARRIES a
  sidecar per truth, so the moment a bank lands is the moment there are
  fourteen banked sidecars to invalidate. A restore would still work --
  `restore_truths` re-checks with the seed-only gate -- but every restored
  rung would read as drifted from then on, and the next bank taken over
  those truths would refuse. Any execution has to say what happens to the
  banked sidecars, and none of them can just be re-stamped without an
  argument that the move changed no behaviour.

**The live cost is not re-measurement, it is design pressure.**
`ast/ensure_ir.sh` is a separate file rather than a function in
`oracle_lib.sh` for exactly this reason -- adding to `oracle_lib.sh`
would have invalidated every recorded truth. That rationale was written
down in the fresh-sandbox item and left the queue with it, so it is
recorded here now and nowhere else. `oracle_lib.sh` has not changed since
2026-08-23, through two days of heavy emitter work, which reads as
stability and may instead be the avoidance working.

**Verification, whatever the execution:** a pure move changes no
behaviour, and the way to show that is a rebank in a sandbox whose
fourteen truths come back byte-identical to `truth/seed-6cf4a8e0/`. About
40 minutes detached, and it is the same shape as every other inert-change
proof in JUSTIFICATIONS.

## 3. The refusal-gaps branch, rebased and re-verified

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

## 4. Every unhandled construct must refuse BY NAME

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

## 5. The tiers stay green, and each one earns its keep

**Objective: DUE_DILIGENCE that keeps turning into HUNTING.** The tiers
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

## 6. The stack is measured now, and the emitter's prose about it is wrong

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

## 7. Diagnostics as a banked set

**Objective: INTEGRITY.** A pinned count (CDX6020 x43 in
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

## 8. The external review, batches 1 and 3

**Objective: INTEGRITY** -- these are wrong-bank and wrong-PASS closers.
`REVIEW-2026-08-19.md` (Marley, ~34 findings); Batch 2 is done
(2026-08-22, `e91fdb3`). Each batch's first act is re-checking its list against the
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

## 9. Venue plumbing, what is left of it

**Objective: ERGONOMICS.** Pushes go through the deploy keys
(`github-ladder`, `github-nr`) since 2026-08-23. The straw scripts
(`droplet_compile/transpile`, the two-venue sweep) are NOT retired: they
are the keyboard-tempo tools, and both models share the box under the
compute lock. Nothing else here is open: what used to sit in this item
left the queue with the fresh-sandbox work on 2026-08-25.

## 10. zigc has a runner now, and one inconclusive result

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
  **The gate Steve set is satisfied; the send itself is still his call.**
