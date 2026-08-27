# What the build of `af119cc5` must show

Two fixes since `8f1b202a`:

    dcc7d1eb  finding 59  a list literal prefers its own elements over a
                          context variable bound nowhere        (COMPILER)
    af119cc5  finding 60  an unused let of a bare name discards nothing (PLUG)

## The probe, and the prediction that is not obvious

    case A  (ctd "StepA" (args int-default))   UNCHANGED -- already fixed by 57
    case B  (list (tvar 19))                   UNCHANGED -- and NOT because
                                               finding 59 missed it

**Case B must still not move, and the reason is now a specific guard rather
than an absence.** Its witness is an `int-lit`, and `list-elem-prefers-witness`
keeps `usable-witness-ty`'s widening clause: a numeric witness must not pin a
literal that still has widening to do. So finding 59 fixes a list whose
elements are a declared type (`hamt-test`) and deliberately does NOT fix one
whose elements are bare integers. If case B clears, the widening guard is not
doing what it says.

## Family B, which finding 59 is for

    hamt-test      markers -> clean       (T25 was unbound anywhere)
    kvstore-test   markers -> clean
    list-test      markers -> clean       (T618)
    lang-smoke     markers -> markers     family B gone, family A remains
    typeclass-poly markers -> markers     same

## Finding 60

    roc-alias-original   refused -> MATCH   answering 6
    roc-alias-list       match -> match     the twin must not move
    roc-alias-triple     match -> match

## What must NOT move

    roc-iter-map / keep-if / drop-if   still `T16 of __lam_0`
    typeclass-smoke                    still family A

Those four are monomorphisation and neither fix touches them. If any of them
clears, one of these changes reaches further than it claims.

    tvar-in-declared-type    match, unchanged, answering 73

## The corpus

Against the `8f1b202a` tree. Expect `clean` up by about three, `codex-refused`
to appear as its own bucket at 13 (the error-gate fix, not a change in
behaviour), and the blast radius to be small and wholly explicable. Every
moved `.zig` gets named and accounted for; an unexplained mover outranks the
wins.
