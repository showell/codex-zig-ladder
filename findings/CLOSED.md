# Findings: closed

Findings whose question is answered and whose fix exists -- absorbed by an
Update, or made and verified on our own arm. They keep their numbers, which
is why the live register skips: a number is a name, not a position.

An entry here is done. If one turns out not to be, move it back to
`README.md` rather than editing a contradiction into its paragraph, and say
in the paragraph what reopened it.

Whether a fix has been SENT is not tracked here -- several of these are fixed
on branches that have not landed upstream, and the ladder's `PRIORITIES.md`
outbound queue is what says where each one stands.

| # | What it was | Disposition |
|---|---|---|
| 1 | `net-recv-raw` truncates odd-length frames | Update 43 -- the count is rounded up before it reaches RBCR; receive-side checksums followed. |
| 2 | The `deck-record` intercept fires on the name alone | Update 43 -- the `deck-record` intercept gates on the defining chapter, not the bare name. |
| 3 | `bytes-to-text` is O(n^2) in 42 of 44 plugs | Update 43 -- one linear `bytes-to-text` in `PlugTypes`, shared by every plug. |
| 4 | TypeChecker uses `capability-names` without citing Capability | Update 43 -- the cite was added, and `check-subset-cites.ps1` written so the class is caught next time. |
| 5 | An unreachable match arm passes without a word | Update 43 -- CDX2096 refuses an arm nothing can reach. |
| 11 | WITHDRAWN as filed: the diagnostics-count claim was our harness | WITHDRAWN as filed; the cause was ours. What survived it closed in Update 46. |
| 12 | `__deck-set` is emitted without its argument, and zig will not compile the result | Fixed -- `__deck-set` is emitted with its argument. |
| 15 | Match guards are dropped by the zig emitter; the arm fires on pattern alone | Update 48 -- native match guards. Was upstream issue 72. |
| 16 | The hosted heap starts at 0 and the deck is a no-op; three corpus oracles observe both | Fixed on the u47 pin (`24c0d925`), sent as PR 75, absorbed by Update 48. |
| 18 | Integer arithmetic in the zig plug was overflow-checked; the language wraps | Fixed on the u47 pin (`78e8da1b`); ours, recorded for the ruling. |
| 19 | Char literals were CCE while Char values were codepoints; resolved by migrating Char to the CCE code | Char migrated to the CCE code on the pin (`ea8d51ac`); confirmed 2026-08-22. |
| 26 | `peek-qword` trapped on every negative qword | Fixed on the branch (`3a490b8c`) -- `peek-qword` no longer traps on a negative qword. |
| 27 | A freshly reserved buffer is zero on bare metal and arbitrary here | Fixed (`c7feba61`) -- a reserved buffer is zero here as it is on bare metal. |
| 28 | `substring` traps on bare metal and clamps here, so a killed program keeps running | Fixed -- `substring` traps out of range instead of clamping. |
| 29 | A substring put on the deck was never on the deck | Fixed and confirmed end to end -- a decked substring is really decked. |
| 30 | The shifts refused counts the hardware simply masks, so we killed programs upstream runs | Fixed -- shift counts are masked as the hardware masks them, not refused. |
| 31 | `address-of` answered 0 for everything, so every object was the same object and also null | Fixed -- `address-of` answers a real identity instead of 0. |
| 33 | No tail calls: recursion depth on this arm is bounded by the thread stack | Update 50's interim push -- PR 81 absorbed verbatim; a self tail call in the zig plug emits as a loop. |
| 35 | A non-ASCII identifier is emitted raw, and zig's identifiers are ASCII | Fixed on the heap branch (`1249ad8a`) -- non-ASCII identifiers are transliterated. |
| 37 | The 512 MB stack is protecting the parser's header scan, and that scan is mutual TAIL recursion | Update 50's interim push -- PR 82 absorbed; the two top-level scans return their item, so each tail-calls ITSELF. |
| 40 | The zig plug calls a curried definition flat, so an under-applied chain it cannot inline will not compile | Update 50's interim push -- PR 83 absorbed verbatim; an over-applied definition applies the rest through the returned closure. |

## 1. `net-recv-raw` truncates odd-length frames

**CLOSED in Update 43.** The count is rounded up before it reaches RBCR.
The follow-on closed too: TCP and IP checksums are now verified on
receive, and a frame claiming more bytes than it carries is refused.

**Diagnosed, fixed in this PR, not compiled here.** Full write-up:
`PLUG_IR_TRANSPORT.md`. Read that one first if you read only one.

`emit-net-recv-raw-helper` derives its `rep insw` word count with
`shr rcx, 1`, which rounds down, so an odd-length frame loses its final
byte. The helper returns the full length anyway and the receive buffer is
never cleared, so that byte comes back as whatever the previous frame
left at the same offset. Silent, plausible, undiagnosed. Severity tracks
the number of odd frames: one gives a wrong program, 33-37 gives
`!EXC=06` inside `parse-expr`.

You have compensated for this before -- `ne2k_inject_rx` in
`tools/codex-vm.c` pads odd frames, with a comment naming the mechanism,
and `ip-total-length` is the guest half. Both are workarounds; the
receive path itself was never fixed, so it is sound only against an
emulator that pads for it. QEMU's `ne2k_isa` does not, and neither would
real hardware.

**Also worth your time:** nothing verifies receive-side TCP checksums. A
substituted payload byte reached the parser unchallenged.

## 2. The `deck-record` intercept fires on the name alone

**CLOSED in Update 43.** The intercept compares the chapter that defined
`deck-record` instead of matching the bare name.

**Reproducible, undecided -- we did not want to guess your intent.**

The x86-64 emitter intercepts any 1-argument call literally named
`deck-record` (`emit-apply` in
`codex/compiler/Emit/X86_64Compound.codex`) and emits `__deck-enter` /
evaluate-arg / `__deck-exit` instead of calling the function. In a unit
that never runs the compiler opening's phase-allocator initialization,
that corrupts allocator state and the program later reads garbage where a
pointer should be. Reproduces on the Update 40 and Update 41 seeds. The
decisive control: renaming the identity function to `my-id`,
byte-identical otherwise, passes.

`PlugTypes.codex` ships `deck-record : a -> a` so plug bundles
type-check outside the kernel, but the intercept fires on the name
regardless of who defined it -- so every plug kernel appears to execute
uninitialized deck enter/exit sequences today. The zig plug passes its
oracle anyway; our lexer subject died deterministically, which can only
be allocation-pattern luck.

