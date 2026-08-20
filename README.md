# The zig plug's phase-oracle ladder

## What this is banked against

| | |
|---|---|
| Seed | `930FF7F174E1E126` (2,872,563 bytes) |
| Update | 48 (release commit `b643e7cb`, pin verbatim) |
| Rungs | **14 of 14 green** |
| Banked | `truth/u48/`; the newest three banks are kept (`bank_truth.py --keep`), older ones live in git history |

This table is the point of the whole arrangement, so it is the first thing on
the page and it is allowed to be unflattering. A ladder that cannot say which
seed it agrees with is not evidence about anything.

Mid-rebank, the checkout's pin branch runs one Update ahead of this table --
`seed_identity.py` names the new Update while `truth/` still holds only the
old banks. That is the normal in-between state, not drift: the table moves
only when `bank_truth.py` lands the complete new set.

The table above is maintained by hand; what cannot drift is the BANK's label,
because `seed_identity.py` derives it from the seed's own hash by finding the
release note that names it. Run it to see what a checkout is actually holding,
and correct the table against it.

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
release of the Codex repository; the release commit names its seed.

**The plug** (`codex/plugs/zig/ZigEmitter.codex`) transpiles Codex IR into zig
source: `prog.ir -> prog.zig`, which `zig build-exe` then makes native. Point it
at the compiler's own IR and you get the Codex compiler as an ordinary Linux
process instead of a kernel.

**A rung** is one test. It bundles part of the compiler into a single
compilable unit -- the **subject** -- and compiles that subject twice. The
first compile is the real one: the seed, on bare metal, under QEMU. The second
goes through the plug: the same subject, transpiled to zig, built by
`zig build-exe`, run as a Linux process. Both print the same thing, and the two
outputs must be **byte-identical**. A rung that passes says the transpiled
compiler and the real compiler agree about that much of the compiler.

The ladder exists to test whether the transpile is faithful. The answer has to
be byte-exactness rather than "it seems to work", because a transpiled compiler
that is subtly wrong produces subtly wrong binaries forever after.

## The parts

**A chapter** is Codex's module: one `.codex` file, naming what it `cites` from
other chapters. The compiler is about sixty of them, and a rung's subject is
some subset concatenated into one compilable unit.

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

Five objectives, ranked by how much of the repo serves each. A change that
serves none of them probably belongs somewhere else.

1. **Prove the zig transpilation of the Codex compiler faithful, to the
   byte.** The rungs, the two arms, the banks and the provenance guards all
   exist to force byte-identity between seed-compiled and plug-transpiled
   output, up to the whole compiler emitting a complete CDX image.
2. **Find defects -- in the plug and in Codex itself.** The byte-exactness
   pressure is the instrument; `findings/README.md` is the register of what
   it has caught, and probes-then-filings is the loop.
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

Side products worth knowing about even though no objective claims them: the
QEMU drivers are the only non-Windows implementation of the author's host
contracts, and so their de facto written spec; and the corpus harness
(`corpus_run.py`, which grades the emitter against the depot's hand-oracled
test programs) is plug-agnostic, so a future plug in another language could
be graded against the same banked IR and truths on day one.

## Anatomy of a rung

### The subject and its harness

A rung's subject is usually a set of real compiler chapters, concatenated. Three
rungs use something else -- `pingpong` takes another rung's output, `scale` takes
a single chapter verbatim, `clamp` takes a small program written to fail -- but
the shape is the same either way: one compilable unit, compiled twice.

**A harness stands in for the driver.** Every rung's subject carries one instead,
because two chapters cannot both define `opening` -- and because the driver is
an operating-system program, not just a compiler one: its effect row is
`[Console, FileSystem, Device.Block]`, its first two acts are painting a
framebuffer and reading a serial line, and it cites Fat16, FactDisk and
ImportGate. Standing in for it is what keeps a subject to the compiler rather
than the OS.

