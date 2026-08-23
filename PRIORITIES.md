# What is next, in order

Kept here rather than in anybody's head or memory file. If a memory or an
essay disagrees with this file, this file wins. The README's "Processing a
new Update" is the ceremony's step list; on a conflict about ORDER, that
list is the spine and this file adds items and says where they slot.

This is the queue, not the diary. **Done items leave the list** -- DONE.md
holds one line and a pointer each, measurements go to JUSTIFICATIONS.md,
findings to the register. An item here carries only what is still true and
still to do. (Rewritten 2026-08-23; the previous version had grown its
DONE paragraphs in place and was 700 lines of which perhaps 150 were live.)

Every item opens with an **Objective** naming which of three modes it runs
in, because the same 40-minute run means different things in different
modes, and mistaking one for the other misprices the work:

- **Hunting.** Fishing for defects that are not ours -- the project's
  product. A surprise is the payoff; a clean pass is a mild disappointment.
- **Due diligence.** Verifying our own changes break nothing. Green earns
  no celebration; only a red result is information.
- **Instrument work.** Making the harness honest or cheap. The other two
  modes are only as trustworthy as it is.

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

## 2. Send the heap unification

**Objective: due diligence, then outbound.** Branch
`zig-plug-heap-unification`, 21 commits on the u49 pin, fork tip
`8cb8a0e4`; per-commit Confidence paragraphs; verified by the u49 chain
(tiers green, census 0 differ / 0 crashed, sweep 14/14) through
`1249ad8a`, with `6bf05013` + `8cb8a0e4` riding the guard-and-ir chain. Sends after item
1 lands and re-verifies, based on whatever the current release is then --
absorption is a content question, never a patch-id question. The PR body
names findings 33 and 34 as the reach limits that remain.

## 3. Tail calls become loops (finding 33)

**Objective: instrument work on the emitter; scheduled high by Steve
2026-08-22.** Every `*-loop (xs) (i) (acc)` in the compiler is a self-call
in tail position; bare metal jumps, the plug calls, and Debug zig keeps
every frame -- `zigemit` on the 13 MB fibx IR wants >2 GiB of thread stack
for 3.28M `tokenize_loop` frames. The change: a def whose body's tail
positions are self-calls of the same arity becomes `while (true) {` with
parameter reassignment through temporaries; non-self tail calls stay
calls. Proof: the chain, then zigemit past tokenizing on the stock 512 MB
stack on the fibx subject.

## 4. The refusal-gaps branch, rebased and re-verified

**Objective: hunting reached through our own gap-filling** -- every
family implemented promotes a slab of census programs into the comparing
stage where the depot's oracles can see them. Branch
`zig-plug-refusal-gaps` (fork, 11 commits off the PR-76 tip) has never
been rebased onto u49 nor verified since its cold review. In order:

- Rebase onto the heap branch (item 2's tip). **Drop `1b2f089a`** (the
  `@"..."` quoting): finding 35's `1249ad8a` supersedes it with
  transliteration, which also answers the cold review's "quoting breaks
  when a name is extended after sanitizing".
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

## 5. The tiers stay green, and refusals must be countable

**Objective: instrument work that keeps turning into hunting.** The seven
tiers and the probes exist (DONE.md 2026-08-21); `tiers_run.py` runs them
as a set per Update with `findings/gold/EXPECTED.txt` as the ledger of
admitted disagreements (`ex` noted, `!!` red, `??` stale -- both of the
last two want a human). Standing rules: run after any emitter change; add
a row whenever a finding names a primitive that has none; Codex when the
property is observable from inside a program so bare metal is the oracle,
zig-only otherwise and labelled so; never print an address; keep a control
column.

**The open question:** three findings in one day (`probe-tyvar-leak`,
`probe-show-types`, finding 32's `IrTry`) failed as raw zig errors rather
than a `@compileError("zig plug: ...")` marker. `zig-is-unmapped` and
`corpus_run.py --transpile` read only markers, so these score ZERO in the
ranking that sets priorities however often they bite. The systemic fix --
every unhandled construct refuses by name -- is worth more than any one
of them. Item 4's census is where the count would show.

## 6. Venue plumbing

**Objective: instrument work.** Pushes go through the deploy keys
(`github-ladder`, `github-nr`) since 2026-08-23. Left:

- `allcycles.sh` should REGENERATE a refused or missing `.ir` rather than
  stopping, so a fresh sandbox sweeps without a full rebank first (the
  f35 chain lost a run to this on 2026-08-23; `ring_compile.py` per unit
  plus `stamp-ir` is the whole cost).
- The straw scripts (`droplet_compile/transpile`, the two-venue sweep)
  are NOT retired: they are the keyboard-tempo tools, and both models
  share the box under the compute lock.

## 7. The external review, batches 1 and 3

**Objective: instrument work** -- wrong-bank and wrong-PASS closers.
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

## 8. Provenance watches one file too many

**Objective: instrument work.** The truth sidecars hash `oracle_lib.sh`
whole, so a guard-or-comment edit to the zig-arm half invalidates every
recorded truth's provenance (it cost a full truth-arm re-measurement on
2026-08-20). Segregate by volatility: the truth-arm machinery
(mode_flags, truth_arm, split plumbing) into its own sourced file the
sidecar watches; the zig-arm half free to move. Do it right after a bank
lands, never between recording and banking.

## 9. Execute the rung renames (proposed, not started)

**Objective: instrument work.** `RENAME-PROPOSAL.md` has the mapping and
migration plan (temporary file; the executing commit deletes it). No
re-bank needed -- no rung name appears inside a banked truth -- so 42
files move by `git mv` unchanged. The hazard: `ast/` outputs are
gitignored, and three sites spell old names as literals
(`ast/f3_run.zig:222`, `ast/f4_boot.py:26-29`,
`overnight_verify.sh:99-100`); a missed one reads yesterday's dump and
passes green. Clean the orphans before the first sweep. Waits until the
findings that cite current names stop being re-read.

## 10. Diagnostics as a banked set

**Objective: instrument work.** A pinned count (CDX6020 x43 in
`check_diags.py`) says something changed; a banked set diffed like a
truth file says what, and retires the pins that move whenever the unit
list changes rather than when the source does.

## 11. Parked: the notebook / Prism angle

A bookmark, deliberately last. A Python-hosted notebook showing how Codex
source becomes assembly stage by stage is a weekend-sized demonstrator of
Damian's dusty **Prism** design (`apps/prism/design/Active/PrismDesign.md`);
the native loop and `zigc` already are its machinery in cheap form. If
picked up, re-read the design against what exists and ask Damian what he
would want first. Also parked, the endgame framing (random839): piggyback
the C# DDC witness path with zig -- C# stops at "compiles", zig RUNS.

---

## Outbound queue

- **PR 76** -- absorbed in Update 49 (`bdf0049b`); the eight census reds
  it owed all flipped. Closed.
- **Next: the heap unification** (item 2), after item 1.
- **Then: the refusal gaps** (item 4), rebased onto it.
- PRs 71-75: absorbed, one line each in DONE.md.

## Per-Update ceremony

README "Processing a new Update" is the spine: read the release, pin a
branch, tier bare columns, rebank on the droplet, bank over green arms,
`bank_diff.sh`, re-pin POLICY from the census, README timings and table,
tag `uNN-14of14`; then rebase the branches, natives, tiers, census. u49
took one evening end to end (DONE.md 2026-08-22) and the next one should
take less, since the droplet does all of it now.
