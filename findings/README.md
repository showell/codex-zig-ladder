# Findings

What the ladder has turned up, numbered in the order filed. **Each finding's
own opening paragraph states where it was found, whose arm it is, and whether
it is fixed -- that paragraph is the authority.** No tally lives on this line:
a count maintained by hand beside free-form status paragraphs says whatever it
last said rather than what is true.

This file holds the LIVE ones. Findings that are fully closed move to
`CLOSED.md`, which keeps their numbers and a one-line disposition each, so the
gaps here are explained rather than mysterious.

## A HYPOTHESIS IS NOT A FINDING, and it goes in its own section

**Added 2026-08-26, and the reason is worth keeping.** Finding 47 was filed
three times: first as an upstream compiler defect, then as a return-type gap,
and finally as three missing arms in one `when`. Each rewrite came from
reading source or IR rather than from reasoning about the previous version,
and each time the refuting evidence was under a minute away -- the first
filing was killed by prose that the fix commit under discussion had cited in
its own first paragraph.

The register is part of why. It had exactly ONE shape -- a filed finding with
a confidence line -- so a first guess had to enter as a finding or not at all,
and three corrections got recorded where one hypothesis surviving two
falsifications would have been the process working.

**So: a claim enters as a hypothesis, numbered `H<n>`, and is promoted to a
finding number only when its falsification test has been RUN and it
survived.** H-numbers are never reused and a promoted hypothesis says which
finding it became, so the trail from guess to result stays readable.

**Every hypothesis MUST carry two lines, and they are the point of the
form:**

    Falsified by:  <the specific observation that would prove this wrong>
    Cost to test:  <what running that costs -- minutes, a guest, a rebuild>

**If you cannot name a falsification test, you do not have a hypothesis
either -- you have a hunch, and it does not go in this file.** If you can
name one and it is cheap, RUN IT BEFORE FILING; the form exists for the
tests that are not cheap, or for a claim that has to be recorded while the
box is busy.

**And every FINDING gains a matching line:**

    Falsification attempted:  <what was tried against it, and survived>

A finding with no such line is a finding nobody tried to break.

## ONE ENTRY HAS CONTESTED STATUS -- 51. The other four are SETTLED and gone

**Found 2026-08-27 while pruning this file, and it stopped a bad deletion.**
Two of our own records disagree about whether PR 92 closed these:

