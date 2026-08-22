# The proper fix: one heap, so `__heap-restore` means something

Design note, written 2026-08-18 while the arena change swept. The arena is the
interim; this is the version that makes the plug honour an instruction it
currently accepts and discards.

## What the prelude has today

There IS a bump allocator in the zig prelude, and it is a faithful one:

    var cx_heap: std.ArrayListUnmanaged(u8) = .empty;
    var cx_hp: i64 = 0;
    fn cx_heap_save() i64 { return cx_hp; }
    fn cx_heap_advance(n: i64) i64 { cx_hp += n; cx_buf_want(cx_hp); return 0; }
    fn cx_heap_restore(h: i64) i64 { cx_hp = h; return 0; }

It is just not where objects come from. `cx_heap` serves `peek-byte`,
`poke-byte`, the `__buf-*` family and the emit workspace reserved through
`__heap-advance`. Records, lists, text and closures come from a general
allocator and never touch it.

Bare metal has **one** heap. `__alloc` bumps the same pointer that
`__heap-save` and `__heap-restore` move, and a buffer address is an offset into
the same space. That is the whole difference, and it is why:

- `__heap-restore` reclaims everything on bare metal and nothing in zig
- `emit-all-defs` (`X86_64.codex:1082-1089`) brackets **every definition** in
  save/restore, so emission costs the max over definitions on bare metal and
  the sum in zig. On `scale`, that is 61 definitions.

## The change

Make object allocation come from `cx_heap`/`cx_hp` as well, by giving that
region a `std.mem.Allocator` vtable and pointing `cx_gpa` at it.

**The one thing that makes it delicate:** `cx_heap` is an ArrayList and
reallocates when it grows, so a pointer handed out before a grow dangles after
it. Bare metal does not have this problem because its arena is a fixed region.
So the region must be reserved once, up front, and never grown:

    cx_heap.ensureTotalCapacityPrecise(std.heap.page_allocator, cx_heap_reserve)

Reserving is not committing. Linux gives back lazily faulted pages, so resident
memory stays proportional to what is actually touched; the measured 238 MB
should not move. A reservation of 2 GiB of address space costs nothing until
used, and running out of it should `@panic` loudly rather than realloc, because
a realloc is a silent dangling-pointer bug.

Sketch:

    fn cx_bump_alloc(_: *anyopaque, len: usize, alignment: u8, _: usize) ?[*]u8 {
        const base = std.mem.alignForward(usize, @intCast(cx_hp), @as(usize, 1) << @intCast(alignment));
        if (base + len > cx_heap.capacity) @panic("cx heap exhausted");
        if (cx_heap.items.len < base + len) cx_heap.items.len = base + len;
        cx_hp = @intCast(base + len);
        return cx_heap.items.ptr + base;
    }

`resize` is worth implementing rather than returning false, because bare metal
has the same fast path: `__list_snoc` extends **in place** when the block is the
topmost allocation and only reallocates otherwise
(`X86_64ListHelpers.codex:223-265`, "path 2"). So:

    resize: true when base + old_len == cx_hp and the new length fits
    free:   rewind cx_hp when the block is topmost, otherwise a no-op

That is not an optimisation, it is the mirror. A plug whose list growth
reallocates where bare metal extends is allocating a different amount of memory
for the same program, which is how we got here.

## What it buys

- `__heap-restore` reclaims everything, so `emit-all-defs`'s per-definition
  bracketing works as designed and emission goes from sum-over-definitions to
  max-over-definitions.
- The harness's own per-subject release starts reclaiming, which is what
  `6fedfc7` claimed and did not do.
- One number describes the program's memory instead of two, and `__heap-save`
  means the same thing on both arms.

## What to watch

- **Alignment.** Records are pointer-sized; `cce_table` and friends are not
  allocated. `alignForward` at every alloc covers it, but a mis-set alignment
  is a wrong-answer bug rather than a crash on x86, so it wants a probe.
- **`cx_buf_want` must stop growing the list** once the region is reserved; it
  should assert instead.
- **The reservation size is a new constant** and the honest place for it is
  beside `demand-lift-floor`, not buried in the prelude.
