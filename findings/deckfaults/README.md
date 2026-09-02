# The two U54 fault specimens, carried out of a retired sandbox

Sandbox `20260902T121126Z-u54-rebank` was retired 2026-09-02 rather than kept.
These four files are everything in it that did not regenerate from a script.
The five working truths it held (lex, parse, desugar, scope, check) were NOT
carried: they are ~7 minutes of guests and a kept truth nobody re-derived is
the footgun BOX's After-4 is about.

    lex-fault-tokenize-collect.dump   923 B   the deck-intrinsic fault, RESOLVED
    lower-fault-str-concat.raw      1,660 B   the fault still OPEN
    lower-subject.cdx.map          67,287 B   resolves the .raw's RIP to a symbol
    ANALYSIS.md                             the mechanism, written while chasing it

## Why the map is here

`lower-fault-str-concat.raw` is useless without it. `RIP=0x100191` means
nothing until it resolves to `__str_concat+72`, and the map is what does that.
A dump kept without its map is a dump nobody can read.

Resolve with:

    python3 - <<'PY'
    import re
    rows=[]
    for l in open('findings/deckfaults/lower-subject.cdx.map'):
        m=re.match(r'0x([0-9A-Fa-f]+)\s+(\d+)\s+(.+)',l.strip())
        if m: rows.append((int(m.group(1),16),int(m.group(2)),m.group(3)))
    rows.sort()
    def sym(a):
        for s,n,nm in rows:
            if s<=a<s+n: return f"{nm}+{a-s}"
    for a in (0x100191,): print(hex(a), sym(a))
    PY

## What each one is

**`lex-fault-tokenize-collect.dump` -- RESOLVED, kept as the specimen the fault
gate was built against.** `!EXC=0e` at `tokenize-collect+546`. Cause: the
harness never called `init-phase-allocator`, so `ir-prune-unreachable-roots`
removed it, the emitter's gate read "no phase allocator", `deck-record`
compiled to a 4-byte identity, and U54's bivy rewind reclaimed the tokens.
Fixed by giving the harnesses the driver's deck prologue.

**`lower-fault-str-concat.raw` -- RESOLVED 2026-09-02, and it was NEITHER
candidate.** `!EXC=0d` (#GP) at `__str_concat+72` after 46 lines of correct
output. Cause: the harness called `check-chapter` BARE where the driver wraps
it in `deck-record` (`opening.codex:631`). check-chapter issues its own
`__deck-exit` before the per-definition walk and `__deck-enter` after it
(`TypeChecker.codex:2388,2393`), exiting an extent it assumes the CALLER
opened; bare, the nesting counter runs to -1, where every `deck-record` in the
walk is a no-op and the results land on the bivy while `check-batch` reclaims
as though they had not. Fixed by giving `check_call()` the wrapper; `lower`
banks an 83-line truth.

**NOT inside `lower-chapter`, which this file said twice.** `emit-let`
(`Emit/X86_64.codex:2274`) is strict, so a harness computes every binding
before it prints a line: 46 lines of output means lowering FINISHED. The fault
is in the next print, `show-bindings`, whose text is `"tb " & b.name & " "` --
and the registers agree, `RDI` a fresh heap text and `RSI` at 2.16 MB in
static data, which is the `" "` literal. The faulting call is the second `&`,
reading a CHECK-phase Text one phase behind where the dump was read.

Both candidates were falsified:
  - **COMPILER-38's rename pass** -- `rename = False` faults with every
    register byte-identical, the only change in 65 lines being `F[00]` moving
    four bytes because the source moved by one word.
  - **the deck reservations** -- closed by arithmetic, no run needed: 1,232 MB
    raw against 954 MB at the derived scale of 77, in a 3,072 MB guest whose
    stack sits at 3,072 MB and whose frontier at the fault was 1,247 MB.

See `HARNESS_FIDELITY.md` for the standing account; this dump is kept as the
specimen the sixth deviation was read out of.
