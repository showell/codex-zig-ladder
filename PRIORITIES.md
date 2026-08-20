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

## 1. Finish the u48 re-pin ceremony (IN FLIGHT 2026-08-20)

**Objective: due diligence, with the two-venue sweep's acceptance run as
instrument work riding it.** Pin `u48-rebank` at `b643e7cb`, ZERO
cherry-picks -- verbatim, and the census re-pins verbatim too (Steve:
"the noisy bank is the honest bank"; the five hunt subjects will read
red until PR 76 absorbs, and that diff IS the measurement of what the
depot shipped). The truth phase is COMPLETE (12/12 units recorded under
the u48 seed, prov'd -- `ladder_status.py` confirms) and the wiring
batch has landed (2026-08-20, six commits closing review items
S1/S7/D1/D3/D4/C1/C3/C4/C5 plus the mem_mb plumb). Remaining, in order:

1. Acceptance run of the two-venue sweep: `sweep_prep.sh` ->
   `sweep_canary.sh` -> `sweep_long.sh` -- this IS the ceremony's sweep
   (the local sweep was deliberately cut at 7/14 for the venue change);
   expected to reproduce 14/14 over the recorded truths. First
   rung_stamp timings decide the real canary/long split point.
2. Bank over green arms: `bank_truth.py`, then `bank_diff.sh` for
   u47 -> u48.
3. Verify Update 48's native match guards on the re-pinned sweep;
   close finding 15 / issue 72 in the register. Workaround-hygiene
   extends to SCRIPTS (review S5): delete `tonight.sh` in the same
   commit (its step 2 exists to confirm the finding being closed), and
   sweep the other orphans (recon.sh, verify_merge.sh,
   run_bag_probes.sh, ast/irmemcycle.sh) for retire-or-document.
4. Census re-pin: `native_build.sh` from the pin, full
   `corpus_run.py --changed --bank`. Expect the five PR-76 subjects
   red and possibly the 36 ex-codexir aborts back until absorption.
5. Diagnostics POLICY re-pin, timings refreshed into README "Running
   it", banked-against table, tag `u48-14of14`, push.

## 2. The heap unification

**Objective: land our own fix; the verification is due diligence.**
`findings/zig-heap-unification.md`. Closes `__heap-restore` being a
no-op on the zig arm; the arena is the interim. Pre-approved in shape by
Damian ("send it as its own PR when the hunt settles" -- it has), as are
the `cx_show_int` double allocation and the per-instruction throwaway
list. The design must first answer what an out-of-region absolute
address means (the SMP subjects peek ~2.1 GB against RLIMIT_AS caps that
count reserved space, not resident pages). Next PR after 76, off
whatever base is current when it goes.

## 3. The external review, in three batches

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

## 4. Widening the hunting ground: the gap families

**Objective: hunting, reached through our own gap-filling.** The census
buckets with oracles left to consult are all blocked on OUR gaps; every
family implemented promotes a slab of programs into the comparing stage
where the depot's oracles can finally see them (random895 -- gap work is
not port-finishing, it is instrument reach). By expected yield:

- **bool-vs-i64 coercions** -- dominates the ~111 refusals.
- **`cx_approx_eq`** -- finding 20's fix: the 4-ULP ordinal-distance
  test replacing `==` on IrApproxEq (measured both arms 2026-08-20).
- **The memory-access builtin family** (`poke-byte`, `peek/poke-16/32`,
  `bit-not`) -- the coherent slab atop the ~232 markers; implementing
  the family unblocks a large slice at once. Explore before asking
  Damian for anything.
- **Non-ASCII identifiers**: `zig-sanitize` needs `@"..."` quoting
  (ident-letters reached this the day the char migration landed).
- **Unit families** (finding 17's fix shape): `unit-def` emits an alias
  of its backing type; 8 refusals.
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

Queued behind it: the heap unification (item 2). Base for anything new:
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
