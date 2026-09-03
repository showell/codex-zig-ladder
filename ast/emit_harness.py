#!/usr/bin/env python3
"""The back-end harness, shared by every rung that compiles a subject all the
way to a CDX binary.

The driver is the compiler's own entry point, x86-64-emit-cdx, and the output
is what it returns: the symbol map, then header-bytes, the content buffer and
tail-bytes, 32 to a line. Nothing here decides anything about emission -- the
whole point is that the rung runs the real thing, so a copied driver that
could drift is exactly what this is not.

**A harness takes a LIST of subjects and runs each one.** That is the fix for a
conflation the ladder shipped with: a rung is a claim, a unit is a compile, and
they were the same word. ir_to_x86_on_cce compiled the same 2.4 MB unit as
ir_to_x86_on_fib, and passes_to_x86_on_arith the same 2.58 MB unit as
passes_to_x86_on_mid, differing only in a Text literal, so
the ladder paid for four compiles to ask four questions of two binaries.
Compiling the unit is 80-90 per cent of what a big rung costs (measured, sweep
of 2026-08-17), so the second question was costing almost as much as the first
and learning nothing new about the compiler.

The pipeline therefore moves into `run-<prefix>`, a function of the subject
text, called once per subject with a delimiter line between the dumps. That
shape was not invented here: gen_zigc_harness.py has run pipeline_source over a
bound `src` since the hosted compiler existed.

What this costs is fault isolation, and it is worth naming. Two dumps from one
process means a fault in the first subject takes the second down with it, where
two rungs used to fail independently -- and that mattered exactly once, when
the arith rung faulted and the mid rung was still measured. The delimiter is what buys most of
it back: a truncated run names the subject it died in.
"""


def codex_literal(s):
    """Escape a program so it can ride inside the harness as a Text literal."""
    for ch, name in {'\t': 'tab', '\r': 'carriage return'}.items():
        if ch in s:
            raise SystemExit(f'subject contains a {name}; CCE has no escape for it')
    if any(ord(c) > 127 for c in s):
        raise SystemExit('subject has non-ASCII chars; the zig runtime panics on multibyte CCE')
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


# The three pieces below are shared with the front-end rungs, whose harnesses
# predate this file and write their own pipelines. Those rungs bundle only the
# front end on purpose -- being cheap is what earns them their place low on the
# ladder -- so they cannot take frontend_source whole. They can take these,
# because every chapter the three need is already in all four bundles.

# opening.codex:442 opens with `let mountain-base = init-phase-allocator`, and
# this is not only about setting the deck cell. X86_64Chapter.codex:1147 decides
# whether deck-record is the intrinsic or an ordinary function:
#
#   pa-slug = def-chapter-slug defs-lifted "init-phase-allocator" ...
#   dr-slug = def-chapter-slug defs-lifted "deck-record" ...
#   deck-record-intrinsic = (pa-slug /= "" & pa-slug == dr-slug)
#
# A harness that never calls init-phase-allocator leaves it unreachable, IR
# emission prunes it, pa-slug comes back "", and the flag is False. Then
# deck-record is emitted as what it looks like -- `mov rax,rdi ; ret`, four
# bytes -- and every value the compiler wraps in it to survive emit-all-defs's
# per-function __heap-restore is freed at that boundary instead. bag-add wraps
# both its cons cell and its record, so the second diagnostic a compile records
# walks a dangling spine: that is clamp's RDI=0 into __list_snoc.
#
# Naming it is the whole job -- the marker has to be in the unit. It is
# __heap-save + __deck-set, so the zig arm emits it without trouble.
#
# The reservation has to follow immediately, and cover the whole run rather than
# sit in front of emission. init-phase-allocator points the deck cell at the
# current heap top and bivy carries on from the same address, so with the
# intrinsic live the first deck-record extent would allocate on top of the parse
# and check data still in use. opening.codex never leaves that window open:
# `build lex-deck-height` is line 444, two lines after the init at 442. Ours is
# one region for every phase instead of the driver's thirteen, which is the part
# of its shape a harness can skip.
#
# build's body is inlined rather than cited because build also reaches
# deck-reservation-guard -> poke-byte, and poke-byte has no ZigEmitter entry:
# citing it would make the builtin reachable and break the zig arm. The guard
# pokes the boot stack's guard page, which a reservation this size does not come
# near.
#
# The reservation's size is the one thing the two kinds of harness do not
# share. The RUNG harnesses run bare-metal inside a ~1 GB guest and keep
# demand-lift-floor (104 MB), the driver's own constant, because that is the
# number the rungs were banked at and it is upstream's. The HOSTED harnesses
# (codexir, zigc) run as Linux processes inside the plug's 4 GiB arena and
# take HOSTED_DECK_BYTES: finding 24 measured the fibx subject at 381 MB of
# deck -- eight uncompacted phases at bare metal's per-object sizes, ~153
# deck bytes per subject byte -- against the 104 MB the placeholder gave it,
# and the corruption that followed was the deck overrunning live objects.
# 512 MB covers the measured need with a third to spare; a subject that
# needs more refuses at the region guard rather than corrupting.
HOSTED_DECK_BYTES = 512 * 1024 * 1024

def deck_prologue(deck_bytes=None):
    adv = str(deck_bytes) if deck_bytes is not None else 'demand-lift-floor'
    return f"""let mountain-base = init-phase-allocator
    in let deck-base = __heap-save
    in let deck-set = __deck-set deck-base
    in let deck-adv = __heap-advance {adv}
    in """

DECK_PROLOGUE = deck_prologue()