- **PRIORITIES recorded** *"Closed by it: finding 47 (tvar scope guard), 50
  (`show`'s five type cases), 51 (a refusal strands its parameters), 52
  (Boolean literal patterns), 53 (the thread entry)"*.
- **These entries say otherwise**: 50 and 53 both say *"Not fixed."* and 47
  says *"not yet verified"*.

**Neither is evidence, and the likely story favours PRIORITIES.** Every one of
these was found on 2026-08-26 and PR 92 shipped on 2026-08-26 -- so an entry
saying "Not fixed" may simply predate its own fix by hours and never have been
revisited. That is the ordinary way a register goes stale, and it is why this
file is orientation rather than evidence.

**SETTLED 2026-08-27 for two of the five, from data already on the box.** The
honest re-bank's `run.jsonl` -- all 318 clean programs built and run at the
pin, which contains PR 92 -- plus the banked census's markers, together cover
both stages:

    52  Boolean spelling 'True'    0 run failures, 0 markers   -> CLOSED, deleted
    53  thread entry startFn       0 run failures, 0 markers   -> CLOSED, deleted
    51  stranded parameters        0 run failures              -> closed on the
                                                                  evidence there is
    47  tvar not declared          12 programs carry a marker  -> UNSETTLED
    50  show / Real                15 programs carry a marker  -> UNSETTLED

**47 and 50 are unsettled for a reason a corpus run will not fix.** Their
signatures OVERLAP other live work: `not declared at this site` is also finding
55's marker and, per finding 62, covers two distinct causes; `__real_to_text`
is item 1c, a separate live gap. A corpus scan cannot attribute those markers
to a finding. **Settling them needs each finding's own reproducer run, not more
corpus data**, which is a smaller and different job than the one first queued.

51 is closed on the only evidence available and is left in place at lower
confidence rather than deleted on it.

## Hypotheses

*Not findings. Each carries what would refute it and what that costs.*

### H2 -- LANDED, and deleted from this register

Absorbed upstream 2026-08-27 as main CL 20184 (new seed CL 20189), recorded
as COMPILER-30. The root cause was the CST lambda carrying no span. Findings
57, 58, 59, 61, 62, 63 and 64 are its descendants and are the live ones; the
H2 text itself is in git and in `findings/CLOSED.md`.


### H1. FALSIFIED 2026-08-26 17:52 -- Update 50 made the largest ladder unit uncompilable to IR-CCE in a 3 GB guest

Raised 2026-08-26 17:42, when `ast/rebank_all.sh` died at 11/12 on
`passes_to_x86` -- 2.65 MB of source, the largest unit. Its CDX compile
succeeded (2,304,302 bytes) and the IR-CCE compile of the same source then
stalled: `RuntimeError: guest stopped consuming at rpos 2097152 of 2652454`,
with the host having written the whole blob in two refills.

**What suggests it.** The same unit, same step, same host and same 3 GB
guest emitted **13,883,457 bytes of IR in 195 s** on 2026-08-25 against the
interim `0c4327d5` (`~/runs/20260825T122248Z-u50-rebank`). The only thing
that moved is the codex tree going interim -> release, and IR-CCE is exactly
the path Update 50 added `lift-lambdas` to. The zig plug is NOT in this path
-- the seed performs this compile -- so our own changes are excluded.

**What already argues against it.** The stall is during INPUT CONSUMPTION,
at 79% of the source, which is before a lift would run at all. A
lift-memory story does not explain a guest that stops reading. **This is
recorded because it is the fact that does not fit, and the fact that does
not fit is the one worth keeping.**

    Falsified by:  the retry of that one unit completing, or stalling at a
                   DIFFERENT rpos. Either kills determinism, and a
                   non-deterministic stall is transport or QEMU, not the
                   release -- the tree cannot explain a moving failure.
                   Also falsified by the interim tree stalling the same way
                   when re-run, which would make it not-Update-50 at all.
    Cost to test:  one unit, roughly six minutes of box time, the other
                   eleven truths already on disk in the sandbox. IN FLIGHT
                   since 17:44 (`~/runs/20260826T171739Z-u50-rebank-tvar/
                   retry-passes.log`).

**FALSIFIED, by its own stated test, nine minutes after it was raised.** The
retry of that one unit COMPLETED: `stream: 14,029,343 bytes in 219 s`,
`SIZE: 14029026, got 14029026`, `wrote ast/passes_to_x86.ir`. A stall that
does not reproduce is not the release -- a tree cannot explain a moving
failure -- so this is transport or QEMU, and it belongs with the transport
defect rather than with Update 50. The rebank was resumed from the sweep
rather than re-recording eleven good units.

**One number worth keeping out of it.** The IR is 14,029,026 bytes against
the interim's 13,883,457 -- **+145,569, about 1%** -- which is the lift
adding lifted definitions to the largest unit, and it compiles fine. So the
lift's cost on this path is measured now, and it is small. That was the
thing H1 was reaching for, and it turns out to be the opposite of a problem.

**What it would have cost to file this as a finding instead:** a numbered
entry in the register asserting a release regression, and a retraction. The
hypothesis form was written twenty minutes before this and H1 was its first
use.


This directory holds the findings and the probes that make them runnable. It
is discussion material rather than a proposed addition to the Codex tree,
which is why it lives here: PR 67 is cut down to the `contrib/README.md`
pointer, so the record moved to the repository that maintains it. Take any of
it into the tree whenever it is useful; nothing here needs to be there for the
ladder to run.

**A finding here reaches nobody by itself.** `contrib/README.md` in the Codex
tree names the route: a small branch off master carrying a `Ladder:` line,
with the entry written into `codex/plugs/plugs-backlog.md` or
`codex/compiler/compiler-backlog.md`. Findings 14, 12 and 66's arrived that
way and their rows carry our name. Nothing notifies anyone otherwise.

The probes are Codex chapters and still compile with the depot's own tooling:

    build/compile.ps1 -Src findings/<probe>.codex -Out <out>.cdx

**What is banked, and against which seed, lives in the ladder's own README and
only there.** This page says what happened to findings, not what the ladder is
pinned to; when the two disagreed it was always this copy that had gone stale.

**The CDX2064 ATA finding is filed upstream as issue 70** (2026-08-18) and has
no number here: the compiler's own CDX2064 caught `emit-ata-wait-ready-bounded`
patching its loop jcc six bytes late, which is finding 10's mutation hazard
with a live site attached. Detail in `findings/cdx2064-ata-wait-ready.md`,
including the eight sibling sites the checker cannot see.

**Findings 6, 8 and 9 are recorded as found rather than fixed, and were
measured against seed 2,798,031** -- they have not been re-checked since.
Findings 7 and 10 were re-checked and still stand: `codex/compiler` has no
`IRExpr` map or fold, and `emit-record-set-builtin` still stores through the
evaluated pointer, so `__record-set` still mutates while the `mutable` keyword
still promises value semantics nothing delivers.

## 6. `lift-lambdas` exists, and runs after the plug wire is written

`codex/compiler/IR/LambdaLifting.codex` is a complete lambda-lifting pass:

```
lift-lambdas        : IRChapter, Integer -> IRChapter
FreeVar             = record { name : Text, type-val : CodexType }
collect-free-vars   : IRExpr, SkipListText, SkipListText, List FreeVar -> List FreeVar
build-lifted-params : List FreeVar, List IRParam -> List IRParam
build-partial-app   : Text, CodexType, List FreeVar, Integer, Integer, SourceSpan -> IRExpr
```

It has one caller, `opening.codex:831`, in the `cdx-chapter` path with its
own LIFT phase and deck budget. The plug path is `emit-ir-cce`, which runs
`compile-frontend-ir` and the named IR pipeline and never reaches it. So
the IR on the wire still contains lambdas that close over enclosing
locals, and nothing in the plug interface says so.

**What that cost here.** Zig admits a comptime constant into a nested
function and refuses a runtime value, so
`map-list (\a -> resolve-type-expr tdm a) args` cannot be emitted as
written: `tdm` is a parameter of the definition around it. Getting the
check rung green meant adding free-variable analysis to the zig emitter --
a list of the names that are runtime locals of the function being emitted,
threaded through definition parameters, let bindings, match binders and
act bindings, intersected with the names each lambda body mentions, with a
shadowing rule so a lambda parameter that hides an enclosing local is not
mistaken for a capture.

Almost none of that was necessary. `lift-lambdas` rewrites the use site as
a **partial application** of the lifted definition, and this plug already
handled partial application -- `zig-closure-make` builds the environment
struct and the trampoline, and predates this work. Lifted IR would have
arrived in a form the plug already knew how to emit.

`FreeVar` also carries `type-val`. The plug has no equivalent, so each
capture's field type is `@TypeOf` of the value hoisted outside the
environment struct, because read from within it the enclosing local is
exactly what zig will not name. That works, but it is a workaround for
type information this pass already computes.

**Not a request to move it.** Lifting is a pessimization for any target
that has closures, which is most of them: C#, JS, Haskell, Clojure and
Elixir all want the lambda to stay a lambda. Running it before the fork
would make the primary consumers worse to make the tertiary ones simpler.
Opt-in is the right shape, and the mechanism for that already exists and
is already used for a plug:

```
default-ir-pipeline   = ["fold-constants", "inline-leaf-calls", "inline-single-caller"]
text-plug-ir-pipeline = ["fold-constants"]
```

`lift-lambdas` is a phase with its own deck budget rather than a
registrable pass, so this is not a one-line change. But `passes=` is
already the place where a plug says which transforms it wants.

**The smaller export may be the better one.** This plug never wanted
lifting. It kept each lambda where it was and only needed to know the
lambda's free variables and their types. A plug targeting C would want the
whole pass; a plug targeting a language with closures wants neither;
this one wanted only the query. `collect-free-vars` is cheaper to expose
than `lift-lambdas` and serves more targets.

Offered as an observation with a measurement attached rather than a
request. "Tertiary plugs pay this, that is the deal" is a legitimate
answer.

## 7. There is no `IRExpr` map or fold, so every plug rewrites the walk

`Types/CodexTypeTree.codex` gives `codex-type-map-children` and
`codex-type-fold-children`, and consumers build on those instead of
re-enumerating the type constructors. `IRExpr` has no equivalent, so a plug
that needs to ask anything about an IR subtree enumerates all 24 of them
itself. This one has `zig-occurs`, a 24-arm `when` answering "does this
expression mention this name", used to decide whether a `let` binding is
dead, whether a parameter needs a discard, and which names a lambda
captures. Finding 6's free-variable analysis is built on it.

Stated as duplication rather than as a bug, because we went looking for the
obvious hazard and did not find it. The one arm in `zig-occurs` that does
not descend fully is `IrHandle`, which skips its clauses -- and this plug
also drops handler clauses at emission, so the walk is consistent with the
feature being unimplemented rather than with an oversight. `IrTry` and
`IrWithTimeout` looked like gaps at first glance and are not: their first
fields are `Integer`, not `IRExpr`.

So the cost we can demonstrate is only that the walk had to be written, not
that writing it went wrong. Worth weighing against the fact that the
precedent for the fix is already in the tree: the type tree got its map and
fold, and the IR did not.

## 8. passes=text-plug changes the IR's type vocabulary, and nothing says so

`IR/Passes.codex` tells a plug that emits SOURCE to drop the inline passes,
and says why in so many words:

```
 A plug that emits SOURCE resolves a call by its name, so a pass that
 substitutes a body and deletes the call deletes the plug's only handle on
 it. The inline passes are therefore absent here and must stay absent.

  text-plug-ir-pipeline : List Text
  text-plug-ir-pipeline = ["fold-constants"]
```

Good advice, and taking it changes more than which calls survive. It changes
which TYPE CONSTRUCTORS reach the wire.

`probe-forall-sort.codex` in this directory is the reproducer: bundle it
with `codex/foreword/core/Sort.codex` and nothing else, compile IR-CCE, and
read the def. Compile the same `sort-by` inside a large unit under each
pipeline and the definition's type differs:

```
default-ir-pipeline    (fn (list (tvar 51)) (fn ... (list (tvar 51))))
text-plug-ir-pipeline  (forall 51 (fn (list (tvar 51)) (fn ... (list (tvar 51)))))
```

With the inline passes on, a polymorphic definition arrives already
specialised and its quantifier is gone. With them off it arrives quantified,
and `ForAllTy` appears on the wire where the machine-code plugs reading the
same IR-CCE never see it.

**What it cost us.** This plug handled `ForAllEff`, the effect-level
quantifier, in eight places, and `ForAllTy` in none -- so a quantified type
had no arrows to count, could not be peeled to find a return type, and had
no zig rendering at all. It surfaced as `sort-by` emitted with return type
`void` around a body returning a list, three phases away from the cause, and
only because zig objected to the mismatch. Six milestones had passed on the
default pipeline without ever meeting the constructor.

That is our defect to fix and we have fixed it. The finding is that nothing
warns a plug author this is coming. The prose above is careful to say the
inline passes matter to a source plug; it does not mention that following
the advice widens the type vocabulary the plug must handle. A plug developed
and tested against the default pipeline is not tested against the IR it will
actually receive once it does the recommended thing.

Worth a look across the fleet: any plug that emits source, uses
`text-plug-ir-pipeline`, and has no `ForAllTy` arm has the same hole. The
symptom is not a crash but a wrong type, which is the kind that travels.

Two smaller notes from the same trail, neither demonstrated to have fired,
both offered only as things we noticed:

`lower-def` reads a definition's type with `lookup-type-bsearch types rn`,
which answers `ErrorTy` from three separate paths -- empty list, position
past the end, name mismatch at the position found -- and never distinguishes
"no such binding" from "the binding is an error type". A definition that
silently loses its type is hard to trace back from, as this one was.

`zig-peel-return`'s analogue in any plug has the same shape: peeling N
arrows off a type with fewer than N returns what is left rather than
reporting the shortfall. Combined with the above, a missing type becomes a
plausible wrong type rather than an error.

## 9. An undefined type name in an annotation compiles without a word

Misspell a value name anywhere and CDX3002 says so. Misspell a TYPE name
in an annotation and nothing does: the unit compiles clean, runs, and
answers correctly around the phantom.

Three probes, each one chapter:

- `probe-phantom-field.codex` -- a record field typed `List PhantomType`,
  with `PhantomType` defined nowhere. Compiles with zero diagnostics; the
  record is constructed with `[]` for the phantom field, the program runs
  and prints its other field.
- `probe-phantom-bare.codex` -- the field typed bare `PhantomBare`, no
  List wrapper. Same silence.
- `probe-phantom-sig.codex` -- a definition signature
  `f : PhantomSig -> Integer`. Same silence, so the hole is not specific
  to field position: type names in annotations are simply never
  existence-checked the way value names are.

Found by bundling: our lir subject carried `CodegenState` before its
`TypeBinding` field type's chapter was in the unit, and bare metal
accepted it -- then again with `RenameEntry`, which `TypeEnv` names in a
field without citing ChapterScoper. The monolithic build always carries
every definition, so the miss costs nothing there; a subset build sails
through compilation and the mistake surfaces later, somewhere else, or
never. The zig plug is stricter than the seed here only by accident of
its target: zig demands the struct exist.

Seed F3722EAC (Update 43), QEMU/TCG, verified against all three probes
on 2026-08-16.

## 10. `__record-set` mutates, and only two lines in the tree depend on it

Every plug has to decide whether `__record-set r "f" v` returns a new
record or the same one modified. Nothing in the language says. The
declaration syntax offers a `mutable` keyword on records, which reads as
a promise that plain records are values -- and `CodegenState` is a plain
record.

Bare metal does not read it that way. `emit-record-set-builtin`
(X86_64Builtins.codex) evaluates the record to a pointer, stores the
field through it with `emit-narrow-store-proven`, and returns that same
pointer. There is no copy anywhere in the function, for mutable and
plain records alike. The C# plug agrees:

    _Buf.rset(record, __rs => { __rs.field = v; })

a lambda that assigns through a reference and hands the object back. So
the rule is that `__record-set` mutates. The `mutable` keyword selects
something else -- whatever it selects, it is not this.

The rule is invisible almost everywhere, because the ordinary shape is
bind-the-result-and-use-the-result: 354 `__record-set` calls in the ir_to_x86
subject and copy would serve for all but two of them. It takes an ALIAS
-- reading a binding made before the update -- for the two answers to
differ, and the x86 back end aliases in exactly two places:

`X86_64Helpers.codex:1539`

    in let st12c = emit-list-tail st12b
    in let st14 = emit-text-concat-list st12b      <- st12b, not st12c

`X86_64Helpers.codex:453-457`

    in let st25 = st-append-code st24 (mov-store reg-r13 reg-r15 0)
    in let st26 = st-append-code st25 (mov-rr reg-rax reg-r13)
    in let st27 = st-append-code st26 (pop-r r15 & r14 & r13 & r12 & rbx)
    in st-append-code st25 x86-ret                 <- st25, not st27

Both are correct under mutation and both read as typos, the second
especially: `emit-unicode-bytes-to-text-helper` sits twelve lines below
with the identical shape and ends `st-append-code st27 x86-ret`. A
reader cannot tell the pair apart by intent, only by running them.

Under value semantics the damage is silent and specific. The emitted
machine code loses `__list_tail`'s entire 69-byte body -- its name still
recorded in the offset table, so the function count is unchanged -- and
loses a 12-byte epilogue, leaving a helper that pushes five callee-saved
registers and never pops them. 81 bytes short out of 45,432, found only
by diffing the ir_to_x86_on_fib subject's emitted code against bare metal.

Three things might be worth doing, in ascending order of appetite:

1. Say it somewhere. One sentence in the `__record-set` docs -- "returns
   the record, mutated in place" -- costs nothing and every future plug
   reads it.
2. Rewrite the two sites to use the binding they mean (`st12c`, `st27`).
   The output is identical under mutation and they stop reading as bugs.
3. Decide what `mutable` on a record declaration is for, given that
   plain records already have reference semantics. If it is vestigial,
   dropping it removes a promise the implementation does not keep.

Found by the ir_to_x86_on_fib rung: the x86 code generator compiling fib, emitted
two ways. The zig plug had given plain records value semantics on the
strength of the declaration, which is why the divergence appeared at all
-- and it is now one representation, a pointer, matching bare metal and
C#. Seed F3722EAC (Update 43), QEMU/TCG, 2026-08-16.

## 13. A cite is satisfied by presence, but only after the registry says no

**Proposed change, not a defect they have today.** Patch:
`findings/present-hoist.patch` (two files, +12/-2).

`Resolve-PlugForewords` opens by stating the rule:

> A cite is satisfied two ways, and the second one is why the strict pattern
> needs this: the chapter is RESOLVED through the registry, or it is already
> PRESENT because Add-PlugChapter bundled it.

The code asks the second question only when the first one fails. `$present` is
consulted inside the not-found branch, so a chapter that is BOTH present in the
unit and resolvable from the registry is bundled a second time, under the quire
the cite named, with every definition in it duplicated.

That is the shape of both bundling bugs this ladder has been bitten by.
`ListUtils` sat in eleven of our bundles for months and produced 108-plus
CDX3006 warnings a sweep; `CCE` did the same and Update 46's CDX3001 made it
fatal. Both were ours to fix, in the sense that our bundles hand-list thirty to
fifty chapters where a depot plug lists two. Nobody upstream is doing that
today, which is exactly why the change is cheap now.

Hoisting the presence test above the registry lookup makes the rule the comment
already describes. Measured 2026-08-18, on Update 46 plus the `__deck-set` fix:

| what | result |
|---|---|
| ladder bundles, 14 rungs | byte-identical |
| our other three bundles (irmem, min, zigc) | byte-identical |
| **depot plug bundles, all 52 using `Build-TranspilerPlug`** | **byte-identical** |
| the `cites Plug chapter Plug Types` path (arm64, riscv) | still resolves, no exit 3 |
| a bundle that both lists and cites `ListUtils` | 96 duplicated lines gone, nothing else changed |

The fleet numbers come from bundling every plug twice, with the compile step
stubbed the way `cycle.sh` already stubs it. So the change is inert across the
whole tree as it stands and only fires on the pattern that has cost us two
debugging campaigns.

`plug-build-lib.ps1` is generated, so the patch carries both
`codex/build/plugbuildlibScript.codex` and the regenerated script. The generator
was compiled and run to confirm it emits the shipped file: 230 of 230 lines
identical before the change, and after it the emitted text differs from the
shipped script by exactly the hoist. The 52-plug measurement above was then
re-run against the GENERATED file, not a hand edit.

Not verified: their gate.

## 14. `check-generated-scripts.ps1` cannot run under Linux pwsh

`build/compile.ps1` grew a QEMU fallback for hosts with no `codex-vm.exe` and
it works: it compiled the generator above on Linux in 37 seconds, taking the
`$script:UseCodexVm` false branch.

`build/test-compile-batch.ps1` did not get the same treatment. Line 98 calls

    Start-Process -FilePath $script:CodexVmBin ... -WindowStyle Hidden

unconditionally, and PowerShell on Linux refuses the parameter outright:

    Start-Process: The parameter '-WindowStyle' is not supported for the
    cmdlet 'Start-Process' on this edition of PowerShell.

It fails in under three seconds, before any compile, so `check-generated-scripts.ps1`
is unavailable on a Linux host whatever else is installed. Anything else routed
through the batch runner is unavailable with it.

The workaround is what finding 13's verification did: `compile.ps1` per
generator, then run the `.cdx`. That is one VM boot per generator instead of one
for the set, which is the cost the batch runner exists to avoid, so it is a
workaround and not a fix.

## 17. Unit families are handled three different ways in three emission paths, and none of them is right -- 16 corpus programs, three error messages, one gap

**Found 2026-08-19 by triaging the census's undeclared-identifier refusal
family. Characterized from IR and emitter source; fix not yet applied.**

`Timestamp = unit family NanoStamp` (Foreword DateTime) declares a
units-of-measure type: integer-backed, compile-time scale factors. The IR
carries the declaration as `(unit-def "Timestamp" (a-named "Integer"))`,
type annotations as `(a-named "Timestamp")`, and resolved types as
`(unit "Timestamp" int-default)` -- the backing type rides along in both
forms. The zig emitter has no arm for any of the three: the unit-def is
dropped, the name is emitted verbatim as a zig type, and the program is
refused on an undeclared identifier. This bypasses the loud-marker net
("no zig type for this codex type") exactly the way the emitter rules
predict: a name error, not a type error.

The census says the family is worth having: 8 of 72 refusals
(ota-update, ota-gate-block, ota-state-machine, final-batch-test on
Timestamp; osc-noise, audio-diffusion-test, av-codec-test on Frequency;
infra-test on Duration). The ninth undeclared-identifier refusal
(literal-subpattern's `sin`) is a separate libm gap.

Cross-plug: the C# emitter declares nothing for `AUnitTypeDef` and its
type renderer maps `UnitTy (name) (inner)` to `"void"`
(CSharpEmitterExpressions.codex:60), so a unit-typed record field should
emit illegal C# -- unverified, since its witness path never compiles the
corpus. The machine-code plugs erase units to integers, which is the
model to follow.

Fix shape (zig): `unit-def` emits `const <Name> = i64;` (the backing
type is in the node, so the alias is faithful, not a guess); emit-zig-type
and zig-expr-type get a `(unit name inner)` arm answering the inner
type's rendering. ota-update's IR never applies a unit constructor in an
expression, so the type-level mapping may be the whole fix; whether the
front end folds scale conversions into plain arithmetic is the thing the
rerun will answer.


**REACH RE-MEASURED 2026-08-26 21:4x by the corpus reading pass, and it
is 16 programs, not 8 -- because the gap wears three different error
messages and only one of them was being counted.**

    11  use of undeclared identifier 'Frequency' / 'Timestamp' / 'Duration'
     3  expected type 'void', found 'comptime_int'
     2  invalid operands to binary expression: 'void' and 'void'

All sixteen are unit-family subjects. `unit-family`, `units-foreword`,
`unit-smoke` and `implicit-convert` are the four that were never counted,
and their names say what they are.

**The three messages are three emission paths disagreeing with each
other about the same type:**

- **The type mapping erases it.** `emit-zig-type` maps `UnitTy` to
  `"void"` (`ZigEmitter.codex:296`). A `Length` parameter becomes a zig
  `void`, so `(w +% h)` becomes `void +% void` -- that is
  `unit-family.zig:842`, and it is the `invalid operands` message.
  `unit-smoke` is the same erasure meeting a literal: `const built = 99`
  against a `void`, which is `expected type 'void', found comptime_int`.
- **The record-field path emits the NAME.** `sound-test.zig:844` reads
  `ob_sample_rate: Frequency,` -- the family name, verbatim, undeclared
  in zig. That is the message the original finding counted.
- **The constructor path emits a real function.** `fn Meter` IS present
  in `unit-family.zig`, so constructors survive while the type they
  construct does not.

So the plug does not simply lack a mapping. It has three, they are
inconsistent, and the loudest of them (the bare name) is the one that got
noticed while the erasure quietly turned typed arithmetic into `void`
arithmetic.

**UNVERIFIED:** which path emits the record field, and whether the
constructor functions have coherent bodies. Both are one read of the
emitter away and neither changes the count.

**Why this matters for ranking:** at 16 it is the second-largest cause in
the corpus behind finding 53, ahead of everything else. The earlier
number put it fourth.
## 20. `IrApproxEq` emits `==`; the 4-ULP band has zero width on the zig arm

**Found 2026-08-18 by an emitter audit (probe written then, blocked on the
real-literal family until 2026-08-19); both arms measured 2026-08-20.
Ours to fix -- the emitter's arm, not an upstream defect.**

`~` is the only equality Real has (`==` on a Real is refused, CDX2085),
and bare metal implements it as a 4-ULP band: both operands map to
monotonic ordinals and the ordinal distance compares against 4
(X86_64.codex, emit-approx-eq: `cmp 4 / setcc be`). ZigEmitter maps
IrApproxEq and IrApproxEqExact alike to zig `==`.

The probe (`findings/probe-approx-eq.codex`) uses 0.1 + 0.2 vs 0.3 --
adjacent doubles, one ULP apart by construction, no bit-twiddling
builtins. Measured:

    bare metal (droplet appliance, u48 seed):  one-ulp 1 / same 1 / far 0
    zig arm (u48 emitter; the natives' IrApproxEq path is diff-verified
    identical to the verbatim release):        one-ulp 0 / same 1 / far 0

The controls agree on both arms, so the divergence is exactly the
tolerance. The probe's own folder caution was checked: the emitted IR
carries the IrApproxEq nodes, so both arms evaluated `~` at runtime.

Fix shape (ours, rides the next emitter batch with the gap families): a
`cx_approx_eq` prelude fn implementing the same ordinal mapping and
distance-4 test, with IrApproxEq routed to it; whether IrApproxEqExact
keeps `==` is a question for the IR's own definition of exactness --
read `ir-expr-type`'s chapter before assuming.

## 21. The zig plug discarded `__list-with-capacity`, corrupting the emit tables

**Found 2026-08-21 by the heap-unification branch's own ladder run. Ours
to fix -- the plug's arm, not an upstream defect. Fixed on the branch at
`17329ed9`; the branch is still red on a second, open escape.**

`cx_ll_with_capacity` was `_ = n; return cx_ll_empty(T)`. The emit tables
are pre-sized to `accum_capacity()` so a push inside `emit-all-defs`'
per-definition save/restore bracket never reallocates; ours grew
geometrically from zero, so a push moved the backing array into scratch
the bracket then reclaimed. The compiler predicts this failure verbatim in
the guard beside that bracket ("a push past it reallocates into scratch
that this loop reclaims, corrupting the table").

Invisible until `__heap-restore` did something: the arena never reclaimed,
so the moved array stayed valid forever. This is the second defect the
arena was masking rather than causing.

Full diagnosis, the open second escape, and -- importantly -- the false
lead that was ruled out (the deck nesting counter going negative is
FAITHFUL; `X86_64Builtins.codex:1030` does the same) are in
`findings/zig-heap-unification.md`, section "The ladder run, 2026-08-21".

## 22. Text accumulation is linear on bare metal and quadratic on the zig arm

**Found 2026-08-21 with `findings/probe-memory-model.codex`, measured on
both arms the same day. Ours to fix -- the plug's arm. Asymptotic, not a
constant factor, which makes it the most consequential plug divergence
found so far.**

Bare metal selects `__str_concat_inplace` (`Emit/X86_64TextHelpers.codex:287`)
for a text accumulator, via the tail-recursion analysis at
`Emit/X86_64.codex:2376-2396` (`is-inplace-append`) and `:225-250`
(`inplace-accumulators`) -- the Update 43 change that took a quadratic
selfhost path to linear. ZigEmitter has no equivalent: it always emits a
fresh `cx_concat`, so an accumulator loop copies the whole accumulator every
iteration.

The probe builds a text by repeated concatenation at n = 64, 128, 256 and
prints the bytes consumed and the ratios:

    bare metal   72   136    264    ratios 1.9 1.9 -> LINEAR
    zig arm    2080  8256  32896    ratios 4.0 4.0 -> QUADRATIC

The zig figures are exactly the triangular numbers `n(n+1)/2` (2080 =
64*65/2, and so on), which is what copying the accumulator each step costs.
Bare metal is `n + 8`. At n = 256 that is 264 bytes against 32,896 -- 125x
-- and the gap grows without bound, so it will dominate any constant-factor
difference on a large enough subject.

Two controls in the same run say this is a real divergence and not the
probe's shape. `push-accum` is linear on both arms (528/1040/2064 against
681/1145/2889). `cat-accum` -- building a LIST by repeated `&` -- is
quadratic on **both** (20240/73232/277520 against 44065/137249/471073), so
that one is inherent to the source and not ours to fix.

The same run independently reproduces finding 21 from the other direction:
`__list-with-capacity` costs bare metal exactly `cap*8 + 16` (16, 144, 2064
at capacities 0, 16, 256 -- the rule read out of
`emit-list-with-capacity-builtin-bivy`) and costs the unfixed zig plug a flat
~25 bytes at every capacity, because it discarded its argument.

Filed with it, from writing the probe: **`__deck-alloc` has no zig emitter
at all** (`zigemit` plants `@compileError`; the builtin appears nowhere in
`codex/plugs/zig/`), and **`__list-with-capacity` with an uninferable element
type emits an undeclared type variable rather than refusing** -- called in an
unannotated lambda it produced `cx_ll_with_capacity(T52, ...)`, which is the
"never map an unhandled construct onto a valid-but-different one" failure
with the marker net silent.

## 23. The plug's CCE encoder refuses U+22A2, which is in the compiler's own source

**Found 2026-08-21 while re-deriving the deck numbers through the native
loop. Ours to fix -- the plug's arm. Small, sharp, and it blocks a whole
measurement path.**

`cx_cp_to_cce` walks the CCE table, then the tier-1 ranges, then tier-2, and
panics if a codepoint matches none: "codepoint outside the CCE tiers". U+22A2
`⊢` matches none.

Tested one codepoint at a time through `native/codexir`:

    Γ U+0393  ok      τ U+03C4  ok      é U+00E9  ok
    ⊢ U+22A2  REFUSED ε U+03B5  ok      λ U+03BB  ok

So the gap is one character, not a family. It occurs exactly once in the
depot, at `codex/compiler/Types/TypeCheckerInference.codex:8` --
"The judgment is Γ ⊢ e : τ | ε" -- and that single occurrence aborts
`codexir` on the whole 2,496,998-byte ir_to_x86 subject, five seconds in, before
any compilation happens.

Bare metal encodes it: the ladder's two ir_to_x86 rungs pass through the
ring, where the seed does the encoding, so the plug's tier coverage is
narrower than bare metal's rather than the character being unencodable.

Consequence worth naming: the native loop is the cheap path (a third of a
second against eleven minutes through QEMU), and it works on every corpus
program because those are ASCII. It fails on real compiler source. That is
the wrong way round -- the cheap path should be the one that handles the
hard input -- and it is why the deck numbers have been measured on patched
artifacts rather than emitted ones.

Fix needs bare metal's own tier table read out and matched, not guessed: the
encoding is observable, so inventing a code for U+22A2 would diverge on
every text that contains it.

## 24. codexir dies on a large subject, and it is not a lifetime bug -- nor a volume defect

**Found 2026-08-21 with the native loop, once finding 23's CCE fix let it
ingest real compiler source. OPEN. Ours to fix, arm unknown -- the evidence
rules out every mechanism we have chased this week.**

`native/codexir` built from `zig-plug-heap-unification` aborts 12.7 seconds
into the 2,496,998-byte ir_to_x86 subject:

    check_chapter -> register_all_defs -> resolve_def_name
      -> rename_has_entry -> bsearch_rename_pos -> cx_list_at

`cx_list_at` reads a `CxList` whose metadata is impossible. One run:
`len 131,892,766,817,456`, `cap 131,892,689,737,336` -- **capacity smaller
than length**, which no ArrayList can produce. Another: `len` equal to the
list's own data pointer minus 1080, i.e. pointer-shaped. The binary search
then takes `mid = len/2` and indexes 66 trillion elements past the region.

So a live object's header is being read as something that is not a header.

**What it is not**, each ruled out by measurement rather than argument:

- **Not use-after-reclaim.** `codexir.zig` contains exactly one
  `cx_heap_restore` -- the definition. It never calls it. Nothing is
  reclaimed.
- **Not reuse of freed memory.** Making `cx_bump_free` never rewind the
  frontier, so no byte is ever handed out twice, changes nothing.
- **Not the in-place text concat** landed in `0e24f7cf`. Reverting it to the
  copying form changes nothing.
- **Not a wrong argument.** Printed at both ends: `renames` is the same
  pointer at creation and at the `register_all_defs` call, with `len 0`. A
  bsearch over a zero-length list never indexes at all, so the header is
  intact at the call and garbage by the time it is read.
- **Not the deck guard's business.** `cx_frontier_crosses` is compiled in
  and never fires.

**Update 2026-08-21, from tier 5:** the buffer suspect below is EXONERATED as a
divergence. `findings/prim-buffers.codex` shows an out-of-buffer write lands on
the neighbour on BOTH arms, so that is upstream's semantics and we mirror it.
The same run found a better candidate that did not previously exist as a
hypothesis -- finding 27, a reserved buffer reading as zero on bare metal and
as dead objects here.

Which leaves one category: **something writes over a live object**, with no
reuse in play. The only writers into the region besides the allocator are
the `__buf-*` family, which write at `base + offset` with no bound beyond
the whole reservation -- `cx_buf_want` checks the address against
`cx_heap_reserve` and nothing checks it against the buffer's own capacity.
That is the next instrument: refuse a buffer write that lands outside the
buffer it names.

Worth its own line: this reproduces in **12 seconds natively** where the
equivalent rung is eleven minutes through QEMU, which is the whole return on
finding 23.

**Confirmed on a clean build, 2026-08-21.** The first sighting was on a
hand-patched `codexir.zig`, which is not evidence about the toolchain. Rebuilt
from scratch in a sandbox (ladder `4349606`, codex `a9a329a0`) with the CCE fix
coming from the emitter rather than a patch, and with the subject regenerated
in that sandbox: identical crash, identical frames, `cx_list_at` ->
`bsearch_rename_pos` -> `rename_has_entry` -> `resolve_def_name` ->
`register_all_defs` -> `check_chapter`. It runs 38 seconds before dying rather
than 12.7, which is the only difference and is unexplained.

**Split in half by the slack experiment, 2026-08-21 evening.** The census
natives (branch tip `1db8a78c`) reproduce the crash at slack 0 in 17.6s with
the exact recorded frames, and the deck instrument narrates the mechanism as
it happens: `used=191933132 reserved=109051904 headroom=-82881228`, monotonic,
never a rewind. With ONLY `cx_deck_slack` raised to 256 MB (the JUSTIFICATIONS
methodology, one constant in the emitted source), **the corruption does not
happen** -- no GP fault, no impossible header -- the run goes 103s, emits
488 KB of IR, and then dies cleanly at the bump allocator's own guard:
`cx heap: exhausted at 1610611665 + 1725 of 1610612736`, with the deck past
381 MB. So the CORRUPTION half is closed: deck overrun tramples live heap
objects, and the pointer-shaped length was trampled-header garbage, not a
layout defect. The OPEN half is consumption: bare metal compiles this same
subject inside its arena under the same 104 MB demand-lift-floor (the banked
ir_to_x86_on_fib truth is the proof), and deck-exit keeping its position is faithful
(emit-deck-exit-builtin stores r10 back to deck-pos-addr identically), so
this arm allocates deck volume bare metal does not -- by hundreds of MB.

**CLOSED 2026-08-22 by the deck census (`deck_census.py`, JUSTIFICATIONS
"deck census"). The volume half was a misread of our own harness, and the
premise above -- "bare metal compiles this same subject inside its arena
under the same 104 MB floor" -- is false.** `demand-lift-floor` is what
`ast/emit_harness.py` reserves for its ONE deck, and its own comment says it
is "a first number, not a measured one ... one region for every phase
instead of the driver's thirteen". The real driver (`opening.codex`
444-830) gives each phase its own deck and compacts between them: lex 96 MB,
parse 384 + 392, desugar 72, scope 104, **check 648**, lower 328, resolve
200, lift 104 -- about 2.3 GB of reservations, and BuildSettings records
LOWER alone using 312-315 MB of its floor on the whole compiler. Nothing
bare-metal ever compiled this subject through 104 MB of deck; the harness
crammed eight phases' decks into the lift phase's number.

The census keys every deck byte by (allocator call site, outermost
`deck-record` bracket) and shows no family growing out of proportion:

    bracket site                     deck bytes   allocs   avg   phase
    parameterize_walk_sum_ctors      49,801,752  2,075,073  24   check
    desugar_def                      48,363,576  1,496,826  32   desugar
    lower_chapter                    38,726,096    974,434  39   lower
    parameterize_walk_children       37,699,904  1,178,122  32   check
    make_end_node                    36,917,144  1,258,539  29   parse
    make_token                       30,302,596    473,478  64   lex
    ...                             381,663,332 total at exhaustion

Per-object sizes are bare metal's (tier 4: a record is fields*8 on both
arms; the one representation gap is `cx_ll_empty` at 24 bytes where bare
metal's empty literal is 16). Summed by phase, every phase sits far under
its bare-metal floor. The 381 MB is simply what eight uncompacted phases
cost on a 2.5 MB subject. Main heap at the same moment: 1.23 GB, also
spread across families at bare-metal sizes, which is why the 256 MB slack
run still exhausted the 1.5 GiB arena.

**The run completes when given room.** With the arena at 2.5 GiB and the
deck slack at 512 MB, `native/codexir` compiles the ir_to_x86 subject in 63 s,
rc 0, 13,193,485 bytes of IR, deterministic across three runs. Against the
seed's `ir_to_x86.ir` (same subject hash, decoded from CCE) the IR agrees line
for line up to def ORDER, the chapter title (`Parsmi--FibxHarness` vs
`Program`), and one type spelling: our harness prints `(record-ty
"SkipNodeText" (args))` where the seed driver prints `(ctd "SkipNodeText"
(args))` -- 930 lines of 3,822 touched, all the same three causes. That
spelling is a HARNESS-driver difference to run down (which resolve step
the seed's `emit-ir-cce` applies that `gen_codexir_harness.py` does not,
or vice versa), not finding 24.

What the crash WAS: a deck sized at 3.7x too small for the subject,
overrunning into main's live objects because the harness (by its own
admission) guessed the number -- "too small shows up as CDX9002 or a
fault, which is the honest direction to be wrong in". It did. The guard
from `e4d2fcd1` missed it because the overrun runs main-from-below (the
direction the guard does not see, and no queue item carries it -- the
pointer here named a PRIORITIES numbering that no longer exists).
The flagship commit's "capacity diverges at scale" should now read
"the hosted harness reserves one placeholder-sized deck for every phase".
Next instrument: per-allocation-path deck byte counts on a subject size
ramp. Also observed: the `e4d2fcd1` crossing guard never fired before the
slack-0 GP fault; main re-entering from below after a restore is a trample
direction it does not see.

