# The harness stands in for `opening.codex`, and every deviation is a bug

**Opened 2026-09-02, during the Update 54 ceremony, after a morning spent
finding out the hard way.** This file is the standing account of one idea:
the ladder's rung harnesses are a REIMPLEMENTATION of the compiler's driver,
and the closer they are to `codex/compiler/opening.codex` the fewer of these
mornings there are.

`U54.log` has the day-by-day; this file is the argument and the checklist.

## The rule

**Read `opening.codex` on every new Update, and emulate it as closely as we
can.** Not "call the same phases" -- do what it does, in the order it does it,
with the arguments it passes.

**A deviation must be justified by a platform difference that actually
exists.** Windows-vs-Linux is the only class that can earn one, and QEMU takes
most of that away: the guest is the same machine whoever booted it. If a
deviation cannot name the platform fact behind it, it is a bug that has not
been found yet.

Deviations that ARE justified are few and each is written down where it lives:
`BootPaintStubs.codex` replaces a screen painter with a stub because the real
one puts a WALL CLOCK in a truth arm and a truth that changes between two
identical runs is not an oracle. That is a real reason. "We only need the
phases" is not.

## What this cost on 2026-09-02

Six deviations. The first five were found one at a time, each after a
failure; the sixth was found by reading the driver, which is what this
file was opened to make the cheaper habit:

| deviation | how it surfaced | cost |
|---|---|---|
| harness never called `init-phase-allocator`, so `ir-prune-unreachable-roots` removed it and the deck intrinsic silently switched OFF | every lexing rung page-faulted at `tokenize-collect+546` | ~3 h |
| `check-chapter` 5 args at U53, 9 at U54 | nine CDX2000 at codegen naming FIELDS, not arity | ~30 min |
| `lower-chapter` 8 args at U53, 9 at U54 | same shape, one function over | ~20 min |
| `lower-chapter`'s ceiling passed as 0, disabling the deck guard | suspected in a #GP; **turned out to be a no-op for it** | ~20 min |
| deck floors used RAW (scale 100) where the driver DERIVES a scale from unit length | measured harmless -- see below | closed |
| `check-chapter` called BARE where the driver wraps it in `deck-record` | `lower` faulted `!EXC=0d` in `__str_concat` reading a CHECK-phase Text | found by reading |

Five of the six are the same mistake: **the harness called the driver's
functions without doing the driver's setup.** The sixth is the same mistake
about the driver's ARGUMENTS.

**The ladder already knew and the knowledge did not spread.** Four of twelve
harnesses call `DECK_PROLOGUE` and the comment above each says exactly what
happens without it, naming the rung it once cost. `emit_harness.py` records two
earlier instances of the identical shape: `ir-emit-roots` drifting from six to
four in BOTH hosted harnesses at once, and the four diagnostic bags the driver
builds itself that a harness calling only the phases never gets. Its own words:
"being wrong together looks exactly like being right."

## The sixth deviation, and it is checklist item 3 unapplied

**`check-chapter` cannot be called bare, and it says so itself.** It issues a
`__deck-exit` immediately before its per-definition walk and a `__deck-enter`
after it (`Types/TypeChecker.codex:2388,2393`) -- the only hand-written pair
anywhere in the compiler outside the emitter. `BuildSettings.codex:154` states
the requirement in as many words: "CHECK is the exception and the reason is
three lines of check-chapter ... so that walk runs OUTSIDE the extent and the
cell is live."

**The extent it exits is the CALLER'S**, and the caller upstream ships is
`opening.codex:631`, `deck-record (check-chapter ...)`. Every harness here
called it bare.

What that does is mechanical. `emit-deck-enter-builtin` swaps R10 only on the
ZERO crossing of a nesting counter. Bare, the counter goes 0 -> -1 at
check-chapter's own exit; at -1 every `deck-record` inside the walk is a no-op,
so the per-definition results land on the BIVY while `check-batch` reclaims to
`cb-bivy-mark` as though they had not.

**And it is invisible to the phase that commits it.** `check` prints
`cr.types` on the next line and is green. `lower` builds the resolved tables,
takes a 328 MB reservation and runs the whole of lowering first, and only then
reads a `Text` whose length word is now someone else's data. That is the
`!EXC=0d` in `__str_concat`: R10 non-canonical because the previous concat
bumped it by a garbage length.