# CHECK's own two reservations, and the four arguments they feed.
#
# `check-chapter` took five parameters through Update 53 and takes NINE at
# Update 54: the four new ones are `check-base`, `keep-base`, `keep-ceiling`
# and `poison`, the per-definition reclamation work. A harness still passing
# five does not fail loudly -- it UNDER-APPLIES, so `check-chapter ...`
# evaluates to a function, and the first `cr.state` on it surfaces three
# phases later as nine CDX2000 "emit-field-access: unresolved type for field",
# at codegen, naming fields instead of naming the arity. That is COMPILER-18's
# shape (our issue 79) seen from the outside.
#
# Mirrored from the driver rather than invented, `opening.codex:626-633`
# (`compile-type-check`):
#
#     keep-base    = build keep-height
#     check-base   = build check-deck-height
#     check-ceiling= check-base + check-deck-height
#     check-chapter ... check-ceiling check-base keep-base
#                       (keep-base + keep-height - 4194304) poison
#
# The driver scales both floors through `scaled-floor (flags.deck-scale) ...`,
# which lives in opening.codex and cannot be cited from a harness that IS the
# opening. At the default scale of 100 (`compile-flags-default`) `scaled-floor`
# returns the floor itself, so the constants are used directly and the scaling
# is not reproduced. If a rung ever needs a smaller deck, that is where the
# knob goes.
#
# `poison` is 0: the driver passes `poison-check` only under
# `flags.poison-compact`, which is off by default and is a debugging aid.
#
# THE 4 MiB SUBTRAHEND IS THEIRS, not a fudge -- `keep-base + keep-height -
# 4194304` is the driver's own expression, so it is copied whole rather than
# simplified into a number nobody can trace back.
CHECK_SETUP = """let keep-height = demand-check-keep-floor
    in let keep-base = build keep-height
    in let check-height = demand-check-floor
    in let check-base = build check-height
    in let check-ceiling = check-base + check-height
    in """

# `lower-chapter` took eight parameters through Update 53 and takes NINE at
# Update 54. The ninth is `rename : Boolean`, and it is COMPILER-38 -- the fix
# for our own issue 113, where lowering now renames only the colliding binders
# inside a definition (`v`, `v_1`, ...) so two live bindings never share an IR
# name. Under-applying it fails exactly as check-chapter did: a function where
# an IRChapter was expected, and CDX2000 on `.defs` / `.effect-op-names` at
# codegen rather than an arity complaint.
#
# TRUE, because that is what both driver paths these harnesses model pass.
# `compile-frontend-cdx` (opening.codex:842) passes True unconditionally, and
# `compile-frontend-ir` (:768) -- the wire path the plug consumes -- calls
# `compile-frontend-passes ... True`. The only False caller is plain
# `compile-frontend` (:764), which is the no-passes path and not what any rung
# is standing in for.
#
# It is also the flag that makes these rungs EXERCISE COMPILER-38 rather than
# route around it, which is one of the things upstream asked us to confirm.
# LOWER's reservation, and the ceiling that guards it.
#
# The eighth argument is a CEILING and the harnesses passed 0 for it, which
# disables the overflow guard: `deck-short-of` answers False for a 0 ceiling,
# so nothing ever asks whether the deck is running out. That was survivable
# while it was, and stopped being at U54.
#
# WHY IT SURVIVED AND THEN DID NOT. These four harnesses have had a LIVE deck
# (DECK_PROLOGUE) and a 0 ceiling for a long time and were green at U53. U54
# adds the COMPILER-38 rename pass, which builds `v_1` binder names by string
# concatenation -- more deck traffic, through the very helper the fault landed
# in. Measured 2026-09-02: `lower` faulted !EXC=0d (#GP) at `__str_concat+72`
# with registers holding what read as instruction bytes, after 65 good lines
# of output.
#
# PhaseAllocator's own prose describes this exact failure and is why a starved
# deck is not a theory: "Starving that floor to 16 MB did not raise CDX9002; it
# crashed in __text_compare on a garbage pointer, which is the failure the
# guard exists to prevent, with the guard present and compiled in."
#
# So the driver is mirrored here too (`opening.codex:780-785`), the same way
# CHECK_SETUP mirrors its phase. A real reservation, and a ceiling derived from
# it rather than a zero that means "do not check".
# The deck the driver hands the EMITTER, and the reason it exists here even
# though these harnesses mostly do not lift: `lift-ir-for-emit`
# (opening.codex:1722) is the last `build` before x86-64-emit-cdx runs, so it
# is what emission's deck-record extents allocate inside. Without it they
# allocate inside whatever the previous phase left.
# THE PROBE'S LIFT FLOOR, and it is the whole of the next experiment.
#
# At `demand-lift-floor` (104 MB) emission faults 1,224 bytes past
# lift-ceiling. That overshoot says NOTHING -- a bump allocator crossing a
# ceiling always crosses by about one allocation, so the number measures the
# allocation that tripped, not the distance the cursor travelled. Two
# hypotheses predict it equally:
#
#   DECK EXHAUSTION   emission really does use the whole 104 MB deck, and the
#                     guard is right.
#   BIVY vs CEILING   the ceiling is armed while R10 is the BIVY, which sits
#                     immediately above the reservation by construction -- the
#                     2026-08-27 defect PhaseAllocator says arm-at-enter fixed.
#
# They are indistinguishable at ONE ceiling and trivially distinguishable at
# two. Raise the floor and the bivy rises with it, so BIVY vs CEILING faults
# again at the new ceiling + about a kilobyte; DECK EXHAUSTION gets 3x the room
# and either survives or dies far in. One run, one variable, no ambiguous
# outcome.
PROBE_LIFT_FLOOR = 335544320          # 320 MB, against demand-lift-floor's 104

# THE SEAL EMISSION NEEDS, and it is not optional.
#
# `build` publishes its top in deck-reservation-top-cell; `emit-build`
# (Emit/EmitAllocator.codex:11) is `build` MINUS that poke, so the extent
# x86-64-emit-cdx hand-issues (Emit/X86_64Chapter.codex:1249) is armed with
# whatever the last `build` left there -- LIFT's ceiling, not its own.
# emit-build then takes `deck-pos := __heap-save`, so if the bivy frontier has
# risen above LIFT's ceiling by even one allocation, `__deck-enter` arms a
# ceiling the cursor is already past and the first bump inside
# bare-metal-trampoline hits a ud2 before emission allocates anything.
#
# compile-frontend-cdx ends with `compact-phase` (opening.codex:934), which is
# `__heap-restore (__deck-pos)` -- it drags the frontier back inside the deck
# and re-establishes the invariant X86_64.codex:1105 states outright: "a
# compact leaves deck-pos and the bivy frontier equal." We made five `build`
# calls and no compacts, which is why upstream emits a 3 MB compiler with a
# 104 MB LIFT floor and we could not emit a 15-line fib with 320 MB.
#
# Measured 2026-09-02: frontier 1,852,674,888 against a top of 1,852,674,392
# before the seal; lift-base + 496 after it, and both ir_to_x86 subjects then
# emitted clean.
EMIT_SEAL = """let compacted = phase-compact
    in """

LIFT_SETUP = """let lift-height = demand-lift-floor
    in let lift-base = build lift-height
    in let lift-ceiling = lift-base + lift-height
    in """