## 25. The zig plug intercepts `deck-record` by name; bare metal gates it on the defining chapter

**Found 2026-08-21 by `findings/prim-deck.codex` on its first bare-metal run.
Ours to fix -- the plug's arm. Measured on both arms, same program.**

`deck-record` is declared as the identity function and given meaning by the
code generator, which brackets its argument in `__deck-enter`/`__deck-exit`.
Bare metal only does that when the intrinsic is ENABLED, and it gates that on
the defining chapter: `X86_64Chapter.codex:1146-1148` sets
`deck-record-intrinsic` only when `deck-record`'s chapter slug equals
`init-phase-allocator`'s. Where they differ, `deck-record` stays the identity
it is written as. ZigEmitter (`:1999`) intercepts by name alone, with no gate,
and its prose claims it does this "the same way x86-64 does it" -- which was
true once and is now stale.

A chapter that declares its own `deck-record` shows the split directly:

    assertion                       zig arm   bare metal
    deck-pos frozen in extent       yes       yes
    heap-save moves in extent       yes       NO
    deck-pos advances after         yes       NO

On bare metal nothing is bracketed, so the allocations land on the main
frontier and the deck cursor never moves. On the zig arm they land on the
deck. Same source, two different machines.

The ladder's own rungs do not show it because their slugs coincide, and the
`subj-deck-record` rename in the bundles is deliberately a pass-through on
both arms for exactly this reason. So this is latent for the ladder and live
for any subject that declares the name itself -- which is every probe we write
from here, and any depot program that does the same.

Fix is to port the gate: read `deck-record`'s defining chapter and
`init-phase-allocator`'s, and only intercept when they match. Until then the
two marked lines in `prim-deck.codex` are the standing detector.

## 32. `fail` does not fail, and `trying` does not try

**Found 2026-08-21 by `findings/probe-trying-fail.codex`, written because a
frequency pass left `fail` as the last builtin with 70 call sites and no
assertion. Ours. TWO defects, one construct.**

Reading `fail` turned up something better than a missing test: **on bare metal
it does not terminate.** `emit-fail-builtin` (`Emit/X86_64Builtins.codex:908`)
evaluates the message, DISCARDS it, stores 1 at `try-fail-flag-addr`, and
returns 0. Execution continues.

It is a signal, and the thing that reads it is Codex's retry construct:

    trying N times
      ...body...
    falling back to
      ...fallback...
    end

`emit-try-check-flag` (`Emit/X86_64.codex:1487`) reloads the flag after each
statement of the body and branches when it is set, so a failed attempt is
retried up to N times and then the fallback runs.

**The plug implements neither half.**

    fail   ->  @panic(<message>)                                  terminates
    IrTry  ->  emit-zig-act body ctx d (zig-type-is-void ty)       body only

The second is the worse one. It emits the body and **silently discards `fb`
and `fail-stmts`** -- the fallback and the failure handler are not refused, not
marked, not mentioned. They are simply absent. That is the shape this emitter
already carries a standing warning about from the `IrVecPat` defect: an
unhandled construct mapped onto a valid-but-different one, producing a wrong
program with no diagnostic.

**Measured, both arms, same program:**

    probe-trying-fail                       bare metal          zig arm
    body ran once                           printed             <no compile>
    attempt                                 printed TWICE       <no compile>
    fell back, and the program is alive     printed             <no compile>
    reached the end                         printed             <no compile>

The oracle retries the body the full 2 times, runs the fallback, and carries on
to the end. That is the whole construct working, and it is what the plug turns
into a dead program.

**And it does not even compile.** `@panic` diverges, so any statement after a
`fail` -- including everything after the enclosing `trying` block -- is
unreachable, and zig refuses with

    error: unreachable code

which names no Codex construct and is not a `@compileError` marker. Third
member of that family today, after the type-variable leak and polymorphic
`show`: the plug fails in a register the census cannot count, so the gap scores
zero in the ranking that decides what to fix first.

**Why the ladder is green with 70 `fail` sites and six `trying` blocks in the
compiler.** Not established here. The reachability column added to
`tier_coverage.py` is the tool for it, and the `address-of` precedent is
suggestive -- a construct can be everywhere in the source and nowhere in the
emitted program. Recorded as a question, not an answer.

**Not fixed.** Unlike the other findings today this is not a helper returning a
wrong number; it is an unimplemented language construct, and implementing retry
semantics in the emitter is a design change rather than a correction. The
minimum honest step is that `IrTry` should REFUSE by name when it has a
fallback or failure block it cannot emit, so the gap becomes countable. What
`fail` should compile to depends on how a plug is meant to model the flag, and
that is a question for Damian rather than a decision to take here.

## 34. The hosted harnesses never reclaim, so a 13 MB IR exhausts zigemit's 1.5 GiB arena

**Found 2026-08-22, same experiment, same arm. Ours. OPEN, harness-shaped.**

