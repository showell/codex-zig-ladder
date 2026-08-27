# What the build of `8f1b202a` must show

Written before the build. Two independent compiler changes on
`roc-ports-type-recovery`, cut from the PR 93 branch so its fixes are under
them:

    dabd84e7  finding 57  subst-type-vars-from-arg learns from declared types
    8f1b202a  finding 58  an empty list literal keeps its solved element type

## The four Roc ports that fail today

    roc-iter-map        markers -> MATCH   (answers 24)
    roc-iter-keep-if    markers -> MATCH
    roc-iter-drop-if    markers -> MATCH
    roc-fold-empty      markers -> MATCH   (answers 42)

Taking the ports from **7 of 11 to 11 of 11**. If a port reaches `clean` but
its value disagrees, the recovered type is wrong rather than missing, and that
is worse than the refusal it replaced.

## The probe

`findings/probe-ctd-subst.codex`, whose two cases fail for different reasons
and must therefore move differently:

    case A  __lam_0  (fn int-default (ctd "StepA" (args (tvar 16))))
            -> (fn int-default (ctd "StepA" (args int-default)))

    case B  __lam_1  (fn int-default (list (tvar 19)))
            -> UNCHANGED

**Case B must not move.** Its branches are non-empty list literals that
themselves carry `(tvar 19)`, so the witness is refused before any
substitution is attempted; finding 58 touches only EMPTY literals and finding
57 only the learning walk. If case B clears, one of these changes reaches
further than it claims and the reason has to be found before it ships.

The probe answers `7` and `9`; `probe-ctd-subst.expected` is banked.

## The corpus

Against the PR 93 baseline in `~/runs/20260827T161748Z-h2-span`, not against
the u51 bank -- the tree under test has PR 93 in it.

    clean 324 -> higher, by at least the four ports above
    NOTHING moves the other way, and no program gains a marker

**The blast-radius argument is the real check.** Count the emitted `.zig`
files that differ from the PR 93 tree's. Finding 57 touches a walk that only
fires when a type has variables to learn, and finding 58 only when a list
literal is empty AND the context supplied no type, so the set that moves
should be small and every member of it should be explicable. A large diff
means one of these fires somewhere it was not meant to.