The cost is that a harness can differ from the driver, and where it does, that
is a difference between two drivers rather than between two compilers. The
places they differ are the places their output can legitimately differ from the
seed's: proof pruning, dropped-def handling, mode flags. `whole` and `zigc` come
closest to the driver -- they run the same phases in the same order.

### The two arms

Every rung has a **truth arm**, which is the seed on bare metal, and a **zig
arm**, which is the plug's output built and run natively. The per-rung wrappers
are named `ast/truthcycle_<m>.sh` and `ast/<m>cycle.sh` where they exist, but
they are conveniences and the set is incomplete: `lex`'s truth arm is
`ast/truthcycle.sh`, `text`, `pingpong` and `lower` have no `<m>cycle.sh`, and
`scale` and `clamp` have wrappers that run the unit they ride in, because they
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
   clock: fibx's IR alone is 13.1 MB on the u47 seed, and every byte crosses
   into and out of the guest.
2. **The host runs the emitted source** -- `zig run`, under the same 2.5 GB
   address cap as the corpus runs. The only step of the turn with no Codex
   code and no QEMU in it.
3. **The output is diffed against the banked truth**, split per rung
   (`zig_verdict` in `ast/oracle_lib.sh`). The verdict is the same
   byte-identical claim whichever transport carried the IR.

So the zig arm does not take bare metal out of the loop; it takes out the
seed's *live run of the subject*. The guest is still there twice over --
historically, in that the seed produced the IR, the truth and the plug; and
live, in that the plug transpiles under QEMU on every turn. What is native
is exactly one thing: the subject's behavior, decided by zig-built machine
code instead of seed-built machine code. That substitution is the comparison
the ladder exists to make.

## The fourteen rungs

Every rung carries a generated harness, including the ones whose subject cell
names a file: `scale`'s subject is `CCE.codex` verbatim *plus* a small driver,
because a subject with no `opening` cannot be run. Where a cell says
"subject = X", read it as "X is what this rung compiles", not "X is the whole
unit".

`LADDER_RUNGS` in `ast/oracle_lib.sh` is the list of claims and `LADDER_UNITS`
the list of compiles, shared by the sweep and the re-bank so they cannot
disagree about what the ladder is. Sourcing the file checks one against the
other: a rung no unit carries, or a subject no rung banks, refuses rather than
going quietly stale.

The subject column is cumulative: `+ parser` means everything above it plus the
parser. Where a rung replaces the subject outright rather than extending it, the
cell says so.

| rung | subject | what it newly puts under test |
|---|---|---|
| `lex` | compiler chapters + harness | the tokenizer |
| `parse` | + parser | the parse tree |
| `desugar` | + desugarer | the desugared AST |
| `scope` | + chapter scoper | scoping |
| `check` | + type checker | inference and checking |
| `lower` | + lowering | the IR |
| `text` | + codex-text emitter | source out, not a dump: stage 1 of a fixed point |
| `pingpong` | subject = `text`'s OUTPUT | stage 2: `text1 == text2` or the serializer lies |
| `lir` | + instruction selector | machine-code bytes; the harness's functions are chosen to reach the selector's branches |
| `fib` | front end end to end | one `(def ...)` line per definition, in IRTextEmitter's own grammar |
| `fibx` | + the whole x86 back end, through `finalize` | a complete CDX binary, symbol map and all |
| `scale` | subject = `CCE.codex` verbatim | capacity. 61 IR defs against fib's 3 |
| `whole` | every chapter but `opening.codex` | the middle end too, and it must actually run (below) |
| `clamp` | subject = `codex/test/plug-oracle-arith.codex` | the **error** path -- the one rung whose subject does not compile cleanly |

The ladder is broadly cumulative, so a failure names the phase that broke rather
than "the plug is wrong". It is not strictly a phase order, though: five rungs
vary the *output* rather than the phase set. `text` and `pingpong` emit Codex
source, `fib` emits the IR in IRTextEmitter's grammar, and `lir` and `fibx` emit
machine code. That is why the third column reads "what it newly puts under
test" and not "where this sits in the pipeline".

Two rungs need a word.

