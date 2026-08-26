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

## 1. Finding 47: the guard is BUILT and MEASURED, and the message does not reach the user

**MEASURED 2026-08-26 20:08 by `verify_emitter.sh` on `419c292d`
(`~/runs/20260826T195402Z-f47-guard2`), the first chain that ever
compiled the three guard commits.**

    leg0 natives      GREEN  5m13
    leg1 tvar-matrix         case (g) diagnosed, and see finding 51
    leg2 corpus       GREEN  2m54   tvar markers 40 -> 8 -> 0, match 183 -> 185
    leg3 codexzig     GREEN  5m54   fixed point holds
    leg4 roc-ports    RED    2 of 11, three iterator ports -> finding 51
    leg5 sweep               running

**It did not compile at first.** `zig-closure-make` handed a sentinel-carrying
`Integer` to a parameter bounded `0..4294967295`; CDX2051, leg0 red in eleven
seconds, fixed in `419c292d`. Neither `8b493672` nor `d4ba6e75` had ever been
through a compiler -- the chain that should have caught it was cut before they
landed, which is the exact miss `verify_emitter.sh` exists to prevent.

**Zero type-variable markers across 606 programs**, down from 8 distinct over
10 program-hits at 19:02 and 40 before any fix. Nothing that matched stopped
matching. Reach is honest and small: 325 of 329 verdicts carried because the
emitted zig was byte-identical, and of the 12 that moved, 10 are programs
added today. The two real movers both went toward honesty --
`typeclass-poly` refused -> markers, and `inductive-list` markers -> refused
because the tvar marker had been standing in front of finding 48.

**What is left is finding 51**, and it is fixed at the keyboard in `6bf2911c`,
NOT BUILT. The refusal is correct and zig reports the parameter it stranded
instead. Next build settles it.

## 1a. `show` has five type cases and the plug implements one -- WRITTEN, NOT BUILT

**Written 2026-08-26 20:2x in `8b641203`. Text shows as itself, Boolean as
`True`/`False` through `zig-escape-text` (so the CCE bytes come from the same
escaper every other literal uses), everything else stays `cx_show_int`, and
the unit wrapper comes off first. Reals REFUSE -- see item 1c.**

Confirmed while writing it: `emit-show-bool` spells the tags `"True"` and
`"False"`, so `roc-early-return-predicate.expected` holding Roc's `True` is
right and the port needs no adaptation note.

Still owed: the `TextTy` case is predicted from source and NOT measured, and
no corpus program produced that mismatch. One probe before the fix claims it.

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

     40  startFn return type (thread entry)      finding 53   fix staged
     11  undeclared Frequency/Timestamp/Duration finding 17   unit families
      3  expected type 'void', found comptime_int             unclassified
      2  undeclared identifier 'True'            finding 52   fix staged
      2  expected 1 argument(s), found 0                      unclassified
      2  invalid operands: 'void' and 'void'                  unclassified
     10  singletons (shadowing, switch exhaustiveness, sin, CxFn1, ...)

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

## 1b. The corpus measurement cannot see a compiler error, and it is the same gate as this morning's

**Objective: INSTRUMENT. KEYBOARD to write (`ast/CodexIrHarness.codex`), BOX
to verify (`./native_build.sh`, then `./corpus_run.py --run`).**

Finding 49. `ast/CodexZigHarness.codex` got the driver's error gate this
morning; `ast/CodexIrHarness.codex` never had it, runs the same
`check-chapter`, binds the same `cr.state`, and lowers and prints regardless.
Measured over one 5,529-line bundle: an undefined name and a deleted argument
both give `rc=0`, an IR of the same size, and nothing on stdout. The
undefined name reaches the IR as a typed node.

`corpus_run.py` gates only on `returncode != 0 or not stderr`, so every
corpus program that does not compile is scored on the zig its broken IR
produced. When the same blind spot was opened in the codexzig path it showed
41 of 593.

**It goes AFTER items 1 and 1a, and that ordering is the point.** Item 1's verdict is
a DELTA against a bank taken with this instrument. Change the instrument
first and the comparison is gone -- the tree is part of the measurement, and
so is the harness. Run item 1's chain, then fix the gate, then re-measure
everything and expect the census to move.