With the stack out of the way, `native/zigemit` on `ir_to_x86.ir` dies at
`cx heap: exhausted at 1610612724 + 22 of 1610612736` after 83 s and
1.23 MB of output. The ring transpile of the same IR inside the seed OS
runs `emit-all-defs` with its per-function `__heap-restore` and finishes
inside a 3072 MB guest; `ZigEmitHosted` and `CodexIrHarness` both cite the
compiler's functions but drop the driver's reclaim discipline, and
`codexir.zig` / `zigemit.zig` each contain exactly one `cx_heap_restore`
-- the definition (finding 24 established this for codexir). The arena is
a lazily-faulted reservation since `c7feba61`, so raising `cx_heap_reserve`
is free of resident cost and is the cheap way to lift this; the honest
way is for the hosted harnesses to bracket per def the way the driver
does. The cheap way is the one that shipped: PR 77 carried the zig
one-heap with the emit deck's flat term at 24 to 28 MB, and Update 50
absorbed it. The honest way is still unbuilt and no queue item carries
it.

## 36. The python plug's TCO matches a self-call by NAME, so a partial or over-application in tail position loops instead of applying

**Found 2026-08-24 by source reading, while implementing the same
transformation for the zig plug (finding 33). THEIRS. SOURCE-READ ONLY.**

**RE-FRAMED 2026-08-26, and the original framing was WRONG.** The
Cobblestone compiler lane answered PR 87's question with seven compiled
arms, and we verified the load-bearing part ourselves: **bare metal's
gate is arity-blind in exactly the same way.** `is-self-call`
(`Emit/X86_64.codex:75-80`) walks the apply spine and answers True on
reaching an `IrName` equal to the definition's name; it never counts
arguments. `has-tail-call` (`:82-90`) routes `IrApply` straight into it,
and `should-tco` (`:108-111`) adds only `params > 0`.

So the python plug is not diverging from the reference implementation.
**It is faithfully copying it.** This finding as filed says the python
plug got something wrong that C# or bare metal got right, and that is not
what is happening.

**And the defect cannot fire on compiler output.** A definition cannot
tail-call itself at non-full arity in a well-typed program: for return
type R the body would need `R = (remaining params) -> R`, an infinite
type. Six of their seven arms refuse (CDX2001, or CDX2010 *Infinite type*
by name where the return type is inferred); the seventh compiles and is
not the shape -- one parameter, one argument, a FULL-arity self call
whose result happens to be a function. The exclusion happens in the TYPE
CHECKER, one stage before the pass.

**What survives is a TRUST-MODEL finding, and it is worth more than the
original.** The wire's grammar CAN express a partial self-application in
tail position -- application is curried, one argument per node
(`IRTextEmitter.codex:382`), a saturated call and a partial application
are the same spine shape, and nothing marks saturation. The plug-side
parser accepts it structurally with no arity check
(`plugs/common/IRTextParser.codex:705`, verified). A plug fed
hand-authored or third-party IR text is protected by NOTHING in the plug.
Every plug's TCO gate is safe by an invariant that lives somewhere else,
and no plug says so.

**The lesson that generalises past this row:** reading bare metal's pass
as the reference tells you what the pass does, not what makes it safe.
This gate is correct only because of an upstream invariant it does not
state and does not check. Copying the pass copies the hole.

`codex/plugs/python/PythonEmitter.codex`, Section: Tail Call
Optimization. `is-self-call` collects the apply chain and compares the
ROOT's name to the definition's name:

    is-self-call-root (e) (func-name) =
     when e
      is IrName (n) (ty) (sp) -> n == func-name
      is otherwise -> False

Nothing compares `list-length (chain.args)` against
`list-length (d.params)`. `emit-py-tco-jump` then evaluates one
temporary per ARGUMENT and `emit-py-tco-assign` assigns one parameter
per PARAMETER:

    emit-py-tco-temps  args   -> _tco_0 .. _tco_{nargs-1}
    emit-py-tco-assign params -> p_0 = _tco_0 .. p_{nparams-1} = _tco_{nparams-1}

So the two loops agree only when a self-call is applied at exactly full
arity, and codex applies partially by design -- "a 4-argument function
called with 2 yields something callable with the remaining 2" is the
zig emitter's own description of the language.

**Under-application** (`f a` in tail position, where `f` takes three):
the assign loop reads `_tco_1` and `_tco_2`, which this iteration never
bound. On the FIRST iteration that is a NameError. On any later one it
is worse: python function locals persist across the `while` body, so
`_tco_1` still holds the previous iteration's value and the loop
continues with a stale argument and no diagnostic at all. The program
was supposed to return a closure and instead loops.

**Over-application** (`f a b c` where `f` takes two, returning a
function): `(f a b) c` is an apply of the RESULT. The jump assigns the
two parameters, evaluates `_tco_2` for its side effects, drops it, and
continues -- the outer application disappears silently.

Both directions are wrong answers rather than crashes, which is the
shape worth the register entry. The fix is one clause in `is-self-call`
or in `should-tco`: a self-call is a tail call only at full arity;
anything else falls through to `emit-py-normal-def` and stays an
ordinary call, which is correct however it is applied.

Reproducer to run before filing (not yet run):

    Chapter: ProbePyTcoArity

    Section: Shapes

      add3 : Integer, Integer, Integer -> Integer
      add3 (a) (b) (c) = a + b + c

      pick : Integer -> (Integer, Integer -> Integer)
      pick (n) = if n == 0 then add3 1 else pick (n - 1)

      opening : [Console] Nothing = act
        print-line-uni (show ((pick 3) 2 3))
      end

`pick` is one-parameter and its tail position holds a self-call at full
arity, so it is TCO'd correctly; the interesting case is a definition
whose tail position applies ITSELF undersaturated. Shape that second
probe against the emitted python -- read
`emit-py-tco-jump`'s output directly rather than inferring from the
answer, since the stale-temporary path produces a plausible number.

The zig plug takes the other choice: `zig-tail-self-call` requires
`list-length (chain.args) == tail-arity`, so an under- or
over-application is not a tail call and emits `return <expr>;`
unchanged.

**Confidence: MEDIUM.** The source reading is unambiguous -- the two
loops are keyed on different lengths and nothing reconciles them -- but
no python arm has been run, so whether any real program reaches the
shape is unknown, and the stale-temporary path is reasoned from python's
scoping rather than observed. Run the reproducer before filing
upstream.

## 61. OURS. A generic function whose type parameter appears ONLY in its return type is called with no type argument, though the IR carries the instantiation

**REPORTED UPSTREAM: issue 94 section 4 -- included as OURS and already fixed, as evidence about where the wire is thin rather than as a request.**

**Found 2026-08-27**, when finding 59 cleared `hamt-test` and `kvstore-test`
to `clean` and they then failed the zig build. **This is the next gap, not a
regression** -- both were `markers` before and had never been built.

    fn hamt_empty(comptime T58: type) HamtMap(T58)                emitted
    hamt_empty()                                                  called
    zig: error: expected 1 argument(s), found 0

    fn hamt_set(comptime T65: type, m: HamtMap(T65), ...)         emitted
    hamt_set(i64, m0, "...", 42)                                  called -- CORRECT

**The emitter already threads type arguments, and the rule it uses is the
defect.** It derives them from the VALUE arguments: `hamt-set` takes an
`m : HamtMap(T)` and a `value : T`, so `T` is readable off the call. `hamt-empty`
takes nothing at all -- its type parameter appears only in the RETURN type --
so there is nothing to read and it emits none.

**The answer is on the wire and is not being asked for.** At the call site the
IR types `hamt-empty` as `(ctd "HamtMap" (args int-default))`, fully
instantiated. The instantiation is not missing; the emitter derives it from
the wrong place.

**This is the smallest concrete piece of the monomorphisation item, and it
argues for the comptime direction.** No specialisation engine is needed for
it: read the call site's own instantiated type and pass it. It is also the
case that a specialisation engine would find hardest, because there is no
argument to specialise ON.

## 65a. The finding 65 fix WORKS on plain classes and ADDS A MARKER on a superclass chain -- NOT READY TO SHIP

**REPORTED UPSTREAM: issue 94, "Leads, explicitly not findings" -- sent as a LEAD, with the superclass failure stated as a failure and the fix explicitly not offered.**

**Built and measured 2026-08-27 21:01, against the pre-fix baseline taken the
same hour.**

**The claim held, exactly as pre-registered.** The instrument's one-respect
pair moved the way it had to and its control did not:

    Tellable-dict-Integer   (tvar 289) -> int-default     the head type now reaches it
    Tellable-dict-Boolean   boolean    -> boolean         unchanged
    Showable-dict-Integer   (tvar 511) -> int-default
    Showable-dict-Boolean   boolean    -> boolean

**The narrow falsifier held too.** Nothing with a compound head acquired a
declared type: no `*-dict-List` exists and `to-text-List` still carries its own
free variable. The fix fired only where it can prove the head.

**But `typeclass-poly` GAINED A MARKER**, and that is disqualifying on its own:

    unresolved type variable T319 of Sortable-dict-Integer      NEW
    Equatable-dict-Integer  (tvar 298) -> (tvar 297)   still free
    Sortable-dict-Integer   (tvar 298) -> (tvar 319)   still free

**The differentiator is a SUPERCLASS.** `typeclass-poly` is the only one of the
three that has one -- `class Equatable a => Sortable` -- so its dictionary
carries a `__super-Equatable` field pointing at another dictionary. Neither
dictionary in that chain takes the declared type, and the emitter now names one
of them in a refusal it did not make before.

**Not shipped, and not in the second PR.** The programs were already red so no
verdict regressed, but a change that adds a refusal is a regression in refusal
terms, and today's own rule is that an unexplained mover outranks the wins.

**What is NOT yet known**, and it is being left as a question rather than a
guess at the end of a long session: why a superclass chain declines the
declared type, and whether the `args` on those dictionaries mean the dict type
has a parameter the instance count says it should not have. Reasoning about
this construct has been wrong twice today; the next step is to read the
synthesised `EquatableDict` type definition against `count-class-instances`,
not to adjust the fix and rebuild.

## 68. A `let` bound to an immediately-applied lambda chain records the LAMBDA'S type, not the application's result, so the IR contradicts itself

**BOTH ARMS, so the rungs cannot see it.** Update 53, pin `u53-rebank` at
`58b08c38`, length ZERO -- no local patch under this.

`codex/test/roc-fold-sum.codex:51` applies a lambda to three arguments:

    let total = (\xs base step -> fold-loop xs base step 0) [1, 2, 3, 4] 0 (\acc x -> acc + x)

`total` is an Integer. The IR binds it as a three-argument function:

    (let "total" (fn (list int-default) (fn int-default
                   (fn (fn int-default (fn int-default int-default)) int-default))) ...)

and then reads it back at the use site as `int-default`
(`(name "total" int-default)` under `show`). **One binding, two types.** The
binding carries the type of the LAMBDA; the use site carries the type of the
APPLICATION, which is the correct one.

**Bare metal says the same thing, which is what makes it the compiler's.**
`run_seed_probe.sh` on the same chapter, seed `B066CEB5`: the seed's own
IR-CCE wire binds `total` to the identical function type and uses it as
`int-default`. So this is not our plug rendering the type checker wrong --
`native/codexir` and the seed agree, and they agree on something
self-contradictory.

**Why the ladder stayed green over it.** A defect BOTH arms share is invisible
to a byte-identity comparison, which is what fourteen rungs are. It surfaces
only when the emitted zig is actually built: `zig build-exe` rejects
`expected type 'i64', found 'CxFn3(...)'` because the plug faithfully emitted
what the IR said. The corpus builds; the rungs compare. This is the case that
distinguishes them.

**The site is `lower-apply-lambda-chain`** (`codex/compiler/IR/Lowering.codex`),
which Update 53 changed under COMPILER-32 step 3:

    -   in let fn-ty = build-curried-fun-ty arg-irs 0 n ty
    +   in let want = expected-or-recorded-ty ty ctx sp
    +   in let fn-ty = build-curried-fun-ty arg-irs 0 n want
    -   in apply-chain-fold func-ir arg-irs 0 n (ir-expr-type func-ir) ty sp
    +   in apply-chain-fold func-ir arg-irs 0 n (ir-expr-type func-ir) want sp

At a `let` with no annotation `ty` is the no-expectation sentinel, so `want` is
now whatever the checker recorded at `sp` -- and the value flowing into the
binding is the lambda's type rather than the result of applying it.

**Reach: three corpus programs**, `roc-fold-sum`, `roc-fold-count`,
`roc-fold-product`, all the same shape.

**NOT YET ESTABLISHED: whether Update 53 introduced this.** The corpus baseline
(census 2026-08-27) was measured on natives built from `a961dcb6`, a branch
rather than a release, so the `markers -> refused` transition crosses a base
change and is not clean evidence on its own. What needs no baseline is the
observation above: the seed's wire contradicts itself today. Settling the
"since when" wants one bare-metal probe at the Update 52 seed.

## 67. OURS. `zig-prelude-decls` is documented as the union over the whole prelude and covers 22 of its 96 declarations, so a program declaring `cx-print` will not compile

