# Rung renaming proposal (TEMPORARY — delete in the commit that executes it)

Proposed 2026-08-21 from a cold read of the harness generators, `oracle_lib.sh`,
the bundlers and the u48 bank. Nothing has been renamed. Full discussion in
`~/showell_repos/claude-steve/random909.md`.

## The scheme

> A **unit** is named for the stage its bundle reaches. A **rung** is its
> unit's name plus `_on_<subject>`, when and only when that unit carries more
> than one subject.

Two consequences worth having. The `_on_` suffix becomes the visible marker of
the unit/rung split — exactly four rungs get one, and those four are exactly
the two composite units, so the rung list shows the ladder's shape without
consulting `unit_rungs`. And subject stays out of every name where it is a
coverage knob, so raising a `SUBJECT_FILE` never invalidates a name.

## Mapping

| current | proposed rung | unit | moves? |
|---|---|---|---|
| `lex` | `lex` | `lex` | no |
| `parse` | `parse` | `parse` | no |
| `desugar` | `desugar` | `desugar` | no |
| `scope` | `scope` | `scope` | no |
| `check` | `check` | `check` | no |
| `lower` | `lower` | `lower` | no |
| `fib` | `ir_to_wire` | `ir_to_wire` | yes |
| `text` | `ir_to_codex` | `ir_to_codex` | yes |
| `pingpong` | `ir_to_codex_roundtrip` | `ir_to_codex` | yes |
| `lir` | `lir_to_x86` | `lir_to_x86` | yes |
| `fibx` | `ir_to_x86_on_fib` | `ir_to_x86` | yes |
| `scale` | `ir_to_x86_on_cce` | `ir_to_x86` | yes |
| `whole` | `passes_to_x86_on_mid` | `passes_to_x86` | yes |
| `clamp` | `passes_to_x86_on_arith` | `passes_to_x86` | yes |

**Six names do not move.** `lex parse desugar scope check lower` are already
stage names for rungs alone at their stage. Renaming them buys nothing and
costs the noisiest greps in the repo — they are also the worst whole-word
collision offenders (`text` 234 hits, `whole` 98, `fib` 91, `check` 65,
`parse` 53, mostly coincidental).

Why the eight move: `fib` is not about fib (so is `lower`, so is `text`, so is
`fibx`) — it is IRTextEmitter's serialisation. `text` names the medium, not the
emitter under test, which is `CodexEmitter` producing Codex source. `pingpong`'s
whimsy carried nothing; the fixed-point claim belongs in the name. `lir` alone
reads as "the LIR" rather than "LIR selection into machine code", and the new
name also flags that it runs no front end. `whole` conflates "whole compiler
bundled" with "middle end actually runs" — `passes_` is true only there and in
clamp. `clamp` names a field of the subject's record, three levels from what
the rung tests.

Confirmed while proposing: `scale`'s subject **is** `CCE.codex`
(`ast/gen_scale_harness.py:28`) plus an appended `Scale Driver`.

Flagged, not decided: `passes_to_x86_on_*` is long, and
`ir_to_x86_on_{fib,cce,mid,arith}` would be shorter and uniform. Recommended
against — `whole` and `fibx` test genuinely different amounts of compiler, and
that is more load-bearing than a subject difference. Also note "CCE" already
names the wire encoding all over this repo; the `_on_` position disambiguates,
but say so in the README.

## Migration

**No re-bank.** All 42 banked truth files were grepped: no rung name appears in
any truth *as a rung name*. The only hits are `--- desugar ---` as a dump
separator and `scale-by-four`/`scale-total` as identifiers inside subject
programs. The banks move by `git mv` and their bytes do not change.

The rule that keeps it free: **do not touch harness print strings or
subject-program identifiers.** `fib`, `double`, `scale-by-four` and
`--- desugar ---` are content; changing any costs an hours-class re-bank.

**Derivation points** (single-authority, cheap): `ast/oracle_lib.sh:19`
`LADDER_RUNGS`, `:31` `LADDER_UNITS`, `:39-45` `unit_rungs`, `:124-146`
`mode_flags`, `:418-428` `arm_for`; `truth_prov.py:35` `COMPOSITE`;
`check_paths.py:50` prose; `ast/gen_fibx_harness.py:50` and
`ast/gen_whole_harness.py:67` subject pairs. `bank_truth.py` and
`ladder_status.py` derive from `oracle_lib.sh` and need no edit.

