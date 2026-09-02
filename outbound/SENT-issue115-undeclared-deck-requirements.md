# Four things depend on the deck discipline without declaring it, and each fails differently

*Sent 2026-09-02 as https://github.com/damiant3/Cobblestone/issues/115.
Written by Claude, on Steve Howell's account and at his direction.*

---

## The shape

The deck discipline has requirements that live in prose. Four places depend on
one and say so nowhere a compiler or a caller can act on it. We hit all four in
one day building Update 54 rung harnesses, and the reason they are worth one
issue rather than four is the CONTRAST: the same class of omission fails at
four different distances from its cause.

| # | what is undeclared | how it fails |
|---|---|---|
| 1 | `SyntaxNodes` uses comprehensions but cites no `ListUtils` | **loudly, at compile** — 20x CDX3002 |
| 2 | `Lexer` defines `copy-sx-diag`, which `SyntaxNodes` also defines | **loudly, at compile** — CDX3006 |
| 3 | `Lexer` needs the deck-record intrinsic and cites no Phase Allocator | **at run time**, as a page fault |
| 4 | `check-chapter` must be called inside a deck extent | **in a later phase**, on data it already returned |

1 and 2 are cheap. 3 and 4 are the ones worth your time.

## 1 and 2: two cite gaps that fail loudly

`Syntax/SyntaxNodes.codex:3` cites `Foreword chapter Maybe` and nothing else,
while the file uses 45 `for .. in .. ->` comprehensions, which desugar to
`map-list`. `Syntax/Lexer.codex` defines `copy-sx-diag`, and so does
`SyntaxNodes`.

Both refuse at compile in a bundle that does not otherwise carry the chapter —
20x CDX3002 and a CDX3006 respectively, in ours. `build/check-subset-cites.ps1`
exists and all of these got past it. We mention them only because they are the
same omission as 3 and 4 with the failure moved earlier, which is the whole
argument below.

## 3: the Lexer acquired a deck dependency at U54 and declares none

`Syntax/Lexer.codex` has **zero** `cites` lines, at U53 and at U54, and uses
`deck-record` **60 times**.

That was survivable until U54. U53's `tokenize-collect` recursed with
`__linked-list-push acc tok` and reclaimed nothing. U54's rewinds the bivy after
every token, and says so at `Lexer.codex:598`:

> a token's own record is deck-recorded by make-token, so the only thing the
> next step needs from above the mark is the final state. Its fields are read
> into locals, the bivy rewinds to the mark, and the state is rebuilt below it

So correctness now REQUIRES `deck-record` to actually move the record. And
whether it does is decided by a gate at `Emit/X86_64Chapter.codex:1266`:

```
pa-slug = def-chapter-slug defs-lifted "init-phase-allocator" ...
dr-slug = def-chapter-slug defs-lifted "deck-record" ...
deck-record-intrinsic = (pa-slug /= "" & pa-slug == dr-slug)
```

The discriminator is the DEFINING CHAPTER, and the prose beneath it explains
why — a plug kernel used to emit `__deck-enter`/`__deck-exit` against a phase
allocator it never initialised, so a bundle without the chapter now gets the
plain identity call it declared. That is deliberate and we are not asking you
to change it.

The problem is that a cite is what forces the chapter into a bundle, which is
what turns the intrinsic on — and the one chapter that now rewinds the bivy is
not among the seven that cite Phase Allocator. It compiles clean and page-faults
at run time.

**Two things make it nastier than a missing cite.** The gate's input is
`init-phase-allocator` surviving to codegen, so `ir-prune-unreachable-roots` can
take it away from a bundle that carries the chapter and satisfies every cite.
And the failure is a silent DEFAULT rather than a refusal: `deck-record`
compiles to a 4-byte identity and nothing says so.

**Measured on our side**, and stated plainly because our harnesses were also at
fault for not doing the driver's setup: every lexing rung faulted at
`tokenize-collect+546`; adding the driver's deck prologue turned a 923-byte
fault dump into a 6,041-byte truth, with `init-phase-allocator` absent from the
old symbol map and present at `0x0010B8FE` in the new one, and the subject
growing 438,050 → 525,673 bytes, which is the `__deck-enter`/`__deck-exit` pairs
the gate flip emits.

**You would not see this.** Your deck-less bundles are plugs, and plugs consume
IR rather than lexing, so nothing on your side lexes without a deck.

## 4: `check-chapter` has a calling convention and the signature does not carry it

This is the one we would most like a second opinion on.

`check-chapter` issues its own `__deck-exit` before the per-definition walk and
`__deck-enter` after it (`Types/TypeChecker.codex:2388`, `:2393`) — the only
hand-written pair anywhere outside the emitter. So it EXITS an extent it assumes
its caller opened, and `opening.codex:631` is the caller that opens one:

```
check-result = deck-record (check-chapter (sr.scoped) ... )
```

Called without that wrapper the nesting counter goes to **-1**, and
`emit-deck-enter-builtin` swaps `R10` only on the zero crossing — so at -1 every
`deck-record` inside the walk silently stops being one. Per-definition results
land on the bivy while `check-batch` reclaims to `cb-bivy-mark` as though they
had not.

**The damage does not surface in CHECK.** It surfaces in whichever later phase
first re-reads CHECK's result. On our ladder `check` is green and prints
`cr.types` on the next line; `lower` builds the resolved tables, takes its
reservation and runs lowering first, then reads a `Text` whose length word is
now someone else's data — `!EXC=0d` in `__str_concat` with `R10` non-canonical,
having been bumped by a garbage length. Restoring the wrapper turns that into an
83-line truth, and `check`'s own output does not move either way.

**Where the requirement IS written down:** `Core/BuildSettings.codex:154` and
`TypeChecker.codex:2517`. Both are correct and both are framed as *why
`deck-short-of` is the right predicate there*, not as *what a caller owes*.
Nothing sits above the signature at `TypeChecker.codex:2355` — the line before it
is the end of `check-proof-grammar-loop`.

**This one is ours before it is yours.** Our harness called it bare; your driver
does not. We are reporting it because the requirement is invisible at the
definition and its violation is silent, not because your code is wrong.

## The ask

We are not attached to any particular fix, and the four instances probably do
not want the same one.

- For 1–3, the question is whether `check-subset-cites` can be taught the
  dependency that is not a cite — a chapter that uses `deck-record` needs Phase
  Allocator in the bundle, and the emitter already computes exactly that
  predicate at `X86_64Chapter.codex:1266`. It knows when the intrinsic is off;
  today it only stays quiet about it.
- For 4, the cheapest honest fix is prose above the signature. A stronger one is
  for `__deck-exit` to refuse a non-positive nesting counter — that turns a
  silent -1 into an immediate, local failure, and nothing legitimate reaches it.

**What we have not done:** measured the cost of any of it, checked the non-zig
plugs (no toolchain here, not our lane), or run your battery. Instances 3 and 4
are partly our own harness's fault and we have fixed our side of both; the half
worth your time is that in each case the mechanism degrades to a silent default
instead of refusing.

**Timing, so you can weigh this properly: we are only just starting to process
Update 54.** That means two things. We do not have the bandwidth yet to attempt
our own fixes for any of the four, so this is a report rather than a patch we
are holding back. And we are early enough in our own checks that we may well
find more of this class as we work through the rest of them — if so we will add
them here rather than opening another issue.
