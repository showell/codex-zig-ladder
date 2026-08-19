# What is next, in order

Kept here rather than in anybody's head or memory file, because there are now
several threads and they were drifting apart. If a memory or an essay disagrees
with this file, this file wins. Dated entries so staleness is visible. Done
items leave the list; git history is their record.

## The native loop, which changes what is cheap

Built by `native_build.sh`:

    native/codexir   .codex -> IR      ~0.1s
    native/zigemit   IR     -> .zig    ~0.05s

No QEMU in either. A Codex source to a running zig program is about a third of
a second. Rebuild both after any emitter change; that script is also the only
thing that compiles the plug **through itself**, which is how the
`comptime_int` defect surfaced.

The ladder is still the ladder: expensive, per-Update, and it answers "does the
whole compiler survive transpilation". Everything below is the cheap loop.

---

## 1. Corpus conformance

`codex/test/` holds 553 programs at the top level, most beside a hand-verified
`.expected` file: an oracle per program, written by someone with no knowledge
of this plug, which is the property our own probes cannot have. **The design
is `corpus/README.md`** (banked census diffed like a truth file, changed-only
reruns keyed on emitted-zig hashes, a set-cover sentinel gate, full census
per-Update only); its sequencing starts with item 4 below, which poisons the
denominator until fixed.

The known gap family is coherent: `poke-byte`, `peek/poke-16/32`, `bit-not` --
the memory-access builtins; implementing the family unblocks a large slice at
once. Explore before asking Damian for anything; if it pays off, the ask is
"would you want this as a signal on your side", not "persist your IR".

## 2. Two emitter defects: finish the probes, file

- **Char literals are CCE codes while every other Char is a codepoint**, so
  `char-at s i == 'x'` is always false and compiles clean. Zig arm measured
  (`findings/probe-char-literal.codex`: found-x 0 where the language says 1,
  controls clean); owed: the bare-metal half, then file.
- **`IrApproxEq` emits `==`**, dropping the 4-ULP tolerance. Probe written
  (`findings/probe-approx-eq.codex`); its two blockers
  (`bits-to-real-approx` emitter, `text-to-double-bits` prelude) landed
  2026-08-19 with the multi-byte CCE work. Run the probe both arms, file.
- **The CCE alias limit of Char-as-codepoint (2026-08-19, DISCUSS before
  acting).** CCE has aliases: é is tier-0 code 97 AND tier-1 code 233, and
  the canonical encoder always answers 97. Bare metal never notices --
  char-code / code-to-char are identity there, and byte-wise text rebuilds
  (the compiler's own ir-quote) pass frame bytes through untouched. The
  zig plug's codepoint Char makes those ops a code->cp->code detour that
  canonicalises, so a 3-byte frame OPENER whose byte value collides with a
  tier-0 codepoint (224-226, 228, 231-235, 237 -- ten of sixteen openers)
  comes back as the wrong byte: tier-2 text through ir-quote corrupts,
  found when the multi-byte smoke printed a stray é from an emoji frame.
  char-to-text is now single-byte again (bare metal's mov-store-byte
  contract), which restores identity everywhere else. The structural fix
  is Char = CCE code, the C# model, same tension as the char-literal
  finding above -- an emitter-wide representation change, Steve's call.
- **Real-literal candidates in the other plugs, found by cross-reading
  while fixing ours (2026-08-19, unverified):** the JavaScript emitter's
  IrNumLit is `Number(BigInt.asIntN(64, bits))` -- the bits as a NUMBER,
  not a bitcast, so any real literal is off by ~18 orders of magnitude
  (its own text-to-double-bits arm does the DataView reinterpret
  correctly, one line up). Subtler: JS parseFloat and C# double.Parse are
  correctly-rounded parsers where bare metal's __text_to_double is
  one-division-after-integer-accumulate, so long-fraction literals can
  carry different bits per plug. Probe before filing either.

## 3. The heap unification

`findings/zig-heap-unification.md`. Closes `__heap-restore` being a no-op on
the zig arm, which costs sum-over-definitions instead of max-over-definitions
during emission; the arena is the interim. Pre-approved in shape by Damian
("send it as its own PR when the hunt settles"), as are the `cx_show_int`
double allocation and the per-instruction throwaway list.

## 4. Multi-byte CCE in the zig prelude

`cx_cp_to_cce` panics on any codepoint outside the 97-entry single-byte table
and `cx_cce_to_utf8` refuses bytes >= 128 symmetrically. The ladder rungs
never hit it (subjects arrive as compiled-in CCE literals); hosted `codexir`
converts raw stdin then lexes, so this took the hosted-vs-seed IR comparison
0 for 11. The honest fix is multi-byte encode and decode in the prelude; it
unblocks the seed-independence experiment and plausibly some census units.

## 5. Census fallout (numbers from the 2026-08-19 run, `corpus/run.json`)

278 transpile-clean units -> 117 match / 95 refused / 33 differ (overcounted
by the capture-byte artifact, since fixed -- deflates on the next run) /
5 crashed.

- **Two refusal classes are one fix each:** bool passed where i64 is
  expected, and zig 0.16's Thread `startFn` signature (prelude-level).
  Together they cover most of the 95.
- **Five runtime crashes on integer overflow** (bloom-spread,
  consistent-hash-balance, ...) -- candidate findings, since bare metal
  evidently does not trap there. Wants the probe treatment.

## 6. `codexir` core-dumps on a real test program

Two crashes in the 40-program pilot; `corpus_run.py --limit 40` reproduces
them and `corpus/transpile.json` names them (stage `codexir`). A
hosted-compiler crash is its own finding; identify and reduce.

## 7. ring_compile busy-loops when its QEMU dies

The read/refill loop needs a child-liveness check that turns a dead guest
into a loud failure -- today a defunct QEMU leaves ring_compile spinning at
100% CPU with a frozen log until killed by hand. Same honesty class as the
memory caps: an unattended runner must never convert a crash into a hang.
Until fixed, detection is a stale log mtime beside a hot python process.

## 8. Diagnostics as a banked set

Diffed like a truth file, retiring the CDX6020-style count pins that move
whenever the unit list changes rather than when the source does.

## 9. Parked: the notebook / Prism angle

Not work, a bookmark, deliberately last. A Python-hosted notebook showing how
Codex source becomes assembly, stage by stage, is a weekend-sized
demonstrator of Damian's dusty **Prism** design
(`apps/prism/design/Active/PrismDesign.md`: source in the center, every
plug's output arrayed around it, the compiler as the web server). The native
loop and `zigc` already are its core machinery in cheap form; the 50-sidecar
fan-out is the part that stays dusty. If picked up, re-read the design
against what exists now and ask Damian what he would want first.

---

## Filed and waiting

- **PR 73** (2026-08-19): plain-switch literal pin + `__linked-list-empty`
  consumes its size hint, via upstream's own functions.
- **PR 74** (2026-08-19): batch compiler starts on Linux pwsh
  (`-WindowStyle` only on Windows), generator + emitted script.

---

## How to read this list, given how the work actually goes

Two modes alternate: at the keyboard, where decisions and code happen, and
away from the machine, where something long should be running unattended.
**Keyboard work** is the probes and emitter changes (items 2, 3, 4), the
tooling fixes (7, 8), and landing what reviews come back on. **Away work** is
running what those produce: `tonight.sh`, the census stages of item 1,
`ast/allcycles.sh` after any emitter change.

The rule that makes both work: **one compute job at a time.** The machine has
about 3 GB usable and QEMU takes most of it. Anything fired from the keyboard
waits for what is already running, the way `tonight.sh` does.
