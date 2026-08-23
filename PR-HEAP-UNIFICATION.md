# PR body draft: zig plug heap unification

Branch `zig-plug-heap-unification`, 21 commits on the Update 49 release
(`bdf0049b`). Applies cleanly on current master: the two commits since
(`ff9eaf4c`, `5b8091e2`) touch `tools/codex-vm.c` and docs only.

---

The zig plug's heap becomes bare metal's heap: one region, a bump
frontier that is the same number `__heap-save` answers on bare metal,
and the deck as a true second cursor into the same region --
`__heap-restore` actually reclaims, `__deck-enter`/`exit` swap through
the bivy at nesting depth zero, and a decked value survives the rewinds
that reclaim everything else. Before this branch the plug's allocator
was a growing arena that never rewound: every heap observable a program
could print disagreed with bare metal, and saturation subjects diverged
unboundedly.

What rides along is what the one-heap model surfaced, each as its own
commit with a Confidence paragraph:

- **The region is a 4 GiB lazily-faulted reservation** (rawAlloc, zero
  resident cost until touched). Measured: `codexir` on the 2.4 MB fibx
  subject completes rc 0 in 34 s with peak resident 2.30 GiB, IR output
  13,223,342 bytes, byte-identical across runs.
- **A crossing guard.** Two cursors share the region and nothing
  enforced the deck's reservation: the deck could climb out of its span
  and allocate among main's live objects, and the wreckage surfaced as
  a segfault thousands of allocations later. `cx_bump_alloc` now
  refuses at the crossing, in both directions: the deck reaching the
  parked frontier inside an extent, and main overlapping the deck's
  live span `[deck base, deck cursor)` from below -- the direction the
  measured corruption actually took. BuildSettings already records the
  same failure shape on bare metal (starving the floor crashes on a
  garbage pointer rather than raising CDX9002, because `deck-short-of`
  reads a cell that is frozen inside a phase-wide extent); the plug arm
  refuses it by name. A ladder regression probe triggers the refusal on
  purpose.
- **Allocation-shape mirrors.** In-place growth when the block is the
  topmost allocation (bare metal's `__list_snoc` path 2); list
  constructors reserve the true total; text concat extends the frontier
  block; text results are copies, so a decked text is really decked;
  substring traps out of range instead of clamping; text-replace with
  an empty pattern copies.
- **Observability fixes.** `address-of` returns a heap-relative
  identity instead of 0 (mode-ordinal and copy-sx-text short-circuit on
  `== 0`); `peek-qword` wraps, because every bit pattern is a legal
  i64; an uncovered codepoint becomes `?` as bare metal does; a
  non-ASCII name is transliterated before it becomes a zig identifier.
- **The deck instrument.** The deck high-water mark is reported from
  the one place that can see it (the deck-pos cell is frozen inside an
  extent), which is how the reservation numbers above were measured.

Verification: the ladder's tier set is green both arms; the 323-program
census moved no verdict (0 differ, 0 crashed against the banked
truths); the 14-rung sweep is 14/14 with recorded truths
byte-identical. Each commit carries its own Confidence paragraph with
what was measured and what is still exposed.

Reach limits, named so the next branch has a floor:

- **Finding 33:** the plug emits every call as a call; bare metal
  tracks tail position and jumps. `zigemit` on the 13 MB fibx IR wants
  >2 GiB of thread stack for 3.28M `tokenize_loop` frames. The fix
  (self-tail-call in tail position becomes a loop) is the next branch.
- **Finding 34:** the hosted harnesses drive emission without the
  driver's per-def reclaim discipline, so emission cost is a single
  peak rather than a sawtooth. The 4 GiB region absorbs it for every
  subject the ladder runs; per-def save/restore brackets are queued
  beside the finding-33 work, where they become measurable.

---

## Open points before send (not part of the body)

- [ ] guard-and-ir chain green (tiers incl. probe-deck-overrun, census,
      sweep) -- in flight, sandbox 20260823T205521Z
- [ ] Steve's yes on the finding-34 recommendation (note, not fold-in)
- [ ] re-check absorption against upstream tip on send day
- [ ] confirm final commit count / tip sha in the body header