# UPDATE 55 GAVE LOWERING A KEEP, and the reservation order below is the
# driver's, not a convenience: `compile-frontend-passes` (opening.codex:789)
# builds the KEEP FIRST, then the scratch deck, then sets the deck to the
# scratch base before it calls. `lower-chapter` reads `__deck-pos` as its own
# scratch base (Lowering.codex:1736) and switches between the two itself, so a
# caller that leaves the deck wherever the previous phase left it hands lowering
# an arbitrary scratch region. That is why the `__deck-set` is here and is not
# optional -- it was not needed before U55, because nothing read the position.
LOWER_SETUP = """let lower-keep-height = demand-lower-keep-floor
    in let lower-keep-base = build lower-keep-height
    in let lower-height = demand-lower-floor
    in let lower-base = build lower-height
    in let lower-ceiling = lower-base + lower-height
    in let set-ls = __deck-set lower-base
    in """


# `rename=False` is a BISECTION KNOB and is wrong on purpose, exactly like
# `scan=False` above it: the two driver paths these harnesses model both pass
# True, so nothing may ship with it. It exists because the COMPILER-38 rename
# pass is the one thing lowering gained at Update 54, and one guest with one
# variable is what tells a candidate from a cause.
# AND IT ANSWERS A TUPLE NOW: `(IRChapter, Integer)`, the chapter and the keep
# end. Every caller binds `let (ir, lower-keep-end) = ...`; the second half is
# what the driver tests its saturation against and no rung reads it yet.
#
# `lower-chapter` has moved for three Updates running -- 8 parameters at U53, 9
# at U54, 11 and a tuple at U55 -- and NONE of them read as an arity error.
# Codex curries, so an under-applied call is a FUNCTION VALUE and the failure
# lands one line later against whatever consumes it: `CDX2001: Type mismatch:
# Rec:IRChapter vs Fun` at `run-ir-pipeline`, naming neither this call nor the
# argument it wants. README "Processing a new Update" step 1 has the read that
# catches it before a guest runs.
def lower_call(ch='ch', bound='bound', cst='cst', rename=True,
               renames='[]', colliding='skip-list-text-empty', assignments='[]'):
    return (f"deck-record (lower-chapter {ch} {bound} {cst} (rr.ctor-names) "
            f"{renames} {colliding} {assignments} lower-ceiling {rename} "
            f"lower-keep-base (lower-keep-base + lower-keep-height))")


# CHECK IS THE ONE PHASE THAT CANNOT BE CALLED BARE, and it says so itself.
#
# `check-chapter` issues a `__deck-exit` immediately before the per-definition
# walk and a `__deck-enter` after it (`Types/TypeChecker.codex:2388,2393`), so
# that walk runs OUTSIDE the phase extent and `deck-short-of` reads a live
# cell. `BuildSettings.codex:154` states the requirement in as many words:
# "CHECK is the exception ... so that walk runs OUTSIDE the extent and the
# cell is live." It is the only function in the compiler outside the emitter
# that issues either builtin by hand.
#
# The extent it exits is the CALLER'S, and the caller is the driver:
# `opening.codex:631` writes `deck-record (check-chapter ...)`. Called bare the
# nesting counter goes to -1 instead of 0, and at -1 every `deck-record` inside
# the walk is a no-op -- `emit-deck-enter-builtin` swaps R10 only on the zero
# crossing -- so the per-definition results land on the BIVY while the batch
# machinery reclaims to `cb-bivy-mark` as though they had not.
#
# What that costs is not the phase; it is whoever reads the phase's result
# LATER. `check` prints `cr.types` immediately and is green. `lower` allocates
# the resolved tables, a 328 MB reservation and the whole of lowering first,
# and then reads a Text whose length word is someone else's data -- measured
# 2026-09-02 as !EXC=0d in `__str_concat` with R10 non-canonical, bumped by a
# garbage length. See HARNESS_FIDELITY.md.
def check_call(ch='ch', renames='[]', colliding='skip-list-text-empty',
               assignments='[]'):
    return (f"deck-record (check-chapter {ch} {renames} {colliding} "
            f"{assignments} check-ceiling check-base keep-base "
            "(keep-base + keep-height - 4194304) 0)")

# The checker records a type for every expression, not only for bindings, and
# the driver resolves that table too: opening.codex:635 runs
# resolve-all-expr-types and line 692 rebuilds the UnificationState around the
# result, so what reaches lowering is `expr-types = sorted-et`.
#
# resolve-all-expr-types lives in opening.codex and cannot be cited from here,
# so its body -- a map applying deep-resolve to each entry -- is written as the
# comprehension it is, the same way resolved-env is.
EXPR_TYPES = """in let resolved-et = for e in (sort-expr-types ((cr.state).expr-types)) -> ExprTypeEntry { key = e.key, ty = deep-resolve (cr.state) (e.ty) }
    in let cst = __record-set (cr.state) "expr-types" resolved-et"""

# What lowering gets as its type table, and the second half of clamp.
#
# opening.codex:761 passes `checked.all-bindings`, which compile-type-check
# builds as resolve-all-bindings over `check-result.types & resolved-env`. Both
# halves matter and they hold different things: check-chapter puts the INFERRED
# types of the chapter's defs in `.types`, while register-type-defs puts the
# chapter's declared types -- every record and sum it announces -- in the env.
# Handing lowering `cr.types` alone therefore hands it a table with no entry for
# any type the subject declares.
#
# arith's gauge is `(Gauge { g = n }).g`. Lowering an AFieldAccess lowers its
# receiver with the hint ErrorTy (Lowering.codex:55), so a record literal in
# receiver position has nothing to fall back on: lower-record asks
# lookup-type-split for "Gauge", the env-side entry is missing, and ctor-raw
# comes back ErrorTy, so the IrRecord is annotated ErrorTy and carries it to
# emission. emit-field-access resolved that to no record type and refused with a
# ud2, exactly as it should. Nothing was unresolved; the name was never in the
# table to resolve.
#
# A subject only notices when it reads a field straight off a literal. A field
# read off a NAME goes through the binding, which arrives typed -- which is why
# the compiler chapters the big rungs compile never tripped this, and eighteen
# lines of arith did.
#
# resolve-all-bindings lives in opening.codex and cannot be cited from here, so
# its body -- a map applying deep-resolve to each binding -- is written as the
# comprehension it is.
BINDINGS = """in let resolved-env = for b in ((cr.env).bindings) -> TypeBinding { name = b.name, bound-type = deep-resolve cst (b.bound-type) }
    in let bound = for b in (sort-bindings (cr.types & resolved-env)) -> TypeBinding { name = b.name, bound-type = deep-resolve cst (b.bound-type) }"""

