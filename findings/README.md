# Findings

Twenty-nine, numbered in the order they were filed. **Each finding's own
opening paragraph states where it was found, whose arm it is, and whether it
is fixed -- that paragraph is the authority.** No summary tally lives on this
line, because a tally maintained by hand beside twenty-nine free-form status
paragraphs says whatever it last said rather than what is true.

This directory holds the findings and the probes that make them runnable.
It is discussion material rather than a proposed addition to the Codex tree,
which is why it lives here now: PR 67 is cut down to the `contrib/README.md`
pointer, so the record moved to the repository that maintains it. Take any of
it into the tree whenever it is useful; nothing here needs to be there for the
ladder to run.

The probes are Codex chapters and still compile with the depot's own tooling:

    build/compile.ps1 -Src findings/<probe>.codex -Out <out>.cdx

**What is banked, and against which seed, lives in the ladder's own README
and only there.** This page says what happened to findings, not what the
ladder is pinned to; when the two disagreed it was always this copy that had
gone stale.

Which Update absorbed what: findings 1-5 by Update 43, finding 11's remainder
by Update 46, finding 16 by Update 48 (as PR 75, credited), and finding 15 /
issue 72 by Update 48's native match guards. Findings 18 and 19 were fixed on
the u47 pin and sent as PR 76, which is still open and unabsorbed. Findings
6, 8 and 9 are recorded as found rather than fixed.

Findings 1 through 5 were fixed by Update 43 and each is marked at its
heading. Finding 1's fix is verified present in this seed: `emit-net-recv-raw-helper`
carries the round-up as `st56a`/`st56b`, the same two instructions and the same
insertion point that were proposed (see PLUG_IR_TRANSPORT.md, now marked
resolved).

Two re-checked today and still standing:

- **Finding 7** -- no `IRExpr` map or fold exists in `codex/compiler`, so every
  plug still rewrites the walk.
- **Finding 10** -- `emit-record-set-builtin` still stores through the
  evaluated pointer and returns it, so `__record-set` still mutates and the
  `mutable` keyword still promises value semantics nothing delivers.

**Findings 6, 8 and 9 are not re-checked against this seed.** They were
measured on 2,798,031 and are recorded here as they were found.

**Finding 12 is new and fixed in this PR.** Finding 11 was withdrawn as filed --
the cause was ours -- and the one thing that survived it is closed in Update 46.

**The CDX2064 ATA finding is filed upstream as issue 70** (2026-08-18; it has
no numbered section here -- section 15 is the match guards): the compiler's own
CDX2064 caught `emit-ata-wait-ready-bounded` patching its loop jcc six bytes
late, which is finding 10's mutation hazard with a live site attached. Detail in
`findings/cdx2064-ata-wait-ready.md`, including the eight sibling sites the
checker cannot see and the open question about argument evaluation order.

**Findings 13 and 14 were added 2026-08-18, against Update 46.** 13 is a
proposal with a patch and a measurement rather than a defect report: the depot
does not have the bug today and the change is inert across all 52 of its plug
bundles. 14 is a portability gap found while verifying 13.

## 1. `net-recv-raw` truncates odd-length frames

**CLOSED in Update 43.** The count is rounded up before it reaches RBCR.
The follow-on closed too: TCP and IP checksums are now verified on
receive, and a frame claiming more bytes than it carries is refused.

**Diagnosed, fixed in this PR, not compiled here.** Full write-up:
`PLUG_IR_TRANSPORT.md`. Read that one first if you read only one.

`emit-net-recv-raw-helper` derives its `rep insw` word count with
`shr rcx, 1`, which rounds down, so an odd-length frame loses its final
byte. The helper returns the full length anyway and the receive buffer is
never cleared, so that byte comes back as whatever the previous frame
left at the same offset. Silent, plausible, undiagnosed. Severity tracks
the number of odd frames: one gives a wrong program, 33-37 gives
`!EXC=06` inside `parse-expr`.

You have compensated for this before -- `ne2k_inject_rx` in
`tools/codex-vm.c` pads odd frames, with a comment naming the mechanism,
and `ip-total-length` is the guest half. Both are workarounds; the
receive path itself was never fixed, so it is sound only against an
emulator that pads for it. QEMU's `ne2k_isa` does not, and neither would
real hardware.

**Also worth your time:** nothing verifies receive-side TCP checksums. A
substituted payload byte reached the parser unchallenged.

## 2. The `deck-record` intercept fires on the name alone

**CLOSED in Update 43.** The intercept compares the chapter that defined
`deck-record` instead of matching the bare name.

**Reproducible, undecided -- we did not want to guess your intent.**

The x86-64 emitter intercepts any 1-argument call literally named
`deck-record` (`emit-apply` in
`codex/compiler/Emit/X86_64Compound.codex`) and emits `__deck-enter` /
evaluate-arg / `__deck-exit` instead of calling the function. In a unit
that never runs the compiler opening's phase-allocator initialization,
that corrupts allocator state and the program later reads garbage where a
pointer should be. Reproduces on the Update 40 and Update 41 seeds. The
decisive control: renaming the identity function to `my-id`,
byte-identical otherwise, passes.

`PlugTypes.codex` ships `deck-record : a -> a` so plug bundles
type-check outside the kernel, but the intercept fires on the name
regardless of who defined it -- so every plug kernel appears to execute
uninitialized deck enter/exit sequences today. The zig plug passes its
oracle anyway; our lexer subject died deterministically, which can only
be allocation-pattern luck.

