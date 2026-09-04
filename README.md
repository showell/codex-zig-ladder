# DEPRECATED

**This repository is retired as of 2026-09-04. Do not fix it, tidy it, or keep
it current.** The useful parts are moving to focused repos; whatever nobody
carries over dies here with it.

`PRIORITIES.md` is no longer the plan. It is a record of one.
`OLD_README.md` is what this file used to say.

## Where the work went

| repo | what it is |
|---|---|
| [`codex-qemu`](../codex-qemu) | **run Codex on real x86 and tell me what came out** — the QEMU transport, carved out of here first because it was this repo's one irreplaceable capability |
| [`rust-codex-compiler`](../rust-codex-compiler) | a completely independent oracle: `.codex` in, standard Codex IR out, plus an interpreter that sees MEANING rather than shape |
| [`codex-zig-transpiler`](../codex-zig-transpiler) | a fixed point against a large subject |
| [`codex-wasm-transpiler`](../codex-wasm-transpiler) | a fixed point against a large subject |
| [`safari-codex`](../safari-codex) | an actual application, four arms on one source |

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
encoded as guards. That is in `codex-qemu` now, and it was always the expensive
part; the rungs were the cheap enumeration on top of it.
