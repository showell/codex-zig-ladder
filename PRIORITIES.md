# What is next, in order

Kept here rather than in anybody's head or memory file, because there are now
several threads and they were drifting apart. If a memory or an essay disagrees
with this file, this file wins. Dated entries so staleness is visible.

**Clock on the list, 2026-08-19:** Update 47 is banked (item 8 done). The
next seed churn restarts that clock; item 3's prepared PR and item 4 are the
unlanded emitter work that rots fastest when it does.

## The native loop, which changes what is cheap

Built 2026-08-18 by `native_build.sh`:

    native/codexir   .codex -> IR      ~0.1s
    native/zigemit   IR     -> .zig    ~0.05s

No QEMU in either. A Codex source to a running zig program is about a third of a
second. Rebuild both after any emitter change; that script is also the only
thing that compiles the plug **through itself**, which is how the `comptime_int`
defect surfaced.

The ladder is still the ladder: expensive, per-Update, and it answers "does the
whole compiler survive transpilation". Everything below is the cheap loop.

---

## 1. Corpus conformance (2026-08-18)

`codex/test/` holds **553 programs at the top level**, which is what the runner
globs, most beside a hand-verified `.expected` file. (1,541 and 190 are the
RECURSIVE counts including subdirectories, which nothing walks today; the
earlier version of this file quoted those and overstated the reach 13x.) An oracle per program, written by someone with no knowledge
of this plug, which is the property our own probes cannot have.

Staged so the cheap half comes first:

1. transpile all 553 and **histogram the `@compileError` markers**. Native,
   minutes, no zig compilation. Output is a coverage census of the emitter
   ranked by how often each missing arm actually bites.
2. compile and run the subset that transpiles clean, diffing against
   `.expected`. That is the conformance gate.
3. the `.failing` cases are a second, different question: does the plug
   reproduce a refusal. 11 at the top level, 190 recursively; no code path yet.

**Cites are resolved now** (`cite_resolve.py`, 2026-08-18), so the whole
corpus is in scope rather than the 120 self-contained programs. That mattered:
the first histogram was 64 markers and not one was an emitter gap -- every test
is a driver whose function lives in a cited chapter, and an unresolved call
looks exactly like a missing arm.

Pilot on 40 resolved programs: **24 clean, 14 with markers, 2 crashed
codexir**. The gaps are one coherent family -- `poke-byte`, `peek-32`,
`peek-16`, `poke-16`, `poke-32`, `bit-not` -- the memory-access builtins.
Implementing that family unblocks a large slice in one go. `poke-byte` is
already a known hole: `emit_harness.py` steps around it in a comment rather
than citing the chapter that reaches it.

Explore this before asking Damian for anything. If it pays off, the ask is not
"persist your IR" but "would you want this as a signal on your side".

## 2. The four emitter defects: probe, then file

- ~~Match guards dropped~~ **FIXED UPSTREAM at a061c173** (2026-08-19, issue
  72 closed): a guarded match emits a labeled if-chain, an unguarded one
  keeps the switch, our probe shape is now guard rows in
  plug-oracle-arith.codex (49/49). The same rows graded the other plugs:
  python/wasm answer wrong values, csharp fails to build, typescript drops
  guards AND miscloses a variant type -- registered as plugs-backlog 1.46,
  the plugs lane's problem now, not ours.
- **Char literals** are CCE codes while every other Char is a codepoint, so
  `char-at s i == 'x'` is always false and compiles clean. **Zig arm
  MEASURED 2026-08-19** through the native loop
  (`findings/probe-char-literal.codex`): found-x 0 where the language says
  1, controls clean. Owed: the bare-metal half once QEMU frees, then file.
- **`IrApproxEq` emits `==`**, dropping a 4-ULP tolerance. Probe written
  (`findings/probe-approx-eq.codex`, 0.1 + 0.2 ~ 0.3, one ULP, with a
  constant-folding caution); its zig arm waits on a SEED compile because
  writing it found TWO MORE gaps: `bits-to-real-approx` has no emitter
  (the f32 probe, `findings/probe-real-approx-bits.codex`, refuses with 3
  markers) and `text-to-double-bits` is an unimplemented prelude marker, so
  native codexir aborts on ANY real literal.
- ~~`__linked-list-empty` drops its argument~~ FIXED (`cx_ll_empty_n`).

## 3. ~~Upstream the two emitter fixes~~ SENT 2026-08-19 as PR 73

Two lines reusing upstream's own functions: their `zig-pin-lit-arms` applied
to the plain switch path (they pin only the guarded chain), and
`__linked-list-empty` routed through their `cx_ll_with_capacity`. Verified
before sending: plug compiled through the a061c173 seed, warmup oracles
3/3 byte-identical.

## 4. The heap unification

`findings/zig-heap-unification.md`. Closes `__heap-restore` being a no-op on the
zig arm, which costs sum-over-definitions instead of max-over-definitions during
emission. PR 71's arena is the interim.

## 5. README debts -- DONE 2026-08-19

The SHA-256 self-check is in the epistemics section, the arena is operating
rule 4, and the whole file was restructured to the cold sequence review's
table of contents the same day.

## 6. `codexir` core-dumps on a real test program

Two crashes in the 40-program resolved pilot, so `corpus_run.py --limit 40`
reproduces them and `corpus/transpile.json` names them (stage `codexir`). A
hosted-compiler crash is its own finding; identify and reduce.

## 6b. ring_compile busy-loops when its QEMU dies (2026-08-19)

Observed once, cost 23 silent minutes of an unattended run: during the u47
truth-arm rerun, lex's IR-CCE compile lost its QEMU (child went defunct)
and `ring_compile.py` spun at 100% CPU without noticing, log frozen, until
killed by hand. The read/refill loop needs a child-liveness check that
turns a dead guest into a loud failure. Same honesty class as the caps:
an unattended runner must never convert a crash into a hang.

