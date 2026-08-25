# One zig program, for the zig community

**Status: SUPERSEDED 2026-08-25. The program exists, and it was built the
other way.** `codexzig_build.sh` produces `native/codexzig` -- Codex source
in, zig out, one process -- by merging the two halves in CODEX, as one
bundle, rather than merging the two emitted zig files as this note proposed.
Everything below is the study of the zig-level route and is kept as the
record of why that route was not taken.

**Why the Codex-level merge wins, in one line: the merge happens before the
emitter runs.** So there is one program with one `main`, one arena and one
thread -- and the whole of this note's hard part evaporates. No 94 duplicate
symbols, no `@import` namespacing, no patching `cx_write_all` or
`cx_read_file_uni` inside generated code, no two heaps and no `madvise`
reclaim between them. Nothing generated is edited, so nothing rots when
`ZigEmitter.codex` moves.

**And the seam is smaller than this note assumed.** It is not two functions
patched at the I/O boundary; it is one expression, because the two halves
already meet at a type: `emit-zig-chapter : IRChapter, List ATypeDef -> Text`
and `IRChapter` is the compiler's own. The front end has that value in hand,
so the combined harness hands it over directly and `IRTextParser` is not
carried at all -- it exists to rebuild those values from text off a serial
ring, which is the plug's situation and not a hosted program's.

Measured on the first build: 59,151-line bundle, 27.8 MB binary, no deck
overflow and no plug refusals; Fib to 36,833 bytes of zig in 10 ms; and the
output is byte-identical to `codexir | zigemit` on 85 programs.

## What it is

`native/codexir` and `native/zigemit` are two zig programs today, and the
pipeline between them is a shell pipe: source in, IR out, IR in, zig out.
The idea is a Python program that combines the two emitted `.zig` files
into ONE zig program, whose main runs the whole pipeline internally --
Codex source straight to emitted zig, no intermediate file.

**The reason is publicity, not engineering.** A single program is something
the zig community can be handed, built with one command, and understood in
one sitting. Two programs joined by a pipe is a toolchain; one program is a
demonstration. The pitch to that audience is that zig compiles and runs a
complete, self-hosted compiler for an entirely different language.

**We keep the two separate programs for everything we actually do.** The
intermediate IR is not a byproduct, it is the thing most of the ladder's
questions are asked about: the truth arm compiles a subject to IR-CCE and
hands the SAME IR to the plug, the tiers and the corpus read it, and
finding after finding has been read directly out of a `.ir` or the `.zig`
beside it. A merged binary that never writes the IR would be worse for us
in every case. This is an artifact for other people.

## Is it feasible

Yes, and the seam is better placed than it looks. Measured on the emitted
files from sandbox `20260824T193723Z-tailcall-sweep` (codexir 1,888,049
bytes, zigemit 431,831 bytes):

**Do not concatenate the two files.** They share **68 identical `cx_*`
prelude symbols**, and a further **26 top-level function names collide**
among the compiler's own definitions. A textual merge is 94 duplicate
symbols, and the fix -- renaming inside generated code -- is exactly the
kind of edit that rots the next time `ZigEmitter.codex` changes.

**`@import` gives the namespacing for free.** Three files is still one
program for the purpose: `zig build-exe main.zig`, one binary, one command.

    const ir   = @import("codexir.zig");
    const emit = @import("zigemit.zig");

Zig looks for `main` only in the ROOT file, so the `pub fn main` each
emitted file already carries is very likely just an unused public
declaration in a non-root module. **Test that before writing a parser to
strip them** -- it may be that nothing needs stripping at all.

**The I/O seam is two functions.** Input arrives as
`cx_read_file_uni("/dev/stdin")` -- that is the 10-byte CCE path a
mis-invoked `codexir` panics on -- and output leaves through
`cx_write_all`, which the `cx_print`/`cx_print_line` pair sit on top of and
which writes to stderr (the emitted runtime prints with
`std.debug.print`; corpus_run calls that "a wart the plug should fix").
So the transform is:

- patch `codexir`'s `cx_write_all` to append to a buffer instead of stderr
- patch `zigemit`'s `cx_read_file_uni` to return that buffer

**That buffer must NOT live in codexir's arena.** Allocate it from the page
allocator in the merged main. The reason is the next section: codexir's
arena is reclaimed before zigemit runs, and a buffer inside it would be the
program freeing its own input.

Everything else stays byte-identical to what the emitter produced, which is
the property worth protecting: the less this rewrites, the less it drifts
when the emitter moves.

## Two heaps, and why only one of the two costs anything

The obvious worry is that a merged process carries two runtimes and so
reserves 4 GiB twice. Separate the two costs and only one is real.

**Address space is free.** `cx_heap_base()` reserves LAZILY -- one
`page_allocator.rawAlloc` of `cx_heap_reserve` on first call, cached in
`cx_heap_mem` -- and JUSTIFICATIONS' resident bound already measured what
that costs: peak resident 2,469,888,000 bytes (2.30 GiB) against a 4 GiB
region, "the reservation is lazily faulted exactly as claimed". Two
reservations on 64-bit is 8 GiB of virtual address space and approximately
no memory. Optimising the reservation count is optimising the number that
does not matter.