# cst and bound together, which is how a caller always wants them: bound is
# built with cst, so a harness that took one without the other would resolve
# its bindings against an unresolved expression table.
RESOLVED_TABLES = EXPR_TYPES + "\n    " + BINDINGS


# The Codex-visible half of the note above: prose the two hosted harnesses put
# at the head of their driver, written once because two copies of it is the
# same failure the lift itself was.
LIFT_PROSE = """ The lift is opening.codex:1713-1720, and it is on that path only since
 Update 50 -- the release names it in four words, "the DDC witness holds
 after the lambda-lift break". Before that a plug never received a
 `__lam_N`, which is also why nothing noticed these harnesses had none: the
 codexzig fixed point held because NEITHER arm lifted, so the property was
 never tested against a subject carrying a lifted lambda, and the first
 time it was, it failed. It goes between the IR pipeline and
 ir-prune-unreachable-roots, where the driver puts it -- pruning first drops
 the lifted definitions, which are reachable only from the bodies the lift
 rewrote. The ceiling is 0 and emit_harness.py says why it is not the
 driver's."""


# The four bags the driver merges before it decides whether to emit at all:
# lex errors from `toks.errors` (opening.codex:449 wraps the same list), the
# parse bag from `doc.parse-bag` (:485), the resolve bag from `rr.bag`, and the
# type checker's from `cr.state.bag`, which is what `check-bag0` at :620 merges.
#
# It lives HERE, once, and not in the two generators, because a copied list is
# what this tree keeps paying for. `ir-emit-roots` drifted from upstream's six
# to four in BOTH harnesses and no oracle could see it -- being wrong together
# looks exactly like being right. Then the error gate itself existed in one
# harness and not the other, and the ungated one was used all night as an
# oracle: on 2026-08-26 it reported a three-line program to Damian's compiler
# lane as a type-checker soundness hole, then as a miscompile in our plug, and
# it was neither. The seed refused it with CDX2001 and so did the GATED harness
# built from the same plug.
#
# `check_harness_gates.py` still compares the generated files, because a
# constant shared in python does not prove the emitted Codex agrees.
# THE DRIVER BUILDS BAGS OF ITS OWN, and a harness standing in for it gets none
# of them by calling the phases. `opening.codex:479-482` constructs
# entry-dup-bag, shadow-bag and collide-bag directly from `scan.def-headers`,
# because no phase returns them -- so a harness that merges only what the phases
# hand back is missing three whole classes of diagnostic, including the one that
# started this: CDX3006, cross-chapter name collision, is `collide-bag`.
#
# Measured 2026-08-30: a probe defining `is-digit` produces CDX3005 on the seed
# and NOTHING through a harness merging the four phase bags, because the shadow
# check is not a phase. The four were copied faithfully and were never the
# driver's list.
BAG_SIDE = (
    "in let czg-bset = skip-list-text-from-list builtin-names\n"
    "    in let czg-shadow-bag = bag-from-list (check-shadowed-builtins "
    "(scan.def-headers) czg-bset 0 (list-length (scan.def-headers)) [])\n"
    "    in let czg-collide-bag = bag-from-list (check-cross-chapter-collisions "
    "(scan.def-headers) colliding assignments 0 (list-length (scan.def-headers)) [])\n"
    "    in let czg-entry-bag = bag-from-list (check-entry-point-duplicate assignments)\n"
    "    ")

BAG_MERGE = ("bag-merge-all [bag-from-list (toks.errors), doc.parse-bag, "
             "rr.bag, cr.state.bag, czg-shadow-bag, czg-collide-bag, "
             "czg-entry-bag]")


def halt_gate(prefix, artifact):
    """The driver's error gate, for a harness that stands in for it.

    `prefix` names the harness's bag/formatter (`czg`, `irc`); `artifact` is
    what is NOT emitted, for the message. Returns the two Codex lines that go
    after the frontend and before the emit, ending in `else` so the caller's
    next line continues the let-chain.

    CODEGEN-HALTED is the marker the rest of the tree refuses on by name
    (ast/f4_boot.py), which is why the text is that and not a new word.
    """
    return (f"{BAG_SIDE}in let {prefix}-bag = {BAG_MERGE}\n"
            f"    in if bag-has-errors {prefix}-bag "
            f"then print-text ({prefix}-halted (bag-errors {prefix}-bag))\n"
            f"    else ")


def halt_formatter(prefix, artifact):
    """The `<prefix>-halted` definition. The driver's PRINTERS are not
    reachable -- they live in opening.codex, which cannot be bundled beside a
    harness defining `opening` -- so this prints the count and the first error
    rather than the full report."""
    nl = chr(10)
    return (
        "  " + prefix + "-halted : List Diagnostic -> Text" + nl
        + "  " + prefix + "-halted (es) =" + nl
        + "   let n = list-length es" + nl
        + "   in let e0 = list-at es 0" + nl
        + '   in "CODEGEN-HALTED: " & show n & " error(s); no ' + artifact
        # `\n`, NOT a real newline. A Text literal whose opening quote is the
        # last thing on its line is accepted in silence and comes out EMPTY, so
        # the trailing newline this line appears to add has never been emitted
        # by any harness this function generated. `codex_literal` above has done
        # `.replace(chr(10), '\\n')` all along; this literal is built by hand and
        # did not use it. Cobblestone PR 114 makes the compiler refuse it instead
        # of accepting it, which is what turned a cosmetic bug into a build one.
        + ' emitted; first CDX" & show (e0.code) & " " & (e0.message) & "\\n"'
    )


