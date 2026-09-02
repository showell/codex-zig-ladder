# plugs 2.02's open half: which arms `zig-pat-switch-value` under-drops

**Status: read from source at U54, NOT measured.** No corpus run, no plug
build. This is an argument with a falsifier at the end, not a result.

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

## WHAT WOULD FALSIFY THE BROAD FIX

One case: an earlier `.Name` arm that does NOT match every value of that
constructor while being trivially guarded. If such a shape exists, dropping a
later capturing arm on the same name loses a live branch, and that IS a
miscompile -- worse than today's loud refusal. Candidates to look for before
touching anything:

  - a nested pattern inside the payload that makes the earlier arm partial
    (does the IR even carry those, or are they lowered to guards?)
  - a range or literal sub-pattern in a payload position
  - anything that makes `zig-guard-trivial` answer True on a guard that is not
    actually total

**That question is answerable by reading `zig-guard-trivial` and the lowering of
nested patterns, and it has not been done.** Until it is, this note prefers the
narrow fix on grounds of caution, not of correctness.

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