**FIXED AND SENT: [PR 98](https://github.com/damiant3/Cobblestone/pull/98), branch `zig-tree-shaking`, backlog row `plugs-backlog.md` 2.02, `Ladder: u52-shake-578`.** Both probes are back in the tier set and green. Stays live here until absorbed.

**Reproduced on both arms.** `findings/probe-prelude-collide.codex`, run
`20260828T192913Z-shake-on-corpus`:

    bare metal   runs, 7 lines banked, all correct
    zig          error: duplicate struct member name 'cx_print'
                 error: duplicate struct member name 'cx_new'
                 error: duplicate struct member name 'cx_concat'

Zig forbids two container-level declarations with one name. The prelude
declares 96, and `zig-sanitize` renames a program's name only when it appears
in `zig-prelude-decls`:

      zig-sanitize (name) = ... if is-zig-prelude-decl s then s & "_" ...

That list has 101 entries and covers **22** of the 96 declarations, **and not
one of them is a function**. The 96 are 74 `fn` and 22 `const`/`var`; the
reserved list holds exactly those 22 const/var globals, and its other 79
entries are prelude LOCALS and parameters (`a`, `i`, `buf`). `main` and
`cx_entry` are in it but are not prelude declarations at all -- `zig-main`
emits them into the PROGRAM region. So the coverage of the prelude's own
functions is zero, and any Codex program with a top-level named `cx-print`,
`cx-new`, `cx-concat`, `cx-text-eq` or 70 others fails to transpile.

**AND FIVE OF THE 74 ARE CAMELCASE, WHICH IS WHAT MAKES THIS MORE THAN A
CURIOSITY.** 69 are `cx_`-prefixed, and `cx-` is effectively the plug's
namespace -- a Codex author has little reason to enter it, which is why zero
of the 578 corpus programs collide. The other five are `CxList` and
`CxFn1`..`CxFn4`, the comptime type constructors, and Codex type names ARE
CamelCase. `CxList` is a name a real program could pick without any sense of
trespassing. Confirmed with a second probe, `probe-cxlist.codex`, which
declares `CxList` and `CxFn1` as record types:

    bare metal   runs, 3 lines banked, all correct
    zig          error: duplicate struct member name 'CxList'
                 error: duplicate struct member name 'CxFn1'

**The cause is in the deriving script, not in anybody's judgement.**
`build/check-zig-prelude-surface.ps1` derives the reserved surface from
emitted output by reading `const NAME`, `var NAME`, `|capture|` and function
PARAMETERS -- and never the function's own name:

      [regex]::Matches($line, '\bfn\s+[A-Za-z_][A-Za-z0-9_]*\s*\(([^)]*)\)')
          foreach ($p in $m.Groups[1].Value -split ',') { ... }

It reads past `fn NAME` to get at the parameter list and drops the name on the
way. So it has been printing `OK: every derived name is reserved` over a
surface missing three quarters of the declarations, and the emitter's own
prose -- "The list is the UNION over the whole prelude and stays that way" --
describes something that has never been true.

**THE FIRST VERSION OF THIS PROBE PASSED, AND THAT IS WORTH RECORDING.** It
declared `cx-print` and `cx-new`, called each once, and came out byte-identical
on both arms: `inline-leaf-calls` and `inline-single-caller` had removed both
before the emitter ever saw them (`CDX4030` says so in the diagnostics). Two
call sites and a non-leaf body is what makes the definitions survive to
emission. A probe the optimiser deletes tests nothing.

**The fix is small and MEASURED BYTE-NEUTRAL.** Add the 74 function names to
`zig-prelude-decls` and teach the surface script to derive `fn NAME`. Adding a
name changes emission only for a program that declares it, and **zero of the
578 transpiled corpus programs declare any of the 74** -- checked against the
program region of every emitted `.zig`. So the change is verifiable against a
byte-identity sweep, and the programs it does affect currently do not compile
at all.

Not in the tier set: it kills the zig arm on purpose, so it sits in `EXCLUDED`
until the fix lands, then rejoins.

## 66. The recursive structural-eq helper is synthesised BELOW the IR, so exactly one backend has it

**Found 2026-08-28. CORRECTED the same day after a cold read; the first
version had the fact right and the cause wrong, and the cause is the useful
half.** Probe `findings/probe-recursive-eq.codex`, in the tier SET, its two
disagreeing rows admitted in `EXPECTED.txt`.

    row                          bare metal   zig plug
    equal shape, two objects     yes          no      <-- disagrees
    different shape              no           no
    a value compared to itself   yes          yes
    equal shape, nested          yes          no      <-- disagrees
    different shape, nested      no           no

Zig arm measured from `probe-recursive-eq.zig` (emits `(a_ == b_)`) built and
run; `__eq_Tree` appears exactly once in the bare-metal CDX map.

**THE CAUSE, and it is a fix-location argument.** Codex has TWO structural
equality mechanisms and they sit on opposite sides of the IR:

- `deriving Eq` synthesises a source-level `__eq_<T>` in the DESUGARER
  (`Ast/Desugarer.codex:663`, `:765-777`), and `lower-eq-dispatch`
  (`IR/Lowering.codex:646-656`) rewrites `==` into a call to it **in the IR**.
  Above the wire, so **every plug in the fleet inherits it for free.**
- The recursive-sum helper is synthesised in the BACK END
  (`Emit/X86_64.codex:2911`, `:3062`, `:3257-3271`, appended by
  `X86_64Chapter.codex:1150`), **below the wire.** Only x86-64 has it.

`grep -rl "eq-sum-is-recursive\|__eq_" codex/plugs/` returns nothing. So the
plug cannot see it, and **this is not a zig problem**: their own
`codex/test/recursive-eq.no-cross` says *"structural == on a recursive variant
is synthesised by the x86-64 emitter only (COMPILER-24); arm64 answers ne where
eq is expected, riscv unmeasured."* Two of their backends are already wrong.

**Hoisting the recursive synthesis into lowering, where `deriving Eq` already
lives, fixes zig, arm64 and riscv in one place.** That is the ask.

**WHAT THE FIRST VERSION GOT WRONG.** It said "bare metal compares by contents;
the zig plug compares by identity". **Bare metal does NOT compare a plain
record by contents.** `emit-eq-op` falls through to `emit-comparison`
(`X86_64.codex:2927`, `:3300-3308`), a raw register compare, and the source
says so on purpose: *"It answers True for records, lists and sums on purpose.
`emit-eq-op`'s fallthrough compares those by POINTER and means to."* There is
no large invisible population of silent wrong answers, which the first version
claimed. The zig plug has four sum representations
(`ZigEmitter.codex:1383-1394`) and only one of them is silent:

    sum shape                zig type        zig ==          bare metal      verdict
    generic (tparams > 0)    union(enum)     compile error   structural      LOUD
    all-nullary              enum            correct tag     emit-sum-tag-eq AGREE
    self-recursive           *NameS ptr      identity        __eq_<Sum>      FINDING 66
    non-recursive + payload  union(enum)     compile error   emit-sum-full-eq LOUD

**Also corrected: Update 52 did not open this path.** The helper landed in
`3942e362` (PR 93's absorb); `git diff 3942e362 968d4600 -- codex/compiler/Emit/`
is two lines. Update 52 is where we happened to look.

**Not filed as a defect against them** -- closing the zig side is ours. The
fix-location argument goes to them, because it is worth more than our half.

Related: finding 10 (records are pointers), finding 42 (the other silent wrong
answer), [[reference_csharp_plug_is_gold_standard]].

## 65. An instance's HEAD TYPE names the dictionary it synthesises and never types it, so the dictionary's type argument is whatever the METHOD BODIES happen to pin

**REPORTED UPSTREAM: issue 94 section 2 -- the second leg of the argument, MEASURED. The fix is not offered there; see 65a for why.**

**Found 2026-08-27 by instrument, after reasoning about the same code was
wrong once** (finding 64). Blocks `typeclass-smoke` and `typeclass-poly`, and
is half of `lang-smoke`.

**The source, and it is explicit.** `synth-instance-defs`
(`Ast/Desugarer.codex`) reads the head type and uses it for the NAME only:

    in let type-name = token-text (id.type-name)
    in let def-name = make-name (class-name & "-dict-" & type-name)
    ...
    in let def = deck-record (ADef {
     name = def-name,
     params = [],
     declared-type = [],          <-- the head type reaches the name, not this
     body = body,

With no declared type, the dictionary's type argument is inferred from its
record body alone -- so it is pinned by whatever the METHOD BODIES constrain
and by nothing else. `instance Showable Integer` asserts the type and the
synthesised definition does not carry the assertion.

**The instrument: `findings/probe-instance-head-type.codex`**, a one-respect
pair. Same class, same arity, same return type; the ONLY difference is whether
the method body uses its parameter in a way that pins it.

    instance Tellable Integer   tell (x) = "int"                  ignores it
    instance Tellable Boolean   tell (b) = if b then ... else ... branches on it

    Tellable-dict-Integer    args (tvar 289)     FREE
    Tellable-dict-Boolean    args boolean        CONCRETE

**If the head type reached the dictionary both would be concrete.** Only the
one whose body pins it is.

**It explains every instance in `typeclass-smoke` without exception**, which is
what raised it:

    Showable Integer        to-text (x) = show x                 show is polymorphic  -> FREE
    Showable Boolean        to-text (b) = if b then ...          pins Boolean         -> CONCRETE
    Showable (List Integer) to-text (xs) = ... list-length xs    list-length is poly  -> FREE
    Equatable Integer       is-equal (x) (y) = x == y            == does not pin      -> FREE

**A NOTE ON THE PROBE, because the first version answered nothing.** Calling
the class method directly at each type resolves to the specialised method and
never builds a dictionary -- the wire had no `Tellable-dict-*` in it at all. A
CONSTRAINED generic function (`announce : Tellable a => a -> Text`) is required
to force one. Recorded in the probe's own prose.

**THE FIX IS TWO FIXES, and measuring said so where writing the obvious line
would not have.** A compound head's argument is discarded AT PARSE TIME, by a
function that says so in its own name:

    parse-instance-type-head (st) =
     if is-left-paren (current-kind st)
      then let st1 = advance st
       in (current st1, skip-to-close-paren (advance st1) 1)
     else (current st, advance st)

For `instance Showable (List Integer)` it returns the **`List` token** and
`skip-to-close-paren`s the rest. `Integer` is gone before the desugarer runs,
and `InstanceDef` could not hold it regardless:

    InstanceDef = record { class-name : Token, type-name : Token, methods : ... }

`type-name` is a single TOKEN. The def name `to-text-List` on the wire is that
token and nothing else.

So:

- **SIMPLE heads** (`instance Showable Integer`) are fixable where finding 65
  says: give the synthesised definition a `declared-type` of
  `<Class>Dict <type-name>`, which is in hand two lines above.
- **COMPOUND heads** (`instance Showable (List Integer)`) cannot be, because
  the CST never carried the argument. Fixing those means `InstanceDef.type-name`
  becoming a type EXPRESSION rather than a token, and
  `parse-instance-type-head` keeping what it currently skips.

**That second half is COMPILER-30's shape exactly** -- a CST node too weak to
carry what the source plainly says, so a fact the programmer wrote down cannot
reach the code that needs it. COMPILER-30 was `LambdaExpr` with no span; this
is `InstanceDef` with a token where a type belongs.

Neither is attempted here. The simple half is a small change with a measurable
target; the compound half is a parser and node change and should be argued
before it is written.

## 64. WITHDRAWN AS DIAGNOSED, and re-stated: an instance DICTIONARY's type argument is never instantiated, and the method lambda's parameter is a symptom

**The first version of this entry said this was COMPILER-30's second site and
that `token-span (m.name)` fixed it. BUILT 2026-08-27 and IT DOES NOT.** The
claim was also sent upstream before it was built, and has been corrected there.

    typeclass-smoke  __lam_1 x  (tvar 16)   predicted int-default, UNCHANGED
    typeclass-smoke  __lam_2 b  (tvar 16)   predicted boolean,     UNCHANGED
    markers          unchanged; both programs still red

**Why the span was never the blocker.** COMPILER-30's arm fires only when the
context supplies NO expectation -- `lower-let` handing down `ErrorTy`. A method
lambda is a record FIELD VALUE, and the field has a declared type:

    (rec-def "ShowableDict" (tparams "a")
      (fields (rec-field "to-text-impl" (a-fun (a-named "a") (a-named "Text")))))

so the expectation is `a -> Text`, the arm never fires, and the span it would
have used is irrelevant. The parameter peels from the field type, and its `a`
is the dictionary's own type argument.

**Which is where the defect actually is.** `Showable-dict-Integer` is typed
`(record-ty "ShowableDict" (args (tvar 511)))` while `Showable-dict-Boolean` is
`(args boolean)` -- **the instance's type argument is instantiated for one
instance and not the other**, and the unit contains no `forall` quantifiers, so
`tvar 511` is bound nowhere. Every type variable in those lambdas is downstream
of that.

**The change is NOT inert, which is its own warning.** It moved variable
numbering -- `__lam_1`'s body went `(tvar 516)` to `(tvar 511)`, `to-text-List`
swapped two -- without moving any parameter cell. A change that perturbs
unification while fixing nothing is worse than one that does nothing, because
it looks like progress in a diff.

**Still open and now correctly scoped:** why one instance instantiates its
dictionary and its sibling does not. That is the question to instrument, and
reasoning about it has now been wrong once.

**The `ForExpr` `map-list` lambda is the ONLY remaining synthetic-span site.**
The instance-method site is not one -- its lambda has an expectation, so the
span cannot help it.



**Found 2026-08-27 evening, doing the separation Steve asked for.** Blocks
`typeclass-smoke` and `typeclass-poly`. **It is not an unconstrained type; it
is COMPILER-30 in a second place**, and it is a site PR 93 deliberately
excluded.

PR 93's own commit says it: *"Two compiler-generated lambdas still desugar to
synthetic-span and are NOT in this commit, because the matrix does not measure
them."* One of the two is `Desugarer.codex:1455`:

    in let field-val = if list-length params == 0 then lam-body
     else deck-record (ALambdaExpr params lam-body synthetic-span)

**Measured now.** `typeclass-smoke`'s method lambda disagrees with itself
inside one node:

    (def "__lam_2" (params (param "b" (tvar 16))) (fn (tvar 16) text)
      (if (name "b" boolean) ...))

parameter cell `tvar 16`, body `boolean`. That is H2's case c exactly, one
construct over. `__lam_1` is worse -- `x` is `tvar 16` in the parameter list
and `tvar 516` in the body, inside a dictionary typed `tvar 511` -- and **the
unit contains no `forall` quantifiers at all**, so every one of those variables
is unbound by construction, which is what the emitter reports.

**The asymmetry that proves it is not honest polymorphism:**

    (def "Showable-dict-Boolean" ... (record-ty "ShowableDict" (args boolean)))
    (def "Showable-dict-Integer" ... (record-ty "ShowableDict" (args (tvar 511))))

A dictionary NAMED `-Integer`, typed with a free variable, beside a Boolean
sibling that is concrete.

**Fixed on the branch** (`406ae2f9`) by passing `token-span (m.name)`, which
was available all along.

**Predicted, and NOT yet measured:** this should give the method lambdas'
parameters their real types. Whether it also fixes the DICTIONARY's own type
argument (`args (tvar 511)`) is a separate question -- that is the record
type's argument, not the lambda's -- and if the dict stays free after this,
that is a third thing and wants its own finding rather than being folded in.

**The lesson for the exclusion rule.** "Not measured, so not in this commit"
was the right call for PR 93 and it should not become "not measured, so it
does not matter". The excluded site was two programs, and it took one evening
to find them. `Desugarer.codex:78` -- `ForExpr`'s `map-list` lambda -- is the
remaining one, still unmeasured, still excluded, and now on notice.

## 63. OURS, and PRE-EXISTING. The discard rule checks the wrong SCOPE: `zig-occurs body n` sees the continuation, and zig sees the whole function

**CORRECTED 2026-08-27 after steps 1 and 2. The first version of this entry
blamed emitter inlining and an `IrApply`, and both halves were wrong.** The
correction is the finding.

**Step 2 -- where the inlining happens: THE COMPILER, not the emitter.**
`ident2` is not on the wire at all. `called-twice` lowers to

    (let "a" (list int-default) (name "x" (list int-default))
     (let "b" (list int-default) (name "x" (list int-default))
      (apply (apply (name "list-at" ...) (name "a" ...)) (int-lit 0) ...)))

so `let a = ident2 x` is already `let a = x`. **`zig-let-discard` therefore
sees an `IrName`, not an `IrApply`, and the predicate SHOULD have fired.**

**Why it did not, and this is the actual defect.** The rule is
`zig-name-is-local ctx n & zig-occurs body n`, and `body` is the let's
CONTINUATION -- the code after the binding. Here the continuation reads `a`,
not `x`, so `zig-occurs` answers False and the discard is kept. But `x` is read
at `const a = x;`, which comes BEFORE the discard. **Zig's "read elsewhere" is
the whole enclosing function; ours is everything after this point.** The rule
is right and its scope is wrong.

So this is not a separate finding from 60 after all. It is finding 60's rule
with a scope that happens to agree with zig's whenever the earlier use is
absent, which is most of the time.

**Step 1 -- how often it bites: ONCE, in 595 emitted programs.** Scanning
every emitted `.zig` for `_ = <ident>;` where the identifier is genuinely READ
elsewhere on the same line (excluding declarations and the discard itself)
finds four sites in two files. Three are `_ = _ctx2;` in `par-nested`, which
refuses for an unrelated and pre-existing reason
(`expected type 'i64', found 'CxFn1(void,i64)'`) and never reaches a discard
error. The fourth is `roc-list-called-twice`, the port written to probe this.

**So the honest sizing is: one program, and it is one we wrote.** The pattern
needs an unused binding whose value is a name that was read EARLIER, which the
depot's own corpus produces nowhere. Roc's aliasing cluster produces it
readily -- case 20 is exactly that shape -- so it will recur as ports land, but
it is not blocking anything today.

**What a fix would need**, if it is ever worth doing: the enclosing
definition's body at the discard site, so the occurrence check can use zig's
scope instead of the continuation. `emit-zig-def` has it; threading it through
would touch `ZigCtx`. **That is a bigger change than the defect currently
justifies**, and the earlier plan -- test the emitted STRING rather than the
tree -- is now known to be solving the wrong problem, since the node was an
`IrName` all along.

## 62. The `is not declared at this site` marker covers TWO causes, and only one of them is finding 59

**REPORTED UPSTREAM: issue 94, "The question we cannot answer from outside" -- this entry is the evidence that a marker string cannot attribute a cause, which is why that section asks for a wire distinction rather than a patch.**

**Recorded 2026-08-27 because a prediction was wrong**, and the wrongness was
the useful part: `list-test` was predicted to clear with `hamt-test` and
`kvstore-test` and did not. All three carried the same marker text. The causes
are different and the marker cannot tell them apart.

**Cause A -- a FOREIGN variable where an in-scope answer exists.** `hamt-test`:
the definition is `forall 70`, the element is `tvar 70`, and the literal's
element-type slot said `tvar 25`, which the unit binds nowhere. That is
finding 59 and it is fixed.

**Cause B -- an HONESTLY unconstrained variable.** `list-test`:
`cl-is-empty (cl-nil)` on an empty cons-list constant. Nothing in the program
ever determines the element type, because `is-empty` does not look at an
element. There is no in-scope answer to prefer, because there is no answer at
all.

Cause B is case g of the H2 matrix again, and the same question the zig plug
faces for `\k -> 1`: what does a backend emit for a type the program genuinely
does not constrain? Any type is correct. Refusing is honest. Choosing one is a
DEFAULTING RULE and it needs to be decided deliberately rather than fallen
into.

**The lesson for the queue: classify by CAUSE, never by marker text.** The
scoping pass that produced the nine-program estimate grouped by message, and
that is why one of the three predicted programs did not move.

## 60. OURS. An unused `let` emits a discard that zig refuses when the discarded name is also read elsewhere

**THE RULE, MEASURED against zig 0.16 rather than inferred from one error
message -- and the inference was wrong twice before this table existed:**

    const x = 7; _ = x;             compiles
    const x = 7; _ = x; use(x);     error: pointless discard of local constant
    fn f(n) { _ = n; }              compiles
    fn f(n) { _ = n; use(n); }      error: pointless discard of function parameter
    fn f(n) { }                     error: unused function parameter

**The discard is an error exactly when the name is ALSO read elsewhere**, and
that holds for locals and parameters alike. It is not about being a local, and
it is not two opposing rules; it is one rule. Both earlier readings of it were
wrong and both shipped into a build.

**Three attempts, and what each one broke:**

1. **any `IrName`** -- dropped `_ = cx_deck_enter();`. An `IrName` with arity 0
   is emitted as a CALL, so an effect vanished. `deck-bracket-contract`
   `match -> DIFFER`, a wrong answer.
2. **a local, unconditionally** -- dropped `_ = n;` where `n` was read nowhere
   else, so the parameter became unused. `const-narrow-proven`
   `match -> refused`.
3. **a local that is also read elsewhere** (`zig-name-is-local ctx n &
   zig-occurs body n`) -- the rule above.

**The cost, stated plainly: this finding unblocks ONE port and took three
builds.** What earned its keep was the checking, not the fixing -- the blast
radius that forced running 56 programs, and a five-line zig experiment that
would have settled the rule before the first attempt had it been run first.
The same lesson the canary taught this morning, already written down and not
applied.

---

### The original entry

**THE FIRST FIX WAS WRONG AND PRODUCED A WRONG ANSWER. Recorded first because
it is the more useful half of this entry.** `af119cc5` tested for `IrName` and
dropped the discard for every one. An `IrName` with arity 0 is emitted by
`emit-zig-name` as `zig-sanitize n & "()"` -- a CALL -- so the discard of an
effect was dropped:

    deck-bracket-contract   match -> DIFFER     lost `_ = cx_deck_enter();`
    const-narrow-proven     match -> refused

Measured against the `8f1b202a` tree; the u51 bank would not have shown it,
and the new bank-identity banner is what said so. **A refusal would have been
survivable. A silently wrong deck-bracket count is the exact failure this tree
exists to catch, and it shipped into a build.**

**What caught it was the blast radius, not the plan.** The pre-registration
predicted a small, explicable set of moved `.zig` files. It was 56, dominated
by `e1000-*`, `dhcp-*` and `web-mux-*` programs with no lists and no unused
lets in sight. That mismatch is what forced running all 56, and running them
is what found the wrong answer. **An unexplained blast radius is a stronger
signal than any of the wins it comes packaged with, and it should be checked
BEFORE the wins are celebrated.**

The corrected predicate is `zig-name-is-local`, which mirrors `emit-zig-name`'s
own precedence and answers True only where that function falls through to a
plain identifier.

---

### The original entry

**Found 2026-08-27 by porting Roc case 10 sequentially**, which is the whole
argument for porting a suite in its own order rather than cherry-picking the
interesting-looking cases.

    let x = [1, 2, 3] in let y = x in <body reads x, never y>

    emitted   b1: { _ = x; break :b1 ((cx_list_at(x, 0) +% ...)); }
    zig       error: pointless discard of local constant

**Why the discard exists at all, and it is not wrong to have one.** The
emitter's own prose says it: "zig refuses any unused constant or capture, and
the IR legitimately carries bindings nothing reads, so let and capture
emission checks whether the body ever names the binding and discards when it
does not." An unused binding must still SEQUENCE its value, because the value
may do work.

**What is wrong is discarding a bare name.** `_ = x;` where `x` is a local
const is an error in zig, and zig is right -- a name has nothing to sequence.
The fix is `zig-let-discard`: emit nothing for an `IrName`, discard everything
else exactly as before. Both `IrLet` arms (`emit-zig-expr` and
`emit-zig-tail`) routed through it. The `__seq` arms are deliberately
untouched, because a `__seq` let's value is a field store -- the effect the
discard exists to preserve.

**The control pair is what made it visible.** `roc-alias-original` (case 10)
and `roc-alias-list` (case 9) differ in one respect: which of two names for
the same list is read. The one reading the ALIAS passes; the one reading the
ORIGINAL, leaving the alias unread, does not. One half of a one-respect pair
failing is a much stronger signal than a lone red program, and Roc keeps
eleven more cases in that cluster.

## 59. A non-empty list literal takes its element type from the CONTEXT even when the context's type is an unbound variable and the literal's own elements are correctly typed

**Found 2026-08-27 at the keyboard, no guest**, while scoping monomorphisation.
**Blocks `hamt-test`, `kvstore-test`, `list-test` outright**, and is half of
what blocks `lang-smoke` and `typeclass-poly`; it is also one of three gaps in
the three `db-*` programs. **Same family as COMPILER-30 / PR 93, and the
FOURTH instance of the shape.**

**It is the lambda defect they already fixed, one node over.** The prose under
`lower-lambda` says a lambda "used to record the EXPECTED type it was handed,
which at a polymorphic call is the callee's declared parameter with its type
variables still in it", and `lambda-recorded-ty` was the fix. A list literal
does exactly that and has no equivalent guard.

    lower-nonempty-list (elems) (ty) (ctx) (sp) =
     let resolved = deep-resolve (ctx.ust) ty
     in let from-context = when resolved is ListTy (e) -> e is otherwise -> ErrorTy
     in let elem-ty = when from-context
        is ErrorTy -> ir-expr-type (lower-expr (list-at elems 0) ErrorTy ctx)
        is otherwise -> from-context

The elements are consulted ONLY when the context offers nothing at all. When
the context offers a type it wins unconditionally -- including when it is a
variable and the elements are concrete.

**The measurement, from `hamt-test`.** `collision-set-loop` is
`(forall 70 ...)`; every parameter is `tvar 70`. One node reads:

    (list-expr (elems (record "HamtEntry" ... (record-ty "HamtEntry" (args (tvar 70)))))
               (ctd "HamtEntry" (args (tvar 25))))

The element is typed 70, the list it is appended into is typed 70, and the
literal's own element-type slot says 25. **The IR for this unit binds only
`forall 67` and `forall 70` -- there is no `forall 25` anywhere**, so the
emitter's "type variable T25 is not declared at this site" is literally
accurate: the variable is unbound at the site that must emit it.

**The same shape with a concrete witness** is case B of
`findings/probe-ctd-subst.codex`, which was written as a control for finding
57, is not one, and was kept for this: `(list-expr (elems (int-lit 0)) (tvar
19))` -- an `int-lit` element under a variable element type.

**Two ways to fix, and the choice matters.** Where the elements are concrete,
preferring them is obviously right. Where the elements carry an IN-SCOPE
variable and the context carries an out-of-scope one -- `hamt-test` -- the
answer is not "erase the variable" but "use the one that is bound here".
`branch-recorded-ty`'s `usable-witness-ty` refuses any witness with typevars,
so it cannot be reused as-is for that case.

## 58. A list literal's element type is never recorded, so an empty list whose element type the checker resolved reaches the plug as `(list error)`

**Found 2026-08-27 at the keyboard, no guest**, diagnosing the last of the
eleven Roc ports. Blocks `roc-fold-empty` and nothing else in the corpus so
far. **Same family as COMPILER-30 / PR 93 -- a type the checker solved that
the IR does not carry -- and it is the THIRD instance of the identical
shape.**

    __lam_0  xs   (list error)          the wire
    (list-expr (elems) error)           the literal itself

The program is `(\xs base step -> fold-loop xs base step 0) [] 42 (\acc x ->
acc + x)`, and `fold-loop : List Integer, ...` declares the element type one
line down. `fold-loop`'s own parameter comes out `(list int-default)`, so the
checker unified it; the literal keeps `error`.

**Both halves of the mechanism, read at the pin.**

- `infer-list` (`Types/TypeCheckerInference.codex`) answers an empty literal
  with a FRESH TYPE VARIABLE and **never calls `record-expr-type`**, so the
  resolved answer is never filed under the literal's span.
- `lower-empty-list` (`IR/Lowering.codex`) resolves the CONTEXT's expectation
  and falls to `is otherwise -> deck-record (IrList [] ErrorTy sp)` when the
  context supplies none. The same `ErrorTy` floor as H2.

**Smaller than H2, because the span already exists.** `AListExpr` carries a
real span (`Desugarer.codex:47`, `is ListExpr (elems) (sp)`), unlike
`LambdaExpr` which carried none. So this needs no CST change: record the type
in `infer-list`, and have `lower-empty-list` ask before it falls to `ErrorTy`.

## 57. `subst-type-vars-from-arg` cannot learn a type variable from any USER-DECLARED parametric type, so a branch join keeps a variable both of its branches had resolved

**Found 2026-08-27 at the keyboard, no guest.** Blocks three of the eleven
Roc ports -- `roc-iter-map`, `roc-iter-keep-if`, `roc-iter-drop-if` -- which
all refuse with `unresolved type variable T16 of __lam_0/__lam_1`. **Same
family as COMPILER-30 / PR 93.**

**The measurement, from `roc-iter-map`'s own wire.** `range-to : Integer,
Integer -> Iter Integer` is fully monomorphic, so this is NOT
monomorphisation:

    then-branch   (name "DoneA" (ctd "Step" (args int-default)))    CONCRETE
    else-branch   (apply (name "One" ...) ... (ctd "Step" (args int-default)))  CONCRETE
    the `if`      (ctd "Step" (args (tvar 16)))                     A VARIABLE

Both branches carry the resolved answer and the join does not.

**The cause, and the machinery that should have prevented it already
exists.** `lower-if` (`IR/Lowering.codex:44`) calls `branch-recorded-ty` with
`if-witness-ty` as the witness, which is exactly this case.
`usable-witness-ty` accepts `(ctd "Step" (args int-default))` -- no error, no
typevars, and `ty-admits-widening` is False for anything that is not a bare
`IntegerTy`/`RealTy`. So the substitution IS attempted and learns nothing:

    subst-type-vars-from-arg    IR/LoweringTypes.codex:57-64
      is TypeVar   / ListTy / FunTy / TypeApply   ->  handled
      is otherwise -> target                      <-- the floor

`SumTy`, `RecordTy`, `ConstructedTy`, `LinkedListTy`, `VectorTy`, `UnitTy`
and `LinearTy` all carry type children and all land on that floor. **Every
ADT in the language is invisible to this walk.** The asymmetry is the tell:
`subst-type-var-in-target`, the APPLYING direction, uses
`codex-type-map-children` and handles all of them -- only the LEARNING
direction is blind.

**This is the compiler-side twin of finding 47**, which is the same blindness
in the zig plug's own recovery walk ("knows `List a` and `a -> b` and nothing
the subject declares").

**Reproducer: `findings/probe-ctd-subst.codex`**, case A. Its case B is NOT a
control and the probe says so -- it fails a layer earlier, its branches
themselves carrying the variable, which is a fourth thing to look at and not
evidence for this one.

## 56. WITHDRAWN ENTIRELY -- there is no soundness hole and no miscompile; `native/codexir` never reads the diagnostic bag, which is finding 49

**Settled 2026-08-26 23:5x. Nothing was wrong with any compiler.** The
type checker is correct, bare metal is correct, and the zig plug compiles
that type checker correctly. The instrument was deaf.

**The measurement, all on one tree (codex `cab52a35`), same source unit:**

    program              bare metal (seed)   native/codexir   native/codexzig
    probe-pr87-alias     CDX2001 Int vs Fun  rc=0, NONE       CDX2001 Int vs Fun
    probe-pr87-direct    CDX2001 Int vs Fun  rc=0, NONE       CDX2001 Int vs Fun
    probe-cdx2001-text   CDX2001 Int vs Text rc=0, NONE       CDX2001 Int vs Text

`codexir` and `codexzig` are **the same compiler emitted by the same
plug**, differing only in their harness. `ast/CodexZigHarness.codex`
merges the bags and halts; `ast/CodexIrHarness.codex` calls
`check-chapter`, binds `cr.state`, and contains the word "bag" **zero
times**. So the checker computed CDX2001 every time and one harness
never asked.

**That is finding 49, filed on the morning of the same day, still open,
and then used all night as an oracle.**

**The zig plug is EXONERATED, and better than that** -- `codexzig`
producing the identical code and message as the seed, for both shapes, is
positive evidence that the plug compiles the type checker correctly here.

**Three wrong attributions in one investigation, each corrected by the
next measurement:**

1. "Codex's type checker is unsound" -- refuted by their four-seed
   non-repro with a positive control.
2. "Our plug miscompiles the type checker until CDX2001 stops firing" --
   refuted by `codexzig`, which is that same miscompiled-by-hypothesis
   plug and reports the diagnostic correctly.
3. The truth: our IR harness does not consult the bag it was handed.

**The control did its job and I nearly did not run it.** `probe-pr87-direct`
is what showed the alias was never the trigger; `probe-cdx2001-text` is
what showed the shape was never the trigger either. Both were cheap and
both were written only because someone asked what would falsify the
claim.

**What this costs beyond the retraction:** every probe run tonight went
through `codexir`, and so does `corpus_run.py`. A corpus program carrying
a compiler error emits IR anyway and we then build and match its zig. See
finding 49 -- it is no longer a tidy-up, it is the integrity of the
measurement.

## 55. `emit-zig-atype` emits ANY unrecognized type name verbatim, with no scope and no refusal -- 12 programs behind one `else`

Found 2026-08-26 22:1x by chasing `queue-test`'s `use of undeclared
identifier 'a'` and landing on the same line as finding 17's
`Frequency`. **OURS**, `ZigEmitter.codex:445-447`. Not fixed.

    is ANamedType (name) (s) ->
     let mapped = zig-lookup-type zig-type-map (name.value) 0
     in if text-length mapped > 0 then mapped else zig-sanitize (name.value)

**One fallback, two findings, twelve programs.** Record fields and ctor
payloads arrive as `ATypeExpr` rather than as a resolved `CodexType`, so
they take this path and never reach `emit-zig-type`. When the name is
not in `zig-type-map` it is emitted as itself:

- `Frequency`, `Timestamp`, `Duration` -- unit families. **11 programs**,
  and this is finding 17's part B.
- `a` -- a source-level TYPE VARIABLE. **1 program**, `queue-test`:
  `Queue a = record { ... }` in `foreword/core/Queue.codex`, and the
  emitted line reads `QueueS(T52){ .front = cx_ll_empty(a), ... }`. The
  definition declares `comptime T52` and the field's element type is
  spelled `a`, in the same expression.

**This path bypasses everything built for type variables tonight.**
`emit-zig-type` takes a scope and refuses a stray variable
(`zig-stray-tvar` / `zig-tvar-scope-refusal`, findings 46 and 47).
`emit-zig-atype` takes no scope, has no refusal, and answers with the
source name. So a type variable that arrives as an `ANamedType` rather
than a `TypeVar` walks past the guard, the scope check and the marker,
and lands in the output as an undeclared zig identifier.

**Why it is loud rather than wrong:** an undeclared identifier is a zig
error, so nothing ships a wrong answer. It is also invisible to the
marker histogram that ranks emitter work, because it produces no marker
-- the same blind spot finding 17 named in 2026-08-19 and the reason its
reach was undercounted for a week.

**The fix is one `else`, and it is the same `else` for both symptoms:**
resolve the name against the unit-defs and the enclosing definition's
type parameters, and refuse with a marker when neither answers. Doing it
also lets the histogram see the class.

**Falsification attempted:** the alternative was that `a` and
`Frequency` are two different defects that happen to look alike. Refuted
by reading the path -- both are `ANamedType` whose `name.value` misses
`zig-type-map`, and both reach the same `zig-sanitize (name.value)`.
They differ only in what the name means.

## 54. The prelude's own locals shadow user top-level names, and about forty-five of the commonest identifiers are live ammunition

Found 2026-08-26 22:0x by the corpus reading pass, looking for something
unrelated to units to piggyback on a chain. **OURS**,
`codex/plugs/zig/ZigEmitter.codex`, `zig-prelude`. **Two instances
fixed; the class is NOT.**

    corpus/dns-answer-count.zig:22:11   local constant shadows declaration of 'l'
    corpus/tcp-checksum-refuse.zig:209:9  local variable shadows declaration of 'base'

Both error lines are in the PRELUDE, not in user code:

    fn cx_ll_empty(comptime T: type) *CxList(T) {
        const l = cx_gpa.create(CxList(T)) catch @panic("oom");
    fn cx_ipow(a: i64, b: i64) i64 {
        var base = a;

against user top-levels `fn l() DnsResponse` and `fn base() NetSession`.
Zig forbids a local shadowing a container-level declaration, so the
prelude's private variable names are effectively **reserved words for
every Codex program the plug compiles** -- and nothing says so.

**The plug guards user names against prelude DECLARATIONS and not
against prelude LOCALS.** `zig-prelude-decls` holds `std`, `main`,
`cx_heap_mem` and the deck globals; `zig-sanitize` appends `_` to any
codex name in it. The prelude's locals are not in that list.

**The surface is 45 names, measured** by extracting every `const`/`var`
binding from the prelude of an emitted program:

    acc al ascii b b0 base bot buf c chunk clamped code cp dot e fd frac
    i k l large_val m n neg o off out p path r raw rc s start top u v xs z
    (plus the cce_* tables)

`i`, `n`, `s`, `acc`, `buf`, `out`, `top`, `start`, `code`, `path` --
these are ordinary names for an ordinary definition. Two programs hit it
today because two programs happened to define `l` and `base`.

**MEASURED AGAIN 2026-08-26 22:32, after the rename was built, and the
first measurement was WRONG in a way the fix exposed.** Both programs
still refuse -- the error moved one line and changed kind:

    before   dns-answer-count.zig:22:11  local constant shadows declaration of 'l'
    after    dns-answer-count.zig:26:15  function parameter shadows declaration of 'l'

**The surface is 66 names, not 45.** The first extraction searched for
`const` and `var` bindings and never looked at prelude function
PARAMETERS, which shadow exactly the same way. Nineteen more names, and
they are worse than the first batch because they are the commonest
parameter names there are:

    a, alignment, bits, bytes, ctx, d, e, h, hi, len, lo, memory,
    new_len, path_cce, ra, sep, vs, x, y

`x`, `y`, `d`, `e`, `len`, `ctx`, `a`. A Codex program defining a
top-level `x` cannot be compiled by this plug.

**So the two instances are NOT fixed** and the prediction that they would
move was wrong. What the rename bought was the discovery that the class
is half again as big as filed -- the fix moved the error to the next
shadow of the same name, which is the loudest possible way to say the
first measurement was incomplete.

**The class fix is now clearly the only fix**, and it is bigger than
before: renaming 66 prelude identifiers, locals and parameters both. The
`check_*.py` guard that re-derives the surface must count parameters
too, or it will certify the same incomplete list.

**Why the whole class was not fixed tonight, stated rather than
skipped.** There are two routes and both are too big for a piggyback:

- **Add the 45 names to `zig-prelude-decls`.** Rejected on measurement,
  not taste: `zig-sanitize` has **55 call sites** covering type names,
  ctor names, parameters and definitions, so this renames `i`, `n` and
  `s` everywhere in every program -- widening exactly the rename
  machinery that produced finding 42, to buy two programs.
- **Rename all 45 prelude locals.** Correct, and confined to our own
  text since the prelude is 66 separate string literals. But it is a
  regex rewrite over 931 lines of zig embedded in Codex string
  literals, and a subtle miss breaks every emitted program rather than
  one.

The second is the real answer and it wants its own sitting, not a
piggyback. **What would make it safe:** re-derive the local list from an
emitted `.zig` after the rename and assert it is empty of unprefixed
names -- the same shape as the ladder's other `check_*.py` guards, so
the class cannot come back silently.

## 51. A refusal that replaces an EXPRESSION strands the parameters that fed it, and zig reports the stranding, never the refusal

**STATUS CONTESTED -- see "THREE ENTRIES HAVE CONTESTED STATUS" at the top of
this file. PRIORITIES recorded PR 92 as closing this; this entry disagrees;
neither has been re-checked. Do not cite either way.**


Found 2026-08-26 20:08 by `verify_emitter.sh` legs 1 and 4 on the
`f47-guard2` chain -- the first chain that ever compiled the
type-variable guard. **OURS**, `codex/plugs/zig/ZigEmitter.codex`. Not
fixed.

The guard does what item 1 asked. Case (g) of the probe matrix and the
three iterator Roc ports used to emit `use of undeclared identifier
'T16'`, a bare zig error naming no variable, no callee and no reason.
They now emit a sentence:

    fn iter_map(comptime T44: type, comptime T45: type, it: Iter(T44), transform: CxFn1(T44, T45)) Iter(T45) {
        return cx_new(IterS(T45){ .next = @compileError("zig plug: unresolved type variable T16 of __lam_0") });
    }

**Zig never prints that sentence.** The refusal consumed the only
expression that read `transform`, so the parameter went dead, and zig's
unused-parameter check runs against the signature before the
`@compileError` in the body is analysed.

**Measured, not inferred.** Zig reports a column, and the column lands on
the parameter the refusal stranded in every case:

    roc-iter-map      857:68   transform: CxFn1(T44, T45)
    roc-iter-keep-if  857:52   pred: CxFn1(T44, bool)
    roc-iter-drop-if  857:52   pred: CxFn1(T44, bool)
    probe.zig         908      wrap_int(n: i64), body is the refusal alone

Four programs, three of them Roc ports written by people who have never
seen this emitter.

**This is finding 42 arriving from the other side.** There, zig's
unused-parameter error was the only reason a silent wrong answer became
visible, and we were glad of it. Here the same check buries a message
that was correct. The check is not the defect either time; what changed
is whether we had anything to say.

**Falsification attempted:** the alternative was that the stranding is
unrelated to the refusal and the parameter was already dead. Refuted by
the column: in all three ports the named parameter is the closure the
refusal replaced, and `roc-iter-map` strands `transform` while leaving
`it` alone -- `it` still has a reader, `transform` does not.

**The fix is in the refusal, not the guard.** A definition whose body
carries a refusal must discard the parameters that refusal stranded
(`_ = transform;`), so the first thing zig analyses is the message.
`emit-zig-def` already owns the parameter list and already builds the
body, so it is the one place that can see both.

## 49. `native/codexir` emits IR for a program with compiler errors and says nothing, because its harness never consults the diagnostic bag

Found 2026-08-26 on the ladder droplet, while looking for a keyboard-cost
gate on an emitter refactor. **OURS**, `ast/CodexIrHarness.codex`. Not fixed.

**It is the sibling of the gate the cold read fixed this morning.**
`ast/CodexZigHarness.codex` was found skipping the driver's error gate
(`opening.codex:1676-1678`) and now merges four bags and halts:

    czg-bag = bag-merge-all [bag-from-list (toks.errors), doc.parse-bag,
                             rr.bag, cr.state.bag]
    if bag-has-errors czg-bag then print-text (czg-halted (bag-errors czg-bag))

`CodexIrHarness.codex` runs the same `check-chapter`, binds the same
`cr.state`, and then lowers and prints regardless. The file is 59 lines and
the words `error`, `halt` and `diag` do not appear in it.

**Measured, three runs over one 5,529-line bundle of the zig plug.** The
clean source, an undefined name, and a call with an argument deleted all
produce `rc=0`, an IR of the same size, and **zero** non-telemetry lines on
stdout. The undefined name reaches the IR as a typed node:

    (name "scopeX" (list (int 0 4294967295 ov-error) ...

**Falsification attempted.** The obvious escape is that the diagnostic rides
the IR stream rather than stdout. It does not: `CDX9002` and `undefined`
occur in the emitted IR exactly as often in the CLEAN run as in the two
broken ones -- seven and one -- because every occurrence is prose inside the
plug's own source. Nothing is reported anywhere.

**What it costs us.** `corpus_run.py` runs all 593 corpus programs through
`native/codexir` and gates only on `returncode != 0 or not stderr`, so a
program that does not compile is scored on the zig its broken IR produced.
The same blind spot in the codexzig path, once opened, showed 41 of 593
carrying compiler errors nobody had seen. **How many of the 593 this one
hides is unknown and is the first thing to measure after the fix** -- it is
not the same number, because `corpus_run` resolves cites through the fixed
`cite_resolve` and the 41 included 28 that were an artifact of that.

**Confidence: HIGH.** Source read and behaviour measured, and the fix is the
gate that already exists four files away.

**Why it is not fixed yet.** It changes what `corpus_run.py --run` reports,
and that run is the measurement PRIORITIES item 1 rests on. Moving the
instrument in the middle of reading it would confound both.


**FIXED 2026-08-26 23:5x (`7a6071d`), building as this is written.** The
gate its sibling already had, taken from ONE place rather than copied:
`BAG_MERGE`, `halt_gate()` and `halt_formatter()` now live in
`ast/emit_harness.py` and both generators call them. The zig harness
regenerates **byte-identical** (4898 bytes) after the refactor, so its
half is provably inert and the `codexzig` fixed point cannot move from
it. `check_harness_gates.py` compares both generated harnesses to each
other AND to `opening.codex`, because agreeing with each other is
necessary and not sufficient -- the `ir-emit-roots` drift is exactly the
case where both agreed and both were wrong.

**Note for whoever edits a harness next:** `ast/*Harness.codex` is
GITIGNORED. The harnesses are generated by `ast/gen_*_harness.py`, and
editing the `.codex` directly is editing the artifact. Git refused the
add, which is the only reason it was caught -- the same "I had the
artifact, not the source" shape as the whole finding.

**What it cost before it was found.** This produced a false report to
Damian's compiler lane twice in one evening (finding 56, withdrawn), and
their lane spent a four-seed refusal sweep with a positive control
telling us we were wrong. It was also used as the oracle for every probe
run that night.

**MEASURED 2026-08-27 00:05, chain `f49-gate2`, codex `cab52a35` with the
gate as the only delta. 13 corpus programs carry compiler errors.**

    before   clean 326, markers 264, unresolved 16 | match 269, no-expected 30
    after    clean 317, markers 260, unresolved 16, zigemit 13 | match 267, no-expected 23

Nine left the clean set: `quotes-gate` and `quotes-parse` were scoring
**match**, and seven had no `.expected` and so asserted nothing
(`class-op-no-instance`, `effect-launder-fork/map/record`,
`let-effectful-bug`, `mutable-alias`, `parser-resync`). **Exactly two
verdicts were contaminated.** Zero movers among the programs that stayed
-- the whole diff is nine removals.

**An independent check, free:** `codexzig`'s gate finds 13 halts on this
corpus after the morning's `cite_resolve` fix took it 41 -> 13. This
gate, in a different harness, independently finds 13. Two gates, same
number, which is the agreement that was absent all night.

**SWEEP 14/14 GREEN**, chain `f49-gate2` complete on all six legs
(natives 5m18, tvar matrix, corpus, codexzig fixed point, Roc ports
3/11 unchanged, sweep 26m). So the gate changes nothing bare metal can
see, and the `codexzig` fixed point holds -- which also confirms the
byte-identical regeneration of the zig harness after the refactor.

**Reported to PR 92** as a corrected headline (`match 183 -> 267`); the
six emitter findings' reach numbers are counted by error signature
rather than by the clean set and are unaffected.
## 48. A self-recursive type that is also GENERIC is emitted with no indirection, so zig says it contains itself

Found 2026-08-26 on the ladder droplet. **OURS**,
`codex/plugs/zig/ZigEmitter.codex`. Promoted from H3 after its falsification
test ran and it survived.

**It was MASKED, and that is how it was found.** `inductive-list` carried an
`unresolved type variable` marker until finding 47's fix resolved it, and
underneath sat this. The program never reached a build, so nothing could see
it, and the census filed it under a class it does not belong to.

**The reproducer is `findings/probe-recursive-generic.codex`**, two types
identical in shape and differing only in whether they carry a parameter:

    Nat = | Zed | Suc (Nat)
    Stack (a) = | Empty | Push (a) (Stack a)

    non-generic     const NatS = union(enum) { ... };
                    const Nat = *NatS;              <- the indirection
    generic         fn Stack(comptime a: type) type {
                      return union(enum) {
                        Push: struct { a, Stack(a) },   <- no pointer
                      }; }

    error: type 'Stack(i64)' depends on itself for field declared here

**Falsification attempted.** The test named before running it: if BOTH types
failed, the defect would be recursion handling generally rather than the
generic case, and H3 would be misnamed. `Nat` builds and answers 2. Only the
parameterised one fails. The plug HAS the machinery -- `zig-typedef-recursive`
boxes a self-recursive type and `emit-zig-ctor-apply` reads it to choose
`tname & "S"` -- and the generic emission path has no counterpart to
`const Nat = *NatS`.

**Confidence: HIGH.** Two types, one difference, one builds and one does not,
and the missing construct is visible in the output.

**Not yet established:** how many corpus programs this reaches. `inductive-list`
is one. The count is unknown because until finding 47's fix most such programs
stopped at a marker, which is the same blind spot that hid this one.

## 46. A type variable is not an answer, and taking one as an answer put `T23` in a scope that declares no such name

Found 2026-08-26 on the ladder droplet, on the first Update whose ceremony ran
the codexzig gate. **OURS**, `codex/plugs/zig/ZigEmitter.codex`, and FIXED the
same day. This is the diagnosis of the forty-seven undeclared `T38`s that
stopped Update 50, and it answers that item's own question -- *is the wire
carrying `T38`, or is the emitter writing it?* -- with the second: **the wire
is right and the emitter is wrong.**

**The whole defect is five lines of IR.** `warmups/lamtvar.codex` is thirty
lines of Codex whose two rows differ in one thing, and the IR shows why:

    map-list      : (tvar 23 -> tvar 24) -> (List (tvar 23) -> List (tvar 24))
    mapped-named  : apply (apply map-list bump)     xs   -- bump : int -> int
    mapped-lambda : apply (apply map-list __lam_0)  xs   -- xs   : List int
    __lam_0       : (params (param "x" (tvar 23))) (fn (tvar 23) int-default)

`__lam_0`'s parameter carries the type it was HANDED -- map-list's own `a`,
still a variable. That is not a compiler defect. The driver lifts lambdas
AFTER the resolve pass, and CSharpEmitter.codex states it outright above
`is-lam-def`: "a `__lam_N` def carries the expected types its lambda was
handed, not the resolved ones". C# answers `dynamic`. Zig has no `dynamic`,
so this plug has to recover the type, and it has the machinery to: it walks
each declared parameter type against the type actually supplied and answers
with what sits where the variable sits.

**The bug is the sentinel.** "Not found" was the empty string in one walk and
`VoidTy` in the other. Matching map-list's declared `(a -> b)` against
`__lam_0`'s `(tvar 23 -> Integer)` answers `a = tvar 23` -- which is neither
sentinel, so the scan **stopped there**, satisfied, and never read the list
argument one place along, whose `List a` against `List Integer` is the answer
that was wanted. The variable was then emitted as the literal text `T23` into
a caller that declares nothing of the kind:

    fn mapped_named(xs: *CxList(i64)) *CxList(i64) {
        return map_list(i64, i64, ... p0: i64 ... return bump(p0);      ... CxFn1(i64, i64) ...);
    }
    fn mapped_lambda(xs: *CxList(i64)) *CxList(i64) {
        return map_list(T23, i64, ... p0: T23 ... return __lam_0(p0);   ... CxFn1(T23, i64) ...);
    }

**The emitter had built a marker for exactly this gap and it could not fire.**
`zig-resolve-tvar` ends in `@compileError("zig plug: unresolved type variable
T<id> of <callee>")`, and the note above it explains, at length, why a marker
beats the `anyopaque` it replaced. A variable answer looked like success, so
the code path that reaches the marker was never taken. **A gap detector that
a plausible wrong answer walks past is not a detector** -- the same shape as
finding 45's advisory reservation, one register up.

**There were two mechanisms and they needed the same rule**, which is the
lesson this file has now recorded three times (`zig-renamed-scan` against
`zig-subst-all`, and the emitter's own note says "when a fix turns out to be a
scan direction, go look for the sibling mechanism"). One walk answered Text
for the type-argument list, one answered CodexType for substitution; the prose
above them claimed "the walk is shared and only the answer differs" and it was
not shared, it was copied. They are one walk now, and the fix was written once.

**And a second half, from the same root.** With `a` recovered, the emitted
`p0: T23` and `CxFn1(T23, i64)` still had to go: `emit-zig-name` handed the
lambda's raw type to `zig-closure-make` without reading it through the
enclosing call's own type bindings. And `__lam_0` is emitted GENERIC -- its
parameter really is a variable -- so `fn __lam_0(comptime T23: type, x: T23)
i64` was being called as `__lam_0(p0)`, one argument against two. The
trampoline is a call site like any other and had never applied a generic
callee. It does now, and the types come from two places: the arguments
already supplied, and the parameters the trampoline is about to take, which
the function type it stands in for is the only thing that names. That is the
seventh site of "A GENERIC NAME MUST BE APPLIED, and nothing enforces it
centrally", which the emitter's own prose predicted in as many words.

**Why nothing caught it, and this is the part worth keeping.** The IR pipeline
does not lift lambdas -- `lift-lambdas` is called by the DRIVER
(`opening.codex:1716`), not by `default-ir-pipeline`. So `native/codexir`
never produces a `__lam_N` at all, and **every runner built on the natives is
structurally blind to this**: `corpus_run.py`, `tier_run.py --zig`, and with
them the entire tier set, which stayed green through the whole failure. The
first thing to meet it was the ceremony, on a real release, through the seed.
The reproducer had to be routed through the seed for the same reason, and
`warmups/regen.sh` had to learn cite resolution before a warmup could reach a
foreword definition at all.

**Reproducer:** `./warmups/regen.sh lamtvar` then `./cycle.sh lamtvar`. Red
before the fix with one `use of undeclared identifier 'T23'` against 39,703
bytes of otherwise-fine zig; green after, and the two rows come out identical
but for the callee name, with `__lam_0(i64, p0)` applying the generic. Bare
metal answers `4` and `4` and the warmup diffs against it, so this is an
oracle match rather than an eyeball.

**Residue, not fixed here.** `zig-subst-arg-type` has no callers -- it
duplicates the resolver's substitution loop and nothing reaches it. It was
updated to keep compiling rather than deleted, because a bug fix is not the
place to remove upstream code.

## 45. The deck reservation is advisory: overrunning it is detected, printed, ignored, and then faults 200% in

Found 2026-08-25 on the ladder droplet against our fork's stack. **THEIRS**,
the emitted runtime's heap/deck machinery. Cheap to reproduce and it needs
no QEMU: the reservation is a literal in the emitted zig.

`__heap-advance N` (the harness's deck prologue, `emit_harness.deck_prologue`)
reserves N bytes of deck; the hosted tools use 512 MB. **Nothing enforces
it.** The runtime's own tracer computes the headroom and prints it going
negative on every allocation after the boundary, and no code path acts on
that number. The program keeps allocating until it walks off something and
takes a fault.

Reproduced by rebuilding `native/codexzig` with the reservation lowered --
`sed s/cx_heap_advance(536870912)/cx_heap_advance(16777216)/` on the emitted
zig, then `zig build-exe`, about ten seconds and no VM -- and feeding it
`ast/parse-subject.codex`, which wants ~68 MB:

    CX-DECK used=16574254 reserved=16777216 headroom=202962     <- last good
    CX-DECK used=18816630 reserved=16777216 headroom=-2039414   <- over
    ... 15 more traced steps, all negative ...
    CX-DECK used=33496942 reserved=16777216 headroom=-16719726  <- 200%
    General protection exception (no address available)
    cz16.zig:141:25: 0x13fbace in cx_list_at__anon_53837
        return l.items.items[@intCast(i)];

**It reaches about 200% of the reservation before dying** (33,496,942 of
16,777,216 is 199.65%, and that is the last TRACED value, not the value at
the fault -- the tracer only prints when the peak grows by a megabyte, so
every number here is a floor), and it dies in
`cx_list_at` reading past the end of a list -- a memory fault in the middle
of the compiler, not a diagnosis. A user who meets this sees a GP exception
in a list accessor and has no reason to suspect the deck.

**The good half, established by the same run:** no partial output is
produced. The emitted zig is built as one Text and printed at the end, so
the 12,931 bytes on stderr are the panic trace and contain zero lines of zig
source. The failure cannot be mistaken for a successful transpile.

**A different overrun IS guarded**, which is what makes this one a gap
rather than a policy: the ladder's own `probe-deck-overrun` tier catches the
heap-and-deck cursors meeting and says so by name -- "cx heap: the two
cursors met -- alloc at 6295544 + 64 crosses (hp=... dptr=... deck_base=...
bivy=... nest=0)". So the machinery can refuse; the reservation boundary
just is not one of the things it refuses on.

**Why it matters now.** JUSTIFICATIONS "The deck costs ~153 MB per MB of
source" measures the hosted compiler at 421 MB of its 512 MB deck on its own
2.87 MB bundle, and `passes_to_x86` at 385 MB. Every Update adds chapters.
The first Update that crosses the line will not report a deck problem -- it
will report a GP fault in `cx_list_at`, most likely during a rebank, and the
hour spent finding that is the cost of the missing check.

**Suggested fix, unattempted:** refuse in the allocator when the deck cursor
would pass the reservation, with the numbers the tracer already computes.
Hedged: we have not tried it, it is core runtime, and we can verify only the
zig arm.

## 43. No plug `run.ps1` consults the VM host selection in the config it sources, so no plug can be run on Linux

Found 2026-08-25 on the ladder droplet against `0c4327d5`, which is
`upstream/master` verbatim. **THEIRS, and not a plug defect** -- it is
how every plug reaches a VM. **SENT as PR 88** (plugs backlog 1.61,
ladder tag `plug-run-no-vm-host`). Measured, not read; the walk-through
is the essay `what-run-ps1-does-on-this-box`.

`build/vm-config.ps1:14-16` states the contract: "codex-vm (the WHP
hypervisor) is the primary and is Windows-only; QEMU is the fallback and
the only host on Linux/WSL. Both paths are live." The file implements it
-- `:21` chooses (`$script:UseCodexVm`), `:22-52` discovers a QEMU,
`:55-56` is the error for having neither.

**Nothing that runs a plug reads any of it.** Across all 56
`codex/plugs/*/run.ps1`,
`grep -lni 'qemu|UseCodexVm|Start-VmRun|FallbackVmBin'` returns nothing.
They divide three ways: 38 delegate to `build/plug-run.ps1`, which
hardcodes `tools\codex-vm.exe` (`:49`) and launches it (`:53`) with no
fallback; 8 hardcode the same path themselves (`wasm:50`, `html:46`,
`spirv:43`, `t3isa:43`, `winforms:40`, `ptx:39`, `wgsl:39`,
`evidence:117`); and 10 use `$script:CodexVmBin` from the sourced config
(`riscv:54`, `csharp:81`, `javascript:47`, `maui:65` and six more),
reading its PATH variable while skipping its CHOICE variable, which is
the worst of the three because it looks like consultation.

What a Linux user gets, run here with the built zig plug and a real IR:

    [plug-run] IR input: 1481 bytes
    [plug-run] Plug: codex/plugs/zig/build-output/zig-plug.cdx
    [plug-run] Listening on TCP 9145
    plug-run.ps1: The variable '$proc' cannot be retrieved because it
                  has not been set.
    exit 1, one second

**The diagnosis is wrong as well as the outcome.**
`$ErrorActionPreference = 'Stop'` (`:20`) makes `Start-Process` on a
missing path terminating at `:53`, so control leaves the `try` for the
`finally` at `:167` **without reaching `:59`**; there `:168`'s
`if (($proc -and (-not $proc.HasExited)))` reads a variable that was
never assigned, and `Set-StrictMode -Version Latest` (`:19`) throws on
that -- an exception in a `finally` replacing the original. Reproduced
in isolation with those four lines and nothing else. And
`vm-config.ps1:55-56`'s "no VM host" cannot fire here: its condition is
having NEITHER host, and QEMU is present.

**`build/compile.ps1` is the shape of the fix.** Same hardcoded binary
at `:209`, but `:218` is `if ($script:UseCodexVm)` -- the line the plug
scripts lack -- and `:239` falls back to `Invoke-VmCompileFallback`
(`vm-config.ps1:821`). Measured here, that leg works: `hello.codex` to
IR-CCE in four seconds, in a `qemu-system-x86_64 ... -m 3072` guest.

**The design record already contains both halves.**
`docs/Designs/Active/Build/Build.md:699` says of the non-delegating
plugs "The remaining 17 are deliberately untouched and are not a residue
to close" -- true of delegation, which is what that paragraph is about,
and orthogonal to hosting, which cuts across all three groups. Its
census reads 55 and 17 where the tree now has 56 and 18 (`evidence`).
And `:684-694` names the mechanism outright: both generated scripts
"carried defects that survived because a generator with no live target
is compiled but never compared against anything". This is another one,
and the live target it lacks is a Linux run.

**The transport is the part that is not a copy-paste, and the ladder has
a working recipe.** Under codex-vm the guest dials the host's TCP
listener; the QEMU consumers in `vm-config.ps1` read the serial wire
(`:835`), so `Invoke-VmCompileFallback` is not a template. The ladder
does what `plug-run.ps1` wants, daily: `plug_run.py` listens on 9145 and
lets the guest dial out, and `codex_vm.py:48-49` boots it with user-mode
networking (`-netdev user,id=net0 -device
ne2k_isa,netdev=net0,irq=9,iobase=0x300,mac=52:54:00:12:34:56`).

**The ask sent with it is one ruling:** is Linux a supported host for
RUNNING plugs, or only for building them? Either answer is a small
change, and they are different changes.

**Hedges, stated in the entry.** We have not tried a fix on Windows and
cannot. `plug-run.ps1` is generated, so the change belongs in
`codex/build/plugrunScript.codex`. And we cannot say whether anyone runs
plugs on Linux today -- the ladder does not, because it wrote its own
transport rather than wait for this one.

**What the cold read cost, and it was the headline again.** The first
draft said 38 of 56 were affected and "the other 18 take other paths and
are not affected". Zero of 56 consult the host selection; the true scope
is all of them. The same draft had the `$proc` chain backwards, crediting
the wait loop at `:59` for a message that comes from the cleanup at
`:168`. Both survived because they were read rather than run -- the
second took four lines of PowerShell to settle.

## 38. A self tail call in a definition that returns a FUNCTION jumps to a poison address on bare metal

**Found 2026-08-24 while writing tier 13, isolated the same hour. THEIRS
-- bare metal, not the plug. **SUPERSEDED 2026-08-24 by finding 39.**
PR 78 carried this framing and was CLOSED unmerged in favour of PR 79.
The self tail call is not the mechanism: it is one route into the
closure-representation defect that finding 39 describes, and the same
corruption is reachable with no recursion at all. What survives here is
the observation and its register dump; the predicate, the title and the
mechanism paragraph below are all WRONG and are kept only because the
2x2 is how the trail started. Read finding 39 instead.**

    add3 : Integer, Integer, Integer -> Integer
    add3 (x) (y) (z) = x + y + z

    make-adder : Integer -> (Integer, Integer -> Integer)
    make-adder (n) = add3 n                                    -- prints 47

    count-down : Integer -> (Integer, Integer -> Integer)
    count-down (n) = if n == 0 then add3 5
                     else count-down (n - 1)                   -- FAULTS

Both definitions return a closure -- `add3` applied to one of its three
arguments. The first reaches it directly and answers `applied 47`. The
second reaches it through a **self tail call**, and the seed-compiled
binary takes a general protection fault:

    applied 47
    !EXC=0d RIP=a5f000ff53f000ff CR2=a5f000ff53f000ff
            R13=000000000000000a R15=0000000000000019 RBP=000000003ffffff0

`a5f000ff53f000ff` is a poison fill, not an address: the program jumped
through a code pointer nothing ever wrote. No diagnostic, no CDX code --
a register dump, which is what a Codex program's fault looks like.

**The 2x2 is what makes it sharp.** Three cells are measured and the
fourth is the crash:

    return type   reached directly        reached by self tail call
    Integer       fine (everywhere)       fine (tier 13, arg-swap et al)
    a function    fine (make-adder, 47)   FAULTS (count-down)

So neither ingredient is enough on its own. It takes a self tail call
whose value is a closure.

**Hypothesis, stated as one.** Bare metal has turned self tail calls into
jumps since Update 30, which reuses the caller's frame; a closure built
in that frame would be clobbered by the jump that is supposed to return
it. That is consistent with a poison code pointer, but it is inference
from the shape and the register dump, NOT something measured in the
emitter -- `emit-expr`'s tail-position path and where a partial
application's environment is allocated are what a fix would have to read.

**Read from source while writing PR 78, still not measured.** `emit-apply`
(`Emit/X86_64Compound.codex:148`) tests
`st.tco.active & saved-tail & is-self-call` FIRST and routes straight to
`emit-tail-call`, which shuffles the arguments into the parameter slots
and `jmp`s to `loop-top`. That short-circuits ahead of every arity and
result-type decision below it in the same function -- including the
`is FunTy` arm that sends `make-adder`'s body to
`emit-partial-application`. And `is-self-call` (`Emit/X86_64.codex:75`)
walks the `IrApply` chain to its `IrName` and matches on NAME alone: no
arity test, no return-type test. So the two cells of the 2x2 that differ
are reached through different code, and the faulting one skips the arm
the working one takes. That names the asymmetry; it does not establish
that the environment is what gets clobbered. Where `build-partial-app`
(`IR/LambdaLifting.codex:312`) allocates relative to the reused frame is
the next thing to read. Note the name-only rule is the same shape as
finding 36 in the python plug.

**Why nothing caught it.** Every `*-loop` in the compiler returns a
value, not a function, so the compiler cannot reproduce this on itself,
and the plug oracle's Lambdas section (added at Update 48 for
COMPILER-13) exercises capture and application but not a self-recursive
definition that RETURNS a closure. Our own tier 13 tried to and hit it
by accident on its first run.

**Confidence: HIGH.** Reproducible, minimal, and isolated by a control
in the same file that answers correctly on the same arm in the same
run. What is NOT established is the mechanism above, or whether the zig
arm shares it: the zig arm cannot answer yet, because it refuses this
shape at compile time (`fn make_adder(n: i64) CxFn2(i64, i64, i64)` --
a separate gap, and ours).
