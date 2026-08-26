# Findings

What the ladder has turned up, numbered in the order filed. **Each finding's
own opening paragraph states where it was found, whose arm it is, and whether
it is fixed -- that paragraph is the authority.** No tally lives on this line:
a count maintained by hand beside free-form status paragraphs says whatever it
last said rather than what is true.

This file holds the LIVE ones. Findings that are fully closed move to
`CLOSED.md`, which keeps their numbers and a one-line disposition each, so the
gaps here are explained rather than mysterious. A finding is moved only when
its question is answered AND its fix exists; "fixed but not sent upstream" is
closed for this register's purposes, and `PRIORITIES.md`'s outbound queue is
what tracks the sending.

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

## 17. Unit families have no hosted-plug mapping; 8 census refusals are this one gap

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
transformation for the zig plug (finding 33). THEIRS.
SOURCE-READ ONLY -- no python arm has been run against it, and the
reproducer below is the thing to run before this is filed upstream.**

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

## 41. `riscv` and `java` break the same curried-application rule as finding 40, and riscv's correct fix is already in the tree, dead

**Found 2026-08-24 by an independent read of the plug family while
settling finding 40's open question. THEIRS -- `codex/plugs/riscv` and
`codex/plugs/java`, no ladder arm in the path. OPEN, and the QUESTION IT
ASKED IS ANSWERED. SENT as PR 80 (plugs-backlog 1.57), doc-only, off
`upstream/master` 5b8091e2, ladder tag `curried-apply`; the row was
absorbed 2026-08-25 by Update 50's interim push at main 19117.**

**RULED BINDING (Damian, rulings queue call 21, 2026-08-24):** the
Rulebook's over-application rule at `DevelopersRulebook.md:258` binds
every plug that keeps an arity map, with no exemption -- the reasoning
recorded upstream being that an exemption "would leave riscv shipping a
correct fix nothing calls and java consulting no arity at all". The
wiring is assigned: riscv calls `rv-emit-closure-over-apply` from its
dispatch, java gains the arity check, both in reek's plugs close-out
lane, with the observed-miscompile verification the 1.57 row asks for.
So the finding stays live only until that wiring lands; nothing here is
waiting on us, and the one thing we said we would not do -- run the java
arm on a host with no JDK -- is retracted on the PR rather than pending.

**What the ruling also decides:** it is the same rule at a fourth site in
finding 36 (the python plug), which was held back precisely to see
whether the rule bound. It does, so 36 no longer has to argue the rule
for itself -- see the outbound queue in `PRIORITIES.md`.

`docs/DevelopersRulebook.md:256-260` requires three cases of a plug that
knows the callee's arity: flat at that arity, under-applied with one
arrow per missing parameter, over-applied by applying the rest. Surveying
the family for finding 40 turned up two more plugs implementing two of
the three, and the way each fails is worth a row of its own.

**`riscv` has the fix and never calls it.** The named-definition path
(`RiscVCodeGen2.codex:583-591`) tests `list-length args < known-arity`
and routes to `rv-emit-partial-application`; every other case, including
`args > known-arity`, falls into `rv-emit-direct-call` with the whole
argument list. Seventy lines further down,
`rv-emit-closure-over-apply` (`:660-668`) is a correct take/drop
over-apply -- and `grep -rn rv-emit-closure-over-apply codex/plugs/`
returns exactly three hits: its signature, its definition, and its own
self-recursive tail. **Nothing in the tree calls it.** Someone wrote the
right thing and never wired it up.

**`java` never consults arity at all.** `JavaEmitter.codex:158-168`
emits `func & "(" & emit-jv-apply-args args ... & ")"` for both the
`IrName` root and the `otherwise` root, with no lookup on either path.
`lookup-arity` is defined at `:69-70` and `grep -n lookup-arity
JavaEmitter.codex` returns only those two lines -- the signature and the
definition. It is dead code in a second plug, for a second reason.

**`arm64` is a near miss worth recording rather than filing.** It has
the mechanism -- `a64-emit-oversaturated-call` (`Arm64CodeGen2.codex:927-932`),
reached from `:980-981` -- but the arity it consults is
`a64-known-arity` (`:901-915`), a hardcoded table of builtin names
(`list-at`, `par-map`, ...). It does not fire for user definitions. Its
local-closure path at `:976-978` does use a real def-arity table.