**The fix is four files away**: merge `bag-from-list (toks.errors)`,
`doc.parse-bag`, `rr.bag` and `cr.state.bag`, halt if the bag has errors.
Copy the PIPELINE, not the list -- that is the lesson this file has now
learned three times (`ir-emit-roots`, the lambda lift, this).

## 2. Send the emitter fix, and decide which HEAD the rebank runs on

**Objective: OUTBOUND, then DUE_DILIGENCE. KEYBOARD to write the PR, BOX
for the rebank.**

**The harness lift is DONE and verified** (ladder `9266f10`, chain
`~/runs/20260826T160728Z-u50-harness-lift/`, 2026-08-26 16:32). Both hosted
harnesses now run LambdaLifting where `opening.codex:1713-1720` runs it. The
lift went into `emit_harness.py`'s `frontend_source` behind a `lift` flag
rather than into the two generated chapters -- `ast/*Harness.codex` is
gitignored and rewritten before every bundle, so an edit there is undone
silently, and two copies of the phase would have been the same failure one
level down. The flag defaults OFF: the rungs banked their truth against a
driver that did not lift.

**The ceiling is 0 and that is not laziness.** `lift-defs` asks
`deck-bound-short-of`, which compares `__heap-save` against the ceiling, and
the driver asks it from inside a phase-wide `deck-record` extent where
`__heap-save` reads the DECK CURSOR. Nothing `emit_harness.py` builds wraps a
phase in such an extent -- which is why every ceiling in that file is 0 -- so
`__heap-save` there is the real heap top, already above the reservation, and
a non-zero ceiling would stop the lift on its FIRST definition and emit a
truncated program without saying so. What bounds it is the 512 MB
reservation, and the emitted zig fails loud past it: `probe-deck-overrun`
passes by panicking with "the two cursors met".

### What the chain said

    leg0 natives          GREEN   codexir.ir 8,669,320 -> 8,870,818 bytes
    leg1 codexzig gate    GREEN   fixed point holds, 354 __lam on BOTH arms
    leg2 tiers --bare     GREEN   21 gold banked, committed as 782a45a
    leg3 tiers --zig      RED     STALE admission only; 0 unexpected on 22
    leg4 corpus census    GREEN   five programs moved, 134 -> 133 gaps
    leg5 codexzig corpus  RED     correct 179, halted 13, unresolved 16,
                                  564/564 byte-identical -- baseline exactly

Both REDs are the standing state. leg3's is the COMPILER-18 ledger; leg5
exits 1 whenever anything halts and the same 13 halt.

**The gate is the result.** It held last night because NEITHER arm lifted, so
the property was never posed against a subject containing a lifted lambda.
It now holds with 354 of them on both sides.

**The census move is smaller than this item used to claim, and that is worth
recording.** Four spawn programs -- `nested-spawn`, `network-scope-spawn`,
`proc-state-running`, `spawn-memo-table` -- gained `no emitter for
poke-byte`, because their spawned thunk bodies are lifted into defs the
emitter now walks. `db-full-test` LOST `unresolved type variable T88 of
hamt-fold`, one more site where a lifted lambda carries its own type
arguments and finding 46's rule finds a concrete answer. Nothing else in 594
programs moved, and no verdict changed. The blind spot was real and NARROW at
corpus scale; where it bit was the self-host.

### What is left

1. **The PR** for the emitter fix (finding 46, branch
   `zig-plug-tvar-not-an-answer` on the pin). Plugs backlog row, `Ladder:`
   line, and per the standing rule NAME THE STACK -- here that is the bare
   pin, since all eight prior PRs landed. **The harness lift is OURS and does
   NOT ride it.** Cold-read before sending; three outbound artifacts in a row
   had the wrong headline claim.