def notices_reporter(prefix):
    """The `<prefix>-report` definition: every diagnostic the bag holds that is
    NOT an error, as UTF-8 bytes ready for stdout.

    WHY STDOUT AND NOT print-text. `print-text` is `cx_print` is
    `std.debug.print`, which is stderr -- and stderr is where the emitted zig
    goes, because `codexzig < prog.codex 2> prog.zig` is the invocation. A
    harness that printed a warning would inject it into the artifact. The plug
    says so itself at `zig-p-cx-deck-report`: "STDOUT, never stderr. stderr
    carries the program's output and every comparison in the ladder diffs it,
    so a measurement written there would corrupt the thing being measured."

    `write-binary` is the only Codex-level route to fd 1 and it takes raw bytes;
    `Foreword chapter CCE` already carries `text-to-utf8-bytes`, the symmetric
    partner of `utf8-bytes-to-text`, so no builtin and no compiler change is
    needed.

    NO EMBEDDED NEWLINE IN A LITERAL, and the reason is stronger than it was.
    This paragraph used to say `czg-halted` ends a line inside a text literal,
    closes it with a bare `"` on the next, and COMPILES -- while the same shape
    with anything after the closing quote raises CDX0007. That asymmetry was
    read as a lexer quirk to route around. It was a DEFECT: the literal was
    silently EMPTY, so every `<prefix>-halted` this file generated has been
    dropping the trailing newline it appears to add. Cobblestone PR 114 makes
    the compiler refuse it, `halt_formatter` now emits `\n`, and "which
    compiles" is no longer true of any tree carrying that fix.

    The decision here is unchanged and now rests on the right reason: the line
    terminator is appended as the BYTE it becomes, 10, after the Text is
    converted, rather than depending on what the lexer accepts. That also
    keeps the accumulator a byte list rather than a Text, so this does not
    rebuild a growing string per diagnostic (finding 22).

    INFOS ARE COUNTED, NOT PRINTED. One port's fifteen units carried 3,685
    CDX4010 `bounds proven` infos against ten real CDX3006 warnings. Printing
    every non-error would bury the thing worth reading in its own telemetry.
    """
    nl = chr(10)
    P = prefix
    return (
        f"  {P}-sev-word : Integer -> Text{nl}"
        f"  {P}-sev-word (s) = if s == sev-warning then \"warning\" else \"notice\"{nl}"
        f"{nl}"
        f"  {P}-notice-line : Diagnostic -> Text{nl}"
        f"  {P}-notice-line (d) ="
        f" \"CDX\" & show (d.code) & \" \" & {P}-sev-word (d.severity) & \": \" & (d.message){nl}"
        f"{nl}"
        f"  {P}-line-bytes : Text -> List Integer{nl}"
        f"  {P}-line-bytes (t) = list-push (text-to-utf8-bytes t) 10{nl}"
        f"{nl}"
        f"  {P}-notices : List Diagnostic, Integer, List Integer -> List Integer{nl}"
        f"  {P}-notices (ds) (i) (acc) ={nl}"
        f"   if i >= list-length ds then acc{nl}"
        f"   else let d = list-at ds i{nl}"
        f"   in if (d.severity) == sev-info then {P}-notices ds (i + 1) acc{nl}"
        f"   else {P}-notices ds (i + 1) (acc & {P}-line-bytes ({P}-notice-line d)){nl}"
        f"{nl}"
        f"  {P}-info-count : List Diagnostic, Integer, Integer -> Integer{nl}"
        f"  {P}-info-count (ds) (i) (n) ={nl}"
        f"   if i >= list-length ds then n{nl}"
        f"   else let d = list-at ds i{nl}"
        f"   in if (d.severity) == sev-info then {P}-info-count ds (i + 1) (n + 1){nl}"
        f"   else {P}-info-count ds (i + 1) n{nl}"
        f"{nl}"
        f"  {P}-report : DiagnosticBag -> List Integer{nl}"
        f"  {P}-report (b) ={nl}"
        f"   let ds = bag-diagnostics b{nl}"
        f"   in let body = {P}-notices ds 0 []{nl}"
        f"   in let n = {P}-info-count ds 0 0{nl}"
        f"   in if n == 0 then body{nl}"
        f"   else body & {P}-line-bytes (\"codexzig: \" & show n & \" info diagnostics not shown\"){nl}"
    )