## 7. Diagnostics as a banked set

Diffed like a truth file, retiring the CDX6020 and CDX2064 count pins that move
whenever the unit list changes rather than when the source does.

## 8. Update 47 -- DONE 2026-08-19: banked, 14/14 both arms

`truth/u47` is banked (seed 90646EEB), the sweep was 14/14 ORACLE PASS with
the arena on the pin, and the u46 diff is the first Update to move what we
measure: 9/14 byte-identical, parse and clamp moving with their upstream
subjects, fibx/scale/whole growing by the ATA-guard/burst-helper bytes.
u47's QEMU bulk-output path needed no codex_vm.py change and is ~10% faster
on big-unit output. What remains from this entry is item 3's prepared PR and
the heap unification (item 4).

## 9. tonight.sh's first full run: the fallout (2026-08-19, random883)

The run finished in 13 minutes; census 278 units -> 117 match / 95 refused /
33 differ / 28 no-expected / 5 crashed (`corpus/run.json`). Issue 72 filed
from step 1's bare-metal confirmation. What it left behind, cheapest first:

1. ~~The `\x01` expected-file artifact~~ DONE 2026-08-19: it is a
   capture-channel byte (with CRLF as its sibling), and corpus_run now
   normalizes both the way the depot's own adjudicator strips CRs. The
   differ column deflates to its honest value on the next run.
2. **Multi-byte CCE in the zig prelude.** Step 3 (hosted codexir vs seed IR)
   went 0 for 11 on one cause: decode-escapes -> cx_char_to_text ->
   cx_cp_to_cce panics on any codepoint outside the 97-entry single-byte
   table, and cx_cce_to_utf8 refuses bytes >= 128 symmetrically. The ladder
   rungs never hit it (subjects arrive as compiled-in CCE literals); codexir
   converts raw stdin then lexes. The honest fix is multi-byte CCE encode and
   decode in the prelude; it unblocks the seed-independence experiment and
   plausibly some census units.
3. **Two census refusal classes that are one fix each:** bool passed where
   i64 is expected (the ip-checksum-odd shape, now a large family), and
   zig 0.16's Thread `startFn` signature (prelude-level, every
   thread-spawning unit). Together they cover most of the 95 refusals.
4. **Five runtime crashes on integer overflow** (bloom-spread,
   consistent-hash-balance, ...) -- candidate findings, since bare metal
   evidently does not trap there. Wants the probe treatment.

## 10. Possible follow-up, parked: the notebook / Prism angle (2026-08-19)

Not work, a bookmark, deliberately last. The earlier riff on Python angles
for this project landed on a Python-hosted notebook that uses Codex to show
how source becomes assembly, stage by stage. Damian already designed the
maximal version: **Prism** (`apps/prism/design/Active/PrismDesign.md`,
upstream) -- Codex source in the center, every plug's output arrayed around
it, the compiler itself as the web server and the plugs as live TCP
sidecars. He calls it dusty; it predates Update 40.

Why it belongs at the end of THIS list: the zig work has been quietly
building Prism's expensive parts in cheap form. `native/codexir` and
`native/zigemit` run the front end and a plug with no VM at all (a third of
a second, no QEMU, no sidecar fleet), `zigc` is the whole compiler as an
ordinary process, and the ladder already speaks the IR wire and knows the
per-phase output modes. A notebook driving those native binaries is a
weekend-sized demonstrator of Prism's core loop; the full design's
50-sidecar fan-out is the part that stays dusty. If picked up, start by
re-reading the design against what exists now and asking Damian what he
would want first.

---

## Filed and waiting

NOTHING IS WAITING as of 2026-08-19 morning: everything filed has landed,
all at mirror commit **a061c173** (Perforce 17251-17254, **seed 800A7683** --
more churn past u47's release seed 90646EEB; a bank against 90646EEB is a
statement about the Update 47 release, a061c173 is post-release).

- ~~PR 69~~ LANDED at a061c173 (plug-build-lib.ps1 + its generator).
- ~~PR 71~~ LANDED at a061c173, re-applied by hand (their comment cut to
  three lines, house style). Measured on their side: 23 cx_gpa in the
  emitted subject. **Heap unification (item 4) is pre-approved in shape:**
  "send it as its own PR when the hunt settles and it will be reviewed on
  its own." Same invitation for cx_show_int's double allocation and the
  per-instruction throwaway list.
- ~~Issue 70~~ CLOSED by Update 47 ("ATA jcc + absent-drive guards"). Retire
  any workaround of ours and re-pin the CDX2064 population at the u47 rebank.
- ~~Issue 72~~ FIXED at a061c173 (see item 2).
- **PR 73** (2026-08-19): switch pin + ll-empty consume, item 3 above.
- **PR 74** (2026-08-19): finding 14, batch compiler -WindowStyle guard,
  generator + emitted script, regen-proven byte-for-byte.


---

## How to read this list, given how the work actually goes

Two modes alternate: at the keyboard, where decisions and code happen, and away
from the machine, where something long should be running unattended. A cold
review on 2026-08-18 found the list badly shaped for that -- roughly twenty
minutes of unattended work against hours of keyboard work -- so:

**Keyboard work** is items 3, 5, 7, writing probes, and landing emitter changes.
**Away work** is running what those produce: `tonight.sh`, `ast/allcycles.sh`
after an emitter change, and the IR-equivalence diff.

The rule that makes both work: **one compute job at a time.** The machine has
about 3 GB usable and QEMU takes most of it; a corpus pilot run beside a sweep
on 2026-08-18 was harmless but noticeably slowed the machine. Anything fired
from the keyboard waits for what is already running, the way `tonight.sh` does.