2. **DECIDED 2026-08-26: the rebank runs on the FIX branch,
   `zig-plug-tvar-not-an-answer` (`a961dcb6`).** The question looked like it
   had teeth and it does not, once two things are checked.

   `ast/rebank_all.sh` does two halves: bank the 14 bare-metal truths
   through the seed, then rebuild the zig plug and sweep against them.

   **The truths cannot move.** The fix branch differs from the pin in
   exactly ONE file, `codex/plugs/zig/ZigEmitter.codex`, and bare metal
   never runs the plug. The check that could have broken that argument is
   whether any RUNG SUBJECT bundles ZigEmitter -- it would then be part of
   what gets compiled -- and none does: `bundle_codexzig.ps1` and
   `bundle_ringplug.ps1` are the only two that carry it, and neither is one
   of the fourteen (`lex parse desugar scope check lower ir_to_codex
   ir_to_codex_roundtrip lir_to_x86 ir_to_wire ir_to_x86_on_fib
   ir_to_x86_on_cce passes_to_x86_on_mid passes_to_x86_on_arith`).

   **The sweep half cannot run on the pin at all.** That is what the 47
   `T38`s are: `native_build.sh` does not get through them on the bare
   release. Banking on the pin buys a correctly-labelled bank and a dead
   second half.

   So the only argument for the pin was the label, and the label is what
   the standing rule already covers: measure against OUR FORK'S STACK and
   NAME it. Here the stack is one commit, and it is the one about to be a
   PR. **Bookkeeping owed with the bank: record that the tree carried
   `a961dcb6`**, alongside the seed and harness-content the sidecars keep
   already.
3. **`ast/allcycles.sh` is still UNPAID**, and it is owed to the rebank, not
   to a chain: `restore_truths.py` answers "NO BANK for this seed" because
   `truth/u50` does not exist, and the sweep dies at rung one, 0/14. Nothing
   can pay it before the rebank.

### COMPILER-18 looks FIXED in Update 50, and the ledger is what said so

`prim-closure`'s `under-mutual` row on BARE METAL, across the three banks:

    u49              not-47
    seed-6cf4a8e0    not-47
    u50              47

The arms now AGREE, so tier 14's admission in `gold/EXPECTED.txt` went STALE
and `tiers_run.py` set the whole set RED to say so -- confirmed again by the
harness-lift chain's leg3 (STALE 1, green 15, noted 6, zero unexpected).
**This is the mechanism working exactly as `prim-closure.codex` says it
should** -- "it is the whole point of the file that the admission becomes
STALE the day the arms agree". Nothing in the zig plug is involved; the bare
arm does not touch it.

**Do not just delete the admission.** Confirm the partial application really
keeps its arity now (read `emit-partial-application` and `is-self-call`
against the release), then retire the admission, close finding 39, and say so
on the COMPILER-18 row. **The tier stops being a detector the day it stops
disagreeing**, so what replaces it is a live question -- that belongs with
"The tiers stay green, and each one earns its keep".


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

## 6. PR 87's row is ANSWERED and withdraws; the re-scope is drafted and unsent

**Objective: OUTBOUND. KEYBOARD, and the drafting is done.**

Answered 2026-08-26 by the Cobblestone compiler lane over Gmail, measured
against seed C3181693 (main 19889), seven arms compiled. **Q1 no, Q2 yes,
Q3 no distinct node exists.** The row withdraws.

**Two of the three answers landed on US, not on the row:**
- PR 87's reproducer is their arm B -- one parameter, one argument, a
  FULL-arity self call whose result happens to be a function. We already
  knew it could not reproduce; we did not know why.
- The TCO gate is arity-blind **on bare metal too**
  (`Emit/X86_64.codex:75-80`, verified here). Finding 36 filed that as a
  python-plug defect; python is copying the reference faithfully.
  Finding 36 is re-framed.

**What is left to send:** `outbound/DRAFT-pr87-rescope.md`, the
trust-model version they said they would find worth having -- no plug's
TCO gate checks arity, the invariant that makes that safe lives in the
type checker, and nothing near the gate says so. It asks for a comment
rather than a parser arity check, because who feeds hand-authored IR to
a plug is their call.

**Owed if we take their falsifiers** (offered in the draft, one compiler
run): three probe shapes -- a tail self-call under `deck-record`, one at
a non-final `act` statement, one through a `let`-bound alias -- plus
confirming the two coverage gaps we already read in bare metal
(`has-tail-call` answers False for `IrTry` outright; `has-tail-call-act`
inspects only the last statement). Neither gap looks like a route to the
shape; a tail call the pass declines to optimise is a deeper stack, not
a wrong answer.

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
