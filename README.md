# DEPRECATED

**This repository is retired as of 2026-09-04. Do not fix it, tidy it, or keep
it current.** The useful parts are moving to focused repos; whatever nobody
carries over dies here with it.

`PRIORITIES.md` is no longer the plan. It is a record of one.
`OLD_README.md` is what this file used to say.

## Where the work went, and how the pieces relate

This repository is retired, but its README, its `U<NN>.log` files and its
Claude memory are still the index for every Cobblestone-related repo here.
Start at this table.

**Four coordinates locate any piece of work.** Naming all four is how you avoid
comparing two things that were never comparable.

| axis | values |
|---|---|
| **toolchain** | Rust · Zig · Wasm · QEMU (bare metal) |
| **subject** | fib · curated 28 · safari · the compiler itself (self-host) |
| **version** | a released Update (U56 = `6cd2ca1b`) · a candidate branch (`u57-candidate`) |
| **layer** | frontend (lex, parse, desugar, check, lower) → IR → plug → binary |

### Toolchains — two directions of attack

**Rust tests the system from the OUTSIDE IN.** `rust-codex-compiler` is an
independent reimplementation of the frontend, so it can disagree with upstream
about the IR. It is the only arm that can see a defect ABOVE the IR, because it
does not inherit upstream's frontend.

**Zig and Wasm test the system from the INSIDE OUT.** Both run Damian's own
frontend and check what comes out the back: each transpiles the compiler's own
source and must emit the same bytes for it twice — under QEMU and as the binary
that emitted it. A fixed point says the whole frontend plus the whole emitter
agree with themselves on the largest subject available. It cannot see a
frontend defect, because both of its passes inherit the same frontend.

**QEMU is the ground truth under both.** `cobblestone-qemu` runs Codex on real
x86 with no host runtime, which is the only place `address-of`, boxing, the
deck and memory are real rather than modelled.

| repo | toolchain | what it proves |
|---|---|---|
| [`rust-codex-compiler`](../rust-codex-compiler) | Rust | an independent frontend: `.codex` in, Codex IR out, graded byte-for-byte against `codexir`; plus an interpreter that sees MEANING rather than shape |
| [`codex-zig-transpiler`](../codex-zig-transpiler) | Zig | the fixed point, and the `codexir`/`codexcheck` oracles the Rust arm is graded against |
| [`codex-wasm-transpiler`](../codex-wasm-transpiler) | Wasm | the same fixed point through a second plug, which is what makes a shared-component defect visible |
| [`cobblestone-qemu`](../cobblestone-qemu) | QEMU | run Codex on real x86 and tell me what came out |

### Subjects — what gets compiled

A subject is not a toolchain. The same subject run through two toolchains is
the comparison that finds things; the same toolchain run on two subjects is
coverage.

| repo | subject |
|---|---|
| [`cobblestone-curated-tests`](../cobblestone-curated-tests) | 28 resolved units with upstream's own expected output, citing nothing — no `CODEX_ROOT`, no quire registry |
| [`safari-codex`](../safari-codex) | a real application, four arms on one source |

`fib` lives in `cobblestone-qemu` because it cites nothing and needs no
bundler, which is what makes it the transport smoke test. The compiler's own
source is the largest subject there is, and it is what the fixed point uses.

### Reading a claim

"The fixed point holds" is a claim about **Zig · the compiler itself ·
u57-candidate · frontend-through-plug**. It says nothing about Rust, nothing
about safari, and nothing about U56 as released — where it does NOT hold.
Every one of those four is load-bearing.

Still here and not yet carried: `findings/` and `outbound/` — 344 of this
repo's 521 tracked files, the accumulated register of what we found in Damian's
compiler and what we sent him. That is a record with no machinery attached and
it deserves a home; it has not got one yet.

## Why it is being retired

Each of the repos above can be described in a phrase. This one could not. It was
a rung harness, a QEMU driver, a sandbox system, a findings register, an outbound
PR queue, a corpus census, a branch-topology ledger and three linters.

**And it was structurally unable to find a whole class of defect.** Its two arms
— bare metal and the zig plug — are both Damian's front end. They share the
lexer, parser, desugarer, checker and lowering, and diverge only at the emitter.
So anything wrong above the IR is invisible to it *by construction*, because both
arms inherit it identically. That is not a gap in coverage; it is a property of
the design.

The proof arrived on the day it was retired. Codex converts a decimal `Real`
literal incorrectly — 10 of 120 ordinary doubles land one ULP away, in the front
end, so every backend gets the same wrong bits. Fourteen rungs never saw it and
never could. An independent front end found it in fifteen minutes.

The long version is
[an essay](http://143.244.172.148:9100/notes/what-the-ladder-is-for.md).

## What was worth keeping, and is

The **progression** — a ladder works because a failure at rung N tells you rung
N−1 was fine, so you climb cheapest-first and the first red names its own layer.
Fourteen rungs was that idea with every historical frontier still nailed to it;
four layers is the same idea usable:

1. the text survives · 2. the meaning survives · 3. the IR survives · 4. the
machine survives

And the **QEMU knowledge** — the ring protocol, the gdbstub write-position
injection, the stall at exactly `RING_SIZE` that fires spuriously, the memory
bounds added after an emitted binary livelocked the host twice. Months of ouches
encoded as guards. That is in `cobblestone-qemu` now, and it was always the expensive
part; the rungs were the cheap enumeration on top of it.
