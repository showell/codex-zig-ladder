# codex-zig-ladder -- a Diverse Double-Compiling check on the Codex compiler

**Codex** is a programming language whose compiler is written in itself and
emits bare-metal kernel images, so compiling anything with it means booting a
machine. It is developed at
[damiant3/Cobblestone](https://github.com/damiant3/Cobblestone) -- the language
is Codex, the project is Cobblestone.

**The zig plug** is a transpiler living in that project. It turns Codex IR into
zig source, so the Codex compiler can also be built as an ordinary Linux
executable instead of a kernel.

**This repository asks whether the plug is honest.** It compiles the same
compiler source two ways -- once by the trusted Codex seed on bare metal under
QEMU, once through the plug and the zig toolchain -- and requires the two
results to agree byte for byte. That is a Diverse Double-Compiling check in
Wheeler's sense, built in fourteen steps called **rungs**, each putting more of
the compiler under test than the last.

**The goal is finding defects**, in the plug and in Codex itself.
[`findings/README.md`](findings/README.md) is the register of what it has
caught.

This repository lives *outside* the Codex checkout it audits and modifies
nothing in it; point it at one with `CODEX_ROOT` ("Running it", below). It is
built for one dedicated host and refuses to compute anywhere else ("The
venue").

If you are new here: "What this is" has the vocabulary, "What the check proves,
and what it does not" has the honest limits, and "Processing a new Update" is
the operating procedure.

## What this is banked against

| | |
|---|---|
| Seed | `B066CEB5` (3,064,878 bytes) |
| Update | 53 (`58b08c38`; pin branch `u53-rebank`, length ZERO -- no cherry-picks, because the outbound queue emptied into this release. See "The checkout") |
| Rungs | **14 of 14 green** |
| Banked | `truth/u53/`; every bank is kept. u45-u48 were pruned by a `--keep 3` that is retired, and live in git history |

This table is the point of the whole arrangement, so it is the first thing on
the page and it is allowed to be unflattering. A ladder that cannot say which
seed it agrees with is not evidence about anything.

**Update 53 is the release that unblocked the zig arm.** Update 52 could not be
transpiled to zig at all -- its arms came back 6 of 14 and `native_build.sh`
exited 1 -- so it was never banked, and this table said Update 51 for a week.
Update 53 sweeps 14 of 14 with zero diffs.

**Update 52 was never banked and the rule that skipped it is retired.** Its
truths were measured and sound, but the green-arms rule of the day said not to
bank over red arms -- and a truth is a bare-metal measurement the plug's arms
cannot reach, so a red arm was never a reason to withhold a good measurement.
Every Update is banked now, and what the arms said rides in `ARMS` beside
`SEED`. What stays gated on green arms is this table and the `uNN-14of14` tag:
the claim, not the measurement. The cost is visible above -- this bank diffs
against u51, across two seeds.

**Three truths moved from u51 and eleven did not**: `ir_to_x86_on_fib`,
`ir_to_x86_on_cce` and `passes_to_x86_on_mid`, but NOT `lir_to_x86` or
`passes_to_x86_on_arith` -- a subset of the x86 family rather than all of it.
The five-second seed canary predicted that shape before the rebank started:
diagnostics byte-identical between the two seeds, the emitted image 1,552 bytes
larger and diverging from byte 9. Front end holds, image moves.

**The table is maintained by hand; prefer `ladder_status.py`.** What cannot
drift is the BANK's label, which `seed_identity.py` derives from the seed's own
hash by finding the release note that names it.

Mid-rebank, the checkout's pin branch runs one Update ahead of this table --
`seed_identity.py` names the new Update while `truth/` still holds only the
old banks. That is the normal in-between state, not drift: the table moves
only when `bank_truth.py` lands the complete new set.

A bank is named for a SEED, not for a commit, and Update 51 is the case that
shows why that is the right key. Three public commits share seed `C3181693`
-- the release `7a6c5682`, the same-night addendum `a0425e10`, and the
emitter repair `012a9d2e` -- so all three bank as `u51` and this one table
answers for all three. `seed_identity.py` derives the name by finding the
release note that names the seed's hash; when no note names it, it refuses
`uNN` and labels the bank `seed-XXXXXXXX` instead, which is what Update 50's
interim push got. The refusal is the design.

**A rebank whose truths come back byte-identical is not a wasted rebank.**
This one was run because the u51 bank had been taken from a run killed at
3/14, and all fourteen truths reproduced exactly, sidecars included -- so the
banked answer was right and is now known to be right rather than assumed.
The rest of what a rebank buys is unaffected by the truths not moving: the
diagnostics census only exists in a tree that measured bare metal AND swept,
and the timings below are only honest if they were measured under this seed.

## What this is

This repository holds a Diverse Double-Compiling check, in Wheeler's sense:
take one piece of source, compile it two ways through toolchains of unrelated
lineage, and require the two results to agree byte for byte. If they disagree,
one of the two toolchains is wrong. The check here is built in fourteen steps,
called rungs, each putting more of the compiler under test than the last.

Four things to know before anything else.

**Codex** is the language this repository implements. Its compiler is written
in Codex and emits bare-metal images, so compiling anything means booting a
machine: `ring_compile.py` runs the compiler as a QEMU kernel and feeds it
source over a serial line.

**The seed** (`seed/Codex.cdx`) is the trusted compiler binary at the root of
that. It is the authority every measurement here is compared against, and it is
also what produces the IR the plug consumes -- which is why a new seed
invalidates everything banked. Seeds change with each **Update**, an upstream
release of Cobblestone (`damiant3/Cobblestone`, the project Codex is the
language of); the release commit names its seed.

**The plug** (`codex/plugs/zig/ZigEmitter.codex`) transpiles Codex IR into zig
source: `prog.ir -> prog.zig`, which `zig build-exe` then makes native. Point it
at the compiler's own IR and you get the Codex compiler as an ordinary Linux
process instead of a kernel.

**A unit** is one compile. It bundles part of the compiler into a single
compilable **subject**, and that subject is compiled twice. The first compile
is the real one: the seed, on bare metal, under QEMU. The second goes through
the plug: the same subject, transpiled to zig, built by `zig build-exe`, run
as a Linux process.

**A rung** is one claim, and it is what the two runs are compared over. Both
print the same thing, and the two outputs must be **byte-identical**. A rung
that passes says the transpiled compiler and the real compiler agree about
that much of the compiler. Usually a unit carries one rung and the two words
name the same thing; two units carry two rungs each, because one compiled
compiler can be handed more than one program to compile, and each answer is
its own claim. Fourteen rungs, twelve units -- "The twelve units" below is
organised by the compile, and names the rungs riding in each.

The ladder exists to test whether the transpile is faithful. The answer has to
be byte-exactness rather than "it seems to work", because a transpiled compiler
that is subtly wrong produces subtly wrong binaries forever after.

## The parts

**A chapter** is Codex's module: one `.codex` file, naming what it `cites` from
other chapters. The compiler is about sixty of them, and a unit's subject is
some subset concatenated into one compilable whole.

**The seed is not only a compiler.** It is an operating system with the compiler
inside it: it has a network stack, a FAT16 driver, a framebuffer and a process
model, all written in Codex. That is why a transport can be an oracle surface,
why `read-file-uni` means a disk, and why the compiler's `opening` has an effect
row mentioning block devices.

**CCE** is Codex's own character encoding, one byte per common character, and it
is what `Text` is made of everywhere inside the compiler -- on bare metal, in
the C# plug and in the zig plug alike. A target's own encoding appears at I/O
and nowhere else. **IR-CCE** is the IR text wire format in that encoding, and it
is what a plug is fed.

**A CDX** is what the Codex compiler emits: a bare-metal image in three
pieces -- a 224-byte header, the content, and a tail. The content holds the
code, the rodata, the capability and effect tables, and a debug map of symbol
names and offsets; the header says where each piece is, where to start, and
carries a sha256 of the content. A multiboot header sits immediately after the
224, so a loader will boot it. It is a kernel, not a hosted program -- running
one means booting a machine.

**The driver** is `codex/compiler/opening.codex`: the chapter holding the real
compiler's `opening`, which reads a mode line and a source unit, runs the front
end, the IR pipeline and the back end, and writes the result out. It is what you
are running when you run the Codex compiler.

## Why this exists

Six objectives, ranked by how much of the repo serves each -- roughly, since
the sixth earns its place by yield rather than by volume. A change that serves
none of them probably belongs somewhere else.

1. **Prove the zig transpilation of the Codex compiler faithful, to the
   byte.** The rungs, the two arms, the banks and the provenance guards all
   exist to force byte-identity between seed-compiled and plug-transpiled
   output, up to the whole compiler emitting a complete CDX image.
2. **Find defects -- in the plug and in Codex itself.** The byte-exactness
   pressure is the instrument; `findings/README.md` is the register of what
   it has caught (`findings/CLOSED.md` holds the ones that are done, keeping
   their numbers), and probes-then-filings is the loop.
3. **Build toward a Diverse Double-Compiling witness in Wheeler's sense.**
   "What the check proves" below is scrupulous about how far along that road
   this is; taking the seed out of the loop is the standing endgame.
4. **Measure what each upstream Update actually changes in the emitted
   image.** The bank-to-bank diff is the only artifact that can say; this
   objective fell out of the banking discipline so organically that a cold
   reviewer named it before we did.
5. **Turn the Codex compiler into an ordinary, fast Linux process.** `zigc`
   and the native loop make the compile step seconds instead of a VM boot,
   which changes what is cheap for everything above.
6. **Unit-test the primitives, on both arms, as a standing instrument.** The
   rungs answer "which of fourteen programs disagreed"; the tiers
   (`findings/prim-*.codex`, run by `tier_run.py`) answer "which primitive
   did", in seconds rather than an hour. They are the newest objective and the
   highest-yield one so far -- findings 21 through 30 came almost entirely from
   here, several of them invisible to a sweep by construction, and one of them
   would have caught a defect that cost a day. Coverage is chosen by COUNTING,
   not by taste: a frequency pass over the whole compiler ranks the builtins by
   real call sites, and the gap between that ranking and what the tiers assert
   is the work list. A primitive with hundreds of uses and no assertion is a
   bug waiting for a subject large enough to expose it.

Side products worth knowing about even though no objective claims them: the
QEMU drivers are the only non-Windows implementation of the author's host
contracts, and so their de facto written spec; and the corpus harness
(`corpus_run.py`, which grades the emitter against the depot's hand-oracled
test programs) is plug-agnostic, so a future plug in another language could
be graded against the same banked IR and truths on day one.

## Corpus testing: measuring a change against the depot's own tests

**One command, and its docstring is the method:**

    ./compare_arms.py <base-ref> <head-ref> --plan   # blast radius, 2 seconds
    ./compare_arms.py <base-ref> <head-ref>          # the real thing

It cuts both trees, transpiles the full population on each, byte-diffs the
emitted zig, and builds and runs **only the programs that differ** -- because a
program whose emitted zig is byte-identical across the arms cannot have a
different verdict, so running it is a tautology at full price. Cost scales with
the change's blast radius rather than with the corpus: on 2026-08-30, nine
commits across plug, compiler and foreword moved 48 of 1,233 programs, and the
expensive stage ran 48 instead of 709.

The result is a committed artifact under `results/<id>/`, not a log in a
sandbox: both tree shas, each arm's natives, the population, and every moved
verdict and differing file by name. The sandboxes are retired on success and
kept only on failure.

`compare_arms.py`'s module docstring is the authority and is maintained with the
code; `affected.py` derives which programs can see a change; `corpus_run.py`
does one arm's sweep. **Do not write a new script pair per change** -- there
were three, and all three were buggy in the scaffolding rather than the
measurement.

## Anatomy of a rung

### The subject and its harness

A subject is a set of real compiler chapters, concatenated with stubs and a
harness. What that compiler then compiles when it runs is its PROGRAM, and
the two are different things -- "The twelve units" below names both for
every unit, and says which of them a rung's name refers to. Most programs
are a fifteen-line fib snippet; three units use something else --
`ir_to_codex_roundtrip` takes another unit's output,
`ir_to_x86_on_cce` a single chapter verbatim, `passes_to_x86_on_arith` a
program written to fail. The shape is the same either way: one compilable
subject, compiled twice.

A caution for anyone reading the code beside this: `oracle_lib.sh`,
`emit_harness.py` (`subjects=`) and `split_truth.py` still use "subject"
for the PROGRAM, and the generated harness spells it `subject-<rung>` --
a Codex identifier that reaches the compiled subject, so renaming it costs
a measurement. The code's word is older than this section's.

**A harness stands in for the driver.** Every subject carries one instead,
because two chapters cannot both define `opening` -- and because the driver is
an operating-system program, not just a compiler one: its effect row is
`[Console, FileSystem, Device.Block]`, its first two acts are painting a
framebuffer and reading a serial line, and it cites Fat16, FactDisk and
ImportGate. Standing in for it is what keeps a subject to the compiler rather
than the OS.

The cost is that a harness can differ from the driver, and where it does, that
is a difference between two drivers rather than between two compilers. The
places they differ are the places their output can legitimately differ from the
seed's: proof pruning, dropped-def handling, mode flags. `passes_to_x86` and `zigc` come
closest to the driver -- they run the same phases in the same order.

**AND AT UPDATE 55 THE COLLISION THAT FORCED ALL OF THIS WENT AWAY.** Upstream
split the entry point out: `opening.codex` now defines `codex-opening`, and a
fourteen-line `codex/compiler/EntryPoint.codex` holds
`opening = codex-opening` and nothing else. `Chapter: Opening` is therefore
BUNDLABLE by a program that supplies its own `opening`, which is the thing that
was impossible for fourteen Updates. It is upstream's own smaller cut of the
seam PR 116 asked for, and it closed PR 116.

So the standing instruction changes direction. A harness should stop
re-implementing the driver and start CITING it: cite `Codex chapter Opening`,
call `compile-frontend-passes` or the phase function the rung is about, and
carry only what the rung genuinely needs to differ in. Every hand copy of the
driver's argument lists is a bug waiting for the next Update to write it --
see the ceremony step below for the count.

### The two arms

Every rung has a **truth arm**, which is the seed on bare metal, and a **zig
arm**, which is the plug's output built and run natively. The per-rung wrappers
are named `ast/truthcycle_<m>.sh` and `ast/<m>cycle.sh` where they exist, but
they are conveniences and the set is incomplete: `lex`'s truth arm is
`ast/truthcycle.sh`, `ir_to_codex`, `ir_to_codex_roundtrip` and `lower` have no
`<m>cycle.sh`, and `ir_to_x86_on_cce` and `passes_to_x86_on_arith` have
wrappers that run the unit they ride in, because they
have no compile of their own to run. The arms themselves are `truth_arm` and
`arm_for` in `ast/oracle_lib.sh`; the wrappers are one line each on top.

A **cycle** is one full turn of a subject through an arm: bundle the source,
compile it (through the seed on the truth arm; through the plug, from banked
IR, on the zig arm), run what came out, compare the output. Every
script with `cycle` in its name is one of these turns -- `truthcycle_<m>.sh`
turns a rung's truth arm, `ast/<m>cycle.sh` its zig arm, and the root
`cycle.sh` turns the plug itself (bundle, ring-compile, and warmup oracles as
the run-and-compare, when named). `allcycles.sh` is exactly its name: the
plug's cycle, then every rung's. When prose here prices a mistake "a cycle",
this turn is the unit -- about a minute for a small probe, a quarter-hour
when the plug itself must rebuild.

**Banking** is recording a truth arm's output as the golden file
(`ast/<m>.truth`) that the zig arm is diffed against. **Re-banking** is doing it
again because something upstream moved -- most often a new seed, which
invalidates both arms at once.

Those working copies are unversioned, because a rung rewrites them on every run.
`bank_truth.py` copies a complete set into `truth/<update>/` under the seed that
produced it, and those are tracked. That is what makes two Updates comparable:
`truth/u45/u45-lower.truth` against `truth/u46/u46-lower.truth` is one rung
measured under two compilers, and the diff is the only artifact that says what
an Update changed in the emitted image. A bank is a set, so it refuses to write
one from a tree where some rungs ran under an older harness than others.

### What a zig-arm turn actually executes

The arm's name suggests the guest has left the loop, and it has not. A
zig-arm turn assumes three artifacts on disk, every one of them seed-produced
in QEMU:

- **the subject's IR** (`ast/<m>.ir`), written by the seed at the last
  re-bank -- the zig arm never re-compiles the subject;
- **the banked truth** (`ast/<rung>.truth`) it will be judged against, from
  the same re-bank;
- **the plug itself** (`zig-plug.cdx` for TCP, `ast/ringplug.cdx` for the
  ring), a CDX binary the seed compiled
  from the ZigEmitter bundle -- `zig-plug.cdx` when `cycle.sh` last
  turned, `ast/ringplug.cdx` when `ringplug_build.sh` did (allcycles.sh
  runs both). The turn guards this with fingerprint checks
  (`plug_provenance`, `refuse_stale_ringplug`) rather than trusting the tree.

The turn itself is three steps:

1. **QEMU boots the plug as the guest kernel**, and the banked IR goes in
   over the rung's transport (TCP or the ring -- below). Codex machine code
   on the virtual metal parses the IR and emits zig source back over the
   wire. On the four expensive rungs this step is nearly all of the wall
   clock: ir_to_x86's IR alone is 13.1 MB on the u47 seed, and every byte crosses
   into and out of the guest.
2. **The host runs the emitted source** -- `zig run`, under the same
   resident bound as the corpus runs. The only step of the turn with no Codex
   code and no QEMU in it.
3. **The output is diffed against the banked truth**, split per rung
   (`zig_verdict` in `ast/plug_arm_lib.sh`). The verdict is the same
   byte-identical claim whichever transport carried the IR.

So the zig arm does not take bare metal out of the loop; it takes out the
seed's *live run of the subject*. The guest is still there twice over --
historically, in that the seed produced the IR, the truth and the plug; and
live, in that the plug transpiles under QEMU on every turn. What is native
is exactly one thing: the subject's behavior, decided by zig-built machine
code instead of seed-built machine code. That substitution is the comparison
the ladder exists to make.

## Two layers, two words

Every rung compiles twice, and the README used one word for both layers
until 2026-08-23. Now:

- The **subject** is what the seed compiles: real compiler chapters, a few
  stubs, and a generated harness, concatenated into `ast/<unit>-subject.codex`
  and compiled under QEMU into a bare-metal CDX (the truth arm) and into IR
  the plug consumes (the zig arm). A subject is a compiler, or the front
  part of one.
- The **program** is what that compiler compiles when it runs: a text
  literal the harness carries (`subject-<rung>` in the generated Codex),
  handed to the subject's own lexer at boot. The program is `Lexer.codex`
  for the `lex` unit and a fifteen-line fib snippet for most of the others.

The truth file is the subject's output while compiling its program: a dump
the harness prints, never the compiler's own artifacts. Every unit below is
described the same way -- what the subject holds, what the program is, what
the harness runs, what flags the compile takes, and what the truth file
contains, line by line -- because those five things are all a rung is.

## Naming

**A unit is named for the stage its subject reaches. A rung is its unit's
name plus `_on_<program>`, when and only when that unit carries more than
one program.** So the `_on_` suffix is the visible mark of the unit/rung
split: exactly four rungs carry one, and they are the two composite units.
`LADDER_RUNGS` in `ast/oracle_lib.sh` is the list of claims and
`LADDER_UNITS` the list of compiles; sourcing the file checks one against
the other, and `truth_prov.py` repeats the check at import.

Renamed 2026-08-23. The old names survive in commit subjects, the
`u46`..`u49-14of14` tags, and upstream issues 70/72 and PR 76, so the map
stays here for good:

| old | rung now | unit |
|---|---|---|
| `fib` | `ir_to_wire` | `ir_to_wire` |
| `text` | `ir_to_codex` | `ir_to_codex` |
| `pingpong` | `ir_to_codex_roundtrip` | `ir_to_codex_roundtrip` |
| `lir` | `lir_to_x86` | `lir_to_x86` |
| `fibx` | `ir_to_x86_on_fib` | `ir_to_x86` |
| `scale` | `ir_to_x86_on_cce` | `ir_to_x86` |
| `whole` | `passes_to_x86_on_mid` | `passes_to_x86` |
| `clamp` | `passes_to_x86_on_arith` | `passes_to_x86` |

`lex parse desugar scope check lower` did not move. The harness CHAPTER
names inside the generated `*Harness.codex` (`FibxHarness`, `WholeHarness`)
and their walker prefixes reach the compiled subject as Codex identifiers
and were deliberately left alone; only the file names follow the unit.
`cce` in a rung name is the chapter `foreword/core/CCE.codex`; `CCE`
elsewhere in this repo is the wire encoding named after it.

## What the truth arm does, for every unit

`truth_arm` in `ast/oracle_lib.sh`, in order: `gen_<unit>_harness.py` writes
the harness (and any stubs it derives from real chapters); `bundle_<unit>.ps1`
concatenates chapters, stubs and harness into `ast/<unit>-subject.codex`
through the author's own `plug-build-lib.ps1`, so cites resolve the way the
depot resolves them; two blobs are written from that source -- a CDX
compile and an IR-CCE compile, each with the unit's mode flags appended --
and each is compiled by the seed in its own QEMU boot (`ring_compile.py`);
the CDX is then booted (`codex_vm.run_cdx`), its serial output captured
with the `WD:`, `HEAP:` and `STACK:` chatter dropped, and written to
`ast/<unit>.raw`; `split_truth.py` turns that into one `ast/<rung>.truth`
per rung -- a copy for a single-program unit, a cut on the
`=== subject <rung> ===` / `=== end <rung> ===` marks for the two
composite units, marks removed. A provenance sidecar records the seed and
the harness content the truth was measured under.

Mode flags (`mode_flags`): `decks=N` raises the seed's compile-time deck
reservation past the derived default; `passes=text-plug` drops the inline
IR passes so emitted source keeps its calls. Both go on BOTH blobs, so
the two arms compile the same thing.

Three refusals sit inside that sequence, and a new unit meets all three:
`check_bundles.py` before the blobs (no chapter under two quires),
`check_diags.py` after each compile (a diagnostic code the POLICY table
does not name stops the arm), and `seed_identity.require_match` after the
split (the seed moved mid-run; the truths are discarded). Between the two
compiles the IR gets its own sidecar (`truth_prov.py stamp-ir`), keyed on
the seed, the subject's bytes and the flags.

One gap worth knowing: the harness-content hash banking checks watches
`gen_<unit>_harness.py` and `bundle_<unit>.ps1`, plus the three shared files
in `truth_prov.SHARED` (`emit_harness.py`, `oracle_lib.sh`, `split_truth.py`)
-- which is why the plug arms live in `ast/plug_arm_lib.sh` and not in
`oracle_lib.sh`: moving them back would rekey every truth on disk, so editing the generator
that owns a composite unit's SECOND program
(`gen_ir_to_x86_on_cce_harness.py`,
`gen_passes_to_x86_on_arith_harness.py`) changes what is measured without
changing the hash.

The front-end units are cumulative -- each subject is the previous one
plus the chapters named, minus the stub those chapters make real (`check`
drops `ScopeStubs`, `lower` drops `CheckStubs`, `ir_to_codex` drops
`LowerStubs`) -- until `ir_to_codex`. After that the subjects branch:
`lir_to_x86` drops the front end entirely, `ir_to_wire` and `ir_to_x86`
grow from `lower`, and `passes_to_x86` grows from `ir_to_x86`. The
"+ chapters" line in each section says what it grows from.

## The twelve units

### `lex` -- the tokenizer

**Subject.** `Core/{BuildSettings,Phase,TextFormat,CdxCodes,Severity,SourceText,Diagnostic}`,
`Syntax/{Token,Lexer}`, plus `LexStubs.codex` (an identity `deck-record`,
since nothing this small carries the phase allocator) and the harness.
**Program.** `Syntax/Lexer.codex`, whole: the lexer tokenizes its own
source. **Harness.** `tokenize` once. **Flags.** none.
**Truth.** `tokens N`, then one line per token: `kind offset+len LxCy`,
with `|text|` appended except for `Newline`, `Indent`, `Dedent` and
`EndOfFile`; then `---` and `errors N`.

### `parse` -- the parse tree

**Subject.** `lex` + `Core/{Name,DiagnosticBag}`, `Types/{CodexType,CodexTypeHelpers}`,
`IR/IRChapter`, `Syntax/{SyntaxNodes,ParserCore,ParserExpressions,Parser}`,
`Foreword/ListUtils`; `LexStubs` still. **Program.** `Syntax/Parser.codex`.
**Harness.** tokenize, `parse-document`. **Flags.** none.
**Truth.** counts interleaved with listings, starting `lex-tokens`: the
counts (`lex-errors`, `chapter`, `defs`, `type-defs`, `prose-len`,
sections, citations, quotations, prose-blocks, annotations), one
`def <name> params N anns N LxCy slug <slug>` line per definition, the
section titles, then `parse-errors`, the diagnostics, `.` and `---`.

### `desugar` -- the desugared AST

**Subject.** `parse` + `Ast/{AstNodes,Desugarer}` and the real
`Core/PhaseAllocator` (Desugarer cites it, and a cite names a chapter, so
`LexStubs` steps aside); `BootPaintStubs.codex` stands in for the screen
painter PhaseAllocator cites. **Program.** `Ast/AstNodes.codex`.
**Harness.** tokenize, parse, `desugar-document`. **Flags.** none.
**Truth.** an abridged parse half (`lex-tokens`, `lex-errors`, `chapter`,
`defs`, the `def` lines, `parse-errors` -- not the section list, type-defs,
citations or diagnostics `parse` prints), then `--- desugar ---`: the
`adef` lines and their counts. Each front-end unit prints its
predecessor's SHAPE this way, never its bytes: the program differs too, so
no two truths share a line.

### `scope` -- scoping and name resolution

**Subject.** `desugar` + `Core/SkipListText`, `Semantics/{ChapterScoper,NameResolver}`;
`ListUtils` is no longer listed because Collections cites it and the cite
brings it; `ScopeCollectionsStubs.codex` (Collections minus its
`bsearch-text-pos` section) and `ScopeStubs.codex` (the builtin table's
names only). **Program.** `Semantics/NameResolver.codex`. **Harness.**
tokenize, parse, desugar, `scope-achapter` with an empty colliding-name
table, `resolve-chapter`; no `scan-document`. **Flags.** none.
**Truth.** the desugar shape, then `--- scope ---`: `resolve-errors`,
`ctor-names`, `top-level-names` and `type-names` counts, then the
constructor and top-level name listings.

### `check` -- inference and checking

**Subject.** `scope` + `Core/Collections` (real, now), `Types/{CodexTypeTree,TypeEnv,Unifier,TypeChecker,TypeCheckerInference}`;
`CheckStubs.codex` is the builtin table with `bs-emit` stripped (that field
is typed over the code generator, which is not here). **Program.** the
built-in fib snippet, fifteen lines and 264 bytes, spelled identically in
NINE generators -- with a tenth, divergent copy in `gen_lex_harness.py` (184
bytes, ten lines), which is a trap for anyone editing fib. This is where the
program shrinks from a real chapter to a toy, and every unit after it compiles fib unless it says otherwise. **Harness.** tokenize, parse, desugar, scope, resolve,
`check-chapter`. **Flags.** none.
**Truth.** the scope shape, then `--- check ---`: one `tb <name> <kind>`
line per type binding, then `substitutions`, `next-id` and `expr-types` as
counts (the substitutions themselves are not listed).

### `lower` -- the IR, as a tree walk

**Subject.** `check` + `IR/{LoweringTypes,Lowering}`; `LowerStubs.codex`.
**Program.** fib. **Harness.** the full front end, `lower-chapter`, with
the driver's `DECK_PROLOGUE` and `RESOLVED_TABLES` taken from
`emit_harness.py`; RESOLVE (`rewrite-ir-defs`) does not run here, so
constructed types stay unresolved in the IR. Like `scope`, `ir_to_codex`,
its roundtrip and `ir_to_wire`, this harness hand-writes its pipeline with
no `scan-document` and empty rename and collision tables; only `ir_to_x86`
and `passes_to_x86` take `frontend_source`'s scan. **Flags.** `decks=100`
(the derived deck scale overflows the seed's CHECK deck on this subject).
**Truth.** the check shape, then `--- lower ---`: `ir-name`, `ir-eff-ops`
and any `eff-op` lines, one `irdef` line per definition, and a pre-order
walk of every expression, `eN <kind>` per node.
A designed dump of the IR, not the IR's own text -- that is `ir_to_wire`.

### `ir_to_codex` -- Codex source out

**Subject.** `lower` + `Emit/CodexEmitter`; `TextStubs.codex`. The bundle
strips every prose line -- about 80 KB, none of it executable (one leading
space marks prose, two mark a definition). It was added when CodexEmitter
put the subject 2.4% over what the 1 MB serial ring could then carry;
`ring_compile.py` streams larger blobs now, so the strip survives as a
property of this banked subject rather than a necessity. **Program.**
fib. **Harness.** the front end, lower, then one call to
`codex-emit-text-chapter`, printed. **Flags.** `decks=100 passes=text-plug`
-- the inline passes would delete the calls the emitted source needs.
**Truth.** the emitted Codex source of fib, and nothing else. This is the
first rung whose truth is the compiler's own output rather than a dump the
harness designed.

### `ir_to_codex_roundtrip` -- the fixed point

**Subject.** the same chapter list as `ir_to_codex`, with
`PingpongStubs.codex` in place of `TextStubs.codex` -- the two stub files
are byte-identical, written by the same bs-emit-stripping transform, so
the subjects differ only in the harness chapter name and the program.
It is a separate unit and always will be:
its program cannot exist until `ir_to_codex` has run. **Program.**
`ast/ir_to_codex.truth` -- the working truth of the previous unit, the
emitted source itself. **Harness.** as `ir_to_codex`. **Flags.** as
`ir_to_codex`. **Truth.** the emitted source again. The rung's real claim is
not arm agreement but `ir_to_codex.truth == ir_to_codex_roundtrip.truth`,
checked by `roundtrip_fixed_point` in the sweep so it cannot be skipped.

### `lir_to_x86` -- the instruction selector, no front end

**Subject.** not cumulative. `Foreword/CCE`, `Core/{OffsetTable,VmProfile,...}`,
`Types/{CodexType,TypeEnv,CodexTypeHelpers}`, `IR/{IRChapter,Lir}`,
`Emit/{EmitAllocator,X86_64Encoder,X86_64State,X86_64Lir}` -- the
selector, its state and encoder, and what CodegenState's fields reach. No
lexer, parser, checker or lowering. Stubs: `BootPaintStubs`, `LirStubs`,
and `CheckStubs` -- which `gen_check_harness.py` writes and nothing here
does, so this unit's truth arm needs `check`'s generator to have run in
the same tree. The sweep orders `check` first, which is why this stays
invisible until someone runs the unit alone. **Program.** two hand-built `LirFunc` values, `add` and `branch`, chosen
to reach the selector's branches -- LIR data structures rather than Codex
text, because this subject has no front end to lex any.
**Harness.** `lir-emit-func` on each. **Flags.** none.
**Truth.** `add len N`, one line of decimal bytes, `branch len N`, bytes.
Compared as text; never executed.

### `ir_to_wire` -- the front end end to end, in IRTextEmitter's grammar

**Subject.** `lower` + `Core/OffsetTable`, `Emit/IRTextEmitter`;
`LowerStubs`. **Program.** fib. **Harness.** the front end and lower with
`DECK_PROLOGUE` and `RESOLVED_TABLES`, no RESOLVE, then `ir-emit-def` per
definition. **Flags.** `decks=100`. **Truth.** six count lines,
`--- ir-text ---`, one `(def ...)` line per definition in the grammar the
IR-CCE wire carries, `.`.

### `ir_to_x86` -- the x86-64 back end, through `finalize`

**Subject.** `lower` + `Core/{OffsetTable,VmProfile}`, `Types/Builtins`
(the real table, so no `CheckStubs`), `IR/{Lir,ResolveTypes}`,
`Emit/{IRTextEmitter,EmitAllocator,CdxWriter}` and fifteen `Emit/X86_64*`
files -- fourteen are pages of one chapter, `X86_64Boot` is a chapter of
its own; `BootPaintStubs` only. About 2.47 MB (u47). **Harness.**
`emit_harness.harness_source` with `passes=False`: the front end with scan
on, `RESOLVED_TABLES`, RESOLVE on (of the twelve units only this one and
`passes_to_x86` run it), then the driver's own `x86-64-emit-cdx` and `finalize`.
The chapter is still `FibxHarness` with `fibx-` walkers. The one compile
runs both programs in one process, printing a mark before and after each.
**Flags.** `decks=160` -- two programs' worth of extents in one run.
**Truth, per rung.** `check-errors N`, `ir-defs N`, `emit-errors N`,
`emit-diags N`, one `diag <code> sev <n> <message>` per diagnostic, `.`;
then, only if the diagnostic bag holds no errors: `header-len`,
`content-len`, `tail-len`, `--- symbols ---` (the symbol map),
`--- header ---`, `--- content ---`, `--- tail ---`, each as decimal bytes
thirty-two to a line; otherwise the single line
`CODEGEN-HALTED: errors in bag; no binary printed`. Digits, not a binary:
`ast/f4_boot.py` is what reassembles and boots them.

#### `ir_to_x86_on_fib`

Program: the fifteen-line fib snippet plus a frameless `double`, chosen for
what they do NOT need -- machine-word arithmetic, two self-calls as the only
fixups, no rodata, no runtime helper. That is what lets `ast/f3_run.zig`
carve fib out of the dumped buffer and call it. Full image in the truth.

#### `ir_to_x86_on_cce`

Program: `foreword/core/CCE.codex` verbatim (refused if it ever gains a
cite; the program compiler resolves none) plus a three-print driver.
Capacity: 61 IR definitions against fib's 3, so accumulators, deck sizing,
the WCET walk and the code buffer all scale. Full image in the truth.

### `passes_to_x86` -- every compiler chapter but two, with the IR pipeline running

**Subject.** `bundle_passes_to_x86.ps1` calls `bundle_ir_to_x86.ps1` and
appends `IR/{Occurrence,IRCheck,LambdaLifting,Simplify,Passes,LirTargets}`
and `Emit/CodexEmitter`. Every chapter under `codex/compiler/` is now in
except `opening.codex` (it defines `opening`, and so does the harness) and
`Core/BootPaint.codex`, which stays the stub: the real painter cites
Foreword CCE, which would put CCE in twice and fail with CDX3001, and
nothing the harness reaches calls it. About 2.58 MB, the largest unit.
**Harness.** `harness_source` with `passes=True`: as `ir_to_x86`, plus
`run-ir-pipeline default-ir-pipeline` exactly where `compile-frontend-passes`
runs it. Calling it is what keeps Simplify, Occurrence and LambdaLifting in
the IR -- emission prunes to what `opening` reaches, so bundling them
without the call would prune them straight back out. Chapter still
`WholeHarness`, walkers `whole-`. **Flags.** `decks=172`.
**Truth, per rung.** as `ir_to_x86`, with `pass-infos N` after `ir-defs` --
the only evidence the pipeline did anything.

#### `passes_to_x86_on_mid`

Program: the twenty-line `Mid` chapter in the generator -- `fib`,
`double`, `scale-by-four`, a `folded` constant, an `opening` printing one
integer -- chosen so each of the three default passes has work
(`fold-constants` on `folded` and `7 * 6`, `inline-leaf-calls` on `double`,
`inline-single-caller` on `scale-by-four`; dropping the inline passes moves
`scale-by-four` from 22 bytes to 29). With fib alone the pipeline is a
no-op and this truth came out byte-identical to `ir_to_x86_on_fib`'s.
Full image in the truth.

#### `passes_to_x86_on_arith`

Program: `codex/test/plug-oracle-arith.codex`, verbatim. Its record field
`Integer between -100 and 100 clamping` produces emit errors, so this is
the one rung whose truth is the diagnostic accounting and `CODEGEN-HALTED`
-- **no header, content, tail or symbol map**. It exists because every
other rung exercises the success path, and it is the rung that caught the
deck intrinsic being off in every bundle we had ever built
(`findings/README.md`). It rides in this unit because the question it asks
-- does the transpiled compiler record the same diagnostics as bare metal?
-- needs the same 2.58 MB compiler as `_on_mid`.

## Counting

Fourteen rungs, twelve compiles (`LADDER_UNITS`), twelve bundler scripts:
`bundle_passes_to_x86.ps1` is one call into `bundle_ir_to_x86.ps1` with
seven extra chapters and its own harness, which is why those two cannot
drift apart. Three rungs carry a
full CDX image in their truth -- `ir_to_x86_on_fib`, `ir_to_x86_on_cce`,
`passes_to_x86_on_mid` -- and those three are what `f4_boot.py` boots.
The ring transport is a property of the unit, not the rung: `ir_to_x86`
and `passes_to_x86` take it, and the four rungs they carry ride in with
them. `CODEX_ALL_RING=1` sends every unit through it, for a venue whose
guest is too small to boot the TCP plug.

The names invite a reading they do not support: `lex` does not test the
lexer. Every rung diverges at the same place -- the seed compiles one
subject twice, and the arms part company only after the seed's own front
end, IR pipeline and IR serializer have all run -- and what is compared is
what the subject prints. If the seed's lexer is wrong, both arms are wrong
together and `lex` is green. The unit names say how much of the compiler
the plug had to transpile, not how deeply that phase was verified.

## What each Update moved

**The bank-to-bank diff is the only artifact that can say what an Update
changed in the emitted image**, and both answers it gives are the point: an
Update that moves nothing we measure and an Update whose diff itemises exactly
what it changed are each something a single sweep cannot tell you. `bank_diff.sh`
produces it; `U<NN>.log` records what each one said. Per-Update detail lives
there rather than here, so this section cannot go stale.

The shape so far: u45 to u46 was byte-identical on all fourteen rungs, and every
Update since has moved between three and five -- almost always `lex`, `parse`
and the image-carrying `_on_` rungs, almost never `lir_to_x86`.

The same diff is what proves a bundle edit image-preserving before it is
trusted; the ones already proven are in `JUSTIFICATIONS.md`. The merge of the
composite units was proven that way: fourteen truths byte-identical under twelve
compiles.

## The two transports

The transport is how a subject's IR gets into the guest. It differs between
rungs; the verdict never does.

- **TCP** (`plug_run_checked.py`) is the default. It exercises the Codex-written
  network stack on every run, which is itself an oracle surface -- it is where
  the odd-frame defect (finding 1: the NE2000 DMA fed one stale byte into
  every odd-length receive) was caught. An output is trusted when the pcap parity
  proof holds (`pcap_parity.py`: frame parity follows TCP payload parity);
  when the proof cannot be established, the fallback is two transfers at
  different chunk sizes agreeing byte-for-byte.
- **The ring** (`plug_run_ring.py`) is for subjects past the TCP intake ceiling.
  The TCP receive path costs ~130 bytes of guest heap per byte of IR; the
  compiler's own serial-ring reader costs one. ir_to_x86's IR is 13.1 MB on
  the u47 seed, so it has no choice.

`arm_for` in `ast/plug_arm_lib.sh` decides, because which transport is needed is a
property of the IR, and the IR belongs to the unit: the `ir_to_x86` and
`passes_to_x86` units take the ring, and the four rungs they carry ride in
with them.

There are two plugs, built from the same `ZigEmitter`: one fed over TCP, one fed
through the serial ring. Both have to be rebuilt together, or a sweep reports
yesterday's emitter for whichever rungs use the other one.

## What the check proves, and what it does not

Be careful about how much DDC to claim here. Two things are true, and both
matter.

**The code generation on the zig arm has genuinely independent lineage.** The
bytes of the zig arm's executable are produced by the zig toolchain, which has
nothing to do with Codex -- not its back end, not its seed, not anything in this
repository. Worth being specific, because it is better than it sounds: the rungs
run their zig with `zig run` (`ast/plug_arm_lib.sh`, `zig_verdict`), and zig 0.16
does not use LLVM for that. It uses its own x86-64 back end. Measured on the
command the rungs actually use, not on a nearby one: `zig run` produces a
10,253,773-byte binary and `zig run -fllvm` produces a 4,113,312-byte one. So
the machine code on the two arms comes from two independently written x86-64
code generators, and a third is one flag away if we ever want it.

When the two arms agree on the output of a compiler phase, that
agreement crossed a real toolchain boundary. This is the DDC property, and it is
the reason the ladder is worth running.

**The seed is still in the loop.** The plug consumes IR, and it is the seed that
compiles the subject down to that IR. So both arms pass through the seed before
they diverge. The seed has not been removed, and this ladder on its own is
therefore not a complete DDC witness -- it is a DDC check over the part of the
pipeline that comes after the IR.

And the caveat that outranks both:

What it proves is **agreement, not correctness.** Both arms descend from the
same source, so a mistake they share is a mistake the ladder cannot see -- if
the back end computed a rodata offset wrongly, the transpiled back end would
reproduce that faithfully and the diff would be empty. That is what
`ast/f4_boot.py` ("Consumers of what the ladder emits", below) is for:
booting the emitted binary asks a third party with no stake in the argument.

One shape of the shared-mistake worry is closed for the content section, and
by the compiler's own hand: the CDX header carries a SHA-256 that
`cdx-build-header` computes over the content bytes, and recomputing it from
the decimal bytes the four back-end truths print reproduces it in all four
(audited 2026-08-18, no violations -- alongside header offsets that tile
exactly, symbol extents that tile with no gaps, a debug map whose 722 names
all match the symbol map, and `ir_to_codex_roundtrip.truth` byte-identical to
`ir_to_codex.truth`). Two arms drifting into the same nonsense would have to keep a
hash the emitting compiler computed for its own reasons while doing it.

Two provenance facts that bound all of it:

**The plug is not an independent tool.** `zig-plug.cdx` is `ZigEmitter.codex`
compiled *by the seed* and run *as a QEMU kernel*. The seed therefore produced
both the IR the two arms rest on and the tool that generates the zig arm. The
only lineage in the building genuinely unrelated to Codex is zig's own back end.

**Nothing here is checked by running it.** Even in the strongest rungs the CDX
bytes are compared as digits. `ast/f3_run.zig` and `ast/f4_boot.py` do execute
emitted code, but they run artifacts already known to be byte-identical between
arms, so each is one execution rather than a comparison -- and neither is in
`allcycles.sh`.

Which leaves two sentences worth being careful about.

**What this establishes.** Given IR produced by the seed, the zig plug plus an
unrelated x86-64 code generator reproduce, byte for byte, the observable output
of the seed's own back end across fourteen rungs over twelve subjects, up to
and including the entire compiler minus its driver -- and for three of those
rungs, the complete CDX image the compiler emits.

**What it does not establish.** That the seed is honest. The seed sits upstream
of the divergence on both arms, and it also compiled the plug that produces the
zig arm. Agreement here is evidence about code generation, not about the front
end both arms inherit.

## What this needs, and what it does not

**It needs almost no changes to the Codex repository.** Everything Linux and
QEMU specific lives here. The driver that boots the guest, `codex_vm.py`, is
ours: it launches QEMU directly and re-implements the contracts the author's
`codex-vm` host provides (the guest RAM size written at physical `0xFE8`
before boot, the ring preload, the paced serial send) rather than calling
`Start-VmRun` in `build/vm-config.ps1`. Every plug defect the ladder found
was fixed in `ZigEmitter.codex` and carried upstream, so the checkout needs
at most the fixes that have landed upstream but postdate the Update being
banked. That claim is checkable, and the command is the check:

    git -C <your Codex clone> log --oneline <release-commit>..HEAD

The baseline is the release commit of the Update being banked, never
`upstream/master` -- the mirror moves mid-Update (the author's Perforce main
runs ahead of the public releases, and landings of our own PRs appear
between them), so a moving baseline cannot anchor a claim. What may sit on
top of the release commit is defined under "The checkout" below; anything
else is a patch nobody has justified, which is what the check is for.

**From the checkout, tracked and used unmodified:** `seed/Codex.cdx`,
`build/concat-codex-self.ps1`, `codex/plugs/common/plug-build-lib.ps1`, the
chapters under `codex/compiler/`, and `codex/test/plug-oracle-arith.codex` with
its `.expected`.

**From the checkout, NOT tracked, and self-regenerating:**
`codex/plugs/zig/build-output/zig-plug.cdx` and `plug-source.codex`. A fresh
clone does not have them, and nothing needs building to get them: `cycle.sh`
regenerates both -- it runs the author's bundler with the compile step
stubbed out (`Build-PlugCdx` is replaced, since that step needs the author's
Windows host) to write `plug-source.codex`, then compiles that through the
seed with `ring_compile.py` to produce `zig-plug.cdx` and its fingerprint.
`ast/allcycles.sh` runs `cycle.sh` first, so a fresh CODEX clone needs no
prior build step, and `cycle.sh` is the only producer of these artifacts
here (it alone writes the fingerprint `plug_provenance` demands; the
author's own plug build is Windows-only and never runs on this host). A
fresh LADDER clone is a different matter: the banks are tracked, but the
working `ast/*.truth` and `ast/*.ir` files the arms consume are not. It does
NOT need a rebank for them. `ast/allcycles.sh` restores what it can and
rebuilds the rest: `restore_truths.py` copies each banked truth into place
rather than re-measuring it, and `ast/ensure_ir.sh` regenerates any missing
or unstamped `.ir`. Before those existed the only way to get those files was
a full rebank -- about 27 minutes spent producing INPUTS.

**From the host:** `qemu-system-x86_64` (8.2.2), `python3` (3.12.3),
PowerShell 7 installed at `~/.local/pwsh/pwsh` (the bundling scripts invoke
that path directly; 7.5.4 here), and `zig` (0.16.0) for the arm under test.
`/dev/kvm` is optional: `CODEX_ACCEL` selects the accelerator and the
default is `tcg` -- which measured FASTER than KVM for this workload
(see "The droplet venue"). A second ssh-reachable host for the compile
stage is optional too; nothing requires it.

**Point it at a checkout with `CODEX_ROOT`.** The ladder lives outside the
tree it audits, so it cannot find one by looking upward, and it will not
guess:

    CodexRootError: no Codex checkout at or above /home/you/codex-zig-ladder
    (looked for codex/compiler/opening.codex); set CODEX_ROOT to the checkout
    you mean

That refusal is the feature. A ladder silently pointed at the wrong checkout
banks truth against a seed nobody named, which is the single failure this whole
exercise exists to prevent. Pointing it at each Update in turn is the same
variable and no other change. `ladder_root.py` resolves both roots and is the
only thing that knows where the checkout is; `check_paths.py` asserts every
path the ladder opens resolves, without running a rung, so a bad setup is a
five-second answer rather than an hour-two surprise.

The ladder repo itself clones from
`git@github.com:showell/codex-zig-ladder.git`; see the NOT-tracked
paragraph above for what a fresh ladder clone must regenerate first.

## The zig build mode is part of the experiment

**Every zig build in this ladder is Debug, and that is a decision rather than
a default nobody looked at.** No `-O` flag appears anywhere in the repository:
`native_build.sh`, `cycle.sh`, `tier_run.py`, `overnight_verify.sh`,
`ast/oracle_lib.sh` and `recon.sh` all invoke `zig run` or `zig build-exe`
bare, and bare means Debug.

Keep it that way, for a reason specific to what this ladder is for. Its job is
to find places where the plug and bare metal disagree. Debug turns undefined
behaviour into a loud panic at the point it happens; a release mode turns the
same divergence into a wrong answer that may still compare byte-identical by
luck, and a rung that passes by luck is worse than one that fails.

**What actually changes with the mode.** Measured on zig 0.16.0, one program
per cell:

| behaviour | Debug | ReleaseSafe | ReleaseFast | ReleaseSmall |
|---|---|---|---|---|
| a local declared `= undefined` reads as | **0xAA** | 0x00 | 0x00 | 0x00 |
| signed overflow | **panic** | **panic** | wraps | wraps |
| slice index past the end | panic | panic | UB | UB |
| `@intCast` out of range | panic | panic | UB | UB |

The top two rows are measured, one program per cell. The bottom two follow
zig's documented safety-check placement and have not been measured cell by
cell here, though they are the ones this ladder leans on hardest.

The first row is a narrower claim than it looks, and is **not** finding 27's
question. That finding is about `Allocator.alloc`'s `@memset(_, undefined)` on
a runtime-sized buffer surviving optimisation; this row is about a fixed-size
local, which a release build may fold away whether or not the memset elsewhere
survives. Neither is evidence for the other.

**The asymmetry with bare metal is the part worth internalising.** Bare metal
has no build mode. Its guarantees are *in the instruction stream*:
`emit-index-bounds` emits two UD2s around every `list-at` and `char-at`, and
`emit-substring-bounds` emits three around every `substring`. Ours are partly
in the build mode. `cx_list_at` is `l.items.items[@intCast(i)]` and
`cx_char_at` is `s[@intCast(i)]` -- both correct today, both correct *because
we build Debug*. So "the plug matches bare metal on out-of-range access" is a
claim about Debug, and only about Debug.

**This has already bitten once.** Finding 27 hid for as long as it did because
its mechanism was mode-dependent: `Allocator.alloc` memsets to `undefined`,
which is 0xAA in Debug and elided in ReleaseFast, so the old code was
zero-and-lazy in a release build and 0xAA-and-committed only in the mode we
actually use. Finding 18 is the same family from the other side -- the plug was
overflow-checked where the language wraps, and the fix was to use wrapping
operators, which are mode-independent *on purpose*.

**So if anyone ever wants release-mode rungs**, the prelude has to carry its
own explicit checks first, rather than borrowing zig's. Otherwise several
guarantees the findings register depends on evaporate silently and the ladder
stays green while doing it. Changing the mode also invalidates the plug arm of
every banked truth; the bare-metal arm is unaffected, which is why
`tier_run.py` banks that column and not this one.

## Running it

Paths below are relative to this repository; the bundlers and rung scripts
live in `ast/`, the transports and VM helpers at the top level. Everything wants
`CODEX_ROOT` in the environment:

    export CODEX_ROOT=/path/to/your/Codex/clone

    ast/truthcycle.sh         # one rung's truth arm: bundle, compile, bank
    ast/lexcycle.sh           # the same rung through the plug, diffed
    ast/allcycles.sh          # rebuild both plugs, sweep all fourteen
    ast/rebank_all.sh         # re-bank every truth arm, then sweep

    verify_emitter.sh         # the standing answer to an EMITTER change: six
                              # legs -- natives, the type-variable case matrix,
                              # the corpus, the codexzig fixed point, the Roc
                              # ports, and the sweep. The sweep is leg 5 of 6.
                              # It exists because the chain was assembled by
                              # hand twice in one day and the second assembly
                              # measured a tree two commits behind the one
                              # under test. It stamps both HEADs before it
                              # starts so that cannot happen quietly again.
    zigc_verify.sh            # re-runs the zigc transcript; caches the build
    run_seed_probe.sh         # compile a probe on BARE METAL, the seed, in
                              # QEMU. Read its header before asking any
                              # question about what "the compiler" does:
                              # native/codexir is the compiler as OUR PLUG
                              # renders it, and answering a compiler question
                              # with it cost a wrong report upstream, twice.
    check_harness_gates.py    # the two hosted harnesses copy two lists from
                              # the driver (emit roots, and the diagnostic
                              # bags gating emission). This compares them to
                              # each other AND to opening.codex, because
                              # agreeing with each other is necessary and not
                              # sufficient -- the emit-roots list once drifted
                              # in both at once, and being wrong together
                              # looks exactly like being right.
    roc_ports_run.py          # eleven programs ported from Roc's evaluator
                              # suite, against Roc's own expected values --
                              # a second oracle written by people who have
                              # never seen this emitter

A passing rung prints one line:

    ORACLE PASS: zig lex output byte-identical to bare-metal truth

**`ast/allcycles.sh`** rebuilds both plugs and then sweeps every rung. It is the
guard against fixing one rung and breaking four. A unit whose output contains
neither `ORACLE` nor `TRANSPORT FAILED` is failed. `ORACLE` matches both
`ORACLE PASS` and `ORACLE DIFF`, so the rule is not catching failure -- it is
catching **silence**, a rung that produced no verdict at all. One did once, and
read exactly like a rung that never ran.

**`ast/rebank_all.sh`** re-records every truth arm and then sweeps.
Run it bare: it relaunches itself detached into
`logs/rebank-<stamp>.log` and prints the tail command, so a hung VM or
a closed terminal cannot take the verdicts with it. Run it after any seed change: a new seed invalidates both arms, since it compiles the truth
binary *and* produces the IR-CCE the plug consumes. It is ordered cheapest rung
first and stops on the first failure, because the failure modes are shared.

Then the smaller pieces:

- `ast/truthcycle_<m>.sh` / `ast/<m>cycle.sh` -- one rung, one arm, where such a
  wrapper exists (see the two-arms section: the set has holes, and the
  `_on_cce` and `_on_arith` wrappers run the unit they ride in).
- `ast/plugcycle.sh <m>` -- rebuild and run one rung, reporting markers grepped
  from the emitted zig. Error counts under-report: zig stops at the first
  `@compileError`.
- `cycle.sh [prog...]` -- rebundle the zig plug and ring-compile it, then run
  whichever warmup oracles you NAME. `cycle.sh hello recurse fib` runs three
  small programs with banked answers (gitignored; a fresh clone regenerates
  them with `warmups/regen.sh`) and checks the plug end to end before any
  rung is worth running -- a warmup diff fails the cycle; `cycle.sh` with no
  arguments, which is how
  `allcycles.sh` invokes it, rebuilds the plug and runs no warmups at all.
- `tier_run.py <program.codex>` -- one small Codex program on BOTH arms, side
  by side, with a marker on every line that moved. This is the unit-test loop
  rather than the rung loop: the tier files (`findings/prim-*.codex`) price and
  pin one primitive family each, and the probes beside them isolate a single
  question. Seconds on the plug's side; the bare-metal column is banked under
  `findings/gold/`, keyed on the program's bytes plus the seed sha, so it costs
  QEMU once and re-runs itself when either changes. Most of the findings
  numbered 21 and up came from here rather than from a sweep -- a rung says
  which of fourteen programs disagreed, a tier says which primitive did.
- `ring_compile.py` -- compile through the seed under QEMU via the codex-vm ring
  contract. This is the compile path, not the transport of the same name. Blobs
  larger than the 1 MB ring stream through it: the host refills behind the
  guest's read cursor over the gdbstub. `ring_refill_test.sh` is that path's
  oracle.
- `codex_vm.py` -- launch/READY/run helpers shared by the above.
- `droplet_*.sh` and `sweep_*.sh` -- drive this box's QEMU from a second
  host. Read their headers; "The venue" below says where they stand.

Costs -- this section is the one home for timing figures; re-measure and
update them here at every rebank. Measured 2026-08-29 (seed `B066CEB5`,
pin `u53-rebank` at `58b08c38`, this 8 GB box, `CODEX_MEM_MB=3072` TCG,
per-unit timestamps in `logs/rebank-20260829-170007.log`):

- **`rebank_all.sh` end to end is 43.5 minutes** (2612 s) -- 31.5 for the
  twelve truth arms (1894 s) and 13 for the trailing sweep (777 s elapsed
  by its own report, 718 s across the units). Truth arms, cheapest first:
  lex 17s, parse 56s, desugar 64s, scope 71s, check 129s, lower 168s,
  ir_to_codex 178s, roundtrip 164s, lir_to_x86 29s, ir_to_wire 186s,
  **ir_to_x86 362s, passes_to_x86 470s**. The last two are 44 per cent of
  the truth side between them and always have been -- 43 per cent at
  Update 51, so the shape is stable across two seeds.
- **The sweep** runs all fourteen rungs in 13 minutes: lex 5s, parse 19s,
  desugar 20s, scope 24s, check 55s, lower 64s, ir_to_codex 69s,
  roundtrip 68s, lir_to_x86 6s, ir_to_wire 63s, ir_to_x86 132s,
  passes_to_x86 193s.
- **The rest of a cycle, same box and seed.** `native_build.sh` 341 s;
  `tiers_run.py` as a set 26 s once the natives exist (the bare columns
  come from `findings/gold/uNN/` and cost nothing); a `core` corpus transpile
  of 1,233 programs 357 s; `codexzig`'s eight stages 449 s, three of them
  guests. See "Corpus testing" for what a two-arm comparison costs, which is
  not this number -- it depends on the change.
  `sweep_canary.sh` (lex+parse+desugar) is a REMOTE driver -- it sources
  `sweep_lib.sh`, calls `run_unit_remote`, and assumes `sweep_prep.sh` has
  run -- and its own header budgets 2-3 minutes including the straw. Adding
  scope would push it further for little coverage.
- **A sweep's cost depends on what it has to REBUILD, and the biggest
  term is not the sweep.** A sweep in a tree with no `.ir` files rebuilds
  all twelve through `ensure_ir` first: the 2026-08-27 01:56 sweep took
  1656 s that way against this one's 861 s in a tree the truth arms had
  just filled. Same fourteen rungs, same emitter, same seed; the
  difference is inputs. Read a sweep timing with its tree's state
  attached or it means nothing.
- **The sweep used to be the expensive half and is not any more.** It was
  1716 s on 2026-08-23 and 657 s on 2026-08-24 with the SEED UNCHANGED, so
  the 2.6x is the ladder's own work, not the Update's -- the emitter grew
  the self-tail-call transformation in that window (PR 81) and the zig arm
  of the two big units was the slow half. Attributed by window and by
  mechanism; nobody has ablated it, so read it as the likely cause rather
  than a measured one.
- **The census re-pin** (`native_build.sh`, then `corpus_run.py --changed
  --bank`): the natives are 11 minutes, the census a few more. Every Update
  re-pin reruns all of it, because the natives are rebuilt and every emitted
  zig has to be re-derived before it can be compared.

  **Re-deriving everything does not mean the emitted zig MOVES.** The natives
  change on every build -- their shas move for reasons as trivial as the
  directory they were built in -- while the zig they emit usually does not.
  Expect almost all of it to come back the same, and treat the handful that
  moved as the result. That asymmetry is the whole basis of the corpus method
  above.

Run long jobs detached and watch for the markers above.

## The venue

Everything computes on this box (the 8 GB ladder droplet, dedicated,
since 2026-08-23): natives, tiers, census, sweeps, rebanks, each in its
own sandbox (next section), detached with a log. Every compute entry
point refuses on a host without `CODEX_LADDER_VENUE`, which
`~/.codex_ladder_env` exports along with the guest sizing
(`CODEX_MEM_MB=3072`, `CODEX_ACCEL=tcg`; why: JUSTIFICATIONS.md "Droplet
compile venue"). The laptop edits and reads logs; nothing authored lives
only there.

`droplet_*.sh` and `sweep_*.sh` at the repo root drive this box's QEMU
from a second host over one held ssh per job (log lines stream back, the
exit code propagates, artifacts scp back); their headers carry their
contracts. They are keyboard-tempo tools, not the ceremony's path.

## Machine capacity

What this box has, what each kind of job is ALLOWED to cost, and which of
those numbers are ceilings rather than measurements. Written 2026-08-27
because "one compute job at a time" had been standing in for an arithmetic
nobody had done, and the question it is really asked to answer -- may a
second job run beside this one -- cannot be answered without it.

| | |
|---|---|
| RAM | 7,941 MB |
| CPUs | 2 |
| Swap | **none** |
| Disk | 154 GB, 117 GB free |

**No swap is the fact the rest of this section turns on.** An over-commit
here is not a slowdown somebody notices and backs out of; it is an OOM
kill, and the kernel picks the victim. Every ceiling below exists to keep
a sum under 7.9 GB, and a job with no ceiling is a job that can take the
box down with it.

### The declared ceilings

Numbers in the code, not observations. Three bound a job; the fourth is a
gap.

| what | ceiling | where |
|---|---|---|
| A QEMU guest | 3,072 MB | `CODEX_MEM_MB` in `~/.codex_ladder_env`; the seed guest dies silently above it |
| The zig arm of a rung | **6 GB** | `ZIG_ARM_MEMORY_MAX`, `ast/oracle_lib.sh:356`, applied by `bounded_run` |
| An emitted binary under a corpus runner | 800 MB | `RUN_MEMORY_MAX`, `corpus_run.py:207`; the full corpus replayed under it with zero hits and a max RSS of 145 MB |
| **`codexzig` itself** | **none** | `codexzig_corpus.py:89` runs the tool with no `BOUNDED` prefix |

**3 GB + 6 GB does not fit in 7.9 GB, and neither number is wrong.** They
never overlap inside one sweep, because a rung's arms are sequential: the
guest compiles the subject and exits, and only then does the zig arm run.
The 6 GB is a ceiling for a job that HAS the box, not a budget for sharing
it. Two jobs each honouring its own ceiling can still add to an OOM, so
the ceilings are not by themselves an argument that concurrency is safe.

**The unbounded one is what to fix before anything runs beside a sweep.**
`codexzig_corpus.py` bounds the emitted program it builds and does not
bound the tool that emits it, while `corpus_run.py`'s own comment calls the
resident bound "not optional". The incident that bought that rule -- an
unbounded runaway livelocking a whole host, 2026-08-19 -- is available to
any codexzig run today.

### What a guest actually costs

A guest's declared size is a RESERVATION. QEMU's resident set grows with
the pages the guest touches, so a 3,072 MB guest does not cost 3,072 MB
until it needs to. Sampled every five seconds across the last four minutes
of the u51-repair sweep -- `passes_to_x86`, the largest unit, through the
ring arm:

    peak qemu RSS      1,012 MB   against a 3,072 MB guest
    peak system used   1,991 MB
    minimum available  5,950 MB

**The zig arm's real peak is UNMEASURED and the 6 GB ceiling has never
been approached in a recorded run.** This sweep could not measure it:
`~/.cache/zig` is 21 GB, it is GLOBAL rather than per sandbox, and exactly
one file in it was written during the whole run -- so the zig builds were
cache hits and no `zig` process was resident long enough to sample.
`overnight_verify.sh:99` already wraps one rung in `/usr/bin/time -v`,
which is the cheapest way to get the number when it is wanted.

### The rule, and what is sacred in it

**One QEMU guest at a time is the invariant** (Steve, 2026-08-27). Two
guests stacked do not fail; they thrash, which reads as mysterious
slowness rather than as the refused launch it should have been.

**"One compute job at a time" is the older and broader form of that rule,
and it is broader than the invariant needs.** Today the two are one lock:
`compute_lock.take()` is a flock plus an "is any `qemu-system-*` running"
check, taken both by `codex_vm.launch` -- the one line in this tree that
starts a guest -- and directly by three runners that start no guest at all
(`corpus_run.py:449`, `codexzig_corpus.py:95`, `codexzig_scale.py:53`). So
a codexzig corpus pass and a sweep exclude each other for a reason that has
nothing to do with guests.

**And it is not applied consistently**, which is the tell that it is policy
by accident rather than by decision: `roc_ports_run.py:106` calls
`require_venue()` and never takes the lock, so the same class of work --
codexzig over a named set, then `zig run` -- is lock-free in one runner and
lock-holding in its neighbour. Neither starts a guest.

The lock conflates two questions with different answers: *may I start a
guest* (one at a time, sacred) and *may I use this box* (a capacity
question, which the tables above are the input to). Separating them is what
would let a codexzig pass run beside a sweep. It is not done, so the honest
statement today is that concurrency here is UNTESTED, not that it is
forbidden.

### Where the newest `codexzig` lives

`codexzig` is not one binary in a known place. `codexzig_build.sh` builds it per
sandbox (~10 minutes), `native/` is gitignored, and a fresh sandbox carries
none -- so "the current one" is always a question about `~/runs`, never about the
checkout, and any answer written here goes stale within days.

What stales one, roughly in the order it happens: the emitter
(`codex/plugs/zig/ZigEmitter.codex`), the ladder's harness chapters and the roots
list they share, the compiler chapters `codexir` bundles, and the seed -- because
the build runs through the seed and the ring plug before it reaches its own fixed
point.

## One sandbox per experiment

Every run on a shared box gets its own directory. `./sandbox.sh <label>`
makes two detached worktrees -- the ladder and a Codex checkout -- plus an
`env` file that points `CODEX_ROOT` inside the sandbox, and a `MANIFEST`
recording both commits. Then:

    ./sandbox.sh my-experiment
    cd ~/runs/<stamp>-my-experiment/ladder && . ../env

`./sandbox.sh --list` shows them; `./sandbox.sh --prune [keep]` removes all
but the newest N and prunes the worktrees.

The failure this prevents is not a run that crashes. It is a run that reads
yesterday's artifact and PASSES. Every output the ladder produces is
gitignored -- `ast/*.truth`, `*.truth.prov`, `*.ir`, `*.zig`, `*-subject.codex`,
`*-source.codex`, `native/*` -- so a shared checkout quietly accumulates a
complete set of plausible, real, stale files under exactly the names the next
run looks for.

**A generated file in source control goes stale and misleads rather than
documenting anything.** `ast/zigemit-source.codex` was tracked until 2026-08-29
as a "provenance snapshot" -- until it was measured: 279,579 bytes against the
366,757 a real Update 53 bundle produces, six ZigEmitter commits and 2,380 lines
stale. Diffing against it did not say which tree a build came from; it said
which tree plus everything since, with no way to tell those apart. Nothing was
lost by untracking it, because git history holds every snapshot ever committed.

Two other instances in one afternoon on 2026-08-21: a debug-instrumented
`native/codexir` and a clobbered `ast/codexir.zig` left where a later census
would have used them without complaint, and blobs written to fixed `/tmp` paths
a second experiment would have overwritten.

A fresh worktree carries none of those, which is the whole point: a run that
needs natives must build them or be handed them deliberately, and cannot
inherit them by accident. Worktrees share the object store, so the cost is
the working tree rather than the history -- about 400-700 MB a sandbox against
119 GB free on the droplet.

Pointing `CODEX_ROOT` inside the sandbox is deliberate too: it makes "someone
pulled the shared checkout mid-run" stop being a thing that can happen.

## What identifies a run

A ladder result is never identified by one thing. It takes a pair of refs --
which Codex tree was measured, and which ladder tree did the measuring -- plus
an identity for the two native tools that did it. Neither repo's `git log`
holds the pair, which is what `U<NN>.log` and a sandbox's `MANIFEST` are for.

**The natives cannot identify themselves, and this cost real time to learn.**
Zig bakes the build directory into every binary it produces, for stack traces.
Every ladder run happens in a fresh sandbox by design. So a sha over
`native/codexir` moves on every single run whatever the source did -- the main
checkout's binaries still read
`/home/steve/runs/20260826T160728Z-u50-harness-lift/ladder/ast` out of a plain
`grep -a`, because they were built in a sandbox and copied in.

Three mechanisms compared those shas across runs and none of them could work.
Two of them could only ever report a difference, which made a guard phrased
"the stamp must have changed, or the fix never reached the build" pass every
time; one could only ever report the bank as stale, which made the census
banner fire on every run and re-banking pointless. **A check that has lost the
ability to fail has not lost the ability to look like a check**, and that is
the failure mode this whole tree is built to prevent.

`tool_identity.py` names a tool by its INPUTS instead -- the four things
`build_one` actually feeds it:

    the bundled subject   what this tool IS
    the ring plug bundle  what transpiled it
    the seed              what compiled it
    the zig version       what linked it

None of them mentions a path, which is the property that makes the answer
portable. `zigc_verify.sh` had exactly this list inline since 2026-08-25,
where it turns a seven-minute build into an 8.7-second cache check; it was
right there first and simply had no name until `corpus_run.py` became the
second user.

So the corpus census records both halves. `meta.built_from` is the tool
identity; `meta.base` is the source coordinates -- codex sha, branch (or
`null` and a `codex_points_at` list when detached, which is the normal case),
ladder sha, seed. `bank_describes_this_tree` answers three ways: **same**,
**different**, and **unknowable** for a bank taken before 2026-08-29, whose
`tools` field holds binary shas that cannot be compared to anything.

**The general rule, and the one worth carrying elsewhere: identify a
measurement by its source coordinates, never by its materialised artifacts.**
A repo and a ref survive being rebuilt, copied, relocated and pruned. A binary
does not. And when you build the thing that does the identifying, check that
it can say NO -- `census_confirm.sh` exists to ask a bank about a tree it has
never seen, and its negative control (cut at a different ref, expect
`different`) is not optional.

## Operating rules

1. **Sweep after any emitter change.** `ast/allcycles.sh`. One rung passing
   proves nothing about the other thirteen.
2. **Re-bank after any seed change.** `ast/rebank_all.sh`, before any diff means
   anything. The full procedure, prerequisites included, is "Processing a
   new Update" below.
3. **Validate a new subject standalone first.** Compile it through the seed on
   its own (about a minute) before spending a full cycle -- a quarter-hour to
   bank plus the same through the plug, for the expensive rungs -- discovering
   it does not compile.
4. **One QEMU guest at a time is the invariant**; "one compute job per host"
   is how it is enforced today. `codex_vm.launch` takes the lock -- the one
   line in this tree that runs qemu -- so no entry point has to remember to,
   and it refuses beside a FOREIGN guest too (the Codex tree's own
   `build/compile.ps1` starts one and asks nobody). "Machine capacity" above
   has the arithmetic and names the runners that take the lock without ever
   starting a guest.
5. **Every emitted-binary run is bounded** (`bounded_run`: cgroup
   MemoryMax). A runaway dies oom-killed and is recorded as such; the
   bound is never lifted to make a rung pass. Measurements:
   `JUSTIFICATIONS.md` "The resident bound, measured".

## The checkout: cloning and branching

How the Codex clone `CODEX_ROOT` points at is managed. This lived in nobody's
head for a while and the head it lived in got confused, so, written down:

**The pin is a branch named for the Update.** `uNN-rebank` points at the
release and nothing else; `ladder_status.py` prints whether it still equals
`upstream/master`, and today it says `u54-rebank = upstream/master exactly`.

**At Update 54 the stack is ONE PR, and it is named for its contents rather
than by the `uNN-stack` template: `u54-plus-pr100`.** Nine of the ten PRs
outstanding at Update 53 landed in the release; the tenth, PR 100 (the zig
plug's `real-to-int` / `real-from-int`), did not, and its emitter is not in
the tree. It is not a defect on their side -- the emitter was verified correct
upstream and the blocker is that its `.expected` encodes x86's answers for NaN
and overflow into `codex/test/ops`, which `build/test-cross-batch.ps1` grades
on arm64 and riscv64 too, where both saturate.

**That branch exists for safari-codex, which cannot build without it** -- 50
of its chapters call the pair -- and it is a stack in the README's sense above,
so a claim measured with those builtins present names `u54-plus-pr100` and a
baseline is banked on bare `u54-rebank`.

**When there IS a stack, it is a BRANCH, not working-tree edits**, named
`uNN-stack`, and `git diff uNN-rebank..uNN-stack` is exactly what we are
carrying. Drop a PR's part at the next pin move rather than carrying it twice.

**Which of the two you measure on depends on what the number is FOR, and this
used to be written as one rule.** It is two.

- **A finding, a defect number, a claim in a PR: measure on the STACK.** A
  number taken on bare upstream is a number about a compiler already missing
  our own fixes, and it will be wrong in the direction that flatters us.
  Name the branch in the PR, so the reader can reproduce it.
- **A BASELINE that later runs are compared against -- the corpus census
  above all -- is banked on PLAIN UPSTREAM.** It is the tree everything else
  is measured against, so it has to be one Damian would recognise. A census
  banked on our stack folds our unlanded branches into every future
  comparison silently, and the rows never say so. `rebank.sh` enforces this
  and says why in its header; the 2026-08-29 census is banked at `58b08c38`,
  bare.

The distinction is not pedantry. The two answers differ by exactly the work
we have sent and they have not taken, which is the quantity a reviewer most
needs held still.

**A stack is committed, never working-tree edits.** A patch is not a commit --
a `git checkout`, a pin move, or a stash nobody pops drops it silently, and the
next measurement is then against a different compiler than the last one named,
with nothing recording the difference. Committing costs nothing and removes the
whole class.

**Two remotes, with different jobs.** `upstream` is `damiant3/Cobblestone`
-- renamed from `NewRepository` on 2026-08-25, with the interim push that
absorbed our six PRs. GitHub redirects the old URL, so nothing broke and
nothing announced itself; the remote here was repointed at the new name
because a redirect is a courtesy, not a fact to depend on. **Our fork keeps
its own name**, `showell/NewRepository`: a fork does not follow its
upstream's rename, and the asymmetry is real rather than a mistake to fix.
The local directory is still `~/showell_repos/NewRepository` and stays that
way -- sandbox MANIFESTs record it by path, and renaming it mid-cycle would
strand every one of them.

`upstream` is read-only in practice: the mirror is downstream of the author's
Perforce, so nothing merges there and PRs are landed by being re-applied on
their side. `origin` is the `showell/NewRepository` fork, and it exists to
hold pushed branches: PR branches, and the pin branch below. A local `master`
has no job in this model: reference `upstream/master` directly and keep no
local `master` -- a branch nobody advances only goes stale and then reads as
if it means something.

**The ladder runs against a pin branch, one per Update.** When an Update is
being banked, the checkout sits on a branch named for it (`u47-rebank`),
created at the Update's release commit and never rebased. On top of the
release commit it carries the fewest cherry-picks the ladder cannot run
without, and each must already be landed or filed upstream -- the pin is a
delivery vehicle for nothing. `git log <release-commit>..HEAD` is the
whole statement of what we changed, and the ideal length is zero.

Update 47's pin ran to SEVEN cherry-picks, six of them correctness fixes, so
its zig arms measured the pin rather than the verbatim release -- exactly the
deviation step 4's working rule exists to prevent. Every pin since starts at
zero and stays there, and the census re-pins verbatim too: the noisy bank is
the honest bank (agreed, Steve + Claude, 2026-08-20).

**The working tree parks on the pin for the entire banking cycle.**
`CODEX_ROOT` names a working tree, not a commit: a `git checkout` there
mid-sweep rebuilds the plug from whatever the tree now holds, and that cost a
90-minute sweep once (2026-08-18). The fingerprint guard in `oracle_lib.sh`
now refuses to run arms when the plug's chapters or its bundle moved
under a built plug, but the guard is a tripwire, not a workflow. PR work
therefore never happens in this tree: branch in a disposable `git worktree`
somewhere else (the session scratchpad), off `upstream/master`, push to the
fork, and delete the worktree after the PR lands; `git worktree prune` in the
main clone clears the stubs.

**Pulling an Update:** `git fetch upstream`, read the release commit (its
message names the seeds and what moved), create `u<NN>-rebank` at it,
cherry-pick only what the ladder still needs, push the pin to the fork, then
follow "Processing a new Update" below. The register of "what the ladder
still needs" is `findings/README.md` plus the "Outbound queue" in
`PRIORITIES.md`: anything there marked filed-but-not-landed is a candidate,
and the first check is always whether the Update just landed it. The pin
being on the fork means no clone is precious.

**Re-cloning from scratch** is therefore cheap and occasionally worth doing,
since a long-lived clone accumulates branches from work that has since
landed. `git clone git@github.com:showell/NewRepository.git`, then
`git remote add upstream https://github.com/damiant3/Cobblestone.git`, then
`git switch u<NN>-rebank` (the pin is on the fork). Git carries everything
else: point `CODEX_ROOT` at the new clone, let `check_paths.py` prove the
wiring in five seconds, and the first `cycle.sh` (or the sweep, which runs
it) regenerates the untracked plug artifacts from the seed.

## Processing a new Update

What happens when the depot publishes a release, in order. Each step exists
because skipping it has already cost something once; the citations are to the
Update where it did.

### 1. Stand on THEIR driver, not on a copy of it

**Before anything else, ask what our side still re-implements.** Every harness
that copies the driver's phase order is a copy of something we do not own, and
it goes stale silently: Codex curries, so a call left short of an argument is a
FUNCTION VALUE, not an error. Five of the last seven Updates moved a phase
function we call, and every one was found by a rung dying an hour into a run.

Update 55 split the entry point out -- `opening.codex` defines `codex-opening`,
`EntryPoint.codex` holds `opening` -- so **`Chapter: Opening` is bundlable by a
subject that supplies its own entry point**, and a harness can call the driver
instead of restating it. `ast/emit_harness.py`'s `driver_cdx_source()` does
that, and `zigc` uses it: thirty lines of copied phase order and deck arithmetic
became two calls.

    in let fe = compile-frontend-cdx src "Codex_Codex" compile-flags-default
    in let res = compile-to-cdx fe

**Where a harness cannot cite the driver, say why in the harness prose.** The
cost is real and worth stating: a subject carrying `Chapter: Opening` reaches
serial, device and x86-64 code, so a source plug then owes emitters for paths a
hosted target never runs. That is a reason to stay with a copy; "we always have"
is not.

### 2. Run the linters before any guest

Three checks, all seconds, all needing no QEMU. They exist because each one has
already been paid for the expensive way.

**Arity -- our calls against their signatures.**

    xref arity ast/ $CODEX_ROOT/codex/ --phases     # driver phases only
    xref arity ast/ $CODEX_ROOT/codex/              # everything

Indexes every definition in the checkout by its parameter list and walks every
application in ours. `lower-chapter` went 8 -> 9 -> 11 across three Updates and
`check-chapter` 5 -> 9 at U54; the second of those went unnoticed for two
Updates and is the actual cause of the T38 refusal, where the emitter cannot
type the closure it must generate for a call four arguments short. Partial
application is legal, so a short call in argument position is dropped; `--partial`
shows those.

**Cites -- does each bundle define what it reads.**

    python3 check_bundles.py            # every bundle, rung subjects and plugs

`xref bundle` under the hood, and it names the file to add rather than only the
name that is missing. cycle.sh runs it on the plug bundle between bundling and
the guest. The gap it closed: for years this asked only about
`ast/<m>-subject.codex`, so the plug bundle -- the one every rung depends on --
was the one nobody checked, and a bundle short three chapters cost 23 seconds of
QEMU and a dead sweep to discover.

**Pages -- is a multi-file chapter still all there.**

    python3 check_zig_pages.py          # Chapter: Zig Emitter is four files

A chapter spanning k > 1 files needs `Page N of M` at every foot, and every
bundler must LIST the pages. Upstream adding, renaming or renumbering one is a
red line here rather than a pile of undefined names inside a bundle.

**A green from all three is not a promise the compile passes.** They answer
NAMES and COUNTS, never shapes. A bundle they call complete can still fail on a
type.

### 3. Read before running anything

Fetch, and read the release commit against our own registers before any
compile runs:

- **The release note against `findings/README.md` and the open issues.** An
  Update that closes something we filed also orphans the workaround we built
  for it, and a workaround that outlives its finding actively corrupts
  measurements: the `deck-record` rename outlived the finding Update 43
  closed and silently disabled the seed's deck discipline in every bundle for
  weeks. When a finding closes, grep for its workaround and delete it in the
  same commit that acknowledges the closure.
- **The diff on the surfaces we speak or re-implement.** Two files on our
  side hard-code the host contracts rather than calling `Start-VmRun`:
  `codex_vm.py` carries the RAM size cell at physical 0xFE8 and the serial
  `SIZE:` framing, and `ring_compile.py` carries the ring itself
  (`RING_ADDR` 0x500000, `RING_SIZE` 1 MB pinned to the seed's
  serial-ring-buf-size, and the wpos/rpos cells 28704/28712 pinned to
  `X86_64Boot.codex`). A release that touches `codex/compiler/Emit/` (the
  boot stub and output helpers), `tools/codex-vm.c`, or `build/vm-config.ps1`
  can move a contract either file hard-codes, and a moved contract shows up
  as a diff in every truth at once, indistinguishable from a compiler
  change. Read those diffs against BOTH files first. Also
  `codex/plugs/zig/` (the emitter is fleet-maintained now, see step 6) and
  the net stack if the TCP arm matters to the question at hand.
- **The seed hashes.** The release note names the public seed; depot `main`
  may already be several seeds past it. The bank is a claim about the
  released seed, so everything below uses the release commit, not main.
- **THE DRIVER'S SIGNATURES, BEFORE ANY GUEST RUNS.** Five of the last seven
  Updates moved a phase function our harnesses call, and every one of them was
  discovered by a rung dying an hour in rather than by reading. `lower-chapter`
  alone has moved three Updates running:

      U53   8 params                              -> IRChapter
      U54   9 params  (+ rename : Boolean)        -> IRChapter
      U55  11 params  (+ keep-base, keep-ceiling) -> (IRChapter, Integer)

  **An arity change here does not read as an arity error.** Codex curries, so
  an under-applied call is a FUNCTION VALUE, and the type error surfaces one
  line later against whatever consumes the result -- at U54 and again at U55 it
  read `CDX2001: Type mismatch: Rec:IRChapter vs Fun` against `run-ir-pipeline`,
  naming neither the call nor the argument it wants. That cost an afternoon the
  first time. Read the signatures instead:

      # every signature the release moved, in the files our harnesses call into
      git -C $CODEX_ROOT diff <old> <new> -- codex/compiler \
        | grep -E '^[-+]  [a-z][a-z0-9-]* :' | sort -u -k2

      # every driver function our harnesses call
      grep -ohE '\b(compile-[a-z-]+|lower-chapter|check-chapter|scope-achapter|resolve-chapter|run-ir-pipeline|lift-lambdas)\b' \
        ast/*Harness.codex ast/gen_*_harness.py | sort -u

  Every `^[-+]  <name> :` line is a signature that moved. **`xref arity` does the
  crossing** -- see step 2 -- so read the diff for INTENT and let the tool find
  the call sites. What the diff tells you and the tool cannot: whether a new
  parameter wants a value the harness has lying around, or a deck reservation it
  has to compute.

  The size of the exposure is worth seeing written down. Measured 2026-09-03:
  **9** hand-written `lower-chapter` calls, 22 `resolve-chapter`, 17
  `scope-achapter`, 10 `check-chapter`, 5 `run-ir-pipeline`. Fifty-odd call
  sites we wrote against signatures we do not own, in a language that answers an
  under-applied call with a value rather than an error. Step 1 is how that
  number goes down; step 2 is how it stays honest until it does.

  **The fix for the class, not the instance**, is the entry-point split that
  landed at U55: cite `Chapter: Opening` and call the driver's own phase
  functions, so a moved signature is a compile error at the call we did not
  write. See "A harness stands in for the driver" above.

### 4. Probe the contract before committing hours to it

Both seeds are one `git show <commit>:seed/Codex.cdx` away, and
`ring_compile.compile_ring(..., seed=...)` accepts an explicit seed, so the
cheap experiment needs no checkout CHANGE -- `CODEX_ROOT` must still name a
valid checkout for the imports to resolve, but it can stay wherever it is.
The seed parameter is not reachable from `ring_compile.py`'s command line;
call the function. Reuse a small blob from an earlier run's working tree --
blobs are gitignored, so a fresh tree has none until `ast/arithcycle.sh`
(which writes `ast/arith-cdx.blob` in its first seconds) or any rung has
run once -- and run the pair:

    git -C $CODEX_ROOT show <old>:seed/Codex.cdx > $SANDBOX/seed-old.cdx
    git -C $CODEX_ROOT show <new>:seed/Codex.cdx > $SANDBOX/seed-new.cdx
    python3 -c "import ring_compile as r; \
      r.compile_ring('ast/arith-cdx.blob', '$SANDBOX/probe.cdx', seed='$SANDBOX/seed-new.cdx')"

(`$SANDBOX` is what `sandbox.sh`'s env file exports; probe artifacts belong
to the experiment's directory, not `/tmp`.)

and the same line with the old seed for the baseline. This confirms the new
seed boots under our QEMU flags, takes the ring preload, and produces output
our reader parses. Five seconds per compile. If the release claims
throughput work, add one mid-size unit for a timing point (`check` at 4.8 MB
of IR showed Update 47's FIFO-burst output as about 10 percent of wall
time). If output differs in size for the same input, that is the first look
at what the Update changed in the image -- note it, it previews the bank
diff.

### 5. Prerequisites for the rebank itself

- **The clone sits on the pin branch, and the SEED must be the release's.**
  The pin ("The checkout" above) is the release commit plus its sanctioned
  cherry-picks, none of which may touch seed identity. `seed_identity.py`
  derives the bank's name from the release note that names the seed's hash,
  so a seed-file swap into an older tree banks as `seed-XXXXXXXX` rather
  than `uNN` -- honest, but not the label anything else references. A clean
  tree, parked on the pin.
- **The tree must not move while the ladder reads it.** `CODEX_ROOT` names a
  working tree, and a checkout mid-sweep rebuilt the plug from the wrong
  emitter once and reproduced an already-fixed defect (2026-08-18, 90
  minutes). Know what is actually guarded: the TCP plug's fingerprint is
  two shas (`plug_fingerprint` in `oracle_lib.sh`, read by
  `plug_provenance`) -- the two chapters an operator edits, and the
  BUNDLE that was compiled, which is the half that also covers
  `PlugTypes.codex` and `IRTextParser.codex`. The ring plug's guard is
  still the stronger one, because it RE-BUNDLES: `ringplug_build.sh`
  records the bundle sha in `ast/ringplug.cdx.fp` and `plug_run_ring.py`
  re-bundles and refuses a mismatch before booting, so it catches a
  source edit that was never bundled and this one does not. Banking refuses a moved
  seed or moved harness content after the fact (the `truth_prov` sidecars),
  and the truth arm records the seed as it begins and refuses its own
  truths if `seed_identity.require_match` finds it moved by the split
  (`oracle_lib.sh`). The zig arms have no such check. Everything beyond
  that is operator discipline:
  do not touch the clone until the run finishes or is killed. The clone is
  not PR scratch space during a sweep -- build PRs in a worktree elsewhere.
- **`seed_identity.py` says the right thing** (seed hash, Update number,
  `truth/uNN` target) and **`check_paths.py` passes.** Five seconds, versus
  discovering a broken path an hour into the truth arms.
- **One compute job.** Nothing else runs until the bank is taken.
- **Bank the tier columns before the long run.** `./tiers_run.py --bare`
  runs every tier's bare-metal arm under the new seed -- seconds each --
  and writes `findings/gold/uNN/`. Gold is keyed to the seed, so a re-pin
  stales every column at once; banking them here, tracked, is what lets
  the next Update diff tier rows the way `bank_diff.sh` diffs truths.

### 6. Decide what the zig arms measure

The truth arms depend only on the seed. The arms phase builds the plug from
the tree's `ZigEmitter.codex`, and since the depot settled ownership
(2026-08-18: the zig plug is ordinary fleet code, edited like any other
plug), the emitter in a release is theirs, possibly carrying fixes we do not
have and missing fixes we have not landed.

The working rule: **sweep the release's emitter verbatim.** The sweep is then
a measurement of what the depot shipped, which is the claim a `uNN` bank
should stand behind; rungs that fail under the verbatim emitter but passed
under our local fixes are precisely the list of what needs to go upstream as
small PRs from master, which is the flow the depot asked for. Local emitter
fixes live as PR branches, never as a standing fork the sweep quietly
depends on -- the longer a fix stays local, the more the fleet's own edits
drift under it.

This rule is a judgment call, not a law of the setup. The alternative --
sweep with our fixes applied, so the arms stay green and the bank lands
faster -- measures a compiler nobody ships. If the fleet's emitter and ours
diverge far enough that verbatim sweeps are mostly red, the right response
is landing the fixes, not softening the rule; revisit it if that flow stops
working.

One carve-out (agreed, Steve + Claude, 2026-08-19): a capacity prerequisite
the big arms cannot RUN without on this machine may ride the pin, provided
it is already landed or filed upstream -- a bank whose two biggest rungs can
never execute measures less, not more honestly. A correctness fix may not,
because a wrong answer IS the measurement.

### 7. Run, bank, retire

**A NEW SEED MEANS REBANK, NOT SWEEP, AND THE ORDER IS NOT NEGOTIABLE.** A
sweep (`ast/allcycles.sh`) compares this plug's arms against BANKED truths, and
a new Update's seed has none -- `restore_truths.py` says `NO BANK for this
seed` and the sweep used to carry on regardless. It does not fail there; it
fails whenever the first rung needs a `.truth` as its own subject, which is
`ir_to_codex_roundtrip`, six rungs and 398 seconds of QEMU later, as a
FileNotFoundError out of a harness generator. Measured on the first U55
sandbox. `allcycles.sh` now refuses at second zero and names the remedy, but
the order is the thing to remember: **rebank, then sweep.**

- **Warmups first**: `./cycle.sh hello recurse fib` checks the plug end to
  end on the new checkout in minutes. `rebank_all.sh` does not run them --
  its first plug exercise is the sweep at the END, hours in, so a gross
  plug-side breakage found there was findable at the start.
- Then the rebank. `ast/rebank_all.sh` detaches itself (nohup, a log
  under `logs/rebank-<stamp>.log`, the compute lock taken first) so a
  hung VM cannot take the verdicts with it; run it plainly and tail the
  log it names. Run it in a sandbox (`./sandbox.sh uNN-rebank`), never in
  the shared checkout.

  Truth arms run cheapest-first and stop on the first failure; a CDX9002 on
  a big rung usually means the deck scale -- the seed's compile-time memory
  reservation -- needs raising (the `decks=` entries in `oracle_lib.sh`'s
  `mode_flags`), not that something broke.
- **Bank as soon as the truth arms are green** (`bank_truth.py`), whatever
  the zig arms have done or whether they have run at all. A truth is a
  bare-metal measurement and the plug cannot reach one; `bank_truth.py`
  derives what the arms said from `ast/<rung>.diff` and records it in
  `ARMS` beside `SEED`, where `bank_diff.sh` reads it back. Green arms gate
  the banked-against table and the `uNN-14of14` tag, whose own name is the
  rule.
  Terminology, because a crashed session once nearly tagged over its
  absence: the rebank RECORDS working truths (`ast/<m>.truth`; its
  "banked" log lines mean this) -- the BANK is `truth/uNN/`, written
  only by an explicit `bank_truth.py`, which `rebank_all.sh` never
  runs. "All banked" in a rebank log does not mean the bank exists.
  `--force` REPLACES the destination with the ready subset; after an
  interrupted rebank, re-run the missing units instead. It refuses
  mixed-harness sets on its own, which is the one bank rule that catches a
  real lie and is still in code.
- Diff the new bank against the previous one: `./bank_diff.sh` (defaults
  to the two newest banks, so this instruction cannot go stale per
  rebank). Byte-identical rungs are the headline when they happen (u45 to
  u46: all fourteen), and any rung that moved is the Update's image
  change, localized to a subject.
- Re-pin the diagnostics populations -- an EDIT to the `POLICY` table in
  `check_diags.py`, taking the new counts from the `--census` block
  `allcycles.sh` prints at the end of the sweep. The counts are a function
  of the unit list and the seed, and a stale pin cries wolf.
- **Re-measure the timings and put them in this README, every rebank.** The
  log has the wall time per phase (truth arms, plug builds, arms); refresh
  the numbers in "Running it" in the same commit that updates the
  banked-against table, so the cost quoted is always the cost under the
  CURRENT seed. Stale timings misprice every scheduling decision made from
  them, and the timings are also the check on a release's own throughput
  claims: Update 47's FIFO-burst output showed up as roughly 10 percent on a
  mid-size unit, and the rebank is where such a claim gets measured at full
  scale rather than assumed.
- Update the banked-against table at the top of this file, tag
  (`uNN-14of14`), push. Tags are the ladder's two fixed points: `uNN-14of14`
  on the commit that banked an Update, and `prNN-verified` on the ladder
  commit whose chain verified an outbound PR (the PR body cites it, with
  the branch tip and the bank it was measured against).
- **The tiers as a set, after the natives.** Rebuild `native/` from the
  checkout the bank measured (`native_build.sh`), then
  `./tiers_run.py`: every tier both arms, one verdict line each. Green
  or `noted` (differs only on rows `findings/gold/EXPECTED.txt` names)
  is a pass; `RED` is an unexpected disagreement and `STALE` is a ledger
  row whose arms now agree -- a finding closed, or a row to delete. Both
  want a human before the tag. The set runs in about three minutes and
  the ledger is where a known divergence is admitted, dated, with its
  finding number; a cost row that quietly moves is visible there and
  nowhere else.

## Consumers of what the ladder emits

These are run by hand, not by `allcycles.sh`; the sweep's cost covers the
fourteen rungs only.

The rungs prove the plug emits the same bytes. These ask whether the bytes mean
anything.

The `f` numbers are milestones of the fib ladder: F1 was fib through the front
end, F2 was fib through the x86 back end (the `ir_to_x86_on_fib` rung), F3 runs the emitted
code, F4 boots the emitted binary.

- `ast/f3_run.zig` -- carves a function out of an emitted CDX, drops it in RWX
  memory and calls it. `fib(30) = 832040`, from both the truth dump and the zig
  dump. Works because the emitted code uses the System V ABI and buffer-relative
  call displacements.
- `ast/f4_boot.py` -- reassembles the dump into a real CDX the way
  `emit-binary-tail` does (header, content, tail), boots it, and checks it prints
  what its program says. Six binaries: the fib, cce and mid programs, from truth and from
  zig. This is the one check that does not depend on the two arms sharing a
  mistake.
- `native_build.sh` -- builds `codexir` (.codex -> .ir) and `zigemit`
  (.ir -> .zig), the two tools that take QEMU out of the pipeline entirely.
  `zigemit` is not a second implementation: it is the same `ZigEmitter`, bundled
  with a four-line body that reads stdin and writes STDERR (print-text is
  std.debug.print in the emitted runtime -- a wart, and why every caller
  uses `2>` redirects) instead of the ring plug's serial framing, then
  transpiled and built like anything else here.
- `codexzig_build.sh` -- builds `codexzig`, which is `codexir` and
  `zigemit` in ONE program: Codex source in on stdin, zig out on stderr, one
  process. Not a merge of the two emitted zig files (that was studied and
  rejected -- they share hundreds of declarations, so a textual merge is a
  pile of duplicate symbols to rename inside generated code); it is one
  Codex bundle, `codexir`'s chapter set plus two chapters, the emitter and
  the IR text parser. **The two halves are joined by a `let`, not a pipe:**
  the harness emits the IR text and parses it straight back in memory. That
  round trip is deliberate. A direct hand-off looked possible, because
  `emit-zig-chapter` takes the compiler's own `IRChapter` -- but the wire
  DERIVES what the AST does not carry (`IRTextEmitter.codex:404-406` infers
  a record's implicit type parameters as it serialises, finding 44), so the
  direct version emitted zig that will not compile for a type declared like
  `SortPartition`. Going through the wire makes this the same code in the
  same order as `codexir | zigemit`, which is why agreement with the
  pipeline is structural.
  **The build ends with the fixed point**: the binary it just produced must
  re-emit `ast/codexzig.zig` -- the file the seed-under-QEMU plus
  ring-plug-under-QEMU path wrote minutes earlier -- byte for byte.
  `./codexzig_build.sh --check <prog.codex>` transpiles one program both
  ways and byte-compares, refusing a `CODEGEN-HALTED` or an output carrying
  no `pub fn main`, because two tools failing identically is not a pass.
- `codexzig_corpus.py` -- the breadth and correctness runner for `codexzig`:
  every corpus program byte-compared against the pipeline, and the
  well-behaved subset (clean + match) built, run, and checked against the
  depot's `.expected`. The `.expected` half is one of two checks in this tree
  whose oracle was written by someone with no knowledge of the plug; the
  other is `roc_ports_run.py`, whose expected values are the Roc project's
  own, written by people who have never heard of Codex.
- `codexzig_scale.py` -- the deck. Every unit subject through `codexzig`
  with its deck peak and headroom (JUSTIFICATIONS "The deck costs ~145 MB per
  MB of source"), then a squeeze that lowers the reservation and confirms
  the failure is still finding 45's: negative headroom printed and ignored,
  twice the reservation reached, a GP fault in `cx_list_at`, and no emitted
  zig written.

## zigc: the compiler as an ordinary process

`ast/ZigcHarness.codex` is the `passes_to_x86` unit's chapter set with a real I/O
boundary instead of a baked-in Text literal and a decimal dump: **source in on
stdin, a CDX binary out on stdout.** Built the same way every rung is -- bundle,
compile to IR with the seed, transpile through the plug -- and then
`zig build-exe` on the result.

    $ ast/gen_zigc_harness.py && pwsh ast/bundle_zigc.ps1   # write and bundle it
    $ # ...then compile that subject to IR with the seed and push it through the
    $ # plug, exactly as a rung's two arms do, leaving ast/zigc.zig
    $ zig build-exe ast/zigc.zig -femit-bin=zigc      # 16,905 lines of zig, no
                                                      # @compileError markers, ~4s
    $ ./zigc < ast/repro-mid.codex > mid.cdx          # ~3s
    $ ls -l mid.cdx
    -rw-r--r-- 1 steve steve 87257 mid.cdx

**What it emits is a CDX, not an ELF**, because it is a port of the Codex
compiler and emitting a bare-metal image is what that compiler does. So the
output still wants a machine to boot it:

    $ python3 -c "import codex_vm; codex_vm.run_cdx('mid.cdx')"
    program output (0s):
      > 276

For that subject the 87,257 bytes were byte-identical to what the seed produces
for the same source, and the binary booted and printed the same answer. Roughly
three seconds against about a minute for the equivalent VM round trip.

Two things it is not:

- **Not the driver.** It stands in for `opening.codex` and skips what that
  chapter does around emission -- proof pruning, dropped-def handling, mode
  flags. For subjects that need none of it the output matches the seed's byte
  for byte; for subjects that do, it legitimately differs, and comparing the two
  is comparing two different drivers rather than two compilers.
- **Not a native-code compiler.** `zigc` runs natively; its *output* is still a
  kernel image. Compiling a Codex program to something Linux runs directly is
  the other axis -- transpile the program itself through the plug
  (`prog.codex -> prog.ir -> prog.zig -> zig build-exe`), which is what
  `native_build.sh`'s two tools automate.

## Generated files

`ast/gen_<m>_harness.py` writes `ast/<M>Harness.codex` -- except
`gen_ir_to_x86_on_cce_harness.py` and `gen_passes_to_x86_on_arith_harness.py`,
which own only their unit's second program; the harness itself comes from
the `ir_to_x86` and `passes_to_x86` generators. `ast/emit_harness.py` holds the compile pipeline once --
`frontend_source` (source text to a lowered IR) and `pipeline_source`
(that plus the x86 emission) -- so the five generators that run it
(`gen_ir_to_x86` and `gen_passes_to_x86`, whose units carry the `_on_` rungs;
`gen_zigc`; `gen_codexir`) cannot drift from each other. Four more
generators import only its shared tables (`DECK_PROLOGUE`,
`RESOLVED_TABLES`).

The bundlers are PowerShell (`ast/bundle_<m>.ps1`), because they call the
repository's own `plug-build-lib.ps1` to resolve chapter cites. That is why pwsh
is a requirement here.

Everything generated is ignored and regenerates from a script beside it. The
scripts are the record. There are no exceptions as of 2026-08-29; the last
one, `ast/zigemit-source.codex`, is written up under "One sandbox per
experiment" as a worked example of why a generated file in source control
goes stale and misleads rather than documenting anything.

## Open questions

- ~~The `zigc` transcript above has no runner behind it~~ Resolved by
  `zigc_verify.sh`, which does the elided middle step and caches the
  expensive build by fingerprint (`rm zigc` forces a rebuild). Its header
  states the reason it exists: "a number nothing re-checks is a number that
  was true once." **Still wrong, verified 2026-08-29: the transcript names
  `ast/repro-mid.codex`, which does not exist and is gitignored
  (`ast/.gitignore`). `zigc_verify.sh` defaults to `ast/repro.codex`, which
  is tracked.** The fingerprint it caches on moved to `tool_identity.py` on
  2026-08-29 and is now 16 hex where it was 64, so the first run after that
  change rebuilds `zigc` once.
- ~~`passes_to_x86_on_arith`'s paragraph points at finding 11~~ Resolved. Finding 11 was
  withdrawn as filed: the cause was ours, a harness that skipped the driver's
  RESOLVE phase. What survived it -- `emit-record` laying a record out by a
  rule no reader uses when the type is unresolved -- is closed in Update 46.
  What `passes_to_x86_on_arith` actually earned is separate and larger: it is the rung that
  caught the deck intrinsic being off in every bundle we had ever built.
- **Could the seed be taken out of the loop entirely, making this a complete
  DDC witness?** Today both arms pass through the seed, because it is the seed
  that compiles a subject down to the IR the plug consumes. `codexir` and
  `zigemit` are the beginning of an answer -- a native compiler emitting IR and
  a native plug consuming it -- but nothing yet establishes that a
  seed-independent chain produces the same IR, which is the claim that would
  matter.
