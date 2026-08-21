# Findings: seven closed upstream, twelve standing, five fixed here, one proposal

This directory holds the findings and the probes that make them runnable.
It is discussion material rather than a proposed addition to the Codex tree,
which is why it lives here now: PR 67 is cut down to the `contrib/README.md`
pointer, so the record moved to the repository that maintains it. Take any of
it into the tree whenever it is useful; nothing here needs to be there for the
ladder to run.

The probes are Codex chapters and still compile with the depot's own tooling:

    build/compile.ps1 -Src findings/<probe>.codex -Out <out>.cdx

**Status: the ladder is banked at Update 47 (2026-08-19); Update 48
(`b643e7c`) is released and the re-pin is in progress (2026-08-20).**
Update 48 absorbed PR 75 (finding 16's fix, credited) and implements
match guards natively -- finding 15 / issue 72 closes pending the
re-pinned sweep's confirmation. Findings 18 and 19 (below) were fixed on
the u47 pin and filed as PR 76. Earlier status: findings 1-5 fixed by
Update 43; finding 11's remainder closed by Update 46; findings 6, 8, 9
were measured on 2,798,031 and are recorded as found.

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
bind-the-result-and-use-the-result: 354 `__record-set` calls in the fibx
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
by diffing the fibx subject's emitted code against bare metal.

Three things might be worth doing, in ascending order of appetite:

1. Say it somewhere. One sentence in the `__record-set` docs -- "returns
   the record, mutated in place" -- costs nothing and every future plug
   reads it.
2. Rewrite the two sites to use the binding they mean (`st12c`, `st27`).
   The output is identical under mutation and they stop reading as bugs.
3. Decide what `mutable` on a record declaration is for, given that
   plain records already have reference semantics. If it is vestigial,
   dropping it removes a promise the implementation does not keep.

Found by the fibx rung: the x86 code generator compiling fib, emitted
two ways. The zig plug had given plain records value semantics on the
strength of the declaration, which is why the divergence appeared at all
-- and it is now one representation, a pointer, matching bare metal and
C#. Seed F3722EAC (Update 43), QEMU/TCG, 2026-08-16.

## Finding 11 (WITHDRAWN as filed; what is left is narrower)

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

`whole` transpiles both of those functions to zig and compiles clean. It took a
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
`14b2b8b6`; the branch is still red on a second, open escape.**

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
`codexir` on the whole 2,496,998-byte fibx subject, five seconds in, before
any compilation happens.

Bare metal encodes it: the ladder's fibx and scale rungs pass through the
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

## 24. codexir dies on a large subject, and it is not a lifetime bug

**Found 2026-08-21 with the native loop, once finding 23's CCE fix let it
ingest real compiler source. OPEN. Ours to fix, arm unknown -- the evidence
rules out every mechanism we have chased this week.**

`native/codexir` built from `zig-plug-heap-unification` aborts 12.7 seconds
into the 2,496,998-byte fibx subject:

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
- **Not the in-place text concat** landed in `86675554`. Reverting it to the
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
from scratch in a sandbox (ladder `4349606`, codex `6fe3f49d`) with the CCE fix
coming from the emitter rather than a patch, and with the subject regenerated
in that sandbox: identical crash, identical frames, `cx_list_at` ->
`bsearch_rename_pos` -> `rename_has_entry` -> `resolve_def_name` ->
`register_all_defs` -> `check_chapter`. It runs 38 seconds before dying rather
than 12.7, which is the only difference and is unexplained.

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
thought to test negative values. Ours. FIXED on the branch (`1a5ec700`).**

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
Ours to fix. OPEN.**

    assertion                       zig arm   bare metal
    neighbours undisturbed          NO        yes
    fresh span is zeroed            NO        yes
    write past end lands on it      yes       yes

A buffer is a span of the heap reserved by `__heap-save` then
`__heap-advance`. On bare metal that territory has never been written, so it
reads as zero -- the plug's own prelude comment claims to match "an arena the
guest zero-fills at boot". On this arm it reads as whatever was last there.

The mechanism is `cx_bump_free` rewinding the frontier when the freed block is
topmost. Bare metal has no equivalent -- `__list_snoc` extends in place and
nothing hands a byte back -- so its frontier only ever advances into untouched
memory. Ours can retreat over written bytes and then re-reserve them, so a
"fresh" buffer arrives full of dead objects.

Consequence: any code that assumes a reserved span reads as zero is correct on
bare metal and wrong here. `init-emit-workspace` reserves the 8 MB code buffer
and 2 MB data buffer exactly this way. It is also how tier 5 found finding 26:
a qword read from supposedly-fresh memory had a high top byte.

**Note for finding 24:** the out-of-buffer write is unchecked on BOTH arms, so
that is upstream's semantics and not a divergence. The last named suspect for
the `codexir` corruption is therefore exonerated as a *divergence*, though an
unchecked write remains a possible mechanism on either arm. This zero-fill gap
is the better candidate and did not exist as a hypothesis before tier 5 ran.