def frontend_source(src, passes, scan=True, deck_bytes=None, resolve=True, lift=False):
    """The compiler's own sequence from source text to a lowered IRChapter,
    bound as `ir`. Every program built here runs exactly this -- the oracle
    harnesses and the hosted compiler alike -- so it is written once. `src` is
    whatever expression yields the source Text.

    `resolve` runs the RESOLVE phase (build-type-def-map + rewrite-ir-defs)
    and must mirror which driver the harness stands in for: it lives in
    compile-frontend-cdx ONLY -- compile-frontend-ir, the sequence behind
    emit-ir-cce, emits the IR with its annotations unrewritten. A harness
    that dumps IR with resolve on prints record-ty where the seed driver
    prints ctd for every let binding whose nullary ConstructedTy resolves
    to a record -- 930 lines of the ir_to_x86 IR. The CDX harnesses keep it on
    (finding 11 is what skipping it costs THEM); the IR-emitting harness
    turns it off.

    `passes` runs the IR pipeline between lower and emit, where
    compile-frontend-passes runs it. Not cosmetic: IR emission prunes to what
    the opening reaches, so a program that never calls run-ir-pipeline prunes
    Simplify, Occurrence and LambdaLifting straight back out of the unit
    however many chapters were bundled.

    `lift` runs LambdaLifting between the IR pipeline and emission, where
    emit-ir-cce runs it -- and only SINCE Update 50, which is why this
    parameter exists and why it defaults off. The rungs banked their truth
    against a driver that did not lift; the two hosted harnesses stand in for
    one that does. LIFT_PROSE carries the account a reader of the bundle
    needs.

    `scan=False` restores the empty renames/colliding/assignments this used to
    pass, and exists only to bisect a failure against the scan. It is wrong on
    purpose -- the driver computes those values -- so nothing should ship with
    it.
    """
    # opening.codex runs a RESOLVE phase between the IR pipeline and emission
    # (lines 633-634 and 823-825). Skipping it was the defect behind finding 11:
    # without build-type-def-map the emitter's st.type-defs holds no entry for a
    # record declared in the subject, so resolve-constructed-ty fails and
    # emit-field-access refuses with a ud2; and without rewrite-ir-defs the IR
    # still carries unresolved ConstructedTy annotations into emission.
    #
    # This is the one piece the front-end rungs do NOT share: rewrite-ir-defs
    # lives in ResolveTypes.codex and none of their bundles carry it. Adding a
    # chapter to buy a resolved IR dump would grow four rungs whose whole value
    # is being small, and fibx and whole already prove the resolved path.
    # The LIFT phase, and the ceiling it is NOT given.
    #
    # opening.codex:1713-1720 builds a 104 MB deck floor for the lift and hands
    # lift-lambdas its top, so lift-defs can stop rather than overrun. That
    # ceiling cannot be copied here and 0 is not laziness. lift-defs checks
    # deck-bound-short-of, which compares __heap-save against the ceiling, and
    # the driver asks it from INSIDE a phase-wide deck-record extent, where
    # __heap-save reads the deck cursor. No harness built here wraps a phase in
    # such an extent -- which is why every ceiling in this file is 0 -- so
    # __heap-save is the real heap top, already above the reservation the
    # prologue made, and any non-zero ceiling would stop the lift on its FIRST
    # definition and emit a truncated program without saying so. What bounds
    # the lift here is deck_bytes, and the emitted zig fails loud when it is
    # exceeded: cx_bump_alloc panics with "the two cursors met".
    # RESOLVE AND LIFT GET THEIR OWN RESERVATIONS, because the driver takes
    # them and because the guard that catches their absence is real.
    #
    # `compile-frontend-cdx` does not stop at LOWER. It seals that phase and
    # then builds a RESOLVE deck before `rewrite-ir-defs` (opening.codex:853)
    # and a LIFT deck before emission (`lift-ir-for-emit`, :1722) -- and the
    # LIFT one matters even to a harness that never lifts, because it is what
    # hands the EMITTER a fresh deck. A harness that stops reserving at LOWER
    # runs the whole of x86-64-emit-cdx inside LOWER's spent one.
    #
    # That was invisible until the check-chapter wrapper landed. The
    # per-allocation guard (`deck-guard-code`, X86_64Helpers.codex:46) compares
    # R10 against `deck-ceiling-addr` and traps with ud2 -- but the cell is
    # armed at __deck-enter and only holds anything once some `build` has
    # written `deck-reservation-top-cell`. These harnesses took no `build` at
    # all, so the guard was dead code and the overrun was silent. Measured
    # 2026-09-02, first run with reservations present: `ir_to_x86` died
    # !EXC=06 at `write-bytes+154` with R10 at 1,306 MB against LOWER's
    # ceiling near 1,238 MB. PhaseAllocator records the same exception from
    # 2026-08-27 for the same reason.
    #
    # `rewrite-ir-defs` also takes the ceiling the driver passes it, where this
    # passed 0 -- the same "0 means do not check" this file already corrected
    # for lower-chapter.
    RESOLVE_SETUP = """let resolve-height = demand-resolve-floor
    in let resolve-base = build resolve-height
    in let resolve-ceiling = resolve-base + resolve-height
    in """
    lowered = "ir-lowered" if lift else "ir"
    # EVERY ONE OF THESE IS WRAPPED, because two of them take a CEILING and a
    # ceiling read from outside an extent truncates silently.
    #
    # `deck-bound-short-of ceiling band` reads R10. Inside an extent R10 is the
    # deck cursor and the question is "how much of this deck is left"; outside
    # one R10 is the BIVY, which `build` has just advanced to the reservation's
    # top, so the predicate is true on the FIRST item and the walk returns what
    # it has -- nothing. `rewrite-ir-defs-acc` (IR/ResolveTypes.codex:113) and
    # `lift-defs` (IR/LambdaLifting.codex:50) both do exactly that.
    #
    # Measured 2026-09-02, and it cost a second run: giving rewrite-ir-defs the
    # driver's real ceiling while still calling it bare turned "never check"
    # into "always truncate". `ir-defs 0` for a three-definition subject, then
    # CDX2040 "Unresolved call to 'opening'" at codegen -- a silent truncation
    # reported four phases later as a missing entry point.
    #
    # The driver wraps all four: opening.codex:857-859 for the resolve trio and
    # :1726 for the lift.
    RESOLVE = (f"""in {RESOLVE_SETUP}let type-map = deck-record (build-type-def-map (ch.type-defs) 0 (list-length (ch.type-defs)) [])
    in let sorted = deck-record (sort-bindings (type-map & bound))
    in let {lowered} = __record-set ir0 "defs" (deck-record (rewrite-ir-defs sorted (ir0.defs) resolve-ceiling))""" if resolve else
        "" if lift else "in let ir = ir0")
    LIFT = (("\n    " if RESOLVE else "")
            + f"in {LIFT_SETUP}let ir = deck-record (lift-lambdas {lowered if resolve else 'ir0'} lift-ceiling)") if lift else ""

    if scan:
        head = f"""let toks = tokenize {src} 1
    in let scan = scan-document (make-parse-state (toks.tokens) {src})
    in let assignments = build-all-assignments {src} (scan.def-headers) 0 []
    in let colliding = find-colliding-names assignments
    in let renames = build-global-rename-table assignments colliding"""
    else:
        head = f"""let toks = tokenize {src} 1
    in let assignments = []
    in let colliding = skip-list-text-empty
    in let renames = []"""
    # NOT a second spelling of the two phase calls. frontend_source kept its
    # own for as long as it has existed, and that is exactly how it arrived at
    # Update 55 still passing Update 53's arities while check_call and
    # lower_call had been corrected: five harnesses wrong together, which is
    # the shape `ir-emit-roots` had and the shape emit_harness's own prose
    # warns about. There is one spelling of each call in this file now, and the
    # scan tables that make these harnesses differ from the others are
    # ARGUMENTS to it rather than a reason to copy it.
    lower_here = lower_call(renames='renames', colliding='colliding',
                            assignments='assignments')
    lower = (f"""let (ir-raw, lower-keep-end) = {lower_here}
    in let passed = run-ir-pipeline default-ir-pipeline ir-raw False
    in let ir0 = passed.chapter""" if passes else
        f"let (ir0, lower-keep-end) = {lower_here}")
    return deck_prologue(deck_bytes) + head + f"""
    in let doc = parse-document (make-parse-state (toks.tokens) {src}) 0
    in let dr = desugar-document {src} doc (doc.chapter-title) 0
    in let ch0 = dr.dr-chapter
    in let ch = scope-achapter ch0 colliding assignments 0
    in let rr = resolve-chapter ch colliding assignments 0
    in {CHECK_SETUP}let cr = {check_call(renames='renames', colliding='colliding', assignments='assignments')}
    {EXPR_TYPES}
    {BINDINGS}
    in {LOWER_SETUP}{lower}
    {RESOLVE}{LIFT}"""


