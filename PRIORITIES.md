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

- **COMPLETENESS.** Closing a hole in the zig plug. **New and first-class
  as of 2026-08-26**, on Steve's ruling: the plug is close enough now that
  its own state matters, and each hole closed unmasks the next defect.
  Not every hole is owed -- "does not port nicely to zig and does not come
  up in real life" is a legitimate place to stop, said out loud.
- **HUNTING.** Fishing for defects that are not ours. **Turned DOWN
  2026-08-26**, same ruling: still the thing that produces the product,
  but no longer the default activity. Findings arrive faster than we can
  measure, write up and merge them, so draining the pile beats adding to
  it. A surprise is still the payoff.
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

**THE MISSION CHANGED 2026-08-26**, in a note reply on
`where-the-ladder-stands`. Steve: *"our goal should shift to finishing the
zig plug ... we don't need to completely finish it -- some things just
don't port nicely to zig and don't come up in real life -- but we should
keep closing holes."* And: *"This doesn't mean that we abandon the goal of
reporting defects. We still want to send stuff over the wall with the
proper amount of due diligence on our side. Anything that we can verify
with our toolchain should be checked."* Both goals are live; neither
replaces the other. Ordering rule that follows: **a known hole with a
clear fix outranks a new hunt.**

**The baseline rule (Steve, 2026-08-26): every hypothesis we hunt from here
is a CHILD OF THE UPDATE 50 COMMIT.** `upstream/master` is `8cc80685` and
everything done before it has been absorbed, so a branch cut from an older
pin is measuring a tree nobody is going to ship against. Both live branches
already satisfy it -- `zig-plug-tvar-not-an-answer` and `roc-corpus-ports`
are children of `8cc80685` -- and the rule is written down for the next one.

**Housekeeping is part of that.** Sandboxes older than about four hours were
pruned on 2026-08-26 (25 down to 5, 11 GB down to 2.4), along with four
stale PR worktrees left in a dead session's scratchpad holding 1.2 GB and
four branches hostage from checkout. **Every run directory cited in this
file or in the register before 14:00 on 2026-08-26 is GONE** -- the numbers
out of them are recorded here and in JUSTIFICATIONS, which is where they
belong, but the raw logs are not recoverable and a citation to one is a
dead pointer. Two gaps worth knowing: `sandbox.sh --prune` runs
`git worktree prune` on the LADDER only, so the depot's metadata needs the
same command by hand, and nothing prunes worktrees created outside
`~/runs`.

**The venue rule (Steve, 2026-08-22): everything computes on this box.**
Every job below -- natives, tiers, census, sweeps, rebanks -- runs in a
sandbox (`./sandbox.sh <label>`, `. ../env`, detached with a log). Every
compute entry point refuses on a host without `CODEX_LADDER_VENUE`
(`bb39139`), which `~/.codex_ladder_env` exports. One compute job at a
time.

## H2 IS SETTLED. IT IS UPSTREAM, IT IS ROOT-CAUSED, AND IT IS FIXED.

**Objective: OUTBOUND.** Entry point: KEYBOARD, then one BOX run for due
diligence.

The canary (`c6cd236a`) answered on 2026-08-27 at 16:09Z: **the arm FIRES and
the lookup MISSES**, on all five affected lambdas. Its own driver printed that
verdict off a grep of the parameter cells, which was right for the wrong
reason -- only one parameter cell moved, and that one was contamination from a
neighbour. The evidence is the whole wire, not the cell table, and it is
banked in `findings/h2-wire/` with the pin's baseline beside it.

**The root cause, found by reading source from where the canary pointed:**

    Syntax/SyntaxNodes.codex:23   | LambdaExpr (List Token) (Expr)

The lambda is the only expression node in the CST with no span. Its
neighbours all carry one, so `Desugarer.codex:55` has nothing to pass and
writes `synthetic-span`, and `is-synthetic-span` (`file-id == 0`) gates BOTH
`record-expr-type` (`Unifier.codex:147`) and `lookup-expr-type` (`:178`).
Every lambda in the language is filed under file-id 0, which is to say not
filed. That is why the parked patch was byte-identical: it wrote into a
channel that discards and read from one that always misses. **Not a span
mismatch -- no span.**

