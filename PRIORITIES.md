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

## 1. The heap unification -- the branch carries the fixes, one crash open

**Objective: land our own fix; finishing it is hunting our own plug.**
`findings/zig-heap-unification.md` for the design and the deck diagnosis;
`findings/README.md` 21-29 for what the unit tests found. Read the
EXCLUSIONS before touching anything -- several plausible mechanisms are
recorded as refuted, each with the test that killed it, and re-running them
is the main way to waste a day here.

Landed on `zig-plug-heap-unification` 2026-08-21, each measured on both
arms. `git log --oneline master..zig-plug-heap-unification` is the list; what
each one bought:

    14b2b8b6  __list-with-capacity honoured, and a cursor-collision refusal
    62ee2dd2  a deck allocation overrunning its reservation now refuses
    c09cd892  list constructors reserve the true total -- 6.96 MB of deck
    86675554  text concat extends in place            finding 22, asymptotic
    6fe3f49d  an uncovered codepoint substitutes      finding 23
    1a5ec700  peek-qword wraps                        finding 26
    3c4c00d6  reserve with rawAlloc                   finding 27
    def42bc7  substring traps out of range            finding 28
    35292021  substring and split copy                finding 29
    2202d3e5  text-replace copies                     finding 29, 4th site
    c86e66d5  shift counts masked to six bits         finding 30

Finding 23 is the one that unblocked the native loop on real source, and
finding 27 took a compile from 38.0s real / 15.3s sys to 11.4s / 1.8s,
because the old code committed all 1.5 GiB.

Natives rebuilt 2026-08-21 in sandbox `20260821T180749Z-natives-f29b`
through `2202d3e5`, and findings 28, 29 and 30 are confirmed on both arms
through them. **`c86e66d5` postdates that build and is verified as standalone
zig only**; `findings/gold/probe-shift-count.txt` holds the bare-metal column
it must match, so confirming it after the next rebuild is one command.

**The natives must be rebuilt after any emitter change, and that is the gate
for everything downstream.** `native_build.sh` in a sandbox, >25 minutes, and
nothing else may touch the CPU while it runs: the guest asks for 3072 MB on
a 3849 MB box, and a concurrent `zig run` is enough to stall its transport
mid-transfer.

**The droplet sweep was killed at 10/14 with fibx stalled on stale IR, so
it answered nothing.** Re-running it is now the question that GATES the Text
narrowing rather than a status check: most of these fixes landed after the
last real deck measurement, and if the four emit rungs now fit their
reservation the narrowing may be unnecessary. Cheaper than the narrowing
either way, and if they still overflow it says by how much. Needs the
rebuilt natives first.

**Still open: finding 24**, the `codexir` crash on the 2.5 MB subject, which
now reproduces natively in 11 seconds instead of eleven minutes through
QEMU. Ruled out by measurement, do not re-test: use-after-reclaim (that
binary never calls `__heap-restore`), reuse of freed memory (free made a
no-op changes nothing -- run twice), the in-place concat, a wrong argument
(pointer identical at creation and use, length zero), the deck guard, an
out-of-buffer write (unchecked on BOTH arms, so upstream semantics), and the
0xAA fill (zero-filling changes nothing). The live lead is the shape of the
corrupt value: a length field of order 1.3e14, which is POINTER-shaped in
the Linux mmap regime rather than 0xAAAA-shaped. That reads as field-offset
confusion or a struct-layout mismatch -- a pointer sitting where a length
belongs -- not as uninitialised or stale memory.

Still unanswered from the original design and still required before the PR:
what an out-of-region absolute address means (the SMP subjects peek ~2.1 GB
against RLIMIT_AS caps that count reserved space, not resident pages).
Sends after 76.

## 1.5 The unit tests -- INVENTORY COMPLETE 2026-08-21, keep it green

