# Outbound: the backlog row for finding 37

TEMPORARY -- delete in the commit that records it as sent, the way
PR-HEAP-UNIFICATION.md was. Until then this is the draft of the only
route this finding has upstream (contrib/README.md: a small branch off
master with a `Ladder:` line, entry in the quire's backlog).

Finding 38's row LEFT this file on 2026-08-24: sent as PR 78, where it
is COMPILER-18, off `upstream/master` 5b8091e2 with a `Ladder:` line
naming ladder tag `finding-38`. That PR is the worked example of the
route, and the number to claim here is the next one after 18.

Unlike 38, this one is not doc-only: the fix is a change to
`Syntax/Parser.codex`, so the branch carries the restructure and the row
together. PRIORITIES item 3.5 holds what it still wants -- a rebase onto
the u49 pin, off our tail-call branch.

---

| COMPILER-NN | **The two top-level scans are three-function mutual TAIL recursion, so every plug and bare metal pay a frame per definition** | From the zig-plug ladder, 2026-08-24 (`findings/README.md` 37; instrument `stack_probe.py`). `scan-top-level` / `try-scan-type-def` / `try-scan-def-header` (`Syntax/Parser.codex`, streaming header scan) and `parse-top-level` / `try-top-level-type-def` / `try-top-level-def` (the parse) each go once around per top-level definition, and **every edge is a tail call** -- no frame in either cycle is live when the next is entered. Measured on the compiler's own back-end unit bundled as one document (2,503,544 bytes, 4,511 top-level definitions), compiled by a native binary built through the zig plug: 2,393 nested `scan_top_level` frames at the shallower cliff, 3,385 nested `parse_top_level` at the deeper one. **Nothing in the fleet flattens mutual tail calls** -- `is-self-call` is self-only here, in the python plug, and in the zig plug -- so this is paid on x86-64 as well, where it is invisible only because the kernel stack is generous and frames are small. **The change is source-shaped and needs no emitter work anywhere:** have the two `try-*` functions RETURN what they found (a small record: the accumulated lists plus the new state) instead of tail-calling the loop, and the loop tail-calls ITSELF, which every existing TCO already flattens. **Measured with exactly that change applied** (ladder branch `parser-scan-self-recursive`): the minimum thread stack the transpiled compiler needs for that document falls from 32 MB to **4 MB**, and what remains on the failing trace is `desugar_expr_at` at 297 frames -- structural recursion over one expression's nesting depth, not growth in the size of the document. Behaviour preserved: the restructured parser compiled that unit to IR, through the plug to a native binary, and both of the ladder's rung outputs are byte-identical to its Update 49 bank. **One detail a re-implementer must keep:** when `parse-type-def` fails, the definition parse re-reads from the ORIGINAL state, not from the state the type parser returned -- the two functions this replaces did that, and merging them makes it easy to lose. |
