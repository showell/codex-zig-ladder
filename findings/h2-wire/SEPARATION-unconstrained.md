# Separating the unused values from the free types

Steve's instruction, 2026-08-27: *"First, separate the unused values from the
free type. Everything else becomes simple busy work after that."*

Done. **The unused-value bucket is EMPTY, and three of the eight programs are
not unconstrained types at all -- they are dropped ones.** So the defaulting
question is smaller than the eight-program marker count suggested, and part of
what looked like it is more of findings 57-59.

Method: for each program carrying a `type variable ...` or `no element type`
marker, find what carries the free variable and ask whether that value is ever
used -- a lambda entered, a value stored or passed, a literal read.

## 1. GENUINELY FREE, and the value IS used -- 2 programs

These are the real question, and they are the whole of it.

    roc-alias-empty   x = [] ; y = x ; length y
                      only the length is ever asked, so no line depends on the
                      element type. Both x and y ARE read.
    list-test         cl-is-empty (cl-nil)
                      is-empty looks at a constructor tag, never a payload.

## 2. ENTERED -- monomorphisation, ours -- 3 programs

    roc-iter-map / roc-iter-keep-if / roc-iter-drop-if
      __lam_0 is in the function position of an apply. The enclosing
      definition is `iter-map : Iter a, (a -> b) -> Iter b`, genuinely
      polymorphic, so the variable is honest and the call site instantiates
      it. Nothing to default; the type argument has to be threaded.

## 3. NOT FREE AT ALL -- the type was dropped -- 3 programs

**`typeclass-smoke` and `typeclass-poly`.** The instance dictionaries lose
their instance type, and the asymmetry is the proof:

    (def "Showable-dict-Boolean" ... (record-ty "ShowableDict" (args boolean)))
    (def "Showable-dict-Integer" ... (record-ty "ShowableDict" (args (tvar 511))))

A dictionary NAMED `-Integer` typed with a free variable, while its Boolean
sibling is concrete. Its method lambda repeats H2's case c exactly:

    (def "__lam_2" (params (param "b" (tvar 16))) (fn (tvar 16) text)
      (if (name "b" boolean) ...))          -- param says tvar 16, body says boolean

and `__lam_1` disagrees with itself in three ways at once: `x` is `tvar 16` in
the parameter list and `tvar 516` in the body, inside a dictionary typed
`tvar 511`. **The unit contains NO `forall` quantifiers at all**, so every one
of those variables is unbound by construction, which is precisely what the
emitter reports.

**`lang-smoke`.** Same shape and it closes a loop:

    (def "__lam_0" (params (param "x" (tvar 25))) (fn (tvar 25) int-default)
      (binary add-int (name "x" int-default) (name "x" int-default) int-default))

    let "doubled" (list int-default)   ... (list-expr (elems (int-lit 1) ...) (tvar 25))

The `let` says `int-default` and the literal it binds says `tvar 25`. **This is
probe case B**, the case `list-elem-prefers-witness` deliberately declines
because its widening clause refuses a numeric witness. Case B was pre-registered
as "must not move" and treated as a curiosity; it is in fact what blocks a core
smoke test, and finding 59 stops one step short of it on purpose.

## 4. UNUSED VALUE -- 0 programs

None. The archetype is matrix case g (`let h = \k -> 1 in n`, `h` never read),
and it is a PROBE, not a corpus program. Every free variable in the corpus sits
in a value that is entered, stored in a record field, or passed as an argument.

## What follows

- **The defaulting question is two programs**, not eight, and both are the
  clean shape: a container whose element type no line depends on. The essay's
  recommendation is unchanged and now cheaper to act on.
- **Three programs belong to the dropped-type family** and want their own
  finding, not a defaulting rule. Defaulting them would have manufactured
  answers for types the checker had solved -- the exact failure the essay
  warns about, waiting in the exact programs we would have applied it to.
- **Probe case B is promoted from curiosity to blocker.** Whatever is done
  about the widening guard should be measured on `lang-smoke`.
