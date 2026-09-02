# `real-atan2` and signed zero: our answer to the question on PR 107

**Status: source reading and the IEEE table. NOT run.** No probe has been
compiled on either arm. The recommendation is argued, not measured.

## The question they asked

Upstream recorded the divergence in the chapter rather than fixing it, and
asked us on PR 107:

> `real-atan2` branches on `y >= 0.0`, and `-0.0 >= 0.0` is true in IEEE, so
> `real-atan2 (-0.0) (-1.0)` answers +pi where zig answers -pi, and
> `real-atan2 (-0.0) (1.0)` answers +0.0 where zig answers -0.0. Your table
> covers only positive zeroes, so nothing tests it either way. If you have a
> view on whether we should match zig there, we would take it.

## Our view: yes, match zig -- and it is not two cases, it is four

The function today:

    real-atan2 (y) (x) =
      if x > 0.0 then real-atan (y / x)
      else if x < 0.0 then (if y >= 0.0 then real-atan (y / x) + dm-pi
                                        else real-atan (y / x) - dm-pi)
      else if y > 0.0 then dm-half-pi
      else if y < 0.0 then 0.0 - dm-half-pi
      else 0.0

C99 Annex F.9.1.4, which is where zig's `std.math.atan2` gets its answers,
specifies every signed-zero case. Walking the whole table against the code:

| y | x | IEEE / zig | Codex today | |
|---|---|---|---|---|
| +0 | x > 0 | +0 | +0 | ok |
| -0 | x > 0 | **-0** | +0 | **DIVERGES** (theirs, #1) |
| +0 | x < 0 | +pi | +pi | ok |
| -0 | x < 0 | **-pi** | +pi | **DIVERGES** (theirs, #2) |
| y > 0 | +-0 | +pi/2 | +pi/2 | ok |
| y < 0 | +-0 | -pi/2 | -pi/2 | ok |
| +0 | +0 | +0 | +0 | ok |
| -0 | +0 | **-0** | +0 | **DIVERGES (not named)** |
| +0 | **-0** | **+pi** | 0 | **DIVERGES (not named)** |
| -0 | **-0** | **-pi** | 0 | **DIVERGES (not named)** |

**The three unnamed rows all come from `x = -0.0` and one from `y = -0.0` at
`x = +0`.** `-0.0` satisfies neither `x > 0.0` nor `x < 0.0`, so a negative-zero
x falls into the arms written for x EXACTLY zero -- and for `y = +-0` those arms
answer 0 where the standard says +-pi. That is a whole quadrant boundary, not a
sign-bit nicety: `atan2(+0, -0)` is the direction of the negative x-axis and
should read +pi the same way `atan2(+0, -1)` does.

## Why match zig rather than declare our own convention

1. **The chapter already names zig as its reference.** Its ACCURACY line is
   stated "against zig 0.16.0 std.math.atan", and the prose says the y = 0,
   x = 0 answer "is what a caller comparing against zig's std.math.atan2 will
   expect". A reference you match except on signed zero is a reference with a
   footnote nobody will read.
2. **These answers are not a zig opinion.** They are C99 Annex F, which zig,
   C, Rust, Go, Java and every libm implement identically. Diverging means
   diverging from everyone.
3. **Silent, and in the direction that hurts.** A wrong quadrant on the
   negative x-axis is not a rounding difference; it is pi radians. A renderer
   sweeping an angle through the axis gets a discontinuity that looks like a
   bug in the caller.

## What makes it fixable NOW and did not before

Distinguishing `-0.0` from `+0.0` is impossible with the comparison operators:
that is exactly what `-0.0 >= 0.0` being true means. It needs the SIGN BIT, and
the sign bit needs a bitcast.

`real-to-bits` landed in Update 54 as our own PR 105 (`Types/Builtins.codex:286`).
So the test is now expressible in Codex where it was not at Update 53:

    dm-is-neg-zero : Real -> Boolean
    dm-is-neg-zero (v) = real-to-bits v == real-to-bits (0.0 - 0.0)

or, more usefully, a sign predicate that works for every value:

    dm-signbit : Real -> Boolean
    dm-signbit (v) = real-to-bits v < 0

That is a pleasing loop to close: the bitcast pair went over the wall as a plug
gap, and it turns out to be the thing the foreword needed to state a correct
atan2.

## What we are NOT saying

- We have not measured any of this. The table is read off the standard and the
  source; no probe exists and neither arm has run one.
- We have not checked whether `dm-atan-core` preserves `-0.0` through the
  series, which decides whether row 2 needs a fix at the `real-atan2` level or
  falls out of the sign predicate anyway.
- The infinity rows of Annex F (`atan2(+-inf, +-inf)` = +-3pi/4, +-pi/4) are
  not examined here at all. If signed zero is being fixed, they are the
  neighbouring question and should be asked in the same pass rather than
  discovered later.
