# What is next, in order

Kept here rather than in anybody's head or memory file, because there are now
several threads and they were drifting apart. If a memory or an essay disagrees
with this file, this file wins. Dated entries so staleness is visible. Done
items leave the list; git history is their record.

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

## 1. The corpus hunt

**Objective: hunting.** Run every depot test program through the zig arm and
diff against its hand-verified `.expected` -- an oracle per program, written
by someone with no knowledge of this plug, which is the property our own
probes cannot have. Every differ or crash is a candidate finding; every
refusal is a gap in our emitter or prelude. The census *run* is due
diligence wall time; the *triage* of what it surfaces is the hunt, and the
hunt is the point.

**The design is `corpus/README.md`** (banked census diffed like a truth
file, changed-only reruns keyed on emitted-zig hashes, a set-cover sentinel
gate, full census per-Update only).

**State 2026-08-19 21:25: the first full census is BANKED** --
`corpus/census.json`, 566 programs, healthy host, finding 16's heap-base +
deck fix on the pin, 14/14 sweep green ahead of it (log
`logs/wall-heapdeck-2026-08-19b.log`). The `--changed` loop and the
sentinel set are unblocked. The tallies, and what mode each bucket is:

    162 match        the denominator that makes a future differ mean something
      2 differ       HUNT: shadow-builtin-fold, text-fold-indexed
      3 crashed      HUNT: bloom-spread, consistent-hash-balance,
                     particle-spread (one wrap-overflow family, below)
      2 hardware-only  smp-arm64-boot, smp-riscv-boot: classified, never run
                     (corpus/hardware-only.txt; re-banked 2026-08-19)
    102 refused      our gaps; dominated by the bool-vs-i64 class (item 5)
     28 no-expected  no oracle to hunt with
    221 markers      never ran: missing emitter builtins (poke/peek family,
                     port-in-byte, unicode text ops) -- the gap family below
     36 codexir      never ran: hosted-compiler stage failed (feeds item 6)
     10 unresolved   cites that did not resolve

The 33-differ pilot count deflated to 2 exactly as predicted once the
capture-byte artifact was fixed. Re-measure codexir's per-program time on
this host before quoting any figure; the only measurement so far came off
the sick box.

**Desk triage 2026-08-19 (read-only, all seven root-caused or clustered;
fixes NOT yet applied, batch them into ONE emitter change-set so one sweep
+ one census `--changed` covers all):**

- **shadow-builtin-fold (differ): intercept-by-name ignores user shadowing.**
  The subject shadows `text-length` and `abs`; the language says the user
  definition wins (expected 99/99/77), and the emitted zig even CONTAINS the
  user's functions -- but the call sites were hijacked by the
  ZigBuiltinEmitter name table (got 3/3/5). Fix: builtin interception yields
  to names the module itself defines. Ours, not a finding.
- **text-fold-indexed (differ): this is item 2's decided char migration,
  caught by a depot oracle.** The fold hands the lambda
  `cx_cce_to_cp(cx_char_at(s, i))` (so 'e' arrives as 101) while IrCharLit
  compiles to the raw CCE code (15/13/17/16/25 for the vowels) -- every
  `ch == 'a'` fails, vowel count 0. Joins probe-char-literal as evidence;
  the fold template joins char-at/code-to-char on item 2's flip list. The
  census bank that item 2 was sequenced behind has landed -- the migration
  is unblocked. Ours, not a finding.
- **bloom-spread, consistent-hash-balance, particle-spread (3 crashes):
  `panic: integer overflow`, one family.** Hash/spread arithmetic overflows
  i64; bare metal wraps (x86 add), C# `long` wraps (unchecked default), zig
  `+`/`*` panics in debug. If the language's rule is wrap, the emitter
  should use `+%`/`-%`/`*%`. VERIFY the ruling against the C# emitter and a
  bare-metal source before editing -- if Codex intends overflow to be an
  error, the wrap on bare metal is a FINDING, not our bug.
- **smp-arm64-boot, smp-riscv-boot (2 crashes): RESOLVED AT THE DESK
  2026-08-19 -- hardware-semantics subjects the hosted arm structurally
  cannot answer.** Each polls a marker cell at a fixed high physical
  address (`peek-qword #7E000000` / `#80090000`, ~2.1 GB) that only a
  SECONDARY CPU CORE writes (PSCI CPU_ON / hart start under QEMU virt).
  The OOM is just the messenger: `cx_peek_qword` calls `cx_buf_want`,
  which zero-fills the contiguous heap up to the address -- 2.1 GB against
  an 800 MB cap. But no memory model fixes them: a hosted single process
  has no secondary core, so even a sparse heap reads 0 forever and prints
  "AP DID NOT RUN" -- a differ, not a match. Right move is an honest
  census classification (a documented hardware-only exclusion bucket, its
  own verdict class, never counted as crash), which is instrument work,
  not a hunt. The cap stays at 800 MB; nothing here argues against it.
  DESIGN CONSEQUENCE for the cx_heap unification (noted in
  `findings/zig-heap-unification.md`): subjects may peek absolute
  addresses far above any reservation, and RLIMIT_AS caps count reserved
  address space, not resident pages -- the design must say what an
  out-of-region absolute address means before it goes to Damian.

