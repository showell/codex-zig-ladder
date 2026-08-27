# What the build of `11df612c` must show -- finding 64

Written before the build. One compiler change since `dafb148f`:
`token-span (m.name)` in place of `synthetic-span` for an instance method's
lambda (`Desugarer.codex:1455`), which is one of the two sites PR 93 excluded.

Measured on the MEASUREMENT branch `roc-ports-batch2`, now a child of the fixes
branch, so the corpus population is described by a ref.

## The lambdas -- what the fix is FOR

    typeclass-smoke __lam_2   (param "b" (tvar 16))  ->  (param "b" boolean)
    typeclass-smoke __lam_1   (param "x" (tvar 16))  ->  (param "x" int-default)

Both bodies already type the name concretely -- `(if (name "b" boolean) ...)`
and a `show` on an int -- so this is H2's case c and the parameter cell should
now agree with its own body.

## The dictionary -- SEPARATE, and predicted NOT to move

    (def "Showable-dict-Integer" ... (record-ty "ShowableDict" (args (tvar 511))))
    (def "Showable-dict-Boolean" ... (record-ty "ShowableDict" (args boolean)))

**Prediction: `Showable-dict-Integer` stays `(args (tvar 511))`.** The
dictionary's type argument comes from the instance declaration, not from the
method lambda's span, and nothing in this change touches it. **If it DOES move,
the fix reaches further than its own argument claims and the reason has to be
found before it ships** -- that would mean the span was feeding something the
analysis did not account for.

## Therefore the programs are predicted to stay RED

    typeclass-smoke   markers -> markers
    typeclass-poly    markers -> markers

with the `unresolved type variable T16 of __lam_N` markers GONE and the
`type variable T511 / T298 is not declared at this site` markers REMAINING,
because those name the dictionary and not the lambda. **A clean `clean` here
would be a surprise and would need explaining, not celebrating.**

## Must not move

    the 26 other Roc ports          unchanged
    tvar-in-declared-type           clean / match
    blast radius                    small, and every mover explicable

`typeclass-smoke` and `typeclass-poly` are the only two programs in the corpus
whose markers name an instance-method lambda, so anything else moving is
unexplained by construction.