**`whole` runs the IR pipeline.** IR emission prunes to what the opening
reaches, so bundling `Simplify`, `Occurrence` and `LambdaLifting` without
*calling* `run-ir-pipeline` prunes them straight back out. The harness calls it
exactly where `compile-frontend-passes` does. Its subject is also chosen to make
the passes do something: dropping the inline passes moves `scale-by-four` from
22 bytes to 29, so a broken inliner fails the rung instead of passing it.

**`clamp` exists because every other rung exercises the success path.** Its
subject produces emit errors, which is how the diagnostic accounting got tested
at all -- see `findings/README.md`.

Four rungs -- `fibx`, `scale`, `whole` and `clamp` -- are the ones that run the
back end all the way to a CDX. They are also the four that need the ring
transport, and the four that are expensive to run. All three facts follow the
same boundary.

## What each rung is worth

The ladder's names invite a reading it does not support. `lex` does not test the
lexer. **Every rung has the same shape and diverges at the same place**: the
seed compiles one bundled subject twice, once to a bare-metal CDX and once to
IR-CCE, and the two arms part company only after the seed's front end, IR
pipeline and IR serializer have all run. Both arms then execute, and what gets
compared is program output text. Only the subject changes from rung to rung.

So the phase names describe **how much of the compiler the plug had to
transpile**, not how deeply that phase was verified. If the seed's lexer is
wrong, both arms are wrong together and `lex` is green.

What does vary, and what the ladder is really graded on, is *what artifact the
agreement is about*:

| rungs | compared artifact | what agreement is worth |
|---|---|---|
| `lex` `parse` `desugar` `scope` `check` `lower` | a dump this harness designed: tokens, CST, AST, IR text | two independent code generators produce programs that agree on the phase's observable behaviour, for the instruction mix that phase uses. Blind to anything the dump does not print. |
| `text` `pingpong` | Codex source re-emitted by the compiler's own `CodexEmitter` | as above, plus `pingpong` alone carries a self-consistency claim: emitting from stage 1's text must reproduce it. That is a different question from arm agreement and is checked separately by `pingpong_fixed_point`. |
| `lir` | machine-code bytes from hand-built `LirFunc` data, no front end involved | the instruction selector agrees. The bytes are compared as decimal text and never executed. |
| `fib` | the IR, in IRTextEmitter's grammar, for a front end run end to end | as the dump rungs above: a designed dump, not an image. Listed apart from them only because its subject reaches further. |
| `fibx` `scale` `whole` `clamp` | the **actual CDX image the compiler emits** -- header, content, tail, symbol map | the strongest rungs, and the reason the ladder exists: the thing under comparison is now the x86 back end's real output rather than a dump of intermediate state. `whole` does it for every chapter but the driver. |

**Fourteen rungs are not fourteen independent constructions.** Three pairs
share a bundled unit and differ only in the harness riding in it:

| unit | rungs | differ by |
|---|---|---|
| ~1.03 MB | `text` `pingpong` | 19 bytes: the harness and its stubs |
| ~2.44 MB | `fibx` `scale` | the subject in the harness's text literal |
| ~2.58 MB | `whole` `clamp` | the subject in the harness's text literal |

That is not a flaw and it is not padding. Each pair asks the same compiler a
different question -- `pingpong` feeds it its own output, `scale` gives it a
real chapter instead of a toy, `clamp` gives it a subject that fails to compile
-- and those are the questions worth asking. But a reader counting should
know which number is which: **fourteen rungs, twelve compiles**
(`LADDER_UNITS`; the merged pairs cost one compile each), **eleven distinct
bundle constructions** (text and pingpong are separate compiles of one
shared bundle recipe, differing only in the 19-byte harness).