- **Verification is the ladder itself.** The change is output-neutral or it is
  wrong, and fourteen banked truths say which.

## Order

1. The arena, landed and sweeping. Two lines, 12.5x, proven.
2. This. Bigger, mirrors bare metal, and closes the no-op.
3. Report the no-op upstream regardless of which fix lands, because it is a
   property of the plug and not of our ladder: the plug accepts `__heap-restore`
   and discards it, and the compiler leans on it 61 times in one subject.

## Absolute addresses vs the reservation (added 2026-08-19, corpus evidence)

The corpus has subjects that peek fixed physical addresses far above any
sane reservation: `smp-arm64-boot` polls `#7E000000` and `smp-riscv-boot`
polls `#80090000` -- both about 2.1 GB, both legitimate guest-physical
addresses on their boards. Today's contiguous `cx_buf_want` zero-fills up
to whatever address is touched, which is how both subjects OOM an 800 MB
cap from 29 lines of source. Two consequences for this design:

- **RLIMIT_AS counts reserved address space, not resident pages.** "Reserve
  4 GB, fault lazily" keeps RSS low but dies instantly under the corpus
  runner's `RLIMIT_AS` cap. Either the reservation stays modest and an
  out-of-region absolute address gets a defined loud behavior (assert with
  the address in the message), or the cap policy moves off RLIMIT_AS for
  emitted programs. Pick one in this design, not at debug time.
- **These two subjects are not the design's problem to solve.** They verify
  that a secondary CPU core executed guest code; a hosted single process
  has no secondary core, so no memory model produces their expected
  output. They are census-classification work (a hardware-only bucket),
  and they are cited here only as proof that out-of-region peeks occur in
  real depot code.

---

# The ladder run, 2026-08-21: what verification found

The unification was built on 2026-08-20 (branch `zig-plug-heap-unification`,
`7ef1ff2f`) and verified overnight. **It is not ready to send.** Ten of
fourteen rungs came back byte-identical to the u48 bank; `fibx` and `whole`
-- the two scale units, two rungs each -- died. This section is the diagnosis
so far, written down because it outlived the session that produced it.

## The reproduction loop, which is the reusable part

The rung costs ~11 minutes on the droplet, and almost all of that is the ring
transpile. Re-running the **already emitted** subject is ten seconds:

    zig run ast/fibx.zig 2> raw          # the subject writes its output to STDERR
    # sections between "=== subject fibx ===" / "=== end fibx ===" and
    # "=== subject scale ===" / "=== end scale ===" compare byte-for-byte
    # against truth/u48/u48-fibx.truth and u48-scale.truth

Two facts make this work and are worth keeping:

- **The truth stream is stderr**, because `cx_print_line` is
  `std.debug.print`. `cx_write_all` (fd 1) carries only binary output, so
  **stdout is free for instrumentation** and never touches the comparison.
- The prelude is plain text in the emitted `.zig`, so a hypothesis about
  allocator or deck behaviour can be tested by patching that file directly,
  with no emitter rebuild and no QEMU. Thirteen experiments ran this way in
  one evening.

## Confirmed: the reclaim is the trigger, and the rest of the arm is correct

With `cx_heap_restore` made a no-op -- the pre-unification arena behaviour --
`fibx` and `scale` are **byte-identical to the u48 bank**
(`ac577dd0e628`, `614ab3e8608d`). So nothing else about the branch is wrong.
The failure is entirely in objects that outlive a reclaim.

Corollary worth stating: **the arena was load-bearing.** Not reclaiming is
what kept pre-existing escapes harmless.

## Defect A -- `cx_ll_with_capacity` discarded its argument (FIXED, `17329ed9`)

    fn cx_ll_with_capacity(comptime T: type, n: i64) *CxList(T) {
        _ = n;                     // discarded
        return cx_ll_empty(T);
    }

`x86_64_init_codegen_sorted` pre-sizes every emit table to
`accum_capacity()` (65536, and 2x/4x for some), precisely so a push inside
`emit_all_defs`' per-definition save/restore bracket never reallocates. The
compiler's own guard sits on that same line and says what happens otherwise:

