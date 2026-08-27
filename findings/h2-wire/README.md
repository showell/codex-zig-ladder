# H2: what the canary answered, and the root cause it led to

The two wires here are the load-bearing measurement of 2026-08-27. They are
banked because they live in `~/runs` sandboxes otherwise, and those are not
durable.

    wire-pin-012a9d2e.txt      the Update 51 pin, no patch      7,935 bytes
    wire-canary-c6cd236a.txt   the canary compiler              7,916 bytes

Both read with `./h2_wire.py findings/probe-h2-lambda-types.codex`, from
`native/codexir` built in each tree, same harness (`ast/CodexIrHarness.codex`
is byte-identical between ladder `9cad748` and `7eb4b5f`), same probe
(md5 `5fac969068db51eb130afcf0ad4fb006`).

## The verdict, and why the cell table undersold it

The canary made `lambda-expected-ty` answer `TextTy` when its lookup misses.
Its driver grepped the parameter cells and reported

    VERDICT: the arm FIRES and the lookup MISSES

which is the right answer, reached for the wrong reason: only ONE parameter
cell moved (`__lam_3 step`), and that one is not even a direct hit. The
evidence is in the full wire, not the cell table.

**Five lifted lambdas moved, all in the RESULT position of their recorded
type**, `(fn error error)` -> `(fn error text)`: `__lam_0`, `__lam_2`,
`__lam_4`, `__lam_6`, `__lam_7`. So the `is ErrorTy` arm fired on every one
of them and the lookup missed on every one of them.

**The parameter cells could not move, and that is mechanical.** `lower-lambda`
peels parameters off the expected type (`Lowering.codex:725`) and
`peel-fun-param` answers `ErrorTy` for anything that is not an arrow
(`CodexTypeHelpers.codex:4-10`). `TextTy` is not an arrow, so every parameter
peels to `ErrorTy` no matter what the canary returns. The canary marker can
only surface where the expected type is used WHOLE -- the recorded type and
the `let` binding's type, both of which moved.

**`__lam_3 step` is contamination, not a hit.** Case d applies a lambda
literal on the spot, so `__lam_3`'s expectation is assembled from the
argument types, and the second argument is `__lam_4`, whose recorded type the
canary had already turned into `text`. `__lam_3`'s own arm never fired: its
`base` cell is `int-default` in both wires.

**The controls behaved.** `__lam_1` (case b) and `__lam_5` (case e) are
byte-identical across the two wires. Both sit at a declared parameter, so
`ty` is not `ErrorTy` and the arm correctly does not fire.

## The root cause, found in source once the canary said where to look

The parked patch `22e9b2cc` added both halves of the intended fix --
`infer-lambda` records its computed function type (`TypeCheckerInference.codex:497`)
and `lambda-expected-ty` looks it up -- and measured byte-identical. This is
why:

    SyntaxNodes.codex:23     | LambdaExpr (List Token) (Expr)
    Desugarer.codex:55       is LambdaExpr (params) (body) ->
                               ALambdaExpr ... synthetic-span

The CST's lambda is the only expression node with NO span field. Its
neighbours all carry one -- `ListExpr (elems) (sp)`, `RecordExpr` uses
`token-span type-tok`, `FieldExpr` uses `token-span field-tok`, `HandleExpr`
uses `token-span eff-tok` -- so the desugarer has nothing to pass and writes
`synthetic-span`. `is-synthetic-span` is `span.file-id == 0`, and it gates
BOTH halves of the side channel:

    record-expr-type  Unifier.codex:147   if is-synthetic-span sp then st
    lookup-expr-type  Unifier.codex:178   if is-synthetic-span sp then ErrorTy

So the patch stored nothing and the lookup could never have hit. Not a span
MISMATCH -- there is no span at all. Every lambda in the language reaches the
checker keyed under file-id 0.