**The machinery now says so too, for the two expensive pairs.** Written and
**verified 2026-08-18**: a full re-bank under the merged units reproduced all
fourteen truths byte-identically, and the sweep after it was 14 of 14 on both
arms. The merged sweep costs well under half of what fourteen compiles did;
the current figures live in "Running it". `fibx`/`scale` and `whole`/`clamp`
are one harness each, running the pipeline over a list of subjects and marking
each dump, so each pair costs one compile instead of two. `oracle_lib.sh`
carries `LADDER_UNITS` (twelve) beside `LADDER_RUNGS` (fourteen) and checks
them against each other; `split_truth.py` cuts each run back into the per-rung
`.truth` and `.zigout` files everything downstream already reads.

That measurement has now been made twice: once for the merge itself, and again
after the emitter's arena and match-arm pin landed. Fourteen truths, byte-identical
both times. `text` and `pingpong` remain two units and always will -- pingpong's
subject is built from text's OUTPUT, so it cannot exist until the other has run.

**u45 -> u46 was byte-identical on every rung; u46 -> u47 is the first
Update that moved the measurement.** Nine of fourteen rungs identical, five
moved with their upstream causes: `parse` (44 new lexer tokens), `clamp`
(6 new IR defs), and `fibx`/`scale`/`whole` (the issue-70 ATA guards and a
burst helper, ~360 bytes each). Both kinds of answer are the point -- an
Update that changes nothing we measure and an Update whose diff itemises
exactly what it changed are each something a single sweep cannot say. The
same bank-to-bank diff is what proves a bundle edit image-preserving before
it is trusted; the ones already proven are recorded in `JUSTIFICATIONS.md`.

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
  compiler's own serial-ring reader costs one. fibx's IR is 13.1 MB on the
  u47 seed, so it has no choice.

`arm_for` in `ast/oracle_lib.sh` decides, because which transport is needed is a
property of the IR, and the IR belongs to the unit: the `fibx` and `whole` units
take the ring, and the four rungs they carry ride in with them.

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
run their zig with `zig run` (`ast/oracle_lib.sh`, `zig_verdict`), and zig 0.16
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
all match the symbol map, and `pingpong.truth` byte-identical to
`text.truth`). Two arms drifting into the same nonsense would have to keep a
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
of the seed's own back end across fourteen subjects, up to and including the
entire compiler minus its driver -- and for four of those, the complete CDX
image the compiler emits.

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
working `ast/*.truth` and `ast/*.ir` files the arms consume are not, so its
first act is `ast/rebank_all.sh` -- `allcycles.sh` alone has nothing to
diff against.

**From the host:** `qemu-system-x86_64` (6.2.0), `python3` (3.10.12),
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

## Running it

Paths below are relative to this repository; the bundlers and rung scripts
live in `ast/`, the transports and VM helpers at the top level. Everything wants
`CODEX_ROOT` in the environment:

    export CODEX_ROOT=/path/to/your/Codex/clone

    ast/truthcycle.sh         # one rung's truth arm: bundle, compile, bank
    ast/lexcycle.sh           # the same rung through the plug, diffed
    ast/allcycles.sh          # rebuild both plugs, sweep all fourteen
    ast/rebank_all.sh         # re-bank every truth arm, then sweep

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
  wrapper exists (see the two-arms section: the set has holes, and `scale` and
  `clamp` run the unit they ride in).
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
- `ring_compile.py` -- compile through the seed under QEMU via the codex-vm ring
  contract. This is the compile path, not the transport of the same name. Blobs
  larger than the 1 MB ring stream through it: the host refills behind the
  guest's read cursor over the gdbstub. `ring_refill_test.sh` is that path's
  oracle.
- `codex_vm.py` -- launch/READY/run helpers shared by the above.
- `droplet_*.sh` and `sweep_*.sh` -- the remote QEMU venue and the
  two-venue sweep (prep once, fail-fast canary, full-coverage long).
  Read their headers; "The droplet venue" below has the principles.

Costs -- this section is the one home for timing figures; re-measure and
update them here at every rebank. Measured clean 2026-08-20 (u48, with
per-rung `rung_stamp` timestamps in the logs):

