# PR 140 -- lower-record: a field's expectation carries the record's applied arguments

https://github.com/damiant3/Cobblestone/pull/140  (sent 2026-09-10, branch
`record-field-applied-args` 0e2b38e4 off clean U57 49fa9f27; on `u58-candidate` as a1e40241)

What it carries: `IR/Lowering.codex` -- `lower-record` computes the applied
record type (from the context's expectation, or the checker's recorded type for
the literal when the context supplies none) BEFORE lowering the fields, and
each field's expectation is its declared type with the declaration's
parameters substituted by the applied arguments. Pinned by
`codex/test/ops/record-closure-field-poly` (zig plug red before, green after;
interpreter either way). No register row: nothing stays open.

A cold review widened it: the first cut covered only a literal whose context
supplied the type; a `let`-bound literal still leaked. Measured on the u58
stack with the widened fix: bootstrap converged in one round; QEMU fixed point
HOLDS; census 1,046 identical / 6 differ / 217 both-refuse, the six all this
shape (queue-test, the three roc-iter ports, typeclass-poly, typeclass-smoke --
the last two are COMPILER-30's "Showable dictionary carries (tvar 511)" lead).
Zig arm: roc 25 -> 28 of 29.

Essay: `:9100/notes/the-declarations-variable.md`. Bundle with the fix:
`~/runs/codexzig-recfield/{codexzig,codexir}`.
