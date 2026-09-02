# The U54 lex page fault: mechanism, read out of the compiler's own source

Status: mechanism established by code reading; Probe B running, Probe C not run.
Nothing here is confirmed by a green rung yet.

## The fault

    !EXC=0e  CR2=0x20000000f  RIP=0x1124fc
    opening+48 -> tokenize+186 -> tokenize-collect+546

Resolved against ast/lex-subject.cdx.map. No diagnostic frame on the stack, so
the error path -- and my copy-sx-diag stub, which only that path reaches -- is
NOT implicated.

## What changed in U54

    Syntax/Lexer.codex        U53   U54
      lex-state-below uses      0     4
      deck-record uses         56    60

U53's tokenize-collect recursed with `__linked-list-push acc tok` and reclaimed
nothing. U54's rewinds the bivy after every token. Its own prose, Lexer.codex
:598:

    "a token's own record is deck-recorded by make-token, so the only thing the
     next step needs from above the mark is the final state. Its fields are read
     into locals, the bivy rewinds to the mark, and the state is rebuilt below it"

So correctness now REQUIRES deck-record to actually move the record.

## Why deck-record is a no-op in this bundle, and it is BY DESIGN

`deck-record` is the identity in source -- in Core/PhaseAllocator.codex exactly
as in the ladder's stub. The real behaviour is a CALL-SITE transform,
`emit-deck-record-wrapper` (X86_64Compound.codex:1849), emitting
__deck-enter / body / __deck-exit. It fires behind a gate
(X86_64Chapter.codex:1264):

    pa-slug = def-chapter-slug defs-lifted "init-phase-allocator" ...
    dr-slug = def-chapter-slug defs-lifted "deck-record" ...
    deck-record-intrinsic = (pa-slug /= "" & pa-slug == dr-slug)

The discriminator is the DEFINING CHAPTER, and the prose under it says why:

    "The intercept in emit-apply used to fire on the name alone, so a plug
     kernel emitted __deck-enter / __deck-exit against a phase allocator it
     never initialized. ... a bundle that does not carry the Phase Allocator
     chapter gets the plain identity call it declared."

So the ladder's stub is NOT drift. A deck-less bundle getting an identity
deck-record is the emitter's intended behaviour, added deliberately to stop a
worse failure.

## The finding

`Syntax/Lexer.codex` HAS NO CITES AT ALL, at U53 or U54. Seven chapters cite
Phase Allocator -- SkipListText, NameResolver, TypeChecker, opening,
ChapterScoper, Desugarer, Lowering -- and the Lexer, which is the one that
now rewinds the bivy, is not among them.

A cite is what forces the chapter into a bundle, which is what turns the
intrinsic on. So the lexer acquired a dependency on the deck intrinsic without
declaring the dependency, and in any bundle that does not otherwise carry
Phase Allocator it is silently compiled without the mechanism it now needs.
`bundle_desugar.ps1`'s own comment records the old state of the world:
"Nothing else in the unit cites Phase Allocator, which is why lex and parse
never needed it."

This is the third instance of one shape found in one morning -- a chapter that
does not declare what it needs -- after SyntaxNodes/map-list and
Lexer/copy-sx-diag. The first two fail loudly at compile. This one does not:
it compiles clean and page-faults at run time.

Upstream would not see it. Their deck-less bundles are plugs, and plugs consume
IR rather than lexing, so nothing on their side lexes without a deck.

## Probes

A (free, done)   resolve RIP against the map        -> tokenize-collect+546
B (running)      desugar truth arm: same U54 lexer,
                 PhaseAllocator present, intrinsic ON
                 green -> lexer correct WITH the deck
C (not run)      lex bundle + PhaseAllocator + BootPaintStubs, deck-record stub
                 dropped, SAME subject -- the one-variable A/B

B is suggestive rather than decisive: desugar's subject text differs from lex's.
C is the clean one.

## Probe B did NOT run the lexer, and that is its own finding

At 4:26 elapsed the desugar guest had used ZERO seconds of CPU (`ps -o times`),
59 MB resident, sleeping. It is not computing and it is not faulting -- it never
got going. So Probe B has not yet said anything about the lexer.

Two things fell out of chasing that.

**`run_cdx` silently ignores the host's guest-size cap.** codex_vm.py's header
says the opposite in as many words:

    "The guest-size default honors CODEX_MEM_MB so a host caps EVERY driver by
     exporting one variable (~/.codex_ladder_env on the droplet), instead of
     trusting each wrapper to pass a number explicitly."

`launch(kernel, mem_mb=None, ...)` honours it -- `if mem_mb is None: mem_mb =
MEM_MB`. But `run_cdx(kernel, mem_mb=1024, ...)` defaults to a NUMBER, not None,
and passes it straight through, so MEM_MB is never consulted on the run path.
The droplet exports CODEX_MEM_MB=3072 and every run-stage guest gets 1024.
Four callers inherit it: oracle_lib's truth arm, tier_run, arithcycle,
bare_expected. `compile_blob` takes mem_mb=None and is correct.

Whether that is today's cause is NOT established. It is a defect either way,
and it is exactly the shape the header was written to prevent.

**A silent guest costs ten minutes.** `recv_all` breaks only on socket timeout
or EOF; there is no halt detection. The truth arm passes idle_timeout=600, so
a guest that says nothing is waited out for the full ten minutes before the
arm can even report. Twelve units make that a real number.
