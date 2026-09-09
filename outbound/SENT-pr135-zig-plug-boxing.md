*Written by Claude, working with Steve Howell, on his account and at his
direction. This is the fix for the defect we filed as #121 and then withdrew,
saying it is ours to fix in the zig plug rather than yours to guard in the
compiler.*

## What this is

Bare metal boxes every variant value: they are heap words, which is why
`address-of` there is `emit-identity-builtin` and no type can fail it -- the
value **is** the address. This plug boxed only what zig's finite-size rule
forced, so `address-of`'s meaning rested on a decision made for SIZING:
`IRExpr` held `IRExpr` directly and was boxed, `IRPat` reached itself only
through `List IRPat` and was not, and `cx_address_of` refused on the second.

This boxes every payload-carrying variant, so the plug agrees with bare metal's
own model and `address-of` is total the way it is there. A generic variant
stays unboxed -- it is emitted as a `fn ... type` with no single declaration to
point at.

## Why it matters

The gap was always present; nothing reached it until Update 55's compiler
memory campaign added the lowering memo-copy (`lcopy-pat`, `lcopy-stmts`) and
asked `address-of p < mc.mc-floor` of an IR pattern for the first time.

- **Update 55:** six of fourteen ladder rungs fail, every one on this refusal.
- **Update 56:** it stops the zig build of the compiler itself -- the plug
  cannot emit a compiler that copies its own IR patterns.

Our Update-58 candidate carries this fix and self-hosts through the zig plug;
it also passes our corpus, self-host, safari and WGSL gates unchanged, so the
change is contained to the boxing decision and does not move emitted bytes
elsewhere.

## The change

Three commits, all in `codex/plugs/zig/ZigEmitter.codex` (net +27 / -14):

1. `zig-typedef-recursive` becomes `zig-typedef-boxed` -- box every
   payload-carrying variant, not only the self-recursive ones; a generic
   variant stays unboxed.
2. a one-line follow-up: the real-to-text prelude was shadowing the prelude's
   own boxing helper.
3. a comment stating the invariant rather than the discovery, so it survives
   ingest.

Expressed against the single-file `ZigEmitter.codex`. On our own branch this
lives across three emitter pages; that four-page split is not upstream and is
deliberately not part of this candidate.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01YMgqDFdVkFRPR6auf3zfTT
