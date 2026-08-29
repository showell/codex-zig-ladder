# The type-def prune, parked 2026-08-28

Pruning unreachable TYPE definitions from the IR before it reaches the wire.
**Parked with real defects open. Do not send.**

## What it is

`emit-ir-cce` and `emit-ir-chapter` hand `ir-prune-unreachable-roots` the
defs and thread `fe.type-defs` PAST it (`opening.codex:1716`), so a chapter's
every declared type reaches the wire whether the program names it or not, and
all 56 plugs emit it. `Foreword Tuple` rides into every unit unconditionally,
which is why `Tup2..Tup5` appear in programs that name none of them.

The change adds `ir-prune-unreachable-typedefs` (~280 lines, all `ir-tdce-*`)
to `codex/compiler/Emit/IRTextEmitter.codex` and calls it at the two IR-wire
emit sites.

## Where the code is

**The measurement sandboxes are deleted (2026-08-29) and nothing here needed
them.** Four trees, 1.8 GB, all cut while the version with the defects below
was being built. Every pointer in this file is a branch, a tag or a commit,
all of them pushed; the numbers recorded here are the answers those runs
produced. Anything wanted again is a fresh sandbox and about fifteen minutes,
against a tree whose staleness nobody has to reason about.


    branch    prune-unreachable-typedefs   @ 3d331701   (pushed)
              cut from 2d5a7532 -- PR 96's tip, the minimal buildable U52 base
    worktree  ~/showell_repos/cobblestone-typedefs

    branch    typedef-prune-on-shaker      @ c8e1cda7   (local only)
              = zig-tree-shaking + the two prune commits, for MEASUREMENT
    worktree  ~/showell_repos/cobblestone-tdshake

    tag       u52-typedef-prune            (the measurement chain)

**Measure on the stacked branch, send the minimal one.** That is the standing
rule and it was learned again here the hard way: measuring on the bare PR-96
base gave three RED tiers that were absent features, not regressions.

## What is verified

Over 578 emitted corpus programs, one variable (the same compiler source,
differing only in whether the harness calls the pass):

    emitted zig   20,955,369 -> 20,079,085     -876,284  (-5%)
    IR wire       40,053,327 -> 38,876,722   -1,176,605  (-3%)
    decls             61,937 ->     52,775       -9,162

    Tup2 declared    578/578 ->    25/578    exactly the 25 that use it
    Tup3             578/578 ->     5/578
    Tup4, Tup5       578/578 ->     0/578

    changed programs     578, of which gained a declaration: 0
    distinct markers 107 -> 106

The IR-wire delta is byte-for-byte identical whether measured on the shaken or
unshaken stack, which is the right answer -- the wire is produced before any
plug runs -- and is a cross-check that both measurements are sound.

Tier set on the stacked branch: **27 tiers, both arms, green 20 / noted 7 /
RED 0.**

One emitter gap closes and it belongs entirely to dead code:
`codex/test/type-name-existence.codex` declares
`Holder = record { item : Later, vec : Vector 4 Integer }` and never mentions
`Holder` again; the plug has no emitter for an applied type, so it emitted
`vec: @compileError(...)` inside `HolderS`. The program was failing to
transpile on account of a declaration it did not ask for.

## The corpus --run, finished 2026-08-29

Real `zig run` -- compile AND execute -- over every clean program, diffed
against the hand-verified `.expected` files. On `typedef-prune-on-shaker`
at `c8e1cda7`:

    326 clean programs; building and running 326
    match 291, no-expected 23, refused 8, hardware-only 2, differ 1, crashed 1

**The one `differ` is `recursive-eq`, and it is FINDING 66, not this change.**

    want  eq ne eq eq ne ...
    got   ne ne ne ne ne ...

That is the recursive structural-equality helper answering `ne` to everything
-- the silent wrong answer already filed as finding 66 and owed to the U52
issue. It is a plug defect on a path this prune does not touch.

**The one `crashed` is `tcp-reliability`**: `panic: index out of bounds: index
0, len 0`. NOT ATTRIBUTED. It may predate this change; nothing here shows
either way, and the run's own header says so:

    *** THE BANK IS NOT ABOUT THIS TREE ***
    Every row below is a difference between two measurements, not a change
    this run caused.

