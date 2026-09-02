# plugs 2.02's open half: which arms `zig-pat-switch-value` under-drops

**Status: the falsifier was found and it fired.** The fix this note first
proposed is WRONG, and so is the one upstream suggested. Both would convert a
loud refusal into a silent wrong answer on a test that already exists.
Everything below is source reading plus one banked corpus verdict; no new run.

## What is open, in upstream's words

They landed our PR 103 and left the row open, saying so in the prose they added
at `ZigEmitter.codex:2101`:

> It answers only for the NULLARY constructor case, so two arms on a
> payload-carrying constructor whose binders are all unused still collide:
> `emit-zig-match-arm` emits a bare prong for those too. That shape is
> under-dropped, which refuses loudly at zig rather than miscompiling.

And in the PR comment: *"the fix is to mirror those two conditions."*

## The three bare-prong cases, read off emit-zig-match-arm

    nsubs == 0                                         -> ".Name => body,"
    nsubs == 1 & (binder == "_" | not (occurs body))   -> ".Name => body,"
    nsubs >= 2 & not (any-sub-occurs subs body)        -> ".Name => body,"

`zig-pat-switch-value` answers only for the first. So cases 2 and 3 are the
under-dropped shapes upstream names.

## Mirroring those two conditions needs the BODY, and that is the catch

Cases 2 and 3 are not properties of the pattern. Whether a binder is used is a
property of the arm's BODY, and `zig-pat-switch-value : IRPat -> Text` is handed
only the pattern. Mirroring them literally means changing that signature and
threading the body to every caller.

## THE BROADER FIX IS SIMPLER AND MAY BE THE RIGHT ONE

For a tagged union, the zig prong value is `.Name` in EVERY IrCtorPat case --
bare or capturing. Zig rejects a duplicate switch value regardless of whether a
prong captures a payload, so two arms on one constructor collide whether or not
their binders are used. Which means:

    is IrCtorPat (name) (subs) (ty) (sp) -> "." & zig-sanitize name

with the `list-length subs == 0` test simply deleted. No signature change, no
body, and it subsumes both of upstream's cases.

**Is dropping a CAPTURING later arm safe?** It is shadowed on the same argument
the nullary case already rests on: an earlier `.Name` arm matches every value
of that constructor, so a later `.Name` arm cannot be reached whatever it binds.
The one thing that could make the earlier arm not match everything is a
non-trivial guard, and `zig-arm-shadowed` already keeps its `zig-guard-trivial`
conjunct for exactly that -- the conjunct PR 103 deliberately kept when its
justifying prose was dropped.

So the broad fix appears strictly better than the narrow one. I want to be
careful saying that, because upstream read this code and suggested the narrow
one, and they may be seeing something this note is not.

## THE BROAD FIX IS WRONG, AND SO IS THE NARROW ONE. Checked 2026-09-02.

The falsifier this section asked for exists, is in the tree, and has a banked
expected output: `codex/test/literal-subpattern.codex`.

    by-int (b) = when b
      is BInt (0) -> 10
      is BInt (1) -> 11
      is BInt (7) -> 17
      is BInt (n) -> 19
      is otherwise -> 99

Four arms, ONE constructor name. Under the broad fix every arm after the first
is "shadowed by `.BInt`" and dropped, so `by-int` answers 10 for every BInt
against an expected `10 / 11 / 17 / 19`. A loud refusal becomes a silent wrong
answer, which is the worst trade available.

**UPSTREAM'S NARROW FIX BREAKS IT TOO**, and I do not think that was intended.
Their condition is "the binders are all unused", and

    zig-pat-binder (p) (i) = when p is IrVarPat (name) (ty) (sp) -> name
                                     is otherwise -> "_"

answers `"_"` for an `IrLitPat`. So `BInt (0)` reads as a bare prong with no
binder, their condition fires, and the arm is dropped exactly as above. The
test conflates "binds nothing" with "must be TESTED for something".

## What the guard shapes actually turned out to be

Of the three candidates this note listed, one was impossible and two were real:

  - **A trivially-guarded but partial arm: cannot exist.** `zig-guard-trivial`
    answers True only for a literal `IrBoolLit True`, which is total by
    construction, and `emit-zig-match-arms` runs only in the `else` of
    `zig-branches-guarded`, so every arm reaching it has a constant-true guard.
  - **Literal sub-patterns: real, tested, and the falsifier above.**
  - **Nested constructor sub-patterns: representable and mishandled** --
    `lower-pattern-at` recurses into subs verbatim, so `Some (Just x)` reaches
    the IR intact.

## SO 2.02'S REAL FIX IS NOT ABOUT SHADOWING AT ALL

`zig-pat-binder` returning `"_"` for everything that is not an `IrVarPat` is the
root. The zig plug does not TEST a literal sub-pattern; it silently treats it as
a wildcard. That is why two `BInt` arms collide in the first place -- both emit a
bare `.BInt` prong -- and it is why widening the shadow test makes things worse
rather than better.

Emit the test, and the arms stop being duplicates. Both other backends already
do it: bare metal calls `emit-pattern-lit-test` on an `IrLitPat` sub
(`X86_64Compound.codex:2208`), and the C# plug emits `cs-bool-lit-text`
(`CSharpEmitterExpressions.codex:1319`). Only zig drops it.

## AND THE ORACLE ITSELF IS PARTIAL, which is a separate finding

`bind-ctor-fields` on bare metal handles `IrVarPat` and `IrLitPat` and ends

    is otherwise -> bind-ctor-fields st scrut-loc sub-pats tys (i + 1) patches

so a NESTED CONSTRUCTOR sub-pattern is skipped: not tested, not bound. The C#
plug recurses (`emit-sub-pattern` calls `emit-pattern` on an `IrCtorPat`) and
gets it right. So for a program matching `Some (Just x)`, C# and bare metal
DISAGREE, and C# is the one that is correct.

THE LADDER CANNOT SEE THAT. Both of its arms ignore nested constructor subs --
bare metal skips them, zig calls them `"_"` -- so they agree, wrongly, which is
exactly the relative-oracle blind spot PRIORITIES describes. The C# plug is the
only witness in the tree, and it is a crib rather than an oracle.

REACHABILITY IS NOT ESTABLISHED. A source grep finds nested constructor
patterns in no test and in one compiler file; `literal-subpattern` covers the
literal case only. So the nested-constructor half may be latent. Whether the
CHECKER accepts the shape at all is the next question and has not been asked.

## Cost note, recorded by upstream and not addressed here

`zig-arm-shadowed` scans backward per arm and allocates a Text per comparison,
so emission is O(n^2) in arm count on a heap with no GC. Bounded at match-arm
sizes today. If the fix above widens what it compares, rendering each arm's
switch value ONCE into a list is the cheap repair, and it should land in the
same change rather than after it.

## What a measurement would need

A corpus A/B on the zig plug: refusal count before and after, and every emitted
`.zig` byte-identical except for programs that actually carry a duplicate arm.
`codex/test/ops/match-shadowed-arm` is the fixture PR 103 added and would need a
sibling carrying a payload-bearing duplicate -- which does not exist yet and is
the first thing to write.
