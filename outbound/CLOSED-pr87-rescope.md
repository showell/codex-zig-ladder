# CLOSED -- sent, ACCEPTED as written

**Sent by Steve over Gmail 2026-08-26. Accepted the same evening.**

Where it landed on their side: the invariant gets **declared in the
Developers Rulebook's plug-wire contract section** ("What the wire
carries") -- naming the shape, the reason it cannot occur in
compiler-produced IR, the CDX2010 occurs check as the component doing
the work, and the hand-authored-IR caveat. A pointer comment at
`is-self-call` is under consideration by the same lane under their
rediscovery rule. **The IRTextParser arity check is recorded as an open
lead, not built** -- they agreed it is a trust-model question and that
nothing today feeds a plug IR the compiler did not produce, so the
question gets written down where it will be found rather than answered
under no pressure.

That is a better outcome than a code change: a comment rots, a rulebook
section is what the next plug author reads.

**OWED BY US, and accepted:**
- The zig **execution** datum -- an executed arm beats a compiled one.
- The falsifier work on more shapes and the two coverage corners,
  **reporting either way, including a null result**, since "tried and
  found nothing" moves confidence where silence does not.
- The **let-bound alias** shape specifically: their seven arms did not
  cover it.

Probes written: `findings/probe-pr87-alias.codex`,
`probe-pr87-deck.codex`, `probe-pr87-armb.codex`. Not yet run.

# Draft: re-scope PR 87's row, in reply to the compiler lane

Requested implicitly by their answer: *"If you re-scope rather than
withdraw, that trust-model version of the row is the one we would find
worth having."* Not sent.

---

## The reply

That is a better answer than the question deserved, and two parts of it
land on us rather than on the row.

First, thank you for naming arm B. PR 87's reproducer *is* B — one
parameter, one argument, a full-arity self call whose result happens to
be a function. We already knew that reproducer could not reproduce; a
cold read of our own branch caught it before you did, and it is recorded
on our side as the worst outbound mistake we have made. You have now
explained *why* it compiles, which we had not worked out. It was not a
near miss at all.

Second, Q2 is the part we did not see coming and it changes one of our
own findings rather than yours. We had filed the python plug's
name-matching TCO gate as a python defect. Having read
`Emit/X86_64.codex:75-80` on your prompting, it plainly is not: bare
metal's `is-self-call` walks the apply spine and answers on the name
alone, never counting arguments, and `should-tco` adds only `params > 0`.
The python plug is copying the reference faithfully. Our finding is
re-framed accordingly — the defect we described is not one, and the
finding was wrong about which component was at fault.

So we withdraw the original claim and re-scope, as you suggested.

## The re-scoped row

**No plug's TCO gate checks arity, and nothing in the plug states why
that is safe.**

- Every gate we have read — bare metal (`Emit/X86_64.codex:75-80`), the
  python plug, and our own zig arm — decides "is this a self tail call"
  by comparing the spine's root name to the definition's name. None
  counts arguments.
- That is safe for compiler-produced IR, and your Q1 establishes why:
  the shape needs `R = (remaining params) -> R`, and the checker refuses
  it, by name where the return type is inferred.
- **It is not safe for IR the compiler did not produce.** Application is
  curried one argument per node, a saturated call and a partial
  application are the same spine shape, nothing marks saturation, and
  `plugs/common/IRTextParser.codex:705` accepts the node structurally
  with no arity check. A plug fed hand-authored or third-party IR text
  is protected by nothing in the plug.
- The cost of the gap is that the invariant doing the work lives in the
  type checker and is stated nowhere near the gate that depends on it.
  A plug author reading the reference implementation — which is what a
  plug author does — reads a gate that looks like it is checking
  something and is not.

**What we are NOT claiming:** any reachable defect from compiler output.
That claim is withdrawn.

**Cheapest fix, if it is worth one:** a comment at `is-self-call` naming
the invariant and the diagnostic that enforces it (CDX2010). An arity
check in `IRTextParser` would be stronger and costs more; whether the
trust model warrants it is your call, not ours — we do not know who
feeds hand-authored IR to a plug.

## On your falsifiers

We can take two of the four, and will report either way.

- **(1) more shapes.** Seven is not the language. We will try tail
  self-calls under `deck-record`, inside `act` blocks at a non-final
  statement, and through a `let`-bound alias of the definition.
- **(2) the untried corners.** We verified both coverage gaps you named
  and they are real in bare metal, not just suspected: `has-tail-call`
  answers False for `IrTry` outright, and `has-tail-call-act` inspects
  only the last statement. Neither looks like a route to the shape — a
  tail call the pass declines to optimise is a deeper stack, not a wrong
  answer — but we will confirm rather than assume.
- **(3)** rests on your inference rules and is yours.
- **(4)** we can execute arms rather than only compiling them, on the zig
  arm, if you want that second datum.

---

## Notes for Steve before sending

- This concedes two errors of ours (the B reproducer, and finding 36's
  framing) and withdraws the original claim. That is the honest shape
  and it costs nothing we should want to keep.
- The re-scoped row asks for a COMMENT as the cheap fix. That is
  deliberate — an arity check in the parser is a trust-model decision
  about who feeds IR to plugs, and we do not have the standing to make
  it.
- The falsifier offer is real work: three probe programs, one compiler
  run. Cheap, and it is the kind of thing that makes the next row of
  ours easier to believe.
