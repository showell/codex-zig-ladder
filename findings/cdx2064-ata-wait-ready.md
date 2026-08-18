# `emit-ata-wait-ready-bounded` patches its loop jcc six bytes late (CDX2064)

Found 2026-08-18 by the zig ladder's diagnostic gate on Update 46 (seed
12B07296), the first compile that gate ever judged. Filed upstream.

## The site

`codex/compiler/Emit/X86_64Boot.codex:3201`, in `emit-ata-wait-ready-bounded`:

    in let dec-pos = st6.code-len
    in let st7 = st-append-code st6 (sub-ri reg-rcx 1)
    in let st8 = st-append-code st7 (jcc cc-ne 0)
    in let st9 = patch-jcc-at st8 (st7.code-len) loop-top      <- line 3216
    in let st10 = patch-jcc-at st9 bsy-set-pos dec-pos
    in patch-jcc-at st10 drdy-set-pos (st10.code-len)

The compiler's own diagnostic, emitted while compiling itself:

    CDX2064: Field 'code-len' is read from 'st7' after 'st7' was updated in
    place by an earlier call bound to a different name; 'st7' now holds the
    updated value, not the original.

## Why the value is wrong

`patch-jcc-at` (`X86_64State.codex`) takes the START of the six-byte jcc:

    patch-jcc-at (st) (jcc-pos) (target-pos) =
     let rel32 = target-pos - (jcc-pos + 6)
     in st-add-deferred-patch (fc-flush st) (make-i32-patch (jcc-pos + 2) rel32)

so the argument wanted is the code length BEFORE the `st8` append. That is what
the same function captures three times for `bsy-set-pos`, `drdy-set-pos` and
`dec-pos`, each one a `let` taken before the append it describes.

`st-append-code` ends in `__record-set st "code-len" new-len`
(`X86_64State.codex:709`), which mutates in place and returns the same record,
so after the `st8` line `st7.code-len` is the length AFTER the jcc. Call the
intended position X. The call therefore runs with `jcc-pos = X + 6`:

| | intended | actual |
|---|---|---|
| displacement written at | X + 2 | X + 8 |
| value written | `loop-top - (X + 6)` | `loop-top - (X + 12)` |

Nothing is appended after the jcc in this function, so X + 6 is where the
caller's next instruction begins. The patch lands four bytes starting two bytes
into that instruction, and the jcc keeps the placeholder displacement of 0,
which falls through instead of looping.

## It is live

`emit-ata-wait-ready-bounded` is called at `X86_64Boot.codex:3279`, in ATA
init.

## The fix, if you want one

Capture it the way the same function already captures the other three:

    in let dec-pos = st6.code-len
    in let st7 = st-append-code st6 (sub-ri reg-rcx 1)
    in let loop-jcc-pos = st7.code-len
    in let st8 = st-append-code st7 (jcc cc-ne 0)
    in let st9 = patch-jcc-at st8 loop-jcc-pos loop-top

This changes emitted bytes, so it moves the fixed point and belongs to whoever
runs the gate rather than to us.

## The part worth more than the site: eight siblings the checker cannot see

The same file spells the same intent a different way in eight places, including
in the two functions immediately above this one:

    X86_64Boot.codex:3164, 3166, 3175, 3177, 3186, 3198, 3326, 3424

each of the form

    patch-jcc-at (st-append-code stN (jcc ...)) (stN.code-len) loop-top

Here the mutating append and the stale read are arguments to ONE call, so
whether `stN.code-len` is the pre-append or post-append value depends on
argument evaluation order, which we did not try to settle from the source.

CDX2064 does not fire on any of them, and reading `TypeChecker.codex:3320-3350`
suggests why: `update-consumed` threads a consumed set across LET BINDINGS and
`rhs-consumes` inspects a let's RHS. A mutation nested inside an argument of the
same expression that reads the field is not a let RHS, so the walk has nothing
to mark stale.

That leaves two possibilities and both are worth knowing:

- the nested form is correct, and CDX2064 has a blind spot that happens to hide
  nothing today but will hide the next one, or
- the nested form is wrong too, and this is nine sites rather than one.

We cannot tell which from here. You can.

## How it surfaced

The ladder compiles compiler subsets under the seed and refuses any diagnostic
code that is not in a table with a reason next to it. This is the first compile
that gate has judged, and CDX2064 was the first unclassified code it saw. The
warning has presumably been emitted on every self-compile since the check was
added; nothing was reading warnings.
