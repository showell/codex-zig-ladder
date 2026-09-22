# Issue 153 -- an empty list literal type-checks as any type

https://github.com/damiant3/Cobblestone/issues/153  (sent 2026-09-22, against Update 61 `3af67f99`, seed `7BCD5BC6BCE0AF41`)

Read cold before sending. The reviewer confirmed the seed IR, the infer-list code and the lowering arm, and caught: the minimal-shapes table cited the non-resolving native build; the control had three diagnostics, not one; 'reaches every back end' and a bare-metal guess were unmeasured; COMPILER-30's invariant is a corpus measurement, so this is new input, not a regression. Its claim that native codexir reports no diagnostics was wrong (it had run `[] + 1`, not the control). Evidence: session scratchpad `u61probe/hole/`, `u61probe/seed/`, `u61probe/min/`, not kept.

## The text sent

TITLE: An empty list literal type-checks as any type: `v : Integer = []` compiles clean

Update 61 (`3af67f99`, seed `7BCD5BC6BCE0AF41`). Also present at Update 60.

The checker gives an empty list literal a bare fresh type variable rather than
a list type, so `[]` unifies with `Integer`, with `Text`, or with anything
else, and the program compiles with no diagnostics. The same looseness puts
`error` on the wire in a clean compile of a nested empty literal (`[[]]`).
COMPILER-81's repair in Update 61 is correct on its own terms; here it closes
a variable that was only unconstrained because of this, which makes the IR
say `Integer` where there is a list.

## Reproducers

Each is a whole unit, cites resolved as `build/compile.ps1` resolves them:

```
Chapter: M
  cites Foreword chapter Console

Section: F

  v : Integer
  v = []

  opening : [Console] Nothing
  opening = act
   print-line-uni (show v)
  end
```

and the same unit with `v = text-length []`, and a control with `v = [1] + 1`.

## What we measured

The seed on bare metal (QEMU), mode `IR-CCE`, Update 61:

| `v =` | diagnostics | IR for `v` |
|---|---|---|
| `[]` | none | `(def "v" "M" (params) int-default (list-expr (elems) error) 0 0)` |
| `text-length []` | none | `(apply (name "text-length" (fn text int-default)) (list-expr (elems) error) int-default)` |
| `[1] + 1` (control) | CDX2001 `List vs Integer`, CDX2003 `Arithmetic operator requires Integer or Real`, CDX2001 `Integer vs List` | none emitted |

So `[]` is accepted as an `Integer` in the first and as a `Text` in the second.

At Update 60 we checked with the checkout's compiler built as a native program
through the Zig plug, stopped at the IR, whose bag halts emission the way the
driver's does: the first two emit the same IR for `v`, and the control halts on
the same CDX2001. (At Update 61 that native build emits the seed's IR byte for
byte on these units.)

We have not run either program; the claim is about what the checker accepts.

## Where it comes from

`Types/TypeCheckerInference.codex:1384-1391`, `infer-list` on zero elements:

```
   in if list-length elems == 0
    then
     let (fr-ty, fr-st) = fresh-and-advance st
     in CheckResult {
      inferred-type = fr-ty,
```

The literal's type is `fr-ty` itself, not `ListTy fr-ty`, so nothing constrains
it to be a list. Our guess at the reason, unconfirmed: `[]` has to serve as
either a `List` or a `LinkedList`, and `empty-list-element-source`
(`IR/Lowering.codex:1458`) accepts either from context. That the literal also
unifies with `Text` suggests the variable is wider than that design needs.

## The nested literal, and COMPILER-30

COMPILER-30 records the invariant "a clean compile carries zero `ErrorTy`" as
holding over the corpus (measured 2026-09-07, 615 clean compiles; closed
2026-09-08), and notes that "the empty-list carrier that produced them is
gone". This is that carrier in a shape the corpus does not contain. A clean
compile of `v = list-length [[]]` on the Update 61 seed:

    (apply (name "list-length" (fn (list int-default) int-default))
           (list-expr (elems (list-expr (elems) error)) int-default)
           int-default)

The outer literal's element type is the inner literal's free variable, so it is
never known to be a list. Lowering finds no list type for the inner `[]` and
takes `lower-empty-list`'s `is otherwise -> IrList [] ErrorTy` arm
(`IR/Lowering.codex:1456`). At Update 60 the outer element stayed an unbound
`(tvar N)`; at Update 61 `rewrite-ir-defs` closes it to `int-default`, so
`list-length`'s argument is typed a list of Integers while its one element is a
list. The Zig plug refuses the program with `no zig type for this codex type`,
at the `error`.

Minimal shapes, the Update 61 compiler built natively:

| expression | inner literal |
|---|---|
| `[[]]`, `[[[]]]` | `error` |
| `[[1]]`, `[[], [1]]`, `[[1], []]` | clean |

Found while verifying Update 61 with a set of programs aimed at COMPILER-81's
`int-default` closure.

---
Written by Claude (Anthropic's model) with Steve Howell, who reviews what is
sent from this account.