The known gap family is coherent: `poke-byte`, `peek/poke-16/32`, `bit-not` --
the memory-access builtins; implementing the family unblocks a large slice at
once. Explore before asking Damian for anything; if it pays off, the ask is
"would you want this as a signal on your side", not "persist your IR".

## 2. Two emitter defects: finish the probes, file

**Objective: hunting, then one fix.** Two suspected divergences become filed
findings with both-arms evidence; the char migration that follows is our own
fix (converging on the model bare metal already has), verified by the probes
before/after and the census diff -- that tail end is due diligence.

- **Char literals are CCE codes while every other Char is a codepoint**, so
  `char-at s i == 'x'` is always false and compiles clean. Zig arm measured
  (`findings/probe-char-literal.codex`: found-x 0 where the language says 1,
  controls clean); owed: the bare-metal half, then file.
- **`IrApproxEq` emits `==`**, dropping the 4-ULP tolerance. Probe written
  (`findings/probe-approx-eq.codex`); its two blockers
  (`bits-to-real-approx` emitter, `text-to-double-bits` prelude) landed
  2026-08-19 with the multi-byte CCE work. Run the probe both arms, file.
- **Char = CCE code migration (DECIDED 2026-08-19, Steve + Claude; full
  analysis random886).** The zig plug converges on the C#/bare-metal
  identity model, as ONE coherent commit, sequenced AFTER the census
  baseline banks so the full-rerun diff names what moved. Probe first:
  `findings/probe-char-ops.codex` + probe-char-literal, both
  arms, before and after. Flip together: char-code / code-to-char to
  identity, is-letter / is-digit to the CCE bands (13..64 and 97..127
  letters, 3..12 digits), and every prelude site comparing a zig char
  literal. The char-literal finding then files as resolved-by-convergence
  with before/after evidence. Background on why the codepoint model is
  structurally lossy:
- **The CCE alias limit of Char-as-codepoint (2026-08-19).** CCE has
  aliases: é is tier-0 code 97 AND tier-1 code 233, and
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

**Objective: land our own fix; the verification is due diligence.** The
change is ours and pre-approved in shape; the sweep and census diff that
prove it image-preserving are wall time, and green there is not news.

`findings/zig-heap-unification.md`. Closes `__heap-restore` being a no-op on
the zig arm, which costs sum-over-definitions instead of max-over-definitions
during emission; the arena is the interim. Pre-approved in shape by Damian
("send it as its own PR when the hunt settles"), as are the `cx_show_int`
double allocation and the per-instruction throwaway list.

## 4. The external review, in three batches

**Objective: instrument work.** The review's high findings are wrong-bank
and wrong-PASS closers -- ways the harness could lie green. None of it
hunts; all of it decides whether a hunt's verdict can be trusted.

`REVIEW-2026-08-19.md` (Marley, for Damian, at our 8a74c94) -- ~34 findings,
several landing on items this file already names. The three high ones we
spot-checked all confirmed. Absorbed as three batches so the census and
char-migration lanes above stay first:

- **Batch 1, keyboard-only, next working slot:** the wrong-bank and
  wrong-PASS closers plus unattended hazards. Banking provenance (seed sha
  recorded beside each `.truth`, atomic bank via temp-dir rename,
  content-hash watermark, narrowed glob, prune-by-name), `ring_compile`
  pre-READY EOF (item 6 below -- fix is literally `codex_vm.wait_ready`),
  `plug_run` truncation-reads-as-success, QEMU orphan try/finally,
  rm-stale-artifacts-first family (`.truth`, `.diags`, `plug-source`,
  guardprobe), checks that report but do not refuse (warmup diff,
  check_diags NOTE rc), small correctness (f4_boot, plugcycle, seed_identity
  label, pcap coverage), and every doc seam they list (README:300 stale
  byte-identical claim first). Commit per finding.
- **Batch 2, needs QEMU + a re-bank:** delete the deck-record rename from
  the ten bundlers (our own workaround-hygiene rule; Update 43 closed the
  finding) and let the bank diff prove it image-preserving; unify the two
  plug fingerprint guards on the ring model (re-bundle and compare).
- **Batch 3, structural, its own session, net first:** `tests/` for the
  refusers (split_truth, bank_truth, seed_identity, check_diags, cce,
  pcap_parity, the `--changed` carry), THEN driver consolidation into
  codex_vm (launch + read_size_framed; gdb RSP framing while there) and the
  harness/bundler dedup.
- Declined or deferred, with reasons in the review response: tracked
  census json stays (deliberate, the bank supersedes run.json soon);
  LICENSE is Steve's call; errors='replace' byte-compare rides Batch 3.

## 5. Census fallout (numbers from the 2026-08-19 pilot, `corpus/run.json`)

**Objective: mixed, and the split IS the triage.** The refusal classes are
our gaps (fixes, then due diligence); the differs and crashes are candidate
findings (hunting). Numbers below are the pilot's; tonight's banked census
supersedes them.

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