**How the family actually splits**, which is the context a backlog row
wants: `csharp` (`CSharpEmitterExpressions.codex:830-841`), `python`
(`PythonEmitter.codex:646-655`), `javascript` (`:501-511`) and `rust`
(`RustEmitter.codex:547-560`) route every non-exact case to a curried
spine, so over-application is handled by construction. The TS family --
`typescript` (`TypeScriptEmitter.codex:205-214`) plus `angular`,
`electron`, `react`, `svelte`, `vue` -- splits on `args > ar` explicitly
with take/drop. `haskell` (`HaskellEmitter.codex:411`) and `ocaml`
(`OCamlEmitter.codex:380`) emit juxtaposition, which is already correct
in those languages; both build an arity map and never consult it, which
is harmless there. The compiler's own x86-64 backend does the take/drop
split at `X86_64Compound.codex:154`. That leaves `zig` (finding 40),
`riscv` and `java` as the three that look flat where the rule says they
must not.

**Confidence: HIGH for riscv and java as source facts, and the dead-code
claim is a grep anyone can rerun.** What is NOT measured is the runtime
consequence: "this produces a broken program" is inference from the
emitted shape rather than an observed failure. Finding 40 is the same
defect observed end to end, which is why it is the one with a reproducer.

**CORRECTION 2026-08-24, and it was in the sent PR.** This finding first
said the runtime consequence could not be checked here because the host
has no PowerShell. That is FALSE: pwsh 7.5.4 is installed at
`~/.local/pwsh/pwsh` -- the ladder's own `truth_arm` invokes it by that
path for every bundle -- it is simply not on `PATH`, which is all
`which pwsh` was reporting. The claim was written from one negative
command and never checked against a tree that uses the thing daily.

What is actually true is narrower and, for the finding, stronger:

- **`test-plugs.ps1` never compiles what it emitted**, so for `java` it
  cannot detect this defect no matter how often it runs.
- **It does not run `riscv` or `arm64` AT ALL.** Its own prose says why:
  the harness drives every plug as `run.ps1 -Src <codex> -Out <text>`
  and asserts non-empty text with markers, while the native backends
  take `-IrInput` and emit the binary wire protocol, so they "fail
  parameter binding and exit 1 in under a second having done no work at
  all". They are excluded from the plug list deliberately.
- Running either plug here is possible but is a real job, not a grep:
  `run.ps1` shells to `build/compile.ps1`, which compiles through the
  seed, which on this box means the QEMU appliance. Not yet done.

**Why nothing caught any of them:** `codex/plugs/test-input/partial.codex`
covers under-application, saturation, and over-application of a LOCAL,
but never over-application of a named top-level definition -- the exact
shape all three plugs mishandle. `codex/plugs/test-plugs.ps1` judges
exit code, non-empty output and text markers (`:93-97`, `:163-177`) and
never compiles what it emitted. A one-line addition to `partial.codex`
would put all three in front of a compiler.

Related: finding 36 (the python plug's TCO matches a self-call by name,
so over-application in tail position loops instead of applying) is the
same rule broken in a fourth place, at a different stage.

## 39. A partial-application closure carries no remaining-arity, so under-application corrupts silently

**Found 2026-08-24 by measuring finding 38 until its framing collapsed.
THEIRS -- the native x86-64 backend, no plug in the path. OPEN. SENT as
PR 79 (COMPILER-18); ladder tag `closure-arity`. Supersedes finding 38.
The row was absorbed 2026-08-25 by Update 50's interim push at main
19116, and it is item 1 in the upstream rulings queue -- still a
question, not yet a decision: give the closure a remaining-arity word so
the trampoline can re-close, or refuse under-application at the emit
site. The recorded default reading is "implement the declared model",
but the object layout and the spec are both Damian's to move. Tier 14 is
our fixture for it and stays in the set.**

**The two programs that carry it.** `let h = add3 10 in show ((h 20) 12)`
prints 42 -- the shape of upstream's own fixture at
`codex/plugs/test-input/partial.codex:9-10`. The same computation in two
steps, `let j = add3 10 in let g = j 20 in show (g 12)`, FAULTS one line
later in the same program (`findings/probe-indirect-under.codex`). And
`findings/probe-closure-silent.codex` -- three ordinary definitions --
prints **6291488** (`0x600020`, a heap address) where 47 belongs, with no
crash and no diagnostic.

**Control:** `add3` returns an Integer, is named by a partial application
in every program in the series, and is correct in all of them. Only
definitions whose return type is a function are affected.

