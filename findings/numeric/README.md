# The standing numeric oracle

**The foreword's docstrings are a specification nobody checks.** `Math chapter
Cordic` claimed ~0.1% accuracy for however long and delivered 0.54% of scale, or
3.68% relative, and nothing in the depot or in this repository compared those
numbers. That is what this is for.

    ./catalog.py            grade every routine that needs no guest
    ./catalog.py cordic     just one

## Two things are graded, and they are different

What the routine **computes**, against mathematical truth. And what its
documentation **claims**, which is a separate assertion that can be wrong on its
own. A chapter whose numbers are fine and whose docstring is off by 37x has one
defect, not none.

**An accuracy figure means nothing without saying which accuracy.** Near a zero
crossing a small absolute error is a large fraction of a small value; near a peak
the reverse. Cordic's worst error is 0.54% of full scale AND 3.68% relative --
the same measurement. So a `Claim` carries a `reading`, and `UNSTATED` is a
verdict rather than a gap: a claim that does not say which reading it means
cannot be checked at all.

## A model must say how it was shown faithful

`grade()` refuses without `validated=`. An integer fixed-point routine
transcribes exactly into Python, which is what makes this free of box time -- and
a transcription nobody checked produces numbers indistinguishable in print from
measurements.

The Cordic model was validated twice before it was allowed to correct a
docstring: it reproduces all 18 cordic values in the depot's own committed
`math-cordic-quadrants.expected`, and bare metal agreed with it on all 20 angles
of the new `math-cordic-accuracy`. **The first draft of `catalog.py` shipped a
hand-transcribed `geo-sin` reporting a worst error of 7.5%, checked against
nothing.** The refusal exists because of that, and Geodesic is absent until its
model earns its place.

## Where the guest-needing half lives

A routine whose answer depends on emitted code cannot be modelled, and belongs in
a bare-metal rig instead. `findings/atan/` is the worked example: one input list,
two generated arms, f64 bit patterns compared, and a comparison that refuses if
the two sides name different inputs. It graded a Real arc tangent against zig's
libm at 6.7e-16 worst error, four ULP.

The split is not about difficulty. It is about what the reference can be: real
`sin` is available in Python, and what a plug emits is not.