**Objective: instrument work that keeps turning into hunting.** Small Codex
programs, one per primitive tier, run on BOTH arms through the real
toolchains and compared. Ordered by what a failure invalidates rather than by
difficulty: if `__heap-save` does not observe allocation, every cost in every
other file is a zero that means nothing.

All seven tiers exist and carry both columns:

    tier 0/1  findings/prim-deck.codex       the meter, the two cursors    16 assertions
    tier 2    findings/prim-lists.codex      lists                          26 cost rows
    tier 3    findings/prim-text.codex       text, CCE, substring, split
    tier 4    findings/prim-records.codex    records and closures
    tier 5    findings/prim-buffers.codex    raw buffers
    tier 6    findings/prim-composite.codex  emit-all-defs in miniature      9 assertions

`findings/primitive-costs.md` is the cost table; `findings/probe-memory-model.codex`
carries the quadratic detector and predates the tiers. `prim-text-semantics`
pins what text MEANS rather than what it costs, as the before-picture for the
`Text` narrowing.

Small probes isolating one answer live beside them, and three exist because a
tier file could not hold the question: `probe-substring-trap` and
`probe-shift-count` each kill one arm on purpose, and `probe-deck-substring`
needs a rewind and a clobber to make its answer visible. Also
`probe-peek-qword`, `probe-fresh-span`, `prim-cce`.

**A tier file cannot assert anything that traps.** One trap takes the file's
other forty assertions with it, so a guarantee question gets its own probe and
the tier keeps the in-range rows.

**Ask whether a helper FAILS on the same inputs, not just whether it computes
the same answer.** Findings 28 and 29 both came from that question and neither
was reachable from a rung sweep. It has not been asked of any other `cx_*`
helper that takes an index or a length, and asking it is a source read rather
than compute -- the cheapest open defect hunt on this list.

**What they found, in one day: findings 22, 23, 25, 26, 27, 28 and 29**, of which 25
was invisible to eleven days of rung sweeps because the ladder's own chapter
slugs coincide, and 26 and 27 were found by a test tripping over them before
anyone thought to look. Tier 6 would have caught defect A outright -- when
`__list-with-capacity` discarded its argument, "table survived 8 brackets"
would have said no, in about a second.

**Standing work, not a finished task.** Run the tiers after any emitter
change -- `tier_run.py <file>` does both arms and diffs them, and it banks the
bare-metal column, so only the plug's side costs anything after the first run.
Add a tier row whenever a finding names a primitive that has none.

Rules that make these worth the trouble. Codex whenever the property is
observable from inside a Codex program, so bare metal is the oracle; zig only
when it is not, and then it is a regression test with no oracle and must be
labelled so. Never print an address. Assert the instrument before believing
it -- every file checks its own meter against a known reservation. Keep a
control: `cat-accum` is quadratic on BOTH arms, so it is inherent to the
source and not ours, and without that column it would have been filed as a
plug defect. And where the arms legitimately differ, mark the lines and say
why rather than letting the file claim byte-identity it does not have.

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

## 2.2 The sweep consumes IR it does not create -- GUARDED 2026-08-21

**Objective: instrument work, and the wrong-PASS kind.** Found 2026-08-21
when a sweep was launched in a fresh sandbox and every rung died instantly:
`allcycles.sh` reads `ast/<rung>.ir` and does not produce it. Those files are
truth-arm output. In the shared checkout they persist from whatever ran last,
so the dependency is invisible; a fresh worktree has none, which is how it
surfaced.

**The hazard is not the crash, it is the silence.** Nothing verifies that a
`.ir` came from the branch and seed now under test. The 22 files sitting in
the droplet checkout when this was found were generated by the GAPS-branch
sweep at 02:42, and were about to be used for a HEAP-branch sweep. If a stale
`.ir` survives a branch or seed change, the zig arm transpiles yesterday's IR
and compares it against today's bank -- a green that means nothing. That is
the same failure the provenance sidecars already guard for banked truths
(`truth_prov.py`), applied to the wrong artifact.