**Renamed files:** 14 `gen_*_harness.py`, 12 `bundle_*.ps1`, ~24 per-rung
scripts (`*cycle.sh`, `truthcycle_*.sh`), 42 banked truths across u46/u47/u48.
Leave `arithcycle.sh` alone — `arith` is a probe, not a rung.

### The risk: a stale name silently selects the wrong artifact

All of `ast/*.truth`, `*.truth.prov`, `*.ir`, `*-subject.codex`, `*.zig`,
`*.zigout` are gitignored, so `git mv` will not touch them. After the rename
the tree holds a full set of plausible, real, pre-rename artifacts under the
old names, and anything still spelling an old name reads them and looks green.

Three sites spell old names as literals and are **not** derived from
`LADDER_RUNGS`:

1. `ast/f3_run.zig:222` — `{ "fibx.truth", "fibx.zigout" }`. Tracked,
   hand-written, never validated against the ladder lists. Highest risk: miss
   it and F3 carves fib out of a stale dump and passes.
2. `ast/f4_boot.py:26-29` — `RUNGS = [("fibx","6765"), ...]`, with hardcoded
   expected answers that would still match.
3. `overnight_verify.sh:99-100` — `zig run fibx.zig`.

Mitigation: after renaming, `git clean -ndX ast/` and delete the orphans before
the first sweep, so a missed literal fails loud instead of reading yesterday.

### A latent bug the rename exposes, in our favour

`ladder_status.py:47-56` iterates `LADDER_UNITS` looking for
`ast/{unit}.truth.prov`, but sidecars are per-**rung**. It works today only
because `fibx` and `whole` happen to be both a unit name and a rung name. Under
the new scheme `ir_to_x86` and `passes_to_x86` are no rung's name and the
status line would report them missing forever. Fix in the same pass — it is the
exact conflation the rename is meant to end, showing up in code.

### Mechanical snag

`oracle_lib.sh:170-172` derives the harness filename with bash `${m^}`:
`fibx` → `FibxHarness.codex`, but `ir_to_x86` → `Ir_to_x86Harness.codex`.
Replace with an explicit `harness_for()` case and keep the CamelCase chapter
filenames unchanged — which also keeps generated harness bytes identical, the
strongest available evidence the banks are still valid.

**Do not `sed`.** A blind substitution corrupts `check_diags.py`,
`plug_run_ring.py`, `cite_resolve.py` and every subject program.

## Order — three commits, on a clean tree

1. **Preparatory, no renames.** Replace the `${m^}` derivation; fix
   `ladder_status.py` to iterate rungs. Verify with no QEMU: regenerate every
   harness and confirm byte-identical output.
2. **The rename, atomic.** Hash the banks first; `git mv` everything; edit only
   the derivation points plus the three hardcoded literals; clean the orphaned
   `ast/` artifacts; then the no-QEMU gate — `bash -n` every script, source
   `oracle_lib.sh` (its `LADDER MISMATCH` check runs at source time), import
   `truth_prov` (its unit/rung cross-check runs at import), `check_paths`,
   `check_bundles`, `ladder_status`, regenerate harnesses and diff, re-hash the
   banks. Only then one `allcycles.sh` sweep for 14/14. **No re-bank.**
3. **Prose.** README tables, findings, PRIORITIES/DONE/JUSTIFICATIONS, plus a
   permanent old→new table that never gets removed — 14 commit subjects, three
   tags, and upstream issues 70/72 and PR 76 cite the old names and are outside
   our control.

Do not split commit 2: `oracle_lib` and `truth_prov` cross-checks reject the
intermediate state anyway, and a half-renamed bank is the one artifact nobody
can validate mechanically. Not in this pass: harness chapter names, the
`prefix` argument to `harness_source`, and the `Quire` tags — those reach
generated Codex identifiers and through them the compiled unit.

## Loose thread found while proposing, unrelated to naming

Whether `clamp` still tests what its docstring says. The u48 bank shows
`emit-errors 6` / 19 diags / `CODEGEN-HALTED`, so the error path is still
exercised — but finding 15 closed with u48's native `Match` guards and
`plug-oracle-arith` moving to `match`. Whether the six errors are still the
same six deserves its own look. It does not affect naming:
`passes_to_x86_on_arith` stays true either way, where `clamp` already does not.
