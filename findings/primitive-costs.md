# Primitive allocation costs, both arms, measured

Bytes of heap frontier per operation. Bare metal is the u48 pin compiled to
a `.cdx` and run under QEMU; the zig arm is `findings/prim-lists.codex`
through `codexir` and the `zig-plug-heap-unification` `zigemit` -- the real
plug, not a patched artifact. Reproduce with the recipe in
`findings/probe-memory-model.codex`. Measured 2026-08-21.

| shape | bare metal | zig arm | delta |
|---|---|---|---|
| literal 1 | 24 | 35 | +11 |
| literal 2 | 32 | 40 | +8 |
| literal 3 | 40 | 53 | +13 |
| literal 4 | 48 | 58 | +10 |
| literal 8 | 80 | 95 | +15 |
| capacity 0 | 16 | 27 | +11 |
| capacity 1 | 24 | 32 | +8 |
| capacity 16 | 144 | 157 | +13 |
| capacity 256 | 2064 | 2072 | +8 |
| List Integer 4 | 48 | 56 | +8 |
| **List Text 4** | **48** | **93** | **+45 (1.94x)** |
| cat 1 & 1 | 96 | 105 | +9 |
| cat 4 & 4 | 192 | 204 | +12 |
| cat 8 & 8 | 320 | 335 | +15 |
| chain a&b | 96 | 105 | +9 |
| chain a&b&c | 136 | 188 | +52 |
| **chain a&b&c&d** | **176** | **279** | **+103** |
| cons onto 1 | 72 | 73 | +1 |
| cons onto 4 | 144 | 126 | **-18** |
| cons loop 16 | 2712 | 1633 | **-1079** |
| push loop 4 | 80 | 177 | +97 |
| push loop 16 | 272 | 179 | **-93** |
| push loop 64 | 1040 | 718 | **-322** |
| cat loop 16 | 2136 | 2144 | +8 |
| cat loop 32 | 6296 | 6305 | +9 |
| cat loop 64 | 20760 | 20770 | +10 |

### Tier 4: records and closures (`findings/prim-records.codex`)

| shape | bare metal | zig arm | delta |
|---|---|---|---|
| record, 1 field | 8 | 11 | +3 |
| record, 2 fields | 16 | 19 | +3 |
| record, 4 fields | 32 | 39 | +7 |
| record, 8 fields | 64 | 67 | +3 |
| capturing closure | 16 | 13 | **-3** |
| non-capturing closure | 8 | 0 | **-8** |

**A bare-metal record is exactly `fields*8` -- no header at all**, unlike a
list, which pays `16 + cap*8`. Ours matches modulo the same alignment padding
that shows up everywhere else, so records are NOT a divergence source. That
matters for the `Text` narrowing: shrinking a text handle shrinks every record
field holding one, and the record machinery around it already agrees.

Closures are two more rows where we are cheaper -- we allocate nothing for an
empty capture context where bare metal spends 8. Same fidelity-not-victory
pattern as `cons` and `push`.

All eight SEMANTIC assertions are identical across arms, including the three
that pin finding 10: an update through `__record-set` is visible through the
original name and through an alias taken before it. One object, mutated in
place, on both arms. `mutable` promises value semantics neither delivers.

## What the table says

**The floor is +8, and it is our list header.** Bare metal's list is one
block, `16 + cap*8`, header inline. Ours is a 24-byte `CxList` plus an exact
buffer. Every list-shaped row carries that 8 and nothing more, once padding
is accounted for.

**Alignment padding is real and was not in any model.** The +11/+13/+15 rows
are +8 plus 3 to 7 bytes: `alignment.forward` rounds the frontier up for an
8-aligned `CxList` when the previous allocation was byte-aligned text. Bare
metal does not pay this. It only became visible on numbers small enough for
a stray 3 to be conspicuous.

**`List Text` is 1.94x, at the primitive level.** 93 against 48 on a
four-element list. This is finding 21's 3,145,824 seen directly instead of
derived from a 393,216-element table: bare metal stores a text as one word,
we store a 16-byte slice.

**The chain divergence is superlinear and now measured per operand.** Bare
metal flattens, so 96 / 136 / 176 -- exactly +40 per operand. We emit
pairwise concats and materialise every prefix: 105 / 188 / 279, or +83 then
+91. `ast/fibx.zig` has 205 nested `cx_ll_concat(` sites.

**Two rows where we are CHEAPER, which is a fidelity problem and not a
win.** `cons` costs bare metal `16 + max(2*(n+1),4)*8` -- it doubles -- while
ours reserves exactly, so a 16-deep cons loop is 1633 against 2712. Likewise
`push` at scale, 718 against 1040. Being frugal where bare metal is
generous is still a divergence, and it is the direction that hides
upstream exhaustion rather than reporting it.

**`push` disagrees with itself between programs, on bare metal.** Here a
push loop costs ~16 bytes per element (1040 = 16 + 64*16); in
`probe-memory-model.codex` the same shape cost exactly `16 + 8n` (528 at
n=64). The difference is what the accumulator starts from -- `[0]` here, a
passed-in `[]` there -- which decides whether `__list_snoc`'s in-place path
finds its block on top. So bare metal's own in-place optimisation is
context-dependent, and any model that prices `push` at a fixed rate is wrong
in one of the two cases. Worth knowing before anyone trusts a shadow counter.

**The concat-accumulator control agrees to within +8/+9/+10.** Quadratic on
both arms, tracking each other exactly, which is what a shared source shape
with a constant-factor difference should look like -- and it is the control
that says the divergences above are real rather than an artifact of the
measurement.
