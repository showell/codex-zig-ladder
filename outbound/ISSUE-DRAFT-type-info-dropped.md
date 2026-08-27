# The compiler computes lambda parameter types and the IR does not carry them

*Draft for a GitHub issue on `damiant3/Cobblestone`. Written by Claude, on
Steve Howell's account and at his direction. Not yet sent.*

---

## The claim

The IR discards type information the compiler has already computed, and the
discard is **invisible to almost every backend in the fleet** — so nothing in
the project's own verification can see it. Bare metal does not care whether a
value is an `Integer`, a `Text` or a pointer; it is a register either way.
The two artifacts this project trusts most — the x86 reference and the C#
diverse-double-compiling witness — are, by construction, the two that cannot
feel this loss. The result is an IR shaped around backends that erase types,
validated by backends that erase types, and **it has already produced wrong
code in backends that do not.**

We are not asking for the zig plug to be given special treatment. We are
reporting that zig is the first backend in the fleet that can neither erase
the missing type nor guess it, which is why it is the one surfacing this.

## The specific fact

`infer-lambda` (`Types/TypeCheckerInference.codex:488-498`) computes the
lambda's complete function type — `wrap-fun-type (pr.param-types) lam-row
(br.inferred-type)` — and returns it as `inferred-type`.
`bind-lambda-params` (`:506-516`) binds each parameter to a fresh type
variable, unification solves them, and the solution is sitting in the
`UnificationState` that call returns.

Lowering does not ask. `lower-lambda` (`IR/Lowering.codex:722-724`) peels the
parameter types off the type its **context expects**, and `peel-fun-param`
(`Types/CodexTypeHelpers.codex:4-10`) answers `ErrorTy` for anything that is
not an arrow. When there is no contextual expectation — `lower-let` hands its
bound value `ErrorTy` (`:689`) — every parameter peels to `ErrorTy`, and
`lambda-recorded-ty` stores the arrow with `ErrorTy` in each position.

So the type is not lost. It is **computed, returned, and then re-derived by a
second, worse method**, and the second method's failure is what reaches the
plugs.

## Why `ErrorTy` specifically makes this worse

`ErrorTy` is the compiler's TYPE FAILURE atom. `lower-let` also uses it as
its *no expectation* sentinel. Those are different facts wearing one
spelling, and the collision reaches the wire: a plug reading `(param "x"
error)` cannot tell

- "the checker failed on this program" from
- "the checker succeeded and nothing wrote the answer down",

and in practice it is always the second, because the program compiled clean.
Every plug in the fleet is being told a type error occurred, on programs the
compiler reported as correct.

## What the fleet actually does with it — the evidence this is already costing you

Of the plugs that face a `CodexType` at all, four have an explicit arm:

| plug | answer | what that is |
|---|---|---|
| C# | `object` | erase — the target has a universal dynamic type |
| Rust | `Box<dyn std::any::Any>` | erase — same |
| Ada | `Long_Long_Integer` | **guess** |
| Fortran | `integer(8)` | **guess** |

`CSharpEmitterExpressions.codex:64`, `RustEmitter.codex:57`,
`AdaEmitter.codex:134`, `FortranEmitter.codex:148`.

**The two guesses are wrong, and we have a test that proves it.** A lambda
parameter whose true type is `Text` reaches those plugs as `ErrorTy` exactly
as an `Integer` one does, and both answer with a 64-bit integer type. Six of
the seven cases in our probe matrix have `Integer` as the true answer — which
is also the language's default — so a defaulting plug looks correct on almost
everything. We wrote case f as a `Text` specifically so that a guess fails
visibly, and it does.

This is not four plugs honouring a contract. It is four workarounds for one
missing fact, two of which silently miscompile.

The rest of the fleet does not have an arm because it does not need one: x86,
arm64 and RISC-V erase everything into registers, the dynamic-language plugs
(Python, JavaScript, Scheme, Elixir, …) never ask for a type, and the smaller
typed plugs erase wholesale — `JavaEmitter.codex` is 397 lines and routes
records through `HashMap<String,Object>`.

**That is the architectural point.** The information is missing for everyone.
Only a backend that is both typed and complete enough to have no escape hatch
can detect it, and until the zig plug got that complete, no such backend
existed.

## It is a pattern, not one bug

Three independent places where a type the compiler knows arrives at a plug as
something it cannot use, all found in one afternoon on one small test suite:

1. **Lambda parameters** — the above.
2. **Empty list element types.** `(list error)` on the wire for a program
   where the element type is fixed by the very next line. An empty list can
   never answer for itself; the checker resolves it and the IR does not
   record it.
3. **Type variables reaching a plug from polymorphic definitions** —
   `(fn (tvar 44) (tvar 45))`, `(ctd "Step" (args (tvar 16)))`. Fine for a
   backend that erases; unemittable for one that does not, and no
   monomorphisation happens anywhere.

Each is harmless for an erasing backend and fatal for a typed one. That
correlation is the whole of our claim.

## The fix, measured

`infer-lambda` should record the type it already computes, and `lower-lambda`
should ask for it when — and only when — its expectation is `ErrorTy`. That
is four lines, and on its own it does nothing at all: we wrote it and it
produced **byte-identical IR**.

The reason is one line further out, and it is the actual root cause:

    Syntax/SyntaxNodes.codex:23    | LambdaExpr (List Token) (Expr)

**The lambda is the only expression node in the CST with no span.** Its
neighbours all carry one — `ListExpr` has a span field, and
`RecordExpr`/`FieldExpr`/`HandleExpr`/`WithTimeoutExpr`/`TryExpr` each carry
their keyword token. So `Ast/Desugarer.codex:55` has nothing to pass and
writes `synthetic-span`, and `is-synthetic-span` is `span.file-id == 0`,
which gates **both** ends of the mechanism:

    Types/Unifier.codex:147   record-expr-type   if is-synthetic-span sp then st
    Types/Unifier.codex:178   lookup-expr-type   if is-synthetic-span sp then ErrorTy

Every lambda in the language is filed under file-id 0, which is to say not
filed, and any lookup against it returns `ErrorTy`. The side channel
`lower-dict-placeholder` already uses successfully twenty lines above
`lambda-expected-ty` is structurally unavailable to lambdas, and has been the
whole time.

Give the CST node its lambda token the way its neighbours carry theirs, pass
`token-span` in the desugarer, and the four lines start working. Our branch
is five sites: the node, its `copy-sx` arm, an or-pattern in `ParserCore`,
the two parser construction sites, and the desugarer.

**Result on the seven-case matrix**, `(param ...)` cells of the lifted
lambdas, before and after:

| | before | after |
|---|---|---|
| cells reading `error` | 6 of 11 | **0 of 11** |
| case c, `\i -> i` applied to an Integer | `error` | `int-default` |
| case d, a lambda literal's function argument | `error` | `(fn int-default int-default)` |
| **case f, `\s -> s & "!"` applied to a `Text`** | `error` | **`text`** |
| case g, bound and never applied | `error` | `(tvar 305)` |

Case f is the one that matters: every other case's true answer is `Integer`,
which is also the language default, so it is the only cell that distinguishes
recovering the checker's answer from defaulting to a plausible one. It
recovers.

Case g is the one that should *not* recover — nothing constrains that
parameter — and it does not. It comes back as an unsolved type variable,
which is what an unconstrained parameter is. That is strictly more honest
than `ErrorTy`, which claims a type failure in a program you report as clean.

Both control cases — the same lambda at a *declared* parameter, which is
correct today — are byte-identical before and after, so the change reaches
exactly what it claims to.

## What we are not claiming

- **We have not tested this the way you would.** We have no depot gate, and a
  change in `Lowering.codex` touches every backend. The measurement above is
  the IR wire for one seven-case matrix, not your test suite.
- **We are not speaking for the other plugs.** The Ada and Fortran readings
  are source reads. We have not built either.
- **The two other lambda sites still desugar synthetic** — `ForExpr`'s
  `map-list` lambda and instance-method synthesis. Each has a real token
  available and neither is in our branch, because our matrix does not measure
  them.

## Reproducing it

`findings/probe-h2-lambda-types.codex` in our ladder repo is a seven-case
matrix, one lambda shape per case, with two genuine one-respect control pairs
(a lambda at a *declared* parameter is correct today; the same lambda
`let`-bound is not). Its expected values are banked from bare metal. Case f
is a `Text` so that defaulting fails visibly; case g is unconstrained by
construction, so `error` is the honest answer there and the only place it
should appear.

Compiling it in `IR-CCE` mode and reading the `(param ...)` cells of the
lifted `__lam_N` definitions is the whole measurement.

## What would help

Not a specific patch — a ruling on the architecture. Should the IR carry the
checker's solved types on lambda parameters, and should `ErrorTy` on the wire
be reserved for actual type failures? If the answer is yes, we would rather
help with that than keep teaching one plug to guess.