So the verdict diff below cannot be read as caused by the prune. **To attribute
`tcp-reliability`, run `corpus_run.py --run` on `zig-tree-shaking` at
`16751b22` -- which IS this stack minus the two prune commits -- and compare.**
That is the one measurement this file still owes. It wants a fresh sandbox cut
at that commit; do NOT reuse an old one, since the natives must come from the
tree being measured.

**What the verdict diff shows anyway**, against a bank from 08-27 that predates
several changes: a long list of `refused -> match` and `markers -> match`, plus
`type-name-existence markers -> match`, which is the program whose only failure
was a type it never used. Several `zigemit -> codex-refused` rows move the
other way and are equally unattributed.

**None of this bears on the seven open defects above.** A corpus that passes
tells you the corpus lacks the shape.

## THE OPEN DEFECTS, ranked by whether they can drop a LIVE type

Found by a cold review, 2026-08-28. None was caught by any gate here, and the
reason is recorded under "why the gates were blind" below.

**1. Duplicate names across cited chapters are last-writer-wins.**
`ir-tdce-ctor-index` and `ir-tdce-build-index` both key by name with
`offset-table-set` overwriting. `fe.type-defs` aggregates every cited chapter
-- that is why `Tup2..Tup5` are everywhere -- so two chapters each declaring a
constructor `None`, or a type `Node`, is ordinary input. Only the last-indexed
slot is rooted by that name; the other type-def is dropped while live. The
reasoning block in the source covers ctor-vs-type collisions carefully and says
nothing about ctor-vs-ctor or type-vs-type.

**2. Type-class dictionaries may not be rooted.**
`ir-tdce-atype`'s `AConstrainedType (cls) (v) (inner)` does not collect `cls`.
Classes are synthesised into `<Class>Dict` `ARecordTypeDef`s
(`Ast/Desugarer.codex:951-967`), and reachability then depends entirely on the
rewritten signature naming the dict (`:1003-1004`), which happens only when a
class has MORE THAN ONE INSTANCE; the single-instance path erases the
constraint. **Exercise a multi-instance-class program before trusting this.**

**3. `SumCtor.return-type` is never walked.** `ir-tdce-ctors` folds only
`c.fields`. `return-type` is populated for GADT-style `| Ctor (f) : T`
(`Syntax/Parser.codex:883`) and resolved by the checker
(`Types/TypeChecker.codex:3876-3880`). **The AST half DOES walk it**
(`ir-tdce-vctors`), so the two halves of this pass disagree with each other.
Inherited from `codex-type-fold-children` (`Types/CodexTypeTree.codex:47-57`),
which omits it while its sibling `codex-type-map-children` includes it -- a
pre-existing hole made load-bearing for the first time.

**4. No bail-out, where the def prune has one.** `ir-prune-roots-indexed`
returns the chapter UNTOUCHED when its first root is not a def -- a deliberate
"if I cannot find my footing, prune nothing". `ir-prune-unreachable-typedefs`
has no equivalent: with `m.defs` empty, or roots that all miss, it prunes every
type-def.

**5. `offset-table-empty` is a mutating top-level constant.**
(`Core/OffsetTable.codex:29-32`, insert path mutates via `list-set-at`.) Before
this change exactly one OffsetTable was built per emit; now two are. If any
backend memoises a nullary definition rather than re-evaluating it, the second
table starts life holding the DEF prune's entries and `ir-dce-add-name` indexes
`visited` over the wrong list -- arbitrary type-defs kept and dropped,
silently. The zig arm looks safe by ZigEmitter's own note that nullary
definitions are emitted as nullary functions "so the reference must call"; the
other arms are unverified and this is the first code to depend on it.

**6. Effect names are not collected.** `FunTy` ignores `row.labels[].name` and
`EffectfulTy` ignores `effs : List Name`. Sound only if no effect label ever
shares a name with a type-def -- an unstated assumption, and the two namespaces
share one table.

**7. `AForallType` has no arm** in `ir-tdce-atype` and falls into `otherwise`,
dropping both nested `ATypeExpr`s (`Ast/AstNodes.codex:105`). Mitigated -- the
wire prints it as `(a-forall)` and `resolve-type-expr` maps it to `ProofTy`, so
those names never crossed the wire -- but it is a silent hole, not a documented
one.

## Not correctness, but owed