def pipeline_source(src, passes, scan=True, deck_bytes=None):
    """frontend_source plus the x86 emission, bound as `res`. The rungs that
    dump a CDX want this; the one that emits IR wants the frontend only --
    calling x86-64-emit-cdx there would put the whole back end in the IR's
    reachable set for nothing.

    The deck reservation this used to make here moved into frontend_source: it
    has to be open before the first deck-record extent anywhere, not before
    emission, and by emission the frontend has been allocating for a while.
    """
    # The LIFT reservation, taken here because this is where the driver takes
    # it: `lift-ir-for-emit` is the last build before the emitter runs, and
    # these harnesses do not lift, so nothing else would take it. Emission's
    # deck-record extents then allocate in a deck of their own instead of in
    # whatever RESOLVE left behind.
    return frontend_source(src, passes, scan, deck_bytes) + f"""
    in {LIFT_SETUP}{EMIT_SEAL}let res = x86-64-emit-cdx ir sorted"""


# The line that separates one subject's dump from the next. The truth arm
# splits on it, so it is a contract and not a decoration: change it here and
# split_subjects in oracle_lib.sh stops finding anything, which is why both
# sides read it from this one definition.
SUBJECT_MARK = '=== subject'


def subject_mark(rung):
    return f'{SUBJECT_MARK} {rung} ==='


def subject_end(rung):
    """The closing mark, which is what makes a truncated dump detectable.

    An opening mark alone catches a subject that never started. It cannot catch
    one that started and stopped halfway, and the LAST subject in a unit is
    exactly where that is invisible: nothing follows it to be missing. The run
    can end early without an exception -- codex_vm's reader returns what it has
    when the guest goes quiet -- so a half-written dump would otherwise be
    banked as the reference.
    """
    return f'=== end {rung} ==='