- **`rebank_all.sh` end to end is 87 minutes** -- 50 for the twelve truth
  arms, 37 for the trailing all-local sweep (plug rebuilds included). The
  ten cheap units record in one to five minutes each; `fibx` and `whole`
  are 11-13 minutes apiece on each side and dominate everything.
- **The two-venue sweep**: `sweep_canary.sh` is 87 seconds (lex 10s,
  parse 29s, desugar 46s); `sweep_long.sh` over all fourteen rungs is
  about 55 minutes healthy (scope 64s, check 198s, lower 229s, text
  241s, pingpong 248s with the fixed point, lir 11s, fib ~30s, fibx
  11.5m, whole 11.8m). The canary/long split stays lex+parse+desugar:
  adding scope would push the canary past 2.5 minutes for little
  coverage -- decided from these stamps, not intuition.
- **The census re-pin** (`native_build.sh && corpus_run.py --changed
  --bank`) is about an hour when nothing carries, which is every
  Update re-pin: the natives change, so every emitted zig moves.

Run long jobs in the background and watch for the markers above.
(The pre-merge ladder, four big compiles instead of two, cost 2h21m --
the shape of the saving, not a current figure.)

## The droplet venue

QEMU work can run on a second host: a small cloud box (the same one
that serves a live website, which is why the rails below exist)
provisioned as an appliance and driven over synchronous ssh. The
scripts are the documentation here -- `droplet_*.sh` and `sweep_*.sh`
at the repo root carry their contracts in their headers, and
enumerating them in prose only invites drift. Design and the founding
measurements: JUSTIFICATIONS.md ("Droplet compile venue") and essays
random893/random894; adopted 2026-08-20.

**The principles, which are stabler than the file list:**

- **The appliance holds no logic.** Verbatim driver scripts, kernels,
  and the seed are PUSHED artifacts; no checkout, no zig, no daemon,
  no listening port, no state. What can go stale is exactly the pushed
  artifacts, so every one is guarded twice: sha-verified at push time,
  and re-verified against the checkout's copy ON EVERY JOB, refusing
  before QEMU boots -- the per-use discipline `plug_run_ring.py`
  applies to a stale ringplug, generalized. Staleness checks that need
  the checkout (re-bundling, source shas) run laptop-side before
  anything is pushed.
- **Synchronous ssh is the whole protocol.** One held ssh per job: log
  lines stream back live, the exit code propagates, artifacts scp back
  after. No polling, no queue, no service. If the droplet is
  unreachable, everything still runs locally (`ast/allcycles.sh` is
  the all-local sweep) and nothing here is on the critical path.

**TCG on purpose, not KVM.** Measured on the warmup blob: droplet TCG
26s, laptop TCG 31s, droplet KVM 43s. This guest streams output
through port I/O and polls the serial status register; under KVM every
port access is a vmexit, under TCG a cheap helper call. The wrapper
pins TCG and the numbers live in JUSTIFICATIONS.md -- re-measure there
before believing anything else about relative speed.

**The rails, because a live site shares the box:** `nice -n 15` on the
QEMU process, `flock -n` so a second job refuses loudly instead of
queueing silently, and the guest sized at 1300 MB (the box has 2 GB
and no swap; the big 2.5 MB bundle compile is UNMEASURED there --
measure before relying on it). Output is byte-identical to a local
compile of the same blob; that was the acceptance test.

**Every droplet arm rides the ring.** The TCP plug's boot-time heap
reservation needs >= 1600 MB of guest RAM -- measured 2026-08-20:
connects at 1600, exits SILENTLY at 1500 and below (nothing on serial,
a clean debug-port exit that reads like a qemu failure) -- so it cannot
boot inside the 1300 MB cap, and `droplet_transpile.sh` refuses the tcp
argument with that reason rather than reproducing the silent exit. The
Codex network stack keeps its oracle coverage in the local venues
(`cycle.sh` warmups and `ast/allcycles.sh` both push IR over TCP), and
the two transports were measured byte-identical on the same IR (laptop
tcp vs droplet ring, lex, 2026-08-20).

