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

**`lower-fault-str-concat.raw` -- STILL OPEN.** `!EXC=0d` (#GP) at
`__str_concat+72`, after 46 lines of correct output, inside `lower-chapter`.
Identical across two runs either side of the deck-ceiling change, `R13`
byte-identical at `f883480824448b4c` (x86 instruction bytes -- a register
holding code), only heap addresses moving. So the ceiling was NOT the cause.

Two candidates, neither established:
  - COMPILER-38's rename pass, new at U54, which builds `v_1` binder names by
    string concatenation -- the helper the fault lands in;
  - the deck reservations: the harness uses RAW floors (scale 100, 1,232 MB)
    where the driver DERIVES a scale from unit length (77 for this unit,
    872 MB).

The agreed order is isolate first -- `lower` alone with `rename = False`, one
guest and one variable -- then correct the scaling, which is right on principle
either way. See `HARNESS_FIDELITY.md`.