> *"the emit tables are pre-allocated to accum-capacity and a push past it
> reallocates into scratch that this loop reclaims, corrupting the table.
> Raise accum-capacity in BuildSettings and rebuild the seed."*

Our tables started at capacity zero and grew geometrically, so a push inside
the bracket moved the backing array into the bracket's scratch; `restore`
reclaimed it; the list header survived pointing at bytes the next definition
overwrote. Symptom: `fibx` segfaults at address **0x11** inside `djb2_hash`,
hashing a `func_map` key whose slice pointer had become a small integer.

Fixed with `ensureTotalCapacityPrecise` -- precise rather than rounded,
because "pre-allocated to accum-capacity" is a statement about a number.

**Necessary, not sufficient.** With the capacity honoured, `fibx` still dies,
at address **0x896**, in the same call chain. Something else escapes.

## RULED OUT: the deck nesting model (this cost hours; do not re-derive it)

`check_chapter` issues a bare `__deck-exit` with no matching enter, driving
the nesting counter to **-1**, after which every per-definition `deck-record`
in the walk declines to swap. This looks damning, and
`TypeChecker.codex:2455` explains the intent in prose --

> *"check-chapter issues a `__deck-exit` immediately before this walk and a
> `__deck-enter` after it, so the walk runs OUTSIDE the phase-wide extent.
> The cell is therefore live -- each per-definition `deck-record` inside the
> loop enters and exits on its own and writes the frontier back."*

-- so it reads like our arm losing the extent. **It is not a divergence.**
Bare metal does exactly the same thing. Read
`X86_64Builtins.codex:1030` (`emit-deck-exit-builtin`): it loads the counter,
adds -1, stores it, and `jcc cc-ne` **skips** the write-back unless the
decremented value is zero. At zero it goes to -1 and skips, identically to
`cx_deck_exit`. `Arm64CodeGen2.codex:1492` is the same shape with `cbnz`.
Enter matches too, on both arms: the swap happens iff the *pre-increment*
value was zero, which is what `if (cx_nest == 0)` before `cx_nest += 1` does.

Two fixes were tried against this false lead and both are recorded as
**wrong**, because each looks attractive:

- **Hold the counter at zero on an unmatched exit.** `fibx` goes
  byte-identical -- and `scale` then dies, because the bare `__deck-enter`
  never gets a matching exit, so the counter is left at 1 and the next
  subject starts inside a phantom extent. It was masking, not fixing: it
  moved routing *away* from bare metal's.
- **A debt counter** (an unmatched exit owes one enter). Worse: the debt is
  consumed by the first unrelated `deck-record` bracket in the walk.

## Open: what still escapes a bracket

Unidentified. The shape to look for is an allocation made inside
`emit_all_defs`' bracket that is still referenced after the restore. Since
the deck routing is faithful and the emit tables are now pre-sized, the
prime suspect is **growth schedule**: the compiler manages headroom
explicitly (`copy-list-with-headroom (env3.state.expr-types) (def-count * 56)`
in `check-chapter`, and `__list-with-capacity` elsewhere), while
`std.ArrayListUnmanaged` also grows geometrically on its own account. A list
bare metal never reallocates inside a bracket may still reallocate in ours.

Next instrument, in order:

1. **Poison on restore.** Fill the reclaimed span with a recognizable
   pattern so the *first* dangling read fails immediately and legibly
   instead of hundreds of allocations later in a hash function. Encode the
   restore's sequence number in the pattern and the faulting address names
   the bracket that reclaimed the object. (0xDEAD-prefixed values are
   non-canonical, so they fault rather than being read as data.)
2. **A per-bracket allocation census** -- what is allocated between a save
   and its restore, and which of those addresses is read afterwards.
3. Only then re-run the rung through the ladder.

## Also landed on the branch

`cx_bump_alloc` now refuses when the frontier would climb into a deck placed
above it, rather than writing through it in silence. The bound is read from
the live cursor and never a constant, because `__deck-set` places the deck at
run time and the program chooses where. Only the outside-an-extent direction
is checked: the mirror test would read `cx_bivy`, which is stale whenever the
counter and the swap disagree -- as they legitimately do at -1.

