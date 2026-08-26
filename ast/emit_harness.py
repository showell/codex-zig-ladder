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
    lowered = "ir-lowered" if lift else "ir"
    RESOLVE = (f"""in let type-map = build-type-def-map (ch.type-defs) 0 (list-length (ch.type-defs)) []
    in let sorted = sort-bindings (type-map & bound)
    in let {lowered} = __record-set ir0 "defs" (rewrite-ir-defs sorted (ir0.defs) 0)""" if resolve else
        "" if lift else "in let ir = ir0")
    LIFT = (("\n    " if RESOLVE else "")
            + f"in let ir = lift-lambdas {lowered if resolve else 'ir0'} 0") if lift else ""

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
    lower = ("""in let ir-raw = lower-chapter ch bound cst (rr.ctor-names) renames colliding assignments 0
    in let passed = run-ir-pipeline default-ir-pipeline ir-raw False
    in let ir0 = passed.chapter""" if passes else
        "in let ir0 = lower-chapter ch bound cst (rr.ctor-names) renames colliding assignments 0")
    return deck_prologue(deck_bytes) + head + f"""
    in let doc = parse-document (make-parse-state (toks.tokens) {src}) 0
    in let dr = desugar-document {src} doc (doc.chapter-title) 0
    in let ch0 = dr.dr-chapter
    in let ch = scope-achapter ch0 colliding assignments 0
    in let rr = resolve-chapter ch colliding assignments 0
    in let cr = check-chapter ch renames colliding assignments 0
    {EXPR_TYPES}
    {BINDINGS}
    {lower}
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
    return frontend_source(src, passes, scan, deck_bytes) + """
    in let res = x86-64-emit-cdx ir sorted"""


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


def harness_source(chapter, prefix, subjects, passes=False, scan=True):
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
    {pipeline_source("src", passes, scan)}
    in act
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
    end
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