def harness_source(chapter, prefix, subjects, passes=False, scan=True, probe=False):
    """Render the harness chapter. `prefix` names the walkers so two harnesses
    can be bundled in one unit without colliding.

    `subjects` is a list of (rung, text) pairs: the rung name the dump is
    banked under, and the program that rung compiles. Every subject in one
    call shares a unit, a compile and a process, which is the whole point --
    see the module docstring.

    `passes` inserts the IR pipeline between lower and emit, the way
    compile-frontend-passes does. It is off by default because the rungs that
    predate it banked truth without it -- and it is not cosmetic: IR emission
    prunes to what the opening reaches, so a harness that never calls
    run-ir-pipeline prunes Simplify, Occurrence and LambdaLifting straight
    back out of the unit however many chapters were bundled.

    It is a per-UNIT flag, not a per-subject one, and the pairing respects
    that: ir_to_x86's two rungs both run with the passes off, passes_to_x86's both
    with them on. A unit whose subjects wanted different flags would need two
    run functions and would not be one unit."""
    if isinstance(subjects, str):
        raise SystemExit('harness_source takes a list of (rung, text) pairs, '
                         'not a single subject; name the rung it banks under')
    seen = [r for r, _ in subjects]
    if len(set(seen)) != len(seen):
        raise SystemExit(f'duplicate rung name in {seen}; each dump is banked '
                         f'under its own name and they cannot collide')
    # The pipeline's infos are the only evidence it did anything. Without
    # them "the passes ran" is inferred from a byte count, and a pipeline
    # that silently did nothing would look exactly like one that ran.
    info = ('\n      print-line-uni ("pass-infos " & show (list-length (passed.infos)))'
            if passes else '')
    # INSTRUMENT: print the deck geometry BEFORE emission is forced.
    #
    # `let` is strict, so a number bound beside `res` is computed before any
    # print runs and a fault in emission takes the whole dump with it -- which
    # is exactly how the U54 ir_to_x86 fault arrived with nothing to read but
    # registers. The only way to see the geometry emission STARTS from is for
    # a statement to execute before `res` is bound, so under `probe` the emit
    # moves inside the act block behind one print.
    #
    # Wrong on purpose and off by default, like `scan` and `rename`: it moves
    # where emission happens in the harness, so no truth may be banked from it.
    probe_close = "\n    end" if probe else ""
    if probe:
        # LIFT_SETUP ends with a dangling `in `, so the chain is closed with a
        # binding of its own -- otherwise the template's following `in act`
        # reads as `in in act`.
        probe_lift = LIFT_SETUP.replace('demand-lift-floor', str(PROBE_LIFT_FLOOR))
        # THE SEAL THE DRIVER TAKES AND WE NEVER DID.
        #
        # `build` publishes its top in deck-reservation-top-cell; `emit-build`
        # (EmitAllocator.codex:11) is `build` MINUS that poke, so the emit
        # extent is armed with whatever the last `build` left there -- LIFT's
        # ceiling. emit-build then takes deck-pos := __heap-save, and if the
        # bivy frontier has risen above LIFT's ceiling by even one allocation,
        # __deck-enter arms a ceiling the cursor is already past and the first
        # bump in bare-metal-trampoline hits the ud2.
        #
        # compile-frontend-cdx ends with compact-phase (opening.codex:934),
        # which is __heap-restore (__deck-pos) -- it drags the frontier back
        # inside the deck, which is why upstream emits 3 MB with a 104 MB LIFT
        # floor and we could not emit fib with 320 MB. X86_64.codex:1105 states
        # the invariant: "a compact leaves deck-pos and the bivy frontier
        # equal."
        probe_src = (frontend_source("src", passes, scan)
                     + f"\n    in {probe_lift}{EMIT_SEAL}let deck-probe = 0")
        probe_line = ('\n      print-line-uni ("DECK-PROBE lift-base " & show lift-base'
                      ' & " lift-ceiling " & show lift-ceiling'
                      ' & " deck-pos " & show __deck-pos'
                      ' & " heap " & show __heap-save'
                      ' & " lower-base " & show lower-base'
                      ' & " check-base " & show check-base'
                      # THE TWO CELLS THE GUARD ACTUALLY READS. The 320 MB run
                      # proved the fault tracks the CEILING to the byte -- same
                      # 1,224-byte overshoot at both floors -- so R10 is the
                      # bivy and the ceiling is armed. `emit-deck-arm` only
                      # arms on a zero-crossing __deck-enter, which also swaps
                      # R10 to the deck cursor, and the program prologue zeroes
                      # both cells at startup. So either something armed
                      # without the swap, or an extent was entered and never
                      # exited. These two numbers say which, before emission
                      # runs.
                      ' & " ceil-cell " & show (peek-qword deck-ceiling-addr 0)'
                      ' & " counter " & show (peek-qword deck-bound-counter-addr 0)'
                      ' & " res-top " & show (peek-qword deck-reservation-top-addr 0))'
                      '\n      let res = x86-64-emit-cdx ir sorted\n      in act')
    else:
        probe_src = pipeline_source("src", passes, scan)
        probe_line = ''
    decls = '\n\n'.join(f'  subject-{rung} : Text\n'
                        f'  subject-{rung} = "{codex_literal(text)}"'
                        for rung, text in subjects)
    # The mark is printed BEFORE the dump it introduces, so a run that dies
    # inside a subject still names which one. A mark printed after would leave
    # the last dump unattributed, which is the reading a fault most needs.
    # The closing mark is printed by run-<prefix>, AFTER it releases the heap,
    # which is why it is passed in rather than printed here. That ordering is
    # the whole point: the mark now attests that the subject finished AND that
    # its arena went back, so a run that fell over during the release cannot
    # look complete.
    calls = '\n    '.join(f'print-line-uni "{subject_mark(rung)}"\n'
                          f'    run-{prefix} subject-{rung} "{subject_end(rung)}"'
                          for rung, _ in subjects)
    return f'''Chapter: {chapter}

Section: Subjects
{decls}

Section: Byte Dump

  {prefix}-line : Integer, Integer, Integer, List Text -> Text
  {prefix}-line (buf) (i) (hi) (acc) =
   if i >= hi then text-concat-list acc
   else {prefix}-line buf (i + 1) hi (list-push acc (integer-to-text (peek-byte buf i) & " "))

  {prefix}-print-bytes : Integer, Integer, Integer -> [Console] Nothing
  {prefix}-print-bytes (buf) (i) (len) = act
    if i >= len then print-line-uni "."
    else act
      print-line-uni ({prefix}-line buf i (if i + 32 < len then i + 32 else len) [])
      {prefix}-print-bytes buf (i + 32) len
    end
  end

 header-bytes and tail-bytes arrive as lists rather than in the workspace,
 so they need their own walker; splitting on the source of the bytes rather
 than on what they mean keeps both walkers dumb.

  {prefix}-list-line : List Integer, Integer, Integer, List Text -> Text
  {prefix}-list-line (bs) (i) (hi) (acc) =
   if i >= hi then text-concat-list acc
   else {prefix}-list-line bs (i + 1) hi (list-push acc (integer-to-text (list-at bs i) & " "))

  {prefix}-print-list : List Integer, Integer -> [Console] Nothing
  {prefix}-print-list (bs) (i) = act
    if i >= list-length bs then print-line-uni "."
    else act
      print-line-uni ({prefix}-list-line bs i (if i + 32 < list-length bs then i + 32 else list-length bs) [])
      {prefix}-print-list bs (i + 32)
    end
  end

 The symbol map is what the real compiler writes beside a .cdx, and it is
 the only thing that says which bytes are which. It goes through the oracle
 too: a plug that emitted the code correctly but scrambled the map would
 still be wrong.

 A count says a compile went wrong; the messages say what. This prints the
 bag itself so a rung that fails is a rung that explains itself, which is
 the difference between "emit-errors 72" and a diagnosis.

 emit-diags is the length of the same list, printed as a number, because a
 walker that emits nothing and a list that holds nothing look identical and
 the first reading of this had no control to tell them apart.

 The bag gates the byte sections, the way emit-binary-tail gates them on
 bag-has-errors. A compile that recorded an error has ALREADY refused: when
 emit-field-access cannot resolve a record type it emits ud2 where the load
 belonged, deliberately. Printing those bytes anyway produced a binary that
 traps at runtime and a rung that compared two crash dumps -- the harness
 shipping something the compiler had rejected.

  {prefix}-print-diags : List Diagnostic, Integer -> [Console] Nothing
  {prefix}-print-diags (ds) (i) = act
    if i >= list-length ds then print-line-uni "."
    else act
      print-line-uni ("  diag " & show ((list-at ds i).code) & " sev " & show ((list-at ds i).severity) & " " & (list-at ds i).message)
      {prefix}-print-diags ds (i + 1)
    end
  end

  {prefix}-print-lines : List Text, Integer -> [Console] Nothing
  {prefix}-print-lines (ls) (i) = act
    if i >= list-length ls then print-line-uni "."
    else act
      print-line-uni (list-at ls i)
      {prefix}-print-lines ls (i + 1)
    end
  end

Section: Driver

  run-{prefix} : Text, Text -> [Console] Nothing
  run-{prefix} (src) (endmark) = act
    {probe_src}
    in act{probe_line}
      print-line-uni ("check-errors " & show ((cst.bag).error-count))
      print-line-uni ("ir-defs " & show (list-length (ir.defs))){info}
      print-line-uni ("emit-errors " & show ((res.bag).error-count))
      print-line-uni ("emit-diags " & show (list-length ((res.bag).diagnostics)))
      {prefix}-print-diags ((res.bag).diagnostics) 0
      if bag-has-errors (res.bag) then print-line-uni "CODEGEN-HALTED: errors in bag; no binary printed"
      else act
        print-line-uni ("header-len " & show (list-length (res.header-bytes)))
        print-line-uni ("content-len " & show (res.content-len))
        print-line-uni ("tail-len " & show (list-length (res.tail-bytes)))
        print-line-uni "--- symbols ---"
        {prefix}-print-lines (res.symbol-map) 0
        print-line-uni "--- header ---"
        {prefix}-print-list (res.header-bytes) 0
        print-line-uni "--- content ---"
        {prefix}-print-bytes (res.content-buf) 0 (res.content-len)
        print-line-uni "--- tail ---"
        {prefix}-print-list (res.tail-bytes) 0
      end
      {prefix}-release deck-base endmark
    end{probe_close}
  end

 A subject's arena goes back before the next one starts. Nothing here frees as
 it goes -- bare metal and the zig prelude both bump a pointer and never
 collect -- so two pipeline runs in one process is two peaks, and the second
 one killed `zig run` on a 3 GB machine after the first subject had printed
 its whole dump. deck-base is the heap top from the prologue, taken before the
 demand-lift reservation, so restoring to it releases that reservation and
 everything the run allocated on top of it.

 The dump is already printed by the time this runs, so no output moves. The
 closing mark is printed AFTER the release rather than before, which is what
 makes it evidence: a mark in the stream means that subject finished and gave
 its memory back.

  {prefix}-release : Integer, Text -> [Console] Nothing
  {prefix}-release (floor) (endmark) = act
    let reclaimed = __heap-restore floor
    in print-line-uni endmark
  end

  opening : [Console] Nothing = act
    {calls}
  end
'''