Two contracts are possible and we did not want to pick one for you:
either units outside the compiler proper must initialize the phase
allocator (making the `PlugTypes` stub a trap), or `deck-record` outside
the compiler should degrade to a true identity (making the by-name
intercept want a guard -- perhaps firing only when the resolved callee is
the PhaseAllocator chapter's own def).

Each probe is self-contained, no cites, no other chapters. Compile with
`build/compile.ps1 -Src <file> -Out <out>.cdx` and run the cdx.

| file | deck-record | expected |
|---|---|---|
| `repro-crash.codex` | defined as `a -> a` identity, called at two sites | **page fault** (`!EXC` in `__linked_list_to_list`, garbage list pointer) |
| `control-renamed.codex` | byte-identical, every `deck-record` renamed `my-id` | passes: `toks 2` / `errs 0` |
| `probe-site-record.codex` | kept only around the record construction | page fault |
| `probe-site-ctor.codex` | kept only around nullary-ctor arguments | page fault |
| `probe-deck-init.codex` | as repro, plus `__deck-set __heap-save` first | still faults -- base init alone is not the fix |
| `probe-seeded-signal.codex` | none (control shape) | `toks 2` / `errs 1` / `e0 42` |

The shape is distilled from `Syntax/Lexer.codex` (`tokenize-collect`): a
state record threaded through a recursive collector via a variant
payload, with a LinkedList field read at the end.
`probe-seeded-signal.codex` is the honest-signal template -- a probe whose
expected output is an empty list cannot tell "correct" from "the misread
slot happened to hold zero", so it seeds 42 and demands it back.

## 3. `bytes-to-text` is O(n^2) in 42 of 44 plugs

**CLOSED in Update 43, and generalised past what was asked.** Rather than
fixing the copies, `PlugTypes` now holds the one linear definition every
plug shares.

**Fixed for the zig plug in this PR. The other 41 are untouched and will
hit the same wall at the same scale.**

Not a new discovery, and that is the point: `CSharpPlug.codex` and
`RecheckPlug.codex` already carry the linear version, with a comment
recording that the old accumulator "hung on the ~9.7MB compiler IR before
the plug emitted anything". The fix never propagated. The remaining
plugs still concatenate onto an accumulator per chunk, which copies the
accumulator every time.

For a 1.18 MB IR that is ~2.7 GB of allocation against a ~3 GB heap, so
the zig plug printed `OUT OF MEMORY` and emitted nothing.

One trap for anyone tempted by a smaller change: the 256-byte chunk is
deliberate. The inner loop is quadratic too, so cost is
`N^2/2C + N*C/2` and 256 sits near the `sqrt(N)` optimum. Raising it
alone makes things worse -- 8192 measured 4.6 GB and still died.

## 4. TypeChecker uses `capability-names` without citing Capability

**CLOSED in Update 43, by an instrument rather than a cite.** The cite was
added, and then `build/check-subset-cites.ps1` was written to build every
chapter against only what it cites -- which caught `BootPaint` borrowing
`to-unicode` with no cite on its first run. This was the better answer:
the finding was one instance of a class that only a subset build can see,
and the class is now measured from the inside.

Small, and only visible from outside a whole-foreword build.

`Types/TypeChecker.codex:3400` is

```
  capability-vocabulary : List Text
  capability-vocabulary = capability-names
```

and `capability-names` is defined in `foreword/core/Capability.codex:198`.
TypeChecker's cites are Build Settings, Phase Allocator and Tuple. There
is no cite for Capability.

Nothing is broken in the real build, because the whole foreword is
present and the name resolves. It surfaces when a subset of the compiler
is bundled into one unit -- we hit it building a type-check subject for
the plug oracle, where the bundler carries only what is named or cited and
the definition was simply absent.

Worth a one-line cite if you want the dependency declared. We mention it
because it is the same shape as the `deck-record` intercept above:
something the monolithic build makes invisible, which a subset build
notices immediately. If you care about the subset property -- and the plug
bundles are exactly that -- these are the cases that break it.

## 5. An unreachable match arm passes without a word

**CLOSED in Update 43.** CDX2096 refuses an arm nothing can reach.

`Types/TypeCheckerInference.codex:665-666`, in `lint-arg-narrowing`:

```
   in when declared-param
    is IntegerTy (lo) (hi) (mode) ->
     ...
    is otherwise -> st
    is otherwise -> st
```

Two identical catch-alls at the same indentation, in the same `when`. The
second cannot be reached. It looks like a copy-paste slip rather than
intent, and it compiles silently.

We scanned the rest of `codex/compiler` for the same shape and this is the
**only** instance -- 97 other consecutive `is otherwise` pairs are nested
`when` expressions where an inner catch-all sits directly above an outer
one, which is legitimate. So the dead arm is a one-off; the diagnostic gap
is the finding.

**The gap.** Codex says a great deal about far subtler hazards. CDX3005
spends a paragraph on shadowing a builtin, and rightly -- it explains that
the danger is cost rather than answer, and cites the Hamt case that sent
four chapters quadratic. CDX1070 refuses an application that ends at a
newline and names three ways to fix it. Against that, an arm that can
never run seems like something you would want to hear about, and nothing
says anything.

We noticed because zig rejects a second `else` prong outright, so the
emitted code would not compile. Our plug drops the later catch-all, which
is safe precisely because it is unreachable -- but the reason we looked was
a zig error, not a codex one.

Offered as a diagnostic suggestion rather than a bug: an unreachable-arm
warning would have caught this, and the compiler already has the arm list
in hand where it checks exhaustiveness.

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

## 11. WITHDRAWN as filed: the diagnostics-count claim was our harness

**The original claim was wrong and the cause was ours.** It reported a
DiagnosticBag reporting 72 errors with an empty diagnostics list, and asked why
the two targets disagreed about the number. The answer is that our harness
stands in for `opening.codex` and skipped a phase the driver runs:

    type-map      = build-type-def-map (checked.scoped.type-defs) ...
    stds          = sort-bindings (type-map & checked.all-bindings)
    resolved-defs = rewrite-ir-defs stds (ir.defs) resolve-ceiling

Without `type-map` the emitter's `st.type-defs` has no entry for a record
declared in the subject, so `resolve-constructed-ty` fails, and without
`rewrite-ir-defs` the IR still carries unresolved `ConstructedTy` annotations
into emission. Everything downstream followed from that. Nothing here was a
defect in the depot.

### What survives: two record layouts that disagree

**CLOSED in Update 46** (`adfae029`, seed 12B07296). The unresolved-type
fallback -- the by-list layout below -- is deleted, and the branch now raises
the same refusal `emit-field-access` raises, which is the asymmetry this
section asked about. The release gate and the BVT never took the branch, so it
was latent exactly as described. Credited to PR 67 in the change and in
`docs/PM/Active/GitHubUpdates/GitHubUpdate46.md`.

The account below is kept as filed. Nothing on our side worked around it: our
half was a harness that skipped RESOLVE, and running RESOLVE is the driver's
shape whether or not the fallback exists.

`emit-record` (X86_64Compound.codex:1751) chooses a layout by whether the
record's type resolved:

| | ranked by | offsets |
|---|---|---|
| type resolves -- `build-cce-byte-offsets` | `field-sort-key` = `width-prefix(width) & name` | cumulative field widths |
| type does not -- `emit-store-record-fields-by-list` | the raw field name | `rank * 8` |

Every reader uses the first rule unconditionally: `cce-byte-offset-and-type`
(via `accumulate-offset-width-sort`) in `emit-field-access` and in
`emit-record-set-builtin`. The two rules coincide only when every field is
eight bytes wide, because only then does the width prefix stop affecting the
order and the uniform slot match the real width.

`probe-record-layout.codex` is the smallest record where they part:

    Box = record { flag : Boolean, items : List Integer }

    resolved:  items @ 0   flag @ 8    size 9
    fallback:  flag  @ 0   items @ 8   size 16

A Box built through the fallback puts `flag` where `items` is read from, so
`b.items` yields the boolean -- 0 or 1 -- and `list-length` of that reads
`[0 - 8]`, which faults with CR2 at the top of the address space. That is
exactly the crash we chased: `__list_snoc + 3`, `RDI = 0`,
`CR2 = fffffffffffffff8`, called from `bag-add`.

### What is NOT established

**We could not reach the divergent path through `opening.codex`.** The probe
compiles and prints `3` through the normal driver, because the type resolves and
the first layout is used. We reached the second one only with a driver that
skips RESOLVE, which is our bug and now fixed. So this is a latent inconsistency
visible by inspection, not a demonstrated defect, and it may be unreachable in
practice.

The part that seems worth a look regardless is the asymmetry. Faced with the
same unresolved type, `emit-field-access` records an error and emits `ud2` --
it refuses, loudly. `emit-record` silently lays the record out by a different
rule than every reader will use. If the fallback is genuinely unreachable, it
could be an error instead; if it is reachable, it is silent corruption.


## 12. `__deck-set` is emitted without its argument, and zig will not compile the result

**Found 2026-08-17 against Update 45 / seed 270227BE. Fixed in this PR.**

`ZigEmitter.codex` mapped the builtin to a bare constant and never touched
`args`:

    ZigBuiltinEmitter { name = "__deck-set", emit = \args ctx d ty -> "0" },

Answering `0` is right. There is no deck in the zig target, so pointing the
deck cell somewhere is genuinely a no-op. Dropping the argument is the defect:
the argument is a binding at the call site, and zig refuses to compile a
binding whose only consumer disappeared.

    error: unused local constant
    b2: { const deck_base = cx_heap_save(); break :b2 b3: { _ = 0; ...

The remedy was already written two lines below, in the prelude, for the same
problem:

    // address-of answers 0 here by X86_64Compound's own account of
    // targets without it; the argument is still evaluated so its binding
    // stays used.
    fn cx_address_of(v: anytype) i64 { _ = v; return 0; }

So this is the second instance of a pattern that has a solved first instance
sitting beside it. `__deck-set` is the only other entry in the builtins table
that ignores `args` and takes one -- `__deck-enter`, `__deck-exit` and
`__deck-pos` also ignore `args`, and all three are nullary.

### Why it stayed latent

Both of the compiler's own callers use the address for something else as well,
so the binding survives on its second consumer:

    build (size) =
     let p = __heap-save
     in let deck-init = __deck-set p
     in let guarded = deck-reservation-guard p size      <- p used again

    init-phase-allocator =
     let base = __heap-save
     in let deck-init = __deck-set base
     in base                                             <- and here

`passes_to_x86` transpiles both of those functions to zig and compiles clean. It took a
caller that only sets, which is what our harness prologue is once it names
`init-phase-allocator` to turn the deck intrinsic on.

The general shape is worth carrying to the other 43 plugs: a target that has no
analogue for a builtin still has to consume that builtin's operands, or it
silently changes which bindings are live. A target whose compiler happens not to
mind unused locals would not have reported this at all.


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

## 15. Match guards are dropped by the zig emitter; the arm fires on pattern alone

**Found 2026-08-18 by an emitter audit; both arms measured 2026-08-19 against
Update 46 / seed 12B07296. Filed upstream as issue 72 (still present at
Update 47). CLOSED 2026-08-20: Update 48 implements match guards natively,
and its release adds a Match guards section to `plug-oracle-arith.codex`
aimed at exactly this failure shape ("no refusal, a wrong value"). Verified
at the u48 verbatim census re-pin: `plug-oracle-arith` -> match with the
guard rows in it -- two arms on one constructor with different guards, a
guard on a catch-all, a guarded tuple payload, all answered right by the
shipped emitter. `tonight.sh` (whose step 2 existed to measure this
finding's bare-metal half) deleted in the closing commit.**

`IRBranch` carries `guard : IRExpr` (codex/compiler/IR/IRChapter.codex:54) and
`ZigEmitter.codex` never reads it -- the word `guard` does not appear in the
emitter. A guarded arm becomes a bare switch prong and fires whenever its
pattern matches, so the program compiles cleanly on both arms and answers
differently. No refusal, a wrong value.

The probe is `findings/probe-match-guard.codex`: one guarded arm plus a
catch-all, chosen because two arms on the same constructor would be duplicate
switch prongs, which zig rejects, and a refusal would be the lucky case.

    classify : Val -> Integer
    classify (v) =
     when v
      is Num (n) when n < 0 -> 1
      is otherwise -> 0

Bare metal answers `guard-taken 0 / guard-taken 1 / otherwise 0`; the zig arm
answers `1` on the first line.

The machine-code plugs all honour the guard (X86_64Compound.codex:1879,
Arm64CodeGen3.codex:683, RiscVCodeGen3.codex, T3IsaEmitter.codex:980). Neither
the csharp nor the python emitter contains a read of `branch.guard` either;
only zig is measured here.

A fix cannot put a bare `if` inside the prong, because a zig switch prong
cannot re-dispatch to the arms below it. The direct shape is an if-else chain
(pattern test and guard as one condition) for a `when` that contains any
guarded arm.

## 16. The hosted heap starts at 0 and the deck is a no-op; three corpus oracles observe both

**Found 2026-08-19 by the corpus census (the first differ-class verdicts of
the run); zig arm measured by `corpus_run.py`, bare-metal arm is the depot's
hand-verified `.expected` oracles. Fixed on the pin (`24c0d925`) and proven
2026-08-19: 14/14 sweep plus the banked census, all three observing oracles
MATCH. Sent 2026-08-19 as PR 75 (the three-commit chain off `8f997bd8`);
replay spot-verified 5/5 on seed `800A7683`.**

One passage of ZigEmitter (the prose above `zig-name-map`) makes two
semantic choices and documents them as checked-not-assumed. The corpus is
the check, and it caught both:

- **`__heap-save` answers 0 on first call.** Bare metal boots with
  `mov r10, 6291456` (bare-metal-heap-base, 6 MB; essay random848), so a
  heap address is never 0 there. `codex/test/arith-narrow-proven` asserts
  exactly that ("__heap-save proves as a structural heap-address fact"):
  expected `mark-ok`, zig arm prints `mark-zero`.
  **The C# plug shares this defect verbatim** (`static long _ptr = 0;
  heap_save() => _ptr;`, CSharpEmitter.codex:637) and can never catch it
  itself -- its witness path stops at "compiles". Source-read only, not
  yet run.
- **`__deck-enter` / `__deck-exit` / `__deck-pos` are mapped to literal 0.**
  The C# runtime implements the real rule (deck_enter swaps _ptr with
  _dptr saving _bivy; deck_exit restores), and the depot tests observe it:
  `deck-bracket-contract` expects "enter switches to the mark : yes", the
  zig arm answers "no"; `deck-record-contract` likewise for "argument
  evaluates on the deck". The prose's claim "this target has no deck"
  conflates having no memory pressure with having no observable
  semantics; deck position is observable.

The fix (applied in `24c0d925`, swept and census-proven): init `cx_hp` at
6291456 to mirror the boot value -- cx_buf_want then zero-fills a 6 MB
prefix on first heap touch, which is the guest's own boot behavior -- and
port the C# deck rule (~4 small functions) with the three name-map
entries pointed at them. C# is gold for the deck RULE; the heap base is
bare metal's own number, not C#'s.

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

## 18. Integer arithmetic in the zig plug was overflow-checked; the language wraps

**Found 2026-08-19 by the corpus census (three crash-class verdicts); ruling
checked at the desk 2026-08-20; fixed on the pin (`78e8da1b`) the same day.
Ours, not an upstream defect -- recorded for the ruling and the asides.**

`bloom-spread`, `consistent-hash-balance` and `particle-spread` all died
with `panic: integer overflow` in hash-mixing code. The ruling that wrap is
the language's rule rests on five converging sources: CodexSubtypes.md says
Integer IS the 64-bit machine word; the IR names behavior wherever it
deviates (IrAddRealTrapping/Saturating, clamped bounded fields) and
IrAddInt is the plain op; the C# plug emits bare `+` on `long` in C#'s
default unchecked context; bare metal emits `lea`/`add`/`imul`/`neg` with
no `jo` anywhere; and decisively, Foreword's own BloomFilter iterates
`hash * 31 + c` unbounded, mixes with `bit-shru`, then tests `if h < 0
then -h` -- a product of positives that only goes negative by wrapping.

The fix: `+%`/`-%`/`*%` on the integer binop rows, `-%` for non-real
IrNegate, `cx_ipow` mirroring `__ipow` (negative exponent -> 0, wrapping
square-and-multiply) in place of `std.math.pow` which panics on both
overflow and negative exponents, shift counts masked `& 63` (x86 `cl`
semantics; C# `<<` on long masks identically), and a wrapping accumulator
in `cx_text_to_integer`. All three subjects MATCH their `.expected`.

Upstream asides, source-read only, each needing a demonstration before
filing:

- The **python plug** emits `+` on unbounded ints with no 64-bit mask, so
  it silently diverges from bare metal on any overflow; the JS plug is
  worse (f64 loses exact integers past 2^53).
- The **C# plug maps IrPowInt to `^`** (CSharpEmitterExpressions.codex:984),
  which is XOR in C#, not exponentiation.
- **plug-oracle-arith has no overflow row** to catch any of this; a
  wrap-observing row is the oracle proposal that would expose the fleet.

## 19. Char literals were CCE while Char values were codepoints; resolved by migrating Char to the CCE code

**Found 2026-08-18 by an emitter audit (probe written then); caught live by
the census differ `text-fold-indexed` 2026-08-19; resolved by convergence
on the pin (`ea8d51ac`) 2026-08-20. Ours -- the codepoint representation
was the plug's own choice; the migration is the fix, not a report.**
CONFIRMED CLOSED 2026-08-22: natives from the heap branch rebased onto u49
(PR 76 absorbed) ran prim-char, probe-char-ops and probe-char-literal
byte-identical on both arms; the four ledger rows were deleted.

IrCharLit was emitted as its raw IR payload (a CCE code) while `char-at`
answered a Unicode codepoint, so `char-at s i == 'x'` lived in two
alphabets and was false for every letter -- a wrong answer, not a
refusal, on both probes and on the depot's own vowel-count test
(`text-fold-indexed`: expected 3/2/4-style counts, zig arm answered 0s).

Resolution is the identity model bare metal and the C# plug share:
char-code / code-to-char vanish, char-at is the same bare read as
char-code-at, cx_char_to_text stores one raw byte, is-letter / is-digit
use the CCE bands (13..64 and 97..127 letters, 3..12 digits -- read off
`emit-is-letter-builtin` itself). The codepoint model was structurally
lossy (CCE aliases canonicalise through any code->cp->code detour,
corrupting byte-wise text rebuilds); codepoints now exist only at the I/O
boundary.

Both-arms evidence, line-identical on every row (bare metal run on the
droplet appliance, zig arm through the rebuilt natives, 2026-08-20):
`probe-char-literal` answers found-x 1 / found-a 0 / lit-lit 1 /
code-of-x 36 on both arms (the zig arm answered found-x 0 before the
migration); `probe-char-ops` answers all nine rows identically on both
arms, including letter-accent 1 and letter-cyrillic 1 through the second
band, which the old a-z/A-Z test refused. `text-fold-indexed` and
`shadow-builtin-fold` (finding of the same census day: builtin
interception ignored user shadowing, fixed in `993d9f8b` -- whose first
cut broke every ladder rung by yielding for subj-deck-record too, a name
whose definition zig-skip-def deliberately never emits; the yield now
exempts exactly the skip list) both MATCH their `.expected`.

LANDED 2026-08-20: sweep 14/14 green over the batched change-set and the
census re-banked with 42 verdicts moved -- the five hunt targets to
match, differ/crashed/codexir buckets all EMPTY. The unplanned yield of
the batch: all 36 hosted-compiler (codexir) aborts healed, and 15 of
those programs now match outright.

CORRECTED 2026-08-20 (evening, measured at the u48 verbatim re-pin):
the aborts were attributed here to finding 18's wrap fix alone, and
that was wrong by majority. Panic-classifying every codexir abort under
the verbatim emitter: **33 die on `codepoint outside the CCE tiers`
(finding 19's char-CCE class -- cx_char_to_text framing a raw CCE byte
inside the compiler's own decode-escapes) and 4 on `integer overflow`
(finding 18's wrap class).** The healing was real and the batch fixed
all of it, but the credit belongs mostly to the char migration. The
attribution went unexamined because the fixes landed as one change-set
and nobody classified the panics per-program until a newcomer
(gop-composite-vclip, new in u48) forced the question.

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
direction the guard does not see, still riding with PRIORITIES item 1).
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

## 26. `peek-qword` trapped on every negative qword

**Found 2026-08-21 by tier 5 of the unit inventory, by accident, before anyone
thought to test negative values. Ours. FIXED on the branch (`3a490b8c`).**

Bare metal loads eight bytes as one 64-bit value, and every bit pattern is a
legal `i64`. The plug rebuilt it with checked multiply-and-add:

    while (cx_j >= 0) : (cx_j -= 1) cx_v = cx_v * 256 + cx_heap_mem[...]

which traps whenever the top byte sets the high bit -- that is, on every
NEGATIVE qword. `findings/probe-peek-qword.codex` isolates it to eight bytes:
over `00 00 00 00 00 00 00 FF`, bare metal answers `-72057594037927936` and
the plug panicked with integer overflow. Wrapping arithmetic reproduces the
load exactly.

## 27. A freshly reserved buffer is zero on bare metal and arbitrary here

**Found 2026-08-21 by `findings/prim-buffers.codex`, both arms, same program.
Ours. FIXED same day (`c7feba61`).**

    assertion                       zig arm   bare metal
    neighbours undisturbed          NO        yes
    fresh span is zeroed            NO        yes
    write past end lands on it      yes       yes

A buffer is a span of the heap reserved by `__heap-save` then
`__heap-advance`. On bare metal that territory has never been written, so it
reads as zero -- the plug's own prelude comment claims to match "an arena the
guest zero-fills at boot". On this arm it reads as whatever was last there.

**FIXED** (`c7feba61`), and the mechanism was not the one recorded first.

`std.mem.Allocator.alloc` memsets every allocation to `undefined`
(`~/zig-0.16.0/lib/std/mem/Allocator.zig:301`, in `allocBytesWithAlignment`,
which every `alloc`/`create` funnels through), and `undefined` is **0xAA** in
Debug and ReleaseSafe. The 1.5 GiB region therefore arrived filled with 170s
rather than zeros.

**Build-mode dependent, which is why it hid.** That `@memset(_, undefined)` is
elided in ReleaseFast and ReleaseSmall, so the old code was zero-and-lazy in a
release build and 0xAA-and-committed only in Debug/ReleaseSafe. `zig build-exe`
defaults to Debug, which is what the natives are built with.

**Scope, precisely.** The fix zeroes the RESERVATION. Sub-allocations through
`cx_gpa` -- `cx_ll_empty`, `cx_new`, `cx_concat` and friends -- still go
through `Allocator.alloc` and still get memset to 0xAA individually. They are
initialised immediately so that is believed benign, but the claim to make is
"spans carved by `__heap-advance` now read as zero", which is what the probe
measures, not "no 0xAA anywhere". `findings/probe-fresh-span.codex` printed it plainly: 256
nonzero bytes of 256, `170 170 170 ...`, in two separate spans, where bare
metal reads all zeros. Reserving with `rawAlloc` instead skips the wrapper's
memset and the same probe reads zero. `rawAlloc`'s doc warns it is "not
intended to be called except from within the implementation of an
`Allocator`" -- which is exactly where we are, since `cx_bump_alloc` and
`cx_heap_vtable` are one. Worth knowing: the zeroing is an **OS** guarantee
(Linux `mmap(MAP_ANONYMOUS)`, Windows committed pages), not an `Allocator`
interface guarantee, and on wasm `page_allocator` is a reusing pool that makes
no such promise.

Two things follow that were not about zeroing at all. The memset **touched
every page of the reservation**, committing all 1.5 GiB up front -- the exact
opposite of the "resident stays proportional to what is touched" property the
design comment claims for it. And a top byte of 170 is negative, which is how
finding 26 got tripped by a qword read from supposedly-fresh memory.

The first mechanism I recorded here -- `cx_bump_free` rewinding the frontier
so a later reservation lands on written bytes -- was tested and **refuted**
before the real one was found: with free made a no-op, so no byte is handed
out twice, the span still read non-zero. Nothing was being reused; the region
was never zero to begin with. Do not repeat the free-rewind test; it has been
run twice.

Consequence: any code that assumes a reserved span reads as zero is correct on
bare metal and wrong here. `init-emit-workspace` reserves the 8 MB code buffer
and 2 MB data buffer exactly this way. It is also how tier 5 found finding 26:
a qword read from supposedly-fresh memory had a high top byte.

Also tested and refuted for finding 24, twice over. Rebuilding `codexir` with
`cx_bump_free` made a no-op does not change that crash -- identical frames,
same site. Neither does reserving the region with `rawAlloc` so it is
zero-filled rather than 0xAA: same crash, same frames. **The 0xAA fill is not
behind finding 24**, which the observed evidence already hinted at -- the
corrupt length there is pointer-shaped (order 1.3e14), not 0xAAAA-shaped.

That test did confirm the resource half of finding 27 by accident. The same
compile takes **38.0s real / 15.3s sys** with the 0xAA fill and **11.4s real /
1.8s sys** with `rawAlloc`. The memset was touching every page of the 1.5 GiB
reservation, and it cost 13.5 seconds of system time per run. Independently
measured at 512 MiB: `Allocator.alloc` gives 525,952 KB max RSS and 131,178
minor faults, `rawAlloc` gives 1,664 KB and 107.

**Note for finding 24:** the out-of-buffer write is unchecked on BOTH arms, so
that is upstream's semantics and not a divergence. The last named suspect for
the `codexir` corruption is therefore exonerated as a *divergence*, though an
unchecked write remains a possible mechanism on either arm. This zero-fill gap
is the better candidate and did not exist as a hypothesis before tier 5 ran.

## 28. `substring` traps on bare metal and clamps here, so a killed program keeps running

**Found 2026-08-21 by `findings/prim-text.codex` measuring a family that had
no row anywhere. Ours. FIXED same day.**

    findings/probe-substring-trap.codex        zig arm    bare metal
    "about to ask for 40 bytes of a 5-byte"    printed    printed
    answered length                            5          <died>
    "still running, so this arm clamped"       printed    <died>

Bare metal dies with `EXC=06` -- invalid opcode, the UD2 -- and the request is
still on the stack at the fault: `S[10]=5` the source length, `S[20]=0x28` the
40 that was asked for. It never reaches the second print.

**Upstream ruled on this deliberately and wrote down why.** Substring once
took its start and length on trust; `substring a 0 40` on a five-byte string
answered `abcde   s       PASSWORD-1234567890     ` -- the whole of the next
allocation, returned verbatim. The fix traps rather than clamps, at Damian's
ruling, "because a clamp turns a program's bug into quietly wrong data, and
this project's virtues say a safety guarantee is never silently degraded"
(`Emit/X86_64Builtins.codex:640`; `emit-substring-bounds` at `:666` is three
UD2s -- negative start, negative length, and length past the end).

`cx_substring` clamped with `@min` on both ends. So the plug took a program
upstream kills and ran it on quietly wrong data: **the exact outcome the
ruling exists to prevent, reintroduced by the backend that was supposed to
mirror it.** Asked for 40 bytes of a 5-byte text, it answered 5 and carried on.

**FIXED.** Three checks mirroring bare metal's, in the same order, including
the one that is easy to get wrong: the third compares by SUBTRACTING rather
than adding, because `start + len` can wrap and the input that wraps it is the
one an attacker picks. `s.len - cx_a` cannot wrap because the guard above pins
`cx_a` to `[0, s.len]`. Verified standalone on 0.16.0: all seven in-range
shapes the tier file asserts still answer identically, and `substring s 1
maxInt(i64)` now panics where it used to return the tail.

**No rung can have depended on the clamp**, which is why this was invisible to
eleven days of sweeps: a subject that went out of range would trap on bare
metal, so its truth would be broken and the rung red before the comparison
ever ran. Only a test that deliberately goes out of range can see it, and no
tier file could hold one -- a trap would take that file's other assertions
down with it, which is why this probe lives on its own.

**The general shape is worth more than the instance.** This is a bounds check
the plug weakened without anybody choosing to. The refusal net catches
constructs the emitter cannot render; it says nothing about a helper that
renders a construct with a *weaker guarantee* than the original. Ranked by
what it costs to find: sweeps cannot see it, the corpus can only see it if a
test program is deliberately out of range, and a source read finds it in
minutes once you know to compare guarantee to guarantee. Worth a pass over
every `cx_*` helper that takes an index or a length, asking not "does it
compute the same answer" but "does it fail on the same inputs".

## 29. A substring put on the deck was never on the deck

**Found 2026-08-21 by `findings/probe-deck-substring.codex`, both arms, same
program. Ours. FIXED same day and CONFIRMED end to end** through a `zigemit`
built from the fix: `BYTES survived` reads yes, and the concat control still
reads yes on both arms.

    probe-deck-substring                zig arm   bare metal
    length survived                     yes       yes
    BYTES survived                      NO        yes
    concat bytes survived               yes       yes

**A corruption, not a cost curiosity, and the sharper half of finding 28's
family.** Bare metal's substring copies, and it bumps `r10` -- the LIVE
allocation register, which between `__deck-enter` and `__deck-exit` is the
deck cursor. So a substring taken inside a deck extent lands ON THE DECK and
outlives a rewind of the frontier. That is the entire purpose of the deck.

`cx_substring` allocated nothing. It returned a slice of its argument, so the
bytes stayed where the argument's bytes were -- on the frontier, if that is
where the source was built. **A deck extent cannot move them, because there is
no allocation for the extent to redirect.** The value looks decked, reports the
right length, and points at memory the next `__heap-restore` hands back. The
probe allocates over the reclaimed span afterwards so the dangling read is
visible instead of accidentally still correct.

**Live in the shape that matters.** `emit-all-defs` brackets every definition
and carries accumulator tables across the brackets, and the tables that
motivated the whole `Text` narrowing are `List Text`. A text that was supposed
to be copied onto the deck but is secretly a slice of reclaimed frontier is a
table holding garbage -- and it would present as a length or a pointer read
out of whatever object landed there next, which is the shape finding 24 has
been chasing. Not a claim that it IS finding 24: `codexir` never calls
`__heap-restore`, so nothing is reclaimed in that binary. It is the same
failure mode in a different phase.

**Three aliasing sites, all fixed:**

- `cx_substring` now copies through a new `cx_text_dup`, which allocates from
  `cx_gpa` and therefore from the live cursor -- deck inside an extent,
  frontier outside, which is exactly bare metal's rule.
- `cx_text_split` returned a slice per piece; every piece now copies. Bare
  metal's `__text_split` builds real text blocks.
- `cx_concat` opened with `if (b.len == 0) return a;`. Bare metal has no such
  case: both `emit-str-concat-fast-bump` and `emit-str-concat-slow-alloc` bump
  `r10` unconditionally, so `a & ""` is always a fresh block at the live
  cursor. The short-circuit is gone.

**Concat was tested beside it and came out CLEAN on both arms, which is why
the test was worth running.** Our in-place path fires when the left operand
ends exactly at `cx_hp` -- and inside an extent `cx_hp` IS the deck cursor, so
a frontier-resident operand fails that test and falls back to a copy that
lands on the deck. Accidentally correct, for a reason worth keeping: **the
fast path is guarded on the LIVE cursor rather than on a remembered one.** A
prediction that only ever confirms is not worth making, and this one predicted
opposite answers for the two operations and got both.

**Cost consequence, measured after the fix.** The tier 3 rows found this by
showing substring at 0 bytes on our arm against bare metal's `8 + align8(len)`
-- 448 against 0 for a 28-piece scan. That saving WAS the defect. Re-measured
through a `zigemit` carrying the fix, the same rows read 4, 8, 20, 0 and 112:
we allocate a bare byte run where bare metal allocates a length word plus
8-aligned bytes, so the gap is now a flat **12 bytes a piece**, which is the
ordinary header-and-padding rule every other text row in the table pays. That
is the healthier failure -- an explainable representation gap rather than a
semantic divergence wearing the costume of a saving.

**What it says about the `Text` narrowing.** The cold agent's design review
gave two arguments for the packed-offset representation (b) over a
pointer-at-a-length-word (a): that (a) is incompatible with `cx_concat`'s
general in-place path, and that (a) cannot express a slice of somebody else's
bytes. **The second argument dissolves here** -- after this fix nothing in the
prelude expresses such a slice, because bare metal does not either. (b) still
wins, on the concat argument alone, and that argument is untouched.

## 30. The shifts refused counts the hardware simply masks, so we killed programs upstream runs

**Found 2026-08-21 by `findings/probe-shift-count.codex`, both arms, same
program. Ours. FIXED same day. The first divergence where WE are the stricter
arm.**

    probe-shift-count            zig arm    bare metal
    shl 1 by 64                  <died>     1
    shl 1 by 65                  <died>     2
    shr 256 by 68                <died>     16
    shl 1 by -1                  <died>     -9223372036854775808
    shl 1 by -64                 <died>     1
    reached the end              no         yes

Bare metal emits no guard. `emit-bit-shift` (`Emit/X86_64Builtins.codex:1180`)
moves the count into RCX and emits `shl`/`sar`/`shr` in their CL form, and
`shl r/m64, cl` uses **CL mod 64**. So `bit-shl a 64` answers `a`, `bit-shl a
65` shifts by one, and a negative count shifts by its low six bits -- `-1`
becomes 63, `-64` becomes 0. Nothing traps and nothing says anything.

`cx_shl` was `a << @as(u6, @intCast(b))`. `@intCast` of 64 to a u6 does not
fit, and neither does a negative, so both panic. **The plug was stricter than
the language it implements**, which is a divergence in the direction nothing
else on this list points: every other finding here is the plug being laxer
than the oracle. This one kills a program upstream runs to completion.

**FIXED.** One `cx_shift_count(b) = @truncate(@as(u64, @bitCast(b)))` shared by
all three shifts, which is exactly the low six bits, negatives included.
Verified against the banked bare-metal column: all twelve rows match,
in-range and out.

**Why no sweep could see it, and why that generalises.** A rung compares two
outputs; if neither arm ever shifts out of range the rung is green and stays
green, and if one ever does the plug's arm dies with a panic that reads like a
plug bug rather than a semantic difference. The question that found it is the
same one that found 28 and 29 -- *does this helper fail on the same inputs?* --
and it is worth asking of the whole `cx_*` surface rather than one helper at a
time. Two answers from that sweep are already recorded as clean and should not
be re-derived: `cx_mod` is faithful (bare metal takes `idiv`'s remainder then
adds `abs(b)` if it came out negative, the same Euclidean answer), and division
by zero traps on both arms.

**Standing caveat this one exposes.** `cx_list_at` and `cx_char_at` are
bounds-checked only by zig's own Debug-mode checks, where bare metal emits
UD2s into the instruction stream. That is fine today because everything here
builds Debug, and it is written down in README's "The zig build mode is part
of the experiment" -- but it is the same class of difference and it is not
fixed, only documented.

## 31. `address-of` answered 0 for everything, so every object was the same object and also null

**Found 2026-08-21 by `findings/prim-identity.codex` (tier 9), which exists
because a frequency pass ranked `address-of` at 65 uncovered call sites. Ours.
FIXED same day.**

    prim-identity                          zig arm   bare metal
    same object, twice asked               yes       yes
    alias has the same address             yes       yes
    record-set returned the SAME object    yes       yes
    equal contents, two objects            **NO**    yes
    `&` produced a new object              **NO**    yes

`cx_address_of` was `_ = v; return 0;`. Bare metal's is
`emit-identity-builtin` -- it returns the VALUE, and since records, lists and
texts are pointers there, the value IS the address.

**The two failing rows are the controls, and without them this file would have
passed.** Every "yes" above is `0 == 0`, true for the same reason a broken
implementation would make it true. The rows that ask for two things to DIFFER
are the only ones a constant cannot satisfy. This is the "keep a control" rule
from the unit-test item (PRIORITIES 5, then numbered 1.5) earning its place in the sharpest possible way: a test
suite made only of agreement assertions certifies a stub.

**What it actually breaks, from the compiler's own source.** Not hypothetical:

- `mode-ordinal (m) = if address-of m == 0 then 0 else when m is OvError -> 1 ...`
  On this arm `address-of m` is always 0, so the function **always returns 0**
  and never reaches the `when`. `real-width-ordinal` has the same shape.
- `copy-sx-text (b) (t) = if address-of t < b then t else substring t 0 (text-length t)`
  A durability check. `0 < b` is true for any positive bound, so it **always
  shares and never rematerialises** -- and the comment directly above it says
  why that matters: "substring copies bytes, so the rebuilt text does not point
  into the reclaimed region." Sharing instead leaves the text pointing into
  scratch that is about to be reclaimed. Finding 29's failure mode, arriving by
  an entirely different route.
- Memo keys: `cons-mix (cons-mix (cons-mix 12 (address-of ...)) (address-of ...))`
  builds type-memo keys out of addresses. Every address component is 0, so keys
  collapse to their constructor tag. Whether that produces a wrong answer
  depends on whether lookup verifies structurally after hashing, which is NOT
  established here -- recorded as a question, not a claim.

**The 0 was justified, and the justification does not apply.** The plug's own
comment read: "address-of answers 0 here by X86_64Compound's own account of
targets without it". That account says address-of "silently answers 0 on any
target where `address-of` cannot be modelled: **that cost the C# arm every tag
in this table**" -- describing the hazard as a cost that had already bitten,
and upstream's response was to stop depending on it there (they read tags via
`variant-tag` now), not to bless the 0. And this is not such a target: one flat
region with pointers into it is exactly the shape bare metal has.

**FIXED.** `cx_address_of` now returns the value for scalars and a
**heap-relative offset** for pointers. Heap-relative is the load-bearing part:
the answers are compared against `__heap-save` values, which are offsets from
`cx_heap_base`, so a raw `@intFromPtr` would order correctly among itself and
be nonsense against those. Slices take `v.ptr`; anything else refuses by name
rather than returning a number.

**Why no sweep saw it: THE LADDER STRUCTURALLY CANNOT.** Asked as an open
question and answered the same day by an independent read, which also corrected
the count -- 65 occurrences but **62 real call expressions**, since one is the
`BuiltinSpec` table entry and two are prose inside comments.

**59 of the 62 are not in the emitted program at all.** IR emission prunes to
what the `opening` reaches, and every one of those 59 belongs to one of two
families -- the `copy-sx-*` tree in `Syntax/SyntaxNodes.codex` and the
`mcopy-*`/`mkey-*`/`*-ordinal` tree in `Types/Unifier.codex`. Each is rooted in
exactly one caller, and both callers are in `codex/compiler/opening.codex`
(`:492` and `:675`). **That is the one chapter a rung can never bundle**, because
a rung replaces it with a harness and two chapters cannot both define `opening`.
Confirmed in the emitted zig rather than inferred: ten of the fourteen rungs
contain `cx_address_of` exactly once -- the prelude definition, zero calls --
and `fn mcopy_type`, `fn mode_ordinal`, `fn copy_sx_text` appear in none of
them, while a control (`fn deep_resolve`) appears in all.

**The other 3 sit in error branches a clean compile never takes** -- the
`is otherwise ->` arms of `emit-record` and `emit-field-access`, which fire only
when `resolve-constructed-ty` fails. `passes_to_x86_on_mid.truth` and `ir_to_x86_on_fib.truth` both record
`emit-errors 0`. Had they fired they WOULD have diverged and gone red, so this
is "green because the branch is dead", not "green because the divergence is
invisible".

So the answer is the first of the two branches, and the blindness is structural
rather than accidental: **the one chapter the ladder is architecturally required
to exclude is the only chapter that reaches this builtin.** No choice of subject,
no deck scale and no extra rung on the existing pattern would change it. Only a
harness that calls `copy-sx-document-guarded` and `mcopy-types` directly would --
or a unit test with a control row, which is what actually found it.

**Residual, and it is a live trap.** The fix makes `address-of` heap-relative,
which is coherent with `__heap-save`. But the three surviving sites do
`show (address-of rec-ty)` and `peek-qword (address-of rec-ty) 0` -- a
heap-relative offset where bare metal shows an ABSOLUTE address, and a
`cx_peek_qword` read of a zig struct's raw bytes where bare metal reads a tag
word. If either error branch ever fires, that rung goes red on those lines, and
**the first reading will look like an emitter bug rather than a representation
difference.** Arguably the divergence one wants to see; recorded here so whoever
meets it does not spend the afternoon it would otherwise cost.

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

## 33. No tail calls: recursion depth on this arm is bounded by the thread stack, bare metal's is not

**Found 2026-08-22 while running the native chain on the ir_to_x86 subject
(finding 24's closing experiment). Ours. FIXED 2026-08-24 on branch
`zig-plug-tail-calls` (`6cd40143` + the two follow-ups), verified end to
end; not landed upstream.**

**The measurement that closes it** (sandbox `20260824T115824Z-f33-tailcalls`,
natives from the branch, region 4 GiB from the heap branch beneath it):
`native/zigemit` on the 13,219,750-byte `ir_to_x86.ir` completes rc 0 in
27 s **at the stock 512 MB stack** and emits 3,021,734 bytes of zig --
against the recorded baseline where 512 MB died, 2 GiB died, and 3.5 GiB
reached only the end of tokenizing. `tokenize_collect`, the function it
died in, is among the 887 definitions of 3,633 that now emit as loops.

That the emitted program is also RIGHT is the other half, and it is the
half a stack fix could have faked: the zig compiles (2.5 s, 35,550,072
bytes), runs in 0.37 s, and both of its rungs are **byte-identical to
`truth/u49`** -- a full ir_to_x86 unit through the native loop with no
QEMU anywhere in the arm. `findings/probe-tail-loop.codex` covers the
four spine shapes separately and is byte-identical on both arms,
including `sum-nontail`, the control that must NOT be looped.

Note what is NOT closed by this. The 512 MB stack in every emitted
`main` stays load-bearing: the emitter's own prose (`zig-main`) records
that the case which reaches the limit is MUTUAL recursion --
`scan-token -> skip-prose-line -> scan-token` -- which no self-tail-call
elimination flattens, and that .NET overflows on a 96-byte chapter with
a 1 MB main thread. This finding was latent from Update 30, when bare
metal gained `st-set-tail-pos` and the python plug gained TCO in the
same commit; the 512 MB spawn added at Update 43 (2026-08-15) hid the
symptom for a week, until the native loop pointed the plug's own output
at the largest IR we have.

`native/zigemit` on the 13.2 MB native-produced `ir_to_x86.ir` dies in
`tokenize_loop`: a self-recursive loop that advances one TOKEN per frame.
The IR holds 3,282,147 tokens. The emitted program's `main` spawns its work
on a 512 MB thread (`std.Thread.spawn(.{ .stack_size = 512 MB }`), and a
Debug frame of `tokenize_loop` is several hundred bytes, so the stack is
gone before the tokenizer is. Measured: 512 MB dies, 2 GiB dies, 3.5 GiB
gets through tokenizing (and then hits finding 34). Bare metal's emitter
tracks tail position (`st-set-tail-pos` is everywhere in X86_64) and a
tail call there is a jump: its depth is zero for this loop. Every
`*-loop (xs) (i) (acc)` in the compiler has the same shape, and the plug
turns every one into a call.

The fix is in ZigEmitter: a self-tail-call in tail position becomes a
`while (true)` with parameter reassignment. Until then the native loop's
ceiling is subjects whose recursion-per-element stays inside 512 MB --
`codexir.ir` (8.6 MB) fits, `ir_to_x86.ir` (13.2 MB) does not.

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
does. Either is an emitter/harness change, and PRIORITIES item 1 carries
the decision.


## 35. A non-ASCII identifier is emitted raw, and zig's identifiers are ASCII

**Found 2026-08-22 by the u49 census (the first on natives from the heap
branch rebased onto the pin). Ours. CLOSED 2026-08-23 by `1249ad8a`
(`zig-ascii-ident`, transliteration to `_<code>` in both sanitizers):
ident-letters refused -> match on droplet-built natives, tiers 13/6 green,
rebank+sweep 14/14 in sandbox `20260823T021627Z-u49-f35`.**

`codex/test/ident-letters` is new at Update 49 and names a definition
`café` -- one of the thirty-one Tier-0 letters at CCE 97..127 that the
lexer now accepts as identifier characters. `zig-sanitize` maps `-` and
`/`, renames prelude collisions and quotes keywords, and passes every
other byte through; the emitted `fn café() i64` is two raw UTF-8 bytes
in a zig identifier, and zig 0.16 refuses it at the parser
(`ident-letters.zig:769:7: expected '(', found invalid bytes`). Verdict
moved `markers -> refused` between the 08-20 bank and this census: the
old natives stopped at is-letter's band before reaching the name, so
the gap only became visible once finding 19 closed.

Fix is confined to the sanitizer: any byte outside `[A-Za-z0-9_]`
either quotes the whole name (`@"café"`, legal in zig for any
non-empty string) or transliterates it to an escape (`caf_u00e9`);
quoting is simpler and `zig-sanitize` already quotes keywords. The
prefixed names through `zig-raw-ident` need the same rule. One program
hits this today; the census column is `refused`, not a wrong answer.


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


## 37. The 512 MB stack is protecting the parser's header scan, not the lexer's prose cycle -- and that scan is mutual TAIL recursion

**Found 2026-08-24 by measuring what the workaround actually holds up,
after finding 33 removed the self-recursion it was blamed on. Ours to
report; the cycle is THEIRS. OPEN.**

`zig-main` emits every program onto a 512 MB thread and its prose names
the reason:

    the case that reaches the limit is MUTUAL recursion, the lexer's
    scan-token -> skip-prose-line -> scan-token cycle, and no amount of
    self-tail-call elimination flattens that

**The named cycle does not reach any limit.** `scan-to-eol-end` stops AT
the newline without consuming it, so the third call in the cycle sees a
newline, returns a `Newline` token, and unwinds: three frames per prose
line, constant, never chaining to the next line. Measured on native
`codexir` built from the finding-33 branch, one constant changed in the
emitted source (the JUSTIFICATIONS slack methodology):

    prose lines   stack    verdict
        100       256 KB   rc 0
    100,000       256 KB   rc 0        <- identical; no accumulation
    100,000        64 KB   abort
        100        64 KB   abort       <- control: 64 KB is too small for anything

**What does reach the limit** is in the parser, and the same binaries
name it. On the real 2,503,544-byte compiler subject (4,511 top-level
definitions), the 8 MB run's backtrace is 7,096 frames of:

    2,393 x scan_top_level
    2,393 x try_scan_type_def
    2,287 x try_scan_def_header

`Parser.codex` "Header Scanning (streaming)": `scan-top-level` ends
`else try-scan-type-def ... st`; `try-scan-type-def` ends
`scan-top-level ...` on Just and `try-scan-def-header ...` on None;
`try-scan-def-header` ends `scan-top-level ...` on Just. One full turn of
the three-cycle per top-level definition, and **every edge is a tail
call** -- no frame in the cycle is live when the next is entered.

The cliff on that subject:

    stack    verdict
    24 MB    abort
    32 MB    rc 0

So the workaround is load-bearing -- about 28 MB for the largest real
document, roughly 7 KB per definition -- and 512 MB is about 18x that,
which is the headroom nobody had measured. It also bounds the compiler:
a document of ~75,000 definitions overflows even 512 MB, and the failure
is a segfault rather than a diagnostic.

**The fix is a source change with no new emitter machinery anywhere in
the fleet.** Nobody flattens mutual tail calls: bare metal's TCO is
self-only (`X86_64.codex:75`, `is-self-call (expr) (func-name)`), and so
is the python plug's and so is the zig plug's new one. But this cycle
does not need mutual TCO -- it needs to stop being mutual. The two
`try-*` functions are continuations that always return to
`scan-top-level`; have them RETURN their decision instead of calling
back:

    try-scan-type-def   : ... -> ScanStep   (found td + state | not a type def)
    try-scan-def-header : ... -> ScanStep   (found hdr + state | not a header)

and `scan-top-level` dispatches on that and tail-calls ITSELF. A self
tail call is what every TCO in the fleet already flattens, so the scan
becomes O(1) stack on bare metal, on zig, on python and on C# at once,
and the 512 MB spawn stops being load-bearing for the case that actually
drives it.

Not yet done: the same measurement on `zigemit` and on the other
natives, and a check of whether any OTHER cycle appears once this one is
flat. The 512 MB should not be lowered until that sweep exists -- this
entry establishes what one input needs, not what every input needs.
