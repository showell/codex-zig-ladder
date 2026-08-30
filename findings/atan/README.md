# Grading the arc tangent against zig

The measurement behind the `real-atan` offer to Cobblestone's foreword. Run
2026-08-30 against `u53-rebank` (`58b08c38`) and zig 0.16.0.

    ./gen.py                                # writes atan_ref.zig and AtanProbe.codex
    zig run atan_ref.zig 2> zig.txt         # std.debug.print, hence stderr
    # place AtanProbe.codex in a sandbox's codex/test/forewords/ and:
    ./bare_expected.py gpu-devicemath-atan-probe > bare.txt
    ./compare.py zig.txt bare.txt

## The result

    worst absolute error 6.6613e-16   at atan 3.141592654
    worst ULP distance   4            at atan 0.5
    within 1e-15: 60 of 60

`RESULT.txt` is the full table.

**This supersedes a claim that was never backed.** `safari-codex`'s README said
the arc tangent matched zig's "to 1e-9 over eighteen values"; no test, probe or
gold file in that repository ever contained the eighteen values, and the figure
was conservative by seven orders of magnitude. The rig exists so the number is
reproducible rather than remembered.

## Three things it does on purpose

**One input list, two generated programs.** `values.py` is the only place the
inputs are written; `gen.py` emits both arms from it. A hand-kept list on each
side fails silently -- the lists drift, every compared row still matches, and the
report announces agreement because it paired position with position.

**Bit patterns, not rendered decimals.** A float printer is a second
implementation. Two correct printers can disagree about a value they both hold
exactly, and then the comparison is grading the printers. `compare.py` reads i64
bit patterns and does its own ULP arithmetic.

**`compare.py` refuses rather than reports** if the two files do not name the
same inputs in the same order.

## The inputs are chosen to break it, not to look thorough

`|t|` just under, at and just over 1.0 is the reciprocal branch's seam and the
place a direct Taylor series would be hopeless -- which is the whole reason the
implementation halves the argument first. `|t|` near 3 is what the driving port's
outer columns actually reach at a pulled-in focal, so that branch is live rather
than defensive. Both signs of every magnitude, because the fold is written twice.
The axes and both zeroes for `atan2`.

Every literal is asserted under 19 significant digits, so none of them reaches
the wrapping accumulator reported as Cobblestone issue 106. Measuring an arc
tangent through a defect we filed the same morning would be a poor showing.

## Why the depot test rounds

At nano-radian scale, TRUNCATING puts `atan 1e-9` exactly on a boundary -- zero
margin. Rounding moves the tightest value to 0.0088 of a unit against our
6.7e-7 of a unit of error: **13,270x**. The rounding in the test is not cosmetic.