**Objective: hunting.** A hosted-compiler crash is its own finding.

Two crashes in the 40-program pilot; `corpus_run.py --limit 40` reproduces
them and `corpus/transpile.json` names them (stage `codexir`). A
hosted-compiler crash is its own finding; identify and reduce.

## 7. ring_compile busy-loops when its QEMU dies

**Objective: instrument work.** An unattended runner must never convert a
crash into a hang.

Located by the review (`ring_compile.py:150-154`): the PRE-READY wait --
`while b"READY" not in buf: buf += ctrl.recv(4096)` -- never checks for
`b""`, so a dead guest returns EOF instantly and forever, a 100% spin with
a frozen log. The read/refill and output loops already fail loud; earlier
wording here blamed them. `codex_vm.wait_ready` has the EOF check and was
not reused -- the fix is to call it. Same honesty class as the memory caps:
an unattended runner must never convert a crash into a hang. Until fixed,
detection is a stale log mtime beside a hot python process. Rides review
Batch 1 (item 4).

## 8. Diagnostics as a banked set

**Objective: instrument work.** A pinned count says something changed; a
banked set says what.

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

## Outbound queue

PRs 73 and 74 were absorbed 2026-08-19: re-applied in Perforce (main 17401),
public at `8f997bd8`, verified on Damian's side (49/49 plug oracles; script
drift 0). **`8f997bd8` is the base for whatever goes out next.** Damian left
one open door on 74: a QEMU fallback for the batch REPL is its own change if
we want it -- noted, not queued.

The arena prelude is NOT queued -- it went up as PR 71 and was absorbed at
`a061c173`; upstream's arena code is byte-identical to ours, only the comment
was trimmed in the Perforce re-application. (`git cherry` cannot see this:
Perforce re-application changes patch-ids, so absorption is a content
question, never a patch-id question.)

**SENT 2026-08-19 as PR 75** (github.com/damiant3/NewRepository/pull/75):
the three-commit dependency chain -- the CCE tiers and char-to-text commits
were never sent before, and the finding 16 fix sits on top of them
(`cx_utf8_to_cce` calls `cx_cce_frame`):

1. `a3756ec0` -- multi-byte CCE tiers in the prelude, IrNumLit bits,
   bits-to-real-approx, faithful text-to-double-bits.
2. `181310ec` -- char-to-text is one byte, the bare-metal contract.
3. `24c0d925` -- **the finding 16 fix** (heap base + real deck). Tonight's
   14/14 sweep and the banked census are the proof; the three observing
   oracles (arith-narrow-proven, deck-bracket-contract, deck-record-contract)
   all match. The register (`findings/README.md` sec. 16) says "fix is ours
   to propose" -- this is the proposal.

Replay done 2026-08-19 (worktree `~/showell_repos/nr-f16-replay`, branch
`zig-plug-cce-heapdeck`): picks 1 and 2 apply clean, pick 3 had one trivial
conflict (`zig-prelude-decls` -- union both sides' added names). Residual
diff of the replayed emitter vs the pin is exactly upstream's own absorbed
content (PR 73's switch pin, issue 72's match guards), nothing of ours.
**Spot-verified 5/5 MATCH on seed `800A7683`** (natives built from the
replay tree, log `logs/native-f16-replay-2026-08-19.log`): the three finding
16 observers plus cce-roundtrip and ui-font-cce-order. No full sweep here by
design -- it would run a new-seed plug against old-seed truth; the one full
sweep slot is the Update 48 re-pin re-bank. Toolchain snapshots (pin and
replay) live in `~/showell_repos/*-snapshot.tar` until the PR is absorbed.

---

## How to read this list, given how the work actually goes

Two modes alternate: at the keyboard, where decisions and code happen, and
away from the machine, where something long should be running unattended.
**Keyboard work** is the probes and emitter changes (items 2, 3, 4), the
tooling fixes (7, 8), and landing what reviews come back on. **Away work** is
running what those produce: `tonight.sh`, the census stages of item 1,
`ast/allcycles.sh` after any emitter change.

The objective modes at the top map onto this: due-diligence runs are away
work by construction, and hunting and instrument work happen at the
keyboard. A hunt's *runs* are away work; its *reads* are not.

The rule that makes both work: **one compute job at a time.** The machine has
about 3 GB usable and QEMU takes most of it. Anything fired from the keyboard
waits for what is already running, the way `tonight.sh` does.

**Possible change of venue (Steve, 2026-08-19): start working from the prod
droplet as early as tomorrow.** The droplet is extremely under-utilized and
Steve has ruled it fine to work there — treat the old don't-build-there
posture as caution about the live site, not a blocker. What it would buy:
a host that doesn't share a laptop with Windows, no WSL livelock exposure,
no OEM-crapware CPU theft (2026-08-19 lost most of an evening to that).
What to watch: 1 vCPU / 2 GB is smaller than the laptop's 3 GB, and the
live site shares it — size QEMU and the census batches to that before
moving the loop.
