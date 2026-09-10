# PR 141 -- zig and wasm plugs: a nested sub-pattern is a test, not a wildcard

https://github.com/damiant3/Cobblestone/pull/141  (sent 2026-09-10, branch
`plug-nested-patterns` cbf7bd5a off clean U57 49fa9f27; on `u58-candidate` as 075a4550)

Three defects, one commit: both plugs read a constructor or literal INSIDE a
constructor pattern as `_` (silent wrong answers on nested nullary ctors; zig
refuses and wasm answers wrong on a nested payload binding); the zig plug
spelled a Text literal pattern bare at any level (`is "hi" ->` never built).
zig: nested patterns and Text literals route through the chain form
(`emit-zig-chain-work`, a work list of (pattern, value) pairs). wasm:
`wat-ctor-sub-tests-at` / `emit-wat-bind-ctor-subs-at` take the object's
address; bindings and tests sit inside the nested tag test. Pinned by
`codex/test/ops/match-nested-pattern` (20 lines).

Found by the Roc ports `roc-match-nested-tags` and `roc-rec-logic-match`
(the second was green by accident until it gained fall-through cases). A cold
review caught the wasm over-read and the missing Text case before send.

Measured on the u58 stack: zig bootstrap converged in one round; zig fixed point
HOLDS; wasm fixed point HOLDS by both roads; wasm corpus sweep 830/152/26/4 with
the SAME 26 differing before and after; three corpora unchanged through both
plugs. Bundles: `~/runs/codexzig-nestpat`, `~/zigemit` (rebuilt on bare metal
from this stack, sandbox `~/runs/20260910T182338Z-zigemit`).