**A THIRD entry point, SENT as PR 86, found 2026-08-25 while trying to
close the corpus hole in finding 36's family** (`findings/probe-closure-overapply.codex`,
four lines, three definitions). The two programs above reach the defect
through a two-step application. This one reaches it through a **FLAT
OVER-APPLICATION of the named definition**: `pick 0 2 3`, where `pick`
declares one parameter and returns a function. Bare metal FAULTS on that
line -- not a wrong number, a register dump -- while the zig arm answers
6, then 7, then 15 and runs to completion. The sibling
`let p = pick 0 in show ((p 2) 3)` does the silent thing instead: **bare
metal prints 6291624, `0x600028`, a heap address** where 6 belongs, and
faults one line later. Same signature as `probe-closure-silent`'s
6291488, reached from a different direction.

**AND THE VARIABLE IS NOW ISOLATED, 2026-08-25: it is a second CALL
SITE, and nothing else.** Five programs, one property changed at a time,
bare metal each time:

| definition | call sites | bare metal |
|---|---|---|
| `sel (n) = add3 1` | 1 | `6` correct |
| `sel (n) = add3 n` | 1 | `12` correct |
| `sel (n) = add3 n`, four statements | 1 | `12, 25` correct |
| `choose (n) = if n == 0 then add3 1 else add3 2` | 1 | `6` correct |
| `sel (n) = add3 n`, four statements | **2** | **FAULT** |

`probe-overapply-two-callers.codex` and `probe-overapply-one-caller.codex`
are the last two rows and they differ in ONE line: whether the third
statement calls `sel` again or calls `add3`. That controls for statement
count, which the finding itself flags as an unexplained variable.

**So every earlier hypothesis about this was wrong, mine included.** Not
the recursion; not the branch (two return paths with ONE call site is
correct); not an argument-dependent capture. **With more than one call
site, `inline-single-caller` cannot fire, so the partial-application
object is really built and really entered -- and entering it is the
defect.** Inlined, the closure is materialised at the call site and the
trampoline is never reached, which is why every correct row above is
correct.

That also answers the finding's own "why does (2) need the mutual
recursion at all": mutual recursion is simply one way to defeat the
inliner, and a second call site is the cheapest. **The zig side already
had this written down** -- tier 14's prose says `control-pick` "survived
there only because the pipeline inlines pick and materialises the closure
at the call site; even-fn is mutually recursive and nothing can inline
it". This is the same statement for bare metal.

The earlier `choose` file failed for this reason and not the one recorded
for it: it called `choose` three times.

**This is why the corpus hole cannot simply be filled.**
`codex/plugs/test-input/partial.codex` has one definition, `add3`,
returning an Integer, so the Rulebook's over-application case at
`docs/DevelopersRulebook.md:258` is unreachable from it -- the branch
riscv, java, the python plug and (until PR 83) the zig plug all get
wrong. Every shape that WOULD reach that branch needs a definition
returning a function, and every such shape lands on this finding. **The
corpus is missing the case because a program exercising it does not run
on bare metal today.** That is a better answer than "nobody thought of
it", and it is an argument for COMPILER-18's ruling rather than a
separate ask.

**Mechanism, read from source and NOT measured.** A partial application
is `[code-ptr][capture...]` of `(1 + num-captures) * 8` bytes
(`Emit/X86_64Compound.codex:715-733`). Its code pointer is a trampoline
that shifts the incoming argument registers up by the capture count
(`:703-707`), loads the captures beneath (`:709-713`) and `jmp rax`
(`:724-725`) -- so it only works when entered with every remaining
argument at once, and the object stores no count for any caller to
consult. Both entry paths reach it: `emit-over-apply-extras`
(`:154`, `:253-274`) one argument per `call rax` by construction, and
`emit-indirect-call` (`:166-169`, `:205-219`) with whatever the source
wrote.

**Why it is not exotic.** `docs/DevelopersRulebook.md:258-260` declares
the model -- "over-applied by applying the rest one at a time".
`test-input/lambda.codex:19` drives the over-apply path every build and
passes, because its closure wants exactly one more argument. The tree
tests the boundary and nothing past it. COMPILER-12 records the same
shape on the plug side.

**Confidence: HIGH on the measurements, and the mechanism is labelled as
a reading.** Two things are NOT established and are stated as such in the
PR: why the silent case needs its mutual recursion (the flat form
`f (n) = add3 5` prints 47), and why appending a third statement to an
unrelated two-statement program stops its FIRST statement from printing
(`findings/probe-closure-luck.codex` against `-luck2`).

**Everything else in `findings/probe-closure-*.codex` is the search, not
the evidence.** The outbound case is the three files named above.

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
