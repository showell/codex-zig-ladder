# What the wire must say if `bba94d1b` is the fix

Written before the build, so the result cannot be fitted to it. The claim
under test: with the lambda carrying a real span, `infer-lambda`'s
`record-expr-type` actually stores, `lambda-expected-ty`'s `lookup-expr-type`
actually hits, and `peel-fun-param` recovers each parameter from a real
arrow instead of answering `ErrorTy` for a non-arrow.

Compared against `cells-pin-012a9d2e.txt`.

    __lam_0  xs    (list int-default)   UNCHANGED -- the capture always arrived typed
    __lam_0  i     int-default          MOVED from error   (case a, `f 0` applied twice)
    __lam_1  xs    (list int-default)   UNCHANGED -- control b
    __lam_1  i     int-default          UNCHANGED -- control b, already correct
    __lam_2  i     int-default          MOVED from error   (case c, `f n`)
    __lam_3  base  int-default          UNCHANGED
    __lam_3  step  (fn int-default int-default)  MOVED from error
    __lam_4  y     int-default          MOVED from error   (case d)
    __lam_5  y     int-default          UNCHANGED -- control e, already correct
    __lam_6  s     text                 MOVED from error   (case f) -- THE CELL THAT MATTERS
    __lam_7  k     error                UNCHANGED   (case g, never applied)

Readings:

- **`__lam_6 s` is `text`** -- a real recovery. Every other case's true answer
  is `Integer`, which is also the language default, so case f is the only
  cell that separates recovery from a lucky guess. If it comes out
  `int-default`, whatever recovered is a default and not the checker's answer.
- **`__lam_7 k` stays `error`** -- nothing constrains it, so `error` is the
  honest answer and a recovered type there would mean something is inventing
  one.
- **`__lam_3 step` is an arrow** -- this is the cell the plug-side recovery on
  `zig-plug-h2-recovery` had to reconstruct from the callee slot. If the
  compiler answers it, that walk is deleted rather than kept.
- **`__lam_1` and `__lam_5` do not move.** They were already correct, and a
  change in a control means the fix reaches further than claimed.

A cell that comes back as a bare type VARIABLE rather than a type means the
recorded type was read before unification finished and `deep-resolve` is not
doing what `lambda-expected-ty` assumes.