**Done.** The truth arm stamps `ast/<unit>.ir.prov` the moment the IR is known
good, and both `zig_arm` and `ring_arm` refuse before spending a transport --
so the refusal names the rung about to be judged instead of surfacing as a
bank mismatch hours later, or not at all.

The key is **(seed sha, subject bytes, mode flags)**, which is exactly what
the IR is a function of. Not the Codex checkout's HEAD, which was the first
shape proposed here: the plug does not participate in producing IR, so
keying on HEAD would refuse on every plug commit -- every commit that cannot
possibly have changed the IR -- and a guard that cries wolf gets switched off.

**One-time cost, and it lands on the next sweep.** Every `.ir` predating the
guard is refused as UNPROVENANCED, because there is no record to check and
inferring one from timestamps is the failure `truth_prov` already refuses for
truths. Regenerating is one `ring_compile.py ast/<unit>-ir-cce.blob
ast/<unit>.ir` per unit plus a `stamp-ir`, not a full truth arm -- and only
two units cover all four emit rungs, since `scale` rides `fibx` and `clamp`
rides `whole`.

Still open from the original item: `allcycles.sh` should REGENERATE a
refused `.ir` rather than stopping, so a fresh worktree bootstraps itself.

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
  tmux or setsid, logs in the droplet ladder's logs/). DONE 2026-08-21:
  `PHASE_FROM=C nice -n 15 setsid nohup ./overnight_verify.sh > log 2>&1 &`
  survives the ssh going away. Caution: do not let the backgrounded chain
  inherit the ssh session's stdout, or ssh holds the channel open and
  looks hung while the job runs fine.
- **MEASURED LIMIT 2026-08-21: the droplet runs SWEEPS but not NATIVE
  BUILDS at CODEX_MEM_MB=1300.** The gaps sweep went 14/14 green, then
  phase D stalled compiling zigemit to IR through the seed: QEMU burned
  4 seconds of CPU in 28 minutes with both it and `ring_compile.py`
  parked in `do_poll` and both chardev sockets ESTABLISHED -- the guest
  ran briefly and stopped. Same silent-death class as the TCP plug's
  measured 1600 MB floor. Note `ringplug.cdx` (237865 bytes) DID build
  in that same phase at the same cap, and zigemit is 236876 bytes, so
  this is about what the seed's IR compile costs, not blob size; the
  floor is not bisected. Diagnose stalls by CPU TIME, not elapsed --
  `ps -o etime,time` separates "slow" from "dead" in one line.
  Consequence: censuses and native builds stay laptop-side until the
  floor is measured. Raising the cap toward 1600 on a 1968 MB box that
  also serves the live site is not something to gamble unattended.
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

## 4.5 Execute the rung renames (PROPOSED 2026-08-21, not started)

**Objective: instrument work.** The rung names bury the lead -- `fibx` says
nothing about what it tests and `scale` names a property of the input. Worse,
six of fourteen rungs never reach the x86 back end at all and nothing in the
names says so. The full proposal, mapping and migration plan is
`RENAME-PROPOSAL.md`; that file is temporary and gets deleted by the commit
that executes it.

Headlines: a unit is named for the stage it reaches, a rung adds
`_on_<subject>` only when its unit carries two subjects, and **six names do not
move**. No re-bank is needed -- no rung name appears in any banked truth as a
rung name, so the 42 files move by `git mv` with their bytes unchanged.

**Do it when the deck investigation settles, not before.** Every finding
written this week refers to the current names, and renaming while we are still
re-reading them costs more than it saves.

The one hazard worth carrying in your head: all `ast/` outputs are gitignored,
so after a rename the tree still holds a complete set of real, plausible,
pre-rename artifacts under the old names. Three sites spell old names as
literals without deriving them from `LADDER_RUNGS` -- `ast/f3_run.zig:222`,
`ast/f4_boot.py:26-29`, `overnight_verify.sh:99-100` -- and a missed one reads
yesterday's dump and passes green. Clean the orphans before the first sweep.

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
