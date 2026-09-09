*Written by Claude, working with Steve Howell, on his account and at his
direction. This is the boundary-cases test you okayed on issue #125.*

## What this is

It extends `codex/test/ops/real-literal-rounding` with five boundary literals
and their correctly rounded `.expected`. The existing twelve lines are untouched.

**Three of the five are RED AT HEAD on purpose**, and that is the point. The
divisor fix this chapter records is correct, but the significand conversion is
not: the digits accumulate into an i64 and `cvtsi2sd` makes that an f64, which
is exact only below 2^53, so a literal needing 16 or more significant digits
rounds twice and lands one ULP off. The `.expected` values are the *correctly
rounded* bits, so `11.700000000000001` and `97.59752277630605` (one ULP low) and
`993.1027217047139` (one ULP high) mismatch on today's compiler. The two
controls stay green: `0.123456789012345` is 15 digits, and `5.8500000000000005`
is 16+ but rounds the right way — it is here to show the defect is
data-dependent, since its sibling `11.7` does not.

Per your note, this lands with the parser fix (COMPILER-57), not before — a
chapter red at head blocks the gate, so it waits on your side until the parsers
round once.

## Provenance of the expected values

The `.expected` bits are the correctly rounded conversion, taken from an
independent front end and cross-checked against Python's `float`, never captured
from the current compiler — capturing would write the bug in as the oracle.
Confirmed both directions: run through a correctly rounded front end all
seventeen lines match; run through today's compiler exactly the three 16+-digit
lines differ, two low and one high.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01YMgqDFdVkFRPR6auf3zfTT
