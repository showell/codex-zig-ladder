# What is next, in order

Kept here rather than in anybody's head or memory file, because there are now
several threads and they were drifting apart. If a memory or an essay disagrees
with this file, this file wins. Dated entries so staleness is visible.

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

`codex/test/` in the depot holds **1,541 programs, 1,304 with hand-verified
`.expected` output**, plus 190 `.failing` sidecars carrying expected CDX codes
for the error path. An oracle per program, written by someone with no knowledge
of this plug, which is the property our own probes cannot have.

Staged so the cheap half comes first:

1. transpile all 1,541 and **histogram the `@compileError` markers**. Native,
   minutes, no zig compilation. Output is a coverage census of the emitter
   ranked by how often each missing arm actually bites.
2. compile and run the subset that transpiles clean, diffing against
   `.expected`. That is the conformance gate.
3. the 190 `.failing` cases are a second, different question: does the plug
   reproduce a refusal.

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

- **Match guards dropped.** DEMONSTRATED end to end 2026-08-18:
  `findings/probe-match-guard.codex` prints `guard-taken 1` under the plug where
  the language says `0`, because `IRBranch.guard` is never read. Owed: confirm
  the bare-metal side with the seed, then file.
- **Char literals** are CCE codes while every other Char is a codepoint, so
  `char-at s i == 'x'` is always false and compiles clean.
- **`IrApproxEq` emits `==`**, dropping a 4-ULP tolerance.
- ~~`__linked-list-empty` drops its argument~~ FIXED (`cx_ll_empty_n`).

## 3. Upstream the two emitter fixes

`zig-pin-arms` and `cx_ll_empty_n`, once the regression sweep is green. The pin
fires on about 1% of switches (7 of 629 in `check`, 8 of 805 in `text`) with
zero output change across ten programs. Small PR, same shape as PR 71.

## 4. The heap unification

`findings/zig-heap-unification.md`. Closes `__heap-restore` being a no-op on the
zig arm, which costs sum-over-definitions instead of max-over-definitions during
emission. PR 71's arena is the interim.

## 5. README debts

Does not say the merge is verified, does not carry the SHA-256 self-check
result, does not mention the arena.

## 6. `codexir` core-dumps on a real test program

Found in the pilot. A hosted-compiler crash is its own finding; identify the
file and reduce it.

## 7. Diagnostics as a banked set

Diffed like a truth file, retiring the CDX6020 and CDX2064 count pins that move
whenever the unit list changes rather than when the source does.

## 8. Update 47, when it ships

Rebank as `u47`. Read `codex_vm.py` against Fable's QEMU throughput work first,
since we re-implement the host contracts rather than inherit them.

---

## Filed and waiting

- **PR 69** the `$present` hoist (bundling)
- **PR 71** the arena (12.5x memory, byte-identical)
- **Issue 70** CDX2064, the ATA wait loop patching six bytes late. Damian is
  acting on it.
