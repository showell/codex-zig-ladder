# What the build of the finding 65 fix must show

Written before the build.

## The instrument, which is the direct test

`findings/probe-instance-head-type.codex` -- a one-respect pair whose only
difference is whether the method body pins its parameter.

    Tellable-dict-Integer   (args (tvar 289))  ->  (args int-default)   MOVES
    Tellable-dict-Boolean   (args boolean)     ->  (args boolean)       UNCHANGED

Boolean was already concrete by accident of its body; it must stay concrete and
must not change shape.

## The programs

    typeclass-poly    Equatable-dict-Integer (args (tvar 298)) -> (args int-default)
                      Sortable-dict-Integer  (args (tvar 298)) -> (args int-default)

    typeclass-smoke   Showable-dict-Integer  (args (tvar 511)) -> (args int-default)
                      Showable-dict-Boolean  unchanged
                      Showable-dict-List     UNCHANGED and still free

**`typeclass-smoke` is predicted to STAY RED.** Its `Showable (List Integer)`
instance has a compound head, which this change deliberately does not touch, so
at least one free dictionary remains. `typeclass-poly` may clear if it has no
compound head; that is not certain and is not the claim.

**A clean `clean` on typeclass-smoke would mean the change fired on a compound
head**, which is the one thing it must not do.

## Must not move

    the 29 Roc ports, tvar-in-declared-type, and every program with no
    instance declaration at all

This change is reachable only from `synth-instance-defs`, so any mover without
a typeclass instance is unexplained by construction.

---

## AMENDED before the fix was built, from the pre-fix baseline

Baseline taken at `079e21df` (the tree WITHOUT the fix), sandbox
`20260827T204605Z-f65`:

    Tellable-dict-Integer      (tvar 289)      Tellable-dict-Boolean   boolean
    Showable-dict-Integer      (tvar 511)      Showable-dict-Boolean   boolean
    Equatable-dict-Integer     (tvar 298)      Sortable-dict-Integer   (tvar 298)

**It contradicts my stated reason for predicting `typeclass-smoke` stays red.**
I wrote that its `Showable (List Integer)` instance leaves a free
`Showable-dict-List` behind. **There is no `Showable-dict-List`.** The
compound-head instance produces a specialised method `to-text-List` and no
dictionary at all, and the only dictionaries in that unit are `-Integer` and
`-Boolean`.

So the prediction's REASON is wrong, and I do not know whether the conclusion
survives it. Restated honestly, before the build:

- **`Showable-dict-Integer` moves to `(args int-default)`** -- this is the
  claim, and it stands.
- **Whether `typeclass-smoke` goes clean is now OPEN.** Its markers were
  `T511 not declared` plus `T16 of __lam_1/__lam_2`. If T511 was the only thing
  keeping the lambdas' `T16` unresolved, the program may clear; if the lambdas
  have a second cause it will not. I do not know which, and the earlier "must
  stay red" no longer has evidence under it.
- **A clean result is therefore NOT the falsifier I said it was.** The real
  falsifier is narrower and unchanged: **nothing whose head is compound or
  parametric may acquire a declared type.** `to-text-List` must still carry its
  free variable, and no `*-dict-List` may appear.
