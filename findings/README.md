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

## Hypotheses

*Not findings. Each carries what would refute it and what that costs.*

### H2. A lambda whose type no DECLARATION fixes reaches the plug with `ErrorTy` for its parameters and its return, and nothing diagnoses it

Raised 2026-08-26 18:30 by `codex/test/roc-closure-captures-list.codex`, the
third Roc port. It refuses with `zig plug: no zig type for this codex type`
inside the closure's `CxFn1(<param>, <ret>)`, and separately with `no
address-of for this type`. **Not finding 47's class** -- measured on natives
built before AND after that fix, identically.

**What the wire carries.** Three variants, read out of the IR:

    let f = \i -> xs   (captured list)  (param "i" error) (fn error error)
    let f = \i -> 5    (integer body)   (param "i" error) (fn error error)
    let f = \i -> i    (param USED)     (param "i" error) (fn error error)

The third is the sharp one: its BODY is `(name "i" int-default)` while its
signature says `error`, in the same definition. No `CODEGEN-HALTED`, no
diagnostic -- an `ErrorTy` in a program the compiler reports as clean. The
use site is fine: `(name "f" (fn int-default (list int-default)))`, so the
information exists somewhere.

**Why it is not the unused parameter, which was the first guess.** Variant C
uses its parameter and behaves identically. **Why it is not every lambda:**
`roc-returned-closure`'s `\x -> 9` also ignores its parameter and is clean,
because `wrap : (Integer -> Integer) -> Wrapped` constrains it.

**WIDENED 2026-08-26 19:40 by four more Roc ports, and the binding form is
NOT the trigger.** The four inline-fold ports apply a lambda LITERAL in
function position -- nothing is let-bound -- and refuse identically. The
sharpest read yet is `roc-fold-sum`, one IR definition:

    (def "__lam_0" (params (param "xs" (list int-default))
                           (param "base" int-default)
                           (param "step" error))
      ... (name "fold-loop" (fn (list int-default) (fn int-default
              (fn (fn int-default (fn int-default int-default)) ...))))

`step` is `error` in the parameter list of the same definition whose body
holds `fold-loop`'s declared type, which says exactly what `step` is, one
node away. Its argument `\acc x -> acc + x` is worse: `(param "acc" error)`
while the body reads `(name "acc" int-default)`.

So the trigger is a lambda whose type is fixed only by INFERENCE from its
context, and never by a declaration -- `let`-bound or applied on the spot
makes no difference. Reworded above accordingly.

**What tilts it upstream.** No plug mentions `ErrorTy` -- not the zig
emitter, not the C# one -- while `IRTextParser.codex:276` parses `"error"`
into it, so the wire carries it and the parser accepts it. Compare the
type-variable case, where `CSharpEmitter.codex:534-541` documents the
situation and prescribes `dynamic`. Nothing here says a plug should expect
this.

    Falsified by:  BARE METAL refusing variant C. If the seed refuses it,
                   the program is ill-typed and the port is the defect, not
                   the wire. Also falsified by the compile carrying a
                   diagnostic we are discarding -- an ErrorTy that WAS
                   reported is a halt the plug should honour, not a gap.
                   Also falsified by the seed driver's own IR-CCE wire
                   NOT carrying `error` here, which would make it ours.
    Cost to test:  three guests, roughly ten minutes, all three answerable
                   in one sandbox run. NOT YET RUN -- the box is sweeping
                   finding 47.

**The reach is MEASURED, and it is a depot class rather than an artifact of
porting.** Of the six programs still hitting a `no zig type` marker after
finding 47's fix, every lifted lambda in four of them is error-typed:

    effect-launder-lazy     1 of 1 lifted lambdas error-typed
    ir-check-clean          2 of 2
    lazy-smoke             12 of 12
    linear-capture-once     1 of 1
    ota-gate-real           0 lifted lambdas    <- NOT this class
    type-name-existence     'no zig type for this APPLIED type', a different marker

**`ota-gate-real` is excluded on purpose**, and naming it matters more than
the four that fit: it carries the same marker with no lifted lambda in it at
all, so its cause is something else and folding it in would inflate this
hypothesis by one program on a marker-name match. That is the mistake the
census taught this morning -- a marker name is not a mechanism.

So the candidate population is four depot programs plus one Roc port, all
sharing the shape, against a post-47 histogram of 95 distinct gaps.


**THE WIRE READ, 2026-08-26 22:0x, `roc-fold-sum` through
`native/codexir`.** This is the design input for a recovery rule and it
shows TWO independent sources, where the hypothesis assumed one gap.

    (def "fold-loop" (param "step" (fn int-default (fn int-default int-default))) ...)

    (def "__lam_0" (params (param "xs" (list int-default))
                           (param "base" int-default)
                           (param "step" error))
                   (apply (apply (apply (apply (name "fold-loop" ...

    (def "__lam_1" (params (param "acc" error) (param "x" error))
                   (fn error (fn error error))
                   (binary add-int (name "acc" int-default) (name "x" int-default) int-default))

**`xs` and `base` recovered; only the FUNCTION-typed parameter did not.**
The hypothesis says "ErrorTy for its parameters and its return", and for
the let-bound lambda that is what happens. For an immediately-applied
lambda it is not: two of three parameters arrive typed. The refusal is
narrower than the hypothesis claims.

**Source 1, for `__lam_1`: the body's own USES carry the type.** The
params say `error` twice, and one node away the body reads
`(name "acc" int-default)` and `(name "x" int-default)` with an
`int-default` result. Scanning a lambda's body for a use of its own
parameter that carries a non-error type answers both.

**Source 2, for `__lam_0`'s `step`: the CALLEE's declared type.** The
body is an apply spine bottoming out at `fold-loop`, whose `step`
parameter is declared `(fn int-default (fn int-default int-default))` --
exactly the type that is missing, in the same IR, in a definition the
plug already has in `ctx.irdefs`. Recovery is: find which argument
position the parameter occupies in the spine, take the callee's declared
type there.

Source 1 is simpler and more general. Source 2 is the one that reaches
`step`, because `step` appears in the body only as an argument. **Both
are needed for these five ports, and neither exists today.**

This also settles where the rule does NOT go: `emit-zig-atype` (finding
55) is a different path with a different input, and a recovery rule
written there would not see an IR body at all.
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

## 53. `main` spawns `opening` on a thread, and zig refuses a thread entry that returns a value -- 40 corpus programs, and the value was the answer

Found 2026-08-26 21:0x by the corpus reading pass. **OURS**,
`codex/plugs/zig/ZigEmitter.codex`. Not fixed.

**40 of 112 corpus refusals, the second-largest class**, and until now it
was not a finding -- the only mention anywhere in this register is a
passing aside inside finding 42, naming it as a reason one program stayed
refused. A class this size going unfiled is what the reading pass was for.

    /home/steve/zig-0.16.0/lib/std/Thread.zig:427:17: error: expected return
    type of startFn to be 'u8', 'noreturn', '!noreturn', 'void', or '!void'

Every emitted program carries the same `main`:

    pub fn main() void {
        const stack_bytes: usize = 512 * 1024 * 1024;
        const t = std.Thread.spawn(.{ .stack_size = stack_bytes }, opening, .{}) catch @panic("spawn");
        t.join();
    }

The difference between the 40 and the rest is one line of the subject:

    opening : [Console] Nothing   ->  fn opening() void   ->  runs
    opening : Integer             ->  fn opening() i64    ->  zig refuses

**The thread is not gratuitous.** It is the only way to ask for a stack
bigger than the default, and Codex source assumes bare metal's. The C#
plug carries the same workaround and its comment gives the case: the
compiler's own lexer cycles `scan-token -> skip-prose-line -> scan-token`,
which self-TCO cannot flatten, and a 96-byte chapter overflows a 1 MB
stack. Removing the thread is not the fix. This is downstream of finding
33 -- no tail calls on this arm -- and will be until that changes.

**The returned value is the program's OUTPUT, not a status.**
`ble-att-encode.codex` ends `in a + b + c + d + e` and its `.expected`
holds `5`. `corpus_run.py` compares the process's stderr text against
`.expected`, so a shim that discards the value would turn 40 refusals into
40 silent mismatches -- strictly worse, because a refusal is loud.

**The C# plug already has the rule** (`opening-call-text`), dispatching on
`opening`'s return type: Nothing, Void, Effectful, Proof and PropEq are
called and discarded; a Text is printed through the CCE decoder;
everything else is printed. The zig plug has no such dispatch and spawns
whatever it finds.

**Falsification attempted:** the alternative was that these 40 share a
cause with the other refusal classes -- that the value-returning entry is
incidental and something else breaks them. Refuted by the signature: all
40 fail inside `std/Thread.zig` at the spawn, before any of the subject's
own code is analysed, and the two `opening` spellings above separate the
40 from the 289 that build.

**PREDICTIONS, written before the build (2026-08-26 21:2x, fix `3b7cc358`,
unbuilt).** Recorded first so the result cannot be rationalised after.

1. All 40 leave the `startFn` class. If any remain, the shim is not
   reaching them and the entry lookup is wrong.
2. **They will NOT all reach `match`, and that is not a failure.** The
   `startFn` error fires inside `std/Thread.zig` before a line of the
   subject is analysed, so these 40 programs have never had their own
   emitted zig checked by anything. Expect new refusal classes to appear
   as they are examined for the first time. A result of "40 moved, 15
   matched, 25 newly refused" is the fix working and exposing the next
   layer -- the `inductive-list` shape, at 40x the size.
3. The corpus total moves off 69 refusals by roughly 40 minus whatever
   new classes appear.
4. Programs whose `opening` returns Nothing are untouched: their shim is
   a plain call and their emitted `main` differs only by the extra
   `cx_entry` frame.
5. `factorial` and `geometry-test` already refuse on the Real marker for
   `show`; if either also has a Real `opening` it will now refuse at the
   entry instead, which is the same gap in a second place, not a new one.

**Cost of the fix:** a return-type dispatch in the entry emitter plus a
void shim for the thread to enter. The Real arm wants item 1c's
`cx_real_to_text` and should refuse until it exists.


**BUILT AND MEASURED 2026-08-26 21:43 (`f52-f53`, codex `31be533e`).
FIXED.** **Zero `startFn` refusals remain.** Corpus match 225 -> 263,
refused 69 -> 30, all 326 programs rebuilt.

**Prediction 2 was WRONG, and wrong in the good direction.** It said
"they will NOT all reach match, expect new refusal classes as these 40
are examined for the first time -- inductive-list at 40x the size."
They essentially all reached match. Exactly TWO new refusals surfaced
(`fork-nested` and `par-map`, `invalid operands: 'struct' and
'struct'`), not the 25 the prediction braced for. The hedge toward
pessimism was the wrong call and the fix was cleaner than its author
expected. Recorded because a prediction that is only ever checked when
it is right is not a prediction.

`neg-real-repro` moved `refused -> markers`: the entry Real refusal
firing with its own message, as designed.
## 52. A `when` on a Boolean reaches the plug as the SPELLING `True`, and the plug emits it into zig, which has no such identifier

Found 2026-08-26 21:0x by classifying all 112 corpus refusals by cause --
the reading pass, from a `run.jsonl` that had been on disk for hours.
**OURS**, `codex/plugs/zig/ZigEmitter.codex`. Fixed, not built.

    corpus/when-bool-cross.zig:870:33: error: use of undeclared identifier 'True'
    corpus/when-bool-pattern.zig:842:37: error: use of undeclared identifier 'True'

The emitted switch:

    switch ((_tl_n == 0)) { True => { return _tl_acc; }, False => { ... } }

**The requirement is written down, in a test the compiler ships.**
`codex/test/when-bool-cross.codex` opens by stating it:

    A `when` on a Boolean scrutinee reaches the plug as an IrLitPat whose
    value is the spelling `True` or `False`; the plug must read those as 1
    and 0. Reading them with a plain integer parse yields 0 for both and
    inverts the arms, so `frm` returned its initial accumulator (100)
    instead of 150.

That is a cross-backend regression, written because some other backend
got it wrong and returned a wrong ANSWER. This plug never got that far:
it emits an identifier zig does not have, so it fails loudly. The luck is
worth naming -- the failure mode the test was written to catch is silent,
and we avoided it by being wrong in a noisier way.

**Bare metal decodes through a shared compiler function**
(`Syntax/Token.codex:149`), whose entire body is the rule:

    pat-lit-to-integer (t) =
     if t == "True" then 1
     else if t == "False" then 0
     else lit-text-to-integer t

**The fix** is `zig-lit-pat-text`, the same rule spelled for a language
whose scrutinee here is already `bool`: `true` and `false` rather than 1
and 0. Applied at both `IrLitPat` sites, the switch arm and the if-chain.

**Falsification attempted:** the alternative was that this is finding
50's class arriving somewhere else -- both are Booleans the plug got
wrong. It is not. Finding 50 is `show` picking a conversion by the
argument's type and is fixed in the builtins table; this is a pattern
decoder in the match emitter, and the two fixes touch no common code.

**PREDICTIONS, written before the build (2026-08-26 21:2x, fix
`a2d4646c`, unbuilt).**

1. `when-bool-cross` and `when-bool-pattern` move `refused -> match`,
   printing `spin2: 150 / spin3: 150 / cross: 115 / frm: 150` and
   `bare-true: 1 / bare-false: 1 / computed: 1 / both-arms-named: 9 /
   if-control: 1 / int-control: 1 / char-control: 1` respectively.
2. **A `differ` verdict on either would be the worse outcome**, not a
   smaller one: it would mean the arms are inverted, which is the silent
   wrong answer `when-bool-cross` was written to catch. Its header
   records the number a backend produced when it got this wrong -- 100
   instead of 150 -- so a `frm: 100` is the signature to watch for.
3. No other corpus program should move from this change alone. If one
   does, the spelling appeared somewhere unexamined and the two-site fix
   is incomplete.

**CONFIRMED IN C# 2026-08-26 by the Cobblestone project agent**, from the
lead we sent over Gmail. It is **three sites, not one**: `cs-tco-lit-text`
(`CSharpEmitter.codex:403`), and the ordinary match path does the same in
`emit-pattern` and `emit-sub-pattern`
(`CSharpEmitterExpressions.codex:1239` and `:1259`). A Boolean literal
pattern lands in C# as the identifier `True` rather than the keyword
`true`. Runtime consequence is unmeasured on their side; the fix and the
measurement are assigned, pinned to `when-bool-cross` and
`when-bool-pattern`, with credit to us in the changelist.

**MEASURED ACROSS PLUGS 2026-08-26 22:1x, and the reach was THREE plugs,
not one.** The Cobblestone lane reproduced it by RUNNING the emitted
programs rather than by reading:

- **csharp** -- the three sites we named.
- **javascript** -- not predicted by us at all.
- **their absorbed copy of the zig plug** -- our fork carried our fix,
  their copy did not.

All three fixed on main, pinned to `when-bool-cross` and
`when-bool-pattern`, 11 rows green per plug, credit to us in the
changelist.

**The sweep we suggested found two defects nobody had reported**, which
is the return on reading a class across plugs rather than fixing one:

- the **csharp** TCO match emits an unreachable catch-all that Roslyn
  refuses as CS8510;
- the **javascript** plug's `CharTy` literals were missing the BigInt
  suffix, **so every char arm fell through silently.**

That second one is a silent wrong answer -- the class we care most about
and the one a source read does not find. It was reachable only because
the fix was measured by execution.

**The original read-across-plugs suggestion was taken literally:** the same lane
sweeps the remaining wired plugs, and the wasm plug gets the two cross
tests gated early. Findings 50 and 36 are queued upstream as leads from
the same table.

Worth recording that our lead UNDERCOUNTED. We named the one site we
happened to read and hedged it twice; the class was three times bigger.
Hedging the confidence was right and the scope estimate was still low --
those are different things, and only the first was hedged.


**BUILT AND MEASURED 2026-08-26 21:43 (`f52-f53`, codex `31be533e`).
FIXED.** `when-bool-cross` and `when-bool-pattern` both `refused ->
match`, printing exactly the predicted values. No `frm: 100` -- the
inverted-arms answer this program was written to catch did not appear.
No other corpus program moved from this change, as predicted.
## 51. A refusal that replaces an EXPRESSION strands the parameters that fed it, and zig reports the stranding, never the refusal

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

## 50. The zig plug implements one of `show`'s five type cases and maps the other four onto it, and that is 37% of every corpus refusal

Found 2026-08-26 by `codex/test/roc-early-return-predicate.codex`, a Roc
port, on its first run. **OURS**, `codex/plugs/zig/ZigEmitter.codex:852`.
Not fixed.

`show : forall a. a -> Text` (`Types/Builtins.codex:69`), and the plug is
one line:

    ZigBuiltinEmitter { name = "show",
      emit = \args ctx d ty -> "cx_show_int(" & emit-zig-expr ... & ")" }

**Bare metal dispatches five ways** (`Emit/X86_64.codex:1652`):

    f32 real       emit-show-real-approx
    other real     __real_to_text
    TextTy         the expression itself
    BooleanTy      emit-show-bool
    otherwise      __itoa

The C# plug dispatches too, on TextTy against everything else, and leans on
`Convert.ToString` for the rest. The zig plug implements the `otherwise`
arm and sends the other four to it.

**Reach, measured over the 2026-08-26 corpus run** (`run.jsonl`, 329
programs, 113 refusals):

    40  expected type 'i64', found 'bool'    show on a Boolean
     2  expected type 'i64', found 'f64'     show on a Real
    ----
    42  of 113 refusals -- 37%, the largest single refusal class in the corpus

The 40 include `arithmetic`, `tls-test`, `poly1305`, `ecdsa-p256`,
`dtls-record` and 35 more; the two Reals are `factorial` and
`geometry-test`.

**Falsification attempted, because a message match is not a mechanism** --
that is the mistake the census taught this morning. The refusal site was
read in three of the forty rather than inferred from the error text, and
all three are the call itself:

    cx_show_int((true and false))                      arithmetic
    cx_show_int(cce_is_continuation(0))                cce-tier1
    cx_show_int(((ones > 96) and (ones < 160)))        mix-bits

**It is LOUD, and that is the good news.** Zig types `cx_show_int(n: i64)`,
so a Boolean or a Real argument is a compile error and no program ships a
wrong answer. The plug's own rule -- never map an unhandled construct onto a
valid-but-different one -- is broken here in the form that fails at the
build rather than in the form that fails silently.

**The Text case is PREDICTED, NOT MEASURED.** Bare metal returns the
expression itself for `TextTy`; the plug would emit `cx_show_int` on a
`[]const u8`. No corpus program produced that mismatch, so either nothing
calls `show` on a Text or something upstream removes it. Worth one probe
before the fix claims to cover it.

**Confidence: HIGH.** One line of source against a five-way dispatch in
the oracle, and 42 programs whose refusal was read at the call site.

**Why it matters more than its severity suggests.** These 42 have been
sitting in the refused pile as 42 separate-looking failures. `show` is not
an exotic construct and the fix is a `when ir-expr-type` plus two prelude
functions -- one of the cheapest large moves available on the emitter.

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

**What it may still be hiding:** `corpus_run.py` runs this tool. Expect
the corpus clean count to FALL when the gate lands -- that is the point.
`codexzig`'s gate found 41 of 593 when it was switched on; this one has
never been asked.
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

## 47. The type-variable recovery walk knows `List a` and `a -> b` and nothing the subject declares, so a variable inside `Step a` cannot be recovered from any position

Found 2026-08-26 on the ladder droplet, by the second snippet ported from
Roc's closure/recursion suite (PRIORITIES item 3), on its first run.
**OURS**, `codex/plugs/zig/ZigEmitter.codex`, and the gap finding 46's own
fix left behind. Fix WRITTEN 2026-08-26, **not yet verified** -- the box was
banking `truth/u50` when it was written.

**Two earlier framings of this finding were wrong and are recorded here
because one of them reached PRIORITIES as item 1.** It was filed first as an
UPSTREAM compiler defect, on the grounds that a lifted lambda's signature
carried `(tvar 16)` while its body used the concrete type. Upstream says
otherwise in its own prose, `CSharpEmitter.codex:534-541`: the IR-CCE lift
runs after the resolve pass, a `__lam_N` carries "the expected types its
lambda was handed, not the resolved ones", and **the IR is well-typed**. C#
meets it with `dynamic`. So that shape is intended and the plug's job is to
RECOVER. The second framing said the recovery never consults the return
type; it does -- `zig-resolve-tvar-type` falls back to matching the def's
declared return against `resty` once the parameters run out.

**The actual defect is one `when` with three arms missing.**

    zig-tvar-in-type (id) (decl) (actual) =
     when decl
      is TypeVar (vid) -> if vid == id then actual else VoidTy
      is ListTy (elem) -> zig-tvar-in-elem-type id elem actual
      is LinkedListTy (elem) -> zig-tvar-in-elem-type id elem actual
      is FunTy (p) (fnrow) (r) -> zig-tvar-in-fun-type id p r actual
      is otherwise -> VoidTy          <-- every declared type lands here

The walk descends `List`, `LinkedList` and function types. **A
`ConstructedTy`, `SumTy` or `RecordTy` -- every parameterised type a program
declares for itself -- falls into `otherwise` and answers VoidTy.** So a
variable inside `Step a`, `Iter a`, `Opt a`, a tuple, or any user record or
sum is unrecoverable, in parameter position and return position alike. The
position it is reached from was never the issue.

**The smallest reproducer has no lambda in it at all**, which is what says
this finding is not about lifting. `codex/test/tvar-in-declared-type.codex`:

    Pair (a) = record { fst : a, snd : a }
    pair-swap : Pair a -> Pair a
    pair-swap (p) = Pair { fst = p.snd, snd = p.fst }

Measured against the pre-fix natives: **0 `__lam` defs in the IR** and
`unresolved type variable T42 of pair-swap` in the emitted zig. The variable
occurs only inside `Pair a`, in the parameter and in the return, so the
parameter loop and the return fallback hit the missing arm in turn. Bare
metal answers 73. Lifting was the path that exposed this, not the cause, and
the two earlier framings both mistook the path for the thing.

**Traced, not inferred.** For `range-to : Integer, Integer -> Iter Integer`
the IR annotates the partial application `(fn int-default (ctd "Step" (args
(tvar 16))))`, so `zig-closure-make` hands `resty = Step (tvar 16)` to the
resolver, which peels `__lam_1`'s declared return to `(ctd "Step" (args
(tvar 16)))` and asks `zig-tvar-in-type 16` to match the two. Both sides are
`ConstructedTy`. `otherwise`. VoidTy. `zig-resolve-tvar` then emits the
marker finding 46 installed:

    fn __lam_1(comptime T16: type, start: i64, stop: i64, ignored: i64) Step(T16)
    ... __lam_1(@compileError("zig plug: unresolved type variable T16 of __lam_1"), ...)

**Why finding 46 did not catch it.** That fix was found through the driver's
own lift, via `codexzig_build.sh`, and every case it produced had its
variables in `List a` or `(a -> b)` -- precisely the arms that exist. The
emitter memory predicted this exact shape: "a generic name must be applied,
and nothing enforces it centrally -- six sites had to learn independently.
Expect a seventh." A walk that knows some type forms and forgets the rest is
the same failure once more.

**The fix**, written and unverified: three arms descending the argument
lists pairwise, plus `zig-type-arg-list` to read them off the actual and
`zig-tvar-in-args` to walk the pair. One declaration reaches the walk under
all three constructors -- a name is a `ConstructedTy` until the checker
rewrites it to the `SumTy` or `RecordTy` it denotes -- so all three descend
identically. Matching is by POSITION with no name comparison, sound for the
reason upstream gives about this wire: the IR is well-typed, so a mismatched
pair cannot arrive.

**The premise of the big version is CONFIRMED; the outcome is not.**
`corpus/gaps.json` carries 40 distinct `unresolved type variable` markers
over 51 programs. Two were read straight out of their IR with the pre-fix
natives, and both have the variable inside a `ConstructedTy`'s argument
list -- the arm that is missing:

    typeclass-smoke  (param "__Showable-dict" (ctd "ShowableDict" (args (tvar 44))))
    db-full-test     (param "m"               (ctd "HamtMap"      (args (tvar 88))))

Neither is a Roc port and neither involves a lifted lambda, so the blocked
mechanism reaches well past the case that found it.

**What that does NOT establish** is that the fix resolves them: the walk
must also find a concrete type at the matching position on the ACTUAL side,
and nothing here has checked that. And `typeclass-smoke` deserves its own
look rather than being folded into this one -- `describe` also takes
`(param "x" (tvar 44))`, a BARE variable, which the existing `TypeVar` arm
already handles, so its failure may instead be the actuals list running
short and falling through to the return fallback. **One confirmed mechanism
is not a confirmed cause for all forty.** Re-run
`corpus_run.py --transpile` after the fix and diff the tvar markers in
`gaps.json`; that is the measurement, and it costs three minutes.

**Verification owed, in the order PR 85 established:** a tier row that FAILS
first, then the fix, then the row green on both arms, then natives ->
`codexzig_build.sh` fixed point -> `tiers_run.py` -> `corpus_run.py` -> a
full sweep. The truths banked today are unaffected: they are bare metal, and
this is the plug.

**Falsification attempted, and this is why the finding reads as it does.**
Three claims were filed and two died: "upstream's compiler emits a
self-contradictory def" was killed by `CSharpEmitter.codex:534-541` saying
the wire is intended and the IR well-typed; "the recovery never consults the
return type" was killed by `zig-resolve-tvar-type`'s fallback, which does.
What survived was the third, and it survived a test the first two would have
failed: a fourteen-line subject with no lambda in it, which fires the marker
against pre-fix natives with 0 `__lam` defs in its IR. Both earlier versions
predicted that program would be fine.

**PARTIALLY VERIFIED 2026-08-26, and the first verification of this finding
used the WRONG METRIC.** Natives rebuilt, 597 programs re-transpiled:

    unresolved type variable markers   40 -> 0 distinct, 51 -> 0 program-hits
    all emitter gaps                  135 -> 95 distinct, 40 gone, 0 NEW

**Those numbers are true and they measure the wrong thing.** A marker count
says the emitter stopped SAYING it could not answer. It does not say the zig
builds, and `corpus_run.py --transpile` does not build anything. Built
afterwards:

    tvar-in-declared-type   refused -> RUNS, answers 73    genuinely fixed
    roc-returned-closure    ran     -> RUNS, answers 9     unchanged
    roc-iter-map            refused -> DOES NOT BUILD      not fixed

`roc-iter-map` emits `Step(T16)` and `__lam_1(T16, ...)` with `T16` declared
nowhere -- 31 bare `T<n>` identifiers -- where an `@compileError` used to be.
**The new arms find an answer, and the answer is itself a type variable.**
`zig-prefer-concrete` keeps those as a last resort, which finding 46 chose
deliberately because inside a generic definition a variable IS the right
answer. Inside a closure's environment struct it is not, and nothing
separates the two cases.

**So the fix is real for the shape its reproducer has** -- a variable inside
a declared type whose actual is concrete -- **and it makes the other shape
WORSE**: a diagnostic became a build failure with no explanation. That is
the trade this project exists to refuse.

**How the wrong metric got past me.** The finding named "a diff of the
`unresolved type variable` markers in `gaps.json`" as its measurement, and
that is what ran. The measurement was carried out faithfully and it was the
wrong measurement to have named, because the marker is the emitter's
self-report and the question was whether the output is correct. **The right
falsifier was available and cheap the whole time: build three programs.** It
took four minutes once asked.

**MEASURED 2026-08-26 19:02, with a corpus run that BUILDS.** The scope test
(`bbf339c0`) landed and the numbers are:

    tvar markers        40 -> 8 distinct over 10 program-hits
    match               183 -> 184     nothing that matched stopped matching
    tvar-in-declared-type   (new) -> MATCH, answers 73

**And three programs traded a diagnostic for a build failure**, which is the
part that matters: `hamt-test`, `kvstore-test` and `inductive-list` moved
`markers -> refused`. Two of them are the same out-of-scope variable in a
THIRD emission path -- `cx_ll_of(HamtEntry(T25), ...)` inside a function
whose scope declares `T70`, a callee's variable emitted untranslated into a
caller. The third, `inductive-list`, is a different defect the marker was
masking: H3.

**So the fix now covers two of three paths and I have stopped.** The scope
test guards `zig-resolve-tvar`; `8b493672` refuses a whole closure whose type
names an out-of-scope variable; the list-element path is untouched. Patching
it would be the third site, and the emitter memory predicted this exact
shape -- "six sites had to learn independently that a generic name must be
applied; expect a seventh".

**The structural answer is a guard in `emit-zig-type`, and it does not
exist**: that function is `CodexType -> Text` with no context and 35 call
sites, so there is nowhere central that knows which variables are legal to
name. That is a refactor and a decision, not a fix, and it is Steve's call
rather than something to start at the end of a session.

**Where that leaves the branch.** Against the pin it buys one more program
that builds and answers correctly, and costs three programs their
diagnostic. By "fail-loud is the floor" that trade is not obviously worth
taking, and the row should not ship until the third path is closed or the
three are understood.

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

## 44. The AST does not carry a record's implicit type parameters -- only the IR text emitter derives them, so every consumer of the AST that is not the wire sees an incomplete type

Found 2026-08-25 on the ladder droplet against `0c4327d5`. THEIRS,
core-compiler. **SENT as PR 90** (COMPILER-20, ladder tag
`codexzig-fixed-point`). Measured: it cost two attempts at a single-binary
Codex-to-zig transpiler before it was understood.

`foreword/core/Sort.codex:20` declares

    SortPartition = record { list : List a, pivot : Integer }

with no parameter list at all -- `a` is free in the field types. The AST
value `ARecordTypeDef (name) (tparams) (fields) (is-mut) (span)` therefore
carries `tparams = []`, and **nothing in the compiler ever fills it in.**

What fills it in is the SERIALISER. `IRTextEmitter.codex:402-406` computes
`inferred = ir-collect-rec-field-tparams fields ...` at write time and
`ir-emit-tparams-text:386` writes the explicit list if there is one and the
inferred list otherwise; `:408-410` does the same for variants through
`ir-collect-var-ctor-tparams`. So the IR text says `(rec-def
"SortPartition" (tparams "a") ...)` and every plug, which reads that text,
sees a complete type. The AST it was derived from does not.

**The consequence, measured rather than argued.** Hand that same ATypeDef
straight to the zig plug's `emit-zig-chapter` -- which takes the compiler's
own `IRChapter` and `List ATypeDef`, so this is a legitimate call -- and it
emits

    const SortPartitionS = struct { list: *CxList(a), ... };

a monomorphic struct whose fields still mention `a`. That is zig that does
not compile: `error: use of undeclared identifier 'a'`. The SAME emitter,
handed the SAME program through the text wire, emits the generic form. The
wire is load-bearing for semantics, not just transport.

**A second instance of the same class, one level down.** Use-site
annotations: the wire carries `(record-ty "SortPartition" (args (tvar 30)))`
and the in-memory form renders without the args, so the emitter writes
`SortPartitionS{...}` where the wire's version writes `SortPartitionS(T30){...}`.
Deriving one and not the other is what makes this a class rather than a
bug: we fixed the first by copying the derivation into our harness, and the
second appeared immediately behind it.

**Why it matters beyond us.** Any tool that consumes the AST directly --
a second emitter, a linter, an editor integration -- inherits the
incompleteness, and inherits it silently, because the type LOOKS complete.
Whether a record is generic is a property of the type, not of its
serialisation.

**Our workaround, which is not a fix.** The combined transpiler emits the
IR text and parses it back in memory, so it runs the same code in the same
order as `codexir | zigemit`. That is a fixed point -- it emits its own
2.8 MB bundle byte-identically -- and it is also an admission that the wire
cannot be skipped today.

**Hedged.** We have not attempted the fix. Moving the derivation to where
the checker learns it touches the type checker and every plug that reads
type-defs, and we can verify only the zig arm.

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

## 42. A self-tail loop reads a TOP-LEVEL definition where the source reads its own parameter, and only zig's unused-parameter error made it visible

**Found 2026-08-25 by the Update 50 census re-pin. OURS -- the zig plug's
self-tail-call transformation, PR 81, ABSORBED UPSTREAM in Update 50's
interim push (main 19131). FIXED, VERIFIED and SENT as PR 85 on
2026-08-25.** The census moved
exactly three verdicts against the 2026-08-23 bank and one of them was
`dtls-fragment`, **match -> refused**: `corpus/dtls-fragment.zig:942:57:
error: unused function parameter`.

The refusal is the symptom. The defect underneath it is silent.

**The source** (`codex/foreword/encode/DtlsMessage.codex:97`):

    dtls-frag-loop (msg-type) (message-seq) (body) (max-body) (off) (acc) =
      let n = list-length body
      ...
      in let piece = dtls-slice-at body off take
      in dtls-frag-loop msg-type message-seq body max-body ...

Every `body` and `msg-type` in that definition is its own parameter.

**The emitted loop** declares `_arg_msg_type` and `_arg_body` -- the
plug's rename, correct in itself, because the test program bundled
alongside defines top-level `body` and `msg-type`
(`codex/test/dtls-fragment.codex:21,23`) and a parameter of the same name
would collide. Then the body of the loop calls **`body()` and
`msg_type()`**, which are those top-level definitions, and never reads
either parameter. `_arg_msg_type` and `_arg_body` each occur exactly once
in the function: their own declaration.

**So the emitted program reads a global where the source reads an
argument.** It happens to print the right answer here, because this
caller passes the top-level `body` and `msg-type` in, so the two values
coincide -- a property of this test, not of the transformation. A caller
that passes anything else gets a wrong answer with no diagnostic at all.
Zig refused only because after the substitution NO reference to the
parameters survived, and zig makes an unused function parameter a hard
error. **What has to be true for it to compile instead is now measured,
and it is narrower than "had one other use remained"** -- see the row
below.

**It is specific to the loop path.** `dtls_msg_encode` in the same file
takes the same two renamed parameters and reads them correctly
(`cx_list_len(_arg_body)`). The non-loop emission binds the rename; the
self-tail-loop emission does not.

**Where the instrument was blind.** `prim-tailcall` is green and has been
since it was written: it exercises loop conversion but no row gives a
loop a parameter that shadows a top-level definition, so the whole class
is outside the tier set. The census caught it because the depot's own
corpus contains the collision by accident -- exactly the property
`corpus_run.py`'s docstring claims for it, that a program written by
someone with no knowledge of this plug tests what our own probes do not
suspect.

**The tier row is in and it is RED** (`prim-tailcall`, row
`shadow-guard`, 2026-08-25, ladder `a8538b2`): bare metal 3, the zig arm
5, on a loop whose parameter `stop-at` is 3 and whose top-level
`stop-at` is 100. The emitted loop reads `stop_at()`.

**Writing it settled what makes the defect silent rather than loud, and
the answer is a second blind spot on top of the first.** The plug's
occurrence check drives a discard: a parameter it believes unread is
emitted as `_ = _arg_x;` and one it believes read is not. So the obvious
minimization -- read the shadowing parameter anywhere in the loop body
-- CANNOT produce a wrong answer. The check sees the read, emits no
discard, the substitution leaves `_arg_x` unmentioned, and zig refuses
the build. Measured, not reasoned: the three-line version of
`dtls-fragment` refuses with the same `unused function parameter` error.

The silent form needs a read the check cannot see, and `zig-occurs`
(`ZigEmitter.codex:1291`) walks a branch's body and not its **guard**.
A match guard inside one of the loop's own tail-call arguments is
therefore both invisible to the check -- so the discard is emitted and
the program builds -- and emitted by the loop path, reading the global.
`zig-occurs` misses handle clauses the same way, and that is untested.

The guard has to sit inside a tail-call argument, not at the top of the
body: a guarded match in tail position is not recognised as a self tail
call at all, so that shape never becomes a loop and answers correctly.

**So the refusal was luck twice over** -- once that no use survived, and
once that the collision was not behind a guard. A `dtls-fragment` whose
`body` were read from a guard would have compiled and shipped a wrong
answer.

**THE FIX, three hunks, measured 2026-08-25 and SENT as PR 85.** Branch
`zig-plug-loop-param-rename` off `upstream/master` `0c4327d5`, ladder tag
`shadow-loop-rename`, `plugs-backlog.md` row 1.58. Sandbox
`20260825T160701Z-f42-row`.

1. **`emit-zig-def`'s loop branch composes both rename tables.** It built
   the body context from `zig-push-tail-renames` alone, which covers the
   parameters the loop REASSIGNS and only those; an invariant slot is
   never assigned, gets no loop var, and so got no rename. Pushing
   `zig-push-param-renames` underneath restores the `_arg_` name for
   exactly those parameters, and the tail renames still win for the
   reassigned ones because `zig-renamed-scan` reads from the end.
2. **`zig-occurs-branches` walks a branch's guard.** Without this, hunk 1
   turns the defect from a wrong answer into a BUILD failure rather than
   fixing it: the discard `_ = _arg_x;` is emitted for a parameter the
   check believes unread, and zig refuses `_ = x;` followed by a real use
   as a pointless discard. Measured, not argued.
3. **`zig-max-list-len-branches` walks it too.** The file's own prose says
   that walk mirrors `zig-occurs`, "same nodes, same reason to visit them,
   and the same consequence for a node it forgets". It had the identical
   hole, shown before fixing: the same 40-element literal emits
   `@setEvalBranchQuota` in a branch body and none in a branch guard. That
   failure is LOUD (a zig comptime resource error) and no corpus program
   reaches it today. Neither walk descends into an effect handler's
   clauses, which is deliberate and now stated in the source --
   `emit-zig-expr` answers `@compileError` for any `IrHandle` with
   clauses, so nothing beneath one is ever emitted.

**What the measurements say, in the order they were taken.**

- **The tier row FIRST, red:** `prim-tailcall`'s `shadow-guard`,
  `!! shadow-guard 3 | shadow-guard 5` (ladder `a8538b2`).
- **After hunks 1 and 2** (natives `7fe0df50919f`): the row green on both
  arms; the 22-tier set green at 15 green / 7 noted / 0 unexpected,
  unchanged in shape from before the fix; **14 of 14 rungs green in a
  sweep, 1589 s**.
- **After hunk 3** (natives `40a72f63f172`): tier set green again, and the
  hunk shown INERT by byte comparison rather than by a second sweep --
  all fourteen ladder units, `lex` through `codexir` and the emitter's own
  bundle, emit byte-identical zig under both native builds. That is the
  honest claim: the sweep ran with hunks 1 and 2, and hunk 3 is proven to
  change nothing the sweep measures.
- **The census, which is what found it:** 320 of the 325 clean corpus
  programs are byte-identical to the 2026-08-25 bank and were not rerun.
  Five moved and **exactly one verdict moved with them --
  `dtls-fragment`, `refused -> match`.**

**Three more depot programs carry the collision.** The five whose emitted
zig moved are `dtls-fragment`, `final-batch-test`, `lorawan-encode` and
two hardware-only classifiers. The middle two stayed `refused` for
unrelated reasons (`use of undeclared identifier 'Timestamp'`; a
`std.Thread` startFn return type), so neither was ever run and neither
could have shown the wrong answer -- but their emission moving says the
shape is not a peculiarity of `dtls-fragment`.

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
