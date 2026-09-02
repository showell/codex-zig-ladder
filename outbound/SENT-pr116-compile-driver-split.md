# Split `Chapter: Opening` into a Compile Driver chapter and the entry point

*Sent 2026-09-02 as https://github.com/damiant3/Cobblestone/pull/116
from branch `cobblestone-driver-split` (`7d854a55`).
Written by Claude, on Steve Howell's account and at his direction.*

---

## What this is

`opening.codex` is one chapter holding 195 definitions. Among them are every
phase function — `compile-lex`, `compile-parse`, `compile-desugar-and-scope`,
`compile-type-check`, `compile-frontend{,-ir,-cdx}` — the deck arithmetic
(`scaled-floor`, `derive-deck-scale`, `effective-deck-scale`) and
`resolve-all-expr-types`.

They sit in the same chapter as `opening`, which is the program's entry point.
A program that is its **own** entry point therefore cannot bundle that chapter,
because the two `opening` definitions would collide — so it cannot call any of
them, and must reimplement them instead.

This moves 69 of those definitions into `Chapter: Compile Driver`, which
`opening.codex` cites. **Nothing else changes.**

## Why we are asking

We maintain a ladder of rung harnesses that drive your phases directly, to get
per-phase oracles. Because we cannot bundle `Chapter: Opening`, each harness
carries a hand copy of your driver's setup: the reservations, the wrapper
calls, the argument lists. That copy is where essentially all of our bugs live.

Measured on our side, of the last fourteen commits to the generator that
produces those harnesses, **eight** are corrections of the form *"the driver
does X and we didn't"* — six of them on a single day working through Update 54:

- `check-chapter` called without the `deck-record` wrapper it requires
- `lower-chapter` at 8 arguments after it moved to 9
- `check-chapter` at 5 after it moved to 9
- the LOWER ceiling passed as `0`
- the RESOLVE and LIFT reservations missing entirely
- the diagnostic bags the driver merges itself, never merged

None of these is a defect in your compiler. Every one is drift in a copy, and
every one would be structurally impossible if we could call the function
instead of restating it. **The intermediates were never the problem** —
`CompileChecked` already returns `scoped`, `all-bindings`, `ust`,
`ctor-names`, `renames`, `colliding`, `assignments`; `LexResult` returns
`tokens`; `ParseResult` returns `doc`. The phases are not hidden. They are
welded to the entry point by chapter membership, and this unwelds them.

We think it is also a reasonable thing for the chapter itself. A
195-definition chapter that mixes argument parsing and disk loading with the
compilation pipeline has a seam in it; we happened to be the ones leaning on it.

## What moved, exactly

**A pure move.** Every moved definition is the text it was, in the order it was
in. 69 definitions go, 126 stay.

- **Sections moved whole:** `Compile Flags`, `Compile Target`, `Frontend`,
  `Expr-Type Pre-Resolution`.
- **Plus six mode-flag readers** — `mode-flag-value`, `mode-flag-text`,
  `has-mode-flag` and their loops. `deck-scale-of` and `pipeline-of` were the
  only two references from the moved set back into the rest of the file, and
  they are flag parsing, so they belong beside the flags.
- **`Chapter: Compile Driver` grounds `Device.Port`** (`serial-byte` calls
  `port-out-byte`). Opening's own `grounds` line is unchanged.
- **Opening's cite list is untouched**, including two names it already cited
  without using (`x86-64-emit-cdx`, `ir-prune-unreachable`). Pruning those
  would be right and is deliberately not this change.
- Nothing in the build needs to know: `build.ps1` assembles the unit through
  `concat-codex-self.ps1`, which scans `codex/compiler` rather than reading a
  list.

## What we measured

**Static, against the original file:**

| check | result |
|---|---|
| lines of `opening.codex` absent from the two files | **0** |
| new lines in the whole-compiler concat | 23, all ours (chapter header, 6 cites, 1 cite added to Opening, prose, `Page 1`) |
| definitions lost / gained / duplicated | none / none / none (195 = 126 + 69) |
| names the driver needs that live in Opening | **none** — the seam is one-way |
| names Opening uses from the driver | 16, all 16 cited |

