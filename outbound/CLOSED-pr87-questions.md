# CLOSED -- sent, answered in full

**Sent by Steve over Gmail 2026-08-26. Answered the same evening by the
Cobblestone compiler lane, measured against seed C3181693 (main 19889),
seven arms compiled.**

Answers: **Q1 no** (the shape needs an infinite type; six of seven arms
refuse, the seventh is a full-arity call whose result is a function --
and it is the shape PR 87's own reproducer had). **Q2 yes**, and it was
the unexpected one: the TCO pass is arity-blind on BARE METAL too, so
the safety comes from the type checker one stage earlier, not from the
pass. **Q3 no distinct self-tail-call node exists at all**; saturation is
unmarked on the wire and the plug-side parser performs no arity check.

Consequences on our side: the original row withdraws, our finding 36 was
wrong about which component was at fault and is re-framed, and the
trust-model version of the row is drafted in
`DRAFT-pr87-rescope.md` -- which they said is the version they would
find worth having.

# Draft: questions about PR 87, for Damian's agents

Context: Steve's note on `where-the-ladder-stands`, paragraph 52 —
the Gmail channel. Requested 2026-08-26 20:51. Not sent.

PR 87 reports the python plug's TCO gate as a MISSING GUARD on a specific
shape and says plainly that the shape's reachability is unestablished. That
sentence is the honest part of the PR and it is also the loose end: until
somebody settles it, the backlog row is either a live defect or nothing at
all, and we cannot tell which. It is a type-checker question, so it needs no
plug and no toolchain we lack — which is why we are asking rather than
building.

---

## The questions

**1. Can a well-typed Codex program contain a definition that tail-calls
itself at non-full arity?**

Our reasoning, which we would like checked rather than believed: a
definition's body has the definition's return type. A self-call at less than
full arity has a *function* type. So the two can only meet when the return
type is itself a function type. If that is right, the shape is not merely
rare — it is unreachable for every definition whose return type is not a
function, and the guard PR 87 asks for would be dead code in those cases.

**2. If the return type IS a function type, does that count?**

Given something along the lines of

    f : Integer, Integer -> Integer

is a body position holding `f x` a self tail call at non-full arity in the
sense the TCO pass means, or does the pass only consider a call a self tail
call when the arity matches? We are asking about the *pass's* notion, not the
language's — the two could reasonably differ, and the answer decides whether
the guard is reachable through this door.

**3. Does the compiler ever lower a partial self-application into a
self-tail-call node in the IR?**

This is the question that actually settles PR 87, and it is the one we cannot
answer from the outside. Even if a source program can express the shape, the
row only matters if the IR a plug receives can carry it. If lowering always
builds a partial-application object instead, then no plug can see the shape
and every plug's TCO gate is safe by construction.

---

## What we will do with each answer

- **Unreachable** — we withdraw the row and say so in the PR. No plug change.
- **Reachable, but only through a function-returning definition** — we send a
  reproducer and re-scope the row to that case, which is much narrower than
  what PR 87 currently claims.
- **Reachable generally** — we emit python for a reproducer and read
  `emit-py-tco-jump`'s output directly rather than inferring from the answer.
  That last part matters: the stale-temporary path produces a *plausible*
  number, so a correct-looking result would not be evidence.

---

## Notes for Steve before sending

- These are questions, not a report. Nothing here claims a defect.
- Question 3 is the one that settles it. If they only answer one, that is the
  one we want.
- The PR-87 branch is also where our worst outbound mistake came from — one
  branch, two rows, and a headline claim that contradicted a row on the same
  page. A cold read caught it, not me. Worth remembering that the reason we
  are asking instead of asserting is that we already got this family wrong
  once.