**Resident is the real cost, and it is reclaimable** (Steve, 2026-08-24).
The moment codexir has produced the IR its entire arena is dead -- every
byte of that 2.3 GiB peak. Reclaim it before zigemit starts and the merged
program's peak is `max(codexir, zigemit)` rather than the sum, which is a
better memory profile than the two-process pipeline has today, since there
the two peaks are merely separated in time rather than shared.

The cheap version is about three lines and touches nothing inside the
generated code:

1. copy the IR out (13.2 MB for `ir_to_x86`, finding 33's subject)
2. `madvise(cx_heap_mem.ptr, high_water, MADV_DONTNEED)` -- the kernel
   drops the pages and RSS falls immediately
3. `cx_hp = base`, so the cursor does not still believe it is high

Both inputs are already exposed: `cx_heap_save()` returns `cx_hp`, which
is the high-water mark, and `cx_heap_mem.ptr` is the base.

**Do this only outside a deck extent.** `8cb8a0e4` is literally "main may
not overlap the deck's live span", and while an extent is open the deck has
parked `cx_hp` in the bivy -- so a reset there would restore a cursor the
deck still owns. Assert the nest counter is zero and refuse loudly rather
than reclaiming on trust.

**The tempting worse option is sharing one region between the two.** It
sounds tidier and it is not: sharing the region means sharing the CURSOR,
and `cx_hp` is read and written throughout `cx_bump_alloc`, the
save/restore/advance trio, and every deck function. That is many sites
rewritten inside generated code for the same resident win two independent
arenas already give once one of them is reclaimed. Two cursors over one
region, which is what a partial job would leave, is a corruption bug.

None of this is measured yet either -- but `bounded_run`'s cgroup
`MemoryMax` is exactly the instrument for it, so the peak can be a number
rather than an argument.

## What to check before believing any of it

- **The IR buffer lives in codexir's arena unless you put it elsewhere.**
  See the seam above: allocate it outside, or reclaiming frees the input.
- **One thread, not two.** Both files spawn their own 512 MB thread and
  join it; the merged main should spawn once and run both `opening()`s on
  it, at the larger of the two stacks.
- **Compile cost is unmeasured.** ~2.3 MB of zig in one compilation unit,
  with `@setEvalBranchQuota` already needed for the emitter's big literals.
  Probably fine, not known.

None of these has been tried, and nor has the reclaim above. The symbol
counts, the seam, and the heap primitives are read from the emitted files;
everything built on top of them is design, not measurement.

## zigc already exists, and is probably the better artifact

Damian asked (2026-08-24) whether anyone had tried transpiling the whole
compiler straight away. Someone had: `zigc` is the `passes_to_x86`
chapter set with a real I/O boundary -- **source in on stdin, a CDX out
on stdout** -- and the README has carried it since before this note. It
is ALREADY one program, and for a publicity artifact it is the stronger
one: a compiler that takes source and emits a bootable image beats a
merged two-stage transpiler pipeline. The idea above targets a different
output (Codex to zig rather than Codex to CDX), so it is not redundant,
but `zigc` should be the first thing anyone reaches for.

**Re-verified 2026-08-25 by `zigc_verify.sh`, which is new, because
`zigc` was the one ladder claim with no runner behind it.** What the run
establishes:

    zigc.zig     17,994 lines, 0 plug refusals (1 prelude guard excluded)
    zig build-exe    3 s
    zigc compiling ast/repro.codex   under 1 s, 93,104 bytes
    the seed on the same source      91,010 bytes

So it still builds clean and still runs, which is what had gone
unchecked. **The byte comparison is INCONCLUSIVE on this subject and is
not being reported as either a pass or a finding.** The README's original
subject was `ast/repro-mid.codex`, which is gitignored under
`repro-*.codex` and no longer exists; `ast/repro.codex` was substituted
because it is tracked. zigc's output is about 2 KB LARGER than the
seed's, which is the direction you would expect from precisely what zigc
documents itself as dropping -- proof pruning and dropped-def handling.
That is two DRIVERS disagreeing, which the README says is expected, and
not two compilers.

What would settle it is a subject that needs none of the driver's extras.
Finding or making one is the open work; until then the honest claim is
"zigc builds and runs", not "zigc agrees with the seed".

## The pitch, if it is ever made

**Lead with the stronger claim.** "Zig compiles another language" is the
weakest thing that is true here. The ladder can say something much better:
the emitted program's output is **byte-identical to the native x86-64
backend across all fourteen rungs**, which is a diverse-double-compiling
result rather than a "it builds" result. That is the interesting sentence,
and it is one almost nobody else can write.

**Say it is machine-generated zig, first, plainly.** That audience will
read one function and know. Owning it up front reads as confidence;
letting it be discovered reads as an omission. The generated-ness is also
the point -- the claim is about the pipeline, not about anyone's handwritten
zig.

**Credit belongs upstream.** The compiler is Damian's
(`~/showell_repos/NewRepository`); the ladder is the witness that the
transpilation is faithful. Anything published should say which is which,
and Damian should see it before it goes anywhere.