**The fix: branch `h2-lambda-span` (`bba94d1b`), five sites**, giving the node
its lambda token the way `HandleExpr`/`TryExpr`/`WithTimeoutExpr` carry
theirs. Measured in `~/runs/20260827T161748Z-h2-span`, which still holds its
natives:

    matrix cells reading `error`     6 of 11  ->  0 of 11
    case f  (\s -> s & "!" on a Text)  error  ->  text
    case d  (a lambda literal's fn arg) error  ->  (fn int-default int-default)
    case g  (never applied)             error  ->  (tvar 305)
    controls b and e                    unchanged

Case f is the cell that separates recovery from a lucky `Integer` default, and
it recovered. Case g is the cell that must NOT recover, and it did not -- an
unsolved type variable is what an unconstrained parameter is, and it is more
honest than an `ErrorTy` claiming a type failure in a clean program. The
pre-registration (`1e044bf`, written before the build) called ten of eleven
cells and got case g wrong; the reading was wrong, not the compiler.

**THE PLUG-SIDE RECOVERY IS DELETED. Steve's ruling, 2026-08-27:** *"Let's
nuke all remnants of our attempts to work around this on the plug side. I
think the plug-side strategy is doomed to failure ... I don't want any
fragile half-measures here or unnecessary clutter in our upstream message."*
Branch `zig-plug-h2-recovery` deleted (nine commits, 294 lines in
`ZigEmitter.codex`), its three sandboxes removed, 1.7 GB freed. Nothing
anywhere should grow a zig-side arm for this again. One remnant is knowingly
left alone: `3f0f42e5` still sits in the history of the stale
`zig-plug-tvar-not-an-answer` branch, which is based on pre-u51 upstream and
holds a lot of unrelated landed work -- deleting the branch to reach one
commit would cost more than it saves.

## WHAT THE FIXED WIRE DOES TO THE EMITTER, MEASURED

**The zig plug needs no H2 arm at all.** Run against the `h2-span` natives,
the matrix's emitted signatures are:

    __lam_3(base: i64, step: CxFn1(i64, i64)) i64      the arrow, from the checker
    __lam_6(s: []const u8) []const u8                  case f, Text
    __lam_7(comptime T305: type, k: T305) i64          the tvar, handled generically

`unanswered parameters: none`, `closure-wrapper markers: 0`. Every cell the
deleted recovery walk was built to reconstruct now arrives on the wire, and
`__lam_3`'s `step` -- the one it rebuilt from the callee slot -- arrives as a
whole `CxFn1`.

**The matrix still does not build, for one reason and it is not a type gap.**
Case g's CALL SITE refuses by name: `zig plug: unresolved type variable T305
of __lam_7`. `\k -> 1` is never applied, so there is no instantiation to
monomorphise from. That is finding 55's class -- the same one the other three
Roc ports fail on -- and it belongs to the item below, not to H2.

**`verify_emitter.sh` leg 1b is STRICT now (`0de932f`).** Its allowlist was
built for the deleted walk, and on the run that retired it the leg reported
GREEN through a zig file that does not build. It is RED today, naming case g,
which is the correct reading. It will go green when monomorphisation lands,
not before, and it requires a compiler carrying the lambda-span fix.

## THE CORPUS ARTIFACTS ARE FIXED, AND THE BANK SURVIVED

**Objective: INTEGRITY.** Entry point: KEYBOARD. Done 2026-08-27.

The full-corpus `--run` reported **94 programs as `match -> refused`** against
the lambda-span fix. None of it was real. Two defects, one cause, both fixed:

- **The resume compared against a file anything can overwrite.**
  `load_run_carry` took its shas from `transpile.json`, which a bare
  `--transpile` also writes -- so `--transpile` then `--run`, the sequence
  this tool's own docstring recommends, made prev == now for every program and
  carried the whole journal unconditionally. Every verdict line now carries
  its own key (`zig_sha`, `expected_sha`, zig version) and the resume checks
  the line. A keyless line does not carry. (`7567bf0`)
- **Four artifacts were tracked AND rewritten by every run**, so the
  discipline became revert-them-afterwards -- `overnight_verify.sh` ended with
  a `git checkout --` on the trio, throwing away the answer the run had just
  computed. The tracked copies froze while `census.json` advanced through
  `--bank`. `census.json` is the only tracked corpus artifact now; the rest
  are gitignored stage outputs and the revert step is deleted.
- **A bank diff now names the tree it is about** (`2b60551`), comparing the
  bank's `meta.tools` to the natives actually in `native/`. The resume had
  printed "(emitted zig byte-identical, toolchain unmoved)" in the very run
  where it had verified neither, and that parenthetical is what made the wrong
  answer believable. **Prose in output asserting a property the code did not
  check is the deepest version of this bug.**

**The bank itself was HONEST and is now proven so.** Rebuilt from scratch at
the pin with no journal, all 318 clean programs built and run: byte-identical
to the committed `census.json`, zero rows moved, zero shas differ. `clean 318,
match 268, refused 24` is correct and reproduced without a single carried
verdict.

The rule, now in `corpus/README.md`: **a bank is taken deliberately; a stage
output is regenerated. Never track a file that every run rewrites.**

## THE SEND, AND THE ONE THING OWED BEFORE IT

`outbound/ISSUE-DRAFT-type-info-dropped.md` is rewritten (`b56137e`,
`f7675ef`): the plug-side "what we tried" section is gone entirely, so is the
hedge that said we did not know why our patch was inert, and in their place is
the root cause, the fix, and the table above. The ask is a ruling plus an
offer to send the branch as a PR with a `compiler-backlog.md` row. GitHub,
Steve's account, say it is Claude.

**What is owed: due diligence on a core-compiler change.** A change in the
parser and desugarer touches every backend, and the only measurement so far is
one seven-case matrix's IR wire. Before the send, run the fix's compiler
through the corpus and the 14-rung sweep -- the `h2-span` sandbox already has
the natives, so this is one BOX job, not a rebuild. A regression there is the
one thing that would change the message.

## The Update 51 ceremony is closed

Every step done and harvested, 2026-08-27. `u51-14of14`, seed
`C3181693`, pin `012a9d2e`, `check_paths.py` clean, working tree clean.

- **Rebank 14/14 green** in 2541 s; all fourteen truths byte-identical to
  the bank taken from the killed run, sidecars included.
- **`bank_diff` u50 -> u51**: four rungs moved, ten byte-identical.
- **Census compared** for the first time under this seed; CDX6020 at its
  pinned 43, **no re-pin owed**.
- **Tier SET GREEN, 16 green 6 noted** -- and it CAUGHT ONE.
  `prim-closure/under-mutual` went STALE: finding 39 / COMPILER-18 shipped
  in Update 50, bare metal `not-47` at u49 and `47` from u50 on. Row
  deleted at `5f5b42d`. It survived a whole Update because the u50
  close-out ran `tiers_run.py --zig`, the zig arm alone, which
  structurally cannot see a disagreement that STOPPED.
- **Corpus census re-pinned and HARVESTED** (`07ab991`): clean 318, match
  268, refused 24, against the 317/267/24 reported to PR 92 from an Update
  50 tree. One program of drift across an Update; the PR's headline stands
  and nothing is owed.
- **`codexzig` built from the u51 pin, the first ever, and the FIXED POINT
  HOLDS** -- it re-emitted its own 2,365,512-byte bundle byte-identically.

The sandbox `~/runs/20260827T133749Z-u51-natives` still holds the pin's
natives and codexzig. **It is the only sandbox on the box** and it is
worth keeping until the next item is measured, because that item needs
exactly these natives.

## AFTER THAT: THE OTHER THREE PORTS, WHICH ARE A DIFFERENT CLASS

`iter-map`, `iter-keep-if`, `iter-drop-if` fail on type variables
reaching the plug from polymorphic definitions -- `(fn (tvar 44) (tvar
45))`, `(ctd "Step" (args (tvar 16)))`. That is monomorphisation and it
is ours too, and **nothing written covers it**: `7de07cf0` says so
itself, "Does NOT fix finding 55's other half: a source-level type
variable reaching the same fallback." Bigger piece, own sitting.

## THE `ErrorTy` SENTINEL COLLISION, WHICH THE FIX DOES NOT CLOSE

Still true and still worth saying, and it is in the draft: `ErrorTy` is the
compiler's TYPE FAILURE atom AND `lower-let`'s no-expectation sentinel
(`Lowering.codex:689`). Two different facts wearing one spelling, and the
collision reaches the wire -- a plug reading `(param "x" error)` cannot tell a
failed check from an unwritten answer. The lambda-span fix removes the case
that made this bite, but not the collision.

**The lesson that cost two days:** a claim in `findings/README.md` was read as
evidence rather than verified against code. The false sentence was "No plug
mentions `ErrorTy` -- not the zig emitter, not the C# one", and the disproving
grep had already been run that morning. Then the entry over-corrected to "H2
IS OURS" on the strength of four sibling arms, which measurement has now
overturned in the other direction. The register is orientation, exactly like
MEMORY.md. Code is truth, and a measurement beats both.

## STANDING PROPERTY: DOES THE IR CARRY WHAT THE CHECKER KNEW?

**Objective: INTEGRITY.** Entry point: BOX, but it should RIDE a step that
already has natives rather than add one. **NOT URGENT, AND NOT SCOPED --
Steve, 2026-08-27: "We'll scope it properly when we're ready for it."** This
entry exists so the idea is not re-derived from scratch; it is a placeholder
with its design notes attached, not a work item.

**The idea.** H2 was found because a person noticed a refusal and chased it
for two days. The class it belongs to -- a type the checker solved that the IR
does not carry -- is mechanically detectable, and the tree should detect it
instead of a person. Today it is a finding we re-derive; it should be a
property that goes red on its own.

From `notes/zig-as-the-demanding-customer.md` on the essay surface, which is
where the reasoning lives.

**Why it is worth doing at all.** The project's own gates are structurally
blind to this class: the x86 reference and the C# DDC witness both erase
types by construction, so neither can fail on a dropped one. Anything that
catches it has to be built on the arm that cannot erase, which is ours. That
also means nobody upstream is likely to build it.

**What exists already, and it is most of the parts.**

- `findings/probe-h2-lambda-types.codex` -- seven cases, two one-respect
  control pairs, `.expected` banked from bare metal. Case f is a `Text` so a
  defaulting plug fails visibly; case g is unconstrained so no concrete type
  is the honest answer there.
- `h2_wire.py` -- prints the `(param ...)` cells straight off the IR wire, no
  zig generated and no emitter opinion in the reading.
- `verify_emitter.sh` leg 1b -- strict since `0de932f`; already runs the
  matrix end to end against the bare-metal `.expected`.

**The hard part, and it is the whole design question.** The property is NOT
"no `error` on the wire". Case g proves that: `\k -> 1` is never applied, so
nothing constrains its parameter, and an unsolved type variable is the honest
answer. The discriminator that matters is:

    did the checker COMPUTE an answer that the IR failed to carry?   -> upstream
    does the checker have no answer because the program does not
      constrain one?                                                 -> ours,
                                                                        and it
                                                                        is
                                                                        monomorphisation

A first cut could compare, per lifted lambda, what `infer-lambda` computed
against what reached the wire. That needs the checker's answer to be readable
from outside, which the lambda-span fix has now made true for lambdas and is
not true in general.

**What would make it standing rather than occasional.** Run it every ceremony,
on the arm that can see it, with a bare-metal oracle underneath -- the shape
the tier set already has. **Do not build a second mechanism if a tier can
carry it**; a tier row is the existing home for "this disagreement is known
and here is why", and the tier set already caught a stale row this Update.

**Scope it when the outbound queue is empty**, not before. The send, the
`ErrorTy` sentinel collision and monomorphisation are all ahead of it.

## THE PR 92 EMITTER REPAIR LANDED -- `012a9d2e`, and it is OUR CODE VERBATIM

The report went to Damian at ~02:00; `012a9d2e` was pushed the same
night. Measured, not inferred:

- `git diff u51-emitter:codex/plugs/zig/ZigEmitter.codex
  012a9d2e:codex/plugs/zig/ZigEmitter.codex` is **EMPTY**. The depot's
  emitter is byte-identical to our branch's. `plugs-backlog.md` too. The
  whole tree diff between our 19-commit branch and the depot tip is
  **five doc files**.
- All four names are in the code now (`zig-lit-pat-text`,
  `zig-stray-tvar`, `zig-first-stray-tvar`, `zig-tvar-scope-refusal`),
  and `zig-bool-lit-text` is **gone** -- Damian made the same call our
  rebase did, for the same published reason. **The removal Steve had not
  reviewed is moot: it is upstream's own.**
- Both halves of the report were taken. `GitHubUpdate51.md` carries a
  CORRECTION paragraph naming the cause (`p4 copy` loses INTEGRATES to
  the noclobber refusal) and the second half -- that the 19961
  re-measure was x86-only and could not observe the emitter. The zig arm
  was graded this time before the claim was written: 4 of 12 pairs run
  and match, 8 refuse with the designed clean markers.
- `PerforceProcess.md`'s P-CLOBBER row gained a **copy-up variant** with
  our incident in it, and a new standing rule: after every copy-up,
  account the submitted CL's file list against the source CL's in both
  directions before writing any claim on it.

**Consequences for us.** The outbound queue for the zig plug is EMPTY
again -- `u51-emitter` is fully absorbed and the branch is now a
historical marker, not a stack. Ceremony step 4 answers itself for the
first time: **sweep the release's emitter verbatim** and sweeping our
own fixes are THE SAME RUN. `012a9d2e` is not a release (no seed move,
no release note of its own), so the bank stays `u51` and
`seed_identity.py` agrees.

**Ceremony step 1 read clean.** No seed move, nothing under
`codex/compiler/Emit/`, `tools/codex-vm.c` or `build/vm-config.ps1`, so
neither `codex_vm.py`'s RAM/`SIZE:` contract nor `ring_compile.py`'s ring
constants can have moved. Step 2 is vacuous for the same reason -- the
seed is the one already probed at 00:47. Nothing in the Update closes a
finding of ours, so no workaround is orphaned.

**The u51 gold was STRANDED and is recovered (`15ebb21`).** `tiers_run.py
--bare` banked 21 columns SET GREEN inside the killed rebank's sandbox on
2026-08-27, and only the truths were ever harvested out of it; this file
has claimed `findings/gold/u51/` existed ever since and the directory was
not in the checkout. Gold is keyed to the seed, which has not moved.

**When the rebank lands, in order:**

1. `bank_truth.py` -- only if the arms are green, and diff first: the
   truths should be identical to what is already banked.
2. `bank_diff.sh` -- what moved from u50.
3. **Re-pin `check_diags.py`'s POLICY table** from the run's `--census`
   block. This is the debt the whole rebank exists to pay.
4. **Correct the README's banked-against table to u51** and re-measure
   the timings in "Running it" in the same commit. `check_paths.py`
   prints a WARN naming this exact debt.
5. Tag `u51-14of14`, push.
6. `native_build.sh` from this pin, then `./tiers_run.py` as a SET --
   natives are per-emitter and ours are still `d7e148e7b699` from the
   u50 pin. Expect rows to go STALE: the tier ledger admits divergences
   the repaired emitter now fixes.

## What to pick up next

**Post-repair queue, re-sorted 2026-08-27 12:2x. In order.**

**The first two items of the 08-26 23:3x queue were already DONE when it
was written down, and it stood stale for thirteen hours.** Both are
recorded here rather than deleted, because the queue claiming owed work
that was already sent is the kind of error that gets an apology written
twice:

- ~~FINDING 49, the IR harness reads no diagnostic bag~~ -- **CLOSED**.
  Fixed (`7a6071d`), measured (`2286fcf`), swept 14/14, and the
  corrected headline went to PR 92 at 00:06Z. Item 1z has the account.
- ~~Send the finding-56 withdrawal~~ -- **SENT ~00:0xZ and ACCEPTED the
  same night** (`f9a66db`). *"A deaf instrument is the best possible
  ending for this thread: three wrong attributions, zero wrong
  compilers, and every kill was a measurement."* Their four-seed sweep
  is a standing reference arm now. Nothing owed.

**The outbound queue is EMPTY.** PR 92 is CLOSED, its emitter is
upstream, and its last comment (07:25Z) carries no ask. Verified against
GitHub, not against our own files -- which is the check that would have
caught the two stale items above.

1. **Units part B / finding 55** (item 1f) -- one `else` in
   `emit-zig-atype`. `7de07cf0` is WRITTEN and unbuilt; it declares the
   unit family instead of resolving the name. 11 programs, and the same
   `else` also emits a type variable verbatim, which it does NOT fix.
2. **The prelude shadowing class** (finding 54) -- 66 names, both
   candidate fixes costed in row 1.90 and neither taken. Wants its own
   sitting plus a check that re-derives the surface AND counts
   parameters.
3. **H2 -- DONE.** Settled by measurement 2026-08-27 and fixed on
   `h2-lambda-span`; see the top of this file. What is left is the send
   and the due-diligence run before it, not a decision.
4. The rest of the reading pass (item 1e): 24 corpus refusals left, of
   which 11 are item 2 above and 5 are a concurrency cluster nobody has
   read.

5. ~~**Verify the Roc ports' `.expected` against BARE METAL**~~ -- **DONE
   2026-08-27 BY DAMIAN'S LANE, 12 of 12 match** against the shipped seed
   `C3181693`. They are now depot tests and gate with everything else. So
   the adaptations were sound and Roc's values agree with Codex bare
   metal on all twelve; the two-way-oracle question does not arise for
   this batch. Nothing owed.

   **And OUR arm independently agrees on the split, which nobody has
   written down.** His grading of the repaired emitter -- "4 of 12 pairs
   run and match, 8 refuse with the designed clean markers" -- is
   `f49-gate2`'s leg 4 exactly: `roc_ports_run.py` says `3 match, 8 not`
   over the eleven Roc ports (`roc-early-return-predicate`,
   `roc-recursive-var`, `roc-returned-closure`), and the twelfth pair is
   `tvar-in-declared-type`, which the corpus leg scored `match`. Same
   twelve pairs, same four matches, same eight refusals, two gradings
   built by people who did not compare notes. **Leg 4's `RED` is a
   labelling artifact**: `roc_ports_run.py` scores a designed clean
   marker as `not`, so the leg reports red on a result that is the
   expected one. Worth fixing before it is read as a regression.
   (Superseded item text below for the
   reasoning, which still applies to any FUTURE port.)

6. **Verify FUTURE Roc ports' `.expected` against BARE METAL** -- owed,
   and we have not done it. Their values come from Roc, adapted, and
   every run we made compared them against OUR ARM (`codexzig`,
   `corpus_run.py`), never against the seed. Damian's review says it
   will "re-measure the twelve new corpus `.expected` files on bare
   metal before they are trusted as cross-backend truth", which is the
   right check and is the same discipline we got wrong on finding 56 --
   applied to our test DATA rather than our instrument.

   **The ports are a TWO-WAY oracle, and tomorrow's run should not jump
   to the fun conclusion.** Roc's expected values are battle-tested
   across several Roc backends -- but that is INTERNAL consistency, the
   same thing a self-hosting fixed point buys and the same thing it
   cannot detect. If Roc computes a value wrongly and consistently, all
   their backends agree and nobody sees it. Codex bare metal is very
   likely the first outside witness those snippets have had.

   So discriminate before claiming: if **bare metal and our zig arm
   agree with each other** and both disagree with Roc's `.expected`,
   there are still two readings -- our PORT does not faithfully express
   the same computation (ours to fix, and the likelier one), or Roc is
   wrong (theirs, and worth reporting to them). Settle it by re-reading
   the port against the original snippet BEFORE writing to anyone.
   Nothing in the current 3-match/8-fail split is evidence either way:
   the eight fail to BUILD, so no disagreement about a VALUE has been
   observed yet.

   Three outcomes: bare metal agrees and the ports are sound; bare metal
   disagrees and our `.expected` is a bad adaptation, which is ours to
   fix and should be volunteered rather than waited for; or bare metal
   disagrees with our zig arm, which is a finding. **We should run this
   ourselves rather than learn it from their review.** 11 seed compiles,
   one compute job at a time.

**Instruments built 2026-08-26** and worth knowing before you reach for a
command: `verify_emitter.sh` (the six-leg chain), `run_pr87_probes.sh`,
**`run_seed_probe.sh` (bare metal -- read its header before asking any
compiler question)**, and `sandbox.sh <label> [ladder-ref] [codex-repo]
[codex-ref]`, whose fourth argument is how a chain excludes a commit.

## Where things stand, 2026-08-26 evening

**Depth-first is the rule now (Steve, 2026-08-26): the moment a port
unleashes a finding, that finding goes to the top of this list.** That is
why finding 47 is item 1 and the Roc porting it came out of is item 3.

Three efforts are live at once. They are ordered here, and the ordering is
the whole point of writing them down:

    1  finding 47        guard written, NOTHING BUILT             -> item 1
    1a finding 50        show has 5 cases, plug has 1; 42 programs -> item 1a
    1b finding 49        our corpus gate is blind, fix is known    -> item 1b
    2  finding 46's PR   fix done and verified, not sent          -> item 2
    3  the Roc ports     11 ported, run: 2 match 9 refuse        -> item 3

**THE REBANK STALLED ONCE, RESUMED, AND IS SWEEPING.**
`~/runs/20260826T171739Z-u50-rebank-tvar`, on `zig-plug-tvar-not-an-answer`
as decided. `rebank_all.sh` died at 11/12 on `passes_to_x86` -- the largest
unit, 2.65 MB -- with `guest stopped consuming at rpos 2097152 of 2652454`
on the IR-CCE compile, the CDX compile of the same source having just
succeeded.

**It was transport, not the release, and the register carries the reasoning
as H1 (FALSIFIED).** The retry of that one unit completed: 14,029,026 bytes
of IR in 219 s. A stall that does not reproduce cannot be explained by a
tree. Filed as a hypothesis rather than a finding precisely because the fact
that did not fit -- the guest stops READING, before a lift would run -- was
visible from the start.

**A number that fell out of it and is worth keeping:** the IR is +145,569
bytes over the interim's 13,883,457, about **1%**, which is Update 50's lift
adding definitions to the largest unit. It compiles fine. The lift's cost on
this path is measured now and it is small.

**Now sweeping.** All twelve truths are recorded, so `ast/allcycles.sh` was
run directly rather than re-recording eleven good units to reach
`rebank_all`'s second half. **`truth/u50` is still NOT banked** --
`bank_truth.py` is the step after a green sweep, and until it runs the sweep,
`allcycles` in a fresh sandbox, and the roundtrip harness generator all stay
blocked. They remain the same missing bank.


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

## 1z. FINDING 49 -- CLOSED. Fixed, measured, swept 14/14, reported to PR 92

**Objective: INTEGRITY. Fix written and committed `7a6071d`; chain
`f49-gate2` running on codex `cab52a35` so the gate is the ONLY delta.
What is left is to READ THE RESULT and act on it.** Raised 2026-08-26 23:5x after it produced a false report to
Damian's lane and cost them a triage round.

`ast/CodexIrHarness.codex` calls `check-chapter`, binds `cr.state`, and
contains the word `bag` **zero times**. Its sibling
`ast/CodexZigHarness.codex` merges four bags and halts. So
`native/codexir` emits IR for a program with compiler errors and says
nothing.

**Measured 2026-08-26 on one tree, same source unit, three arms:**

    program              seed (bare metal)   native/codexir   native/codexzig
    probe-pr87-alias     CDX2001 Int vs Fun  rc=0, NONE       CDX2001 Int vs Fun
    probe-pr87-direct    CDX2001 Int vs Fun  rc=0, NONE       CDX2001 Int vs Fun
    probe-cdx2001-text   CDX2001 Int vs Text rc=0, NONE       CDX2001 Int vs Text

**What it has already cost.** A three-line program was reported to
Damian's lane as a type-checker soundness hole in Codex. It was not. Then
it was reported as our plug miscompiling their checker. It was not that
either -- `codexzig` is the same plug's output and gets it right. Their
compiler lane ran a four-seed refusal sweep with a positive control to
tell us so.

**What it is still costing, silently.** `corpus_run.py` runs
`native/codexir`. A corpus program carrying a compiler error emits IR
anyway, and we then build its zig, run it, and record a verdict. **We do
not know how many of the 326 "clean" programs have compiler errors**,
because the instrument that would say so is the one that cannot.
`codexzig`'s gate found 41 of 593 when it was turned on; `codexir` has no
such gate and has never been asked.

**The fix** is the gate its sibling already has: merge
`toks.errors`, `doc.parse-bag`, `rr.bag` and `cr.state.bag`, and halt
with `CODEGEN-HALTED` rather than emitting. `CodexZigHarness.codex:5-17`
is the model and its prose explains the driver's behaviour it stands in
for. **Do not copy the list -- reuse the shape**, which is the lesson
that keeps arriving in this tree.

**Then re-run the corpus and expect the clean count to FALL.** That is
the point, not a regression: programs whose verdicts we have been
recording without the right to.

## 0. SHIPPED 2026-08-26 as PR 92 -- do not re-do

**https://github.com/damiant3/Cobblestone/pull/92**, branch
`zig-plug-u50-emitter-batch` off `8cc80685`, ladder tag
`u50-emitter-batch`. 24 commits, rows 1.85-1.90.

    corpus match    183 -> 269
    corpus refused  112 ->  24
    sweep           14/14 on all four chains

Closed by it: finding 47 (tvar scope guard), 50 (`show`'s five type
cases), 51 (a refusal strands its parameters), 52 (Boolean literal
patterns), 53 (the thread entry), 17 part A (units are their backing
type). Rows 1.89 and 1.90 report 17(B)/55 and 54 as OPEN.

**Their reply comes to the PR on GitHub, not email** (Steve asked for
that) -- `gh pr view 92 --repo damiant3/Cobblestone --comments`.

## 1f. Unit families are 53% of everything left, and half the fix is ONE ARM

**PREDICTIONS for the units+shadowing chain, written before it runs
(codex `cab52a35`. It excluded the H2 recovery rule, which no longer
exists -- H2 is fixed in the compiler and the plug-side walk is deleted --
so the exclusion is now vacuous and the base is just `cab52a35`).**

1. `unit-family`, `unit-smoke`, `units-foreword`, `implicit-convert`
   move `refused -> match`. `unit-family` prints `2400 / 240 / 2 / 100`.
2. The 11 `undeclared Frequency/Timestamp/Duration` do NOT move. Part B
   is untouched, and if they move something is not understood.
3. `dns-answer-count` and `tcp-checksum-refuse` move `refused -> match`
   (finding 54's two instances).
4. Corpus refused 30 -> about 24.
5. **The risk is regression, not failure.** `emit-zig-type`'s `UnitTy`
   arm is consulted everywhere, so every program carrying a unit type
   changes its emitted zig -- including programs that MATCH today and
   were matching while their unit values were `void`. A currently-green
   program going red is the outcome to watch for, and it would be this
   change, not the prelude rename, which cannot reach a program that
   does not define a top-level `l` or `base`.
6. Sweep stays 14/14. This is the leg that would catch a unit value
   whose printed answer moved.

**RESULT, chain `f17-f54` on codex `cab52a35`, 2026-08-26 22:32.**
Corpus `match 263 -> 269`, `refused 30 -> 24`. Six moved, every one
`refused -> match`, and **nothing that matched stopped matching** --
prediction 5, the one that mattered, held:

    implicit-convert  media-codec-test  unit-family
    unit-family-mixed  unit-smoke  units-foreword

Two of those (`unit-family-mixed`, `media-codec-test`) were not named in
the prediction, so part A reached further than the four clean fixtures.
The 11 `undeclared Frequency/Timestamp/Duration` did not move, as
predicted -- **part B is still open and is now item 1f(B) + finding 55.**

**Prediction 3 FAILED: finding 54's two programs did NOT move**, and the
failure is worth more than the six that passed. See finding 54 -- the
surface is 66 names, not 45, because the first extraction never looked
at prelude function PARAMETERS.

**Objective: COMPLETENESS. KEYBOARD to write, BOX to verify.** Raised to
the top 2026-08-26 on Steve's call: these have been standing in front of
more interesting defects, and the corpus agrees -- after the f52/f53
build they are **16 of the 30 remaining refusals**.

**It is two fixes, and only the first is easy.**

**(A) `emit-zig-type` maps `UnitTy` to `"void"`** (`ZigEmitter.codex:296`)
and should recurse into the backing type. **One arm.** Buys the 5 clean
programs (`unit-family`, `unit-smoke`, `units-foreword`,
`implicit-convert`, and the second `void`/`void`).

The evidence that it is only this: `unit-family`'s emitted body is
already arithmetically CORRECT end to end --

    const w = Centimeter(20);                        // 20 *% 10   = 200
    const h = Meter(1);                              // 1 *% 1000  = 1000
    const p = ((w +% h) *% 2);                       // 2400
    cx_print_line(cx_show_int(p));                   // 2400
    cx_print_line(cx_show_int(@divTrunc(p, 10)));    // 240
    cx_print_line(cx_show_int(@divTrunc(p, 1000)));  // 2
    cx_print_line(cx_show_int((50 *% 2)));           // 100

and its `.expected` is `2400 / 240 / 2 / 100`. Scale factors multiply,
conversions inlined to `@divTrunc`, `double-length (Millimeter 50)`
constant-folded. The only wrong thing in the program is the return type:

    fn Centimeter(__fv: i64) void {   <- void, should be i64
        return b0: { const __unit_0 = (__fv *% 10); break :b0 __unit_0; };
    }

That `void` is what makes `w` and `h` void, which is what makes
`(w +% h)` an `invalid operands: 'void' and 'void'`.

**(B) Record FIELDS never reach `emit-zig-type`.** They arrive as
`ATypeExpr` and take `emit-zig-atype`, whose `ANamedType` arm emits any
unrecognized name verbatim (`ZigEmitter.codex:445-447`). **The path HAS
now been read, and it is finding 55**: the same `else` also emits a
source-level TYPE VARIABLE verbatim, which is `queue-test`'s
`cx_ll_empty(a)`. So part B buys **12 programs, not 11**, and the fix is
one `else` -- resolve the name against the unit-defs and the enclosing
definition's type parameters, and refuse with a marker when neither
answers.

Note that this path takes **no scope and has no refusal**, so every
type-variable guard built on 2026-08-26 walks straight past it.

**Fixtures: (A) needs none.** `codex/test/unit-family.codex` is 30 lines,
one unit family, four expected values, nothing else going on -- a unit
test that happens to live in the corpus. So are `unit-smoke` and
`units-foreword`.

**(B) does want one.** Its 11 programs are `av-codec-test`,
`edge-mesh-route`, `ota-update`, `sound-test`, `synth-test` and friends --
big, messy, plenty else wrong with them. A new fixture is about ten
lines: one chapter, one unit family, one record with a field of that
type.

## 1c. `show` on a Real needs `__real_to_text`, and this plug has no such thing

**Objective: a FIX. KEYBOARD to write (a `cx_real_to_text` in the zig
prelude), BOX to verify.**

Split out of item 1a because the two halves cost wildly different things and
buy wildly different amounts. Of finding 50's 42 refusals, **40 are `found
'bool'` and 2 are `found 'f64'`** -- the Boolean half is 40 of them and is
done; this is the other 2.

Bare metal's `__real_to_text` is hand-written assembly
(`Emit/X86_64TextHelpers.codex:590`): sign bit, `cvttsd2si` for the integer
part, fifteen fractional-digit iterations, CCE digit offsets. `std.fmt` will
not agree with it on every value, and a `show` that is right for 2.5 and
wrong for 0.1 is worse than one that refuses. So the plug refuses with a
named marker for now, which also puts the gap in the histogram where it can
be ranked.

## 1e. The corpus reading pass -- DONE once, and it is the COMPLETENESS work list

**Objective: COMPLETENESS. KEYBOARD, no compute.** Added on Steve's note
reply: *"I agree. Add the reading pass to priorities."*

**Done 2026-08-26 21:0x** against the `f47-guard2` `corpus/run.jsonl`,
which had been on disk for hours. All 112 refusals classified by cause:

     41  expected type 'i64', found 'bool'          finding 50   FIXED
     40  startFn return type (thread entry)         finding 53   NEW, open
     12  undeclared Frequency/Timestamp/Duration    finding 17   unit families
      3  expected type 'void', found 'comptime_int'  unclassified
      2  expected type 'i64', found 'f64'           item 1c      refuses, named
      2  undeclared identifier 'True'               finding 52   NEW, FIXED
      1  IList(i64) depends on itself               finding 48   open
     11  singletons: shadowing, switch exhaustiveness, arity, sin, ...

**Three causes were 93 of 112.** Two findings came straight out of it
(52 and 53), one of which was the second-largest class in the corpus and
had never been filed -- its only trace in the register was an aside
inside finding 42.

**RE-CLASSIFIED 2026-08-26 21:2x against the f50/f51 `run.jsonl`.** The
pile is 70 (69 refused + 1 crashed), and it is more concentrated than
before, not less:

     40  startFn return type (thread entry)      finding 53   FIXED
     11  undeclared Frequency/Timestamp/Duration finding 17   item 1f (B)
      3  expected type 'void', found comptime_int finding 17   item 1f (A)
      2  undeclared identifier 'True'            finding 52   FIXED
      2  expected 1 argument(s), found 0                      unclassified
      2  invalid operands: 'void' and 'void'     finding 17   item 1f (A)
     10  singletons (shadowing, switch exhaustiveness, sin, CxFn1, ...)

**AFTER the f52/f53 build the pile is 30**, and it is mostly one thing:

     16  unit families (three messages, one gap)  finding 17   item 1f
      2  invalid operands: 'struct' and 'struct'              NEW, unmasked
      1  IList depends on itself                 finding 48
     11  singletons and small classes

The 2 `'struct' and 'struct'` are `fork-nested` and `par-map`, and both
were `startFn` refusals before -- **newly visible, not a regression.**

The `found 'bool'` class (41) is GONE and the `found 'f64'` class (2) has
become named markers -- both fixes in that build confirmed from a second
angle. **The two staged fixes target 42 of the 70**, and `startFn` alone
is now 57% of the pile, up from 36%: the same defect with a bigger share,
because everything around it moved.

**What is left:**
- Re-classify the 69 and update this table.
- The 3 `void`/`comptime_int` and the 11 singletons are unclassified. That
  is the next reading, and it is where the remaining unknown defects are.
- `tcp-reliability` moved `refused -> crashed` in the f50/f51 run: it now
  builds and panics `index out of bounds: index 0, len 0`. A crash is a
  different class from a refusal and it is unexamined.

**The lesson worth keeping:** the evidence for finding 52 and finding 53
had been in our own corpus output for as long as we have been running it.
Nobody had read it. A summary is where a 40-program class goes to hide.

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

**The oracle question, and Steve's 2026-08-26 ruling on it.** This item used
to say a port earns its `.expected` only once bare metal and the zig arm
have been read against each other. **That is SUPERSEDED.** The gate is
codexzig's output against ROC'S HARNESS'S EXPECTED VALUE -- Roc's answer is
the oracle, because it was written by people with no knowledge of this
compiler, and that independence is the whole reason for borrowing somebody
else's suite instead of writing more rows of our own.

Bare metal is still worth reading and `warmups/regen.sh` still produces it
in about two minutes, but it is EVIDENCE and not the gate. The distinction
earned its keep immediately: `roc-iter-map` never reached a bare-metal
comparison, because Roc's expected value and a refusal from codexzig were
already a complete finding.

### The first port is in, and three arms agree on it

**`roc-returned-closure`** (2026-08-26), from the case Roc names "inspect:
returned closure calls captured function argument" -- four lines:

    wrap : (I64 -> I64) -> { next : () -> I64 }
    wrap = |transform| { next: || transform(1.I64) }
    wrapped = wrap(|_| 9.I64)
    (wrapped.next)()                                    -- Roc expects 9

**Why this one first.** It captures a function-typed PARAMETER in a closure
that leaves as a record field and is entered after `wrap` has returned. No
row in the depot's 1371 programs asks that: `record-smoke.codex` puts a
lambda in a record field but captures a Text and an Integer;
`dce-reach.codex` passes a function as a value but calls it in the frame
that received it.

**One environment adaptation, and the file's prose names it** so a reader
does not take the port for a loose one. Roc's `next` is a THUNK, `() ->
I64`, and Codex has no nullary function type -- a nullary definition is a
constant, evaluated once, not a closure to enter -- so `next` takes an
Integer and ignores it. Everything the case asks survives that.

**The oracle question above is ANSWERED for this row, which is why it has an
`.expected`.** Three arms, independently:

    Roc's own expected output                              9
    Codex bare metal (seed under QEMU, warmups/regen.sh)   9
    Codex -> zig plug -> zig 0.16.0                        9

**And it is a lambda-lifting subject, so it was worth reading both ways.**

    pre-lift  natives   ir 2047 bytes   0 __lam   ->  9
    post-lift natives   ir 2373 bytes   4 __lam   ->  9

Pre-lift the plug does the closure conversion itself -- an `_Env1 { c0:
CxFn1(i64,i64) }` boxed with `cx_new`, entered through `.call(.ctx, 1)`.
Post-lift the lambda is a TWO-parameter top-level def applied to ONE
argument, so the record field holds a **partial application** -- finding
39's exact shape, reached by a closure that outlives its frame. Different
code path, same answer.

**Filing is SETTLED (Steve, 2026-08-26): a proper git branch off the latest
and greatest, and no thought given to upstreaming until a critical mass of
snippets is ported.** That is `roc-corpus-ports` in the depot, cut off
`a961dcb6` -- which means it carries the finding-46 emitter fix underneath
and must be rebased onto the pin before anything goes out. The `warmups/`
copy is DELETED; the depot branch is the single home.

**The gate per port is one thing, and it is Steve's wording: the port is
codexzig-executed and returns the same result as ROC'S HARNESS'S EXPECTED
VALUE.** Not bare metal, not our own comparison. `./roc_ports_run.py` is
that gate -- cite-resolve, `native/codexzig`, `zig run`, diff against
`<name>.expected` -- over every `roc-*.codex` in the depot's test directory.
It is a glob and not a manifest, because a list beside the files is a second
thing to keep in step.

**Two ported, and the second one found something.**

    match      roc-returned-closure    Roc 9,  bare metal 9,  codexzig 9
    refused    roc-iter-map            Roc 24, codexzig REFUSES -> finding 47

**Depth-first from here (Steve, 2026-08-26): when a port unleashes a
finding, the finding goes to the top of the queue and this item waits.** So
finding 47 is item 1 and this resumes after it.

### ELEVEN PORTS NOW, AND THE FIRST RUN OF THE SET

Six landed 2026-08-26 (codex `4ea012e0`): the four inline-fold lambdas,
`roc-recursive-var`, `roc-early-return-predicate` and `roc-iter-drop-if`.
`roc_ports_run.py` over all eleven, natives of 16:44:

    match     roc-recursive-var, roc-returned-closure
    refused   4 folds + closure-captures-list          ErrorTy -- H2
    refused   iter-map, iter-keep-if, iter-drop-if     undeclared T16 -- item 1
    refused   early-return-predicate                   show on a Boolean -- finding 50

**Two of eleven match and that is not a disappointment, it is the yield.**
Nine refusals across three distinct classes, one of which (finding 50) was
not on this list at all and is 37% of the corpus refusal pile. The suite is
doing exactly what item 3 says it is for.

The four folds refuse identically, which is why running all four was worth
it: they widened H2 off the let-bound case it was raised on -- an
immediately-applied lambda literal reaches the plug with `ErrorTy` for its
parameters too.

**NOT PORTED, recorded so nobody re-derives it:** "simple early return from
function via bool". `f = |x| if x { return True } else { False }` is
`if x then True else False` in Codex and there is nothing of the case left.

**Eight or so left in the closure/recursion cluster**, and they are the ones
worth doing: the
four inline-fold lambdas, "recursive function with var keeps outer binding",
the two early-return-via-predicate cases, and the closure-captures-list
pair. The rest of the file's ~118 cases are list, record and tag inspection,
which our corpus already covers heavily.

**Adaptations recorded so far**, in each port's own prose: Codex has no
nullary function type, so Roc's `() -> a` thunks take an ignored Integer;
Codex has no anonymous record, so `One({item, rest})` carries its two as
constructor fields; `end` is a reserved word and cannot be a parameter name.
**Roc's numeric literals default to a decimal type** and its expectations
read `10.0` where a Codex Integer prints `10` -- every fold case in that file
is affected, and the adaptation must be named in the port rather than
silently absorbed into the `.expected`.

## 4. Wire codexzig into the Update ceremony, after the canaries

**Objective: ERGONOMICS in service of INTEGRITY. KEYBOARD to wire, BOX to
prove.** Steve's call, 2026-08-25: on an Update, run the canaries and then go
straight to codexzig.

**Where it goes.** README "Processing a new Update" is the spine: (1) read
the release, (2) probe the contract cheaply, (3) prerequisites for the
rebank, (4) decide what the zig arms measure, (5) run, bank, retire. Step 2
is the canary -- the five-second seed probes that confirm the new seed boots
under our QEMU flags. **codexzig goes between 2 and 3**, before the rebank
costs an hour.

**What the gate is.** `./codexzig_build.sh` from the new pin, about ten
minutes of box time, and it ends by re-emitting its own bundle and comparing
byte for byte -- so the build IS the fixed-point check. Then
`./codexzig_corpus.py`, about five minutes. Together that is roughly a
quarter hour to learn whether the new release still transpiles faithfully
across the whole compiler, against fifty-one minutes for rebank plus sweep.
Red means stop and read; green means start the rebank knowing the pipeline
survived.

**Say plainly in the README what it does NOT replace.** Everything codexzig
checks is the zig arm against itself or against `.expected`. The rungs
compare the zig arm against BARE METAL, and a defect the plug and the seed
share -- or one the emitter makes identically on both paths -- is invisible
here and visible there. Finding 42 is the case in point: a silent wrong
answer the fixed point could never have caught, because both arms would have
been wrong together. codexzig says transpilation still works; the rungs say
the answer is right.

**One thing to fix while wiring it:** `codexzig_corpus.py` now skips the
byte-comparison half when `native/codexir` is absent and says so, which is
the fresh-sandbox case the ceremony runs in -- confirm that path actually
works in a fresh sandbox rather than trusting the branch. **Still
unanswered on 2026-08-26**: the build went red before the corpus leg ran, so
that path has not been exercised in a fresh sandbox yet.

**IT RAN FOR REAL ON 2026-08-26, AND IT CAUGHT SOMETHING.** Update 50, the
canaries green, then codexzig between steps 2 and 3 exactly as this item
says: red, 47 undeclared `T38`s, in about fifteen minutes of a fifty-one
minute alternative that would have banked a release whose compiler does not
transpile. The item above is what it caught. **What is left here is the
PROSE** -- the README's "Processing a new Update" still does not name this
step, so the next person to run the ceremony follows a list that omits the
thing that just paid for itself. Write it in, including the paragraph above
about what it does not replace.

## 5. Thirty-nine corpus programs emit zig that cannot compile, one cause

**Objective: HUNTING, then OUTBOUND. KEYBOARD -- `codexzig_corpus.py` and
`zig build-exe -femit-bin=no` answer in seconds each.** Found 2026-08-26 while
characterising the 112 clean-but-unbuildable pile.

The emitted `main` launches the program's entry point on a thread
unconditionally:

    const t = std.Thread.spawn(.{ .stack_size = stack_bytes }, opening, .{})

`std.Thread.spawn` requires the entry function to return `void`, `u8`,
`noreturn`, `!noreturn` or `!void`. Every corpus program whose `opening`
returns a VALUE emits zig that zig rejects before it runs -- 32 returning
`i64`, 6 returning text, 1 returning `f64`. **That is 39 of the 112, one
defect, 35% of the pile.**

It is nearly unrecorded: `findings/README.md:1247` mentions it once in
passing, as the reason `final-batch-test` was never run. Nobody had counted
it.

**What it needs before it goes.** Whether a non-`Nothing` `opening` is
well-formed Codex at all -- the depot's own driver may reject it, in which
case the finding is that our plug accepts what the seed refuses, which is a
different row and a better one. Read `opening.codex`'s own entry handling
first, then decide which claim to write. **Cold-read the artifact before
sending**, per the lesson under "One question left behind PR 87".

## 5a. The 112 pile is characterised now, and the rest is a long tail

The 39 above are the head. The remainder, measured on the whole pile with
`zig build-exe`:

    47  expected type 'i64', found 'bool'  -- generated-code type mismatch
     5  use of undeclared identifier 'Frequency'
     5  use of undeclared identifier 'Timestamp'
     2  use of undeclared identifier 'T16'   (a 16-element tuple; `Tuple`
                                              defines Tup2..Tup5 only)
     2  use of undeclared identifier 'True'
     1  each: Duration, sin, a switch, two shadowing errors, and four more

**The `expected type 'i64', found 'bool'` cluster is 47 programs and is the
next one worth splitting**, on the same method: read the emitted zig at the
reported column, not the Codex.

**The hypothesis that sent us here is REFUTED and should not be retried.**
The queue said these might be the same missing-chapter bug as the halts,
which would have moved 150 programs at once. Measured A/B over all 112, one
variable: 111 refused before, 111 refused after; normalised for shifted line
numbers, four messages differed at all, and none changed class. The two
piles are unrelated.

## 5b. Four programs halt because our harness does not split quoted works

**Objective: INTEGRITY. KEYBOARD.** `quotes-gate`, `quotes-parse`,
`quote-from-peer` and `quote-from-store` halt at the error gate with
`CDX1000 Expected token kind mismatch` -- and `quotes-gate` and
`quotes-parse` are in the well-behaved 181, so they ran and matched
`.expected` while the front end was reporting a parse error about them.

**It is not unit assembly; it is the harness reusing half a driver.** The
driver splits the `%%QUOTED-WORKS%%` blob off the source and verifies the
signed definitions BEFORE tokenising (`opening.codex:1063-1073`,
`split-quoted-works`). `emit_harness.frontend_source` starts at `tokenize`,
so our harness hands the blob to the lexer as if it were code. The digest
`71f85b...` is the token it chokes on.

**Third time this shape has cost us**, after the error gate itself and the
`ir-emit-roots` list: a piece of the real driver the harness does not copy,
with no test that could tell. Fixing it means `frontend_source` calling
`split-quoted-works` -- which means bundling the chapter that defines it,
and that chapter is `opening.codex`, which cannot ride beside a harness
that defines `opening`. Same wall `czg-emit-roots` hit. **Decide whether to
copy the split or to teach the bundler to carry a renamed `opening`; do not
copy it silently, because that is exactly how the roots list drifted.**

The other nine halts are correct: they are negative tests
(`class-op-no-instance`, `effect-launder-*`, `let-effectful-bug`,
`mutable-alias`, `parser-resync`, `effect-handler-clause`) whose whole
purpose is to be diagnosed, and a compiler that diagnoses them is working.

## 5c. The census wants a re-bank, and it should ride Update 50

**Objective: INTEGRITY. BOX-adjacent -- `corpus_run.py --changed --bank`
takes the compute lock, ~25 minutes, no QEMU.**

`cite_resolve` now carries the implicit chapters (`8830e7b`), so every
`zig_sha` in `corpus/census.json` has moved and the bank is dated
2026-08-25. **Do not bank it against the u50-stack**: that tree is gone.
The pin moved on 2026-08-26 -- `u50-rebank` is `8cc80685`, seed `C45E5825`,
banking to `truth/u50` -- so a bank taken against the old tree would have
been stale before it was written. It rides the Update 50 ceremony, which is
itself waiting on the `T38` item at the top of this file.

What a re-bank must absorb, measured 2026-08-26 and both verified as
improvements, not regressions:

    dtls-fragment            refused -> match     NOT ours: finding 42's fix,
                                                  which landed after the bank
    list-comprehension-copy  markers -> refused    ours: its marker was
                                                  literally `no emitter for
                                                  map-list`

**And the number that says why this mattered.** The gap histogram -- the
thing that RANKS which emitter arm to write next -- went from 135 distinct
gaps to 133. The two that vanished are `no emitter for MkTup2` (18
programs) and `no emitter for map-list` (2). Twenty hits in the ranking
were our own missing chapters, which is the failure `cite_resolve.py`'s own
docstring was written to prevent: "the plug's fallback fires -- which looks
exactly like an emitter gap and is not one."

## 6. PR 87 is SETTLED; three probes are written and owe one compiler run

**Objective: OUTBOUND. The drafting and the writing are done; what is
left is a BOX run and a report.**

Answered and then **accepted as written**, 2026-08-26, both over Gmail.
The row withdrew and the trust-model re-scope replaced it. Their side:
the invariant gets declared in the **Developers Rulebook's plug-wire
contract section**, naming the shape, the CDX2010 occurs check as the
component doing the work, and the hand-authored-IR caveat; the
`IRTextParser` arity check is recorded as an open lead, not built.

**Two answers landed on US:** PR 87's reproducer was their arm B (full
arity, result happens to be a function), and the TCO gate is arity-blind
**on bare metal too** -- so finding 36 blamed the wrong component and is
re-framed.

**OWED, and explicitly accepted by them:**
- `findings/probe-pr87-alias.codex` -- the let-bound alias, **the shape
  their seven arms did not cover.** Prediction recorded in the file:
  the checker should refuse it, and if it ever compiled `is-self-call`
  would not fire at all, because through an alias the apply spine's root
  is `g` rather than the definition's name. That defeats the gate in the
  SAFE direction.
- `findings/probe-pr87-deck.codex` -- self tail call under `deck-record`.
- `findings/probe-pr87-armb.codex` -- their arm B with a base case,
  **executed** rather than compiled. Expects `5`. They said an executed
  arm is strictly better evidence and they will take it.
- The two coverage corners are already **source-read confirmed** here:
  `has-tail-call` answers False for `IrTry` outright and
  `has-tail-call-act` inspects only the last statement.

**Report either way. A null result is a result** -- they asked for it in
those words, because "tried and found nothing" moves confidence where
silence does not.

## 7. Diagnostics as a banked set

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

## 8. zigc has a runner now, and one inconclusive result

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

## 9. Every unhandled construct must refuse BY NAME

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

## 10. The refusal-gaps branch, rebased and re-verified

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

## 11. The tiers stay green, and each one earns its keep

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

## 12. The stack is measured now, and the emitter's prose about it is wrong

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

**ALL EIGHT LANDED IN UPDATE 50 (`8cc80685`, 2026-08-26).** The release
note says "eight PRs absorbed" and the tree agrees -- checked file by file
rather than taken on trust: `IRTextParser.codex` is byte-identical to
PR 89's, and finding 42's fix is in the released `ZigEmitter`. **Nothing is
open and nothing is prepared and unsent.** The eight, kept here until the
next queue entry displaces them:

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

**A DETACHED JOB IS RUNNING as of 2026-08-26 14:12 UTC. Read its verdict
before starting anything on the box:**

    tail -5 /home/steve/runs/20260826T141210Z-u50-natives-tiers/CHAIN-STATUS.txt

Three legs: `native_build.sh`, `tiers_run.py --bare`, `tiers_run.py --zig`,
each with its own log beside that file. It holds the compute lock while it
runs. **Leg 1 is the cheap experiment that decides the `T38` item's
diagnosis** -- codexzig joins codexir's chapters to ZigEmitter in ONE unit
and `native_build.sh` builds those two SEPARATELY from the same pin and
seed, so both green means the leak needs them joined (the round trip,
finding 44) and either one red with `T38` means a plain Update 50 emitter
regression. **Leg 2 writes `findings/gold/u50/` into a DETACHED sandbox
worktree: carry it back and commit it**, or the next `--zig` run pays QEMU
again for columns already measured.

**Update 50 ITSELF landed 2026-08-26 (`8cc80685`, seed `C45E5825`), and
its ceremony is STOPPED AT THE GATE.** Do not restart it below the `T38`
item at the top of this file.

Done:

- **Step 1, read before running anything: all four checks clean.** The
  contracts we hard-code both hold -- `ram-size-addr` 4072 (0xFE8) for
  `codex_vm.py`, and `serial-ring-buf-addr` 5242880 / `-size` 1048576 /
  wpos 28704 / rpos 28712 for `ring_compile.py`. `tools/codex-vm.c` moved
  84 lines and every one is I219 bed modelling, no contract surface.
- **All eight PRs (84-91) absorbed, verified rather than taken on trust.**
  `IRTextParser.codex` is byte-identical to PR 89; finding 42's fix
  (`zig-push-param-renames` composed under `zig-push-tail-renames`) is in
  Update 50's `ZigEmitter`. The remaining C# and emitter deltas are
  Damian's new work, not reverts. **The outbound queue is EMPTY again.**
- **Damian changed the emitter too**, so natives must be rebuilt and
  emitter behaviour may move: `zig-occurs` and `zig-max-list-len` now
  descend into a branch's GUARD and not only its body (a 40-element
  literal in a guard emitted no `@setEvalBranchQuota`), plus a
  `char-encode` builtin.
- **The pin moved, and one branch was misnamed.** `u50-rebank` pointed at
  the INTERIM `0c4327d5`, which banked as `seed-6cf4a8e0`; it is
  `seed-6cf4a8e0-rebank` now, and `u50-rebank` is the release. Both
  pushed. Sandboxes record codex COMMITS, not branch names, so nothing was
  stranded.
- **`seed_identity` needed teaching, or the bank would have misnamed
  itself** (`46e8f6a`). Update 50 names its seed in a fifth form,
  `**Release head: main 19777. Seed \`C45E5825\``, and without it the
  release derived as `seed-c45e5825` -- which would have banked a real
  release as if it were an interim and left it out of the `u<N>` pruner
  forever. Now `truth/u50`.
- **Step 2, the canary: GREEN.** New seed boots under our QEMU flags,
  takes the ring preload, output parses, 5.0 s -- same as the old seed.
  **It previews the bank diff**: diagnostics byte-identical (14, same
  codes, same line:col), image 72 bytes SMALLER and diverging from byte 9.
  So expect the x86 truths to move and the front-end truths to hold,
  which is what ~330 lines of changed `Emit/X86_64*` should look like.
- **Step 2.5, the codexzig gate: RED.** See the `T38` item. The rebank has
  not started, and that is the gate working rather than the ceremony
  stalling.

Left: everything from step 3 on, and none of it should begin until the
`T38` question is answered. `check_paths.py` will keep reporting FAIL on
`codex/plugs/zig/build-output/zig-plug.cdx` until `cycle.sh` runs once --
that is the ordinary fresh-pin artifact, not a finding.

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