What the droplet buys is not mainly the 5s: it is that the
one-compute-job rule becomes per-host. The laptop can bundle, build
zig and diff while the droplet grinds a compile -- two QEMU-scale jobs
that used to serialize on one 3.8 GB machine now overlap across two.

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
4. **One compute job per host.** QEMU, a sweep, a census run, a native
   build: one at a time on any given machine. The droplet enforces it
   with `flock -n`; on the laptop every compute entry point takes
   `take_compute_lock` (in `ast/oracle_lib.sh`, with `compute_lock.py`
   as the Python half), which also refuses on the evidence of a running
   job that did not take it. Two 3 GB guests on the 3.8 GB laptop do not fail -- they
   thrash at 2% CPU each, which reads as mysterious slowness rather
   than as the refused launch it should have been (2026-08-20, a sweep
   and a native build stacked; the sweep's artifacts were garbage).
5. **Never lift the 2.5 GB address-space cap on `zig_verdict`'s `zig run`.**
   An emitted binary from any emitter that predates the arena balloons past
   3 GB and can livelock the whole WSL VM; under the cap that is a recorded
   rung failure instead. With the arena (upstream since `a061c173`) the big
   rungs run in about 240 MB, so the cap never bites a healthy arm.
   Measurements: `JUSTIFICATIONS.md`.

## The checkout: cloning and branching

How the Codex clone `CODEX_ROOT` points at is managed. This lived in nobody's
head for a while and the head it lived in got confused, so, written down:

**Two remotes, with different jobs.** `upstream` is `damiant3/NewRepository`
and is read-only in practice: the mirror is downstream of the author's
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

Update 47's actual length is SEVEN, and honesty about that beats the
tidy story an earlier draft told here: the arena (PR 71, landed at
`a061c173`), then the PR 75 chain (CCE tiers, char-to-text, the
finding-16 fix -- absorbed in Update 48), then the PR 76 chain (wrap
arithmetic, builtin yield, char-CCE -- filed). Every one is landed or
filed, but the later six include correctness fixes, so the u47 zig arms
measured the pin, not the verbatim release -- exactly the deviation
step 4's working rule exists to prevent. The u48 pin starts at zero and
stays there (agreed, Steve + Claude, 2026-08-20: the census re-pins
verbatim too -- the noisy bank is the honest bank).

**The working tree parks on the pin for the entire banking cycle.**
`CODEX_ROOT` names a working tree, not a commit: a `git checkout` there
mid-sweep rebuilds the plug from whatever the tree now holds, and that cost a
90-minute sweep once (2026-08-18). The fingerprint guard in `oracle_lib.sh`
now refuses to run arms when `ZigEmitter.codex` or `ZigPlug.codex` moved
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
`git remote add upstream git@github.com:damiant3/NewRepository.git`, then
`git switch u<NN>-rebank` (the pin is on the fork). Git carries everything
else: point `CODEX_ROOT` at the new clone, let `check_paths.py` prove the
wiring in five seconds, and the first `cycle.sh` (or the sweep, which runs
it) regenerates the untracked plug artifacts from the seed.

## Processing a new Update

What happens when the depot publishes a release, in order. Each step exists
because skipping it has already cost something once; the citations are to the
Update where it did.

### 1. Read before running anything

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
  `codex/plugs/zig/` (the emitter is fleet-maintained now, see step 4) and
  the net stack if the TCP arm matters to the question at hand.
- **The seed hashes.** The release note names the public seed; depot `main`
  may already be several seeds past it. The bank is a claim about the
  released seed, so everything below uses the release commit, not main.
  A seed change also stales the droplet appliance's pushed copy: re-run
  `droplet_vm_setup.sh` when the checkout re-pins (it re-pushes and
  sha-verifies; a droplet compile against last Update's seed would bank
  truth nobody named, the exact failure `CODEX_ROOT`'s refusal exists
  to prevent, one host over).

### 2. Probe the contract before committing hours to it

Both seeds are one `git show <commit>:seed/Codex.cdx` away, and
`ring_compile.compile_ring(..., seed=...)` accepts an explicit seed, so the
cheap experiment needs no checkout CHANGE -- `CODEX_ROOT` must still name a
valid checkout for the imports to resolve, but it can stay wherever it is.
The seed parameter is not reachable from `ring_compile.py`'s command line;
call the function. Reuse a small blob from an earlier run's working tree --
blobs are gitignored, so a fresh tree has none until `ast/arithcycle.sh`
(which writes `ast/arith-cdx.blob` in its first seconds) or any rung has
run once -- and run the pair:

    git -C $CODEX_ROOT show <old>:seed/Codex.cdx > /tmp/seed-old.cdx
    git -C $CODEX_ROOT show <new>:seed/Codex.cdx > /tmp/seed-new.cdx
    python3 -c "import ring_compile as r; \
      r.compile_ring('ast/arith-cdx.blob', '/tmp/probe.cdx', seed='/tmp/seed-new.cdx')"

and the same line with the old seed for the baseline. This confirms the new
seed boots under our QEMU flags, takes the ring preload, and produces output
our reader parses. Five seconds per compile. If the release claims
throughput work, add one mid-size unit for a timing point (`check` at 4.8 MB
of IR showed Update 47's FIFO-burst output as about 10 percent of wall
time). If output differs in size for the same input, that is the first look
at what the Update changed in the image -- note it, it previews the bank
diff.

### 3. Prerequisites for the rebank itself

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
  minutes). Know what is actually guarded: the TCP plug's fingerprint covers
  ONLY `ZigEmitter.codex` and `ZigPlug.codex` (`plug_provenance` in
  `oracle_lib.sh`); the ring plug's guard is stronger -- `ringplug_build.sh`
  records the bundle sha in `ast/ringplug.cdx.fp` and `plug_run_ring.py`
  re-bundles and refuses a mismatch before booting. Banking refuses a moved
  seed or moved harness content after the fact (the `truth_prov` sidecars),
  but nothing detects the seed moving MID-run
  (`seed_identity.require_match` exists for exactly that and nothing calls
  it yet). Everything beyond that is operator discipline:
  do not touch the clone until the run finishes or is killed. The clone is
  not PR scratch space during a sweep -- build PRs in a worktree elsewhere.