**Built, with your Update 54 seed under QEMU:**

| check | result |
|---|---|
| the split compiles | yes |
| binary size, base vs split | 3,116,377 B vs 3,116,377 B |
| symbols | 5,571 vs 5,571, identical sets |
| symbols whose byte length differs | **0** |
| total code bytes | 2,686,204 vs 2,686,204 |
| raw binary diff | 144,205 bytes — layout only, see below |
| **`split_compiler(original source)`** | **byte-identical to the original compiler** |
| **the split tree is its own fixed point** | **yes** — `split(split source)` = the split compiler |

The two binaries differ because `CompileDriver.codex` lands at a different
position in the concatenated unit than the `Frontend` section did, so every
address downstream shifts. That reading is confirmed from two independent
directions: no symbol changed size, and the split compiler compiles the
original source back to the original compiler bit for bit.

That last row is the one we would ask you to weigh. It also rules out the risk
we were most worried about: COMPILER-38's binder rename is keyed on
`chapter-slug`, and 69 definitions just changed chapters — if that had altered
a rename, a symbol would have changed size. None did.

## The shape of the diff, since it is the fastest way to judge this

    codex/compiler/CompileDriver.codex | 993 +++++++++++++++++++++++++++++
    codex/compiler/opening.codex       | 973 +---------------------------
    2 files changed, 994 insertions(+), 972 deletions(-)

**`opening.codex` gains exactly one line** -- the cite -- and loses 973.
Nothing in it is rewritten. No signature changes, no accessor is added, no
abstraction is introduced, nothing is renamed, and its own `cites` and
`grounds` lines are untouched. `CompileDriver.codex` is that removed text with
a chapter header on it.

We mention this because the concern you raised is a fair one and this is the
quickest way to settle it: there is nothing here shaped by what a consumer
outside Codex wants, because there is nothing here but a move. If the cut line
or the chapter name should be different, both are yours to choose and neither
costs us anything -- the split is scripted on our side, so re-cutting it
against a different `opening.codex` is minutes.

## What we did NOT test, and it is a real list

- **Windows.** No PE toolchain here. `PeStdio` and the hosted Windows container
  are untested by us in any form.
- **arm64 and riscv64.** Not our lane, no runner.
- **Your gate, the battery, the poison battery, the DDC, the app sweep.** None
  of them. We ran a self-compile and a fixed-point comparison and nothing else.
- **A seed rebuild.** This does not touch `seed/Codex.cdx`, but we have not
  put the change through a release chain, and your release notes show that is
  where fixed-point surprises surface.
- **The non-zig plugs.** No toolchain here.

We are also early in our own Update 54 processing, so treat this as a proposal
with measurements attached rather than a finished piece of work. We are sending
it now specifically so your side can react early if the direction is wrong,
rather than after we have built anything on top of it.

## We know this will probably need a second pass

You have told us you have compiler work in flight in this area today, and that
your change lands when it lands. We are opening this anyway, deliberately,
because we would rather you see the direction early and tell us it is wrong
than have us build on it quietly for a week. **We fully expect to re-cut it
against your `opening.codex` once yours has landed** -- and that is cheap on our
side, because the split is produced by a script rather than by hand: it finds
the section boundaries itself, so pointing it at a different file is minutes,
and re-running the whole verification above is about four minutes of QEMU.

So please do not treat this as a change to merge on our schedule. Merge it when
it suits you, or tell us to redo it, or take the idea and cut it somewhere else
entirely. Any of those is a good outcome. And yes to the advance copy if the
offer stands -- we will shape the next pass against whatever is actually there.

## If you would rather not

The mechanical part is small enough that you may prefer to do it yourselves, or
differently — a different chapter name, a different cut line, or splitting the
disk and quotation machinery out too. We do not have an attachment to this
particular arrangement. What we care about is that the phase functions become
callable from a program that is its own entry point.

And if the answer is no, that is a useful answer: it tells us the hand copy is
permanent, and we will invest in generating it from `opening.codex`
mechanically instead of maintaining it by hand.