## The standing lesson

Ten rungs green would have signed off on both defects. Only `fibx` and
`whole` allocate enough for a reclaim to be reached by a later allocation.
That is the argument for keeping expensive scale rungs in the ladder,
stated as a measurement rather than a preference.

## ROOT CAUSE, 2026-08-21 evening: the deck overruns its reservation

Measured, with the arithmetic closing exactly. Supersedes the "open second
escape" above; that section's ruled-out list still stands EXCEPT the deck
collision, which is back on and is the cause (see the correction below).

`emit-build` places the deck at the current frontier with `__deck-set` and
then lifts the main frontier clear of it with `__heap-advance`, reserving
`defs*65536 + 25165824` bytes. For fibx (3 IR definitions) that is
**25362432 bytes at [115842304, 141204736)**, and the main frontier is
lifted to exactly 141204736 -- so the parked main frontier IS the deck's
top. **Nothing enforces the bound**: `cx_bump_alloc` checked only the
1.5 GiB reserve ceiling.

The deck ran to **149817824 -- 8613088 bytes over**. Out there it
allocated the `CodegenState` that `emit-all-defs` deliberately decks (so
it survives the per-definition restores) at 149819928. The main frontier,
rewound to 141204736 by those same restores, then climbed back; at
`build_debug_map` it crossed 149819928 and wrote over that record.
`st.workspace` became **2190**, and the next read of
`st2d.workspace.code_capacity` faulted at **0x896 = 2190 + 8**, the offset
of that field.

Chain, end to end: deck overruns -> decked state lands in main's region ->
main reallocates over it -> a pointer field becomes a small integer ->
segfault thousands of allocations later, in a hash function, with nothing
near the actual fault.

**Upstream has seen this exact shape.** `BuildSettings.codex` records that
starving the deck floor "did not raise CDX9002; it crashed in
__text_compare on a garbage pointer, which is the failure the guard exists
to prevent, with the guard present and compiled in" -- because
`deck-short-of` reads `__deck-pos`, and that cell is **frozen** inside a
phase-wide extent while the real cursor moves in R10. So the exhaustion
guard cannot fire where exhaustion happens. Worth raising with Damian
independently of our fix.

Landed: `e4d2fcd1` refuses the crossing instead of corrupting silently --
inside an extent the bound is `cx_bivy`, outside it `cx_dptr`, both live
cursors because the program chooses where the deck goes.

**Still open, and now a sizing question rather than a mystery:** the zig
arm needed 8613088 bytes more deck than bare metal reserves for fibx,
against a 25 MB reservation -- roughly a third over.

Representation width was the suspected reason and is now measured rather
than guessed: `findings/primitive-costs.md` prices every shape on both arms.
The floor is +8 per list, our `CxList` header against bare metal's inline
one; `List Text` is 1.94x because a text is a 16-byte slice here and one
word there; and the `&`-chain rows are superlinear because bare metal
flattens where we materialise every prefix.

**The 8613088 is stale as a target.** It was taken before the list
constructors stopped over-reserving (`8d9dbbe7`, 6.96 MB of deck on its
own) and before four more fixes landed. Re-measuring it is PRIORITIES
item 1's gate, and it decides whether the `Text` narrowing is needed at
all rather than merely desirable.

Options if it still overruns are to shrink deck consumption or to scale the
reservation on this arm; the second diverges from a number the depot can
observe (`__deck-pos`), so it is not a free choice.

### Correction: how the earlier exclusion went wrong

The 2026-08-21 morning section lists "the frontier entering the deck" as
ruled out. That was wrong, and the mechanism of the error is worth more
than the error: the invariant check **never armed**. It armed only when a
`__heap-advance` pushed the frontier past a recorded deck top, and
`__deck-set` is called three times in this program -- the arming flag was
reset by a later placement and never set again. A guard that never runs
is exactly as quiet as a guard that passes, and the silence was read as
evidence.

The rule that follows: **an instrument must report how many times it
actually executed.** The run that found the root cause printed
`checks_run=` in its panic and logged every deck placement; that is why
the third `__deck-set` -- the one that mattered -- was visible at all.