- **`seed_identity.py` says the right thing** (seed hash, Update number,
  `truth/uNN` target) and **`check_paths.py` passes.** Five seconds, versus
  discovering a broken path an hour into the truth arms.
- **One compute job.** The machine holds one QEMU comfortably; the sweep
  beside anything else slows both and has livelocked WSL outright when
  memory ran short. Nothing else runs until the bank is taken.

### 4. Decide what the zig arms measure

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
because a wrong answer IS the measurement. Worked example and numbers: the
arena entry in `JUSTIFICATIONS.md`.

### 5. Run, bank, retire

- **Warmups first**: `./cycle.sh hello recurse fib` checks the plug end to
  end on the new checkout in minutes. `rebank_all.sh` does not run them --
  its first plug exercise is the sweep at the END, hours in, so a gross
  plug-side breakage found there was findable at the start.
- Then the rebank, detached so a hung VM cannot take the verdicts with it
  (the script itself neither detaches nor logs):

      mkdir -p logs
      setsid nohup ast/rebank_all.sh > logs/rebank-uNN.log 2>&1 < /dev/null &

  Truth arms run cheapest-first and stop on the first failure; a CDX9002 on
  a big rung usually means the deck scale -- the seed's compile-time memory
  reservation -- needs raising (the `decks=` entries in `oracle_lib.sh`'s
  `mode_flags`), not that something broke.
