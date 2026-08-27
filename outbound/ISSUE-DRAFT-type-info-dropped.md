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

## What we tried, and what it cost

We built the local workaround first, because it was available to us without
touching your compiler: recover a lambda parameter's type from a typed use in
the lambda's own body, or from the callee's declared parameter when the
argument is only passed onward. It works. Against the depot's own test
corpus it moved four programs from "refuses to emit" to "runs and matches
the expected output", including two ported Roc snippets checked against
Roc's own expected values.

**We do not think it is the right fix, and the reason is what did NOT move.**
Three programs still refuse, and each needs a *different* new inference rule:

- a parameter that is never used and never passed (`\ignored -> xs`) — its
  type is only visible from how the *binding* is applied, elsewhere;
- a parameter that is ignored inside the lambda but whose full arrow type is
  known at the site where the closure is *passed* — the definition does not
  know what its own caller knows;
- an empty list's element type, which is not a lambda parameter at all.

Local recovery does not converge, because the information is not local. It
was global, the checker had it, and it was dropped. Every plug that wants it
must now re-derive it independently, with its own bugs — and two plugs have
already got it wrong.

## What we are not claiming

- **We have not fixed it.** We wrote a patch — record the lambda's own type
  in `infer-lambda` against its span, and have `lower-lambda` ask for it when
  and only when its expectation is `ErrorTy` — and it produced **byte-identical
  IR**, with the patch measured to be in the build. We do not yet know why,
  and we are instrumenting rather than guessing. We may be wrong about where
  the right seam is.
- **We have not tested core-compiler changes properly.** We have no depot
  gate, and a change in `Lowering.codex` touches every backend. Anything we
  propose here needs your verification, not ours.
- **We are not speaking for the other plugs.** The Ada and Fortran readings
  above are source reads, not runs. We have not built either.

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
