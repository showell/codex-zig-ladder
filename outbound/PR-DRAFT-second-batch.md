# Second batch: four more places the checker's answer does not reach the IR

*Draft. Authorised by Damian on PR 93, 2026-08-27 19:48Z: "Send all four as the
second PR; that is the word." The register row reserves them for this branch.
NOT YET SENT -- blocked on the mirror push, because all four must be measured
against seed `4341370C` rather than the seed it replaces, and because they
apply onto a base that has COMPILER-30 in it.*

---

## What this is

Four defects of COMPILER-30's family, found while porting Roc's
closure/recursion suite. Each is the same shape as the one you just took: **the
checker computes a type and something between it and the wire drops it.** Two
of them are things PR 93 left explicitly open and you asked to keep.

Every claim below was checked against source rather than against our own notes,
and the discriminator is the one recorded on the row: *did the checker compute
an answer the IR failed to carry?* All four sit on its first side.

## 1. `subst-type-vars-from-arg` cannot learn from a declared parametric type

`IR/LoweringTypes.codex`. The walk has arms for `TypeVar`, `ListTy`, `FunTy`
and `TypeApply`, and `is otherwise -> target`. `SumTy`, `RecordTy`,
`ConstructedTy`, `LinkedListTy`, `VectorTy`, `UnitTy` and `LinearTy` all carry
type children and all land on that floor -- so **a variable inside a declared
`Step a` cannot be learned from any position.**

The visible consequence is a branch join. `lower-if` calls `branch-recorded-ty`
with `if-witness-ty`, `usable-witness-ty` accepts a concrete witness, the
substitution is attempted and comes away with nothing:

    then    (name "Done" (ctd "Step" (args int-default)))     CONCRETE
    else    (apply (name "One" ...) (ctd "Step" (args int-default)))  CONCRETE
    the if  (ctd "Step" (args (tvar 16)))                     A VARIABLE

**The tell that this is a gap and not a design:** `subst-type-var-in-target`,
the APPLYING direction, already walks every variant through
`codex-type-map-children`. Only the learning direction is blind.

The name guard on the three named variants is deliberate -- positional
arguments of two unrelated declared types have nothing to do with each other.

## 2. An empty list literal's solved element type is never recorded

**This is the "empty-list carrier" COMPILER-30 leaves open.**

`infer-list` answers an empty literal with a fresh variable and never calls
`record-expr-type`, so the answer unification later solves has nowhere to go.
`lower-empty-list` then has only the context's expectation and ends at
`is otherwise -> deck-record (IrList [] ErrorTy sp)`.

Smaller than COMPILER-30 was, because the span already exists: `AListExpr` has
carried a real one since the desugarer, unlike a lambda. So this records under
the literal's span and asks for it when -- and only when -- the context supplied
no list type of its own.

## 3. A non-empty list literal prefers a context variable bound nowhere over its own elements

`lower-nonempty-list` consults its elements only when the context offers no
type at all, so a context offering the WRONG type wins unopposed. At a
polymorphic call that context is the callee's declared element type with its
variables still in it.

In `hamt-test`, `collision-set-loop` is `(forall 70)`, its element is
`HamtEntry (tvar 70)`, its target list is `(list (ctd "HamtEntry" (args (tvar
70))))`, and the literal's own element-type slot says `tvar 25` -- **which the
unit binds nowhere.**

This is the fault `lambda-recorded-ty` already guards for lambdas, in its own
prose: a node recording *"the EXPECTED type it was handed, which at a
polymorphic call is the callee's declared parameter with its type variables
still in it."* List literals have no equivalent.

The new predicate is `usable-witness-ty` minus its no-typevars clause, because
here the point is to prefer the variable that is BOUND at this site, not to
erase one. Its other two clauses are kept for the reasons they were written.

## 4. An instance method's lambda is desugared under a synthetic span

**This is one of the two remaining synthetic-span sites COMPILER-30 leaves
open.** `Desugarer.codex`, `synth-instance-fields`. PR 93 excluded it because
nothing measured it. It is measured now:

    (def "__lam_2" (params (param "b" (tvar 16))) (fn (tvar 16) text)
      (if (name "b" boolean) ...))

parameter cell `tvar 16`, body `boolean` -- COMPILER-30's own case c, one
construct over. `__lam_1` disagrees with itself three ways: `x` is `tvar 16` in
the parameters and `tvar 516` in the body, inside a dictionary typed `tvar 511`.
**The unit contains no `forall` quantifiers at all**, so every one of those
variables is unbound by construction.

The asymmetry that rules out honest polymorphism:

    (def "Showable-dict-Boolean" ... (record-ty "ShowableDict" (args boolean)))
    (def "Showable-dict-Integer" ... (record-ty "ShowableDict" (args (tvar 511))))

a dictionary NAMED `-Integer` typed with a free variable, beside a Boolean
sibling that is concrete. The fix is `token-span (m.name)`, available all along.

**`ForExpr`'s `map-list` lambda is still NOT here**, per your row and our own
rule: it waits for an instrument rather than getting a fix nothing measures.

## Measurements

**TO BE RE-TAKEN against `4341370C` before this is sent.** The numbers we have
were measured against `012a9d2e` and we would rather not quote a seed you have
replaced. Expected shape, from the old pin:

- corpus `clean` up by six on 1 and 2 together, with six programs going
  `markers -> match` and nothing moving the other way
- `hamt-test` and `kvstore-test` `markers -> match` on 3
- 4's two programs are `typeclass-smoke` and `typeclass-poly`

## What we are not claiming

- **We have no depot gate.** Our sweep is 14 rungs against a bare-metal bank
  plus a corpus of your own tests, and our arm is the zig plug alone.
- **These were measured with our plug fixes in the tree.** The compiler changes
  here are independent of them, but the corpus numbers are not a measurement of
  your emitter.
