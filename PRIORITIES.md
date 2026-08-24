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

## 3. Send the tail-call branch (finding 33 is FIXED, not sent)

**Objective: outbound.** The emitter change is done and verified
(`zig-plug-tail-calls`, tip `64d7db8e`, off PR 77's `8cb8a0e4`): `zigemit` clears the 13.2 MB IR at the stock 512 MB stack
in 27 s where 2 GiB used to die, and both ir_to_x86 rungs come out
byte-identical to `truth/u49` through a chain with no QEMU in it.
Finding 33 carries the numbers. What stands between it and a PR:

- ~~`IrAct` is not on the tail spine.~~ **DONE 2026-08-24, `64d7db8e`**
  -- the arm is in all four walks (has-self, arg-invariant,
  occurs-outside, emit-zig-tail), with a block whose last statement
  binds falling back to `zig-tail-return` because it has no executing
  tail position. **The flattening it was written for is still
  UNMEASURED.** The commit itself says so ("whether an act-bodied loop
  now flattens is the smoke's to say"), and the sweep below did not
  answer it: no stack number was taken anywhere in that chain. What is
  established is that the arm breaks nothing, which is the weaker half.
- ~~No ladder sweep has run against the branch.~~ **DONE 2026-08-24:
  SWEEP 14/14 GREEN** (658s) against `64d7db8e`, sandbox
  `20260824T193723Z-tailcall-sweep`. Census unmoved (CDX6020 x43),
  fixed point held, and all 14 bare-metal truths byte-identical to
  `truth/u49` -- the emitter change did not leak into bare metal. The
  bank was taken from that sandbox and is a ZERO-BYTE diff against the
  committed `truth/u49`, which is the claim checked a second way. Note
  what 14/14 is: arm agreement against truths from this same tree, not
  correctness.
- ~~Measure that an act-bodied loop actually flattens.~~ **DONE
  2026-08-24, and the answer changes what the PR should claim.** No new
  compute: `65cb244b` and `64d7db8e` differ in `ZigEmitter.codex` by
  exactly the act arm's 74 insertions and nothing else, and both trees
  already have a full set of emitted subjects on disk, so counting
  emitted `while (true)` tail loops per subject is a one-variable
  differential. **The arm fires: +30 loops across 9 of the 15
  subjects** (lower +6, check/ir_to_x86/parse/passes_to_x86 +4,
  desugar/scope +3, ir_to_wire/lex +1; codexir, ir_to_codex,
  ir_to_codex_roundtrip, lir_to_x86 and zigemit unmoved). The parser
  change cannot be manufacturing this: it sits on the `65cb244b` side,
  and that side gained no loop the act tree lacks in any subject.
- **But all 18 distinct functions it reached are OURS, not the
  compiler's.** `show_defs`, `show_texts`, `show_adefs`,
  `show_bindings`, `show_ir_expr`, `show_irdefs`, `show_diags`,
  `show_type_defs`, `show_ir_def_text`, `print_tokens`, and the
  `fibx_*`/`whole_*` print families -- every one is generated by
  `ast/gen_*_harness.py`, the ladder's own dump harness, which exists
  to turn a rung's output into truth text and never ships anywhere.
  Zero compiler functions are in the list. `print-notices-loop`
  (`opening.codex:1421`) is a real compiler act-loop of exactly this
  shape and appears in NO emitted subject, so the ladder's corpus
  structurally cannot show the upstream benefit even where one exists.
- **So the PR body should argue PARITY, not stack.** The honest claim
  for `64d7db8e` is that the python plug has always descended into an
  act's last statement and ours did not, so the two plugs disagreed
  about what a tail position is; the arm removes the disagreement.
  There is no measured stack saving for upstream on this corpus, and
  the branch should not imply one. This also predicts `stack_probe.py`
  returns a null result here -- finding 37 established the binding
  constraint is the parser's header scan, which is not act-bodied.
- ~~The branch layout is wrong and blocks the send.~~ **DONE
  2026-08-24 AND PUSHED -- both branches are level with origin
  (`zig-plug-tail-calls` at `64d7db8e`, `parser-scan-self-recursive` at
  `50a81942`), so the force-push this bullet was waiting on has
  happened.** `zig-plug-tail-calls` = `6cd40143` + `07495229` +
  `912daac7` (`64d7db8e` landed on top afterwards), one coherent
  invariant-parameter commit squashed from
  `a1398e0b`/`d33fecff`/`65cb244b`; the non-compiling middle cut is
  gone. `parser-scan-self-recursive` = those three plus `50a81942`, the
  parser commit alone -- it does NOT carry `64d7db8e`. The two changes
  are file-disjoint (ZigEmitter against Syntax/Parser), and
  `git diff 65cb244b 50a81942` is EMPTY -- the tree item 3.5's 14/14
  sweep verified, reached by the repaired history. Old tips
  kept at `refs/backup/pre-surgery-tail-calls` and
  `refs/backup/pre-surgery-parser`.
- The PR body wants the `Ladder:` line contrib/README.md asks for.

## 3.5. Verify the parser restructure (finding 37), IN FLIGHT

**Objective: hunting, and the upstream item this queue most wants.**
Both per-definition mutual-tail cycles in `Syntax/Parser.codex` --
scan-top-level/try-scan-type-def/try-scan-def-header and
parse-top-level/try-top-level-type-def/try-top-level-def -- are
restructured so the try-functions RETURN their item and the loop
tail-calls itself, which every TCO in the fleet already flattens.
Committed on `parser-scan-self-recursive` (`50a81942`, was `33f72baa`
before the layout surgery; sandbox `20260824T132742Z-f37-parser`, now
detached at `65cb244b` so the branch ref could move), off the tail-call branch so the arm can
actually see the effect: on the u49 pin the plug has no self-TCO, so the
change would flatten nothing there and the measurement would be a null
result.

**MEASURED: 32 MB -> 4 MB**, and the remaining recursion is no longer
per-definition (finding 37 carries the three-row table). Both ir_to_x86
rungs came out byte-identical to `truth/u49` through the native chain,
so the restructure is semantics-preserving as far as that reaches.
It took the emitter's invariant-parameter rule to see it: with the
parser cycles gone the number had not moved, because `sort_partition`
sat underneath.

Left, in order:

- ~~The full rebank+sweep~~ **DONE 2026-08-24: SWEEP 14/14 GREEN**
  (1716s), census unmoved (CDX6020 x43), fixed point held, and 13 of 14
  truths byte-identical to `truth/u49`. The one mover is `parse`, whose
  own program IS the edited `Parser.codex`: its diff is exactly four
  removed defs, three added, two added type-defs and 50 line shifts,
  with **no existing definition changing params, anns or slug**. Both
  arms agree on the new dump, which is the rung that most directly
  tests the change.
- **Rebase onto the u49 pin** for the outbound branch. It sits on
  `zig-plug-tail-calls` because that is the only arm here that can SEE
  the effect (the pin's plug has no self-TCO), but upstream reproduces
  through arms it already has, so the branch it receives should not
  carry ours.
- **A `compiler-backlog.md` row**, which is how a finding reaches Damian
  at all. **Finding 39's is SENT: PR 79, COMPILER-18**, doc-only, off
  `upstream/master` 5b8091e2, `Ladder:` line naming ladder tag
  `closure-arity`. That PR is the worked example of the route, and it is
  where the numbering now stands. (PR 78 carried COMPILER-18 first, for
  finding 38, and was closed unmerged; the number went with 79.) **Finding 37 still wants its row**,
  and unlike 38 it is not doc-only -- the fix is a change to
  `Syntax/Parser.codex`, so the branch carries the restructure and the
  row together. Draft in `BACKLOG-ROW-37.md`.

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

**Tier 13 (`findings/prim-tailcall.codex`) is GREEN**, five rows
byte-identical on both arms, gold banked under `findings/gold/u49/`. It
earned its keep on its first run: the sixth row broke both arms and
minimizing it produced finding 38, a bare-metal fault. The row is gone
and the hole is documented in the file rather than left as a red.
`arg-swap` and `acc-grows` are the rows that matter -- an implementation
that assigns loop parameters without temporaries fails them with a
plausible number rather than a crash.

**Tier 14 (`findings/prim-closure.codex`) is written, banked on bare
metal, and EXCLUDED from the set.** It pins finding 39: `control-flat`
and `control-pick` answer 47, `under-mutual` answers `not-47`, as
relations rather than values because under-application yields a heap
pointer and a tier must not print an address. Like tier 13 it earned its
keep on the first run -- against both arms it produced **finding 40**,
ours: the zig plug emits `even_fn(4, 20, 22)` against its own
`fn even_fn(n: i64) CxFn2(i64, i64, i64)` whenever it cannot inline the
definition. That refusal is what excludes it, and until the plug is
fixed tier 14 is NOT the detector it exists to be -- what would announce
a fixed COMPILER-18 is the ledger row going STALE when the arms agree,
and there is no ledger row while one arm will not build. Set verified
GREEN with the row excluded (15 green, 6 noted) on natives from
`8cb8a0e4`.

**The open question:** three findings in one day (`probe-tyvar-leak`,
`probe-show-types`, finding 32's `IrTry`) failed as raw zig errors rather
than a `@compileError("zig plug: ...")` marker. `zig-is-unmapped` and
`corpus_run.py --transpile` read only markers, so these score ZERO in the
ranking that sets priorities however often they bite. The systemic fix --
every unhandled construct refuses by name -- is worth more than any one
of them. Item 4's census is where the count would show. **Finding 40 is
the fourth in that class** -- a raw zig `error: expected 1 argument(s)`,
no marker, scoring zero.

## 5.5. The stack is measured now, and the emitter's prose about it is wrong

**Objective: instrument work already half done.** `stack_probe.py` (item
3.5's instrument) bisects the emitted thread stack against real
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
  it in the same branch that carries the parser fix, or upstream beside
  it.

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
- **PR 77** -- the heap unification, sent 2026-08-23 on `8cb8a0e4`
  (21 commits on the u49 pin); verified at ladder tag `pr77-verified`.
  Filed, not landed.
- **Finding 33's fix** -- `zig-plug-tail-calls` pushed to the fork, NOT
  sent. Item 3 says what it wants first.
- **PR 79** -- finding 39, the closure-representation defect, sent
  2026-08-24 as one `compiler-backlog.md` row (COMPILER-18) off
  `upstream/master` 5b8091e2, ladder tag `closure-arity`. Doc-only:
  THEIRS, and we have no fix. Open, not landed. Asks for ONE ruling --
  whether the closure gains a remaining-arity word, or under-application
  is refused where emitted -- and deliberately does not add a pinning
  fixture, because accepting a red arm is Damian's call.
- **PR 78** -- finding 38's framing. CLOSED unmerged 2026-08-24 in favour
  of PR 79, with a comment saying why. Two cold-agent reviews are the
  reason it is not still open and wrong; the second one's seven asks are
  all answered in 79. **The lesson worth keeping: a cold agent reviewing
  an outbound artifact needs the REPO, not just the artifact** -- round
  one was firewalled from the tree and its findings were mostly
  "I cannot verify this", while round two opened every cited line and
  found two false claims.
- **Finding 37's fix** -- `parser-scan-self-recursive`. Item 3.5.
  MEASURED now (32 MB -> 4 MB, sweep 14/14 green); what is left is the
  rebase onto the u49 pin and the row. This is compiler code rather than
  plug code, so it goes as a small branch plus a `compiler-backlog.md`
  row, not as a ladder finding.
- **Finding 36** (python plug's TCO keys on name, not arity) -- filed in
  our register at MEDIUM confidence, reproducer NOT run. It is the
  fleet's lane, so it wants a `plugs-backlog.md` row once run.
- **Finding 41** (riscv and java break the curried-application rule;
  riscv's correct over-apply is in the tree and never called) -- THEIRS,
  filed 2026-08-24. This is the strongest doc-only row in the queue: the
  rule is already written at `DevelopersRulebook.md:256-260`, so the row
  reports non-compliance against upstream's own stated contract rather
  than proposing a design. Wants ONE `plugs-backlog.md` row covering
  both plugs, and it should say plainly that the runtime consequence is
  inferred from the emitted shape, not observed. Findings 36, 40 and 41
  are one rule broken in four places; consider whether the row names the
  rule once and lists the sites, which is likelier to get a ruling than
  four separate reports.
- **Finding 40** (ours, the zig plug's half of that same rule) -- the
  design question is SETTLED and the fix is scoped: `emit-zig-apply`
  needs a third branch for `args > ar`, chunked by each closure's arity
  rather than one at a time, AND `emit-zig-name:1053-1057` must stop
  eta-wrapping on the type-spine count. Both sites or neither. Tier 14
  stays excluded until it lands. **One thing is predicted and not
  measured**: that the `emit-zig-name` wrap actually misfires. Cheapest
  check is transpile-only, no zig compile and no lock -- pass a
  closure-returning definition as a bare value and grep the output for a
  `CxFn3` wrapper containing `even_fn(p0, p1, p2)`.
- **A one-line corpus fix would have caught all four.**
  `codex/plugs/test-input/partial.codex` covers over-application of a
  LOCAL but never of a named top-level definition, and
  `test-plugs.ps1` never compiles what it emitted. Worth offering
  upstream alongside the row -- it is the cheapest thing in this queue
  and it is the reason the family drifted.
- **Standing:** a finding in `findings/README.md` reaches Damian only
  when someone opens a PR carrying it. Nothing notifies anyone.
- **Then: the refusal gaps** (item 4), rebased onto it.
- PRs 71-75: absorbed, one line each in DONE.md.

## Per-Update ceremony

README "Processing a new Update" is the spine: read the release, pin a
branch, tier bare columns, rebank on the droplet, bank over green arms,
`bank_diff.sh`, re-pin POLICY from the census, README timings and table,
tag `uNN-14of14`; then rebase the branches, natives, tiers, census. u49
took one evening end to end (DONE.md 2026-08-22) and the next one should
take less, since the droplet does all of it now.
