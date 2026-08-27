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
