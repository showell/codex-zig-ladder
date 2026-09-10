# PR 139 -- inline-single-caller: the declared return type takes the call site's type

https://github.com/damiant3/Cobblestone/pull/139  (sent 2026-09-10, branch
`inline-once-return-type` off clean U57 `49fa9f27`; also on `u58-candidate`
as `527d438f`)

What it carries: `IR/Lowering.codex` -- `InlineLeaf.il-rty`, `once-apply-site`
pairs the declared return type with the site's type, `once-signature-generic`
replaces the parameter-only guard. Pinned by `build/ir-fidelity/cases/
inlined-return-type` (reads with -Passes; DROPPED before, CARRIED after).
Registers COMPILER-74 (provisional number): the checker never resolves a
variable no constraint reaches, so `list-length (make-empty 0)` still reaches a
typed plug as a hole after this fix -- ours defaults it (`default_ambiguous_vars`).

Measured on the u58 stack: bootstrap converged in one round; QEMU fixed point
HOLDS byte-identical; corpus census 1,052 identical / 0 differ / 217 both
refuse -- the shape occurs nowhere in the corpus; zig arms unchanged.

The Rust side of the same fix is rust-codex-compiler `332ae5b`; the essay is
`:9100/notes/the-call-site-already-knew.md`.
