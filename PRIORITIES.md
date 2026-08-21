# What is next, in order

Kept here rather than in anybody's head or memory file, because there are now
several threads and they were drifting apart. If a memory or an essay disagrees
with this file, this file wins. The README's "Processing a new Update" is
the ceremony's step list; this file adds items and says where they slot --
on a conflict about ORDER, the README's list is the spine. Dated entries so staleness is visible. Done
items leave the list -- git history is their record, DONE.md holds one line
and a pointer each when a pointer helps, and measurements go to
JUSTIFICATIONS.md. This file is the queue, not the diary.

Every numbered item opens with an **Objective** line saying what the work is
trying to achieve, and in which of three modes it runs -- because the same
40-minute run means different things in different modes, and mistaking one
for the other misprices the work:

- **Hunting.** Fishing for defects that are not ours -- the project's actual
  product. A surprise is the payoff; a clean pass is a mild disappointment.
- **Due diligence.** Verifying that our own changes break nothing. On the
  happy path this is pure wall time: launch it, let it run, read one line.
  Only a red result is information, and green earns no celebration.
- **Instrument work.** Making the harness itself honest or cheap. It neither
  hunts nor verifies, but the other two modes are only as trustworthy as it
  is.

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

## 1. The heap unification -- VERIFIED RED, one defect fixed, one open

**Objective: land our own fix. The verification stopped being due
diligence the moment it went red; finishing it is now hunting our own
plug.** `findings/zig-heap-unification.md` -- the design note, plus the
2026-08-21 section that is the live diagnosis. Read that section before
touching this; it records what is ruled out as well as what is known,
and one of the exclusions (the deck nesting model) cost hours and looks
exactly like a cause.

State: 10/14 rungs byte-identical to the u48 bank, `fibx` and `whole`
red. With reclaim disabled both are byte-identical, so the rest of the
branch is correct. **Defect A fixed** (`14b2b8b6`, `cx_ll_with_capacity`
discarded its argument -- the emit tables were reallocating inside
`emit_all_defs`' bracket, exactly the corruption the compiler's own
guard text predicts). **A second escape is open**, symptom 0x896;
prime suspect is list growth schedule against bare metal's explicit
headroom. Next instrument is poison-on-restore -- the plan is in the
findings doc.

Cheap loop, established 2026-08-21: patch the emitted `ast/fibx.zig`
prelude and `zig run` it -- **ten seconds**, versus ~11 minutes for the
rung, because the ring transpile is what costs. Truth rides stderr, so
stdout is free for instrumentation.

