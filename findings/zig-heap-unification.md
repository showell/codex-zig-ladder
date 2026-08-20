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
