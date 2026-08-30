"""The ONE list of arc-tangent inputs, and the two programs that read it.

Both arms are generated from this file so they cannot drift. A hand-kept list on
each side is a measurement with a silent failure mode: the two lists disagree,
every value still matches, and the report says the implementations agree.

Chosen to hit the places an argument-halving atan can go wrong rather than to
look thorough:

  * |t| just under, at, and just over 1.0 -- the reciprocal branch's seam, and
    where a direct Taylor series would be hopeless (which is why halving);
  * |t| near 3, which the driving port's outer columns actually reach at a
    pulled-in focal, so the reciprocal branch is live and not defensive;
  * both signs of every magnitude, because the fold is written twice;
  * 0 and the far tails, where the answer is a limit.
"""

ATAN_INPUTS = [
    "0.0",
    "0.000000001", "0.0001", "0.01",
    "0.1", "0.25", "0.5",
    "0.7071067811865476",
    "0.9", "0.99", "0.999", "0.9999999",
    "1.0",
    "1.0000001", "1.1", "1.5", "2.0",
    "2.7182818284590452",
    "3.0", "3.1415926535897932",
    "10.0", "100.0", "1000000.0",
    "-0.000000001", "-0.01", "-0.1", "-0.25", "-0.5",
    "-0.7071067811865476",
    "-0.9", "-0.99", "-0.999",
    "-1.0",
    "-1.0000001", "-1.1", "-1.5", "-2.0", "-3.0",
    "-10.0", "-100.0", "-1000000.0",
]

# (y, x) -- the quadrant cases, including the three axes and both zeroes.
ATAN2_INPUTS = [
    ("1.0", "1.0"), ("1.0", "-1.0"), ("-1.0", "1.0"), ("-1.0", "-1.0"),
    ("0.5", "2.0"), ("2.0", "0.5"), ("-0.5", "2.0"), ("-2.0", "0.5"),
    ("0.5", "-2.0"), ("2.0", "-0.5"), ("-0.5", "-2.0"), ("-2.0", "-0.5"),
    ("1.0", "0.0"), ("-1.0", "0.0"),
    ("0.0", "1.0"), ("0.0", "-1.0"),
    ("0.0", "0.0"),
    ("3.0", "4.0"), ("-4.0", "3.0"),
]

# No literal here may reach the wrapping accumulator reported as Cobblestone
# issue 106: written out, a Real literal's digits are accumulated into one i64.
# The widest above is 17 significant digits (~7.07e15), well inside i64.
for _v in ATAN_INPUTS + [s for p in ATAN2_INPUTS for s in p]:
    _digits = _v.replace("-", "").replace(".", "").lstrip("0")
    assert len(_digits) < 19, f"literal {_v} is wide enough to trip issue 106"