Still unanswered from the original design, and still required before the
PR: what an out-of-region absolute address means (the SMP subjects peek
~2.1 GB against RLIMIT_AS caps that count reserved space, not resident
pages). Pre-approved in shape by Damian ("send it as its own PR when the
hunt settles"), as are the `cx_show_int` double allocation and the
per-instruction throwaway list. Sends after 76, off whatever base is
current when it goes.

## 2. The external review, in three batches

**Objective: instrument work.** The review's high findings are wrong-bank
and wrong-PASS closers -- ways the harness could lie green. None of it
hunts; all of it decides whether a hunt's verdict can be trusted.

`REVIEW-2026-08-19.md` (Marley, for Damian, at our 8a74c94) -- ~34 findings.
The three high ones we spot-checked all confirmed. Several have since been
fixed in passing (banking provenance, ring_compile's pre-READY EOF); each
batch's first act is re-checking its list against the tree:

- **Batch 1, keyboard-only:** the wrong-bank and wrong-PASS closers plus
  unattended hazards -- `plug_run` truncation-reads-as-success, QEMU
  orphan try/finally, rm-stale-artifacts-first family, checks that
  report but do not refuse, small correctness (f4_boot, plugcycle,
  seed_identity label, pcap coverage), doc seams. Commit per finding.
- **Batch 2, needs QEMU + a re-bank:** delete the deck-record rename from
  the ten bundlers (workaround-hygiene; Update 43 closed the finding) and
  let the bank diff prove it image-preserving; unify the two plug
  fingerprint guards on the ring model.
- **Batch 3, structural, its own session, net first:** `tests/` for the
  refusers, THEN driver consolidation into codex_vm and the
  harness/bundler dedup.
- Declined or deferred, with reasons in the review response: tracked
  census json stays; LICENSE is Steve's call; errors='replace'
  byte-compare rides Batch 3.

## 2.5 The droplet becomes a full venue (DECIDED 2026-08-20 late, Steve)

**Objective: instrument work.** The appliance model dies of its own
elegance: the held ssh ties every droplet job to the laptop's wifi, and
today's blip cost a rung. Full checkouts + toolchain on the droplet
means long jobs run AND SURVIVE there, laptop-free. Gopher stays
protected by the same rails (nice, the compute lock, 1300 MB guests,
untouched home dirs).

DONE tonight: git (present), pwsh 7.5.4 at ~/.local/pwsh (the laptop's
path -- scripts run verbatim), both repos cloned (~/showell_repos/*,
NR on the verbatim pin), check_paths green mod cycle-built artifacts,
and **the lex truth arm ran end to end on the droplet, byte-identical
to the banked u48 truth** -- venue-independence of the truth pipeline
is measured, not assumed. Remaining, in rough order:
- zig 0.16.0 (tarball to ~/zig-0.16.0, mirroring the laptop path) --
  unlocks zig arms, natives, censuses droplet-side.
- ~~Push credentials~~ DECIDED (Steve): the droplet is FETCH-ONLY --
  it holds no git credentials, pulls the public repos anonymously, and
  results come home by scp; commits and pushes stay laptop-side. The
  cleanest trust posture beside the live site, revisit only if it
  chafes.
- Detached-job discipline droplet-side (the rebank self-detach pattern;
  tmux or setsid, logs in the droplet ladder's logs/).
- CODEX_MEM_MB=1300 / CODEX_ACCEL=tcg defaults for droplet sessions
  (a droplet-local env file the scripts source, not per-command
  ceremony).
- README venue sections rewritten when the model settles. BOTH modes
  persist, deliberately (Steve, 2026-08-20): **the venue follows the
  mode.** HUNTING stays local or hybrid -- the straw scripts
  (droplet_compile/droplet_transpile, the two-venue sweep) are the
  keyboard-tempo tools and are NOT retired. DUE DILIGENCE moves
  all-on-droplet -- long unattended runs must survive the laptop
  leaving the wifi. The full-venue checkout and the appliance straw
  coexist on the same box; the compute lock is the arbiter as ever.

## 3. Provenance watches one file too many

**Objective: instrument work.** The truth sidecars hash `oracle_lib.sh`
whole, so a guard-or-comment edit to the ZIG-arm half invalidates every
recorded truth's provenance -- it cost a full truth-arm re-measurement
on 2026-08-20, hours after the same session built the guards that fired
(the wiring batch edited oracle_lib between recording and banking; the
diff was provably guards and comments, and the only honest path was
re-measuring). Fix shape: segregate by volatility -- split the
truth-arm measurement machinery (mode_flags, truth_arm, split plumbing)
into its own sourced file that the sidecar watches, leaving the
zig-arm/instrument half free to move. Do it right after a bank lands,
never between recording and banking.

## 4. Widening the hunting ground: the gap families

**Objective: hunting, reached through our own gap-filling.** The census
buckets with oracles left to consult are all blocked on OUR gaps; every
family implemented promotes a slab of programs into the comparing stage
where the depot's oracles can finally see them (random895 -- gap work is
not port-finishing, it is instrument reach).

**BATCH IMPLEMENTED 2026-08-20 evening** on branch
`zig-plug-refusal-gaps` (off the PR-76 tip; nine commits; typecheck
meter: 90 of the census's 105 refusals promoted). In it: the entry
shim (startFn, 39 refusals), Boolean->Integer coercion at declaring
boundaries (35), the memory-access family to C#'s _Buf rules
(alloc-bytes, peek/poke-16/32, poke-byte, bit-not -- the marker slab's
top), unit aliases (finding 17), the approx-eq 4-ULP band (finding
20), @"..." identifier quoting (ident-letters), Boolean literal
patterns, and the observed prelude-shadowing colliders. Verification
= overnight_verify.sh phases C-D (sweep + census); the PR follows it.

Residual classes, measured, for the next batch:
- **Curried/oversaturated calls** (5): a zero-param def whose value is
  a closure called with args needs `f().call(...)`; struct-vs-struct
  binops in the fork/par family ride the same machinery.
- **show of a Real** (2): needs bare metal's __show_real formatting
  mirrored, never guessed.
- **Type-class dictionaries** (2): undeclared `T2`.
- **The systematic prelude-shadowing sweep** (1+): zig bans locals AND
  params shadowing file-scope names; dns-answer-count defines l, base,
  h... -- rename every prelude local and param to cx_, mechanically,
  in one commit. Letter-chasing measured futile.
- **MkTup2 out-of-unit** (16 markers): tuple machinery works when
  Tup2 is declared in-unit; the marker is the type arriving from
  outside. Drags ctor-map + pattern arms; own item.
- One-offs: `sin` (math builtin), one non-exhaustive switch.
- **From the batch's cold review (2026-08-20 late)**: the `@"..."`
  quoting breaks where a name is EXTENDED after sanitizing
  (`zig-sanitize(name) & "S"` gives `@"Name"S`; `_arg_` + raw ident
  ships hi bytes bare -- the file's own comment predicted it); f32
  approx-eq needs bare metal's distinct f32 ordinal path (the current
  band is f64-only, effectively zero f32-ULPs); and IrApproxEqExact
  as `==` diverges from ordinal-distance-0 on same-bits NaN (oracle 1,
  zig 0) -- the last two are register candidates, not just fixes.

Still queued from before:
- **Real-literal candidates in the other plugs** (source-read only,
  2026-08-19): the JS emitter's IrNumLit is `Number(BigInt.asIntN(64,
  bits))` -- bits as a NUMBER, not a bitcast; and parseFloat /
  double.Parse are correctly-rounded where bare metal's
  __text_to_double is not. Probe before filing either. Same family as
  finding 18's asides (python overflow, C# IrPowInt-as-XOR, the missing
  overflow oracle row).

## 5. Diagnostics as a banked set

**Objective: instrument work.** A pinned count says something changed; a
banked set says what. Diffed like a truth file, retiring the
CDX6020-style count pins that move whenever the unit list changes rather
than when the source does. (The sweep's own census note says exactly
this every time it prints.)

## 6. Parked: the notebook / Prism angle

Not work, a bookmark, deliberately last. A Python-hosted notebook showing
how Codex source becomes assembly, stage by stage, is a weekend-sized
demonstrator of Damian's dusty **Prism** design
(`apps/prism/design/Active/PrismDesign.md`). The native loop and `zigc`
already are its core machinery in cheap form. If picked up, re-read the
design against what exists now and ask Damian what he would want first.

Also parked, the endgame framing (random839): piggyback the C# DDC
witness path with zig -- C# stops at "compiles", zig RUNS.

---

## Outbound queue

**LIVE: PR 76** (damiant3/NewRepository/pull/76, sent 2026-08-20): wrap
arithmetic, shadowed-builtin yield, char-CCE migration -- the hunt
three, off `b643e7c`, spot-verified 5/5 against U48's own oracles.
Carries the source-read asides and offers the overflow oracle row.

Queued behind it: the heap unification (item 1, branch
`zig-plug-heap-unification` built and smoke-tested, ladder verification
pending). Base for anything new:
whatever the current release is when it goes; absorption is a content
question, never a patch-id question. PRs 71-75 are absorbed --
one line each in DONE.md.

---

## How to read this list, given how the work actually goes

Two modes alternate: at the keyboard, where decisions and code happen, and
away from the machine, where something long should be running unattended.
**Keyboard work** is the probes, emitter changes, and tooling fixes; **away
work** is running what those produce: the rebanks, the sweeps, the census
runs. A hunt's *runs* are away work; its *reads* are not.

The rule that makes both work: **one compute job per host.** The laptop
holds one QEMU comfortably; the droplet is flocked inside its wrappers
and every laptop entry point takes `take_compute_lock`. The droplet
venue means away work can overlap keyboard work across hosts -- but
never two compute jobs on one.