**The scale deviation is closed by arithmetic, not by a run.** The four raw
floors total 1,232 MB and the derived-77 total is 954 MB, in a guest of 3,072
MB whose stack sits at 3,072 MB and whose frontier at the fault was 1,247 MB.
There is 1.8 GB of slack either way, so the scale cannot have caused this. It
is still worth correcting for fidelity; it was never a candidate.

## Reading a fault dump: `let` is STRICT, so printed output bounds the fault

The 2026-09-02 dump was read as "it dies inside `lower-chapter`" because the
truth stops at the last CHECK line. That inference is backwards.

`emit-let` (`Emit/X86_64.codex:2274`) emits the value into a local and then the
body: **Codex `let` is strict.** A harness is one `let` chain ending in an
`act` block, so every binding -- `ir = lower-chapter ...` included -- is
computed BEFORE the first line is printed. (`ir` has four uses, so no
occurrence pass can sink it, either.)

**So output in a dump is a floor on progress, not a ceiling.** Forty-six lines
printed means every phase completed; the fault is in the PRINT, and the print
names its own subject. Here the next statement was `show-bindings`, whose text
is `"tb " & b.name & " " & ...`, and the registers say the same thing
independently: `RDI` a fresh heap text 15 MB above the top reservation, `RSI`
at 2.16 MB in static data -- the `" "` literal. The faulting call is the
SECOND `&`, on a CHECK-phase artifact, one phase behind where the dump was
read.

## The checklist, for the next Update

Before running a rung after a new release:

1. **Diff every phase entry's ARITY, U(n-1) against U(n).** Extract the
   compiler functions the harnesses call and compare signatures. On U54 exactly
   two moved out of eighteen, and asking the question completely took minutes
   where finding them one failure at a time took an hour.
2. **Diff `opening.codex` itself**, specifically `compile-lex`,
   `compile-type-check`, `compile-frontend-passes` and `compile-frontend-cdx`.
   Every `let` before a phase call is setup the harness owes.
3. **Check what each phase call is WRAPPED in.** The driver writes
   `deck-record (check-chapter ...)`; a bare call is a different program.
4. **Check the SCALE, not just the constant.** `scaled-floor (flags.deck-scale)
   demand-X-floor demand-X-guard-band` with `deck-scale` from
   `effective-deck-scale mode unit-len` -- and with no explicit `decks=` that is
   `derive-deck-scale`, NOT 100.
5. **Ask what the harness does that the driver does not**, which is the same
   question backwards and has never yet been asked here.

## The open question this file exists for

**Why is there a harness at all?**

Every deviation above is a consequence of reimplementing the driver rather than
calling it. The reasons on record are real but none of them is "it must be this
way":

- a rung needs the phases' INTERMEDIATE values (the CST, the AChapter, the
  bindings) and `opening.codex` returns only its final artifact;
- a rung is a slice, so it bundles a subset of chapters and the driver assumes
  the whole compiler;
- the harness must be deterministic, which the driver's clock and progress
  strip are not.

None of those rules out a harness whose driver section is a near-copy of
`opening.codex`'s, with the phase calls opened up for their intermediates. That
is a bigger change than any single fix above and might be worth more than all
of them. It has not been designed and is not scheduled.

## Status at the end of 2026-09-02

Five rungs bank clean at U54: lex, parse, desugar, scope, check. `lower` faults
`!EXC=0d` at `__str_concat+72`, identically across two runs (R13 byte-identical,
only heap addresses moving), after 46 lines of correct output and inside
`lower-chapter`. Two candidate causes, neither established:

- **COMPILER-38's rename pass**, new at U54, which builds `v_1` binder names by
  string concatenation -- the helper the fault lands in;
- **the deck reservations**, which at scale 100 are 1,232 MB where the driver's
  derived scale 77 would take 872 MB.

The agreed plan is (2) then (1): isolate first by running `lower` alone with
`rename = False`, one guest and one variable, which settles whether the rename
pass is implicated; THEN correct the scaling, which is right on principle
regardless. Running the scale fix first cannot distinguish "fixed it" from
"moved it".