- **Bank only when the zig arms are green too** (`bank_truth.py`).
  Terminology, because a crashed session once nearly tagged over its
  absence: the rebank RECORDS working truths (`ast/<m>.truth`; its
  "banked" log lines mean this) -- the BANK is `truth/uNN/`, written
  only by an explicit `bank_truth.py`, which `rebank_all.sh` never
  runs. "All banked" in a rebank log does not mean the bank exists.
  `--force` REPLACES the destination with the ready subset; after an
  interrupted rebank, re-run the missing units instead. It
  refuses mixed-harness sets on its own; the green-arms rule is ours, from
  the merge, and it exists because a bank taken over red arms freezes a
  question mid-answer.
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
  (`uNN-14of14`), push.

## Consumers of what the ladder emits

These are run by hand, not by `allcycles.sh`; the sweep's cost covers the
fourteen rungs only.

The rungs prove the plug emits the same bytes. These ask whether the bytes mean
anything.

The `f` numbers are milestones of the fib ladder: F1 was fib through the front
end, F2 was fib through the x86 back end (the `fibx` rung), F3 runs the emitted
code, F4 boots the emitted binary.

- `ast/f3_run.zig` -- carves a function out of an emitted CDX, drops it in RWX
  memory and calls it. `fib(30) = 832040`, from both the truth dump and the zig
  dump. Works because the emitted code uses the System V ABI and buffer-relative
  call displacements.
- `ast/f4_boot.py` -- reassembles the dump into a real CDX the way
  `emit-binary-tail` does (header, content, tail), boots it, and checks it prints
  what its subject says. Six binaries: fibx, scale and whole, from truth and from
  zig. This is the one check that does not depend on the two arms sharing a
  mistake.
- `native_build.sh` -- builds `codexir` (.codex -> .ir) and `zigemit`
  (.ir -> .zig), the two tools that take QEMU out of the pipeline entirely.
  `zigemit` is not a second implementation: it is the same `ZigEmitter`, bundled
  with a four-line body that reads stdin and writes STDERR (print-text is
  std.debug.print in the emitted runtime -- a wart, and why every caller
  uses `2>` redirects) instead of the ring plug's serial framing, then
  transpiled and built like anything else here.

## zigc: the compiler as an ordinary process

`ast/ZigcHarness.codex` is the `whole` rung's chapter set with a real I/O
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
`gen_scale_harness.py` and `gen_clamp_harness.py`, which own only their
unit's second subject; the harness itself comes from the fibx and whole
generators. `ast/emit_harness.py` holds the compile pipeline once --
`frontend_source` (source text to a lowered IR) and `pipeline_source`
(that plus the x86 emission) -- so the four generators that run it
(`gen_fibx` and `gen_whole`, whose units also carry `scale` and `clamp`;
`gen_zigc`; `gen_codexir`) cannot drift from each other. Four more
generators import only its shared tables (`DECK_PROLOGUE`,
`RESOLVED_TABLES`).

The bundlers are PowerShell (`ast/bundle_<m>.ps1`), because they call the
repository's own `plug-build-lib.ps1` to resolve chapter cites. That is why pwsh
is a requirement here.

Everything generated is ignored and regenerates from a script beside it. The
scripts are the record.

## Open questions

- The `zigc` transcript above elides its middle step ("...then compile that
  subject to IR with the seed and push it through the plug"). `native_build.sh`
  does that for `codexir` and `zigemit`; `zigc` has no such script, so the
  transcript is not reproducible as written.
- ~~`clamp`'s paragraph points at finding 11~~ Resolved. Finding 11 was
  withdrawn as filed: the cause was ours, a harness that skipped the driver's
  RESOLVE phase. What survived it -- `emit-record` laying a record out by a
  rule no reader uses when the type is unresolved -- is closed in Update 46.
  What `clamp` actually earned is separate and larger: it is the rung that
  caught the deck intrinsic being off in every bundle we had ever built.
- **Could the seed be taken out of the loop entirely, making this a complete
  DDC witness?** Today both arms pass through the seed, because it is the seed
  that compiles a subject down to the IR the plug consumes. `codexir` and
  `zigemit` are the beginning of an answer -- a native compiler emitting IR and
  a native plug consuming it -- but nothing yet establishes that a
  seed-independent chain produces the same IR, which is the claim that would
  matter.
