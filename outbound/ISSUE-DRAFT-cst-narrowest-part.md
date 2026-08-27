# Where this compiler loses information: four places, one shape

*Written by Claude, on Steve Howell's account and at his direction. This is an
ARGUMENT and a set of LEADS, not a patch. Every claim below is labelled
**MEASURED** or **LEAD**; nothing unmeasured is presented as fact, and the
distinction is in the text rather than in a footnote because your agents will
read this without either of us in the loop to qualify it.*

*A separate PR carrying three verified compiler fixes follows once the mirror
push lands. This issue deliberately contains no patch.*

---

## The claim

COMPILER-30 was not a one-off. It is the first instance we found of a shape
that recurs: **a CST node too weak to carry what the source plainly says.** The
programmer writes a fact down, the node cannot hold it, and every later stage
reconstructs it by a worse method or gives up.

Four places. Three we have measured; the fourth is already in your rulings
queue.

## 1. `LambdaExpr` had no span — MEASURED, and landed as COMPILER-30

Recorded here only because it is the pattern's first instance and dates it. A
lambda was the sole expression node with no span field, so it desugared to
`synthetic-span`, and `is-synthetic-span` gated both `record-expr-type` and
`lookup-expr-type`. Every lambda in the language was filed under file-id 0.

## 2. `InstanceDef.type-name` is a `Token`, so a compound instance head is discarded at PARSE time — MEASURED

```
InstanceDef = record { class-name : Token, type-name : Token, methods : ... }
```

A single token cannot hold `(List Integer)`, and the parser does not try:

```
parse-instance-type-head (st) =
 if is-left-paren (current-kind st)
  then let st1 = advance st
   in (current st1, skip-to-close-paren (advance st1) 1)
 else (current st, advance st)
```

`instance Showable (List Integer)` arrives as the bare token `List`, its
argument skipped. On the wire the specialised method is named `to-text-List`,
which is that token and nothing else.

**The consequence, measured.** `synth-instance-defs` reads
`token-text (id.type-name)`, builds the dictionary's NAME from it, and emits
the definition with `declared-type = []`. So the dictionary's type argument is
whatever the METHOD BODIES happen to pin, and the instance head asserts a type
the definition never carries:

```
(def "Showable-dict-Boolean" ... (record-ty "ShowableDict" (args boolean)))
(def "Showable-dict-Integer" ... (record-ty "ShowableDict" (args (tvar 511))))
```

A dictionary NAMED `-Integer` typed with a free variable, beside a Boolean
sibling that is concrete. **The asymmetry is not about the head; it is about
the body.** `to-text (b) = if b then "yes" else "no"` branches on a Boolean and
pins it. `to-text (x) = show x` calls a polymorphic function and pins nothing.

**We isolated it with a one-respect pair** rather than inferring it — same
class, same arity, same return type, differing only in whether the body pins:

```
instance Tellable Integer   tell (x) = "int"                    -> args (tvar 289)  FREE
instance Tellable Boolean   tell (b) = if b then "y" else "n"   -> args boolean     CONCRETE
```

If the head reached the dictionary, both would be concrete.

It explains every instance in `codex/test/typeclass-smoke.codex` without
exception, including `Showable (List Integer)` (`list-length` pins nothing) and
`Equatable Integer` (`==` pins nothing).

## 3. `ErrorTy` is two facts in one spelling — yours, already queued

Noted for completeness because it is the same disease: the type-FAILURE atom
doubling as `lower-let`'s no-expectation sentinel means a plug reading
`(param "x" error)` cannot tell a failed check from an unwritten answer. We are
deliberately not patching it on our side either.

## 4. The IR carries instantiations at CALL SITES and not at definitions — MEASURED

Not a CST gap, but the same information-loss shape one stage later, and it is
ours to work around rather than yours to fix — included because it is evidence
about where the wire is thin.

```
fn hamt_empty(comptime T58: type) HamtMap(T58)     called as  hamt_empty()
fn hamt_set(comptime T65: type, m: HamtMap(T65), ...) called as hamt_set(i64, m0, ...)
```

Our emitter derives a type argument from the VALUE arguments, which works for
`hamt_set` and cannot work for `hamt_empty`, whose parameter appears only in the
return type. The instantiation IS on the wire at the call site —
`(ctd "HamtMap" (args int-default))` — so this one is our bug, and we have
fixed it. We mention it because it is the third place where the answer existed
and the consumer was reading the wrong end.

## The question we cannot answer from outside

**What should a backend emit for a type the program genuinely does not
constrain?** `cl-is-empty (cl-nil)`; an empty list whose length is all that is
ever asked; a lambda bound and never applied.

By parametricity, if the variable is genuinely free then no observable
behaviour depends on the choice, so defaulting is correct compilation rather
than a hack. **The difficulty is that we cannot tell when the premise holds.**
On the wire, "genuinely free" and "we lost it" are spelled identically — and
four times this week the honest reading was the second.

**Our recommendation, and we would rather argue it than patch it:** the
compiler knows after unification whether a variable is free or solved, and that
distinction should be on the wire. A plug seeing a FREE marker may default with
confidence; a plug seeing a bare variable knows it is inside a generic; a plug
seeing `ErrorTy` knows something is wrong. One spelling for two facts is what
makes a backend guess.

**And a note on which default, if we ever do default: a zero-sized type, never
an integer.** If the premise holds it is as correct as any other; if the premise
is violated it fails to COMPILE rather than producing a wrong answer. An
integer default is the Ada/Fortran row of the table in PR 93 — correct on the
theorem, wrong on the premise, silent when it matters.

## Leads, explicitly not findings

**LEAD — a fix for the simple half of §2 works and breaks something else.** We
gave the synthesised dictionary a `declared-type` where the head is provably
nullary (a declared type with no parameters, or a nullary builtin), leaving
compound and parametric heads alone. Measured: `Showable-dict-Integer` and the
probe's `Tellable-dict-Integer` both move to `int-default`, controls unmoved,
and nothing with a compound head acquires a type. **But `typeclass-poly` gains a
refusal it did not have** — `unresolved type variable T319 of
Sortable-dict-Integer` — and it is the only one of our three subjects with a
superclass (`class Equatable a => Sortable`), so its dictionary carries a
`__super-` field pointing at another dictionary. **We do not understand why the
superclass chain declines the declared type and are not shipping it.**

**LEAD — Codex permits polymorphic recursion.** A definition calling itself at
`List (List a)` compiles clean; the recursive call is typed one level deeper
than the definition. We mention it because it bears on any monomorphisation
design: the instantiation set is infinite in general, so specialisation cannot
terminate without an arbitrary cap. Our own backend is going the comptime route
because of it. If that is a known and intended property, ignore this; if it is
not, it may interest you.

## What we are not claiming

- **No depot gate.** Our oracle is 14 rungs against a bare-metal bank plus your
  own test corpus, on the zig arm alone.
- **§2's fix is not offered.** The simple half breaks a superclass case; the
  compound half needs `InstanceDef` to carry a type expression and the parser
  to stop skipping, which is a parser and node change we would rather see
  argued than write blind.
- **We have been wrong three times today** about mechanisms in exactly this
  area — the instance-method lambda's diagnosis, a discard rule's scope, and a
  falsifier we had to withdraw before its own build. Each was settled by a
  measurement after prose had already been written. Everything above marked
  MEASURED has a wire reading or a source citation behind it; everything marked
  LEAD does not, and should be read as an invitation rather than a report.

*Ladder: `2bfac41`. Probe fixtures are public:
https://github.com/showell/codex-zig-ladder*
