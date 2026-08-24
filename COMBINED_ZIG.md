# One zig program, for the zig community

**Status: an idea, not a plan (Steve, 2026-08-24, brainstorming).** Nothing
here is scheduled and nothing depends on it. PRIORITIES links this file and
does not carry it as an item.

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

Everything else stays byte-identical to what the emitter produced, which is
the property worth protecting: the less this rewrites, the less it drifts
when the emitter moves.

## What to check before believing any of it

- **Two runtimes means two heaps.** Each reserves 4 GiB since PR 77, so a
  merged process reserves 8 GiB of address space. JUSTIFICATIONS' resident
  bound says the reservation is lazily faulted (peak resident 2.30 GiB
  against a 4 GiB region), so this is probably fine -- but `8cb8a0e4` is
  literally "main may not overlap the deck's live span", and that
  interaction wants measuring rather than assuming.
- **The IR buffer lives in codexir's arena.** Copy it across before zigemit
  runs, or the program depends on nobody resetting that arena.
- **One thread, not two.** Both files spawn their own 512 MB thread and
  join it; the merged main should spawn once and run both `opening()`s on
  it, at the larger of the two stacks.
- **Compile cost is unmeasured.** ~2.3 MB of zig in one compilation unit,
  with `@setEvalBranchQuota` already needed for the emitter's big literals.
  Probably fine, not known.

None of the four has been tried. The symbol counts and the seam are read
from the emitted files; everything after that is design, not measurement.

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