- **A children-fold for `CodexType` already exists** and is not reused:
  `codex-type-fold-children` (`Types/CodexTypeTree.codex:24-41`). The new walk
  is a hand-rolled duplicate that diverges from it. Reuse it, or say why not.
- **Unbounded descent at every IRExpr node.** `ir-tdce-type` descends
  `RecordTy` fields and `SumTy` ctor fields with no fuel and no visited set,
  where `ir-emit-type` stops at name+args and `type-mentions-proof` carries
  FUEL. Cycles look impossible (the type-def map resolves against the partial
  map, so inlining points backward) but a late record structurally contains
  every earlier one it mentions.
- **Allocation, immediately before a documented exhaustion point.** Each
  `offset-table-empty` materialises 2 x 16384-element lists, and `roots` is one
  monolithic list of every value and type name in every def. The prose at
  `IRTextEmitter.codex:1082` records allocator exhaustion at emit time on a
  17-cite program at BOTH 3072 MB and 6144 MB.
- **`(ctors ...)` is emitted unpruned while type-defs are pruned**
  (`emit-ir-chapter-prefix`). The wire can now name a constructor with no
  `(type-defs)` entry. `RecheckPlug.codex:81,92` consumes exactly that pair and
  is the first place to look for a behaviour change.
- **Targets now disagree about the type-def list.** The IR-text target prunes;
  `CtCodexText`, the header-printing paths and the x86 path still receive the
  full list. Probably intended; recorded because it is new.
- Two source comments are wrong: "adds and modifies nothing" is inaccurate for
  `opening.codex` (8 lines), and the comment claiming constructors are rooted
  sits on `ir-tdce-expr` while the property actually lives in
  `ir-tdce-value-names`.

## WHY THE GATES WERE BLIND, which is the part worth keeping

**A missed root fails SILENTLY downstream.** `sum-ctors-by-name` returns `[]`
on a miss (`plugs/common/IRTextParser.codex:482-489`); ZigEmitter builds its
ctor map from the PRUNED list and `zig-find-ctor` returning `-1` reclassifies a
constructor as a plain value name. So under-collection produces wrong-or-
uncompilable zig, not a diagnostic.

Everything run against this change was either a regex over text (the type gate,
the harness check, the comparison script) or a sample of programs that do not
contain the shapes above. **A corpus that passes tells you the corpus lacks the
shape, not that the pass is right.**

And the first measurement of all came back green over a corpus where nothing
had been pruned at all, because the ladder's harness generators kept their own
copy of the driver's emit call. That is fixed and now gated
(`check_harness_gates.py` compares the `ir-prune-unreachable*` names around
each emit call against the driver's, verified to fire), and it is the origin of
[[feedback_green_because_it_never_ran]].

## What to do when it is picked up

1. Write a probe per open defect FIRST -- each needs a program with the shape
   (two chapters declaring the same ctor; a multi-instance class; a GADT-style
   constructor return type; an empty-defs chapter). Confirm each probe FAILS
   before fixing anything.
2. Fix 1-4 at least; 5 needs a decision about whether to depend on nullary
   re-evaluation across all arms, or to thread one table instead of building
   two.
3. Reuse `codex-type-fold-children`, or record why not.
4. Re-measure on `typedef-prune-on-shaker`, re-run the tier set, and run the
   14 rungs -- which need the truth arm COMPUTED for the branch
   (`ast/truthcycle_*.sh`, ~27 min of guests), then `allcycles.sh`. **No bank
   is required**: the property is arm-versus-arm on the same tree, and
   `restore_truths.py` is only a cache for skipping the recomputation.

**THE LADDER HALF IS REVERTED ON MASTER, AND MUST BE RE-APPLIED WITH THE
BRANCH.** `9220f84` taught both harness generators to mirror the driver's
type-def prune. The driver half lives only on `prune-unreachable-typedefs`, so
master was left calling `ir-prune-unreachable-typedefs`, a name no released
Update defines -- and `native_build.sh` therefore could not build `codexir`
against ANY release: `CDX3002: Undefined name`, 92 seconds in. Found running
the Update 53 natives. Reverted here; when the prune is picked up, revert the
revert in the same change that lands the driver half. `check_harness_gates.py`
catches the mismatch in either direction and exits 1, so the pairing is
enforced rather than remembered.