Two contracts are possible and we did not want to pick one for you:
either units outside the compiler proper must initialize the phase
allocator (making the `PlugTypes` stub a trap), or `deck-record` outside
the compiler should degrade to a true identity (making the by-name
intercept want a guard -- perhaps firing only when the resolved callee is
the PhaseAllocator chapter's own def).

Each probe is self-contained, no cites, no other chapters. Compile with
`build/compile.ps1 -Src <file> -Out <out>.cdx` and run the cdx.

| file | deck-record | expected |
|---|---|---|
| `repro-crash.codex` | defined as `a -> a` identity, called at two sites | **page fault** (`!EXC` in `__linked_list_to_list`, garbage list pointer) |
| `control-renamed.codex` | byte-identical, every `deck-record` renamed `my-id` | passes: `toks 2` / `errs 0` |
| `probe-site-record.codex` | kept only around the record construction | page fault |
| `probe-site-ctor.codex` | kept only around nullary-ctor arguments | page fault |
| `probe-deck-init.codex` | as repro, plus `__deck-set __heap-save` first | still faults -- base init alone is not the fix |
| `probe-seeded-signal.codex` | none (control shape) | `toks 2` / `errs 1` / `e0 42` |

The shape is distilled from `Syntax/Lexer.codex` (`tokenize-collect`): a
state record threaded through a recursive collector via a variant
payload, with a LinkedList field read at the end.
`probe-seeded-signal.codex` is the honest-signal template -- a probe whose
expected output is an empty list cannot tell "correct" from "the misread
slot happened to hold zero", so it seeds 42 and demands it back.

## 3. `bytes-to-text` is O(n^2) in 42 of 44 plugs

**CLOSED in Update 43, and generalised past what was asked.** Rather than
fixing the copies, `PlugTypes` now holds the one linear definition every
plug shares.

**Fixed for the zig plug in this PR. The other 41 are untouched and will
hit the same wall at the same scale.**

Not a new discovery, and that is the point: `CSharpPlug.codex` and
`RecheckPlug.codex` already carry the linear version, with a comment
recording that the old accumulator "hung on the ~9.7MB compiler IR before
the plug emitted anything". The fix never propagated. The remaining
plugs still concatenate onto an accumulator per chunk, which copies the
accumulator every time.

For a 1.18 MB IR that is ~2.7 GB of allocation against a ~3 GB heap, so
the zig plug printed `OUT OF MEMORY` and emitted nothing.

One trap for anyone tempted by a smaller change: the 256-byte chunk is
deliberate. The inner loop is quadratic too, so cost is
`N^2/2C + N*C/2` and 256 sits near the `sqrt(N)` optimum. Raising it
alone makes things worse -- 8192 measured 4.6 GB and still died.

## 4. TypeChecker uses `capability-names` without citing Capability

**CLOSED in Update 43, by an instrument rather than a cite.** The cite was
added, and then `build/check-subset-cites.ps1` was written to build every
chapter against only what it cites -- which caught `BootPaint` borrowing
`to-unicode` with no cite on its first run. This was the better answer:
the finding was one instance of a class that only a subset build can see,
and the class is now measured from the inside.

Small, and only visible from outside a whole-foreword build.

`Types/TypeChecker.codex:3400` is

```
  capability-vocabulary : List Text
  capability-vocabulary = capability-names
```

and `capability-names` is defined in `foreword/core/Capability.codex:198`.
TypeChecker's cites are Build Settings, Phase Allocator and Tuple. There
is no cite for Capability.

Nothing is broken in the real build, because the whole foreword is
present and the name resolves. It surfaces when a subset of the compiler
is bundled into one unit -- we hit it building a type-check subject for
the plug oracle, where the bundler carries only what is named or cited and
the definition was simply absent.

Worth a one-line cite if you want the dependency declared. We mention it
because it is the same shape as the `deck-record` intercept above:
something the monolithic build makes invisible, which a subset build
notices immediately. If you care about the subset property -- and the plug
bundles are exactly that -- these are the cases that break it.

## 5. An unreachable match arm passes without a word

**CLOSED in Update 43.** CDX2096 refuses an arm nothing can reach.

`Types/TypeCheckerInference.codex:665-666`, in `lint-arg-narrowing`:

```
   in when declared-param
    is IntegerTy (lo) (hi) (mode) ->
     ...
    is otherwise -> st
    is otherwise -> st
```

Two identical catch-alls at the same indentation, in the same `when`. The
second cannot be reached. It looks like a copy-paste slip rather than
intent, and it compiles silently.

We scanned the rest of `codex/compiler` for the same shape and this is the
**only** instance -- 97 other consecutive `is otherwise` pairs are nested
`when` expressions where an inner catch-all sits directly above an outer
one, which is legitimate. So the dead arm is a one-off; the diagnostic gap
is the finding.

**The gap.** Codex says a great deal about far subtler hazards. CDX3005
spends a paragraph on shadowing a builtin, and rightly -- it explains that
the danger is cost rather than answer, and cites the Hamt case that sent
four chapters quadratic. CDX1070 refuses an application that ends at a
newline and names three ways to fix it. Against that, an arm that can
never run seems like something you would want to hear about, and nothing
says anything.

We noticed because zig rejects a second `else` prong outright, so the
emitted code would not compile. Our plug drops the later catch-all, which
is safe precisely because it is unreachable -- but the reason we looked was
a zig error, not a codex one.

Offered as a diagnostic suggestion rather than a bug: an unreachable-arm
warning would have caught this, and the compiler already has the arm list
in hand where it checks exhaustiveness.

## 11. WITHDRAWN as filed: the diagnostics-count claim was our harness

**The original claim was wrong and the cause was ours.** It reported a
DiagnosticBag reporting 72 errors with an empty diagnostics list, and asked why
the two targets disagreed about the number. The answer is that our harness
stands in for `opening.codex` and skipped a phase the driver runs:

    type-map      = build-type-def-map (checked.scoped.type-defs) ...
    stds          = sort-bindings (type-map & checked.all-bindings)
    resolved-defs = rewrite-ir-defs stds (ir.defs) resolve-ceiling

Without `type-map` the emitter's `st.type-defs` has no entry for a record
declared in the subject, so `resolve-constructed-ty` fails, and without
`rewrite-ir-defs` the IR still carries unresolved `ConstructedTy` annotations
into emission. Everything downstream followed from that. Nothing here was a
defect in the depot.

### What survives: two record layouts that disagree

**CLOSED in Update 46** (`adfae029`, seed 12B07296). The unresolved-type
fallback -- the by-list layout below -- is deleted, and the branch now raises
the same refusal `emit-field-access` raises, which is the asymmetry this
section asked about. The release gate and the BVT never took the branch, so it
was latent exactly as described. Credited to PR 67 in the change and in
`docs/PM/Active/GitHubUpdates/GitHubUpdate46.md`.

The account below is kept as filed. Nothing on our side worked around it: our
half was a harness that skipped RESOLVE, and running RESOLVE is the driver's
shape whether or not the fallback exists.

`emit-record` (X86_64Compound.codex:1751) chooses a layout by whether the
record's type resolved:

| | ranked by | offsets |
|---|---|---|
| type resolves -- `build-cce-byte-offsets` | `field-sort-key` = `width-prefix(width) & name` | cumulative field widths |
| type does not -- `emit-store-record-fields-by-list` | the raw field name | `rank * 8` |

Every reader uses the first rule unconditionally: `cce-byte-offset-and-type`
(via `accumulate-offset-width-sort`) in `emit-field-access` and in
`emit-record-set-builtin`. The two rules coincide only when every field is
eight bytes wide, because only then does the width prefix stop affecting the
order and the uniform slot match the real width.

`probe-record-layout.codex` is the smallest record where they part:

    Box = record { flag : Boolean, items : List Integer }

    resolved:  items @ 0   flag @ 8    size 9
    fallback:  flag  @ 0   items @ 8   size 16

A Box built through the fallback puts `flag` where `items` is read from, so
`b.items` yields the boolean -- 0 or 1 -- and `list-length` of that reads
`[0 - 8]`, which faults with CR2 at the top of the address space. That is
exactly the crash we chased: `__list_snoc + 3`, `RDI = 0`,
`CR2 = fffffffffffffff8`, called from `bag-add`.

### What is NOT established

**We could not reach the divergent path through `opening.codex`.** The probe
compiles and prints `3` through the normal driver, because the type resolves and
the first layout is used. We reached the second one only with a driver that
skips RESOLVE, which is our bug and now fixed. So this is a latent inconsistency
visible by inspection, not a demonstrated defect, and it may be unreachable in
practice.

The part that seems worth a look regardless is the asymmetry. Faced with the
same unresolved type, `emit-field-access` records an error and emits `ud2` --
it refuses, loudly. `emit-record` silently lays the record out by a different
rule than every reader will use. If the fallback is genuinely unreachable, it
could be an error instead; if it is reachable, it is silent corruption.

## 12. `__deck-set` is emitted without its argument, and zig will not compile the result

**Found 2026-08-17 against Update 45 / seed 270227BE. Fixed in this PR.**

`ZigEmitter.codex` mapped the builtin to a bare constant and never touched
`args`:

    ZigBuiltinEmitter { name = "__deck-set", emit = \args ctx d ty -> "0" },

Answering `0` is right. There is no deck in the zig target, so pointing the
deck cell somewhere is genuinely a no-op. Dropping the argument is the defect:
the argument is a binding at the call site, and zig refuses to compile a
binding whose only consumer disappeared.

    error: unused local constant
    b2: { const deck_base = cx_heap_save(); break :b2 b3: { _ = 0; ...

The remedy was already written two lines below, in the prelude, for the same
problem:

    // address-of answers 0 here by X86_64Compound's own account of
    // targets without it; the argument is still evaluated so its binding
    // stays used.
    fn cx_address_of(v: anytype) i64 { _ = v; return 0; }

So this is the second instance of a pattern that has a solved first instance
sitting beside it. `__deck-set` is the only other entry in the builtins table
that ignores `args` and takes one -- `__deck-enter`, `__deck-exit` and
`__deck-pos` also ignore `args`, and all three are nullary.

### Why it stayed latent

Both of the compiler's own callers use the address for something else as well,
so the binding survives on its second consumer:

    build (size) =
     let p = __heap-save
     in let deck-init = __deck-set p
     in let guarded = deck-reservation-guard p size      <- p used again

    init-phase-allocator =
     let base = __heap-save
     in let deck-init = __deck-set base
     in base                                             <- and here

`passes_to_x86` transpiles both of those functions to zig and compiles clean. It took a
caller that only sets, which is what our harness prologue is once it names
`init-phase-allocator` to turn the deck intrinsic on.

The general shape is worth carrying to the other 43 plugs: a target that has no
analogue for a builtin still has to consume that builtin's operands, or it
silently changes which bindings are live. A target whose compiler happens not to
mind unused locals would not have reported this at all.

## 15. Match guards are dropped by the zig emitter; the arm fires on pattern alone

**Found 2026-08-18 by an emitter audit; both arms measured 2026-08-19 against
Update 46 / seed 12B07296. Filed upstream as issue 72 (still present at
Update 47). CLOSED 2026-08-20: Update 48 implements match guards natively,
and its release adds a Match guards section to `plug-oracle-arith.codex`
aimed at exactly this failure shape ("no refusal, a wrong value"). Verified
at the u48 verbatim census re-pin: `plug-oracle-arith` -> match with the
guard rows in it -- two arms on one constructor with different guards, a
guard on a catch-all, a guarded tuple payload, all answered right by the
shipped emitter. `tonight.sh` (whose step 2 existed to measure this
finding's bare-metal half) deleted in the closing commit.**

`IRBranch` carries `guard : IRExpr` (codex/compiler/IR/IRChapter.codex:54) and
`ZigEmitter.codex` never reads it -- the word `guard` does not appear in the
emitter. A guarded arm becomes a bare switch prong and fires whenever its
pattern matches, so the program compiles cleanly on both arms and answers
differently. No refusal, a wrong value.

The probe is `findings/probe-match-guard.codex`: one guarded arm plus a
catch-all, chosen because two arms on the same constructor would be duplicate
switch prongs, which zig rejects, and a refusal would be the lucky case.

    classify : Val -> Integer
    classify (v) =
     when v
      is Num (n) when n < 0 -> 1
      is otherwise -> 0

Bare metal answers `guard-taken 0 / guard-taken 1 / otherwise 0`; the zig arm
answers `1` on the first line.

The machine-code plugs all honour the guard (X86_64Compound.codex:1879,
Arm64CodeGen3.codex:683, RiscVCodeGen3.codex, T3IsaEmitter.codex:980). Neither
the csharp nor the python emitter contains a read of `branch.guard` either;
only zig is measured here.

A fix cannot put a bare `if` inside the prong, because a zig switch prong
cannot re-dispatch to the arms below it. The direct shape is an if-else chain
(pattern test and guard as one condition) for a `when` that contains any
guarded arm.

## 16. The hosted heap starts at 0 and the deck is a no-op; three corpus oracles observe both

**Found 2026-08-19 by the corpus census (the first differ-class verdicts of
the run); zig arm measured by `corpus_run.py`, bare-metal arm is the depot's
hand-verified `.expected` oracles. Fixed on the pin (`24c0d925`) and proven
2026-08-19: 14/14 sweep plus the banked census, all three observing oracles
MATCH. Sent 2026-08-19 as PR 75 (the three-commit chain off `8f997bd8`);
replay spot-verified 5/5 on seed `800A7683`.**

One passage of ZigEmitter (the prose above `zig-name-map`) makes two
semantic choices and documents them as checked-not-assumed. The corpus is
the check, and it caught both:

- **`__heap-save` answers 0 on first call.** Bare metal boots with
  `mov r10, 6291456` (bare-metal-heap-base, 6 MB; essay random848), so a
  heap address is never 0 there. `codex/test/arith-narrow-proven` asserts
  exactly that ("__heap-save proves as a structural heap-address fact"):
  expected `mark-ok`, zig arm prints `mark-zero`.
  **The C# plug shares this defect verbatim** (`static long _ptr = 0;
  heap_save() => _ptr;`, CSharpEmitter.codex:637) and can never catch it
  itself -- its witness path stops at "compiles". Source-read only, not
  yet run.
- **`__deck-enter` / `__deck-exit` / `__deck-pos` are mapped to literal 0.**
  The C# runtime implements the real rule (deck_enter swaps _ptr with
  _dptr saving _bivy; deck_exit restores), and the depot tests observe it:
  `deck-bracket-contract` expects "enter switches to the mark : yes", the
  zig arm answers "no"; `deck-record-contract` likewise for "argument
  evaluates on the deck". The prose's claim "this target has no deck"
  conflates having no memory pressure with having no observable
  semantics; deck position is observable.

The fix (applied in `24c0d925`, swept and census-proven): init `cx_hp` at
6291456 to mirror the boot value -- cx_buf_want then zero-fills a 6 MB
prefix on first heap touch, which is the guest's own boot behavior -- and
port the C# deck rule (~4 small functions) with the three name-map
entries pointed at them. C# is gold for the deck RULE; the heap base is
bare metal's own number, not C#'s.

## 18. Integer arithmetic in the zig plug was overflow-checked; the language wraps

**Found 2026-08-19 by the corpus census (three crash-class verdicts); ruling
checked at the desk 2026-08-20; fixed on the pin (`78e8da1b`) the same day.
Ours, not an upstream defect -- recorded for the ruling and the asides.**

`bloom-spread`, `consistent-hash-balance` and `particle-spread` all died
with `panic: integer overflow` in hash-mixing code. The ruling that wrap is
the language's rule rests on five converging sources: CodexSubtypes.md says
Integer IS the 64-bit machine word; the IR names behavior wherever it
deviates (IrAddRealTrapping/Saturating, clamped bounded fields) and
IrAddInt is the plain op; the C# plug emits bare `+` on `long` in C#'s
default unchecked context; bare metal emits `lea`/`add`/`imul`/`neg` with
no `jo` anywhere; and decisively, Foreword's own BloomFilter iterates
`hash * 31 + c` unbounded, mixes with `bit-shru`, then tests `if h < 0
then -h` -- a product of positives that only goes negative by wrapping.

The fix: `+%`/`-%`/`*%` on the integer binop rows, `-%` for non-real
IrNegate, `cx_ipow` mirroring `__ipow` (negative exponent -> 0, wrapping
square-and-multiply) in place of `std.math.pow` which panics on both
overflow and negative exponents, shift counts masked `& 63` (x86 `cl`
semantics; C# `<<` on long masks identically), and a wrapping accumulator
in `cx_text_to_integer`. All three subjects MATCH their `.expected`.

Upstream asides, source-read only, each needing a demonstration before
filing:

- The **python plug** emits `+` on unbounded ints with no 64-bit mask, so
  it silently diverges from bare metal on any overflow; the JS plug is
  worse (f64 loses exact integers past 2^53).
- The **C# plug maps IrPowInt to `^`** (CSharpEmitterExpressions.codex:984),
  which is XOR in C#, not exponentiation.
- **plug-oracle-arith has no overflow row** to catch any of this; a
  wrap-observing row is the oracle proposal that would expose the fleet.

## 19. Char literals were CCE while Char values were codepoints; resolved by migrating Char to the CCE code

**Found 2026-08-18 by an emitter audit (probe written then); caught live by
the census differ `text-fold-indexed` 2026-08-19; resolved by convergence
on the pin (`ea8d51ac`) 2026-08-20. Ours -- the codepoint representation
was the plug's own choice; the migration is the fix, not a report.**
CONFIRMED CLOSED 2026-08-22: natives from the heap branch rebased onto u49
(PR 76 absorbed) ran prim-char, probe-char-ops and probe-char-literal
byte-identical on both arms; the four ledger rows were deleted.

IrCharLit was emitted as its raw IR payload (a CCE code) while `char-at`
answered a Unicode codepoint, so `char-at s i == 'x'` lived in two
alphabets and was false for every letter -- a wrong answer, not a
refusal, on both probes and on the depot's own vowel-count test
(`text-fold-indexed`: expected 3/2/4-style counts, zig arm answered 0s).

Resolution is the identity model bare metal and the C# plug share:
char-code / code-to-char vanish, char-at is the same bare read as
char-code-at, cx_char_to_text stores one raw byte, is-letter / is-digit
use the CCE bands (13..64 and 97..127 letters, 3..12 digits -- read off
`emit-is-letter-builtin` itself). The codepoint model was structurally
lossy (CCE aliases canonicalise through any code->cp->code detour,
corrupting byte-wise text rebuilds); codepoints now exist only at the I/O
boundary.

Both-arms evidence, line-identical on every row (bare metal run on the
droplet appliance, zig arm through the rebuilt natives, 2026-08-20):
`probe-char-literal` answers found-x 1 / found-a 0 / lit-lit 1 /
code-of-x 36 on both arms (the zig arm answered found-x 0 before the
migration); `probe-char-ops` answers all nine rows identically on both
arms, including letter-accent 1 and letter-cyrillic 1 through the second
band, which the old a-z/A-Z test refused. `text-fold-indexed` and
`shadow-builtin-fold` (finding of the same census day: builtin
interception ignored user shadowing, fixed in `993d9f8b` -- whose first
cut broke every ladder rung by yielding for subj-deck-record too, a name
whose definition zig-skip-def deliberately never emits; the yield now
exempts exactly the skip list) both MATCH their `.expected`.

LANDED 2026-08-20: sweep 14/14 green over the batched change-set and the
census re-banked with 42 verdicts moved -- the five hunt targets to
match, differ/crashed/codexir buckets all EMPTY. The unplanned yield of
the batch: all 36 hosted-compiler (codexir) aborts healed, and 15 of
those programs now match outright.

CORRECTED 2026-08-20 (evening, measured at the u48 verbatim re-pin):
the aborts were attributed here to finding 18's wrap fix alone, and
that was wrong by majority. Panic-classifying every codexir abort under
the verbatim emitter: **33 die on `codepoint outside the CCE tiers`
(finding 19's char-CCE class -- cx_char_to_text framing a raw CCE byte
inside the compiler's own decode-escapes) and 4 on `integer overflow`
(finding 18's wrap class).** The healing was real and the batch fixed
all of it, but the credit belongs mostly to the char migration. The
attribution went unexamined because the fixes landed as one change-set
and nobody classified the panics per-program until a newcomer
(gop-composite-vclip, new in u48) forced the question.

## 26. `peek-qword` trapped on every negative qword

**Found 2026-08-21 by tier 5 of the unit inventory, by accident, before anyone
thought to test negative values. Ours. FIXED on the branch (`3a490b8c`).**

Bare metal loads eight bytes as one 64-bit value, and every bit pattern is a
legal `i64`. The plug rebuilt it with checked multiply-and-add:

    while (cx_j >= 0) : (cx_j -= 1) cx_v = cx_v * 256 + cx_heap_mem[...]

which traps whenever the top byte sets the high bit -- that is, on every
NEGATIVE qword. `findings/probe-peek-qword.codex` isolates it to eight bytes:
over `00 00 00 00 00 00 00 FF`, bare metal answers `-72057594037927936` and
the plug panicked with integer overflow. Wrapping arithmetic reproduces the
load exactly.

## 27. A freshly reserved buffer is zero on bare metal and arbitrary here

**Found 2026-08-21 by `findings/prim-buffers.codex`, both arms, same program.
Ours. FIXED same day (`c7feba61`).**

    assertion                       zig arm   bare metal
    neighbours undisturbed          NO        yes
    fresh span is zeroed            NO        yes
    write past end lands on it      yes       yes

A buffer is a span of the heap reserved by `__heap-save` then
`__heap-advance`. On bare metal that territory has never been written, so it
reads as zero -- the plug's own prelude comment claims to match "an arena the
guest zero-fills at boot". On this arm it reads as whatever was last there.

**FIXED** (`c7feba61`), and the mechanism was not the one recorded first.

`std.mem.Allocator.alloc` memsets every allocation to `undefined`
(`~/zig-0.16.0/lib/std/mem/Allocator.zig:301`, in `allocBytesWithAlignment`,
which every `alloc`/`create` funnels through), and `undefined` is **0xAA** in
Debug and ReleaseSafe. The 1.5 GiB region therefore arrived filled with 170s
rather than zeros.

**Build-mode dependent, which is why it hid.** That `@memset(_, undefined)` is
elided in ReleaseFast and ReleaseSmall, so the old code was zero-and-lazy in a
release build and 0xAA-and-committed only in Debug/ReleaseSafe. `zig build-exe`
defaults to Debug, which is what the natives are built with.

**Scope, precisely.** The fix zeroes the RESERVATION. Sub-allocations through
`cx_gpa` -- `cx_ll_empty`, `cx_new`, `cx_concat` and friends -- still go
through `Allocator.alloc` and still get memset to 0xAA individually. They are
initialised immediately so that is believed benign, but the claim to make is
"spans carved by `__heap-advance` now read as zero", which is what the probe
measures, not "no 0xAA anywhere". `findings/probe-fresh-span.codex` printed it plainly: 256
nonzero bytes of 256, `170 170 170 ...`, in two separate spans, where bare
metal reads all zeros. Reserving with `rawAlloc` instead skips the wrapper's
memset and the same probe reads zero. `rawAlloc`'s doc warns it is "not
intended to be called except from within the implementation of an
`Allocator`" -- which is exactly where we are, since `cx_bump_alloc` and
`cx_heap_vtable` are one. Worth knowing: the zeroing is an **OS** guarantee
(Linux `mmap(MAP_ANONYMOUS)`, Windows committed pages), not an `Allocator`
interface guarantee, and on wasm `page_allocator` is a reusing pool that makes
no such promise.

Two things follow that were not about zeroing at all. The memset **touched
every page of the reservation**, committing all 1.5 GiB up front -- the exact
opposite of the "resident stays proportional to what is touched" property the
design comment claims for it. And a top byte of 170 is negative, which is how
finding 26 got tripped by a qword read from supposedly-fresh memory.

The first mechanism I recorded here -- `cx_bump_free` rewinding the frontier
so a later reservation lands on written bytes -- was tested and **refuted**
before the real one was found: with free made a no-op, so no byte is handed
out twice, the span still read non-zero. Nothing was being reused; the region
was never zero to begin with. Do not repeat the free-rewind test; it has been
run twice.

Consequence: any code that assumes a reserved span reads as zero is correct on
bare metal and wrong here. `init-emit-workspace` reserves the 8 MB code buffer
and 2 MB data buffer exactly this way. It is also how tier 5 found finding 26:
a qword read from supposedly-fresh memory had a high top byte.

Also tested and refuted for finding 24, twice over. Rebuilding `codexir` with
`cx_bump_free` made a no-op does not change that crash -- identical frames,
same site. Neither does reserving the region with `rawAlloc` so it is
zero-filled rather than 0xAA: same crash, same frames. **The 0xAA fill is not
behind finding 24**, which the observed evidence already hinted at -- the
corrupt length there is pointer-shaped (order 1.3e14), not 0xAAAA-shaped.

That test did confirm the resource half of finding 27 by accident. The same
compile takes **38.0s real / 15.3s sys** with the 0xAA fill and **11.4s real /
1.8s sys** with `rawAlloc`. The memset was touching every page of the 1.5 GiB
reservation, and it cost 13.5 seconds of system time per run. Independently
measured at 512 MiB: `Allocator.alloc` gives 525,952 KB max RSS and 131,178
minor faults, `rawAlloc` gives 1,664 KB and 107.

**Note for finding 24:** the out-of-buffer write is unchecked on BOTH arms, so
that is upstream's semantics and not a divergence. The last named suspect for
the `codexir` corruption is therefore exonerated as a *divergence*, though an
unchecked write remains a possible mechanism on either arm. This zero-fill gap
is the better candidate and did not exist as a hypothesis before tier 5 ran.

## 28. `substring` traps on bare metal and clamps here, so a killed program keeps running

**Found 2026-08-21 by `findings/prim-text.codex` measuring a family that had
no row anywhere. Ours. FIXED same day.**

    findings/probe-substring-trap.codex        zig arm    bare metal
    "about to ask for 40 bytes of a 5-byte"    printed    printed
    answered length                            5          <died>
    "still running, so this arm clamped"       printed    <died>

Bare metal dies with `EXC=06` -- invalid opcode, the UD2 -- and the request is
still on the stack at the fault: `S[10]=5` the source length, `S[20]=0x28` the
40 that was asked for. It never reaches the second print.

**Upstream ruled on this deliberately and wrote down why.** Substring once
took its start and length on trust; `substring a 0 40` on a five-byte string
answered `abcde   s       PASSWORD-1234567890     ` -- the whole of the next
allocation, returned verbatim. The fix traps rather than clamps, at Damian's
ruling, "because a clamp turns a program's bug into quietly wrong data, and
this project's virtues say a safety guarantee is never silently degraded"
(`Emit/X86_64Builtins.codex:640`; `emit-substring-bounds` at `:666` is three
UD2s -- negative start, negative length, and length past the end).

`cx_substring` clamped with `@min` on both ends. So the plug took a program
upstream kills and ran it on quietly wrong data: **the exact outcome the
ruling exists to prevent, reintroduced by the backend that was supposed to
mirror it.** Asked for 40 bytes of a 5-byte text, it answered 5 and carried on.

**FIXED.** Three checks mirroring bare metal's, in the same order, including
the one that is easy to get wrong: the third compares by SUBTRACTING rather
than adding, because `start + len` can wrap and the input that wraps it is the
one an attacker picks. `s.len - cx_a` cannot wrap because the guard above pins
`cx_a` to `[0, s.len]`. Verified standalone on 0.16.0: all seven in-range
shapes the tier file asserts still answer identically, and `substring s 1
maxInt(i64)` now panics where it used to return the tail.

**No rung can have depended on the clamp**, which is why this was invisible to
eleven days of sweeps: a subject that went out of range would trap on bare
metal, so its truth would be broken and the rung red before the comparison
ever ran. Only a test that deliberately goes out of range can see it, and no
tier file could hold one -- a trap would take that file's other assertions
down with it, which is why this probe lives on its own.

**The general shape is worth more than the instance.** This is a bounds check
the plug weakened without anybody choosing to. The refusal net catches
constructs the emitter cannot render; it says nothing about a helper that
renders a construct with a *weaker guarantee* than the original. Ranked by
what it costs to find: sweeps cannot see it, the corpus can only see it if a
test program is deliberately out of range, and a source read finds it in
minutes once you know to compare guarantee to guarantee. Worth a pass over
every `cx_*` helper that takes an index or a length, asking not "does it
compute the same answer" but "does it fail on the same inputs".

## 29. A substring put on the deck was never on the deck

**Found 2026-08-21 by `findings/probe-deck-substring.codex`, both arms, same
program. Ours. FIXED same day and CONFIRMED end to end** through a `zigemit`
built from the fix: `BYTES survived` reads yes, and the concat control still
reads yes on both arms.

    probe-deck-substring                zig arm   bare metal
    length survived                     yes       yes
    BYTES survived                      NO        yes
    concat bytes survived               yes       yes

**A corruption, not a cost curiosity, and the sharper half of finding 28's
family.** Bare metal's substring copies, and it bumps `r10` -- the LIVE
allocation register, which between `__deck-enter` and `__deck-exit` is the
deck cursor. So a substring taken inside a deck extent lands ON THE DECK and
outlives a rewind of the frontier. That is the entire purpose of the deck.

`cx_substring` allocated nothing. It returned a slice of its argument, so the
bytes stayed where the argument's bytes were -- on the frontier, if that is
where the source was built. **A deck extent cannot move them, because there is
no allocation for the extent to redirect.** The value looks decked, reports the
right length, and points at memory the next `__heap-restore` hands back. The
probe allocates over the reclaimed span afterwards so the dangling read is
visible instead of accidentally still correct.

**Live in the shape that matters.** `emit-all-defs` brackets every definition
and carries accumulator tables across the brackets, and the tables that
motivated the whole `Text` narrowing are `List Text`. A text that was supposed
to be copied onto the deck but is secretly a slice of reclaimed frontier is a
table holding garbage -- and it would present as a length or a pointer read
out of whatever object landed there next, which is the shape finding 24 has
been chasing. Not a claim that it IS finding 24: `codexir` never calls
`__heap-restore`, so nothing is reclaimed in that binary. It is the same
failure mode in a different phase.

**Three aliasing sites, all fixed:**

- `cx_substring` now copies through a new `cx_text_dup`, which allocates from
  `cx_gpa` and therefore from the live cursor -- deck inside an extent,
  frontier outside, which is exactly bare metal's rule.
- `cx_text_split` returned a slice per piece; every piece now copies. Bare
  metal's `__text_split` builds real text blocks.
- `cx_concat` opened with `if (b.len == 0) return a;`. Bare metal has no such
  case: both `emit-str-concat-fast-bump` and `emit-str-concat-slow-alloc` bump
  `r10` unconditionally, so `a & ""` is always a fresh block at the live
  cursor. The short-circuit is gone.

**Concat was tested beside it and came out CLEAN on both arms, which is why
the test was worth running.** Our in-place path fires when the left operand
ends exactly at `cx_hp` -- and inside an extent `cx_hp` IS the deck cursor, so
a frontier-resident operand fails that test and falls back to a copy that
lands on the deck. Accidentally correct, for a reason worth keeping: **the
fast path is guarded on the LIVE cursor rather than on a remembered one.** A
prediction that only ever confirms is not worth making, and this one predicted
opposite answers for the two operations and got both.

**Cost consequence, measured after the fix.** The tier 3 rows found this by
showing substring at 0 bytes on our arm against bare metal's `8 + align8(len)`
-- 448 against 0 for a 28-piece scan. That saving WAS the defect. Re-measured
through a `zigemit` carrying the fix, the same rows read 4, 8, 20, 0 and 112:
we allocate a bare byte run where bare metal allocates a length word plus
8-aligned bytes, so the gap is now a flat **12 bytes a piece**, which is the
ordinary header-and-padding rule every other text row in the table pays. That
is the healthier failure -- an explainable representation gap rather than a
semantic divergence wearing the costume of a saving.

**What it says about the `Text` narrowing.** The cold agent's design review
gave two arguments for the packed-offset representation (b) over a
pointer-at-a-length-word (a): that (a) is incompatible with `cx_concat`'s
general in-place path, and that (a) cannot express a slice of somebody else's
bytes. **The second argument dissolves here** -- after this fix nothing in the
prelude expresses such a slice, because bare metal does not either. (b) still
wins, on the concat argument alone, and that argument is untouched.

## 30. The shifts refused counts the hardware simply masks, so we killed programs upstream runs

**Found 2026-08-21 by `findings/probe-shift-count.codex`, both arms, same
program. Ours. FIXED same day. The first divergence where WE are the stricter
arm.**

    probe-shift-count            zig arm    bare metal
    shl 1 by 64                  <died>     1
    shl 1 by 65                  <died>     2
    shr 256 by 68                <died>     16
    shl 1 by -1                  <died>     -9223372036854775808
    shl 1 by -64                 <died>     1
    reached the end              no         yes

Bare metal emits no guard. `emit-bit-shift` (`Emit/X86_64Builtins.codex:1180`)
moves the count into RCX and emits `shl`/`sar`/`shr` in their CL form, and
`shl r/m64, cl` uses **CL mod 64**. So `bit-shl a 64` answers `a`, `bit-shl a
65` shifts by one, and a negative count shifts by its low six bits -- `-1`
becomes 63, `-64` becomes 0. Nothing traps and nothing says anything.

`cx_shl` was `a << @as(u6, @intCast(b))`. `@intCast` of 64 to a u6 does not
fit, and neither does a negative, so both panic. **The plug was stricter than
the language it implements**, which is a divergence in the direction nothing
else on this list points: every other finding here is the plug being laxer
than the oracle. This one kills a program upstream runs to completion.

**FIXED.** One `cx_shift_count(b) = @truncate(@as(u64, @bitCast(b)))` shared by
all three shifts, which is exactly the low six bits, negatives included.
Verified against the banked bare-metal column: all twelve rows match,
in-range and out.

**Why no sweep could see it, and why that generalises.** A rung compares two
outputs; if neither arm ever shifts out of range the rung is green and stays
green, and if one ever does the plug's arm dies with a panic that reads like a
plug bug rather than a semantic difference. The question that found it is the
same one that found 28 and 29 -- *does this helper fail on the same inputs?* --
and it is worth asking of the whole `cx_*` surface rather than one helper at a
time. Two answers from that sweep are already recorded as clean and should not
be re-derived: `cx_mod` is faithful (bare metal takes `idiv`'s remainder then
adds `abs(b)` if it came out negative, the same Euclidean answer), and division
by zero traps on both arms.

**Standing caveat this one exposes.** `cx_list_at` and `cx_char_at` are
bounds-checked only by zig's own Debug-mode checks, where bare metal emits
UD2s into the instruction stream. That is fine today because everything here
builds Debug, and it is written down in README's "The zig build mode is part
of the experiment" -- but it is the same class of difference and it is not
fixed, only documented.

## 31. `address-of` answered 0 for everything, so every object was the same object and also null

**Found 2026-08-21 by `findings/prim-identity.codex` (tier 9), which exists
because a frequency pass ranked `address-of` at 65 uncovered call sites. Ours.
FIXED same day.**

    prim-identity                          zig arm   bare metal
    same object, twice asked               yes       yes
    alias has the same address             yes       yes
    record-set returned the SAME object    yes       yes
    equal contents, two objects            **NO**    yes
    `&` produced a new object              **NO**    yes

`cx_address_of` was `_ = v; return 0;`. Bare metal's is
`emit-identity-builtin` -- it returns the VALUE, and since records, lists and
texts are pointers there, the value IS the address.

**The two failing rows are the controls, and without them this file would have
passed.** Every "yes" above is `0 == 0`, true for the same reason a broken
implementation would make it true. The rows that ask for two things to DIFFER
are the only ones a constant cannot satisfy. This is the "keep a control" rule
from the unit-test item (PRIORITIES 5, then numbered 1.5) earning its place in the sharpest possible way: a test
suite made only of agreement assertions certifies a stub.

**What it actually breaks, from the compiler's own source.** Not hypothetical:

- `mode-ordinal (m) = if address-of m == 0 then 0 else when m is OvError -> 1 ...`
  On this arm `address-of m` is always 0, so the function **always returns 0**
  and never reaches the `when`. `real-width-ordinal` has the same shape.
- `copy-sx-text (b) (t) = if address-of t < b then t else substring t 0 (text-length t)`
  A durability check. `0 < b` is true for any positive bound, so it **always
  shares and never rematerialises** -- and the comment directly above it says
  why that matters: "substring copies bytes, so the rebuilt text does not point
  into the reclaimed region." Sharing instead leaves the text pointing into
  scratch that is about to be reclaimed. Finding 29's failure mode, arriving by
  an entirely different route.
- Memo keys: `cons-mix (cons-mix (cons-mix 12 (address-of ...)) (address-of ...))`
  builds type-memo keys out of addresses. Every address component is 0, so keys
  collapse to their constructor tag. Whether that produces a wrong answer
  depends on whether lookup verifies structurally after hashing, which is NOT
  established here -- recorded as a question, not a claim.

**The 0 was justified, and the justification does not apply.** The plug's own
comment read: "address-of answers 0 here by X86_64Compound's own account of
targets without it". That account says address-of "silently answers 0 on any
target where `address-of` cannot be modelled: **that cost the C# arm every tag
in this table**" -- describing the hazard as a cost that had already bitten,
and upstream's response was to stop depending on it there (they read tags via
`variant-tag` now), not to bless the 0. And this is not such a target: one flat
region with pointers into it is exactly the shape bare metal has.

**FIXED.** `cx_address_of` now returns the value for scalars and a
**heap-relative offset** for pointers. Heap-relative is the load-bearing part:
the answers are compared against `__heap-save` values, which are offsets from
`cx_heap_base`, so a raw `@intFromPtr` would order correctly among itself and
be nonsense against those. Slices take `v.ptr`; anything else refuses by name
rather than returning a number.

**Why no sweep saw it: THE LADDER STRUCTURALLY CANNOT.** Asked as an open
question and answered the same day by an independent read, which also corrected
the count -- 65 occurrences but **62 real call expressions**, since one is the
`BuiltinSpec` table entry and two are prose inside comments.

**59 of the 62 are not in the emitted program at all.** IR emission prunes to
what the `opening` reaches, and every one of those 59 belongs to one of two
families -- the `copy-sx-*` tree in `Syntax/SyntaxNodes.codex` and the
`mcopy-*`/`mkey-*`/`*-ordinal` tree in `Types/Unifier.codex`. Each is rooted in
exactly one caller, and both callers are in `codex/compiler/opening.codex`
(`:492` and `:675`). **That is the one chapter a rung can never bundle**, because
a rung replaces it with a harness and two chapters cannot both define `opening`.
Confirmed in the emitted zig rather than inferred: ten of the fourteen rungs
contain `cx_address_of` exactly once -- the prelude definition, zero calls --
and `fn mcopy_type`, `fn mode_ordinal`, `fn copy_sx_text` appear in none of
them, while a control (`fn deep_resolve`) appears in all.

**The other 3 sit in error branches a clean compile never takes** -- the
`is otherwise ->` arms of `emit-record` and `emit-field-access`, which fire only
when `resolve-constructed-ty` fails. `passes_to_x86_on_mid.truth` and `ir_to_x86_on_fib.truth` both record
`emit-errors 0`. Had they fired they WOULD have diverged and gone red, so this
is "green because the branch is dead", not "green because the divergence is
invisible".

So the answer is the first of the two branches, and the blindness is structural
rather than accidental: **the one chapter the ladder is architecturally required
to exclude is the only chapter that reaches this builtin.** No choice of subject,
no deck scale and no extra rung on the existing pattern would change it. Only a
harness that calls `copy-sx-document-guarded` and `mcopy-types` directly would --
or a unit test with a control row, which is what actually found it.

**Residual, and it is a live trap.** The fix makes `address-of` heap-relative,
which is coherent with `__heap-save`. But the three surviving sites do
`show (address-of rec-ty)` and `peek-qword (address-of rec-ty) 0` -- a
heap-relative offset where bare metal shows an ABSOLUTE address, and a
`cx_peek_qword` read of a zig struct's raw bytes where bare metal reads a tag
word. If either error branch ever fires, that rung goes red on those lines, and
**the first reading will look like an emitter bug rather than a representation
difference.** Arguably the divergence one wants to see; recorded here so whoever
meets it does not spend the afternoon it would otherwise cost.

## 33. No tail calls: recursion depth on this arm is bounded by the thread stack, bare metal's is not

**Found 2026-08-22 on the native chain (finding 24's closing experiment).
Ours. FIXED 2026-08-24 on `zig-plug-tail-calls` -- `6cd40143` the
transformation, `07495229` two zig-shape corrections, `912daac7` the
invariant-parameter rule, `64d7db8e` the act-block arm. **SENT as PR 81
on 2026-08-24**, stacked on PR 77, ladder tag `tail-calls`. The branch
layout was repaired and both branches are pushed and level with origin;
the pre-surgery tips are kept at `refs/backup/pre-surgery-tail-calls`
and `refs/backup/pre-surgery-parser`.**

**ABSORBED 2026-08-25 by Update 50's interim push (`111c0fea`), as
PR 81 verbatim: the released `ZigEmitter.codex` is byte-identical to the
clean merge of PRs 81 and 83 on PR 77. Closed.**

**The defect.** Bare metal has tracked tail position since Update 30
(`st-set-tail-pos`) and a self tail call there is a jump; the plug turned
every one into a call. Every `*-loop (xs) (i) (acc)` in the compiler has
that shape, so depth on this arm grew one frame per element where bare
metal's is flat. `native/zigemit` on the 13.2 MB `ir_to_x86.ir` died in
`tokenize_collect`, one frame per token over 3,282,147 tokens: 512 MB
died, 2 GiB died, 3.5 GiB reached only the end of tokenizing. The same
Update 30 commit gave the python plug its TCO; the zig plug was missed.

**The fix.** A definition whose tail positions call itself at full arity
emits as `while (true)` with its parameters as loop variables. The spine
walks if, let and unguarded match; any other tail position emits
`return <expr>;` unchanged, so an unhandled shape loses the loop and
never the meaning.

**The measurement that closes it** (sandbox
`20260824T115824Z-f33-tailcalls`, natives from the branch, 4 GiB region
from PR 77 beneath it): `zigemit` on that same IR completes rc 0 in 27 s
**at the stock 512 MB stack**, emitting 3,021,734 bytes of zig.
`tokenize_collect` is among the 887 definitions of 3,633 that emit as
loops at `6cd40143`.

That the program is also RIGHT is the half a stack fix could have faked:
the zig compiles (2.5 s), runs in 0.37 s, and both its rungs are
**byte-identical to `truth/u49`** -- a full ir_to_x86 unit through the
native loop with no QEMU in the arm. `findings/probe-tail-loop.codex`
covers the spine shapes, `findings/prim-tailcall.codex` (tier 13) the
semantics.

**Two sub-findings the fix produced, both worth keeping:**

- **The next arguments must go through temporaries.** They read the
  parameters the loop is about to overwrite, so assigning left to right
  builds the second argument from the first one's new value. It does not
  crash -- it returns a plausible number. Tier 13's `arg-swap` row is
  the guard.
- **Declining every function-typed parameter was too broad, and cost
  10,000 frames.** Zig will not hold a bare function type in a var, so
  the first cut refused any definition having one. `sort-partition` --
  the compiler's own partition loop, self tail-recursive in both
  branches -- has a comparator among its six parameters and was left
  recursing 10,000 deep, which `stack_probe.py` surfaced only because it
  censuses frames rather than reporting pass/fail. A parameter every
  self call passes back unchanged never varies, so it stays the
  function's own (const) parameter: `cmp`, `hi` and `pv` need no
  variable and only `xs`, `j`, `i` move. A function-typed parameter is
  then a problem only when it actually changes. VERIFIED: `sort_partition` is
  gone from the trace and the stack requirement fell from 32 MB to 4 MB
  (finding 37's table). Stating the discard rule took three attempts --
  zig rejects an unused parameter AND a pointless discard of a used one,
  and the loop deletes exactly one class of occurrence: the parameter
  standing as its own argument in a tail self call.

**What this does NOT close.** The 512 MB stack in every emitted `main`
stays, and finding 37 is why: other recursions hold it up, none of them
the one `zig-main`'s prose blames. That prose says the case reaching the
limit is the lexer's `scan-token -> skip-prose-line` cycle; measured,
that cycle is flat (100,000 consecutive prose lines run in 256 KB). Read
finding 37 for what actually drives the number, and do not repeat the
lexer claim -- it was the reason nobody looked for a year.

## 35. A non-ASCII identifier is emitted raw, and zig's identifiers are ASCII

**Found 2026-08-22 by the u49 census (the first on natives from the heap
branch rebased onto the pin). Ours. CLOSED 2026-08-23 by `1249ad8a`
(`zig-ascii-ident`, transliteration to `_<code>` in both sanitizers):
ident-letters refused -> match on droplet-built natives, tiers 13/6 green,
rebank+sweep 14/14 in sandbox `20260823T021627Z-u49-f35`.**

`codex/test/ident-letters` is new at Update 49 and names a definition
`café` -- one of the thirty-one Tier-0 letters at CCE 97..127 that the
lexer now accepts as identifier characters. `zig-sanitize` maps `-` and
`/`, renames prelude collisions and quotes keywords, and passes every
other byte through; the emitted `fn café() i64` is two raw UTF-8 bytes
in a zig identifier, and zig 0.16 refuses it at the parser
(`ident-letters.zig:769:7: expected '(', found invalid bytes`). Verdict
moved `markers -> refused` between the 08-20 bank and this census: the
old natives stopped at is-letter's band before reaching the name, so
the gap only became visible once finding 19 closed.

Fix is confined to the sanitizer: any byte outside `[A-Za-z0-9_]`
either quotes the whole name (`@"café"`, legal in zig for any
non-empty string) or transliterates it to an escape (`caf_u00e9`);
quoting is simpler and `zig-sanitize` already quotes keywords. The
prefixed names through `zig-raw-ident` need the same rule. One program
hits this today; the census column is `refused`, not a wrong answer.
## 37. The 512 MB stack is protecting the parser's header scan, not the lexer's prose cycle -- and that scan is mutual TAIL recursion

**Found 2026-08-24 by measuring what the workaround actually holds up,
after finding 33 removed the self-recursion it was blamed on. Ours to
report; the cycle is THEIRS. OPEN. SENT as PR 82 (COMPILER-19) --
the `Syntax/Parser.codex` restructure plus its row, off `upstream/master`
5b8091e2, ladder tag `parser-self-tail`. The commit carries the parser
change ALONE, with none of our emitter work under it: `Parser.codex` at
5b8091e2 is byte-identical to the base the change was measured against,
and the file the commit produces is byte-identical to the verified
one.**

**ABSORBED 2026-08-25 by Update 50's interim push (`111c0fea`), as
PR 82 plus its COMPILER-19 row. One duplicated prose block was trimmed
during absorption (Damian, stated in the closeout): the parse-side twin
of the scan-side rationale, which carried the 3,385-frame parse-top-level
measurement. The mechanism paragraph and the state-re-read constraint both
survive in the tree; that one frame count does not. Closed.**

`zig-main` emits every program onto a 512 MB thread and its prose names
the reason:

    the case that reaches the limit is MUTUAL recursion, the lexer's
    scan-token -> skip-prose-line -> scan-token cycle, and no amount of
    self-tail-call elimination flattens that

**The named cycle does not reach any limit.** `scan-to-eol-end` stops AT
the newline without consuming it, so the third call in the cycle sees a
newline, returns a `Newline` token, and unwinds: three frames per prose
line, constant, never chaining to the next line. Measured on native
`codexir` built from the finding-33 branch, one constant changed in the
emitted source (the JUSTIFICATIONS slack methodology):

    prose lines   stack    verdict
        100       256 KB   rc 0
    100,000       256 KB   rc 0        <- identical; no accumulation
    100,000        64 KB   abort
        100        64 KB   abort       <- control: 64 KB is too small for anything

**What does reach the limit** is in the parser, and the same binaries
name it. On the real 2,503,544-byte compiler subject (4,511 top-level
definitions), the 8 MB run's backtrace is 7,096 frames of:

    2,393 x scan_top_level
    2,393 x try_scan_type_def
    2,287 x try_scan_def_header

`Parser.codex` "Header Scanning (streaming)": `scan-top-level` ends
`else try-scan-type-def ... st`; `try-scan-type-def` ends
`scan-top-level ...` on Just and `try-scan-def-header ...` on None;
`try-scan-def-header` ends `scan-top-level ...` on Just. One full turn of
the three-cycle per top-level definition, and **every edge is a tail
call** -- no frame in the cycle is live when the next is entered.

The cliff on that subject, from `stack_probe.py` (banked
`findings/gold/u49/stack.txt`):

    stack    verdict
    24 MB    abort
    32 MB    rc 0

**There are at least TWO such cycles, not one, and the probe found the
second on its first run.** The 8 MB trace above is the streaming header
scan. The trace at the 24 MB cliff names different functions:

    try_top_level_type_def x3386
    parse_top_level        x3385
    try_top_level_def      x3185

-- `parse-top-level` / `try-top-level-type-def` / `try-top-level-def`,
the real parse, with the same three-function mutual-tail shape and the
same one-turn-per-definition cost. So the scan cycle is what dies first
at 8 MB, and once there is room for it the parse cycle dies at 24 MB.
Flattening either alone moves the number by one cycle's worth and leaves
the other; a fix that claims to retire the 512 MB has to do both, and
the probe's `cycle` column is what says whether it did.

So the workaround is load-bearing -- about 28 MB for the largest real
document, roughly 7 KB per definition -- and 512 MB is about 18x that,
which is the headroom nobody had measured. It also bounds the compiler:
a document of ~75,000 definitions overflows even 512 MB, and the failure
is a segfault rather than a diagnostic.

**The fix is a source change with no new emitter machinery anywhere in
the fleet.** Nobody flattens mutual tail calls: bare metal's TCO is
self-only (`X86_64.codex:75`, `is-self-call (expr) (func-name)`), and so
is the python plug's and so is the zig plug's new one. But this cycle
does not need mutual TCO -- it needs to stop being mutual. The two
`try-*` functions are continuations that always return to
`scan-top-level`; have them RETURN their decision instead of calling
back:

    try-scan-type-def   : ... -> ScanStep   (found td + state | not a type def)
    try-scan-def-header : ... -> ScanStep   (found hdr + state | not a header)

and `scan-top-level` dispatches on that and tail-calls ITSELF. A self
tail call is what every TCO in the fleet already flattens, so the scan
becomes O(1) stack on bare metal, on zig, on python and on C# at once,
and the 512 MB spawn stops being load-bearing for the case that actually
drives it.

Not yet done: the same measurement on `zigemit` and on the other
natives, and a check of whether a THIRD cycle appears once these two are
flat. The 512 MB should not be lowered until that sweep exists -- this
entry establishes what one input needs, not what every input needs.

**MEASURED 2026-08-24, and the fix works: 32 MB -> 4 MB.** Both cycles
restructured so the `try-*` functions return their item and the loop
tail-calls itself (`parser-scan-self-recursive`, `50a81942`, was
`33f72baa` before the branch layout surgery), in sandbox
`20260824T132742Z-f37-parser`:

    emitter     min    cliff  cycle on the failing trace
    6f18a4b9    32 MB  24 MB  try_top_level_type_def x3386, parse_top_level x3385
    43ea7875    32 MB  24 MB  sort_partition x10000
    bb2e6b38     4 MB   2 MB  desugar_expr_at x297

Read the middle row before the last. The parser cycles were gone at
`43ea7875` and the number had not moved, because a THIRD recursion sat
underneath: `sort-partition`, left recursing by our own emitter
declining any definition with a function-typed parameter (finding 33's
second sub-finding). Only with that fixed does the parser change show
its own effect, and a pass/fail arm would have reported the parser
change as worthless.

**What is left is a different class.** `desugar_expr_at` recurses over
the SHAPE of one expression, so its depth is the nesting depth of the
deepest expression in the document -- 297 frames -- not the number of
definitions. The per-definition growth that made document size the
stack's driver is gone.

**Correctness, which a stack number cannot speak to:** the restructured
parser compiled the 2.5 MB back-end unit to a 13,206,964-byte IR,
through zigemit and `zig build-exe` to a running binary, and both its
rungs are byte-identical to `truth/u49`. Parse, check, lower and emit
agree with the bank end to end.

**What remains is bounded, and that is the answer to "can the 512 MB
come down".** `desugar-expr-at` carries explicit fuel:

    desugar-expr-at (node) (depth) =
     if depth >= max-recursion-depth then AErrorExpr "desugar fuel exhausted"

`max-recursion-depth` is 1024 (`Core/BuildSettings.codex:201`) and ten
chapters walk their trees under it -- desugarer, name resolver, type
inference, unifier, lowering, occurrence, IRCheck, LIR, CodexEmitter.
So the 297 frames measured are not luck: this whole class is capped at
1024 frames by the compiler's own constant, whatever the input. The
stack requirement is now a function of a source constant rather than of
document size, which it was not before the parser change.

**One residual is NOT fuel-bounded, and it is quicksort.** `qsort-by`
recurses on the left partition with the result in hand -- not a tail
call, so nothing flattens it -- and its depth is O(log n) on balanced
data and O(n) on adversarial. `sort-med3` makes the degenerate case
unlikely rather than impossible. Worth knowing that the tail-call change
already halved its class for free: the SECOND recursion
(`qsort-by xs3 cmp (pr.pivot + 1) hi`) is a self tail call at full
arity sitting in a let chain, so it now loops, which is the textbook
recurse-on-one-side-iterate-on-the-other shape obtained without asking.

**Confidence: HIGH on the measurements and on the restructure; MEDIUM on
what remains.** The cycles are named by the programs' own backtraces,
not inferred, and the restructure is verified against the bank. NOT
established: that 4 MB is the floor for every input (two documents
measured, and only through `codexir` -- `zigemit` and the other natives
have their own recursion), and where quicksort's unbounded left-hand
recursion actually lands on real data. The 512 MB stack should not be
lowered on this evidence alone, but the shape of the argument for
lowering it now exists: one capped class at 1024 frames, one data
dependent class in the sort, and no per-definition growth.


## 40. The zig plug calls a curried definition flat, so an under-applied chain it cannot inline will not compile

**Found 2026-08-24 on tier 14's first run against both arms. OURS -- the
zig plug (ZigEmitter), not upstream. FIXED 2026-08-24 on
`zig-plug-curried-apply` (`835639b7`, off PR 77's `8cb8a0e4`), both sites
in one commit. **SENT as PR 83**, stacked on PR 77 and a sibling of
PR 81 rather than stacked on it; ladder tag `curried-apply-fix`.**

**ABSORBED 2026-08-25 by Update 50's interim push (`111c0fea`), as
PR 83 verbatim. Closed.**

VERIFIED end to end in sandbox `20260824T220516Z-f40-fix2` (natives from
`835639b7`): the plug emits
`b5: { const _o5 = even_fn(4); break :b5 _o5.call(_o5.ctx, 20, 22); }`,
tier 14 compiles and prints 47/47/47, the tier SET is GREEN at 22 tiers
with `prim-closure` back in it (0 unexpected, 1 expected, 0
expected-but-agreeing), the **SWEEP is 14/14 GREEN** (657 s), the
diagnostics census is unmoved at CDX6020 x43, and the bank taken from
that sandbox is a **ZERO-BYTE diff against the committed `truth/u49`**
-- so the emitter change did not reach bare metal, which is what a
plug-only change must be able to say.

`((even-fn 4) 20) 22`, where `even-fn : Integer -> (Integer, Integer ->
Integer)`, is emitted as a saturated three-argument call to a definition
the plug itself emitted as one-ary returning a closure:

    fn even_fn(n: i64) CxFn2(i64, i64, i64) { ... }
    even_fn(4, 20, 22)
    error: expected 1 argument(s), found 3

**The discriminator is inlinability.** `even-fn` is MUTUALLY recursive,
so nothing can inline it, the flat call survives to the emitter, and zig
rejects it. The emitted `opening` does contain a correct closure call --
`_f5.call(_f5.ctx, 20, 22)` -- so the plug knows how to call a closure;
it just does not know it is holding one when the definition stayed a
definition.

**The two "controls" this finding first claimed are weaker than it said,
corrected 2026-08-24.** `grep '^fn ' prim-closure.zig` returns only
`add3`, `even_fn`, `odd_fn` and `opening`: **`pick` is not emitted as a
function at all**, so "pick compiles" was never a statement about
emitting a closure-returning DEFINITION -- the inliner erased it and the
surviving `_f5.call` is the inlined body's call site, reached through
`emit-zig-apply`'s `is otherwise ->` branch because its root is an
`IrIf`, not an `IrName`. Worse for the other one: `probe-closure-solo`'s
whole `opening` body folds to `((5 +% 20) +% 22)` and `make_adder` is not
emitted either, so it exercises constant folding and nothing about
closures. It is not a control. Checked on BOTH trees, because this
finding has been measured on the wrong one before: identical in
`20260824T184156Z-tier14b` (the bare u49 pin) and in
`20260824T185614Z-tier14-pr77` (`8cb8a0e4`, which is the tree the tier
set's zig arm belongs to). The `CDX4030` pipeline line is also a
global default printed for essentially every unit, not a per-file
observation about `prim-closure`. The conclusion survives all three
corrections -- the emitted artifact shows it directly -- but the
evidence it was resting on did not.

**This is finding 39's shape on our side of the fence.** There the call
site assumed an arity the closure could not honour at run time; here the
call site assumes an arity the definition was not emitted with, and zig
catches it at compile time. Upstream corrupts silently, we refuse
loudly, and the disagreement is the same disagreement.

**It fails as a raw zig error, not a `@compileError("zig plug: ...")`
marker**, so `zig-is-unmapped` and `corpus_run.py --transpile` score it
zero. PRIORITIES item 5's open question names three findings in that
class; this is the fourth.

**Reproducers:** `findings/prim-closure.codex` (tier 14, which is
EXCLUDED from the set while this stands), `probe-closure-silent`,
`probe-closure-rec-cmp`. Control: `probe-closure-solo`.

**Confidence: HIGH, and the tree is named because it has to be.** First
measured against natives built from the bare u49 pin `bdf0049b`, which
was the WRONG tree: the tier set's zig expectations come from PR 77's
tip `8cb8a0e4`, and `ast/zigemit-source.codex` -- the committed
provenance snapshot -- says so, since a build on the pin rewrites its
`cx_heap_mem`/`cx_heap_reserve`/`cx_heap_vtable` to `cx_arena_state`
while a build on `8cb8a0e4` leaves it byte-identical. Re-measured there:
the same error at the same declaration, only the line number moved
(534 to 800, PR 77's prelude being longer), with `probe-closure-solo`
still answering `solo 47`. So the defect is present on BOTH trees and is
not an artifact of either. The error is a compile-time refusal with the
emitted text in hand, and the inlined control passes in the same
chapter.

The seed is byte-identical across the two trees
(`a01c1547e92eb0d0`), so tier 14's banked bare column never depended on
which was chosen.

**SETTLED 2026-08-24: the call site is the wrong half, and this is a
documented rule the plug does not follow.** `docs/DevelopersRulebook.md`
lines 256-260 state it, in the section headed "What the wire carries,
for anyone writing a plug" (`:243`). The rule is UNQUALIFIED -- it binds
"a plug", with no list narrowing it, so it reaches every plug that keeps
an arity map. (The plug list at `:254` is the neighbouring LAMBDA
bullet's and does not scope this one; the application bullet names the
TS/JS family only as plugs that already carry the model.)

> Application is curried on the wire ... a plug must emit `f(a)(b)`,
> never `f(a, b)`, unless it KNOWS the callee's arity: a def it emitted
> n-ary is called flat at that arity, under-applied with one arrow per
> missing parameter, **over-applied by applying the rest one at a
> time.**

Three cases; the plug implements two. `emit-zig-apply`
(`ZigEmitter.codex:2067-2071`) looks the arity up, branches correctly on
`args < ar`, and then lets `args > ar` fall into the saturated-call
branch, which emits every argument in the chain -- the loop bound in
`emit-zig-call-args` is `list-length args`, never `ar`. `ar` is computed
and discarded. The over-supplied arguments are not even type-checked:
`zig-callee-param-type` returns `VoidTy` past the parameter list
(`:656`).

The definition-flattening alternative is contradicted, not merely
unchosen. The compiler's own x86-64 backend builds its arity map from
`list-length (d.params)` (`X86_64Compound.codex:38`) exactly as
ZigEmitter does at `:537`, and splits on `args > user-arity` into
`emit-over-apply` (`:154`, implemented `:245-274`). A Codex `FunTy` is a
curried arrow, so `Integer -> (Integer, Integer -> Integer)` and
`Integer, Integer, Integer -> Integer` are the SAME type and
`list-length (d.params)` is the only signal separating them -- flattening
the definition discards it, and would need an eta-expansion `emit-zig-def`
does not have (`:2625` emits the body verbatim).

**The second site is OBSERVED now, not predicted (2026-08-24).**
`findings/probe-closure-value.codex` passes `even-fn` to a helper as a
bare VALUE. The helper has to survive the inliner for the shape to
appear at all -- with one call site it is inlined and the defect shows
up as the ordinary flat call instead -- so the probe calls it twice.
`emit-zig-name` then eta-wraps the definition using the TYPE-spine count:

    fn call(_ctx5: *anyopaque, p0: i64, p1: i64, p2: i64) i64 {
        _ = _ctx5; return even_fn(p0, p1, p2); }
    ... packaged as CxFn3(i64, i64, i64, i64)

The wrapper's own signature is self-consistent, so `zigemit` returns rc 0
and the defect survives to the zig compiler, which refuses it at BOTH
call sites: `p2.zig:804:190: error: expected 1 argument(s), found 3`,
`note: function declared here` at `even_fn`. So the two sites fail the
same way for the same reason and neither is reachable from the other's
reproducer.

**One caution for the fix: the rulebook's "one at a time" is wrong for
zig specifically.** `zig-closure-invoke` (`:2284-2286`) applies all
remaining arguments at once, which is what the working `_f5.call(_f5.ctx,
20, 22)` does. The right shape is to chunk by each closure's arity.
`emit-ts-apply-split` (`TypeScriptEmitter.codex:208-214`) is the
structural template; `zig-closure-invoke` is the correct tail. And
rerouting `args > ar` into `emit-zig-expr-curried` (`:2461-2468`) does
NOT fix it: that path reaches `emit-zig-name:1053-1057`, which eta-wraps
using `zig-fn-param-count` -- the TYPE-spine arrow count, 3 for
`even-fn`, not the emitted 1 -- and lands back on a flat
`even_fn(p0, p1, p2)`. **The emitter carries two disagreeing notions of a
definition's arity** and knows it: `zig-untrusted-return-note`
(`:2513-2518`) prints `"type-val has N arrows for M params"`, and
`zig-def-return-trusted` (`:2520-2522`) tests `>=` rather than `==`,
tolerating the very mismatch that breaks the call path. Both sites move
together or neither does.

**Why nothing caught it:** `codex/plugs/test-input/partial.codex`
exercises under-application, saturation, and over-application of a
LOCAL, but never over-application of a named top-level definition --
the only shape that reaches `ZigEmitter.codex:2070`. And
`codex/plugs/test-plugs.ps1` judges exit code, non-empty output and text
markers (`:93-97`, `:163-177`); it never compiles the emitted target.

Tier 13's prose says the zig arm "would not compile the closure return
type" -- that is out of date; the return type emits fine.

